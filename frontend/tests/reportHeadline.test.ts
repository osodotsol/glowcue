// Run with `npm test` (Node's built-in test runner; Node 24 runs TypeScript directly, no extra dependency).
// All scores are synthetic.
import assert from "node:assert/strict";
import { test } from "node:test";
import { bandCounts, headlineText, reportHeadline, type HeadlineMetric } from "../src/lib/reportHeadline.ts";

type Row = [HeadlineMetric["key"], HeadlineMetric["band"], number | null];
const report = (rows: Row[]): HeadlineMetric[] => rows.map(([key, band, raw_score]) => ({ key, band, raw_score }));

// The distribution seen in the first real analysis (3 priority / 2 watch / 4 good), with invented scores.
const OBSERVED_SHAPE = report([
  ["texture", "priority", 24], ["moisture", "priority", 39], ["oiliness", "priority", 50],
  ["pore", "watch", 59], ["dark_circles", "watch", 70],
  ["acne", "good", 80], ["age_spot", "good", 83], ["wrinkle", "good", 86], ["redness", "good", 97],
]); // prettier-ignore

// The synthetic test fixture's distribution (3 priority / 4 watch / 2 good).
const FIXTURE_SHAPE = report([
  ["oiliness", "priority", 41.3], ["dark_circles", "priority", 44.7], ["pore", "priority", 47.9],
  ["age_spot", "watch", 53.6], ["texture", "watch", 58.2], ["moisture", "watch", 66.8], ["acne", "watch", 72.4],
  ["redness", "good", 81], ["wrinkle", "good", 88.1],
]); // prettier-ignore

test("headline: observed real-analysis shape names three focus areas, led by the lowest score", () => {
  assert.equal(headlineText(OBSERVED_SHAPE), "Three areas to focus on, led by texture.");
});

test("headline: fixture shape (3 priority, 4 watch) is led by its lowest score", () => {
  assert.equal(headlineText(FIXTURE_SHAPE), "Three areas to focus on, led by shine.");
});

test("headline: never says 'comfortable' or 'balanced' while any area is a priority or worth watching", () => {
  for (const metrics of [OBSERVED_SHAPE, FIXTURE_SHAPE]) {
    const text = headlineText(metrics).toLowerCase();
    assert.ok(!text.includes("comfortable") && !text.includes("balanced"), text);
  }
});

test("headline: two priorities", () => {
  const m = report([["redness", "priority", 52], ["pore", "priority", 44], ["texture", "watch", 70], ["acne", "good", 90]]);
  assert.equal(headlineText(m), "Two areas to focus on, led by pores.");
});

test("headline: one priority is a single clear focus, regardless of watch areas", () => {
  const m = report([["moisture", "priority", 38], ["texture", "watch", 62], ["pore", "watch", 70], ["acne", "good", 88]]);
  assert.equal(headlineText(m), "One clear focus: hydration.");
});

test("headline: no priority, one area to watch", () => {
  const m = report([["age_spot", "watch", 68], ["acne", "good", 85], ["wrinkle", "good", 90]]);
  assert.equal(headlineText(m), "Looking good, with dark spots worth watching.");
});

test("headline: no priority, several areas to watch", () => {
  const m = report([["age_spot", "watch", 68], ["texture", "watch", 71], ["pore", "watch", 74], ["acne", "good", 85]]);
  assert.equal(headlineText(m), "Looking good, with three areas worth watching.");
});

test("headline: everything good reads as balanced", () => {
  const m = report([["acne", "good", 85], ["wrinkle", "good", 90], ["redness", "good", 95]]);
  assert.equal(headlineText(m), "Looking balanced, with nothing standing out.");
});

test("headline: unmeasured attributes are ignored and never invent a focus", () => {
  const m = report([["acne", "not_measured", null], ["wrinkle", "good", 90], ["redness", "good", 95]]);
  assert.equal(headlineText(m), "Looking balanced, with nothing standing out.");
  assert.equal(headlineText(report([["acne", "not_measured", null]])), "Your report is ready, but no attribute could be read.");
});

test("headline: italic focus phrase is returned separately", () => {
  assert.deepEqual(reportHeadline(OBSERVED_SHAPE), { lead: "Three areas to focus on, led by ", focus: "texture", tail: "." });
});

test("headline: band counts", () => {
  assert.deepEqual(bandCounts(OBSERVED_SHAPE), { priority: 3, watch: 2, good: 4, not_measured: 0 });
});

test("headline: uses only cosmetic wording", () => {
  const banned = ["diagnos", "treat", "cure", "disease", "condition", "acne"];
  const shapes = [OBSERVED_SHAPE, FIXTURE_SHAPE, report([["acne", "priority", 30]]), report([["acne", "watch", 70]])];
  for (const metrics of shapes) {
    const text = headlineText(metrics).toLowerCase();
    for (const word of banned) assert.ok(!text.includes(word), `${word} in "${text}"`);
  }
});
