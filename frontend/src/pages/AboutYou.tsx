import type { ReactNode } from "react";
import { Button, Chip, MicroLabel, Portrait, ProductImage, SceneImage } from "../components/ui";
import { formatPrice } from "../lib/format";
import { CATEGORY_LABELS, type Category, type ConcernKey, type SkinType } from "../lib/types";
import { CONSULT_STAGES, useApp } from "../state/AppState";

const STAGES = ["Your skin", "Your preferences", "Your shelf", "Your budget"];
const MAX_FOCUS = 3;

const FEEL: { value: SkinType | null; label: string; hint: string; swatch: string }[] = [
  { value: "oily", label: "Shiny all over", hint: "oily", swatch: "bg-terra" },
  { value: "combination", label: "Shiny in the T-zone", hint: "combination", swatch: "bg-peach" },
  { value: "normal", label: "Comfortable", hint: "normal", swatch: "bg-sky" },
  { value: "dry", label: "Tight or dry", hint: "dry", swatch: "bg-line-strong" },
];

export const FOCUS_LABELS: Record<ConcernKey, string> = {
  pore: "Refined pores",
  dark_circles: "Less visible dark circles",
  age_spot: "Fewer visible dark spots",
  moisture: "Hydration",
  oiliness: "Less shine",
  texture: "Smooth texture",
  redness: "Calm redness",
  wrinkle: "Softer-looking wrinkles",
  acne: "Clear blemishes",
};

const SHELF: { category: Category; image: string }[] = [
  { category: "cleanser", image: "gc-cln-01" },
  { category: "moisturiser", image: "gc-moi-02" },
  { category: "sunscreen", image: "gc-spf-01" },
  { category: "serum", image: "gc-ser-02" },
];

const SIZES = [
  { value: "minimal", label: "Minimal", hint: "up to 4" },
  { value: "balanced", label: "Balanced", hint: "up to 6" },
  { value: "complete", label: "Complete", hint: "up to 8" },
] as const;

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

// ------------------------------------------------------------------ fields shared with the routine sidebar
function BudgetField({ dark = false }: { dark?: boolean }) {
  const { preferences: p, setPreferences, config } = useApp();
  const min = config?.budget_min ?? 5000;
  const max = config?.budget_max ?? 150000;
  return (
    <div className="flex flex-col gap-3">
      <label htmlFor="budget" className={`micro ${dark ? "text-peach" : "text-sage"}`}>
        Monthly budget
      </label>
      <output htmlFor="budget" className="display text-[3.4rem] leading-none sm:text-6xl">
        {formatPrice(p.budget)}
      </output>
      <input
        id="budget"
        type="range"
        min={min}
        max={max}
        step={500}
        value={p.budget}
        onChange={(e) => setPreferences({ budget: Number(e.target.value) })}
        className={`h-8 w-full ${dark ? "accent-terra" : "accent-terra-deep"}`}
      />
      <div className="flex flex-wrap gap-2" role="group" aria-label="Budget presets">
        {[15000, 30000, 60000].map((v) => (
          <button
            key={v}
            type="button"
            aria-pressed={p.budget === v}
            onClick={() => setPreferences({ budget: v })}
            className={`min-h-11 rounded-full px-4 text-sm font-medium transition-colors ${
              p.budget === v
                ? dark
                  ? "bg-peach text-ink"
                  : "bg-ink text-surface"
                : dark
                  ? "border border-muted text-surface"
                  : "border border-line-strong"
            }`}
          >
            ₦{v / 1000}k
          </button>
        ))}
      </div>
    </div>
  );
}

function SizeField() {
  const { preferences: p, setPreferences } = useApp();
  return (
    <div role="radiogroup" aria-label="Routine size" className="grid grid-cols-3 gap-1 rounded-2xl bg-sand p-1">
      {SIZES.map((s) => (
        <button
          key={s.value}
          type="button"
          role="radio"
          aria-checked={p.routine_size === s.value}
          onClick={() => setPreferences({ routine_size: s.value })}
          className={`min-h-14 rounded-xl text-sm transition-colors ${
            p.routine_size === s.value ? "bg-surface font-semibold shadow-[0_4px_12px_-6px_rgba(56,44,41,0.3)]" : "text-ink-soft"
          }`}
        >
          {s.label}
          <br />
          <span className="text-[11px] font-normal">{s.hint}</span>
        </button>
      ))}
    </div>
  );
}

