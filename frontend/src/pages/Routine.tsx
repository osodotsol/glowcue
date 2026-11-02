import { useCallback, useState } from "react";
import { Page } from "../components/Layout";
import { RitualStep } from "../components/RitualStep";
import { ArrowDisc, Button, Card, CueMark, ErrorState, Loading, MicroLabel, Notice, SceneImage } from "../components/ui";
import { api } from "../lib/api";
import { formatPrice } from "../lib/format";
import { flyToBag, withTransition } from "../lib/motion";
import { CATEGORY_LABELS, CONCERN_LABELS, type Category, type RecommendationResult, type SelectedProduct, type Step } from "../lib/types";
import { useRemote } from "../lib/useRemote";
import { useApp } from "../state/AppState";
import { PreferenceFields } from "./AboutYou";

// Step positions, mirroring the engine's routine order (backend/app/engine/routine.py).
const STEP_RANK: Record<"am" | "pm", Partial<Record<Category, number>>> = {
  am: { cleanser: 0, serum: 2, eye: 3, moisturiser: 4, sunscreen: 9 },
  pm: { cleanser: 0, toner_exfoliant: 1, serum: 2, eye: 3, moisturiser: 4 },
};
// Owned categories with an unambiguous place in the routine. A serum could belong to either time of day, so an owned
// serum is not placed (a note explains); eye and exfoliant are not collected by the consultation.
const SHELF_SLOTS: Record<"am" | "pm", Category[]> = { am: ["cleanser", "moisturiser", "sunscreen"], pm: ["cleanser", "moisturiser"] };

type ColumnItem = { kind: "product"; step: Step; rank: number; seq: number } | { kind: "shelf"; category: Category; rank: number; seq: number };

/** A product the customer already owns, shown in its place but never analysed, checked or sold by GlowCue. */
function ShelfStep({ category, number, dark }: { category: Category; number: number; dark: boolean }) {
  const label = CATEGORY_LABELS[category].toLowerCase();
  return (
    <article
      aria-label={`Step ${number}: your own ${label}, from your shelf`}
      className={`flex gap-4 rounded-[26px] border border-dashed p-4 animate-rise ${dark ? "border-surface/30 text-surface" : "border-line-strong bg-surface/60"}`}
    >
      <span className={`display text-[46px] leading-none ${dark ? "text-surface" : "text-ink"}`}>{number}</span>
      <div className="flex flex-col gap-1">
        <MicroLabel className={dark ? "text-peach" : "text-sage"}>From your shelf</MicroLabel>
        <strong className="text-[15px]">Your own {label}</strong>
        <p className={`text-[13px] leading-relaxed ${dark ? "text-peach" : "text-ink-soft"}`}>
          {category === "sunscreen" ? "Keep it as the last morning step. " : "Keep using the one you have. "}
          GlowCue hasn&rsquo;t seen this product, so its ingredients and suitability aren&rsquo;t checked. It isn&rsquo;t added
          to your bag.
        </p>
      </div>
    </article>
  );
}

