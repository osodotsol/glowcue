"""The probe's save boundary: identifiers and URLs are removed from a COPY at save time, never from the original.

Offline only: the probe module is imported (its main() never runs) and YouCam is the MockTransport fake.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest
from tests.youcam_fakes import FIXTURE, FakeYouCam, live_settings, make_client, selfie_bytes

from app.services.normalize import SD_ACTIONS, normalise_items
from app.services.youcam_client import DELETE_PATH

_spec = importlib.util.spec_from_file_location(
    "probe_youcam", Path(__file__).resolve().parents[1] / "scripts" / "probe_youcam.py"
)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)  # type: ignore[union-attr]

ID_KEY = re.compile(r"^id$|_id$", re.IGNORECASE)

# Synthetic success response with identifiers at several levels (values invented; not a real response).
RESPONSE = {
    "task_status": "success",
    "task_id": "task-abc",
    "dst_id": "dst-xyz",
    "results": {
        "id": 77,
        "output": [
            {
                "type": "pore",
                "region": "whole",
                "raw_score": 47.9,
                "ui_score": 78,
                "mask_urls": ["https://masks.example.test/p.png"],
                "file_id": "f-1",
            },
            {"type": "pore", "region": "nose", "raw_score": 40.0, "ui_score": 70, "mask_urls": []},
            {"type": "all", "score": 61.5, "Request_ID": "r-9"},
            {"type": "skin_age", "score": 29},
        ],
        "meta": {"engine": "v2.1", "items": [{"Id": 5, "valid": True, "paid": False}]},
    },
}


def walk_keys(value: object) -> list[str]:
    if isinstance(value, dict):
        return [str(k) for k in value] + [k for v in value.values() for k in walk_keys(v)]
    if isinstance(value, list):
        return [k for v in value for k in walk_keys(v)]
    return []


def walk_strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [s for v in value.values() for s in walk_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in walk_strings(v)]
    return [value] if isinstance(value, str) else []


def scores_view(response: dict) -> list[tuple]:
    return [
        (i.get("type"), i.get("region"), i.get("raw_score"), i.get("ui_score"), i.get("score"))
        for i in response["results"]["output"]
    ]


def test_probe_sanitise_removes_identifiers_at_every_level():
    saved = probe.sanitise_for_saving(RESPONSE)
    assert not [k for k in walk_keys(saved) if ID_KEY.search(k)]
    for value in ("task-abc", "dst-xyz", "f-1", "r-9"):
        assert value not in json.dumps(saved)
    assert "id" not in saved["results"] and "Id" not in saved["results"]["meta"]["items"][0]


def test_probe_sanitise_keeps_types_scores_regions_and_metadata():
    saved = probe.sanitise_for_saving(RESPONSE)
    assert scores_view(saved) == scores_view(RESPONSE)  # types, regions, raw/ui/overall scores unchanged
    assert saved["task_status"] == "success"
    assert saved["results"]["meta"]["engine"] == "v2.1"
    assert saved["results"]["meta"]["items"] == [{"valid": True, "paid": False}]  # "valid"/"paid" are not ids


def test_probe_sanitise_still_removes_urls():
    saved = probe.sanitise_for_saving(RESPONSE)
    assert saved["results"]["output"][0]["mask_urls"] == "<removed>"
    assert not [s for s in walk_strings(saved) if s.startswith("http")]


def test_probe_sanitise_never_modifies_the_original():
    before = copy.deepcopy(RESPONSE)
    probe.sanitise_for_saving(RESPONSE)
    assert before == RESPONSE


def test_probe_save_outcome_writes_only_a_sanitised_copy(tmp_path):
    outcome = {"status": "success", "types": ["pore"], "glowcue_scores": {"pore": 47.9}, "result": RESPONSE}
    before = copy.deepcopy(outcome)
    path = probe.save_outcome(outcome, raw_dir=tmp_path)
    assert path.parent == tmp_path and path.name.startswith("probe-") and path.name.endswith(".raw.json")
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert not [k for k in walk_keys(saved) if ID_KEY.search(k)]
    assert saved["glowcue_scores"] == {"pore": 47.9} and scores_view(saved["result"]) == scores_view(RESPONSE)
    assert outcome == before  # the in-memory outcome (and the response inside it) is untouched


@pytest.mark.anyio
async def test_probe_task_id_is_used_for_deletion_before_the_sanitised_save(tmp_path):
    """Order of operations: analyse (task id in memory) -> delete with that id -> only then save a clean copy."""
    fake = FakeYouCam()
    fake.result = copy.deepcopy(FIXTURE["data"])
    fake.result.update({"task_id": "task-123", "dst_id": "dst-9"})
    fake.result["results"]["output"][0]["id"] = 555

    async with make_client(live_settings(), fake) as client:
        items = await client.analyse_skin(selfie_bytes(), "image/jpeg", SD_ACTIONS)
        original = client.last_result

    (delete,) = fake.calls("POST", DELETE_PATH)  # deletion already happened, with the in-memory task id
    assert json.loads(delete.content) == {"task_id": "task-123"}
    assert fake.requests[-1] is delete  # nothing was sent after the delete

    scores_before = normalise_items(items).scores
    snapshot = copy.deepcopy(original)
    path = probe.save_outcome({"status": "success", "result": original}, raw_dir=tmp_path)

    assert original == snapshot and original["task_id"] == "task-123"  # the original response still has its ids
    assert normalise_items(items).scores == scores_before  # analysis results unaffected by saving
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert not [k for k in walk_keys(saved) if ID_KEY.search(k)]
    assert scores_view(saved["result"]) == scores_view(original)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
