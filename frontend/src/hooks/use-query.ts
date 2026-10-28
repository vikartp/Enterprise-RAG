"use client";

import { useState, useCallback } from "react";
import { queryDocuments } from "@/lib/api";
import type {
  ChatMessage,
  QueryEvent,
  PlanStep,
  RetrievedChunk,
  ValidationResult,
  InspectorState,
} from "@/types";
import { generateId } from "@/lib/utils";

export interface UseQueryReturn {
  /** Chat message history */
  messages: ChatMessage[];
  /** Whether a response is currently streaming */
  isStreaming: boolean;
  /** Inspector panel state */
  inspector: InspectorState;
  /** Error message */
  error: string | null;
  /** Send a new query */
  sendQuery: (query: string) => void;
  /** Toggle inspector drawer */
  toggleInspector: () => void;
  /** Set active inspector tab */
  setInspectorTab: (tab: InspectorState["activeTab"]) => void;
  /** Clear chat history */
  clearChat: () => void;
}

export function useQuery(): UseQueryReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inspector, setInspector] = useState<InspectorState>({
    planSteps: [],
    retrievedChunks: [],
    validation: [],
    isOpen: false,
    activeTab: "retrieval",
  });

  const sendQuery = useCallback(
    (query: string) => {
      // Add user message
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content: query,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsStreaming(true);
      setError(null);

      // Reset inspector for new query
      setInspector((prev) => ({
        ...prev,
        planSteps: [],
        retrievedChunks: [],
        validation: [],
        isOpen: true,
      }));

      // Create assistant message placeholder
      const assistantId = generateId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Build history (exclude current messages)
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      queryDocuments(
        query,
        history,
        (event: QueryEvent) => {
          switch (event.type) {
            case "plan":
              setInspector((prev) => ({
                ...prev,
                planSteps: event.plan_steps || prev.planSteps,
              }));
              break;

            case "retrieval":
              if (event.chunks?.length > 0) {
                setInspector((prev) => ({
                  ...prev,
                  retrievedChunks: event.chunks,
                }));
              }
              break;

            case "token":
              // Append streaming token to assistant message
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + event.content }
                    : m
                )
              );
              break;

            case "validation":
              setInspector((prev) => ({
                ...prev,
                validation: event.validation || [],
              }));
              break;

            case "error":
              setError(event.error || "Unknown error");
              break;
          }
        },
        (errMsg: string) => {
          setError(errMsg);
          setIsStreaming(false);
        },
        () => {
          setIsStreaming(false);
        }
      );
    },
    [messages]
  );

  const toggleInspector = useCallback(() => {
    setInspector((prev) => ({ ...prev, isOpen: !prev.isOpen }));
  }, []);

  const setInspectorTab = useCallback(
    (tab: InspectorState["activeTab"]) => {
      setInspector((prev) => ({ ...prev, activeTab: tab }));
    },
    []
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setInspector({
      planSteps: [],
      retrievedChunks: [],
      validation: [],
      isOpen: false,
      activeTab: "retrieval",
    });
  }, []);

  return {
    messages,
    isStreaming,
    inspector,
    error,
    sendQuery,
    toggleInspector,
    setInspectorTab,
    clearChat,
  };
}
