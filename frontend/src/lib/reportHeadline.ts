// The skin-report headline, derived only from the report's own bands so it can never contradict the scores shown.
// Pure (no React, no DOM) so it is unit-tested with Node's built-in test runner: `npm test`.
// Cosmetic wording only; the source of the data (demo or live) is labelled elsewhere and is never implied here.
import type { Band, ConcernKey } from "./types";

export interface HeadlineMetric {
  key: ConcernKey;
  band: Band;
  raw_score: number | null;
}

/** The headline in three parts; `focus` is the phrase the page sets in italics. */
export interface Headline {
  lead: string;
  focus: string;
  tail: string;
}

/** Short noun for each attribute, used in the headline. */
export const HEADLINE_NOUN: Record<ConcernKey, string> = {
  oiliness: "shine",
  moisture: "hydration",
  texture: "texture",
  pore: "pores",
  acne: "blemishes",
  redness: "redness",
  age_spot: "dark spots",
  wrinkle: "fine lines",
  dark_circles: "under-eyes",
};

const COUNT_WORD = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"];
const countWord = (n: number): string => COUNT_WORD[n] ?? String(n);

export function bandCounts(metrics: HeadlineMetric[]): Record<Band, number> {
  const counts: Record<Band, number> = { priority: 0, watch: 0, good: 0, not_measured: 0 };
  for (const m of metrics) counts[m.band] += 1;
  return counts;
}

/** Lowest raw score first (most visible), unmeasured last; key order breaks ties so the result is stable. */
function mostVisible(metrics: HeadlineMetric[], band: Band): HeadlineMetric | undefined {
  return metrics
    .filter((m) => m.band === band)
    .sort((a, b) => (a.raw_score ?? 101) - (b.raw_score ?? 101) || a.key.localeCompare(b.key))[0];
}

export function reportHeadline(metrics: HeadlineMetric[]): Headline {
  const counts = bandCounts(metrics);
  const measured = counts.priority + counts.watch + counts.good;
  if (measured === 0) {
    return { lead: "Your report is ready, but ", focus: "no attribute could be read", tail: "." };
  }
  if (counts.priority === 0 && counts.watch === 0) {
    return { lead: "Looking balanced, with ", focus: "nothing standing out", tail: "." };
  }
  if (counts.priority === 0) {
    if (counts.watch === 1) {
      const first = mostVisible(metrics, "watch");
      return { lead: "Looking good, with ", focus: HEADLINE_NOUN[first!.key], tail: " worth watching." };
    }
    return { lead: "Looking good, with ", focus: `${countWord(counts.watch).toLowerCase()} areas`, tail: " worth watching." };
  }
  const first = mostVisible(metrics, "priority")!;
  if (counts.priority === 1) {
    return { lead: "One clear focus: ", focus: HEADLINE_NOUN[first.key], tail: "." };
  }
  return { lead: `${countWord(counts.priority)} areas to focus on, led by `, focus: HEADLINE_NOUN[first.key], tail: "." };
}

export function headlineText(metrics: HeadlineMetric[]): string {
  const h = reportHeadline(metrics);
  return `${h.lead}${h.focus}${h.tail}`;
}
