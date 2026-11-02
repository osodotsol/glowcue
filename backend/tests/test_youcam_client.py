"""YouCam client against a fake API (httpx.MockTransport). No network, no real key."""

from __future__ import annotations

import json
import logging

import httpx
import pytest
from tests.youcam_fakes import FAKE_KEY, UPLOAD_HOST, Clock, FakeYouCam, live_settings, make_client, selfie_bytes

from app.services.normalize import SD_ACTIONS
from app.services.youcam_client import (
    CREDIT_PATH,
    DELETE_PATH,
    FILE_PATH,
    TASK_PATHS,
    YouCamError,
    describe_shape,
    parse_balance,
)

pytestmark = pytest.mark.anyio  # async tests run on anyio's pytest plugin (installed with FastAPI)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


TASK = TASK_PATHS["v2.1"]
IMAGE = selfie_bytes()


def verified_balance(amount_dec: float | None = 750.25, amount: int | None = 750) -> dict:
    """SYNTHETIC values in the balance structure recorded on 31 Oct 2026 (top-level `results`, no `data`)."""
    entry: dict = {"id": 4242, "type": "ApiPaygToken", "expiry": 1900000000000}
    if amount is not None:
        entry["amount"] = amount
    if amount_dec is not None:
        entry["amount_dec"] = amount_dec
    return {"status": 200, "results": [entry]}


def use_verified_balance(fake: FakeYouCam) -> FakeYouCam:
    """Answer the balance endpoint in the verified shape, using `fake.balance` (read at request time)."""
    fake.overrides.setdefault(
        ("GET", CREDIT_PATH),
        lambda r: httpx.Response(200, json=verified_balance(amount_dec=float(fake.balance), amount=int(fake.balance))),
    )
    return fake


async def run(fake: FakeYouCam, clock: Clock | None = None, **settings):
    use_verified_balance(fake)
    async with make_client(live_settings(**settings), fake, clock) as client:
        return await client.analyse_skin(IMAGE, "image/jpeg", SD_ACTIONS)


async def balance_from(body: object, *, status: int = 200, raw: bytes | None = None) -> float:
    """Run credit_balance() against a fake that answers the balance endpoint with `body` (or raw bytes)."""
    fake = FakeYouCam()
    content = raw if raw is not None else json.dumps(body).encode()
    fake.overrides[("GET", CREDIT_PATH)] = lambda r: httpx.Response(status, content=content)
    async with make_client(live_settings(), fake) as client:
        return await client.credit_balance()


async def test_youcam_client_runs_the_documented_flow_in_order():
    fake, clock = FakeYouCam(), Clock()
    items = await run(fake, clock)

    order = [(r.method, r.url.host if r.url.host == UPLOAD_HOST else r.url.path) for r in fake.requests]
    assert order == [
        ("GET", CREDIT_PATH),
        ("POST", FILE_PATH),
        ("PUT", UPLOAD_HOST),
        ("POST", TASK),
        ("GET", f"{TASK}/task-123"),
        ("GET", f"{TASK}/task-123"),
        ("POST", DELETE_PATH),
    ]
    assert {i.type for i in items} >= {"pore", "dark_circle_v2", "acne"}
    assert clock.sleeps == [10.0, 10.0]  # ~10 s polling, no rapid polling


async def test_youcam_client_registers_the_upload_with_size_and_type():
    fake = FakeYouCam()
    await run(fake)
    body = json.loads(fake.calls("POST", FILE_PATH)[0].content)
    assert body["files"][0]["content_type"] == "image/jpeg"
    assert body["files"][0]["file_size"] == len(IMAGE)


async def test_youcam_client_puts_bytes_with_exactly_the_presigned_headers_and_no_key():
    fake = FakeYouCam()
    await run(fake)
    (put,) = fake.uploads
    assert put.content == IMAGE
    assert put.headers["content-type"] == "image/jpeg"
    assert put.headers["content-length"] == str(len(IMAGE))
    assert "authorization" not in put.headers  # the key never goes to the storage host


async def test_youcam_client_authorises_every_youcam_call_with_bearer_key():
    fake = FakeYouCam()
    await run(fake)
    assert all(r.headers["authorization"] == f"Bearer {FAKE_KEY}" for r in fake.youcam_requests)


async def test_youcam_client_requests_json_sd_actions_without_masks_or_skin_type():
    fake = FakeYouCam()
    await run(fake)
    body = json.loads(fake.calls("POST", TASK)[0].content)
    assert body == {
        "src_file_id": "file-123",
        "dst_actions": list(SD_ACTIONS),
        "miniserver_args": {"enable_mask_overlay": False},
        "format": "json",
    }
    assert len(body["dst_actions"]) == 9
    assert not any(a.startswith("hd_") for a in body["dst_actions"]) and "skin_type" not in body["dst_actions"]


async def test_youcam_client_deletes_the_task_after_success():
    fake = FakeYouCam()
    await run(fake)
    (delete,) = fake.calls("POST", DELETE_PATH)
    assert json.loads(delete.content) == {"task_id": "task-123"}


