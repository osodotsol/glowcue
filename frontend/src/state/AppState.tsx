import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../lib/api";
import { prefersReducedMotion, withTransition } from "../lib/motion";
import type { CartItem, Catalogue, NormalizedAnalysis, Preferences, Product, PublicConfig } from "../lib/types";

export type View = "landing" | "about" | "selfie" | "results" | "routine" | "shop" | "cart" | "checkout";
const VIEWS: View[] = ["landing", "about", "selfie", "results", "routine", "shop", "cart", "checkout"];
export const CONSULT_STAGES = 4;
/** Landing-page sections with their own route ("#/how"), so Back, Forward and reload return to them. */
export type Section = "how";
const SECTIONS: Section[] = ["how"];

const DEFAULT_PREFS: Preferences = {
  budget: 30000,
  owned: [],
  concerns: [],
  skin_type: null,
  fragrance_free: false,
  sensitive: false,
  routine_size: "balanced",
  pinned: [],
};

// ---------------------------------------------------------------- URL hash <-> view
// "#/", "#/about/2", "#/routine" ... so Back, Forward and reload keep the customer's place.
interface Route {
  view: View;
  stage: number;
  section: Section | null;
}

function parseHash(hash: string): Route {
  const [, name = "", sub] = hash.replace(/^#/, "").split("/");
  if ((SECTIONS as string[]).includes(name)) return { view: "landing", stage: 1, section: name as Section };
  const view = (VIEWS as string[]).includes(name) ? (name as View) : "landing";
  const stage = Math.min(CONSULT_STAGES, Math.max(1, Number(sub) || 1));
  return { view, stage, section: null };
}

/** Scroll a landing section (element id = section name) into view, clear of the sticky header. */
export function scrollToSection(section: Section) {
  const el = document.getElementById(section);
  if (!el) return;
  const header = document.querySelector("header");
  const offset = header && getComputedStyle(header).position === "sticky" ? header.offsetHeight : 0;
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - offset - 16, behavior: prefersReducedMotion() ? "auto" : "smooth" });
}

function hashFor(view: View, stage: number): string {
  if (view === "landing") return "#/";
  return view === "about" ? `#/about/${stage}` : `#/${view}`;
}

// ---------------------------------------------------------------- session storage
// sessionStorage holds ONLY preferences, demo scores and cart ids/quantities: never photos.
const STORE_KEY = "glowcue.session.v1";
interface Stored {
  preferences: Preferences;
  analysis: NormalizedAnalysis | null;
  cart: CartItem[];
}

function loadStored(): Stored {
  try {
    const raw = sessionStorage.getItem(STORE_KEY);
    if (raw) return { preferences: DEFAULT_PREFS, analysis: null, cart: [], ...(JSON.parse(raw) as Partial<Stored>) };
  } catch {
    /* storage unavailable: start fresh */
  }
  return { preferences: DEFAULT_PREFS, analysis: null, cart: [] };
}

const isPristine = (s: Stored) =>
  s.analysis === null && s.cart.length === 0 && JSON.stringify(s.preferences) === JSON.stringify(DEFAULT_PREFS);

/** Pure, immutable cart update: never mutates the previous state (safe under React StrictMode). */
export function addItems(items: CartItem[], ids: string[]): CartItem[] {
  return ids.reduce<CartItem[]>(
    (acc, id) =>
      acc.some((i) => i.product_id === id)
        ? acc.map((i) => (i.product_id === id ? { ...i, qty: Math.min(10, i.qty + 1) } : i))
        : [...acc, { product_id: id, qty: 1 }],
    items,
  );
}

