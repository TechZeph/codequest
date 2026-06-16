from __future__ import annotations

import json
import re
from typing import Any

from .llm import LLMError, QuestLLM
from .models import QUEST_MODES, STAT_KEYS, default_quest
from .repo_analyzer import format_repo_summary


class QuestGenerationError(RuntimeError):
    pass


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "quest"


def build_generation_prompt(
    project_profile: dict[str, Any],
    repo_summary: dict[str, Any],
    existing_quests: list[dict[str, Any]],
    quest_count: int = 5,
) -> str:
    completed = [
        f"{quest.get('id')}: {quest.get('title')}"
        for quest in existing_quests
        if quest.get("status") == "completed"
    ]
    active = [
        f"{quest.get('id')}: {quest.get('title')}"
        for quest in existing_quests
        if quest.get("status") == "active"
    ]
    return f"""
You are CodeQuest, a local learning game that turns real software projects into coding quests.

Create {quest_count} quests for an AI-assisted beginner. The quests must directly apply to the project they are building and scale in difficulty.

Project profile:
{json.dumps(project_profile, indent=2)}

Repository summary:
{format_repo_summary(repo_summary)}

Active quests:
{json.dumps(active, indent=2)}

Completed quests:
{json.dumps(completed, indent=2)}

Return only JSON with this shape:
{{
  "quests": [
    {{
      "title": "short title",
      "summary": "what the learner will build or change",
      "difficulty": "beginner|intermediate|advanced",
      "mode": "green|amber|red",
      "skills": {{"cli": 10, "files": 10}},
      "requirements": ["concrete requirement"],
      "verification": {{
        "changed_files": ["relative/path.py"],
        "commands": ["pytest"],
        "expected_paths": ["relative/path.py"],
        "forbidden": ["do not ask AI to write the full solution"]
      }},
      "notes": "short hint that points the learner without solving the quest"
    }}
  ]
}}

Rules:
- Prefer green and amber quests. Use red only for broad refactoring or integration work.
- Every quest must have at least one deterministic verification command or expected path.
- Verification commands must be safe local commands, such as pytest, npm test, or python scripts already implied by the repo.
- Do not invent external services, paid APIs, or new frameworks unless the project profile explicitly asks for them.
- Requirements should be specific enough that a learner knows what to change.
- Make each quest harder than the previous one.
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise QuestGenerationError("Generated response did not contain a JSON object.")
    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise QuestGenerationError(f"Generated response was not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise QuestGenerationError("Generated response must be a JSON object.")
    return parsed


def _clean_skills(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    skills: dict[str, int] = {}
    for key, value in raw.items():
        if key not in STAT_KEYS:
            continue
        try:
            xp = int(value)
        except (TypeError, ValueError):
            continue
        if xp > 0:
            skills[key] = min(xp, 50)
    return skills


def _clean_string_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _normalize_quest(raw: dict[str, Any], index: int, used_ids: set[str]) -> dict[str, Any]:
    title = str(raw.get("title") or f"Quest {index + 1}").strip()
    base_id = slugify(str(raw.get("id") or title))
    quest_id = base_id
    suffix = 2
    while quest_id in used_ids:
        quest_id = f"{base_id}-{suffix}"
        suffix += 1
    used_ids.add(quest_id)

    quest = default_quest(title, quest_id)
    quest["summary"] = str(raw.get("summary") or "").strip()
    quest["difficulty"] = str(raw.get("difficulty") or "beginner").strip().lower()
    mode = str(raw.get("mode") or "green").strip().lower()
    quest["mode"] = mode if mode in QUEST_MODES else "green"
    quest["skills"] = _clean_skills(raw.get("skills"))
    quest["requirements"] = _clean_string_list(raw.get("requirements"))
    quest["notes"] = str(raw.get("notes") or "").strip()

    verification = raw.get("verification") if isinstance(raw.get("verification"), dict) else {}
    quest["verification"] = {
        "changed_files": _clean_string_list(verification.get("changed_files")),
        "commands": _clean_string_list(verification.get("commands")),
        "expected_paths": _clean_string_list(verification.get("expected_paths")),
        "forbidden": _clean_string_list(verification.get("forbidden")),
    }
    if not quest["verification"]["commands"] and not quest["verification"]["expected_paths"]:
        raise QuestGenerationError(f"Generated quest '{title}' has no deterministic verification.")
    if not quest["requirements"]:
        raise QuestGenerationError(f"Generated quest '{title}' has no requirements.")
    if not quest["skills"]:
        quest["skills"] = {"logic": 10}
    return quest


def parse_generated_quests(text: str, existing_quests: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    parsed = _extract_json(text)
    quests = parsed.get("quests")
    if not isinstance(quests, list) or not quests:
        raise QuestGenerationError("Generated JSON must include a non-empty quests list.")

    used_ids = {str(quest.get("id")) for quest in existing_quests or [] if quest.get("id")}
    normalized = []
    for index, raw in enumerate(quests):
        if not isinstance(raw, dict):
            raise QuestGenerationError("Each generated quest must be an object.")
        normalized.append(_normalize_quest(raw, index, used_ids))
    return normalized


def generate_quests(
    llm: QuestLLM,
    project_profile: dict[str, Any],
    repo_summary: dict[str, Any],
    existing_quests: list[dict[str, Any]],
    quest_count: int = 5,
) -> list[dict[str, Any]]:
    prompt = build_generation_prompt(project_profile, repo_summary, existing_quests, quest_count)
    try:
        text = llm.generate(prompt)
    except LLMError:
        raise
    except Exception as exc:
        raise QuestGenerationError(f"Quest generation failed: {exc}") from exc
    return parse_generated_quests(text, existing_quests)

