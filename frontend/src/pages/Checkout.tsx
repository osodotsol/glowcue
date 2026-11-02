import { Page } from "../components/Layout";
import { Button, Card, CueMark, Loading, MicroLabel, SectionTitle } from "../components/ui";
import { ritualOrder, useQuote } from "../lib/commerce";
import { formatPrice } from "../lib/format";
import { useApp } from "../state/AppState";

export function Checkout() {
  const { resetAll, go, cart, productById } = useApp();
  const { data: quote, loading } = useQuote();
  const products = cart.map((i) => productById.get(i.product_id)).filter((p) => p !== undefined);
  const am = ritualOrder(products, "am");
  const pm = ritualOrder(products, "pm");

  return (
    <Page wide>
      <SectionTitle eyebrow="Checkout preview" title={<>Your order, <span className="italic text-terra-deep">previewed.</span></>} />

      <div className="mt-2 grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-2">
        <Card className="min-w-0">
          <MicroLabel className="text-sage">Order summary</MicroLabel>
          {!quote && loading && <Loading label="Preparing summary…" />}
          {!quote && !loading && <p className="mt-4 text-sm text-muted">Your bag is empty.</p>}
          {quote && (
            <>
              <ul className="mt-4 divide-y divide-sand">
                {quote.lines.map((line) => (
                  <li key={line.product_id} className="flex justify-between gap-3 py-2.5 text-sm">
                    <span>
                      {line.qty} × {line.name}
                    </span>
                    <span className="tabular-nums">{formatPrice(line.line_total)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 flex items-baseline justify-between border-t border-ink pt-3">
                <span className="font-semibold">Total</span>
                <span className="display text-[40px] tabular-nums">{formatPrice(quote.subtotal)}</span>
              </p>
              <p role="note" className="mt-4 rounded-2xl bg-bg px-4 py-3 text-xs leading-relaxed text-ink-soft">
                This is a checkout preview. No payment is processed and nothing is ordered or shipped.
              </p>
            </>
          )}
        </Card>

        <Card className="min-w-0 border border-dashed border-line-strong">
          <MicroLabel className="text-sage">Your ritual card</MicroLabel>
          <p className="display mt-2 text-[30px]">Keep this by your mirror.</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-sky p-4 text-sm leading-7">
              <p className="flex items-center gap-2 font-semibold">
                <CueMark variant="am" size={18} /> Morning
              </p>
              {am.length ? am.map((p, i) => <p key={p.id}>{i + 1} · {p.name}</p>) : <p className="text-muted">Nothing for the morning yet.</p>}
            </div>
            <div className="rounded-2xl bg-ink p-4 text-sm leading-7 text-surface">
              <p className="flex items-center gap-2 font-semibold">
                <CueMark variant="pm" size={18} /> Evening
              </p>
              {pm.length ? pm.map((p, i) => <p key={p.id}>{i + 1} · {p.name}</p>) : <p className="text-peach">Nothing for the evening yet.</p>}
            </div>
          </div>
          <p className="mt-3 text-xs text-muted">Suggested order by product type. Your ritual page has the full instructions.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => window.print()}>
              Print card
            </Button>
            <Button variant="outline" onClick={() => go("cart")}>
              Back to bag
            </Button>
          </div>
        </Card>
      </div>

      <div className="mt-8 flex flex-col items-start gap-2">
        <Button size="lg" onClick={resetAll}>
          Start over &amp; clear my data
        </Button>
        <p className="text-xs text-muted">Clears your answers, skin report, bag and photo preview from this browser tab.</p>
      </div>
    </Page>
  );
}
