import { useEffect, useRef, type KeyboardEvent, type RefObject } from "react";

const FOCUSABLE = 'button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Modal behaviour for an overlay panel: focus moves to `initialFocus` on open, Tab is trapped inside `panel`,
 * Esc closes, the page behind cannot scroll, and focus returns on close to `returnFocus` (or, failing that, to
 * whatever had focus on open; a tap does not always focus the button that was tapped, e.g. in iOS Safari).
 * (Same pattern as the bag drawer, which keeps its own copy.)
 */
export function useDialog<P extends HTMLElement, F extends HTMLElement>(
  open: boolean,
  onClose: () => void,
  returnFocus?: RefObject<HTMLElement | null>,
) {
  const panel = useRef<P>(null);
  const initialFocus = useRef<F>(null);

  useEffect(() => {
    if (!open) return;
    const opener = returnFocus?.current ?? (document.activeElement as HTMLElement | null);
    initialFocus.current?.focus();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
      opener?.focus?.({ preventScroll: true });
    };
  }, [open, returnFocus]);

  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") return onClose();
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

  return { panel, initialFocus, onKeyDown };
}
