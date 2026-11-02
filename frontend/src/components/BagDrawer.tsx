import { useEffect, useRef, type KeyboardEvent } from "react";
import { CORE, useQuote } from "../lib/commerce";
import { formatPrice } from "../lib/format";
import { CATEGORY_LABELS } from "../lib/types";
import { useApp } from "../state/AppState";
import { Button, ProductImage } from "./ui";

const FOCUSABLE = 'button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function QtyStepper({ name, qty, onChange, dark = false }: { name: string; qty: number; onChange: (n: number) => void; dark?: boolean }) {
  const cls = `inline-flex h-11 w-11 items-center justify-center rounded-full border text-lg transition-colors disabled:opacity-40 ${
    dark ? "border-muted text-surface hover:bg-ink-soft" : "border-line-strong hover:border-ink"
  }`;
  return (
    <span className="inline-flex items-center gap-1" role="group" aria-label={`Quantity of ${name}`}>
      <button type="button" className={cls} onClick={() => onChange(qty - 1)} aria-label={qty === 1 ? `Remove ${name}` : `One fewer ${name}`}>
        −
      </button>
      <span className="w-7 text-center tabular-nums" aria-live="polite">
        {qty}
      </span>
      <button type="button" className={cls} disabled={qty >= 10} onClick={() => onChange(qty + 1)} aria-label={`One more ${name}`}>
        +
      </button>
    </span>
  );
}

/** Bag: right-hand drawer on desktop, bottom sheet on mobile. Modal, focus-trapped, Esc to close. */
export function BagDrawer() {
  const { bagOpen, setBagOpen, cart, setQty, productById, preferences, go } = useApp();
  const { data: quote, loading, error } = useQuote();
  const panel = useRef<HTMLElement>(null);
  const closeBtn = useRef<HTMLButtonElement>(null);
  const opener = useRef<Element | null>(null);

  useEffect(() => {
    if (!bagOpen) return;
    opener.current = document.activeElement;
    closeBtn.current?.focus();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
      (opener.current as HTMLElement | null)?.focus?.();
    };
  }, [bagOpen]);

  if (!bagOpen) return null;
  const close = () => setBagOpen(false);

  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") return close();
    if (e.key !== "Tab" || !panel.current) return;
    const items = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
    const first = items[0];
    const last = items[items.length - 1];
    if (!first || !last) return;
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  const categories = new Set(cart.map((i) => productById.get(i.product_id)?.category));
  const missing = CORE.filter((c) => !categories.has(c) && !preferences.owned.includes(c));
  const subtotal = quote?.subtotal ?? 0;
  const within = subtotal <= preferences.budget;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-ink/40 animate-fade" onClick={close} aria-hidden="true" />
      <section
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="bag-title"
        onKeyDown={onKeyDown}
        className="drawer-in absolute inset-x-0 bottom-0 flex max-h-[88dvh] flex-col gap-4 rounded-t-[30px] bg-surface p-5 shadow-[0_-30px_60px_-30px_rgba(0,0,0,0.5)] md:inset-y-0 md:right-0 md:left-auto md:max-h-none md:w-[420px] md:rounded-none md:p-7"
      >
        <span className="mx-auto h-1.5 w-11 rounded-full bg-line-strong md:hidden" aria-hidden="true" />
        <div className="flex items-center justify-between">
          <h2 id="bag-title" className="display text-[34px]">
            Your bag
          </h2>
          <button
            ref={closeBtn}
            type="button"
            onClick={close}
            aria-label="Close bag"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-line-strong hover:border-ink"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>

        {cart.length === 0 ? (
          <div className="flex flex-1 flex-col items-start gap-4 py-6">
            <p className="text-muted">Your bag is empty.</p>
            <Button onClick={() => go("shop")}>Browse the edit</Button>
          </div>
        ) : (
          <>
            {missing.length === 0 ? (
              <p className="flex items-center gap-2 rounded-2xl bg-sage-soft px-3 py-2.5 text-[13px] text-sage-deep">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden="true">
                  <path d="M5 12l4 4 10-10" />
                </svg>
                Ritual essentials covered: cleanse, moisturise, protect
              </p>
            ) : (
              <p className="rounded-2xl bg-terra-soft px-3 py-2.5 text-[13px] text-terra-ink">
                Still missing: {missing.map((c) => CATEGORY_LABELS[c].toLowerCase()).join(", ")}
              </p>
            )}
            <ul className="-mx-1 flex-1 overflow-y-auto px-1">
              {cart.map((item) => {
                const p = productById.get(item.product_id);
                if (!p) return null;
                const line = quote?.lines.find((l) => l.product_id === item.product_id);
                return (
                  <li key={item.product_id} className="flex items-center gap-3 border-b border-sand py-3 last:border-0">
                    <div className="h-[76px] w-[62px] shrink-0 overflow-hidden rounded-2xl">
                      <ProductImage id={p.id} alt="" />
                    </div>
                    <div className="flex min-w-0 flex-1 flex-col gap-1">
                      <strong className="text-sm leading-snug">{p.name}</strong>
                      <QtyStepper name={p.name} qty={item.qty} onChange={(n) => setQty(p.id, n)} />
                    </div>
                    <span className="text-sm font-semibold tabular-nums">{line ? formatPrice(line.line_total) : "…"}</span>
                  </li>
                );
              })}
            </ul>
            <div className="flex flex-col gap-2.5" aria-live="polite">
              {error && <p className="text-sm text-terra-ink">{error}</p>}
              <div className="flex items-baseline justify-between">
                <span className="text-sm">Total · {quote?.item_count ?? "…"} items</span>
                <span className="display text-[38px] tabular-nums">{quote ? formatPrice(subtotal) : loading ? "…" : "—"}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-sand" aria-hidden="true">
                <div className={`h-full rounded-full ${within ? "bg-sage" : "bg-terra-deep"}`} style={{ width: `${Math.min(100, (100 * subtotal) / preferences.budget)}%` }} />
              </div>
              <p className="flex justify-between text-xs text-muted">
                <span>Budget {formatPrice(preferences.budget)}</span>
                <span>{within ? `${formatPrice(preferences.budget - subtotal)} left` : `${formatPrice(subtotal - preferences.budget)} over`}</span>
              </p>
              <Button size="lg" onClick={() => go("cart")} disabled={!quote}>
                Review order
              </Button>
              <p className="text-center text-xs text-muted">Checkout is a preview: no payment is processed.</p>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
