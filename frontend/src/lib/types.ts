// Mirrors backend/app/models.py (docs/DATA_MODEL.md). Keep in sync when the API changes.

export type ConcernKey =
  | "oiliness"
  | "moisture"
  | "texture"
  | "pore"
  | "acne"
  | "redness"
  | "age_spot"
  | "wrinkle"
  | "dark_circles";
export type Band = "priority" | "watch" | "good" | "not_measured";
export type SkinType = "normal" | "oily" | "dry" | "combination";
export type Category = "cleanser" | "toner_exfoliant" | "serum" | "eye" | "moisturiser" | "sunscreen";
export type RoutineSize = "minimal" | "balanced" | "complete";
export type Pack = "pump" | "tube" | "dropper" | "jar" | "bottle";

export const CONCERN_LABELS: Record<ConcernKey, string> = {
  oiliness: "Shine & oiliness",
  moisture: "Hydration",
  texture: "Texture",
  pore: "Pores",
  acne: "Blemishes",
  redness: "Redness",
  age_spot: "Dark spots",
  wrinkle: "Fine lines",
  dark_circles: "Under-eye circles",
};

export const CATEGORY_LABELS: Record<Category, string> = {
  cleanser: "Cleanser",
  toner_exfoliant: "Exfoliating toner",
  serum: "Serum",
  eye: "Eye care",
  moisturiser: "Moisturiser",
  sunscreen: "Sunscreen",
};

export interface Metric {
  key: ConcernKey;
  label: string;
  raw_score: number | null;
  ui_score: number | null;
  band: Band;
}

export interface NormalizedAnalysis {
  analysis_id: string;
  mode: "demo" | "live";
  provider: string;
  is_demo: boolean;
  profile_id: string | null;
  metrics: Metric[];
  skin_type: SkinType | null;
  notice: string;
}

/** A friendly error from the API. `retake` means another photo (light, framing, angle) is likely to fix it. */
export interface ErrorDetail {
  code: string;
  message: string;
  retryable: boolean;
  retake: boolean;
}

/** Live analysis of a selfie: poll until it is no longer "running". Mirrors backend models.AnalysisJob. */
export interface AnalysisJob {
  analysis_id: string;
  status: "running" | "success" | "error";
  analysis: NormalizedAnalysis | null;
  error: ErrorDetail | null;
}

export interface DemoProfile {
  id: string;
  name: string;
  summary: string;
}

export interface Product {
  id: string;
  name: string;
  brand: "GlowCue Demo";
  category: Category;
  description: string;
  key_ingredients: string[];
  ingredients_inci: string;
  targets: Partial<Record<ConcernKey, number>>;
  skin_types: SkinType[];
  time_of_day: ("am" | "pm")[];
  frequency: "daily" | "2-3x weekly";
  usage: string;
  actives: string[];
  fragrance_free: boolean;
  sensitive_ok: boolean;
  cautions: string[];
  price: number;
  currency: "NGN";
  pack: Pack;
  source: "fictional_demo";
}

export interface Catalogue {
  disclaimer: string;
  currency: "NGN";
  products: Product[];
}

export interface Preferences {
  budget: number;
  owned: Category[];
  concerns: ConcernKey[];
  skin_type: SkinType | null;
  fragrance_free: boolean;
  sensitive: boolean;
  routine_size: RoutineSize;
  pinned: string[];
}

export interface Priority {
  key: ConcernKey;
  label: string;
  band: Band;
  raw_score: number | null;
  self_reported: boolean;
  why_text: string;
}

export interface Receipt {
  concern_key: ConcernKey | null;
  metric_raw_score: number | null;
  ingredient: string;
  claim_text: string;
}

export interface Alternative {
  product_id: string;
  price_delta: number;
  coverage_pct: number;
  within_budget: boolean;
}

export interface SelectedProduct {
  product_id: string;
  slot: Category;
  receipts: Receipt[];
  alternatives: Alternative[];
}

export interface Step {
  order: number;
  product_id: string;
  instruction: string;
  frequency: "daily" | "2-3x weekly";
  note: string | null;
}

export interface RecommendationResult {
  mode: "targeted" | "maintenance";
  priorities: Priority[];
  selected: SelectedProduct[];
  routine: { am: Step[]; pm: Step[] };
  coverage_pct: number;
  total: number;
  budget: number;
  currency: "NGN";
  budget_status: "within" | "over";
  over_by: number;
  warnings: string[];
  skipped_owned: Category[];
  excluded: string[];
  unaddressed: ConcernKey[];
}

export interface CartItem {
  product_id: string;
  qty: number;
}

export interface CartQuote {
  lines: { product_id: string; name: string; qty: number; unit_price: number; line_total: number }[];
  subtotal: number;
  currency: "NGN";
  item_count: number;
  notice: string;
}

export interface PublicConfig {
  mode: "demo" | "live";
  live_enabled: boolean;
  currency: "NGN";
  budget_default: number;
  budget_min: number;
  budget_max: number;
  disclaimer: string;
}
