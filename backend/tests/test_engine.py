"""Recommendation engine tests: the invariants in .claude/skills/recommendation-engine and spec 9.4 edge cases."""

from __future__ import annotations

import pytest

from app.engine import recommend
from app.engine.concerns import assess, weights
from app.engine.optimiser import SIZE_LIMIT
from app.models import MetricInput, Preferences, RecommendationRequest
from app.services.analysis.demo import DemoAnalysisProvider
from app.services.catalogue import get_catalogue, products_by_id

CATALOGUE = get_catalogue().products
BY_ID = products_by_id()


def metrics_for(profile_id: str) -> list[MetricInput]:
    analysis = DemoAnalysisProvider().analyse_profile(profile_id)
    return [MetricInput(key=m.key, raw_score=m.raw_score) for m in analysis.metrics]


def run(profile: str = "shine-prone", skin_type: str | None = None, **prefs):
    prefs.setdefault("budget", 30000)
    request = RecommendationRequest(metrics=metrics_for(profile), skin_type=skin_type, preferences=Preferences(**prefs))
    return recommend(request, CATALOGUE)


def chosen(result) -> list:
    return [BY_ID[s.product_id] for s in result.selected]


# ----------------------------------------------------------------------------- semantics and priorities
def test_lower_raw_score_means_more_visible_concern():
    states = assess([MetricInput(key="oiliness", raw_score=30), MetricInput(key="moisture", raw_score=90)], [])
    by_key = {s.key: s for s in states}
    assert by_key["oiliness"].band == "priority" and by_key["oiliness"].severity == 70
    assert by_key["moisture"].band == "good"


def test_bands_priority_needs_top3_and_below_60_watch_below_75():
    scores = {"oiliness": 20, "pore": 30, "acne": 40, "texture": 50, "moisture": 74, "redness": 80}
    states = {s.key: s.band for s in assess([MetricInput(key=k, raw_score=v) for k, v in scores.items()], [])}
    assert states == {
        "oiliness": "priority",
        "pore": "priority",
        "acne": "priority",
        "texture": "watch",  # below 60 but not in the top 3
        "moisture": "watch",
        "redness": "good",
    }


def test_missing_metric_is_not_measured_and_excluded_from_weights():
    states = assess([MetricInput(key="oiliness", raw_score=40), MetricInput(key="pore", raw_score=None)], [])
    assert {s.key: s.band for s in states}["pore"] == "not_measured"
    assert "pore" not in weights(states)


def test_weights_sum_to_one_over_active_concerns():
    w = weights(assess(metrics_for("uneven-tone"), []))
    assert abs(sum(w.values()) - 1) < 1e-9
    assert set(w) == {"age_spot", "dark_circles", "texture", "moisture", "oiliness", "pore", "wrinkle"}


def test_self_reported_concern_is_promoted_and_weighted_more():
    metrics = [MetricInput(key="oiliness", raw_score=50), MetricInput(key="wrinkle", raw_score=90)]
    plain = weights(assess(metrics, []))
    reported = weights(assess(metrics, ["wrinkle"]))
    assert "wrinkle" not in plain
    assert reported["wrinkle"] > 0
    assert {s.key: s for s in assess(metrics, ["wrinkle"])}["wrinkle"].self_reported


def test_self_reported_concern_appears_in_priorities_with_explanation():
    result = run("balanced", concerns=["dark_circles"])
    priority = next(p for p in result.priorities if p.key == "dark_circles")
    assert priority.band == "watch" and priority.self_reported
    assert "you told us" in priority.why_text.lower()
    assert any(BY_ID[s.product_id].category == "eye" for s in result.selected)


# ----------------------------------------------------------------------------- slots, budget, determinism
@pytest.mark.parametrize("profile", ["shine-prone", "dry-sensitive", "uneven-tone", "balanced"])
@pytest.mark.parametrize("budget", [15000, 30000, 60000])
@pytest.mark.parametrize("size", ["minimal", "balanced", "complete"])
def test_slot_rules_budget_and_size_always_hold(profile, budget, size):
    result = run(profile, budget=budget, routine_size=size)
    products = chosen(result)
    count = {c: sum(p.category == c for p in products) for c in ("cleanser", "moisturiser", "sunscreen")}
    assert count == {"cleanser": 1, "moisturiser": 1, "sunscreen": 1}
    assert sum(p.category == "serum" for p in products) <= 2
    assert sum(p.category == "eye" for p in products) <= 1
    assert sum(p.category == "toner_exfoliant" for p in products) <= 1
    assert len(products) <= SIZE_LIMIT[size]
    assert result.total == sum(p.price for p in products)
    if result.budget_status == "within":
        assert result.total <= budget and result.over_by == 0


def test_same_input_gives_the_same_output():
    assert run("uneven-tone").model_dump() == run("uneven-tone").model_dump()


def test_bigger_budget_never_lowers_coverage():
    covs = [run("uneven-tone", budget=b, routine_size="complete").coverage_pct for b in (15000, 30000, 60000, 120000)]
    assert covs == sorted(covs)


