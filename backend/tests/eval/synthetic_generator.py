"""Synthetic dataset generation using RAGAS for RAG evaluation."""

from __future__ import annotations

import json
import os
from pathlib import Path


def generate_synthetic_dataset(
    documents_dir: str,
    output_path: str = "synthetic_testset.json",
    test_size: int = 20,
) -> dict:
    """
    Generate a synthetic QA evaluation dataset from ingested documents.

    Uses RAGAS TestsetGenerator to create diverse question-answer pairs
    with varying difficulty levels for comprehensive pipeline evaluation.

    Args:
        documents_dir: Path to directory containing source documents.
        output_path: Where to save the generated dataset.
        test_size: Number of QA pairs to generate.

    Returns:
        Dictionary containing the generated test set.
    """
    try:
        from ragas.testset import TestsetGenerator
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langchain_community.document_loaders import DirectoryLoader, TextLoader
    except ImportError:
        print("Install evaluation dependencies: pip install 'enterprise-rag-backend[eval]'")
        return {}

    # Load documents
    loader = DirectoryLoader(
        documents_dir,
        glob="**/*.{md,txt}",
        loader_cls=TextLoader,
    )
    documents = loader.load()

    if not documents:
        print(f"No documents found in {documents_dir}")
        return {}

    # Initialize generator
    generator_llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    generator = TestsetGenerator.from_langchain(
        generator_llm=generator_llm,
        embeddings=embeddings,
    )

    # Generate test set
    testset = generator.generate_with_langchain_docs(
        documents=documents,
        test_size=test_size,
    )

    # Convert to serializable format
    dataset = testset.to_pandas().to_dict(orient="records")

    # Save
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2, default=str)

    print(f"✓ Generated {len(dataset)} synthetic QA pairs → {output_path}")
    return {"test_size": len(dataset), "output_path": output_path}


if __name__ == "__main__":
    import sys

    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "./test_documents"
    generate_synthetic_dataset(docs_dir)
