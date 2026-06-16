from __future__ import annotations

from typing import Callable, Any


QUESTION_FIELDS = [
    (
        "project_name",
        "Project name",
        "What are you building?",
    ),
    (
        "project_goal",
        "Project goal",
        "What should this project let someone do when it works?",
    ),
    (
        "learner_level",
        "Skill level",
        "Current coding level [beginner/intermediate/advanced]",
    ),
    (
        "preferred_language",
        "Preferred language",
        "Language or stack you want to practice",
    ),
    (
        "time_budget",
        "Session length",
        "How long should a normal quest take?",
    ),
    (
        "learning_goal",
        "Learning goal",
        "What do you most want to learn next?",
    ),
    (
        "ai_comfort",
        "AI use",
        "How should AI be used while you learn?",
    ),
]


def ask_project_profile(
    existing: dict[str, Any] | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> dict[str, Any]:
    profile = dict(existing or {})
    output_func("CodeQuest setup")
    output_func("Answer a few questions so quests can fit your real project.")

    for key, label, prompt in QUESTION_FIELDS:
        default = str(profile.get(key) or "").strip()
        suffix = f" [{default}]" if default else ""
        answer = input_func(f"{prompt}{suffix}: ").strip()
        if answer:
            profile[key] = answer
        elif default:
            profile[key] = default

    profile.setdefault("learner_level", "beginner")
    profile.setdefault("time_budget", "30 minutes")
    profile.setdefault("ai_comfort", "hints and review")
    return profile