/** Compact preference controls reused by the routine page ("Adjust your ritual"). */
export function PreferenceFields({ compact = false }: { compact?: boolean }) {
  const { preferences: p, setPreferences } = useApp();
  return (
    <div className={`flex flex-col ${compact ? "gap-6" : "gap-8"}`}>
      <BudgetField />
      <fieldset className="flex flex-col gap-2">
        <legend className="micro mb-2 text-sage">On my shelf</legend>
        <div className="flex flex-wrap gap-2">
          {SHELF.map(({ category }) => (
            <Chip key={category} selected={p.owned.includes(category)} onToggle={() => setPreferences({ owned: toggle(p.owned, category) })}>
              {CATEGORY_LABELS[category]}
            </Chip>
          ))}
        </div>
      </fieldset>
      <fieldset className="flex flex-col gap-2">
        <legend className="micro mb-2 text-sage">Respect</legend>
        <div className="flex flex-wrap gap-2">
          <Chip selected={p.fragrance_free} onToggle={() => setPreferences({ fragrance_free: !p.fragrance_free })}>
            Fragrance-free
          </Chip>
          <Chip selected={p.sensitive} onToggle={() => setPreferences({ sensitive: !p.sensitive })}>
            Sensitive skin
          </Chip>
        </div>
      </fieldset>
      <fieldset className="flex flex-col gap-2">
        <legend className="micro mb-2 text-sage">Ritual size</legend>
        <SizeField />
      </fieldset>
    </div>
  );
}

// ------------------------------------------------------------------ the four stages
function StageSkin() {
  const { preferences: p, setPreferences } = useApp();
  const full = p.concerns.length >= MAX_FOCUS;
  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <fieldset className="flex flex-col gap-2.5">
        <legend className="mb-3 text-[15px] font-semibold">By midday, my skin looks…</legend>
        {FEEL.map((f) => {
          const on = p.skin_type === f.value;
          return (
            <button
              key={f.label}
              type="button"
              aria-pressed={on}
              onClick={() => setPreferences({ skin_type: on ? null : f.value })}
              className={`flex min-h-14 items-center gap-3 rounded-2xl border px-4 text-left text-[15px] font-medium transition-colors ${
                on ? "border-ink bg-ink text-surface" : "border-line-strong bg-surface hover:border-ink"
              }`}
            >
              <span className={`h-5 w-5 shrink-0 rounded-full ${f.swatch}`} aria-hidden="true" />
              {f.label}
              <span className={`ml-auto text-xs ${on ? "text-peach" : "text-muted"}`}>{f.hint}</span>
            </button>
          );
        })}
        <button
          type="button"
          aria-pressed={p.skin_type === null}
          onClick={() => setPreferences({ skin_type: null })}
          className={`min-h-14 rounded-2xl border border-dashed px-4 text-left text-[15px] ${
            p.skin_type === null ? "border-ink bg-sand" : "border-line-strong"
          }`}
        >
          Not sure yet
        </button>
      </fieldset>
      <fieldset className="flex flex-col gap-2">
        <legend className="mb-3 text-[15px] font-semibold">
          I'd like to see more… <span className="font-normal text-muted">(up to {MAX_FOCUS}, gets extra weight)</span>
        </legend>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(FOCUS_LABELS) as ConcernKey[]).map((key) => {
            const on = p.concerns.includes(key);
            return (
              <Chip
                key={key}
                selected={on}
                onToggle={() => (on || !full) && setPreferences({ concerns: toggle(p.concerns, key) })}
                className={!on && full ? "opacity-50" : ""}
              >
                {FOCUS_LABELS[key]}
              </Chip>
            );
          })}
        </div>
        <p className="mt-3 text-[13px] leading-relaxed text-muted">
          These match the nine cosmetic attributes GlowCue can read. Your picks are weighted more heavily, even if your
          scores look good.
        </p>
      </fieldset>
    </div>
  );
}