function RitualColumn({ result, time, onSwap }: { result: RecommendationResult; time: "am" | "pm"; onSwap: (a: string, b: string) => void }) {
  const { productById, preferences } = useApp();
  const selectedById = new Map<string, SelectedProduct>(result.selected.map((s) => [s.product_id, s]));
  const rank = STEP_RANK[time];
  // Merge the recommended steps (already in engine order) with owned-category steps at their usual position.
  const items: ColumnItem[] = [
    ...result.routine[time].map((step, seq): ColumnItem => {
      const category = productById.get(step.product_id)?.category;
      return { kind: "product", step, rank: (category && rank[category]) ?? 5, seq };
    }),
    ...SHELF_SLOTS[time]
      .filter((c) => preferences.owned.includes(c))
      .map((category, seq): ColumnItem => ({ kind: "shelf", category, rank: rank[category] ?? 5, seq: -1 - seq })),
  ].sort((a, b) => a.rank - b.rank || a.seq - b.seq);
  const steps = items;
  const dark = time === "pm";
  return (
    <section aria-label={dark ? "Evening ritual" : "Morning ritual"} className={`overflow-hidden rounded-[30px] ${dark ? "bg-ink text-surface" : "bg-sky"}`}>
      {dark ? (
        <div className="relative h-44 sm:h-52">
          <SceneImage name="night_still" alt="GlowCue evening products in warm low light" position="45% 62%" />
          <div className="absolute bottom-4 left-5 flex items-center gap-2.5">
            <CueMark variant="pm" size={26} />
            <span className="display text-[28px] text-surface">Good evening.</span>
          </div>
          <span className="absolute right-5 bottom-5 text-xs text-peach">{steps.length} steps</span>
        </div>
      ) : (
        <div className="flex items-center gap-2.5 px-5 pt-5">
          <CueMark variant="am" size={26} />
          <span className="display text-[28px]">Good morning.</span>
          <span className="ml-auto text-xs text-ink-soft">{steps.length} steps</span>
        </div>
      )}
      <div className="flex flex-col gap-3 p-4 sm:p-5">
        {steps.length === 0 && <p className="text-sm">No steps at this time of day.</p>}
        {steps.map((item, index) => {
          if (item.kind === "shelf") {
            return <ShelfStep key={`${time}-shelf-${item.category}`} category={item.category} number={index + 1} dark={dark} />;
          }
          const step = { ...item.step, order: index + 1 };
          const product = productById.get(step.product_id);
          const selected = selectedById.get(step.product_id);
          if (!product || !selected) return null;
          return (
            <RitualStep
              key={`${time}-${step.product_id}`}
              step={step}
              product={product}
              selected={selected}
              tone={time}
              showCoverage={result.mode === "targeted"}
              productById={productById}
              onSwap={onSwap}
            />
          );
        })}
      </div>
    </section>
  );
}

/** The budget decision in one sentence, from the server's actual numbers (never hardcoded). */
function BudgetSummary({ result }: { result: RecommendationResult }) {
  const budget = <strong className="font-semibold">{formatPrice(result.budget)}</strong>;
  const total = <strong className="font-semibold">{formatPrice(result.total)}</strong>;
  if (result.budget_status === "over") {
    return (
      <>
        No complete ritual fits your {budget} budget. The most affordable basic ritual costs {total}, which is{" "}
        {formatPrice(result.over_by)} more.
      </>
    );
  }
  const spare = result.budget - result.total;
  const left = spare > 0 ? <>, leaving {formatPrice(spare)} to spare</> : null;
  if (result.mode === "maintenance") {
    return (
      <>
        Your {budget} budget covers this {total} maintenance ritual{left}. Nothing in your report needs targeting.
      </>
    );
  }
  return (
    <>
      Your {budget} budget covers this {total} ritual{left}. It reaches{" "}
      <strong className="font-semibold">{Math.round(result.coverage_pct)}%</strong> of the concerns your report flagged.
    </>
  );
}

