import { useState } from "react";
import { Page } from "../components/Layout";
import { ArrowDisc, BAND_COLOR, BandBadge, BandBar, Button, Card, InfoNote, GlowArc, MicroLabel, ProductImage } from "../components/ui";
import { reportHeadline } from "../lib/reportHeadline";
import type { ConcernKey, Metric } from "../lib/types";
import { useApp } from "../state/AppState";

/** Plain-language meaning of each supported attribute (higher score = healthier-looking). */
const PLAIN: Record<ConcernKey, string> = {
  oiliness: "How much shine shows across the face.",
  moisture: "How hydrated and comfortable skin looks.",
  texture: "How smooth the skin surface looks.",
  pore: "How visible pores are.",
  acne: "How visible blemishes are.",
  redness: "How much visible redness there is.",
  age_spot: "How visible dark spots are.",
  wrinkle: "How visible fine lines are.",
  dark_circles: "How visible under-eye shadows are.",
};

/** Scale with the engine's band thresholds marked (60 = priority line, 75 = watch line). */
function ScaleGuide({ metric }: { metric: Metric }) {
  const score = metric.raw_score ?? 0;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative h-2 rounded-full bg-sand">
        <div className="band-seg h-full rounded-full" style={{ width: `${score}%`, background: BAND_COLOR[metric.band] }} />
        <span className="absolute -top-1 left-[60%] h-4 w-px bg-ink" aria-hidden="true" />
        <span className="absolute -top-1 left-[75%] h-4 w-px bg-ink" aria-hidden="true" />
      </div>
      <div className="relative h-4 text-[11px] text-muted" aria-hidden="true">
        <span className="absolute left-0">more visible</span>
        <span className="absolute left-[60%] -translate-x-1/2">60</span>
        <span className="absolute left-[75%] -translate-x-1/2">75</span>
        <span className="absolute right-0">less visible</span>
      </div>
    </div>
  );
}

