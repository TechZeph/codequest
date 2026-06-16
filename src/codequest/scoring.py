from __future__ import annotations

from typing import Any

from .models import STAT_KEYS


XP_PER_LEVEL = 100

RANKS = {
    0: "Copy-Paster",
    1: "Script Goblin",
    2: "CLI Apprentice",
    3: "Debug Initiate",
    4: "Automation Tinkerer",
    5: "Repo Smith",
    6: "Local Agent Engineer",
    7: "System Builder",
}


def calculate_total_xp(skills: dict[str, int]) -> int:
    return sum(max(0, int(value)) for value in skills.values())


def calculate_level(total_xp: int) -> int:
    return max(0, int(total_xp) // XP_PER_LEVEL)


def calculate_rank(level: int) -> str:
    capped_level = min(max(0, int(level)), max(RANKS))
    return RANKS[capped_level]


def xp_until_next_level(total_xp: int) -> int:
    return XP_PER_LEVEL - (int(total_xp) % XP_PER_LEVEL)


def apply_quest_xp(profile: dict[str, Any], quest: dict[str, Any]) -> dict[str, Any]:
    skills = quest.get("skills", {}) or {}
    total_award = calculate_total_xp(skills)
    profile["total_xp"] = int(profile.get("total_xp", 0)) + total_award

    stat_xp = {key: 0 for key in STAT_KEYS}
    stat_xp.update(profile.get("stat_xp", {}) or {})
    for skill, xp in skills.items():
        if skill not in stat_xp:
            stat_xp[skill] = 0
        stat_xp[skill] += max(0, int(xp))
    profile["stat_xp"] = stat_xp

    profile["level"] = calculate_level(profile["total_xp"])
    profile["rank"] = calculate_rank(profile["level"])
    return profile


def unlock_achievements(profile: dict[str, Any], completed_quests: list[dict[str, Any]]) -> list[str]:
    unlocked = set(profile.get("achievements", []) or [])
    new_unlocks: list[str] = []

    def add(name: str) -> None:
        if name not in unlocked:
            unlocked.add(name)
            new_unlocks.append(name)

    if completed_quests:
        add("First Blood")

    if any(quest.get("mode") == "green" for quest in completed_quests):
        add("No Copy-Paste Run")

    if any((quest.get("skills") or {}).get("testing", 0) > 0 for quest in completed_quests):
        add("Test Goblin")

    repo_skill_count = 0
    for quest in completed_quests:
        skills = quest.get("skills") or {}
        if any(skills.get(skill, 0) > 0 for skill in ("files", "cli", "architecture")):
            repo_skill_count += 1
    if repo_skill_count >= 3:
        add("Repo Smith")

    if any((quest.get("skills") or {}).get("debugging", 0) > 0 for quest in completed_quests):
        add("Stack Trace Reader")

    if any(
        quest.get("mode") == "amber" and (quest.get("ai_review") or {}).get("enabled") is True
        for quest in completed_quests
    ):
        add("AI Wrangler")

    profile["achievements"] = sorted(unlocked)
    return new_unlocks

