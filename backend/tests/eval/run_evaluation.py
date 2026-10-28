"""RAGAS evaluation runner — measures RAG pipeline quality metrics."""

from __future__ import annotations

import json
from pathlib import Path


def run_evaluation(
    testset_path: str = "synthetic_testset.json",
    output_path: str = "evaluation_results.json",
) -> dict:
    """
    Run RAGAS evaluation metrics on a synthetic test set.

    Metrics evaluated:
    - Faithfulness: Is the answer grounded in the context?
    - Answer Relevancy: Does the answer address the question?
    - Context Precision: Are the retrieved contexts relevant?
    - Context Recall: Is all necessary information retrieved?

    Args:
        testset_path: Path to the synthetic test set JSON.
        output_path: Where to save evaluation results.

    Returns:
        Dictionary with metric scores.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        from datasets import Dataset
    except ImportError:
        print("Install evaluation dependencies: pip install 'enterprise-rag-backend[eval]'")
        return {}

    # Load test set
    with open(testset_path) as f:
        testset = json.load(f)

    if not testset:
        print("Empty test set")
        return {}

    # Convert to HuggingFace Dataset format
    dataset = Dataset.from_list(testset)

    # Run evaluation
    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
    )

    # Format results
    scores = {
        "faithfulness": float(results["faithfulness"]),
        "answer_relevancy": float(results["answer_relevancy"]),
        "context_precision": float(results["context_precision"]),
        "context_recall": float(results["context_recall"]),
    }

    # Save results
    report = {
        "metrics": scores,
        "testset_path": testset_path,
        "test_size": len(testset),
        "summary": _generate_summary(scores),
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 RAGAS Evaluation Results")
    print("=" * 50)
    for metric, score in scores.items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"  {metric:25s} {bar} {score:.4f}")
    print("=" * 50)
    print(f"\n✓ Results saved → {output_path}")

    return report


def _generate_summary(scores: dict[str, float]) -> str:
    """Generate a human-readable summary of evaluation results."""
    lines = []

    if scores.get("faithfulness", 0) < 0.8:
        lines.append("⚠️ Faithfulness is below 0.8 — potential hallucination issues.")
    if scores.get("answer_relevancy", 0) < 0.8:
        lines.append("⚠️ Answer relevancy is low — answers may not address queries well.")
    if scores.get("context_precision", 0) < 0.7:
        lines.append("⚠️ Context precision is low — retriever returning irrelevant chunks.")
    if scores.get("context_recall", 0) < 0.7:
        lines.append("⚠️ Context recall is low — relevant information not being retrieved.")

    if not lines:
        lines.append("✅ All metrics are within acceptable ranges.")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    testset = sys.argv[1] if len(sys.argv) > 1 else "synthetic_testset.json"
    run_evaluation(testset)
