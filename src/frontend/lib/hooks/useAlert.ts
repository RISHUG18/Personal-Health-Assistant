"use client";

import { useState, useCallback } from "react";

export type AlertType = "success" | "error" | "warning" | "info";

interface Alert {
  id: string;
  type: AlertType;
  title: string;
  message: string;
  duration?: number;
}

/**
 * useToastAlert - Hook for displaying toast notifications
 *
 * Usage:
 * ```tsx
 * const { showAlert, alerts } = useToastAlert();
 *
 * const handleSubmit = async () => {
 *   try {
 *     await api.submit(data);
 *     showAlert("success", "Success", "Data submitted successfully");
 *   } catch (error) {
 *     showAlert("error", "Failed", error.message);
 *   }
 * };
 * ```
 */
export function useToastAlert() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const showAlert = useCallback(
    (
      type: AlertType,
      title: string,
      message: string,
      duration = 5000
    ) => {
      const id = Date.now().toString();
      const alert: Alert = { id, type, title, message, duration };

      setAlerts(prev => [...prev, alert]);

      if (duration > 0) {
        setTimeout(() => {
          setAlerts(prev => prev.filter(a => a.id !== id));
        }, duration);
      }

      return id;
    },
    []
  );

  const removeAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  }, []);

  return { alerts, showAlert, removeAlert };
}

/**
 * Error utilities for API responses
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function parseApiError(response: Response): Promise<ApiError> {
  let data;
  try {
    data = await response.json();
  } catch {
    data = { message: response.statusText };
  }

  const message = (data as any)?.message || response.statusText || "Unknown error";
  return new ApiError(response.status, message, data);
}

/**
 * handleApiError - Convert API errors to user-friendly messages
 */
export function handleApiError(error: unknown): {
  title: string;
  message: string;
  severity: "info" | "warning" | "error";
} {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return {
          title: "Not found",
          message: "The resource you're looking for doesn't exist",
          severity: "info",
        };
      case 401:
      case 403:
        return {
          title: "Access denied",
          message: "You don't have permission to perform this action",
          severity: "warning",
        };
      case 422:
        return {
          title: "Invalid data",
          message: error.message || "Please check your input and try again",
          severity: "warning",
        };
      case 429:
        return {
          title: "Too many requests",
          message: "Please wait a moment before trying again",
          severity: "warning",
        };
      case 500:
      case 502:
      case 503:
        return {
          title: "Server error",
          message: "Something went wrong on our end. Please try again later",
          severity: "error",
        };
      default:
        return {
          title: "Error",
          message: error.message || "An error occurred",
          severity: "error",
        };
    }
  }

  if (error instanceof TypeError) {
    return {
      title: "Connection error",
      message: "Unable to reach the server. Check your internet connection",
      severity: "warning",
    };
  }

  return {
    title: "Unexpected error",
    message: error instanceof Error ? error.message : "Something went wrong",
    severity: "error",
  };
}
