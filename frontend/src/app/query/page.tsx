"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  PanelRightOpen,
  PanelRightClose,
  Bot,
  User,
  Loader2,
  Trash2,
  Search,
  Brain,
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  Eye,
  Scale,
  ChevronDown,
  FileText,
  Sparkles,
} from "lucide-react";
import { cn, truncate } from "@/lib/utils";
import { useQuery } from "@/hooks/use-query";
import type {
  ChatMessage,
  InspectorState,
  PlanStep,
  RetrievedChunk,
  ValidationResult,
} from "@/types";

export default function QueryPage() {
  const {
    messages,
    isStreaming,
    inspector,
    error,
    sendQuery,
    toggleInspector,
    setInspectorTab,
    clearChat,
  } = useQuery();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    sendQuery(trimmed);
    setInput("");
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-border glass-card rounded-none">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold">Agentic Query</h1>
              <p className="text-xs text-muted-foreground">
                Hybrid Search · LangGraph · 3-Stage Validation
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearChat}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-card-hover transition-colors"
              title="Clear chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={toggleInspector}
              className={cn(
                "p-2 rounded-lg transition-colors",
                inspector.isOpen
                  ? "text-primary bg-primary/10"
                  : "text-muted-foreground hover:text-foreground hover:bg-card-hover"
              )}
              title="Toggle inspector"
            >
              {inspector.isOpen ? (
                <PanelRightClose className="w-4 h-4" />
              ) : (
                <PanelRightOpen className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-primary/60" />
              </div>
              <h2 className="text-xl font-semibold mb-2">Ask anything</h2>
              <p className="text-sm text-muted-foreground max-w-md">
                Query your indexed documents with hybrid retrieval.
                Open the inspector panel to see retrieval scores,
                reasoning steps, and validation results.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} isStreaming={isStreaming} />
          ))}

          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="px-6 py-4 border-t border-border"
        >
          <div className="flex items-center gap-3 glass-card px-4 py-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1 bg-transparent outline-none text-sm placeholder:text-muted-foreground"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className={cn(
                "p-2 rounded-lg transition-all duration-200",
                input.trim() && !isStreaming
                  ? "bg-primary text-white hover:bg-primary-hover"
                  : "text-muted-foreground cursor-not-allowed"
              )}
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Inspector Drawer */}
      <AnimatePresence>
        {inspector.isOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 420, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-l border-border bg-card/50 overflow-hidden flex-shrink-0"
          >
            <InspectorPanel
              inspector={inspector}
              setActiveTab={setInspectorTab}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ===== Message Bubble ===== */
function MessageBubble({
  message,
  isStreaming,
}: {
  message: ChatMessage;
  isStreaming: boolean;
}) {
  const isUser = message.role === "user";
  const isLastAssistant =
    !isUser && isStreaming && message.content.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-3", isUser && "flex-row-reverse")}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
          isUser
            ? "bg-primary/10 text-primary"
            : "bg-secondary/10 text-secondary"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message */}
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary/10 border border-primary/20"
            : "glass-card"
        )}
      >
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
          {isLastAssistant && (
            <span className="inline-flex gap-0.5 ml-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary typing-dot" />
              <span className="w-1.5 h-1.5 rounded-full bg-primary typing-dot" />
              <span className="w-1.5 h-1.5 rounded-full bg-primary typing-dot" />
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

/* ===== Inspector Panel ===== */
function InspectorPanel({
  inspector,
  setActiveTab,
}: {
  inspector: InspectorState;
  setActiveTab: (tab: InspectorState["activeTab"]) => void;
}) {
  const tabs = [
    { id: "retrieval" as const, label: "Retrieval", icon: Search, count: inspector.retrievedChunks.length },
    { id: "reasoning" as const, label: "Reasoning", icon: Brain, count: inspector.planSteps.length },
    { id: "validation" as const, label: "Validation", icon: Shield, count: inspector.validation.length },
  ];

  return (
    <div className="flex flex-col h-full w-[420px]">
      {/* Tab bar */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = inspector.activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition-colors border-b-2",
                isActive
                  ? "text-primary border-primary"
                  : "text-muted-foreground border-transparent hover:text-foreground"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              {tab.count > 0 && (
                <span className="text-[10px] bg-primary/10 text-primary px-1.5 rounded-full">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-4">
        {inspector.activeTab === "retrieval" && (
          <RetrievalTab chunks={inspector.retrievedChunks} />
        )}
        {inspector.activeTab === "reasoning" && (
          <ReasoningTab steps={inspector.planSteps} />
        )}
        {inspector.activeTab === "validation" && (
          <ValidationTab results={inspector.validation} />
        )}
      </div>
    </div>
  );
}

/* ===== Retrieval Tab ===== */
function RetrievalTab({ chunks }: { chunks: RetrievedChunk[] }) {
  if (chunks.length === 0) {
    return (
      <EmptyState
        icon={Search}
        message="No retrieval results yet. Send a query to see retrieved chunks."
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground mb-3">
        Retrieved chunks with hybrid search scores
      </p>
      {chunks.map((chunk, i) => (
        <div key={chunk.chunk_id || i} className="glass-card p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-medium">{chunk.source_file}</span>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground">
              #{i + 1}
            </span>
          </div>

          <p className="text-xs text-foreground/80 line-clamp-3">
            {chunk.content}
          </p>

          {/* Scores */}
          <div className="grid grid-cols-2 gap-2">
            <ScoreBar label="Dense" score={chunk.dense_score} color="text-primary" />
            <ScoreBar label="Sparse" score={chunk.sparse_score} color="text-accent" />
            <ScoreBar label="RRF" score={chunk.rrf_score} color="text-secondary" />
            <ScoreBar label="Reranker" score={chunk.reranker_score} color="text-success" />
          </div>
        </div>
      ))}
    </div>
  );
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  const pct = Math.min(Math.max(score * 100, 0), 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-muted-foreground">{label}</span>
        <span className={cn("text-[10px] font-mono", color)}>
          {score.toFixed(3)}
        </span>
      </div>
      <div className="h-1 rounded-full bg-border overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500")}
          style={{
            width: `${pct}%`,
            background:
              pct > 70
                ? "var(--success)"
                : pct > 40
                ? "var(--warning)"
                : "var(--destructive)",
          }}
        />
      </div>
    </div>
  );
}

/* ===== Reasoning Tab ===== */
function ReasoningTab({ steps }: { steps: PlanStep[] }) {
  if (steps.length === 0) {
    return (
      <EmptyState
        icon={Brain}
        message="No reasoning plan yet. The agent's thought process will appear here."
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground mb-3">
        Agent&apos;s reasoning plan and tool execution
      </p>
      {steps.map((step) => {
        const statusIcons = {
          pending: <ChevronDown className="w-3.5 h-3.5 text-muted" />,
          executing: <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" />,
          complete: <ShieldCheck className="w-3.5 h-3.5 text-success" />,
          error: <ShieldAlert className="w-3.5 h-3.5 text-destructive" />,
        };

        return (
          <div key={step.step_index} className="glass-card p-3">
            <div className="flex items-start gap-2">
              <div className="mt-0.5">{statusIcons[step.status]}</div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium">{step.description}</p>
                {step.tool && (
                  <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded text-[10px] bg-primary/10 text-primary">
                    🔧 {step.tool}
                  </span>
                )}
                {step.result && (
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {truncate(step.result, 150)}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ===== Validation Tab ===== */
function ValidationTab({ results }: { results: ValidationResult[] }) {
  if (results.length === 0) {
    return (
      <EmptyState
        icon={Shield}
        message="No validation results yet. Three guardrails will be checked after the response is generated."
      />
    );
  }

  const validatorConfig = {
    gatekeeper: {
      icon: "🛡️",
      label: "Gatekeeper",
      desc: "Prompt alignment check",
      color: "primary",
    },
    auditor: {
      icon: "🔍",
      label: "Auditor",
      desc: "Hallucination & grounding",
      color: "accent",
    },
    strategist: {
      icon: "⚖️",
      label: "Strategist",
      desc: "Safety & logic check",
      color: "secondary",
    },
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground mb-3">
        Three-stage validation guardrails
      </p>
      {results.map((result) => {
        const config = validatorConfig[result.validator];
        return (
          <div key={result.validator} className="glass-card p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{config.icon}</span>
                <div>
                  <h4 className="text-sm font-semibold">{config.label}</h4>
                  <p className="text-[10px] text-muted-foreground">{config.desc}</p>
                </div>
              </div>
              <span
                className={cn(
                  "px-2.5 py-1 rounded-full text-xs font-medium",
                  result.passed
                    ? "bg-success/10 text-success border border-success/20"
                    : "bg-destructive/10 text-destructive border border-destructive/20"
                )}
              >
                {result.passed ? "PASS" : "FAIL"}
              </span>
            </div>

            {/* Confidence bar */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-[10px] mb-1">
                <span className="text-muted-foreground">Confidence</span>
                <span className="font-mono">
                  {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-border overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${result.confidence * 100}%` }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className={cn(
                    "h-full rounded-full",
                    result.passed ? "bg-success" : "bg-destructive"
                  )}
                />
              </div>
            </div>

            {/* Reason */}
            {result.reason && (
              <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                {result.reason}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ===== Empty State ===== */
function EmptyState({
  icon: Icon,
  message,
}: {
  icon: React.ComponentType<{ className?: string }>;
  message: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-center">
      <Icon className="w-8 h-8 text-muted/30 mb-3" />
      <p className="text-xs text-muted-foreground max-w-[200px]">{message}</p>
    </div>
  );
}
