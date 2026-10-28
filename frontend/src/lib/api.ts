/* API communication helpers */

import { API_URL } from "./utils";
import type { IngestionEvent, QueryEvent } from "@/types";

/**
 * Upload a file to the ingestion endpoint and stream SSE pipeline events.
 */
export async function ingestFile(
  file: File,
  onEvent: (event: IngestionEvent) => void,
  onError: (error: string) => void,
  onComplete: () => void
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_URL}/api/ingest`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      onError(`Upload failed: ${err}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError("No response stream");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6)) as IngestionEvent;
            onEvent(data);

            if (data.phase === "complete" || data.phase === "error") {
              onComplete();
              return;
            }
          } catch {
            // Skip malformed SSE data
          }
        }
      }
    }

    onComplete();
  } catch (err) {
    onError(err instanceof Error ? err.message : "Network error");
  }
}

/**
 * Send a query and stream SSE response events (plan, retrieval, tokens, validation).
 */
export async function queryDocuments(
  query: string,
  history: { role: string; content: string }[],
  onEvent: (event: QueryEvent) => void,
  onError: (error: string) => void,
  onComplete: () => void
): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, history }),
    });

    if (!response.ok) {
      const err = await response.text();
      onError(`Query failed: ${err}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError("No response stream");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6)) as QueryEvent;
            onEvent(data);

            if (data.type === "complete" || data.type === "error") {
              onComplete();
              return;
            }
          } catch {
            // Skip malformed SSE data
          }
        }
      }
    }

    onComplete();
  } catch (err) {
    onError(err instanceof Error ? err.message : "Network error");
  }
}
