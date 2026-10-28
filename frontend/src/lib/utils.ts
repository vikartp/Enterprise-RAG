/* Utility functions */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes with clsx for conditional classnames */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** API base URL from environment */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Format a score as a percentage */
export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

/** Truncate text to a max length */
export function truncate(text: string, maxLen: number = 200): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + "…";
}

/** Generate a unique ID */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
