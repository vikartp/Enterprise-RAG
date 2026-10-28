import Link from "next/link";
import { Upload, MessageSquare, Shield, Search, Brain, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
      {/* Hero */}
      <div className="text-center max-w-3xl mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 mb-6">
          <Zap className="w-3.5 h-3.5 text-primary" />
          <span className="text-xs font-medium text-primary">Production-Ready Agentic RAG</span>
        </div>

        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-6">
          Enterprise{" "}
          <span className="gradient-text">Hybrid Search</span>
          <br />
          with AI Guardrails
        </h1>

        <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Ingest documents, search with Dense + Sparse hybrid vectors,
          and query through an agentic pipeline with three-stage validation
          — Gatekeeper, Auditor, and Strategist.
        </p>
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl w-full mb-16">
        <Link
          href="/ingest"
          className="glass-card p-8 group hover:border-primary/30 transition-all duration-300 hover:glow-primary"
        >
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary/20 transition-colors">
            <Upload className="w-6 h-6 text-primary" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Ingest Documents</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Upload PDFs, Markdown, TXT, or CSV files. Watch real-time
            processing through restructuring, chunking, enrichment, and indexing.
          </p>
          <div className="mt-4 flex items-center gap-2 text-sm text-primary font-medium">
            Start Ingesting
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </div>
        </Link>

        <Link
          href="/query"
          className="glass-card p-8 group hover:border-secondary/30 transition-all duration-300 hover:shadow-[0_0_20px_rgba(139,92,246,0.15)]"
        >
          <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center mb-5 group-hover:bg-secondary/20 transition-colors">
            <MessageSquare className="w-6 h-6 text-secondary" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Query & Inspect</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Ask questions with streaming responses. Inspect retrieval scores,
            agent reasoning, and validation status in real-time.
          </p>
          <div className="mt-4 flex items-center gap-2 text-sm text-secondary font-medium">
            Start Querying
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </div>
        </Link>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl w-full">
        {[
          {
            icon: Search,
            label: "Hybrid Search",
            desc: "Dense + Sparse vectors with RRF fusion and Cross-Encoder reranking",
            color: "text-accent",
          },
          {
            icon: Brain,
            label: "Agentic Reasoning",
            desc: "LangGraph planner decomposes queries into retrieval sub-tasks",
            color: "text-primary",
          },
          {
            icon: Shield,
            label: "3-Stage Validation",
            desc: "Gatekeeper, Auditor, Strategist guardrails before every response",
            color: "text-success",
          },
        ].map((feature) => (
          <div
            key={feature.label}
            className="text-center p-5 rounded-xl border border-border/50 bg-card/30"
          >
            <feature.icon className={`w-6 h-6 ${feature.color} mx-auto mb-3`} />
            <h3 className="text-sm font-semibold mb-1">{feature.label}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">{feature.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