function ToggleCard({ on, onChange, title, children }: { on: boolean; onChange: () => void; title: string; children: ReactNode }) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-4 rounded-[22px] p-5 transition-colors ${
        on ? "bg-ink text-surface" : "border border-line-strong bg-surface hover:border-ink"
      }`}
    >
      <input type="checkbox" checked={on} onChange={onChange} className="mt-0.5 h-6 w-6 shrink-0 accent-terra" />
      <span className="flex flex-col gap-1">
        <strong className="text-base">{title}</strong>
        <span className={`text-sm leading-relaxed ${on ? "text-peach" : "text-muted"}`}>{children}</span>
      </span>
    </label>
  );
}

function StagePreferences() {
  const { preferences: p, setPreferences } = useApp();
  return (
    <div className="flex max-w-xl flex-col gap-3">
      <ToggleCard on={p.fragrance_free} onChange={() => setPreferences({ fragrance_free: !p.fragrance_free })} title="Fragrance-free only">
        We'll leave out any product with added fragrance.
      </ToggleCard>
      <ToggleCard on={p.sensitive} onChange={() => setPreferences({ sensitive: !p.sensitive })} title="My skin is easily irritated">
        We'll skip strong actives such as retinol and acids, and tell you what we skipped.
      </ToggleCard>
      <p className="mt-2 text-xs leading-relaxed text-muted">
        Cosmetic guidance only. If you have a skin condition, a dermatologist knows best.
      </p>
    </div>
  );
}

function StageShelf() {
  const { preferences: p, setPreferences, productById } = useApp();
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {SHELF.map(({ category, image }) => {
          const on = p.owned.includes(category);
          return (
            <button
              key={category}
              type="button"
              aria-pressed={on}
              onClick={() => setPreferences({ owned: toggle(p.owned, category) })}
              className={`overflow-hidden rounded-[22px] bg-surface text-left transition-[border-color,transform] duration-200 active:scale-[0.98] ${
                on ? "border-2 border-ink" : "border border-line-strong hover:border-ink"
              }`}
            >
              <div className="relative h-28 sm:h-36">
                <ProductImage id={image} alt={productById.get(image)?.name ?? ""} position="50% 50%" />
                {on && (
                  <span className="absolute top-2 right-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-ink" aria-hidden="true">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-surface)" strokeWidth="3">
                      <path d="M5 12l4 4 10-10" />
                    </svg>
                  </span>
                )}
              </div>
              <span className="block px-3 py-2.5 text-[13px] font-medium">
                {CATEGORY_LABELS[category]}
                {on ? " · I have one" : ""}
              </span>
            </button>
          );
        })}
      </div>
      <div className="flex max-w-md flex-col gap-2">
        <span className="text-[15px] font-semibold">How many steps feel right?</span>
        <SizeField />
      </div>
    </div>
  );
}

function StageBudget() {
  const { preferences: p, go } = useApp();
  const feel = FEEL.find((f) => f.value === p.skin_type)?.label ?? "Not sure yet";
  const rows: [string, string, number][] = [
    ["Skin", feel, 1],
    ["Focus", p.concerns.map((c) => FOCUS_LABELS[c]).join(" · ") || "No preference", 1],
    ["Respect", [p.fragrance_free && "Fragrance-free", p.sensitive && "Sensitive skin"].filter(Boolean).join(" · ") || "Nothing specific", 2],
    ["Shelf", `${p.owned.map((c) => CATEGORY_LABELS[c]).join(", ") || "Nothing yet"} · ${p.routine_size}`, 3],
  ];
  return (
    <div className="grid gap-8 rounded-[28px] bg-ink p-6 text-surface sm:p-8 lg:grid-cols-2">
      <BudgetField dark />
      <div className="flex flex-col gap-1 rounded-[22px] bg-ink-soft p-5 text-sm">
        <MicroLabel className="mb-2 text-peach">Your consultation</MicroLabel>
        {rows.map(([k, v, stage]) => (
          <div key={k} className="flex items-baseline justify-between gap-4 border-b border-muted/40 py-2.5 last:border-0">
            <span className="text-peach">{k}</span>
            <span className="text-right">
              {v}
              <button type="button" onClick={() => go("about", stage)} className="ml-1 inline-flex min-h-11 min-w-11 items-center justify-center text-xs text-peach underline underline-offset-4">
                Edit
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

const TITLES: ReactNode[] = [
  <>
    Tell us how your skin <span className="italic text-terra-deep">feels.</span>
  </>,
  <>
    What should your products <span className="italic text-terra-deep">respect?</span>
  </>,
  <>
    What's already <span className="italic text-terra-deep">on your shelf?</span>
  </>,
  <>
    What would you like to <span className="italic text-terra-deep">spend</span> each month?
  </>,
];

export function AboutYou() {
  const { consultStage: stage, go } = useApp();
  const next = () => (stage < CONSULT_STAGES ? go("about", stage + 1) : go("selfie"));
  const back = () => (stage > 1 ? go("about", stage - 1) : go("landing"));

  return (
    <main className="mx-auto max-w-[1280px] md:grid md:grid-cols-[400px_1fr] md:gap-12 md:px-16 md:py-10">
      {/* desktop side panel: portrait + stage index */}
      <aside className="hidden flex-col gap-6 md:flex">
        <div className="h-[340px] overflow-hidden rounded-[180px_180px_24px_24px]">
          <Portrait
            slot="consultation"
            eager
            position="95% 40%"
            alt="Woman with a white towel wrapped on her hair, fingertips framing her face, against a soft teal backdrop"
          />
        </div>
        <nav aria-label="Consultation stages" className="rounded-[24px] bg-surface p-6">
          <MicroLabel className="text-sage">Your consultation</MicroLabel>
          <ol className="mt-4">
            {STAGES.map((name, i) => {
              const n = i + 1;
              const state = n < stage ? "done" : n === stage ? "current" : "todo";
              return (
                <li key={name} className={`border-t ${n === 1 ? "border-ink" : "border-line"}`}>
                  <button
                    type="button"
                    disabled={state === "todo"}
                    onClick={() => go("about", n)}
                    aria-current={state === "current" ? "step" : undefined}
                    className="flex min-h-14 w-full items-center gap-4 text-left disabled:cursor-default"
                  >
                    <span className={`display w-9 text-[26px] ${state === "current" ? "text-terra-deep" : "text-muted"}`}>0{n}</span>
                    <span className="flex flex-col">
                      <span className={state === "todo" ? "text-muted" : "font-semibold"}>{name}</span>
                      {state !== "todo" && <span className="text-xs text-muted">{state === "done" ? "Done · edit" : "In progress"}</span>}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>
      </aside>

      <section className="flex min-h-[calc(100dvh-72px)] flex-col md:min-h-0">
        {/* mobile photo band */}
        {stage === 1 && (
          <div className="relative h-[200px] overflow-hidden md:hidden">
            <Portrait
              slot="consultation"
              eager
              position="50% 30%"
              alt="Woman with a white towel wrapped on her hair, fingertips framing her face, against a soft teal backdrop"
              // The band is width-limited, so object-position cannot move the photo sideways; a slight zoom anchored
              // at the right edge brings her face (63% across the photo) to the centre without cropping the chin.
              className="origin-[100%_65%] scale-[1.2]"
            />
          </div>
        )}
        {stage === 2 && (
          <div className="h-[170px] overflow-hidden md:hidden">
            <SceneImage name="cream_swirl" alt="" />
          </div>
        )}

        <div className="flex flex-1 flex-col gap-6 px-4 pt-5 pb-6 md:px-0 md:pt-2">
          <div className="flex flex-col gap-2">
            <div className="grid grid-cols-4 gap-1.5" aria-hidden="true">
              {STAGES.map((_, i) => (
                <span key={i} className={`h-[3px] rounded-full transition-colors duration-500 ${i + 1 < stage ? "bg-ink" : i + 1 === stage ? "bg-terra-deep" : "bg-line-strong"}`} />
              ))}
            </div>
            <MicroLabel className="text-sage">
              Stage {stage} of {CONSULT_STAGES} · {STAGES[stage - 1]}
            </MicroLabel>
          </div>

          <div key={stage} className="flex flex-col gap-6 animate-rise">
            <h1 className="display text-[2.4rem] sm:text-6xl">{TITLES[stage - 1]}</h1>
            {stage === 1 && <StageSkin />}
            {stage === 2 && <StagePreferences />}
            {stage === 3 && <StageShelf />}
            {stage === 4 && <StageBudget />}
          </div>

          <div className="sticky bottom-0 mt-auto -mx-4 flex items-center gap-3 border-t border-line bg-bg/95 px-4 py-4 backdrop-blur md:static md:mx-0 md:border-t md:bg-transparent md:px-0 md:pt-6">
            <button
              type="button"
              onClick={back}
              aria-label={stage > 1 ? "Previous stage" : "Back to start"}
              className="inline-flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-ink transition-colors hover:bg-ink hover:text-surface"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M15 6l-6 6 6 6" />
              </svg>
            </button>
            <span className="hidden text-[13px] text-muted md:inline">Answers are kept in this browser session, not in an account.</span>
            <Button size="lg" onClick={next} className="flex-1 md:ml-auto md:flex-none">
              {stage < CONSULT_STAGES ? `Continue to ${STAGES[stage]?.toLowerCase() ?? "the next stage"}` : "Continue to selfie"}
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}

