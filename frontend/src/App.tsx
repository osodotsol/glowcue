import { useEffect, type JSX } from "react";
import { BagDrawer } from "./components/BagDrawer";
import { Footer, Header, MobileTabBar } from "./components/Layout";
import { AboutYou } from "./pages/AboutYou";
import { Cart } from "./pages/Cart";
import { Checkout } from "./pages/Checkout";
import { Landing } from "./pages/Landing";
import { Results } from "./pages/Results";
import { Routine } from "./pages/Routine";
import { Selfie } from "./pages/Selfie";
import { Shop } from "./pages/Shop";
import { AppStateProvider, scrollToSection, useApp, type View } from "./state/AppState";


// Simple in-app navigation (no router dependency): one page component per step.
const PAGES: Record<View, () => JSX.Element> = {
  landing: Landing,
  about: AboutYou,
  selfie: Selfie,
  results: Results,
  routine: Routine,
  shop: Shop,
  cart: Cart,
  checkout: Checkout,
};

const POST_REPORT: View[] = ["results", "routine", "shop", "cart", "checkout"];

function Shell() {
  const { view, go, section, goSection, cartCount, bagPulse, catalogue, analysis, setBagOpen } = useApp();
  const CurrentPage = PAGES[view];
  const tabBar = analysis !== null && POST_REPORT.includes(view);

  // "#/how" renders the landing page scrolled to its How-it-works section. Re-run once the catalogue arrives,
  // because the product rows above the section change the page height.
  useEffect(() => {
    if (!section) return;
    const frame = requestAnimationFrame(() => scrollToSection(section));
    return () => cancelAnimationFrame(frame);
  }, [section, catalogue]);
  return (
    <div className="relative flex min-h-screen flex-col bg-bg text-ink">
      {/* a button, not href="#content": the URL hash is reserved for navigation */}
      <button
        type="button"
        onClick={() => document.getElementById("content")?.focus()}
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded focus:bg-surface focus:p-2"
      >
        Skip to content
      </button>
      <Header
        view={view}
        section={section}
        routineAvailable={analysis !== null}
        cartCount={cartCount}
        bagPulse={bagPulse}
        onNavigate={go}
        onSection={goSection}
        onOpenBag={() => setBagOpen(true)}
      />
      <div id="content" tabIndex={-1} className="flex-1 outline-none">
        <CurrentPage />
      </div>
      <Footer onNavigate={go} onSection={goSection} tabBarSpace={tabBar} />
      {tabBar && <MobileTabBar view={view} cartCount={cartCount} onNavigate={go} onOpenBag={() => setBagOpen(true)} />}
      <BagDrawer />
    </div>
  );
}

export default function App() {
  return (
    <AppStateProvider>
      <Shell />
    </AppStateProvider>
  );
}