async def test_youcam_client_task_error_raises_vendor_code_and_still_deletes():
    fake = FakeYouCam()
    fake.task_error = "error_no_face"
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "error_no_face" and not err.value.units_possible
    assert len(fake.calls("POST", DELETE_PATH)) == 1


async def test_youcam_client_never_retries_task_creation():
    fake = FakeYouCam()
    fake.overrides[("POST", TASK)] = lambda r: httpx.Response(503, json={"status": 503})
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "http_503"
    assert len(fake.calls("POST", TASK)) == 1


async def test_youcam_client_retries_a_poll_after_429_then_succeeds():
    fake = FakeYouCam()
    answers = iter([httpx.Response(429, json={"status": 429})])

    def flaky(request: httpx.Request) -> httpx.Response:
        try:
            return next(answers)
        except StopIteration:
            del fake.overrides[("GET", f"{TASK}/task-123")]
            return fake(request)

    fake.overrides[("GET", f"{TASK}/task-123")] = flaky
    items = await run(fake)
    assert items
    assert len(fake.calls("GET", f"{TASK}/task-123")) >= 2


async def test_youcam_client_gives_up_after_two_read_retries():
    fake = FakeYouCam()
    fake.overrides[("GET", f"{TASK}/task-123")] = lambda r: httpx.Response(500, json={"status": 500})
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "http_500"
    assert len(fake.calls("GET", f"{TASK}/task-123")) == 3  # first try + 2 retries


async def test_youcam_client_times_out_with_configurable_limit_and_leaves_running_task():
    fake, clock = FakeYouCam(), Clock()
    fake.statuses = ["running"]
    with pytest.raises(YouCamError) as err:
        await run(fake, clock, youcam_task_timeout_s=30, youcam_poll_interval_s=10)
    assert err.value.code == "timeout" and err.value.units_possible
    assert clock.now <= 40
    assert fake.calls("POST", DELETE_PATH) == []  # cannot delete a task that may still be running


async def test_youcam_client_credit_floor_stops_before_any_upload():
    fake = FakeYouCam()
    fake.balance = 110  # 110 - 14 units < floor of 100
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "credit_floor"
    assert fake.calls("POST", FILE_PATH) == [] and fake.uploads == []


async def test_youcam_client_credit_floor_zero_skips_the_balance_check():
    fake = FakeYouCam()
    await run(fake, credit_floor=0)
    assert fake.calls("GET", CREDIT_PATH) == []


async def test_youcam_client_unrecognised_balance_shape_fails_closed():
    fake = FakeYouCam()
    fake.overrides[("GET", CREDIT_PATH)] = lambda r: httpx.Response(200, json={"status": 200, "data": {"x": 1}})
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "credit_unknown"
    assert fake.uploads == []


async def test_youcam_client_maps_401_to_auth_failed():
    fake = FakeYouCam()
    fake.overrides[("POST", FILE_PATH)] = lambda r: httpx.Response(
        401, json={"status": 401, "error": "Invalid API key"}
    )
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "auth_failed"


async def test_youcam_client_reports_request_error_codes():
    fake = FakeYouCam()
    fake.overrides[("POST", TASK)] = lambda r: httpx.Response(
        400, json={"status": 400, "error": "Not enough", "error_code": "CreditInsufficiency"}
    )
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "CreditInsufficiency"


async def test_youcam_client_refuses_a_non_https_presigned_url():
    fake = FakeYouCam()
    fake.presigned_url = f"http://{UPLOAD_HOST}/put/object-1"
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "bad_response"
    assert fake.uploads == []


async def test_youcam_client_reports_a_failed_upload():
    fake = FakeYouCam()
    fake.overrides[("PUT", "/put/object-1")] = lambda r: httpx.Response(403)
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "upload_failed"
    assert fake.calls("POST", TASK) == []


async def test_youcam_client_rejects_a_zip_result():
    fake = FakeYouCam()
    fake.result = {"task_status": "success", "results": {"url": "https://example.test/result.zip"}}
    with pytest.raises(YouCamError) as err:
        await run(fake)
    assert err.value.code == "unexpected_format"


async def test_youcam_client_can_switch_to_the_v20_task_endpoint():
    fake = FakeYouCam()
    await run(fake, youcam_task_api="v2.0")
    assert len(fake.calls("POST", TASK_PATHS["v2.0"])) == 1 and fake.calls("POST", TASK) == []


async def test_youcam_client_keeps_the_raw_result_in_memory_for_the_probe():
    fake = use_verified_balance(FakeYouCam())
    async with make_client(live_settings(), fake) as client:
        await client.analyse_skin(IMAGE, "image/jpeg", SD_ACTIONS)
        assert client.last_result is not None and client.last_result["task_status"] == "success"


async def test_youcam_client_never_logs_key_urls_or_ids(caplog):
    caplog.set_level(logging.DEBUG)
    fake = FakeYouCam()
    fake.overrides[("POST", TASK)] = lambda r: httpx.Response(
        400, json={"status": 400, "error_code": "InvalidParameters"}
    )
    with pytest.raises(YouCamError) as err:
        await run(fake)
    for secret in (FAKE_KEY, UPLOAD_HOST, "file-123", "task-123", "Bearer"):
        assert secret not in caplog.text
        assert secret not in str(err.value)


