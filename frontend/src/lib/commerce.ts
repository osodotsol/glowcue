import { useCallback } from "react";
import { useApp } from "../state/AppState";
import { api } from "./api";
import type { Category, Product } from "./types";
import { useRemote } from "./useRemote";

/** Server-side quote of the current bag: prices always come from the catalogue on the server. */
export function useQuote() {
  const { cart } = useApp();
  const fetcher = useCallback(() => api.quote(cart), [cart]);
  return useRemote(cart.length ? JSON.stringify(cart) : null, fetcher, 150);
}

export const CORE: Category[] = ["cleanser", "moisturiser", "sunscreen"];

export function timeLabel(p: Product): string {
  const am = p.time_of_day.includes("am");
  const pm = p.time_of_day.includes("pm");
  if (p.category === "sunscreen") return "AM · always last";
  return am && pm ? "AM · PM" : am ? "AM only" : "PM only";
}

const ORDER: Record<Category, number> = { cleanser: 0, toner_exfoliant: 1, serum: 2, eye: 3, moisturiser: 4, sunscreen: 5 };

/** Suggested order for a printable ritual card built from whatever is in the bag. */
export function ritualOrder(products: Product[], time: "am" | "pm"): Product[] {
  return products
    .filter((p) => p.time_of_day.includes(time) && !(time === "pm" && p.category === "sunscreen"))
    .sort((a, b) => ORDER[a.category] - ORDER[b.category] || a.id.localeCompare(b.id));
}