interface AppState {
  view: View;
  consultStage: number;
  go: (view: View, stage?: number) => void;
  section: Section | null;
  goSection: (section: Section) => void;
  config: PublicConfig | null;
  catalogue: Catalogue | null;
  productById: Map<string, Product>;
  loadError: string | null;
  retryLoad: () => void;
  preferences: Preferences;
  setPreferences: (update: Partial<Preferences>) => void;
  photoUrl: string | null;
  setPhoto: (file: File | null) => void;
  analysis: NormalizedAnalysis | null;
  setAnalysis: (analysis: NormalizedAnalysis | null) => void;
  cart: CartItem[];
  addToCart: (productIds: string[]) => void;
  setQty: (productId: string, qty: number) => void;
  cartCount: number;
  bagOpen: boolean;
  setBagOpen: (open: boolean) => void;
  bagPulse: number; // increments on every add, drives the counter bump
  resetAll: () => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [stored] = useState(loadStored);
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [preferences, setPrefs] = useState<Preferences>(stored.preferences);
  const [analysis, setAnalysis] = useState<NormalizedAnalysis | null>(stored.analysis);
  const [cart, setCart] = useState<CartItem[]>(stored.cart);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [bagOpen, setBagOpen] = useState(false);
  const [bagPulse, setBagPulse] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.config(), api.catalogue()])
      .then(([cfg, cat]) => {
        if (cancelled) return;
        setConfig(cfg);
        setCatalogue(cat);
        setLoadError(null);
      })
      .catch((e: Error) => !cancelled && setLoadError(e.message));
    return () => {
      cancelled = true;
    };
  }, [loadAttempt]);

  // Persist; a pristine session is removed instead of written, so "clear my data" really clears.
  useEffect(() => {
    try {
      const next: Stored = { preferences, analysis, cart };
      if (isPristine(next)) sessionStorage.removeItem(STORE_KEY);
      else sessionStorage.setItem(STORE_KEY, JSON.stringify(next));
    } catch {
      /* storage full or blocked: the app still works for this tab */
    }
  }, [preferences, analysis, cart]);

  // Browser Back/Forward (and manual hash edits) drive the view.
  useEffect(() => {
    const onHash = () => withTransition(() => setRoute(parseHash(window.location.hash)));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // Release the in-memory photo when it changes or the app unmounts.
  useEffect(() => () => void (photoUrl && URL.revokeObjectURL(photoUrl)), [photoUrl]);

  const go = useCallback((next: View, stage = 1) => {
    const hash = hashFor(next, stage);
    if (window.location.hash !== hash) window.location.hash = hash; // pushes a history entry; hashchange updates route
    else setRoute({ view: next, stage, section: null });
    setBagOpen(false);
    window.scrollTo({ top: 0 });
  }, []);

  const goSection = useCallback((section: Section) => {
    setBagOpen(false);
    const hash = `#/${section}`;
    if (window.location.hash !== hash) window.location.hash = hash; // the Shell scrolls once the landing page renders
    else scrollToSection(section);
  }, []);

  const setPhoto = useCallback((file: File | null) => setPhotoUrl(file ? URL.createObjectURL(file) : null), []);

  const setPreferences = useCallback((update: Partial<Preferences>) => setPrefs((p) => ({ ...p, ...update })), []);

  const addToCart = useCallback((ids: string[]) => {
    setCart((items) => addItems(items, ids));
    setBagPulse((n) => n + 1);
  }, []);

  const setQty = useCallback((id: string, qty: number) => {
    setCart((items) =>
      qty <= 0
        ? items.filter((i) => i.product_id !== id)
        : items.map((i) => (i.product_id === id ? { ...i, qty: Math.min(10, qty) } : i)),
    );
  }, []);

  const resetAll = useCallback(() => {
    setPhotoUrl(null);
    setAnalysis(null);
    setCart([]);
    setPrefs(DEFAULT_PREFS);
    setBagOpen(false);
    try {
      sessionStorage.removeItem(STORE_KEY);
    } catch {
      /* ignore */
    }
    go("landing");
  }, [go]);

  const value = useMemo<AppState>(
    () => ({
      view: route.view,
      consultStage: route.stage,
      go,
      section: route.section,
      goSection,
      config,
      catalogue,
      productById: new Map((catalogue?.products ?? []).map((p) => [p.id, p])),
      loadError,
      retryLoad: () => setLoadAttempt((n) => n + 1),
      preferences,
      setPreferences,
      photoUrl,
      setPhoto,
      analysis,
      setAnalysis,
      cart,
      addToCart,
      setQty,
      cartCount: cart.reduce((n, i) => n + i.qty, 0),
      bagOpen,
      setBagOpen,
      bagPulse,
      resetAll,
    }),
    [route, go, goSection, config, catalogue, loadError, preferences, setPreferences, photoUrl, setPhoto, analysis, cart, addToCart, setQty, bagOpen, bagPulse, resetAll],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useApp must be used inside AppStateProvider");
  return ctx;
}
