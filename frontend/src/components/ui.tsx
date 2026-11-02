import { useEffect, useState, type ButtonHTMLAttributes, type CSSProperties, type ReactNode, type Ref } from "react";
import { titleForMessage } from "../lib/errors";
import type { Band } from "../lib/types";

// ------------------------------------------------------------------ buttons
type Variant = "primary" | "dark" | "outline" | "ghost" | "light";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-terra-deep text-surface hover:bg-terra-ink disabled:bg-muted/40",
  dark: "bg-ink text-surface hover:bg-ink-soft disabled:bg-muted/40",
  outline: "border border-ink text-ink hover:bg-ink hover:text-surface disabled:border-line disabled:text-muted",
  ghost: "text-ink underline-offset-4 hover:underline disabled:text-muted",
  light: "bg-surface/90 text-ink hover:bg-surface",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "md" | "lg";
  ref?: Ref<HTMLButtonElement>; // React 19 passes ref as an ordinary prop
}

export function Button({ variant = "primary", size = "md", className = "", ...props }: ButtonProps) {
  const sizing = size === "lg" ? "min-h-14 px-7 text-base" : "min-h-12 px-5 text-sm";
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-full font-medium transition-[background-color,color,transform] duration-200 active:scale-[0.97] disabled:cursor-not-allowed ${sizing} ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}

/** Round arrow inside the primary CTA (Edition 2 hero button). */
export function ArrowDisc() {
  return (
    <span className="-mr-4 inline-flex h-10 w-10 items-center justify-center rounded-full bg-surface" aria-hidden="true">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-terra-deep">
        <path d="M5 12h14M13 6l6 6-6 6" />
      </svg>
    </span>
  );
}

// ------------------------------------------------------------------ surfaces
interface CardProps {
  children: ReactNode;
  className?: string;
  padded?: boolean; // explicit opt-out instead of fighting a p-5 class with p-0
  tone?: "surface" | "peach" | "ink" | "sky";
}

const TONES = { surface: "bg-surface", peach: "bg-peach", ink: "bg-ink text-surface", sky: "bg-sky" };

export function Card({ children, className = "", padded = true, tone = "surface" }: CardProps) {
  return <div className={`rounded-card ${TONES[tone]} ${padded ? "p-5 sm:p-6" : ""} ${className}`}>{children}</div>;
}

// ------------------------------------------------------------------ selection
interface ChipProps {
  selected: boolean;
  onToggle: () => void;
  children: ReactNode;
  className?: string;
}

export function Chip({ selected, onToggle, children, className = "" }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onToggle}
      className={`min-h-11 rounded-full border px-4 text-sm font-medium transition-colors duration-200 ${
        selected ? "border-ink bg-ink text-surface" : "border-line-strong bg-surface text-ink hover:border-ink"
      } ${className}`}
    >
      {children}
    </button>
  );
}

// ------------------------------------------------------------------ brand marks
export function CueMark({ size = 28, variant = "brand" }: { size?: number; variant?: "brand" | "am" | "pm" }) {
  if (variant === "am")
    return (
      <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
        <circle cx="20" cy="20" r="18" fill="none" stroke="var(--color-ink)" strokeWidth="3" />
        <path d="M20 2a18 18 0 0 0 0 36" fill="var(--color-terra)" />
      </svg>
    );
  if (variant === "pm")
    return (
      <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
        <circle cx="20" cy="20" r="18" fill="var(--color-ink)" stroke="var(--color-peach)" strokeWidth="2" />
        <path d="M20 2a18 18 0 0 1 0 36" fill="var(--color-peach)" />
      </svg>
    );
  return (
    <svg width={size} height={size} viewBox="0 0 56 56" aria-hidden="true">
      <circle cx="28" cy="28" r="27" fill="var(--color-ink)" />
      <path d="M28 10a18 18 0 0 1 0 36" fill="var(--color-terra)" />
      <circle cx="28" cy="28" r="5" fill="var(--color-surface)" />
    </svg>
  );
}

export function MicroLabel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <span className={`micro ${className}`}>{children}</span>;
}

// ------------------------------------------------------------------ bands and scores
export const BAND_COLOR: Record<Band, string> = {
  priority: "var(--color-band-priority)",
  watch: "var(--color-band-watch)",
  good: "var(--color-band-good)",
  not_measured: "var(--color-line-strong)",
};
export const BAND_LABEL: Record<Band, string> = {
  priority: "Priority",
  watch: "Worth watching",
  good: "Looking good",
  not_measured: "Not measured",
};

