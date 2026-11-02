import { ArrowDisc, BandBar, Button, CueMark, GlowArc, HeroVideo, MicroLabel, Portrait, ProductImage, SceneImage, USE_PRIVATE_ASSETS } from "../components/ui";
import { formatPrice } from "../lib/format";
import { useApp } from "../state/AppState";

const TEMP_PHOTO_NOTE =
  "Temporary photography and film supplied by the owner for this demo; licence not yet verified and replaced before any public release. Brand imagery only, never analysed.";

const HERO_LABEL =
  "Short looping film: a woman with deep skin tone, hair in a low bun, gently touching her cheek and jaw against a warm beige backdrop";

const STEPS = [
  { n: "01", title: "A short consultation", text: "Your skin, your preferences, what's already on your shelf and the budget you'd like to keep." },
  { n: "02", title: "Your skin report", text: "Nine attributes in plain words, your three priorities first, every number shown." },
  { n: "03", title: "Your ritual, priced", text: "The smallest morning and evening routine that covers it, each product with its reason." },
];

export function Landing() {
  const { go, loadError, retryLoad, productById } = useApp();
  const vitC = productById.get("gc-ser-03");
  const edit = ["gc-ser-01", "gc-moi-02", "gc-spf-01", "gc-eye-01"].map((id) => productById.get(id)).filter((p) => p !== undefined);

  return (
    <main>
      {/* ---------------------------------------------------------------- hero */}
      <section className="mx-auto grid max-w-[1280px] md:grid-cols-12 md:gap-x-6 md:px-16 md:pt-6 md:pb-10">
        {/* mobile: full-bleed portrait opening */}
        <div className="relative h-[480px] overflow-hidden md:hidden">
          <HeroVideo label={HERO_LABEL} focusX={45} className="animate-fade" />
        </div>

        <div className="flex flex-col justify-center gap-6 px-4 pt-8 md:col-span-6 md:px-0 md:pt-0 md:pb-10">
          <MicroLabel className="text-sage animate-rise">Issue No. 01 · Your skin, edited</MicroLabel>
          <h1 className="display text-[3.1rem] sm:text-7xl lg:text-[96px]">
            <span className="block animate-rise [animation-delay:90ms]">Know your skin.</span>
            <span className="block animate-rise [animation-delay:180ms]">Choose with</span>
            <span className="block animate-rise italic text-terra-deep [animation-delay:270ms]">confidence.</span>
          </h1>
          <p className="max-w-md text-base leading-relaxed text-ink-soft animate-rise [animation-delay:360ms] sm:text-lg">
            A five-minute consultation becomes your personal edition: a clear skin report, a morning and evening ritual,
            and only the products that earn their place in your budget.
          </p>
          <div className="flex flex-wrap items-center gap-3 animate-rise [animation-delay:450ms]">
            <Button size="lg" onClick={() => go("about", 1)} className="pr-6">
              Begin my consultation <ArrowDisc />
            </Button>
            <Button variant="ghost" size="lg" className="underline" onClick={() => go("shop")}>
              Browse the edit
            </Button>
          </div>
          <ul className="flex flex-wrap gap-x-6 gap-y-1 text-[13px] text-muted">
            <li>Photos analysed only with your consent</li>
            <li>Cosmetic, never medical</li>
            <li>Transparent prices in ₦</li>
          </ul>
          {loadError && (
            <div role="alert" className="flex flex-wrap items-center gap-3 rounded-2xl bg-terra-soft px-4 py-3 text-sm text-terra-ink">
              GlowCue is temporarily unavailable. Please try again in a moment.
              <Button variant="outline" onClick={retryLoad}>
                Retry
              </Button>
            </div>
          )}
        </div>

        {/* desktop: arch portrait with the product render overlapping it */}
        <div className="relative hidden h-[640px] md:col-span-6 md:block">
          <div className="hero-arch absolute inset-x-0 top-6 h-[450px] overflow-hidden rounded-[220px_28px_28px_28px]">
            <HeroVideo label={HERO_LABEL} focusX={50} />
          </div>
          {vitC && (
            <div className="absolute top-[290px] left-6 h-[188px] w-[150px] overflow-hidden rounded-[22px] border-[6px] border-bg shadow-[0_30px_60px_-30px_rgba(56,44,41,0.55)] animate-rise [animation-delay:600ms]">
              <ProductImage id={vitC.id} alt={`${vitC.name}, GlowCue studio render`} position="50% 38%" />
            </div>
          )}
          {USE_PRIVATE_ASSETS && (
            <p className="absolute top-[492px] left-[200px] max-w-[380px] text-[11px] leading-relaxed text-muted">{TEMP_PHOTO_NOTE}</p>
          )}
          <div className="absolute top-[580px] left-0 flex gap-6 text-ink">
            <MicroLabel>Considered</MicroLabel>
            <MicroLabel>Personal</MicroLabel>
            <MicroLabel>Honest</MicroLabel>
          </div>
        </div>
        {USE_PRIVATE_ASSETS && <p className="px-4 pt-3 text-[11px] leading-relaxed text-muted md:hidden">{TEMP_PHOTO_NOTE}</p>}
      </section>

      {/* ---------------------------------------------------------------- meet your edition */}
      <section className="mx-auto max-w-[1280px] px-4 pt-14 md:px-16 md:pt-20" aria-labelledby="edition">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-3">
          <h2 id="edition" className="display text-[2.6rem] sm:text-6xl">
            Meet your <span className="italic text-terra-deep">edition.</span>
          </h2>
          <MicroLabel className="hidden text-muted sm:inline">One report · two rituals · a short edit</MicroLabel>
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:grid-rows-[300px_300px] md:gap-4">
          <div className="relative col-span-1 row-span-2 h-[420px] overflow-hidden rounded-tile md:h-auto">
            <Portrait
              slot="storytelling"
              position="55% 40%"
              alt="Man with curly auburn hair and dense natural freckles, small swipes of white cream on his cheeks"
            />
            <span className="micro absolute bottom-4 left-3 rounded-lg bg-surface/90 px-2.5 py-1.5 text-ink">A ritual, not a regimen</span>
          </div>
          <div className="relative h-[204px] overflow-hidden rounded-tile md:h-auto">
            <SceneImage name="gel_coral" alt="Coral serum gel swatch, GlowCue studio render" />
            <div className="absolute top-4 left-4 flex flex-col gap-1.5 text-ink">
              <MicroLabel>Light</MicroLabel>
              <MicroLabel>Layerable</MicroLabel>
              <MicroLabel>Yours</MicroLabel>
            </div>
          </div>
          {vitC && (
            <button
              type="button"
              onClick={() => go("shop")}
              className="group relative h-[204px] overflow-hidden rounded-tile text-left md:h-auto"
              aria-label={`${vitC.name}, ${formatPrice(vitC.price)}. Open the edit`}
            >
              <ProductImage id={vitC.id} alt="" position="50% 40%" className="transition-transform duration-500 group-hover:scale-105" />
              <span className="absolute inset-x-3 bottom-3 flex items-center justify-between gap-2 rounded-2xl bg-surface/85 px-3 py-2.5 text-[13px]">
                <strong className="truncate">{vitC.name}</strong>
                <span>{formatPrice(vitC.price)}</span>
              </span>
            </button>
          )}
          <div className="col-span-2 row-span-2 flex items-center justify-center rounded-tile bg-sky py-8 md:col-span-1 md:py-0">
            <div className="flex h-[440px] w-[220px] flex-col gap-3 rounded-[38px] border-[6px] border-ink bg-surface px-4 py-6 shadow-[0_40px_80px_-40px_rgba(56,44,41,0.55)]">
              <span className="font-display text-sm">GlowCue</span>
              <span className="display text-[23px] leading-[1.1]">
                Good morning.
                <br />
                Your ritual is <span className="italic text-terra-deep">ready.</span>
              </span>
              <div className="h-28 overflow-hidden rounded-2xl">
                <ProductImage id="gc-ser-01" alt="" position="50% 45%" />
              </div>
              <div className="flex items-center justify-between rounded-2xl bg-bg px-3 py-2.5">
                <span className="flex flex-col">
                  <strong className="text-xs">Morning ritual</strong>
                  <span className="text-[11px] text-muted">5 steps · 4 min</span>
                </span>
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-terra-deep" aria-hidden="true">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-surface)" strokeWidth="2.4">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </span>
              </div>
              <span className="text-[10px] text-muted">Example screen</span>
            </div>
          </div>
          <div className="relative col-span-2 h-[240px] overflow-hidden rounded-tile bg-ink md:h-auto">
            <SceneImage name="night_still" alt="GlowCue evening products in low warm light" position="15% 62%" />
            <div className="absolute top-5 right-6 flex flex-col items-end gap-2 text-right text-surface">
              <MicroLabel className="text-peach">Evening ritual</MicroLabel>
              <span className="display text-[28px] leading-[1.05] sm:text-[34px]">
                Unwind, renew,
                <br />
                <span className="italic">never rush.</span>
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- the edit (product row) */}
      {edit.length > 0 && (
        <section className="mx-auto max-w-[1280px] px-4 pt-14 md:px-16" aria-labelledby="the-edit">
          <div className="mb-5 flex items-baseline justify-between">
            <h2 id="the-edit" className="display text-[2rem] sm:text-5xl">
              The edit
            </h2>
            <Button variant="ghost" onClick={() => go("shop")} className="underline">
              See all 15
            </Button>
          </div>
          <div className="-mx-4 flex snap-x gap-3 overflow-x-auto px-4 pb-2 md:mx-0 md:grid md:grid-cols-4 md:overflow-visible md:px-0">
            {edit.map((p) => (
              <button key={p.id} type="button" onClick={() => go("shop")} className="group w-[168px] shrink-0 snap-start text-left md:w-auto">
                <div className="h-[210px] overflow-hidden rounded-[24px] md:h-[280px]">
                  <ProductImage id={p.id} alt={`${p.name}, GlowCue studio render`} className="transition-transform duration-500 group-hover:scale-105" />
                </div>
                <p className="mt-2 text-[13px] font-semibold">{p.name}</p>
                <p className="text-xs text-muted">{formatPrice(p.price)}</p>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ---------------------------------------------------------------- how it works */}
      <section id="how" className="mx-auto max-w-[1280px] px-4 pt-16 md:px-16" aria-labelledby="how-title">
        <h2 id="how-title" className="display mb-8 text-[2rem] sm:text-5xl">
          How your edition is made
        </h2>
        <ol className="grid gap-8 md:grid-cols-3 md:gap-6">
          {STEPS.map((step, i) => (
            <li key={step.n} className="flex flex-col gap-3">
              <div className="h-[180px] overflow-hidden rounded-[24px] bg-surface md:h-[200px]">
                {i === 0 && <SceneImage name="drops" alt="" />}
                {i === 1 && (
                  <div className="flex h-full flex-col items-center justify-center gap-5 px-8">
                    <div className="flex gap-3">
                      <GlowArc score={41} band="priority" width={84} label="Example: dark spots" showNumber={false} />
                      <GlowArc score={64} band="watch" width={84} label="Example: hydration" showNumber={false} />
                      <GlowArc score={78} band="good" width={84} label="Example: blemishes" showNumber={false} />
                    </div>
                    <div className="w-full max-w-[260px]">
                      <BandBar counts={{ priority: 3, watch: 4, good: 2 }} />
                    </div>
                  </div>
                )}
                {i === 2 && <SceneImage name="cream_swirl" alt="" />}
              </div>
              <span className="display text-[44px] text-terra">{step.n}</span>
              <strong className="text-[17px]">{step.title}</strong>
              <span className="text-[15px] leading-relaxed text-muted">{step.text}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="mx-auto mt-16 flex max-w-[1280px] flex-col items-start gap-4 px-4 md:flex-row md:items-center md:justify-between md:px-16">
        <span className="display flex items-center gap-3 text-[28px] sm:text-4xl">
          <CueMark size={36} /> Ready when you are.
        </span>
        <Button size="lg" onClick={() => go("about", 1)} className="pr-6">
          Begin my consultation <ArrowDisc />
        </Button>
      </section>
    </main>
  );
}
