/* Enterprise Agentic RAG — TypeScript type definitions */

/* ===========================
   Ingestion Pipeline Types
   =========================== */

export type IngestionPhase =
  | "uploading"
  | "parsing"
  | "chunking"
  | "enrichment"
  | "indexing"
  | "complete"
  | "error";

export type PhaseStatus = "pending" | "in_progress" | "complete" | "error";

export interface ChunkData {
  chunk_id: string;
  content: string;
  chunk_index: number;
  source_file: string;
  section_header: string | null;
  token_count: number;
}

export interface EnrichedChunk {
  chunk_id: string;
  content: string;
  chunk_index: number;
  source_file: string;
  section_header: string | null;
  summary: string;
  keywords: string[];
  hypothetical_questions: string[];
}

export interface IngestionEvent {
  phase: IngestionPhase;
  status: PhaseStatus;
  message: string;
  chunks: ChunkData[];
  enriched_chunks: EnrichedChunk[];
  point_ids: string[];
  error: string | null;
}

export interface PipelinePhase {
  id: IngestionPhase;
  label: string;
  icon: string;
  status: PhaseStatus;
  message: string;
}

/* ===========================
   Query / Chat Types
   =========================== */

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface RetrievedChunk {
  chunk_id: string;
  content: string;
  source_file: string;
  section_header: string | null;
  summary: string;
  hypothetical_questions: string[];
  dense_score: number;
  sparse_score: number;
  rrf_score: number;
  reranker_score: number;
}

export interface PlanStep {
  step_index: number;
  description: string;
  tool: string | null;
  tool_input: Record<string, unknown> | null;
  status: "pending" | "executing" | "complete" | "error";
  result: string | null;
}

export interface ValidationResult {
  validator: "gatekeeper" | "auditor" | "strategist";
  passed: boolean;
  confidence: number;
  reason: string;
}

export type QueryEventType =
  | "plan"
  | "retrieval"
  | "token"
  | "validation"
  | "complete"
  | "error";

export interface QueryEvent {
  type: QueryEventType;
  plan_steps: PlanStep[];
  chunks: RetrievedChunk[];
  content: string;
  validation: ValidationResult[];
  error: string | null;
}

/* ===========================
   Inspector State
   =========================== */

export interface InspectorState {
  planSteps: PlanStep[];
  retrievedChunks: RetrievedChunk[];
  validation: ValidationResult[];
  isOpen: boolean;
  activeTab: "retrieval" | "reasoning" | "validation";
}
