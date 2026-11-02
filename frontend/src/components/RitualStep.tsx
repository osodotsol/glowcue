import { useState } from "react";
import { formatDelta, formatPrice } from "../lib/format";
import { CATEGORY_LABELS, type Product, type SelectedProduct, type Step } from "../lib/types";
import { MicroLabel, ProductImage } from "./ui";

interface RitualStepProps {
  step: Step;
  product: Product;
  selected: SelectedProduct;
  tone: "am" | "pm";
  showCoverage: boolean;
  productById: Map<string, Product>;
  onSwap: (current: string, replacement: string) => void;
}

/** One numbered ritual step: photo, how-to, the printed reason, and in-place alternatives. */
export function RitualStep({ step, product, selected, tone, showCoverage, productById, onSwap }: RitualStepProps) {
  const [open, setOpen] = useState(false);
  const dark = tone === "pm";
  const [first, ...more] = selected.receipts;
  return (
    <article
      style={{ viewTransitionName: `step-${tone}-${product.id}` }}
      className={`overflow-hidden rounded-[26px] animate-rise ${dark ? "bg-ink-soft text-surface" : "bg-surface"}`}
    >
      <div className="grid sm:grid-cols-[150px_1fr]">
        <div className="group relative h-52 overflow-hidden sm:h-full sm:min-h-[180px]">
          <ProductImage id={product.id} alt={`${product.name}, GlowCue studio render`} className="transition-transform duration-500 group-hover:scale-105" />
          <span className="display absolute top-1 left-3 text-[46px] text-ink">{step.order}</span>
          <div className="absolute inset-x-3 bottom-3 rounded-2xl bg-surface/88 px-3 py-2 text-ink sm:hidden">
            <MicroLabel className="text-sage">{CATEGORY_LABELS[product.category]}</MicroLabel>
            <p className="text-[15px] font-semibold">{product.name}</p>
          </div>
        </div>
        <div className="flex flex-col gap-2.5 p-4 sm:p-5">
          <div className="hidden sm:block">
            <MicroLabel className={dark ? "text-peach" : "text-sage"}>{CATEGORY_LABELS[product.category]}</MicroLabel>
            <p className="text-base font-semibold">{product.name}</p>
          </div>
          <p className={`text-[13px] leading-relaxed ${dark ? "text-peach" : "text-ink-soft"}`}>
            <strong className={dark ? "text-surface" : "text-ink"}>How:</strong> {step.instruction}
            {step.frequency !== "daily" && <> ({step.frequency})</>}
          </p>
          {step.note && <p className={`text-[13px] ${dark ? "text-peach" : "text-terra-ink"}`}>{step.note}</p>}
          {first && (
            <p className={`border-t pt-2.5 text-[13px] leading-relaxed ${dark ? "border-muted/50" : "border-sand"}`}>
              <span className={`font-display text-base italic ${dark ? "text-peach" : "text-terra-deep"}`}>Why · </span>
              {first.claim_text}
            </p>
          )}
          {more.length > 0 && (
            <details className="text-[13px]">
              <summary className="min-h-11 cursor-pointer content-center font-medium">More reasons ({more.length})</summary>
              <ul className={`space-y-1 pb-1 ${dark ? "text-peach" : "text-muted"}`}>
                {more.map((r) => (
                  <li key={r.claim_text}>{r.claim_text}</li>
                ))}
              </ul>
            </details>
          )}
          <div className="mt-auto flex items-center justify-between gap-3 pt-1">
            <strong className="tabular-nums">{formatPrice(product.price)}</strong>
            {selected.alternatives.length > 0 && (
              <button
                type="button"
                aria-expanded={open}
                onClick={() => setOpen((o) => !o)}
                className={`min-h-11 rounded-full border px-4 text-[13px] font-medium transition-colors ${
                  dark ? "border-peach/60 hover:bg-surface hover:text-ink" : "border-line-strong hover:border-ink"
                }`}
              >
                {open ? "Close" : `Swap · ${selected.alternatives.length}`}
              </button>
            )}
          </div>
        </div>
      </div>
      {open && (
        <div className={`flex gap-3 overflow-x-auto p-4 pt-0 animate-fade`}>
          {selected.alternatives.map((alt) => {
            const p = productById.get(alt.product_id);
            if (!p) return null;
            return (
              <div key={alt.product_id} className={`flex w-40 shrink-0 flex-col overflow-hidden rounded-2xl ${dark ? "bg-ink" : "border border-sand bg-bg"}`}>
                <div className="h-24">
                  <ProductImage id={p.id} alt="" />
                </div>
                <div className="flex flex-1 flex-col gap-1 p-3">
                  <strong className="text-xs leading-snug">{p.name}</strong>
                  <span className={`text-[11px] ${dark ? "text-peach" : "text-sage"}`}>
                    {formatDelta(alt.price_delta)}
                    {showCoverage && ` · ${Math.round(alt.coverage_pct)}% cover`}
                    {!alt.within_budget && " · over budget"}
                  </span>
                  <button
                    type="button"
                    onClick={() => onSwap(product.id, p.id)}
                    className={`mt-auto min-h-11 rounded-full text-xs font-semibold ${dark ? "bg-surface text-ink" : "bg-ink text-surface"}`}
                  >
                    Swap in
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}
