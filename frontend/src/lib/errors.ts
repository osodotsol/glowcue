// Customer-facing wording for request failures, kept in one place (pure: no DOM, so it is unit-tested in Node).
// Technical details (status codes, paths, the underlying error) go to the developer console via lib/api.ts and
// never into these messages. Customers never see words like "server", "backend", "API" or "localhost".

export interface FriendlyError {
  title: string;
  message: string;
}

/** The request never got an answer: offline, a weak connection, or the browser blocked it. */
export const CONNECTION_ERROR: FriendlyError = {
  title: "We're having trouble connecting.",
  message: "Check your internet connection or move somewhere with a stronger network, then try again.",
};

/** GlowCue answered with a gateway failure (502/503/504), for example while it is starting up. Not an internet problem. */
export const SERVICE_ERROR: FriendlyError = {
  title: "GlowCue is temporarily unavailable.",
  message: "We couldn't complete that just now. Please try again in a moment.",
};

/** Any other failure that came back without a message of its own. */
export const GENERIC_ERROR: FriendlyError = {
  title: "We couldn't load this just now",
  message: "Something went wrong. Please try again.",
};

const GATEWAY_STATUSES = new Set([502, 503, 504]);

export function isServiceUnavailableStatus(status: number): boolean {
  return GATEWAY_STATUSES.has(status);
}

/** The wording for an error response that carried no message of its own (a proxy page, an empty body, a crash). */
export function friendlyForHttpFailure(status: number): FriendlyError {
  return isServiceUnavailableStatus(status) ? SERVICE_ERROR : GENERIC_ERROR;
}

/** The title that goes with a known message; unknown messages (for example one written by the API) get the default. */
export function titleForMessage(message: string): string {
  for (const known of [CONNECTION_ERROR, SERVICE_ERROR, GENERIC_ERROR]) {
    if (message === known.message) return known.title;
  }
  return GENERIC_ERROR.title;
}
