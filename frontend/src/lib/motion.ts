import { flushSync } from "react-dom";

/** Motion storyboard helpers. Browser-native only (View Transitions + Web Animations); no animation library. */

export const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Run a state update inside a View Transition when the browser supports it (otherwise instantly). */
export function withTransition(update: () => void) {
  if (prefersReducedMotion() || typeof document.startViewTransition !== "function") {
    update();
    return;
  }
  document.startViewTransition(() => flushSync(update));
}

/** Storyboard D: the product image flies along a soft arc into the bag button. */
export function flyToBag(source: Element | null | undefined) {
  if (!source || prefersReducedMotion()) return;
  const bag = [...document.querySelectorAll<HTMLElement>('[aria-label^="Bag,"]')].find((el) => el.getBoundingClientRect().width > 0);
  if (!bag) return;
  const from = source.getBoundingClientRect();
  const to = bag.getBoundingClientRect();
  const clone = source.cloneNode(true) as HTMLElement;
  const size = Math.min(from.width, from.height, 140);
  Object.assign(clone.style, {
    position: "fixed",
    left: `${from.left + from.width / 2 - size / 2}px`,
    top: `${from.top + from.height / 2 - size / 2}px`,
    width: `${size}px`,
    height: `${size}px`,
    objectFit: "cover",
    borderRadius: "22px",
    zIndex: "60",
    pointerEvents: "none",
  });
  clone.setAttribute("aria-hidden", "true");
  document.body.appendChild(clone);
  const dx = to.left + to.width / 2 - (from.left + from.width / 2);
  const dy = to.top + to.height / 2 - (from.top + from.height / 2);
  const animation = clone.animate(
    [
      { transform: "translate(0, 0) scale(1)", opacity: 1 },
      { transform: `translate(${dx * 0.45}px, ${dy * 0.45 - 80}px) scale(0.6)`, opacity: 0.95, offset: 0.5 },
      { transform: `translate(${dx}px, ${dy}px) scale(0.12)`, opacity: 0.2 },
    ],
    { duration: 620, easing: "cubic-bezier(0.2, 0.7, 0.2, 1)" },
  );
  animation.onfinish = () => clone.remove();
  animation.oncancel = () => clone.remove();
}