# ------------------------------------------------------------------------------------- balance response
# Structure recorded on 31 Oct 2026: {"status": int, "results": [{id, type, amount, amount_dec, expiry}]}.
# All values below are synthetic.


async def test_balance_parses_the_verified_results_shape_using_amount_dec():
    assert await balance_from(verified_balance(amount_dec=750.25, amount=750)) == 750.25


async def test_balance_uses_integer_amount_when_amount_dec_is_absent():
    assert await balance_from(verified_balance(amount_dec=None, amount=640)) == 640.0


async def test_balance_sums_several_unit_batches():
    body = verified_balance(amount_dec=100.5)
    body["results"].append({"id": 7, "type": "ApiPaygToken", "amount": 20, "amount_dec": 20.25, "expiry": 1})
    assert await balance_from(body) == 120.75


@pytest.mark.parametrize(
    "body",
    [
        {"status": 200, "results": [{"id": 1, "type": "ApiPaygToken", "expiry": 1}]},
        {"status": 200, "results": []},
        {"status": 200},
        {"status": 200, "data": [{"type": "ApiPaygToken", "amount": 1000}]},
    ],
    ids=["missing-amounts", "empty-results", "missing-results", "old-guessed-data-wrapper"],
)
async def test_balance_missing_fields_fail_closed(body):
    with pytest.raises(YouCamError) as err:
        await balance_from(body)
    assert err.value.code == "credit_unknown"


@pytest.mark.parametrize(
    "body",
    [
        [{"amount": 10}],
        "1000",
        {"status": 200, "results": {"amount": 10}},
        {"status": 200, "results": ["10"]},
        {"status": 200, "results": [{"amount": "750"}]},
        {"status": 200, "results": [{"amount": True}]},
        {"status": 200, "results": [{"amount_dec": -5.0}]},
        {"status": 200, "results": [{"amount_dec": None, "amount": 10}]},
    ],
    ids=["array", "string", "results-object", "entry-string", "amount-text", "amount-bool", "negative", "dec-null"],
)
async def test_balance_unexpected_types_fail_closed(body):
    with pytest.raises(YouCamError) as err:
        await balance_from(body)
    assert err.value.code == "credit_unknown"


async def test_balance_unexpected_nested_objects_fail_closed():
    body = {"status": 200, "results": [{"amount_dec": {"value": 750.25}, "amount": {"value": 750}}]}
    with pytest.raises(YouCamError) as err:
        await balance_from(body)
    assert err.value.code == "credit_unknown"
    assert "amount_dec:object{value:float}" in (err.value.diagnostic or "")


async def test_balance_malformed_json_fails_closed_and_reports_only_its_size():
    raw = b'{"status": 200, "results": [ {"amount": 9'
    with pytest.raises(YouCamError) as err:
        await balance_from(None, raw=raw)
    assert err.value.code == "credit_unknown"
    assert err.value.diagnostic == f"non-JSON body ({len(raw)} bytes)"


async def test_balance_http_errors_keep_their_mapped_codes():
    with pytest.raises(YouCamError) as err:
        await balance_from({"status": 401, "error": "Invalid API key"}, status=401)
    assert err.value.code == "auth_failed"


async def test_balance_diagnostic_shows_structure_but_never_values(caplog):
    caplog.set_level(logging.DEBUG)
    sensitive = {
        "status": 200,
        "data": [
            {
                "token": "sk-live-SECRET-TOKEN-123",
                "download_url": "https://secret.example.test/file?sig=abc",
                "id": 98765,
                "amount": "750",
                "owner": {"email": "person@example.test"},
            }
        ],
    }
    with pytest.raises(YouCamError) as err:
        await balance_from(sensitive)
    diagnostic = err.value.diagnostic or ""
    expected = (
        "object{data:array[object{amount:str, download_url:str, id:int, owner:object{email:str}, token:str}],"
        " status:int}"
    )
    assert diagnostic == expected
    assert expected in caplog.text
    leaks = ("SECRET-TOKEN", "secret.example", "sig=abc", "98765", "750", "person@example", FAKE_KEY, "Bearer")
    for value in leaks:
        assert value not in caplog.text
        assert value not in diagnostic
        assert value not in str(err.value)


def test_describe_shape_hides_keys_that_look_like_data_and_limits_depth():
    deep = {"a": {"b": {"c": {"d": {"e": {"f": 1}}}}}}
    shape = describe_shape({"https://x.example/a": 1, "1" * 50: 2, "ok_key": deep})
    assert "x.example" not in shape and "1111" not in shape
    assert shape.count("<key>") == 2
    assert "ok_key:object{a:object{b:object{c:object{d:object{e:...}}}}}" in shape


def test_parse_balance_accepts_only_the_verified_shape():
    assert parse_balance(verified_balance(amount_dec=12.5)) == 12.5
    assert parse_balance({"status": 200, "data": {"amount": 12}}) is None
