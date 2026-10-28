"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Hash,
  HelpCircle,
  FileCode,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIngest } from "@/hooks/use-ingest";
import type { EnrichedChunk, PipelinePhase } from "@/types";

const ACCEPTED_FILES = {
  "application/pdf": [".pdf"],
  "text/markdown": [".md"],
  "text/plain": [".txt"],
  "text/csv": [".csv"],
};

export default function IngestPage() {
  const {
    phases,
    enrichedChunks,
    isProcessing,
    isComplete,
    error,
    startIngestion,
    reset,
  } = useIngest();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setSelectedFile(file);
        startIngestion(file);
      }
    },
    [startIngestion]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILES,
    maxFiles: 1,
    disabled: isProcessing,
  });

  return (
    <div className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          Document <span className="gradient-text">Ingestion</span>
        </h1>
        <p className="text-muted-foreground mt-2">
          Upload documents to process through the RAG pipeline — restructuring,
          chunking, enrichment, and vector indexing.
        </p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          "glass-card p-12 text-center cursor-pointer transition-all duration-300",
          "border-2 border-dashed border-border hover:border-primary/50",
          isDragActive && "dropzone-active",
          isProcessing && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          {selectedFile && !isProcessing && isComplete ? (
            <CheckCircle2 className="w-12 h-12 text-success" />
          ) : isProcessing ? (
            <Loader2 className="w-12 h-12 text-primary animate-spin" />
          ) : (
            <Upload className="w-12 h-12 text-muted-foreground" />
          )}

          {isDragActive ? (
            <p className="text-lg font-medium text-primary">Drop your file here</p>
          ) : selectedFile ? (
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-primary" />
              <span className="font-medium">{selectedFile.name}</span>
              <span className="text-xs text-muted-foreground">
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>
          ) : (
            <>
              <p className="text-lg font-medium">
                Drag & drop a document, or{" "}
                <span className="text-primary">click to browse</span>
              </p>
              <p className="text-sm text-muted-foreground">
                Supports PDF, Markdown, TXT, CSV — Max 50MB
              </p>
            </>
          )}
        </div>
      </div>

      {/* Pipeline Visualizer */}
      {(isProcessing || isComplete || error) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8"
        >
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Processing Pipeline
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            {phases.map((phase, index) => (
              <PhaseCard key={phase.id} phase={phase} index={index} />
            ))}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20 flex items-start gap-3"
            >
              <XCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-destructive">Pipeline Error</p>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Chunk Inspector */}
      {enrichedChunks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileCode className="w-5 h-5 text-secondary" />
              Chunk Inspector
              <span className="text-sm font-normal text-muted-foreground">
                ({enrichedChunks.length} chunks)
              </span>
            </h2>
            <button
              onClick={reset}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Upload another file
            </button>
          </div>

          <div className="space-y-3">
            {enrichedChunks.map((chunk, i) => (
              <ChunkCard key={chunk.chunk_id} chunk={chunk} index={i} />
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

/* ===== Phase Card ===== */
function PhaseCard({ phase, index }: { phase: PipelinePhase; index: number }) {
  const statusConfig = {
    pending: { color: "text-muted", bg: "bg-muted/10", icon: null },
    in_progress: {
      color: "text-primary",
      bg: "bg-primary/10",
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
    },
    complete: {
      color: "text-success",
      bg: "bg-success/10",
      icon: <CheckCircle2 className="w-4 h-4" />,
    },
    error: {
      color: "text-destructive",
      bg: "bg-destructive/10",
      icon: <XCircle className="w-4 h-4" />,
    },
  };

  const config = statusConfig[phase.status];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1 }}
      className={cn(
        "glass-card p-4 relative overflow-hidden transition-all duration-300",
        phase.status === "in_progress" && "glow-primary"
      )}
    >
      {/* Progress bar */}
      {phase.status === "in_progress" && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary/20 overflow-hidden">
          <div className="h-full w-1/3 bg-primary animate-[slide_1.5s_ease-in-out_infinite] rounded-full" />
        </div>
      )}

      <div className="flex items-center justify-between mb-2">
        <span className="text-lg">{phase.icon}</span>
        <span className={cn("flex items-center gap-1", config.color)}>
          {config.icon}
        </span>
      </div>
      <h3 className="text-sm font-semibold">{phase.label}</h3>
      {phase.message && (
        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
          {phase.message}
        </p>
      )}
    </motion.div>
  );
}

/* ===== Chunk Card ===== */
function ChunkCard({ chunk, index }: { chunk: EnrichedChunk; index: number }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="glass-card overflow-hidden"
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-card-hover transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xs font-mono text-muted-foreground bg-card px-2 py-1 rounded">
            #{index + 1}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">
              {chunk.section_header || chunk.source_file}
            </p>
            <p className="text-xs text-muted-foreground truncate">{chunk.summary}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-muted-foreground">
            {chunk.hypothetical_questions.length} Q&apos;s
          </span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-border"
          >
            <div className="p-4 space-y-4">
              {/* Chunk text */}
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Content
                </h4>
                <pre className="text-sm bg-card p-3 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono text-foreground/80">
                  {chunk.content}
                </pre>
              </div>

              {/* Summary */}
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> Summary
                </h4>
                <p className="text-sm text-foreground/80">{chunk.summary}</p>
              </div>

              {/* Keywords */}
              {chunk.keywords.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                    <Hash className="w-3 h-3" /> Keywords
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {chunk.keywords.map((kw) => (
                      <span
                        key={kw}
                        className="px-2 py-1 text-xs rounded-md bg-primary/10 text-primary border border-primary/20"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Hypothetical Questions */}
              {chunk.hypothetical_questions.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                    <HelpCircle className="w-3 h-3" /> Hypothetical Questions
                  </h4>
                  <ul className="space-y-1">
                    {chunk.hypothetical_questions.map((q, i) => (
                      <li
                        key={i}
                        className="text-sm text-foreground/80 flex items-start gap-2"
                      >
                        <span className="text-accent mt-0.5">•</span>
                        {q}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
