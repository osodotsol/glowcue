// The only module that talks to the backend. Demo analysis takes a profile id only; a photo is sent ONLY by
// startLiveAnalysis, after the customer has explicitly agreed, and only as a cleaned JPEG (lib/imagePrep.ts).
import type {
  AnalysisJob,
  CartItem,
  CartQuote,
  Catalogue,
  DemoProfile,
  NormalizedAnalysis,
  Preferences,
  PublicConfig,
  RecommendationResult,
  SkinType,
} from "./types";
import { CONNECTION_ERROR, friendlyForHttpFailure, isServiceUnavailableStatus } from "./errors";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly code: string;
  readonly retryable: boolean;
  constructor(code: string, message: string, retryable = false) {
    super(message);
    this.code = code;
    this.retryable = retryable;
  }
}

/** Technical details for developers only (the console). Never the request body, so a photo can never reach a log. */
function logRequestFailure(path: string, reason: string | number, cause?: unknown) {
  const detail = cause instanceof Error ? `${cause.name}: ${cause.message}` : undefined;
  console.warn("[glowcue] request failed", { path, reason, online: navigator.onLine, detail });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}/api${path}`, {
      ...init,
      headers: init?.headers ?? (init?.body ? { "Content-Type": "application/json" } : undefined),
    });
  } catch (cause) {
    logRequestFailure(path, "network", cause);
    throw new ApiError("network", CONNECTION_ERROR.message, true);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const err = (body as { error?: { code?: string; message?: string; retryable?: boolean } } | null)?.error;
    if (err?.message) {
      // GlowCue's own answer (already written for customers): keep it.
      throw new ApiError(err.code ?? "http_error", err.message, !!err.retryable);
    }
    // No message of its own, for example a gateway page while the service starts up: say so plainly.
    logRequestFailure(path, response.status);
    const friendly = friendlyForHttpFailure(response.status);
    const unavailable = isServiceUnavailableStatus(response.status);
    throw new ApiError(unavailable ? "unavailable" : (err?.code ?? "http_error"), friendly.message, response.status >= 500);
  }
  return body as T;
}

const post = <T>(path: string, payload: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(payload) });

export const api = {
  config: () => request<PublicConfig>("/config"),
  demoProfiles: () => request<DemoProfile[]>("/demo-profiles"),
  demoAnalysis: (profileId: string) => post<NormalizedAnalysis>("/analyses/demo", { profile_id: profileId }),
  /** Live cosmetic analysis by YouCam. Call only after explicit consent; `photo` must be a cleaned JPEG. */
  startLiveAnalysis: (photo: Blob) =>
    request<AnalysisJob>("/analyses?consent=true", { method: "POST", body: photo, headers: { "Content-Type": "image/jpeg" } }),
  liveAnalysis: (analysisId: string) => request<AnalysisJob>(`/analyses/${encodeURIComponent(analysisId)}`),
  catalogue: () => request<Catalogue>("/catalogue"),
  recommend: (analysis: NormalizedAnalysis, preferences: Preferences) =>
    post<RecommendationResult>("/recommendations", {
      metrics: analysis.metrics.map((m) => ({ key: m.key, raw_score: m.raw_score })),
      skin_type: analysis.skin_type as SkinType | null,
      preferences,
    }),
  quote: (items: CartItem[]) => post<CartQuote>("/cart/quote", { items }),
};
