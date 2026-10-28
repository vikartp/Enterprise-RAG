"""Tests for validation nodes — schema and structure validation."""

from __future__ import annotations

import pytest

from app.schemas import ValidationResult


class TestValidationSchemas:
    """Tests for validation result schemas."""

    def test_validation_result_gatekeeper(self):
        """Gatekeeper result should have correct structure."""
        result = ValidationResult(
            validator="gatekeeper",
            passed=True,
            confidence=0.95,
            reason="Answer directly addresses the query.",
        )
        assert result.validator == "gatekeeper"
        assert result.passed is True
        assert result.confidence == 0.95

    def test_validation_result_auditor(self):
        """Auditor result should detect hallucination status."""
        result = ValidationResult(
            validator="auditor",
            passed=False,
            confidence=0.80,
            reason="Claim about 'release date' not found in context.",
        )
        assert result.passed is False
        assert "release date" in result.reason

    def test_validation_result_strategist(self):
        """Strategist result should cover safety checks."""
        result = ValidationResult(
            validator="strategist",
            passed=True,
            confidence=0.90,
            reason="No safety or consistency issues detected.",
        )
        assert result.validator == "strategist"
        assert result.passed is True

    def test_confidence_bounds(self):
        """Confidence should be between 0 and 1."""
        result = ValidationResult(
            validator="gatekeeper",
            passed=True,
            confidence=0.5,
            reason="",
        )
        assert 0.0 <= result.confidence <= 1.0


class TestValidationIntegration:
    """Integration tests for validation nodes (require OpenAI API key)."""

    @pytest.mark.skip(reason="Requires OpenAI API key")
    @pytest.mark.asyncio
    async def test_gatekeeper_passes_relevant_answer(self):
        """Gatekeeper should pass when answer is relevant."""
        from app.validation.gatekeeper import validate_gatekeeper

        result = await validate_gatekeeper(
            query="What is Python?",
            answer="Python is a high-level programming language known for its readability.",
        )
        assert result.passed is True

    @pytest.mark.skip(reason="Requires OpenAI API key")
    @pytest.mark.asyncio
    async def test_auditor_detects_hallucination(self):
        """Auditor should detect claims not in context."""
        from app.validation.auditor import validate_auditor

        result = await validate_auditor(
            query="What is the company's revenue?",
            answer="The company reported $50 billion in revenue last year.",
            context="The company was founded in 2020 and has 100 employees.",
        )
        assert result.passed is False

    @pytest.mark.skip(reason="Requires OpenAI API key")
    @pytest.mark.asyncio
    async def test_strategist_catches_unsafe_content(self):
        """Strategist should flag unsafe recommendations."""
        from app.validation.strategist import validate_strategist

        result = await validate_strategist(
            query="How to fix a server issue?",
            answer="Just delete the entire database, it's the fastest solution.",
        )
        assert result.passed is False
