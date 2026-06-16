from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


STAT_KEYS = [
    "cli",
    "files",
    "logic",
    "data",
    "web",
    "testing",
    "git",
    "architecture",
    "debugging",
    "ai_wranging",
]

QUEST_STATUSES = ["not_started", "active", "completed", "failed"]
QUEST_MODES = ["green", "amber", "red"]


@dataclass
class Profile:
    username: str = "learner"
    total_xp: int = 0
    level: int = 0
    rank: str = "Copy-Paster"
    stat_xp: dict[str, int] = field(default_factory=lambda: {key: 0 for key in STAT_KEYS})
    achievements: list[str] = field(default_factory=list)
    current_quest: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "total_xp": self.total_xp,
            "level": self.level,
            "rank": self.rank,
            "stat_xp": self.stat_xp,
            "achievements": self.achievements,
            "current_quest": self.current_quest,
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_quest(title: str, quest_id: str) -> dict[str, Any]:
    return {
        "id": quest_id,
        "title": title,
        "status": "not_started",
        "difficulty": "beginner",
        "mode": "green",
        "summary": "",
        "skills": {},
        "requirements": [],
        "verification": {
            "changed_files": [],
            "commands": [],
            "expected_paths": [],
            "forbidden": [],
        },
        "ai_review": {
            "enabled": False,
            "provider": "none",
            "prompt": "Check whether the implementation satisfies the quest requirements. Give pass/fail and explain why.",
        },
        "notes": "",
    }

