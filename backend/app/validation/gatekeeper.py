"""Gatekeeper validation — checks if the answer addresses the user's query."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas import ValidationResult

GATEKEEPER_PROMPT = """You are a strict quality evaluator for a RAG system.

## Task
Determine if the given ANSWER directly and sufficiently addresses the USER QUERY.

## Criteria
- The answer must be ON-TOPIC and relevant to what was asked.
- The answer must attempt to DIRECTLY ANSWER the question (not just discuss related topics).
- If the answer says "I don't have enough information," that's acceptable ONLY if genuinely uncertain.
- Partial answers that address the core question are acceptable.

## Input
USER QUERY: {query}

ANSWER: {answer}

## Output (JSON)
{{
  "passed": true/false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation of your judgment"
}}

Respond ONLY with JSON."""


async def validate_gatekeeper(query: str, answer: str) -> ValidationResult:
    """
    Gatekeeper validation — verifies the answer directly addresses the query.

    This is the first guardrail: prompt alignment check.

    Args:
        query: The user's original question.
        answer: The generated answer to validate.

    Returns:
        ValidationResult with pass/fail, confidence, and reason.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a precise evaluation judge. Always respond with valid JSON."},
                {"role": "user", "content": GATEKEEPER_PROMPT.format(query=query, answer=answer)},
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return ValidationResult(
            validator="gatekeeper",
            passed=data.get("passed", True),
            confidence=data.get("confidence", 0.5),
            reason=data.get("reason", ""),
        )

    except Exception as e:
        # On error, pass by default (don't block the response)
        return ValidationResult(
            validator="gatekeeper",
            passed=True,
            confidence=0.0,
            reason=f"Validation error: {str(e)}",
        )
