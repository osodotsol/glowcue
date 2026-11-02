import { QtyStepper } from "../components/BagDrawer";
import { Page } from "../components/Layout";
import { Button, Card, ErrorState, Loading, MicroLabel, ProductImage, SectionTitle } from "../components/ui";
import { CORE, timeLabel, useQuote } from "../lib/commerce";
import { formatPrice } from "../lib/format";
import { CATEGORY_LABELS } from "../lib/types";
import { useApp } from "../state/AppState";

export function Cart() {
  const { cart, setQty, productById, preferences, go } = useApp();
  const { data: quote, error, loading } = useQuote();

  if (cart.length === 0) {
    return (
      <Page>
        <SectionTitle eyebrow="Your bag" title={<>Your bag is <span className="italic text-terra-deep">empty.</span></>}>
          Build your ritual or browse the edit to add products.
        </SectionTitle>
        <div className="flex flex-wrap gap-3">
          <Button size="lg" onClick={() => go("about", 1)}>
            Begin my consultation
          </Button>
          <Button size="lg" variant="outline" onClick={() => go("shop")}>
            Browse the edit
          </Button>
        </div>
      </Page>
    );
  }

  const categories = new Set(cart.map((i) => productById.get(i.product_id)?.category));
  const missing = CORE.filter((c) => !categories.has(c) && !preferences.owned.includes(c));
  const subtotal = quote?.subtotal ?? 0;
  const within = subtotal <= preferences.budget;

  return (
    <Page wide>
      <SectionTitle eyebrow={`Bag · ${cart.reduce((n, i) => n + i.qty, 0)} items`} title={<>Your <span className="italic text-terra-deep">bag.</span></>} />
      <div className="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)]">
        <ul className="min-w-0">
          {cart.map((item) => {
            const p = productById.get(item.product_id);
            const line = quote?.lines.find((l) => l.product_id === item.product_id);
            if (!p) return null;
            return (
              <li key={item.product_id} className="grid grid-cols-[84px_1fr] gap-x-4 gap-y-2 border-b border-sand py-4 sm:grid-cols-[96px_1fr_auto_auto] sm:items-center">
                <div className="row-span-2 h-[104px] overflow-hidden rounded-[18px] sm:row-span-1 sm:h-[116px]">
                  <ProductImage id={p.id} alt={`${p.name}, GlowCue studio render`} />
                </div>
                <div className="flex min-w-0 flex-col gap-0.5">
                  <strong className="text-base leading-snug">{p.name}</strong>
                  <span className="text-xs text-muted">
                    {timeLabel(p)} · {formatPrice(p.price)} each
                  </span>
                  <button type="button" onClick={() => setQty(p.id, 0)} className="min-h-11 self-start text-xs underline underline-offset-4">
                    Remove
                  </button>
                </div>
                <div className="flex items-center justify-between gap-3 sm:contents">
                  <QtyStepper name={p.name} qty={item.qty} onChange={(n) => setQty(p.id, n)} />
                  <strong className="tabular-nums sm:w-24 sm:text-right">{line ? formatPrice(line.line_total) : "…"}</strong>
                </div>
              </li>
            );
          })}
        </ul>

        <aside className="flex min-w-0 flex-col gap-4 lg:sticky lg:top-28 lg:self-start">
          <Card tone="ink" className="flex flex-col gap-3.5" padded>
            <MicroLabel className="text-peach">Order summary</MicroLabel>
            <div aria-live="polite" className="flex flex-col gap-3">
              {error && <ErrorState message={error} />}
              {!quote && loading && <Loading label="Checking prices…" />}
              {quote && (
                <>
                  <p className="flex justify-between text-sm text-peach">
                    <span>{quote.item_count} items</span>
                    <span className="tabular-nums">{formatPrice(subtotal)}</span>
                  </p>
                  <p className="flex justify-between text-sm text-peach">
                    <span>Delivery</span>
                    <span>Not included</span>
                  </p>
                  <p className="flex items-baseline justify-between border-t border-muted/50 pt-3">
                    <span>Total</span>
                    <span className="display text-[46px] tabular-nums">{formatPrice(subtotal)}</span>
                  </p>
                  <div className="h-1.5 overflow-hidden rounded-full bg-ink-soft" aria-hidden="true">
                    <div className={`h-full rounded-full ${within ? "bg-peach" : "bg-terra"}`} style={{ width: `${Math.min(100, (100 * subtotal) / preferences.budget)}%` }} />
                  </div>
                  <p className="text-xs text-peach">
                    {within ? `${formatPrice(preferences.budget - subtotal)} under` : `${formatPrice(subtotal - preferences.budget)} over`} your{" "}
                    {formatPrice(preferences.budget)} budget
                  </p>
                </>
              )}
            </div>
            <Button size="lg" variant="light" onClick={() => go("checkout")} disabled={!quote || loading}>
              Preview checkout
            </Button>
            <p className="text-center text-xs text-peach">Checkout is a preview: no payment is processed.</p>
          </Card>
          <p className={`rounded-2xl px-4 py-3 text-sm ${missing.length ? "bg-terra-soft text-terra-ink" : "bg-sage-soft text-sage-deep"}`}>
            {missing.length
              ? `Your ritual is missing: ${missing.map((c) => CATEGORY_LABELS[c].toLowerCase()).join(", ")}.`
              : "✓ Ritual complete: cleanser, moisturiser and sunscreen are covered."}
          </p>
        </aside>
      </div>
    </Page>
  );
}
