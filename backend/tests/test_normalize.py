"""YouCam output -> GlowCue analysis mapping (pure), and compatibility with the recommendation engine."""

from __future__ import annotations

from tests.youcam_fakes import FIXTURE

from app.engine import recommend
from app.models import MetricInput, Preferences, RecommendationRequest
from app.services.catalogue import get_catalogue
from app.services.normalize import SD_ACTIONS, YOUCAM_TO_CONCERN, build_live_analysis, normalise_items
from app.services.youcam_client import OutputItem


def items(raw: list[dict] | None = None) -> list[OutputItem]:
    return [OutputItem.model_validate(i) for i in (raw if raw is not None else FIXTURE["data"]["results"]["output"])]


def test_normalize_requests_exactly_the_nine_sd_actions():
    assert set(SD_ACTIONS) == {
        "pore", "dark_circle_v2", "age_spot", "moisture", "oiliness", "texture", "redness", "wrinkle", "acne",
    }  # fmt: skip
    assert len(SD_ACTIONS) == 9 and "skin_type" not in SD_ACTIONS
    assert not any(a.startswith("hd_") for a in SD_ACTIONS)


def test_normalize_maps_all_nine_attributes_to_the_existing_keys():
    scores = normalise_items(items()).scores
    assert set(scores) == set(YOUCAM_TO_CONCERN.values())
    assert scores["dark_circles"] == 44.7  # from dark_circle_v2
    assert scores["pore"] == 47.9 and scores["age_spot"] == 53.6 and scores["acne"] == 72.4


def test_normalize_uses_raw_score_never_ui_score():
    scores = normalise_items(items()).scores
    raw = {i["type"]: i for i in FIXTURE["data"]["results"]["output"] if "raw_score" in i}
    assert scores["oiliness"] == raw["oiliness"]["raw_score"] != raw["oiliness"]["ui_score"]


def test_normalize_marks_missing_attributes_not_measured_without_inventing_scores():
    partial = [i for i in FIXTURE["data"]["results"]["output"] if i["type"] not in ("acne", "redness")]
    normalised = normalise_items(items(partial))
    assert normalised.scores["acne"] is None and normalised.scores["redness"] is None
    analysis = build_live_analysis("live-x", normalised)
    by_key = {m.key: m for m in analysis.metrics}
    assert by_key["acne"].raw_score is None and by_key["acne"].band == "not_measured"
    assert by_key["acne"].ui_score is None


def test_normalize_ignores_unknown_and_overall_types():
    extra = [*FIXTURE["data"]["results"]["output"], {"type": "brand_new_metric", "raw_score": 12}]
    normalised = normalise_items(items(extra))
    assert normalised.ignored_types == ("all", "brand_new_metric", "resize_image", "skin_age")
    assert "brand_new_metric" not in normalised.scores


def test_normalize_prefers_the_whole_face_item_when_regions_are_returned():
    raw = [
        {"type": "pore", "region": "nose", "raw_score": 20},
        {"type": "pore", "region": "whole", "raw_score": 70},
        {"type": "pore", "region": "cheek", "raw_score": 30},
    ]
    assert normalise_items(items(raw)).scores["pore"] == 70


def test_normalize_treats_out_of_range_or_missing_scores_as_not_measured():
    raw = [
        {"type": "pore", "raw_score": 0},
        {"type": "acne", "raw_score": 140},
        {"type": "texture"},
        {"type": "wrinkle", "raw_score": 1},
        {"type": "moisture", "raw_score": 100},
    ]
    scores = normalise_items(items(raw)).scores
    assert scores["pore"] is None and scores["acne"] is None and scores["texture"] is None
    assert scores["wrinkle"] == 1 and scores["moisture"] == 100


def test_normalize_builds_an_honestly_labelled_live_analysis():
    analysis = build_live_analysis("live-abc", normalise_items(items()))
    assert analysis.mode == "live" and analysis.is_demo is False and analysis.profile_id is None
    assert "YouCam" in analysis.notice and "not medical advice" in analysis.notice
    assert "demo" not in analysis.notice.lower() and "demo" not in analysis.provider.lower()
    assert analysis.skin_type is None
    bands = {m.key: m.band for m in analysis.metrics}
    assert bands["oiliness"] == "priority" and bands["wrinkle"] == "good"


def test_normalize_live_result_feeds_the_existing_recommendation_engine():
    partial = [i for i in FIXTURE["data"]["results"]["output"] if i["type"] != "acne"]
    analysis = build_live_analysis("live-abc", normalise_items(items(partial)))
    request = RecommendationRequest(
        metrics=[MetricInput(key=m.key, raw_score=m.raw_score) for m in analysis.metrics],
        skin_type=analysis.skin_type,
        preferences=Preferences(budget=30000, skin_type="oily"),
    )
    result = recommend(request, get_catalogue().products)
    assert result.selected and result.routine.am and result.routine.pm
    assert {p.key for p in result.priorities if p.band == "priority"} <= {"oiliness", "dark_circles", "pore"}
    assert all(p.key != "acne" or p.band in ("not_measured", "watch") for p in result.priorities)


def test_normalize_fixture_mirrors_the_verified_v21_success_structure():
    """The synthetic fixture keeps the structure verified live on 1 Nov 2026 (docs/YOUCAM_API.md 6.11)."""
    import json
    import re

    data = FIXTURE["data"]
    assert data["task_status"] == "success" and data["error"] is None
    output = data["results"]["output"]
    concerns = [i for i in output if i["type"] in YOUCAM_TO_CONCERN]
    assert [i["type"] for i in output] == [
        "texture", "pore", "oiliness", "age_spot", "redness", "acne", "dark_circle_v2", "moisture", "wrinkle",
        "all", "skin_age", "resize_image",
    ]  # fmt: skip
    for item in concerns:
        assert set(item) == {"type", "raw_score", "ui_score", "mask_urls", "url"}
        assert isinstance(item["raw_score"], float) and isinstance(item["ui_score"], int)
        assert isinstance(item["mask_urls"], list) and "region" not in item  # SD returns no region
    by_type = {i["type"]: i for i in output}
    assert isinstance(by_type["all"]["score"], float) and isinstance(by_type["skin_age"]["score"], int)
    assert set(by_type["resize_image"]) == {"type", "mask_urls", "url"}
    text = json.dumps(FIXTURE)
    assert "http" not in text and not re.search(r'"(id|[A-Za-z]*_id)"\s*:', text, re.IGNORECASE)
    assert "SYNTHETIC" in FIXTURE["_note"]


def test_normalize_ignores_the_undocumented_url_fields_and_null_error():
    normalised = normalise_items(items())
    assert all(v is not None for v in normalised.scores.values())  # all nine measured
    assert normalised.ignored_types == ("all", "resize_image", "skin_age")
