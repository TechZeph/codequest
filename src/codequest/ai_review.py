from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AIReviewResult:
    skipped: bool
    passed: bool | None
    message: str


def review_quest(quest: dict[str, Any], config: dict[str, Any]) -> AIReviewResult:
    ai_review = quest.get("ai_review", {}) or {}
    if not ai_review.get("enabled", False):
        return AIReviewResult(True, None, "AI review skipped: disabled for this quest.")

    provider = ai_review.get("provider") or (config.get("ai_review", {}) or {}).get("provider", "none")
    if provider in (None, "", "none"):
        return AIReviewResult(True, None, "AI review skipped: no provider configured.")

    if provider in {"openai", "ollama"}:
        return AIReviewResult(
            True,
            None,
            f"AI review skipped: provider '{provider}' is recognized but not implemented in the MVP.",
        )

    return AIReviewResult(True, None, f"AI review skipped: unknown provider '{provider}'.")

