"use client";

import { useState, useCallback } from "react";

export type AsyncState = "idle" | "loading" | "success" | "error";

interface UseAsyncOptions {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

/**
 * useAsync - Hook for managing async operations with loading/error states
 *
 * Usage:
 * ```tsx
 * const { state, data, error, execute } = useAsync(
 *   async () => await fetchData()
 * );
 *
 * return (
 *   <>
 *     {state === 'loading' && <Spinner />}
 *     {state === 'error' && <ErrorFallback message={error?.message} />}
 *     {state === 'success' && <Data data={data} />}
 *   </>
 * );
 * ```
 */
export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate = false,
  options?: UseAsyncOptions
) {
  const [state, setState] = useState<AsyncState>(immediate ? "loading" : "idle");
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const response = await asyncFunction();
      setData(response);
      setState("success");
      options?.onSuccess?.();
      return response;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setError(err);
      setState("error");
      options?.onError?.(err);
      throw err;
    }
  }, [asyncFunction, options]);

  return { state, data, error, execute };
}

/**
 * useFetch - Hook for GET requests
 *
 * Usage:
 * ```tsx
 * const { state, data, refetch } = useFetch<ReportData>("/api/reports");
 * ```
 */
export function useFetch<T>(
  url: string,
  options?: UseAsyncOptions
) {
  const { state, data, error, execute } = useAsync<T>(
    () => fetch(url).then(res => {
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return res.json();
    }),
    true,
    options
  );

  return { state, data, error, refetch: execute };
}

/**
 * useApiCall - Hook for any API method with error handling
 *
 * Usage:
 * ```tsx
 * const { state, mutate } = useApiCall(
 *   (data) => fetch("/api/endpoint", {
 *     method: "POST",
 *     body: JSON.stringify(data)
 *   })
 * );
 * ```
 */
export function useApiCall<T, R = void>(
  apiFunction: (payload: T) => Promise<R>,
  options?: UseAsyncOptions
) {
  const [state, setState] = useState<AsyncState>("idle");
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<R | null>(null);

  const mutate = useCallback(
    async (payload: T) => {
      setState("loading");
      setError(null);
      try {
        const response = await apiFunction(payload);
        setData(response);
        setState("success");
        options?.onSuccess?.();
        return response;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        setState("error");
        options?.onError?.(error);
        throw error;
      }
    },
    [apiFunction, options]
  );

  return { state, data, error, mutate };
}