export function Routine() {
  const { analysis, preferences, setPreferences, productById, addToCart, setBagOpen, go } = useApp();
  const [time, setTime] = useState<"am" | "pm">("am");
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [attempt, setAttempt] = useState(0);

  const fetcher = useCallback(
    () => (analysis ? api.recommend(analysis, preferences) : Promise.reject(new Error("No analysis yet"))),
    [analysis, preferences],
  );
  const key = analysis ? `${analysis.analysis_id}|${JSON.stringify(preferences)}|${attempt}` : null;
  const { data: result, error, loading } = useRemote(key, fetcher, 300);

  if (!analysis) {
    return (
      <Page>
        <Card className="text-center">
          <p className="display text-3xl">We need a skin report first</p>
          <Button className="mt-5" onClick={() => go("selfie")}>
            Add a selfie or choose a profile
          </Button>
        </Card>
      </Page>
    );
  }

  function swap(current: string, replacement: string) {
    const slot = productById.get(current)?.category;
    const pinned = preferences.pinned.filter((id) => productById.get(id)?.category !== slot || slot === "serum");
    setPreferences({ pinned: [...pinned.filter((id) => id !== current), replacement] });
  }

  function addRitual() {
    if (!result) return;
    const visible = [...document.querySelectorAll("section[aria-label$='ritual'] article img")].find((i) => i.getBoundingClientRect().width > 0);
    flyToBag(visible);
    addToCart(result.selected.map((s) => s.product_id));
    window.setTimeout(() => setBagOpen(true), 420);
  }

  const summary = [formatPrice(preferences.budget), preferences.routine_size, preferences.fragrance_free && "fragrance-free", preferences.sensitive && "sensitive"]
    .filter(Boolean)
    .join(" · ");

  return (
    <Page wide>
      <div className="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[300px_minmax(0,1fr)]">
        {/* ------------------------------------------------ preferences: sidebar on desktop, collapsible on mobile */}
        <aside className="min-w-0 lg:sticky lg:top-28 lg:self-start">
          <div className="rounded-[26px] bg-surface p-5 lg:p-6">
            <button
              type="button"
              aria-expanded={adjustOpen}
              aria-controls="adjust-panel"
              onClick={() => setAdjustOpen((o) => !o)}
              className="flex min-h-12 w-full items-center justify-between gap-3 text-left lg:hidden"
            >
              <span className="flex flex-col">
                <strong className="text-[15px]">Adjust your ritual</strong>
                <span className="text-xs text-muted capitalize">{summary}</span>
              </span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" className={`transition-transform ${adjustOpen ? "rotate-180" : ""}`}>
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>
            <h2 className="mb-5 hidden font-display text-[22px] lg:block">Adjust your ritual</h2>
            <div id="adjust-panel" className={`${adjustOpen ? "mt-5 block animate-fade" : "hidden"} lg:mt-0 lg:block`}>
              <PreferenceFields compact />
              {preferences.pinned.length > 0 && (
                <Button variant="ghost" className="mt-4 underline" onClick={() => setPreferences({ pinned: [] })}>
                  Undo my swaps
                </Button>
              )}
              <p className="mt-4 text-xs leading-relaxed text-muted">Changes update your ritual instantly.</p>
            </div>
          </div>
        </aside>

        <section aria-live="polite" aria-busy={loading} className="flex min-w-0 flex-col gap-5">
          <div className="flex flex-col gap-3">
            <MicroLabel className="text-sage">Your edition · ritual</MicroLabel>
            <h1 className="display text-balance text-[2.5rem] sm:text-6xl">
              {result ? `${result.selected.length} products.` : "Your ritual."}{" "}
              <span className="italic text-terra-deep">{result?.mode === "maintenance" ? "Simple and steady." : "Each with a reason."}</span>
            </h1>
          </div>

          {error && <ErrorState message={error} onRetry={() => setAttempt((n) => n + 1)} />}
          {!result && loading && <Loading label="Building your ritual…" />}

          {result && (
            <div className={`flex flex-col gap-5 transition-opacity duration-300 ${loading ? "opacity-60" : ""}`}>
              <Card className="flex flex-col gap-4" aria-label="Budget decision">
                <p className="text-[15px] leading-relaxed sm:text-base" data-testid="budget-summary">
                  <BudgetSummary result={result} />
                </p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <p className="display text-[30px] sm:text-4xl">{result.mode === "maintenance" ? "—" : `${Math.round(result.coverage_pct)}%`}</p>
                    <p className="text-[11px] text-muted">{result.mode === "maintenance" ? "maintenance ritual" : "of flagged concerns"}</p>
                  </div>
                  <div>
                    <p className="display text-[30px] sm:text-4xl">{result.selected.length}</p>
                    <p className="text-[11px] text-muted">new products</p>
                  </div>
                  <div>
                    <p className={`display text-[30px] sm:text-4xl ${result.budget_status === "over" ? "text-terra-ink" : ""}`}>{formatPrice(result.total)}</p>
                    <p className="text-[11px] text-muted">of {formatPrice(result.budget)}</p>
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <div className="h-1.5 overflow-hidden rounded-full bg-sand" aria-hidden="true">
                    <div
                      className={`h-full rounded-full transition-[width] duration-500 ${result.budget_status === "over" ? "bg-terra-deep" : "bg-sage"}`}
                      style={{ width: `${Math.min(100, (100 * result.total) / result.budget)}%` }}
                    />
                  </div>
                  <p className={`self-end text-xs tabular-nums ${result.budget_status === "over" ? "text-terra-ink" : "text-ink-soft"}`}>
                    {result.budget_status === "over" ? `${formatPrice(result.over_by)} over budget` : `${formatPrice(result.budget - result.total)} left`}
                  </p>
                </div>
                {result.unaddressed.length > 0 && (
                  <p className="border-t border-line pt-3 text-[13px] leading-relaxed text-ink-soft">
                    <strong className="font-semibold text-ink">Not covered at this budget:</strong>{" "}
                    {result.unaddressed.map((k) => CONCERN_LABELS[k]).join(", ")}. A larger budget or ritual size may help; our
                    catalogue may also have nothing for it.
                  </p>
                )}
              </Card>

              {result.budget_status === "over" && (
                <Notice tone="warn">
                  This basic ritual is {formatPrice(result.over_by)} over your budget.{" "}
                  <button type="button" className="min-h-11 font-semibold underline" onClick={() => setPreferences({ budget: Math.ceil(result.total / 500) * 500 })}>
                    Increase budget to {formatPrice(Math.ceil(result.total / 500) * 500)}
                  </button>{" "}
                  or mark products you already own.
                </Notice>
              )}
              {preferences.owned.includes("serum") && (
                <Notice>
                  Your own serum isn&rsquo;t placed in this ritual: use it as its label directs. GlowCue hasn&rsquo;t checked how it
                  combines with the new products.
                </Notice>
              )}
              {result.warnings
                .filter((w) => !w.startsWith("Your budget") && !w.startsWith("You already own a sunscreen")) // shown as a shelf step
                .map((w) => (
                  <Notice key={w}>{w}</Notice>
                ))}

              {/* mobile: AM/PM tabs; desktop: both rituals side by side */}
              <div role="tablist" aria-label="Time of day" className="grid grid-cols-2 rounded-full bg-sand p-1 lg:hidden">
                {(["am", "pm"] as const).map((t) => (
                  <button
                    key={t}
                    role="tab"
                    type="button"
                    aria-selected={time === t}
                    onClick={() => withTransition(() => setTime(t))}
                    className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-full text-sm transition-colors ${time === t ? "bg-surface font-semibold shadow-sm" : "text-ink-soft"}`}
                  >
                    <CueMark variant={t} size={18} />
                    {t === "am" ? "Morning" : "Evening"} · {result.routine[t].length}
                  </button>
                ))}
              </div>
              <div className="lg:hidden" key={time}>
                <RitualColumn result={result} time={time} onSwap={swap} />
              </div>
              <div className="hidden items-start gap-5 lg:grid lg:grid-cols-2">
                <RitualColumn result={result} time="am" onSwap={swap} />
                <RitualColumn result={result} time="pm" onSwap={swap} />
              </div>

              {(result.skipped_owned.length > 0 || result.excluded.length > 0) && (
                <details className="rounded-[22px] bg-surface p-5 text-sm">
                  <summary className="min-h-11 cursor-pointer content-center font-medium">What we left out and why</summary>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
                    {result.skipped_owned.map((c) => (
                      <li key={c}>{CATEGORY_LABELS[c]}: you already own one.</li>
                    ))}
                    {result.excluded.map((e) => (
                      <li key={e}>{e}</li>
                    ))}
                  </ul>
                </details>
              )}

              <div className="sticky bottom-24 z-30 flex items-center gap-3 rounded-[24px] bg-surface p-2.5 pl-5 shadow-[0_20px_40px_-20px_rgba(56,44,41,0.45)] md:bottom-4">
                <span className="flex flex-col">
                  <span className="text-[11px] text-muted">{result.selected.length} products</span>
                  <strong className="text-lg tabular-nums">{formatPrice(result.total)}</strong>
                </span>
                <Button size="lg" onClick={addRitual} className="ml-auto pr-6">
                  Add ritual to bag <ArrowDisc />
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </Page>
  );
}
