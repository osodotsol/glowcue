import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";
import { useDialog } from "../lib/useDialog";
import type { Section, View } from "../state/AppState";
import { CueMark } from "./ui";

interface HeaderProps {
  view: View;
  section: Section | null;
  /** A skin report exists, so "My Routine" has something to show. */
  routineAvailable: boolean;
  cartCount: number;
  bagPulse: number;
  onNavigate: (view: View, stage?: number) => void;
  onSection: (section: Section) => void;
  onOpenBag: () => void;
}

interface NavItem {
  label: string;
  active: boolean;
  go: () => void;
}

function navItems({ view, section, onNavigate, onSection }: Pick<HeaderProps, "view" | "section" | "onNavigate" | "onSection">): NavItem[] {
  return [
    { label: "Discover", active: view === "landing" && section === null, go: () => onNavigate("landing") },
    { label: "How it works", active: section === "how", go: () => onSection("how") },
    { label: "Shop", active: view === "shop", go: () => onNavigate("shop") },
  ];
}

const BagIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" aria-hidden="true">
    <path d="M5 8h14l-1 12H6L5 8z" />
    <path d="M9 10V7a3 3 0 0 1 6 0v3" strokeLinecap="round" />
  </svg>
);

function BagButton({ cartCount, bagPulse, onOpenBag }: Pick<HeaderProps, "cartCount" | "bagPulse" | "onOpenBag">) {
  return (
    <button
      type="button"
      onClick={onOpenBag}
      aria-label={`Bag, ${cartCount} item${cartCount === 1 ? "" : "s"}`}
      className="relative inline-flex h-11 w-11 items-center justify-center rounded-full text-ink transition-colors hover:bg-surface"
    >
      <BagIcon />
      <span
        key={bagPulse}
        aria-hidden="true"
        className="bag-bump absolute top-1 right-0.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-ink px-1 text-[10px] font-semibold text-surface"
      >
        {cartCount}
      </span>
    </button>
  );
}

/**
 * Edition 2 header. Desktop: slim sticky bar (logo · Discover, How it works, Shop · My Routine, bag).
 * Mobile: logo, bag and a menu button; on the landing page it floats over the hero as frosted pills.
 */
export function Header(props: HeaderProps) {
  const { view, section, routineAvailable, onNavigate } = props;
  const floating = view === "landing";
  const pill = floating ? "max-md:bg-surface/90 max-md:shadow-sm max-md:backdrop-blur" : "";
  // The menu is tied to the route it was opened on, so any navigation (including Back/Forward) closes it.
  const routeKey = `${view}|${section ?? ""}`;
  const [menuOpenAt, setMenuOpenAt] = useState<string | null>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const menuOpen = menuOpenAt === routeKey;
  const items = navItems(props);
  const link = (active: boolean) =>
    `min-h-11 items-center px-3 text-[13px] tracking-[0.02em] transition-colors hover:text-ink ${
      active ? "text-ink underline decoration-terra decoration-[1.5px] underline-offset-[9px]" : "text-ink-soft"
    }`;

  return (
    <header
      className={`${
        floating ? "absolute inset-x-0 top-0" : "sticky top-0 border-b border-line bg-bg/92 backdrop-blur"
      } z-40 md:sticky md:border-b md:border-line md:bg-bg/92 md:backdrop-blur`}
    >
      <div className="mx-auto flex max-w-[1280px] items-center justify-between gap-4 px-4 py-3 md:grid md:grid-cols-[1fr_auto_1fr] md:px-16 md:py-2.5">
        {/* mobile: menu button on the left, before the logo */}
        <div className={`flex items-center justify-self-start rounded-full ${pill}`}>
          <button
            ref={menuButton}
            type="button"
            onClick={() => setMenuOpenAt(routeKey)}
            aria-label="Open menu"
            aria-haspopup="dialog"
            aria-expanded={menuOpen}
            aria-controls="site-menu"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full transition-colors hover:bg-surface md:hidden"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
              <path d="M4 8h16M4 16h16" />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => onNavigate("landing")}
            aria-label="GlowCue home"
            className="inline-flex min-h-11 items-center gap-2.5 rounded-full pr-4 pl-1 md:pl-1.5"
          >
            <CueMark size={30} />
            <span className="font-display text-[22px] tracking-tight md:text-[24px]">GlowCue</span>
          </button>
        </div>

        <nav aria-label="Main" className="hidden items-center gap-3 md:flex">
          {items.map((item) => (
            <button key={item.label} type="button" onClick={item.go} aria-current={item.active ? "page" : undefined} className={`inline-flex ${link(item.active)}`}>
              {item.label}
            </button>
          ))}
        </nav>

        <div className={`flex items-center gap-1 justify-self-end rounded-full ${pill}`}>
          {routineAvailable && (
            <button
              type="button"
              onClick={() => onNavigate("routine")}
              aria-current={view === "routine" ? "page" : undefined}
              className={`hidden md:mr-2 md:inline-flex ${link(view === "routine")}`}
            >
              My Routine
            </button>
          )}
          <BagButton {...props} />
        </div>
      </div>
      {menuOpen &&
        createPortal(
          <NavMenu
            items={items}
            view={view}
            routineAvailable={routineAvailable}
            onNavigate={onNavigate}
            onClose={() => setMenuOpenAt(null)}
            returnFocus={menuButton}
          />,
          document.body,
        )}
    </header>
  );
}

