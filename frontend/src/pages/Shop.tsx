import { useState } from "react";
import { Page } from "../components/Layout";
import { ErrorState, Loading, MicroLabel, ProductImage, SectionTitle } from "../components/ui";
import { timeLabel } from "../lib/commerce";
import { formatPrice } from "../lib/format";
import { flyToBag } from "../lib/motion";
import { CONCERN_LABELS, type Category, type ConcernKey, type Product } from "../lib/types";
import { useApp } from "../state/AppState";

const FILTERS: { label: string; cats: Category[] | null }[] = [
  { label: "All", cats: null },
  { label: "Cleanse", cats: ["cleanser"] },
  { label: "Serums", cats: ["serum"] },
  { label: "Moisturise", cats: ["moisturiser"] },
  { label: "Protect", cats: ["sunscreen"] },
  { label: "Eyes & exfoliate", cats: ["eye", "toner_exfoliant"] },
];

function targetsLine(p: Product) {
  return (Object.entries(p.targets) as [ConcernKey, number][])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([k]) => CONCERN_LABELS[k].toLowerCase())
    .join(", ");
}

function ProductTile({ product, qty, onAdd }: { product: Product; qty: number; onAdd: () => void }) {
  const am = timeLabel(product);
  return (
    <article className="group flex flex-col gap-3">
      <div className="relative h-[250px] overflow-hidden rounded-tile transition-[transform,box-shadow] duration-300 group-hover:-translate-y-1 group-hover:shadow-[0_30px_50px_-30px_rgba(56,44,41,0.6)] sm:h-[320px]">
        <ProductImage id={product.id} alt={`${product.name}, GlowCue studio render`} className="transition-transform duration-500 group-hover:scale-[1.06]" />
        <span
          className={`absolute top-3 left-3 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            am.startsWith("PM") ? "bg-ink text-surface" : am.startsWith("AM ·") && !am.includes("PM") ? "bg-sky text-ink" : "bg-surface/92 text-ink"
          }`}
        >
          {am}
        </span>
        <div className="absolute inset-x-3 bottom-3 flex items-center gap-2 rounded-2xl bg-surface/86 py-2 pr-2 pl-3 backdrop-blur-sm">
          <span className="flex min-w-0 flex-1 flex-col">
            <strong className="text-[13px] leading-snug">{product.name}</strong>
            <span className="text-xs tabular-nums text-ink-soft">{formatPrice(product.price)}</span>
          </span>
          <button
            type="button"
            onClick={(e) => {
              flyToBag(e.currentTarget.closest("article")?.querySelector("img"));
              onAdd();
            }}
            aria-label={qty ? `Add another ${product.name} (in bag: ${qty})` : `Add ${product.name} to bag`}
            className={`inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-surface transition-[background-color,transform] duration-200 active:scale-90 ${
              qty ? "bg-sage" : "bg-ink hover:bg-terra-deep"
            }`}
          >
            {qty ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" aria-hidden="true">
                <path d="M5 12l4 4 10-10" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
            )}
          </button>
        </div>
      </div>
      <div className="flex flex-col gap-1 px-1">
        <span className="text-xs text-muted">Helps the look of {targetsLine(product)}</span>
        <span className="text-[13px] leading-relaxed text-ink-soft">{product.description}</span>
        {qty > 0 && <span className="text-xs font-medium text-sage">In your bag · {qty}</span>}
      </div>
    </article>
  );
}

export function Shop() {
  const { catalogue, loadError, retryLoad, addToCart, cart } = useApp();
  const [filter, setFilter] = useState(0);

  if (loadError)
    return (
      <Page>
        <ErrorState message={loadError} onRetry={retryLoad} />
      </Page>
    );
  if (!catalogue)
    return (
      <Page>
        <Loading label="Loading the edit…" />
      </Page>
    );

  const active = FILTERS[filter] ?? FILTERS[0]!;
  const products = catalogue.products.filter((p) => !active.cats || active.cats.includes(p.category));
  const inCart = new Map(cart.map((i) => [i.product_id, i.qty]));

  return (
    <Page wide>
      <SectionTitle eyebrow={`The edit · ${catalogue.products.length} products`} title={<>Fewer products, <span className="italic text-terra-deep">better</span> reasons.</>}>
        Each product earns its place with a clear reason.
      </SectionTitle>
      <p role="note" className="-mt-4 mb-6 flex items-center gap-2 text-xs text-muted">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" className="shrink-0">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5M12 8v.5" />
        </svg>
        <span>
          GlowCue&rsquo;s range is a concept collection: product details, prices and images are illustrative.
        </span>
      </p>
      <nav aria-label="Categories" className="-mx-4 mb-8 flex gap-1 overflow-x-auto border-b border-line px-4 md:mx-0 md:px-0">
        {FILTERS.map((f, i) => {
          const count = f.cats ? catalogue.products.filter((p) => f.cats?.includes(p.category)).length : catalogue.products.length;
          return (
            <button
              key={f.label}
              type="button"
              aria-pressed={filter === i}
              onClick={() => setFilter(i)}
              className={`-mb-px min-h-12 shrink-0 border-b-2 px-4 text-sm transition-colors ${
                filter === i ? "border-ink font-semibold" : "border-transparent text-ink-soft hover:text-ink"
              }`}
            >
              {f.label} <span className="ml-1 font-normal text-muted">{count}</span>
            </button>
          );
        })}
      </nav>
      <MicroLabel className="sr-only">Showing {products.length} products</MicroLabel>
      <div key={filter} className="grid grid-cols-1 gap-6 animate-fade min-[480px]:grid-cols-2 lg:grid-cols-4 lg:gap-5">
        {products.map((p) => (
          <ProductTile key={p.id} product={p} qty={inCart.get(p.id) ?? 0} onAdd={() => addToCart([p.id])} />
        ))}
      </div>
    </Page>
  );
}