export function BandBadge({ band }: { band: Band }) {
  const style: Record<Band, string> = {
    priority: "bg-terra-soft text-terra-ink",
    watch: "bg-sand text-ink",
    good: "bg-sage-soft text-sage-deep",
    not_measured: "bg-line text-muted",
  };
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${style[band]}`}>{BAND_LABEL[band]}</span>;
}

/** Half-circle gauge. The number is always printed, so colour never carries meaning alone. */
export function GlowArc({
  score,
  band,
  width = 96,
  label,
  showNumber = true,
  delay = 0,
}: {
  score: number | null;
  band: Band;
  width?: number;
  label?: string;
  showNumber?: boolean;
  delay?: number;
}) {
  const value = score === null ? 0 : Math.max(0, Math.min(100, Math.round(score)));
  const style = { strokeDasharray: `${value} 100`, animationDelay: `${delay}ms` } as CSSProperties;
  return (
    <svg
      width={width}
      height={(width * 62) / 100}
      viewBox="0 0 100 62"
      role="img"
      aria-label={`${label ?? "Score"}: ${score === null ? "not measured" : `${value} out of 100`}, ${BAND_LABEL[band]}`}
    >
      <path d="M10 56 A40 40 0 0 1 90 56" fill="none" stroke="var(--color-sand)" strokeWidth="10" strokeLinecap="round" pathLength={100} />
      {score !== null && (
        <path
          d="M10 56 A40 40 0 0 1 90 56"
          fill="none"
          stroke={BAND_COLOR[band]}
          strokeWidth="10"
          strokeLinecap="round"
          pathLength={100}
          className="glow-arc"
          style={style}
        />
      )}
      {showNumber && (
        <text x="50" y="54" textAnchor="middle" fontFamily="var(--font-display)" fontSize="24" fontWeight="300" fill="var(--color-ink)">
          {score === null ? "—" : value}
        </text>
      )}
    </svg>
  );
}

/** Count of attributes per band: the analysis overview (no averaged "skin score"). */
export function BandBar({ counts }: { counts: Record<"priority" | "watch" | "good", number> }) {
  const total = counts.priority + counts.watch + counts.good || 1;
  return (
    <div
      className="flex h-3.5 gap-[3px] overflow-hidden rounded-full"
      role="img"
      aria-label={`${counts.priority} priorities, ${counts.watch} worth watching, ${counts.good} looking good`}
    >
      {(["priority", "watch", "good"] as const).map(
        (b) =>
          counts[b] > 0 && (
            <span key={b} className="band-seg h-full" style={{ flex: counts[b] / total, background: BAND_COLOR[b] }} />
          ),
      )}
    </div>
  );
}

export function ScoreBar({ score, band }: { score: number | null; band: Band }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-sand" aria-hidden="true">
        {score !== null && <div className="h-full rounded-full" style={{ width: `${score}%`, background: BAND_COLOR[band] }} />}
      </div>
      <span className="w-14 text-right text-sm tabular-nums text-muted">{score === null ? "—" : `${Math.round(score)}/100`}</span>
    </div>
  );
}

// ------------------------------------------------------------------ honesty and status
/** A quiet, in-context note (where the scores come from, sample profiles). */
export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <div role="note" className="flex items-start gap-2 rounded-2xl border border-line bg-surface px-4 py-3 text-[13px] leading-relaxed text-ink-soft">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" className="mt-0.5 shrink-0">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v5M12 16v.5" />
      </svg>
      <span>{children}</span>
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "warn"; children: ReactNode }) {
  const style = tone === "warn" ? "bg-terra-soft text-terra-ink" : "bg-surface text-ink";
  return <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${style}`}>{children}</div>;
}