def test_infeasible_budget_returns_cheapest_core_marked_over():
    result = run("shine-prone", budget=1000)
    assert result.budget_status == "over"
    assert result.over_by == result.total - 1000 > 0
    assert {BY_ID[s.product_id].category for s in result.selected} == {"cleanser", "moisturiser", "sunscreen"}
    assert any("budget is below" in w for w in result.warnings)


def test_balanced_skin_gets_a_maintenance_routine_of_the_core_three():
    result = run("balanced")
    assert result.mode == "maintenance"
    assert sorted(BY_ID[s.product_id].category for s in result.selected) == ["cleanser", "moisturiser", "sunscreen"]
    assert result.unaddressed == []


# ----------------------------------------------------------------------------- hard filters
def test_owned_categories_are_skipped():
    result = run("shine-prone", owned=["cleanser", "sunscreen"])
    categories = {BY_ID[s.product_id].category for s in result.selected}
    assert "cleanser" not in categories and "sunscreen" not in categories
    assert result.skipped_owned == ["cleanser", "sunscreen"]
    assert any("own a sunscreen" in w for w in result.warnings)


def test_owning_all_core_products_gives_a_treatment_only_routine():
    result = run("uneven-tone", owned=["cleanser", "moisturiser", "sunscreen"], budget=40000)
    assert result.selected and all(s.slot in ("serum", "eye", "toner_exfoliant") for s in result.selected)


def test_fragrance_free_excludes_fragranced_products():
    result = run("balanced", fragrance_free=True)
    assert all(p.fragrance_free for p in chosen(result))
    assert any("fragrance" in e for e in result.excluded)


def test_sensitive_skin_excludes_strong_actives_with_a_note():
    result = run("uneven-tone", sensitive=True, budget=60000, routine_size="complete")
    assert all(p.sensitive_ok for p in chosen(result))
    assert any("Retinol" in e and "sensitive" in e for e in result.excluded)


def test_redness_priority_triggers_the_gentle_filter_even_without_the_sensitive_flag():
    result = run("dry-sensitive")
    assert all(p.sensitive_ok for p in chosen(result))
    assert any("redness" in e for e in result.excluded)


def test_pinned_product_is_always_included():
    result = run("shine-prone", pinned=["gc-cln-01"])
    assert "gc-cln-01" in {s.product_id for s in result.selected}


# ----------------------------------------------------------------------------- routine rules
def _all_results():
    for profile in ("shine-prone", "dry-sensitive", "uneven-tone", "balanced"):
        for budget in (30000, 80000):
            yield run(profile, budget=budget, routine_size="complete")


def test_sunscreen_is_last_in_the_morning_and_never_at_night():
    for result in _all_results():
        am_cats = [BY_ID[s.product_id].category for s in result.routine.am]
        pm_cats = [BY_ID[s.product_id].category for s in result.routine.pm]
        assert am_cats[-1] == "sunscreen"
        assert "sunscreen" not in pm_cats


def test_vitamin_c_am_only_and_retinol_and_acids_pm_only():
    for result in _all_results():
        am = [BY_ID[s.product_id] for s in result.routine.am]
        pm = [BY_ID[s.product_id] for s in result.routine.pm]
        assert not any({"retinoid", "aha"} & set(p.actives) for p in am)
        assert not any("vitc" in p.actives for p in pm)


def test_retinol_and_exfoliant_together_get_the_alternate_nights_rule():
    result = run("uneven-tone", pinned=["gc-ser-04", "gc-exf-01"], budget=80000, routine_size="complete")
    pm = {s.product_id: s for s in result.routine.pm}
    assert "alternate nights" in pm["gc-ser-04"].note.lower()
    assert "alternate nights" in pm["gc-exf-01"].note.lower()
    assert any("Alternate nights" in w for w in result.warnings)


def test_steps_are_numbered_in_order():
    for result in _all_results():
        for steps in (result.routine.am, result.routine.pm):
            assert [s.order for s in steps] == list(range(1, len(steps) + 1))


# ----------------------------------------------------------------------------- explanations and alternatives
def test_every_selected_product_has_a_receipt_quoting_score_and_ingredient():
    for result in _all_results():
        for sel in result.selected:
            assert sel.receipts, sel.product_id
            for r in sel.receipts:
                if r.concern_key is not None and r.metric_raw_score is not None:
                    assert f"{r.metric_raw_score:.0f}/100" in r.claim_text
                    assert r.ingredient in r.claim_text


def test_sunscreen_gets_the_protection_receipt():
    for result in _all_results():
        spf = next(s for s in result.selected if s.slot == "sunscreen")
        assert any("protects the results" in r.claim_text for r in spf.receipts)


def test_alternatives_are_same_category_and_never_already_selected():
    result = run("shine-prone", budget=60000)
    selected = {s.product_id for s in result.selected}
    for sel in result.selected:
        for alt in sel.alternatives:
            assert BY_ID[alt.product_id].category == sel.slot
            assert alt.product_id not in selected
            assert alt.price_delta == BY_ID[alt.product_id].price - BY_ID[sel.product_id].price


def test_unaddressed_concerns_are_reported_honestly():
    result = run("uneven-tone", budget=20000, routine_size="minimal")
    covered = {c for p in chosen(result) for c in p.targets}
    assert set(result.unaddressed).isdisjoint(covered)
