"use client";

import { useState, useCallback } from "react";
import { ingestFile } from "@/lib/api";
import type {
  IngestionEvent,
  IngestionPhase,
  PipelinePhase,
  EnrichedChunk,
  PhaseStatus,
} from "@/types";

const PIPELINE_PHASES: PipelinePhase[] = [
  { id: "parsing", label: "Restructuring", icon: "📄", status: "pending", message: "" },
  { id: "chunking", label: "Chunking", icon: "✂️", status: "pending", message: "" },
  { id: "enrichment", label: "Enrichment", icon: "🧠", status: "pending", message: "" },
  { id: "indexing", label: "Indexing", icon: "📦", status: "pending", message: "" },
];

export interface UseIngestReturn {
  /** Current pipeline phases with status */
  phases: PipelinePhase[];
  /** Enriched chunks from the pipeline */
  enrichedChunks: EnrichedChunk[];
  /** Whether the pipeline is currently running */
  isProcessing: boolean;
  /** Whether the pipeline completed successfully */
  isComplete: boolean;
  /** Error message if the pipeline failed */
  error: string | null;
  /** Trigger file ingestion */
  startIngestion: (file: File) => void;
  /** Reset the pipeline state */
  reset: () => void;
}

export function useIngest(): UseIngestReturn {
  const [phases, setPhases] = useState<PipelinePhase[]>(
    PIPELINE_PHASES.map((p) => ({ ...p }))
  );
  const [enrichedChunks, setEnrichedChunks] = useState<EnrichedChunk[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updatePhase = useCallback(
    (phaseId: IngestionPhase, status: PhaseStatus, message: string) => {
      setPhases((prev) =>
        prev.map((p) => (p.id === phaseId ? { ...p, status, message } : p))
      );
    },
    []
  );

  const startIngestion = useCallback(
    (file: File) => {
      setIsProcessing(true);
      setIsComplete(false);
      setError(null);
      setEnrichedChunks([]);
      setPhases(PIPELINE_PHASES.map((p) => ({ ...p })));

      ingestFile(
        file,
        (event: IngestionEvent) => {
          // Update the corresponding phase
          updatePhase(event.phase, event.status, event.message);

          // Collect enriched chunks
          if (event.enriched_chunks?.length > 0) {
            setEnrichedChunks(event.enriched_chunks);
          }

          if (event.phase === "error") {
            setError(event.error || "Unknown error");
          }

          if (event.phase === "complete") {
            setIsComplete(true);
          }
        },
        (errMsg: string) => {
          setError(errMsg);
          setIsProcessing(false);
        },
        () => {
          setIsProcessing(false);
        }
      );
    },
    [updatePhase]
  );

  const reset = useCallback(() => {
    setPhases(PIPELINE_PHASES.map((p) => ({ ...p })));
    setEnrichedChunks([]);
    setIsProcessing(false);
    setIsComplete(false);
    setError(null);
  }, []);

  return {
    phases,
    enrichedChunks,
    isProcessing,
    isComplete,
    error,
    startIngestion,
    reset,
  };
}
