"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Upload,
  MessageSquare,
  Sparkles,
  Database,
} from "lucide-react";

const NAV_ITEMS = [
  {
    href: "/ingest",
    label: "Ingest",
    icon: Upload,
    description: "Upload & process documents",
  },
  {
    href: "/query",
    label: "Query",
    icon: MessageSquare,
    description: "Chat & inspect",
  },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 border-b border-border glass-card rounded-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg group-hover:shadow-primary/25 transition-shadow">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight leading-none">
                Enterprise
                <span className="gradient-text ml-1">RAG</span>
              </span>
              <span className="text-[10px] text-muted-foreground tracking-wider uppercase">
                Agentic Hybrid Search
              </span>
            </div>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-primary/10 text-primary glow-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-card-hover"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Status badge */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-success/10 border border-success/20">
              <div className="w-1.5 h-1.5 rounded-full bg-success pulse-dot" />
              <span className="text-xs text-success font-medium">Qdrant Connected</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