export function Results() {
  const { analysis, go, preferences, catalogue } = useApp();
  const sorted = analysis
    ? [...analysis.metrics].sort((a, b) => (a.raw_score ?? 101) - (b.raw_score ?? 101))
    : [];
  const [selectedKey, setSelectedKey] = useState<ConcernKey | null>(null);

  if (!analysis) {
    return (
      <Page>
        <Card className="text-center">
          <p className="display text-3xl">No report yet</p>
          <p className="mt-2 text-sm text-muted">Add a selfie or choose a sample profile first.</p>
          <Button className="mt-5" onClick={() => go("selfie")}>
            Go to the selfie step
          </Button>
        </Card>
      </Page>
    );
  }

  const title = reportHeadline(analysis.metrics);
  const priorities = sorted.filter((m) => m.band === "priority");
  const counts = {
    priority: priorities.length,
    watch: sorted.filter((m) => m.band === "watch").length,
    good: sorted.filter((m) => m.band === "good").length,
  };
  const selected = sorted.find((m) => m.key === selectedKey) ?? sorted[0];
  // Catalogue products that target the selected attribute (labelled "from the edit", not "your ritual").
  const helper =
    selected &&
    [...(catalogue?.products ?? [])]
      .filter((p) => (p.targets[selected.key] ?? 0) > 0)
      .sort((a, b) => (b.targets[selected.key] ?? 0) - (a.targets[selected.key] ?? 0))[0];
  const profileName = analysis.profile_id ? analysis.profile_id.replace(/-/g, " ").replace(/^./, (c) => c.toUpperCase()) : "sample";
  const notMeasured = analysis.metrics.filter((m) => m.raw_score === null).length;

  return (
    <Page wide>
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-3">
          <MicroLabel className="text-sage animate-rise">{analysis.is_demo ? `Sample report · ${profileName}` : "Your skin report"}</MicroLabel>
          <h1 className="display text-balance text-[2.5rem] animate-rise [animation-delay:90ms] sm:text-6xl">{title.lead}
            <span className="italic text-terra-deep">{title.focus}</span>
            {title.tail}
          </h1>
        </div>
      </div>
      <div className="mt-5 animate-rise [animation-delay:150ms]">
        <InfoNote>
          {analysis.is_demo ? (
            <>
              These scores come from the {profileName} sample profile, not from an analysis of your photo. Scores run 1–100, and
              higher means healthier-looking skin.
            </>
          ) : (
            <>
              {analysis.notice}
              {notMeasured > 0 && ` ${notMeasured} attribute${notMeasured === 1 ? " wasn't" : "s weren't"} returned, so ${notMeasured === 1 ? "it shows" : "they show"} as not measured.`}
            </>
          )}
        </InfoNote>
      </div>

      <div className="mt-8 grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-12">
        {/* ------------------------------------------------ overview + priorities */}
        <aside className="flex min-w-0 flex-col gap-4 lg:col-span-4">
          <Card tone="peach" className="flex flex-col gap-4 animate-rise [animation-delay:200ms]">
            <MicroLabel className="text-ink-soft">
              Overview · {notMeasured > 0 ? `${sorted.length - notMeasured} of ${sorted.length}` : sorted.length} attributes read
            </MicroLabel>
            <BandBar counts={counts} />
            <div className="grid grid-cols-3 gap-2 text-xs">
              <span>
                <strong className="display block text-[34px]">{counts.priority}</strong>priorities
              </span>
              <span>
                <strong className="display block text-[34px]">{counts.watch}</strong>worth watching
              </span>
              <span>
                <strong className="display block text-[34px]">{counts.good}</strong>looking good
              </span>
            </div>
            <p className="text-[13px] leading-relaxed text-ink-soft">
              A count of attributes in each band, not a combined score: each attribute is measured on its own scale.
            </p>
          </Card>

          <Card className="animate-rise [animation-delay:280ms]">
            <MicroLabel className="text-sage">Your {priorities.length === 1 ? "priority" : `${priorities.length || "no"} priorities`}</MicroLabel>
            {priorities.length === 0 ? (
              <p className="mt-3 text-sm text-muted">Nothing stands out. Your ritual will focus on maintenance.</p>
            ) : (
              <ol className="mt-3">
                {priorities.map((m, i) => (
                  <li key={m.key} className={`border-t ${i === 0 ? "border-ink" : "border-line"}`}>
                    <button
                      type="button"
                      onClick={() => setSelectedKey(m.key)}
                      className="flex min-h-14 w-full items-center justify-between gap-3 text-left"
                    >
                      <span className="font-display text-xl">
                        0{i + 1} · {m.label}
                        {preferences.concerns.includes(m.key) && <span className="ml-1 text-sm text-terra-deep">★</span>}
                      </span>
                      <span className="font-semibold tabular-nums">{Math.round(m.raw_score ?? 0)}</span>
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </Card>

          <Card tone="ink" className="flex items-center gap-4 animate-rise [animation-delay:340ms]">
            <svg width="56" height="68" viewBox="0 0 64 78" aria-hidden="true" className="shrink-0">
              <ellipse cx="32" cy="39" rx="24" ry="32" fill="none" stroke="var(--color-peach)" strokeWidth="1.4" strokeDasharray="3 4" />
              <path d="M4 14V4h10M50 4h10v10M60 64v10H50M14 74H4V64" fill="none" stroke="var(--color-terra)" strokeWidth="2" />
            </svg>
            <span className="flex flex-col gap-1">
              <strong className="text-sm">Scores, not a face map</strong>
              <span className="text-[13px] leading-relaxed text-peach">
                {analysis.is_demo
                  ? "These scores belong to a sample profile. No photo was analysed, and nothing is mapped onto a face."
                  : "YouCam scored nine attributes from your photo, each from 1 to 100. GlowCue shows those scores; it doesn't map where they appear on your face."}
              </span>
            </span>
          </Card>
        </aside>

        {/* ------------------------------------------------ explorer + all nine */}
        <section className="flex min-w-0 flex-col gap-5 lg:col-span-8" aria-label="Attributes">
          <div role="tablist" aria-label="Choose an attribute" className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 lg:mx-0 lg:flex-wrap lg:px-0">
            {sorted.map((m) => {
              const on = m.key === selected?.key;
              return (
                <button
                  key={m.key}
                  type="button"
                  role="tab"
                  aria-selected={on}
                  onClick={() => setSelectedKey(m.key)}
                  className={`min-h-11 shrink-0 rounded-full border px-4 text-[13px] font-medium transition-colors ${
                    on ? "border-ink bg-ink text-surface" : "border-line-strong bg-surface hover:border-ink"
                  }`}
                >
                  {m.label} · {m.raw_score === null ? "—" : Math.round(m.raw_score)}
                </button>
              );
            })}
          </div>

          {selected && (
            <div key={selected.key} role="tabpanel" className="grid overflow-hidden rounded-[28px] bg-surface animate-fade md:grid-cols-[1.1fr_1fr]">
              <div className="flex flex-col gap-4 p-6 sm:p-8">
                <GlowArc score={selected.raw_score} band={selected.band} width={210} label={selected.label} />
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="font-display text-3xl">{selected.label}</h2>
                  <BandBadge band={selected.band} />
                </div>
                <p className="text-[15px] leading-relaxed text-ink-soft">
                  {PLAIN[selected.key]}{" "}
                  {selected.band === "priority"
                    ? "This is one of your three lowest scores, so your ritual leads with it."
                    : selected.band === "watch"
                      ? "Worth some attention; your ritual may include it if it fits your budget."
                      : selected.band === "good"
                        ? "Looking good: no need to target it."
                        : "Not measured in this result."}
                </p>
                {selected.raw_score !== null && <ScaleGuide metric={selected} />}
                <p className="text-xs text-muted">Priority = one of your three lowest and under 60 · Worth watching = under 75</p>
              </div>
              {helper && (
                <div className="relative min-h-[260px] bg-peach">
                  <ProductImage id={helper.id} alt={`${helper.name}, GlowCue studio render`} position="50% 38%" />
                  <div className="absolute inset-x-4 bottom-4 flex items-center justify-between gap-3 rounded-2xl bg-surface/90 px-4 py-3">
                    <span className="flex min-w-0 flex-col">
                      <MicroLabel className="text-sage">From the edit</MicroLabel>
                      <strong className="text-sm leading-snug">{helper.name}</strong>
                    </span>
                    <span className="shrink-0 text-xs text-muted">targets {selected.label.toLowerCase()}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          <Card className="flex flex-col gap-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="font-display text-2xl">All {sorted.length} at a glance</h2>
              <span className="text-xs text-muted">Numbers always shown · tones match the bands</span>
            </div>
            <ul className="grid grid-cols-3 gap-y-4 sm:grid-cols-5 lg:grid-cols-9">
              {sorted.map((m, i) => (
                <li key={m.key}>
                  <button
                    type="button"
                    onClick={() => setSelectedKey(m.key)}
                    className="flex min-h-11 w-full flex-col items-center gap-1 rounded-2xl py-1 text-xs text-ink-soft hover:bg-bg"
                  >
                    <GlowArc score={m.raw_score} band={m.band} width={78} label={m.label} delay={i * 70} />
                    <span>
                      {m.label}
                      {preferences.concerns.includes(m.key) && <span className="text-terra-deep"> ★</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap gap-4 text-xs text-ink-soft">
              {(["priority", "watch", "good"] as const).map((b) => (
                <span key={b} className="inline-flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: BAND_COLOR[b] }} />
                  {b === "priority" ? "Priority (top 3, under 60)" : b === "watch" ? "Worth watching (under 75)" : "Looking good"}
                </span>
              ))}
              {preferences.concerns.length > 0 && <span>★ your focus</span>}
            </div>
            <details className="rounded-2xl bg-bg p-4 text-sm">
              <summary className="min-h-11 cursor-pointer content-center font-medium">How to read this report</summary>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
                <li>
                  {analysis.is_demo
                    ? "These scores belong to the sample profile you chose, not to a reading of your face."
                    : "These scores come from YouCam's cosmetic analysis of the photo you shared."}
                </li>
                <li>Each attribute is scored 1–100 on its own; higher means healthier-looking skin.</li>
                <li>GlowCue gives cosmetic guidance only. It cannot diagnose or treat skin conditions.</li>
              </ul>
            </details>
          </Card>

          <div className="flex flex-col gap-4 rounded-[28px] bg-ink p-6 text-surface sm:flex-row sm:items-center sm:justify-between sm:p-8">
            <span className="display text-[28px] leading-tight sm:text-[32px]">
              Your ritual is <span className="italic text-peach">ready to build.</span>
            </span>
            <Button size="lg" onClick={() => go("routine")} className="pr-6">
              Build my ritual <ArrowDisc />
            </Button>
          </div>
        </section>
      </div>
    </Page>
  );
}
