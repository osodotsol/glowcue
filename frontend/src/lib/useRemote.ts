import { useEffect, useState } from "react";

interface Remote<T> {
  data: T | undefined;
  error: string | undefined;
  loading: boolean;
}

/**
 * Loads `fetcher()` whenever `key` changes (debounced by `delay` ms). `fetcher` must be memoised with useCallback.
 * Loading is derived from the key, so stale data never shows as current. A null key means "nothing to load".
 */
export function useRemote<T>(key: string | null, fetcher: () => Promise<T>, delay = 0): Remote<T> {
  const [state, setState] = useState<{ key: string | null; data?: T; error?: string; last?: T }>({ key: null });

  useEffect(() => {
    if (key === null) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      fetcher()
        .then((data) => !cancelled && setState({ key, data, last: data }))
        .catch((e: Error) => !cancelled && setState((s) => ({ key, error: e.message, last: s.last })));
    }, delay);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [key, fetcher, delay]);

  const current = state.key === key;
  return {
    data: current ? state.data : state.last, // keep showing the previous result while recomputing
    error: current ? state.error : undefined,
    loading: key !== null && !current,
  };
}
