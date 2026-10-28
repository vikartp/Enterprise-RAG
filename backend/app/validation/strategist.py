"""Strategist validation — checks safety, logic consistency, and business rules."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas import ValidationResult

STRATEGIST_PROMPT = """You are a safety and logic validator for a RAG system.

## Task
Validate that the ANSWER is logically consistent, safe, and follows best practices.

## Criteria
1. **Internal Consistency:** The answer should not contradict itself.
2. **Safety:** The answer should not recommend dangerous, unethical, or harmful actions.
3. **Logic:** The reasoning should be sound — no logical fallacies or non-sequiturs.
4. **Completeness:** Important caveats or warnings should be included where relevant.
5. **Professional Tone:** The answer should maintain appropriate professional tone.

## Input
USER QUERY: {query}

ANSWER: {answer}

## Output (JSON)
{{
  "passed": true/false,
  "confidence": 0.0-1.0,
  "reason": "Explain any consistency, safety, or logic issues found"
}}

Respond ONLY with JSON."""


async def validate_strategist(query: str, answer: str) -> ValidationResult:
    """
    Strategist validation — validates consistency, safety, and business logic.

    This is the third guardrail: safety and logic constraint check.

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
                {"role": "system", "content": "You are a safety and logic validator. Always respond with valid JSON."},
                {"role": "user", "content": STRATEGIST_PROMPT.format(query=query, answer=answer)},
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return ValidationResult(
            validator="strategist",
            passed=data.get("passed", True),
            confidence=data.get("confidence", 0.5),
            reason=data.get("reason", ""),
        )

    except Exception as e:
        return ValidationResult(
            validator="strategist",
            passed=True,
            confidence=0.0,
            reason=f"Validation error: {str(e)}",
        )
