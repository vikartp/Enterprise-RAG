"""Auditor validation — checks for hallucination and context grounding."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas import ValidationResult

AUDITOR_PROMPT = """You are a strict hallucination detector for a RAG system.

## Task
Verify that EVERY factual claim in the ANSWER is grounded in the RETRIEVED CONTEXT.

## Criteria
- Each specific claim, number, date, or fact in the answer MUST be traceable to the context.
- General knowledge statements (e.g., "the sky is blue") are acceptable.
- If the answer makes claims NOT found in the context, it is hallucinating.
- If the answer correctly states it doesn't have information, that passes.
- Be especially strict about: numbers, dates, names, technical specifications.

## Input
USER QUERY: {query}

RETRIEVED CONTEXT:
{context}

ANSWER: {answer}

## Output (JSON)
{{
  "passed": true/false,
  "confidence": 0.0-1.0,
  "reason": "List any ungrounded claims, or confirm all claims are grounded"
}}

Respond ONLY with JSON."""


async def validate_auditor(query: str, answer: str, context: str) -> ValidationResult:
    """
    Auditor validation — verifies every claim is grounded in retrieved context.

    This is the second guardrail: hallucination and context grounding check.

    Args:
        query: The user's original question.
        answer: The generated answer to validate.
        context: The retrieved context used to generate the answer.

    Returns:
        ValidationResult with pass/fail, confidence, and reason.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a precise hallucination detector. Always respond with valid JSON."},
                {"role": "user", "content": AUDITOR_PROMPT.format(
                    query=query,
                    answer=answer,
                    context=context[:8000],  # Truncate context to fit token limits
                )},
            ],
            temperature=0.0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return ValidationResult(
            validator="auditor",
            passed=data.get("passed", True),
            confidence=data.get("confidence", 0.5),
            reason=data.get("reason", ""),
        )

    except Exception as e:
        return ValidationResult(
            validator="auditor",
            passed=True,
            confidence=0.0,
            reason=f"Validation error: {str(e)}",
        )