/** Mobile navigation panel (slides in from the left, under the menu button). Rendered in a portal so the header's blur can't clip it. */
function NavMenu({
  items,
  view,
  routineAvailable,
  onNavigate,
  onClose,
  returnFocus,
}: {
  items: NavItem[];
  view: View;
  routineAvailable: boolean;
  onNavigate: (view: View, stage?: number) => void;
  onClose: () => void;
  returnFocus: RefObject<HTMLButtonElement | null>;
}) {
  const { panel, initialFocus, onKeyDown } = useDialog<HTMLElement, HTMLButtonElement>(true, onClose, returnFocus);

  // The panel is mobile-only: if the window widens to desktop while it is open, close it (and release the scroll lock).
  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 48rem)");
    const onChange = () => desktop.matches && onClose();
    desktop.addEventListener("change", onChange);
    return () => desktop.removeEventListener("change", onChange);
  }, [onClose]);

  const choose = (go: () => void) => {
    onClose();
    go();
  };
  const row = (active: boolean) =>
    `flex min-h-14 w-full items-center justify-between border-b border-line text-left font-display text-[28px] leading-tight tracking-tight transition-colors hover:text-terra-deep ${
      active ? "text-terra-deep italic" : "text-ink"
    }`;
  const allItems: NavItem[] = routineAvailable
    ? [...items, { label: "My Routine", active: view === "routine", go: () => onNavigate("routine") }]
    : items;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <div className="absolute inset-0 bg-ink/40 animate-fade" onClick={onClose} aria-hidden="true" />
      <section
        ref={panel}
        id="site-menu"
        role="dialog"
        aria-modal="true"
        aria-label="Menu"
        onKeyDown={onKeyDown}
        className="menu-in absolute inset-y-0 left-0 flex w-[min(86vw,360px)] flex-col overflow-y-auto bg-surface px-5 pt-3 pb-6 shadow-[30px_0_60px_-30px_rgba(0,0,0,0.5)]"
      >
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-2 font-display text-[20px] tracking-tight">
            <CueMark size={26} /> GlowCue
          </span>
          <button
            ref={initialFocus}
            type="button"
            onClick={onClose}
            aria-label="Close menu"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-line-strong hover:border-ink"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>

        <nav aria-label="Menu" className="mt-8">
          <ul className="border-t border-line">
            {allItems.map((item) => (
              <li key={item.label}>
                <button type="button" onClick={() => choose(item.go)} aria-current={item.active ? "page" : undefined} className={row(item.active)}>
                  {item.label}
                  <span aria-hidden="true" className="text-base not-italic text-muted">
                    →
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {!routineAvailable && (
          <div className="mt-6 rounded-[22px] bg-peach p-4">
            <p className="text-[13px] leading-relaxed text-terra-ink">Your routine appears here after your skin report.</p>
            <button
              type="button"
              onClick={() => choose(() => onNavigate("about", 1))}
              className="mt-3 inline-flex min-h-11 items-center rounded-full bg-terra-deep px-5 text-sm font-medium text-surface hover:bg-ink"
            >
              Start your consultation
            </button>
          </div>
        )}

        <p className="mt-auto pt-8 text-xs leading-relaxed text-muted">
          Guest session: nothing to sign up for. Your answers are used to build your recommendations and are kept in this browser session, not saved to an account.
        </p>
      </section>
    </div>
  );
}

/** Mobile tab bar, shown only after the skin report (onboarding keeps guided step navigation). */
export function MobileTabBar({ view, cartCount, onNavigate, onOpenBag }: { view: View; cartCount: number; onNavigate: (v: View) => void; onOpenBag: () => void }) {
  const tab = (target: View, label: string) => (
    <button
      type="button"
      onClick={() => onNavigate(target)}
      aria-current={view === target ? "page" : undefined}
      className={`min-h-11 pb-3 text-[11px] font-medium ${view === target ? "text-surface" : "text-peach"}`}
    >
      {label}
    </button>
  );
  return (
    <nav
      aria-label="Your edition"
      className="fixed inset-x-3 bottom-3 z-40 grid h-16 grid-cols-5 items-end rounded-3xl bg-ink px-1.5 text-center shadow-[0_20px_40px_-20px_rgba(0,0,0,0.6)] md:hidden"
    >
      {tab("results", "Report")}
      {tab("routine", "Ritual")}
      <button
        type="button"
        onClick={() => onNavigate("landing")}
        aria-label="GlowCue home"
        className="mb-5 inline-flex h-14 w-14 items-center justify-center justify-self-center rounded-full bg-surface shadow-[0_10px_24px_-8px_rgba(0,0,0,0.5)]"
      >
        <CueMark size={32} />
      </button>
      {tab("shop", "Shop")}
      <button type="button" onClick={onOpenBag} className={`min-h-11 pb-3 text-[11px] font-medium ${view === "cart" ? "text-surface" : "text-peach"}`}>
        Bag · {cartCount}
      </button>
    </nav>
  );
}

export const COSMETIC_DISCLAIMER =
  "GlowCue provides cosmetic skincare guidance, not medical diagnosis or treatment. Consult a dermatologist about medical skin concerns.";

interface FooterProps {
  onNavigate: (view: View, stage?: number) => void;
  onSection: (section: Section) => void;
  /** Leaves room for the mobile tab bar, which floats over the bottom of the page. */
  tabBarSpace?: boolean;
}

/** Site footer. Catalogue, sample-profile and payment notes live next to what they describe, not here. */
export function Footer({ onNavigate, onSection, tabBarSpace = false }: FooterProps) {
  const link = "min-h-11 text-left text-sm text-peach transition-colors hover:text-surface md:min-h-0";
  const heading = "text-[11px] font-semibold uppercase tracking-[0.16em] text-surface/60";
  return (
    <footer className={`mt-20 bg-ink text-surface ${tabBarSpace ? "max-md:pb-24" : ""}`}>
      <div className="mx-auto grid max-w-[1280px] gap-10 px-4 pt-14 pb-10 md:grid-cols-[1.5fr_1fr_1fr] md:gap-12 md:px-16">
        <div className="flex max-w-sm flex-col gap-4">
          <button type="button" onClick={() => onNavigate("landing")} className="inline-flex items-center gap-2.5 self-start" aria-label="GlowCue home">
            <span className="inline-flex rounded-full bg-surface p-0.5">
              <CueMark size={30} />
            </span>
            <span className="font-display text-[26px] tracking-tight">GlowCue</span>
          </button>
          <p className="display text-[22px] leading-snug text-peach">
            Know your skin. <span className="italic">Choose with confidence.</span>
          </p>
          <p className="text-sm leading-relaxed text-surface/70">
            One skin scan becomes the best routine your budget can buy, with a clear reason for every product.
          </p>
        </div>

        <nav aria-label="Footer" className="flex flex-col gap-2 md:gap-3">
          <p className={heading}>Explore</p>
          <button type="button" className={link} onClick={() => onNavigate("landing")}>
            Discover
          </button>
          <button type="button" className={link} onClick={() => onSection("how")}>
            How it works
          </button>
          <button type="button" className={link} onClick={() => onNavigate("shop")}>
            Shop the range
          </button>
          <button type="button" className={link} onClick={() => onNavigate("about", 1)}>
            Start your consultation
          </button>
        </nav>

        <div className="flex flex-col gap-2 md:gap-3">
          <p className={heading}>Your privacy</p>
          <ul className="flex flex-col gap-2 text-sm leading-relaxed text-surface/70 md:gap-3">
            <li>Photos are analysed only with your consent.</li>
            <li>GlowCue never stores your photo.</li>
            <li>Your answers build your recommendations and stay in this browser session, not in an account.</li>
          </ul>
        </div>
      </div>

      <div className="border-t border-surface/15">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-3 px-4 py-6 text-xs leading-relaxed text-surface/60 md:flex-row md:items-start md:justify-between md:gap-12 md:px-16">
          <p className="shrink-0">© 2026 GlowCue</p>
          <p className="max-w-[640px] md:text-right">{COSMETIC_DISCLAIMER}</p>
        </div>
      </div>
    </footer>
  );
}

export function Page({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return <main className={`mx-auto ${wide ? "max-w-[1280px]" : "max-w-6xl"} px-4 py-8 sm:py-12 md:px-16`}>{children}</main>;
}