export function Loading({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" className="flex flex-col items-center gap-3 py-16 text-muted">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-terra-deep" aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorState({ message, title, onRetry }: { message: string; title?: string; onRetry?: () => void }) {
  return (
    <Card className="text-center">
      <p className="font-medium">{title ?? titleForMessage(message)}</p>
      <p className="mt-1 text-sm text-muted">{message}</p>
      {onRetry && (
        <Button variant="outline" className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </Card>
  );
}

export function SectionTitle({ eyebrow, title, children }: { eyebrow?: string; title: ReactNode; children?: ReactNode }) {
  return (
    <header className="mb-8">
      {eyebrow && <MicroLabel className="text-sage">{eyebrow}</MicroLabel>}
      <h1 className="display mt-3 text-balance text-[2.6rem] sm:text-6xl">{title}</h1>
      {children && <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">{children}</p>}
    </header>
  );
}

// ------------------------------------------------------------------ photography
/**
 * Brand photography (two portraits) and the hero film live in frontend/public/brand/ and are published with the site.
 * They are brand imagery only: never placed beside or over scores, and never presented as a customer or an analysed
 * face. If a file cannot load, its slot falls back to the matching GlowCue studio render so the layout never breaks.
 * frontend/public/private/ stays git-ignored, is deleted from dist/ by vite.config.ts and is never referenced.
 */
type PortraitSlot = "consultation" | "storytelling";
type SceneName = "hero_still" | "night_still" | "gel_coral" | "cream_swirl" | "drops";
const SCENE_ALT: Record<SceneName, string> = {
  hero_still: "GlowCue vitamin C serum, gel cleanser and barrier cream on a sunlit plinth, studio render",
  night_still: "GlowCue eye gel, retinol serum and ceramide cream on a dark backdrop, studio render",
  gel_coral: "Coral gel texture swatch, studio render",
  cream_swirl: "Swirl of cream texture on a peach background, studio render",
  drops: "Serum droplets on a soft green background, studio render",
};
const PORTRAIT_FILE: Record<PortraitSlot, string> = {
  consultation: "p2-consultation.webp",
  storytelling: "p3-storytelling.webp",
};
/** Studio renders shown only if a portrait fails to load. */
const PORTRAIT_FALLBACK: Record<PortraitSlot, { scene: SceneName; position: string }> = {
  consultation: { scene: "cream_swirl", position: "50% 50%" },
  storytelling: { scene: "gel_coral", position: "50% 50%" },
};

/** A brand portrait from /brand/portraits, or its studio-render stand-in if the file cannot be loaded. */
export function Portrait({
  slot,
  alt,
  position = "50% 30%",
  className = "",
  eager = false,
}: {
  slot: PortraitSlot;
  alt: string;
  position?: string;
  className?: string;
  eager?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    const fallback = PORTRAIT_FALLBACK[slot];
    return (
      <SceneImage name={fallback.scene} alt={SCENE_ALT[fallback.scene]} position={fallback.position} eager={eager} className={className} />
    );
  }
  return (
    <img
      src={`/brand/portraits/${PORTRAIT_FILE[slot]}`}
      alt={alt}
      loading={eager ? "eager" : "lazy"}
      decoding="async"
      fetchPriority={eager ? "high" : "auto"}
      onError={() => setFailed(true)}
      className={`h-full w-full object-cover ${className}`}
      style={{ objectPosition: position }}
    />
  );
}

const HERO_DIR = "/brand/videos";
const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => typeof window !== "undefined" && window.matchMedia(REDUCED_MOTION).matches);
  useEffect(() => {
    const query = window.matchMedia(REDUCED_MOTION);
    const onChange = () => setReduced(query.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);
  return reduced;
}

/**
 * The hero film (frontend/public/brand/videos). Muted, looping, inline.
 *
 * The source file carries baked-in white side bars (130 px left, ~34 px right of 1280 px), so the "frame" box
 * below is sized to the real 1116 x 720 picture and the video is oversized and shifted inside it to hide the bars.
 * The box fills the opening's height and `focusX` slides it horizontally, like object-position.
 * Reduced motion shows the poster frame instead of the film; if the film cannot load, the hero studio render is shown.
 */
export function HeroVideo({ label, focusX = 50, className = "" }: { label: string; focusX?: number; className?: string }) {
  const reduced = useReducedMotion();
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className={`relative h-full w-full overflow-hidden bg-peach ${className}`}>
        <SceneImage name="hero_still" alt={SCENE_ALT.hero_still} position="78% 55%" eager />
      </div>
    );
  }
  const media = "absolute top-0 left-[-11.65%] h-auto w-[114.7%] max-w-none";
  return (
    <div role="img" aria-label={label} className={`relative h-full w-full overflow-hidden bg-peach ${className}`}>
      <div
        className="hero-frame absolute top-0 h-full min-w-full overflow-hidden"
        style={{ aspectRatio: "1116 / 720", left: `${focusX}%`, translate: `-${focusX}% 0` }}
      >
        {reduced ? (
          <img src={`${HERO_DIR}/glowcue-hero-poster.webp`} alt="" decoding="async" onError={() => setFailed(true)} className={media} />
        ) : (
          <video
            ref={(el) => {
              // React does not reliably reflect `muted` as an attribute; set the property so autoplay is allowed.
              if (el) el.muted = true;
            }}
            src={`${HERO_DIR}/glowcue-hero.mp4`}
            poster={`${HERO_DIR}/glowcue-hero-poster.webp`}
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
            disablePictureInPicture
            aria-hidden="true"
            tabIndex={-1}
            onError={() => setFailed(true)}
            className={media}
          />
        )}
      </div>
    </div>
  );
}

/** Original GlowCue Demo studio renders (frontend/public/products). */
export function ProductImage({ id, alt, className = "", position = "50% 45%" }: { id: string; alt: string; className?: string; position?: string }) {
  return (
    <img
      src={`/products/${id}.webp`}
      alt={alt}
      loading="lazy"
      decoding="async"
      className={`h-full w-full object-cover ${className}`}
      style={{ objectPosition: position }}
    />
  );
}

export function SceneImage({ name, alt, className = "", position = "50% 50%", eager = false }: { name: SceneName; alt: string; className?: string; position?: string; eager?: boolean }) {
  return (
    <img
      src={`/products/scenes/${name}.webp`}
      alt={alt}
      loading={eager ? "eager" : "lazy"}
      decoding="async"
      className={`h-full w-full object-cover ${className}`}
      style={{ objectPosition: position }}
    />
  );
}
