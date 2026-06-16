from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .storage import load_profile


TASKS = [
    {
        "label": "CodeQuest Status",
        "type": "shell",
        "command": "cq status",
        "problemMatcher": [],
    },
    {
        "label": "CodeQuest List Quests",
        "type": "shell",
        "command": "cq quest list",
        "problemMatcher": [],
    },
    {
        "label": "CodeQuest Finish Current Quest",
        "type": "shell",
        "command": "cq quest finish ${input:currentQuest}",
        "problemMatcher": [],
    },
]


def install_tasks(root: Path | None = None) -> Path:
    project_root = root or Path.cwd()
    vscode_dir = project_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    tasks_path = vscode_dir / "tasks.json"

    existing: dict[str, Any] = {"version": "2.0.0", "tasks": []}
    if tasks_path.exists():
        shutil.copy2(tasks_path, tasks_path.with_suffix(".json.bak"))
        with tasks_path.open("r", encoding="utf-8") as file:
            existing = json.load(file)

    existing.setdefault("version", "2.0.0")
    existing.setdefault("tasks", [])
    labels = {task.get("label") for task in existing["tasks"]}
    for task in TASKS:
        if task["label"] not in labels:
            existing["tasks"].append(task)

    profile = load_profile(project_root)
    current = profile.get("current_quest") or ""
    existing["inputs"] = [
        item for item in existing.get("inputs", []) if item.get("id") != "currentQuest"
    ]
    existing["inputs"].append(
        {
            "id": "currentQuest",
            "type": "promptString",
            "description": "Quest ID to finish",
            "default": current,
        }
    )

    with tasks_path.open("w", encoding="utf-8") as file:
        json.dump(existing, file, indent=2)
        file.write("\n")
    return tasks_path

