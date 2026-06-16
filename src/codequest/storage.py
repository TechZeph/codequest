from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Profile, now_iso
from .scoring import calculate_rank


CODEQUEST_DIR = ".codequest"


def cq_dir(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / CODEQUEST_DIR


def read_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ValueError(f"Could not parse YAML at {path}: {exc}") from exc
    return default if data is None else data


def write_yaml(path: Path, data: Any, overwrite: bool = True) -> None:
    if path.exists() and not overwrite:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False)


def default_config() -> dict[str, Any]:
    return {
        "llm": {
            "provider": "ollama",
            "ollama_model": "llama3.1",
            "ollama_url": "http://localhost:11434",
            "quest_count": 5,
        },
        "ai_review": {
            "provider": "none",
            "openai_model": "gpt-4.1-mini",
            "ollama_model": "llama3.1",
        }
    }


def default_profile(username: str = "learner") -> dict[str, Any]:
    profile = Profile(username=username)
    profile.rank = calculate_rank(profile.level)
    return profile.to_dict()


def default_log() -> list[dict[str, Any]]:
    return [
        {
            "timestamp": now_iso(),
            "event": "init",
            "message": "CodeQuest initialized.",
        }
    ]


def default_project_profile() -> dict[str, Any]:
    return {
        "project_name": "",
        "project_goal": "",
        "learner_level": "beginner",
        "preferred_language": "",
        "time_budget": "30 minutes",
        "learning_goal": "",
        "ai_comfort": "hints and review",
        "updated_at": now_iso(),
    }


def init_storage(root: Path | None = None, force: bool = False, username: str = "learner") -> list[Path]:
    base = cq_dir(root)
    quests = base / "quests"
    base.mkdir(exist_ok=True)
    quests.mkdir(exist_ok=True)

    files = {
        base / "config.yaml": default_config(),
        base / "project.yaml": default_project_profile(),
        base / "profile.yaml": default_profile(username),
        base / "log.yaml": default_log(),
    }
    created_or_updated: list[Path] = []
    for path, data in files.items():
        existed = path.exists()
        write_yaml(path, data, overwrite=force or not existed)
        if force or not existed:
            created_or_updated.append(path)
    return created_or_updated


def require_initialized(root: Path | None = None) -> Path:
    base = cq_dir(root)
    if not base.exists():
        raise FileNotFoundError("CodeQuest is not initialized. Run `cq init` first.")
    return base


def load_profile(root: Path | None = None) -> dict[str, Any]:
    base = require_initialized(root)
    profile = read_yaml(base / "profile.yaml", default_profile())
    defaults = default_profile(profile.get("username", "learner"))
    defaults.update(profile)
    defaults["stat_xp"] = {**default_profile()["stat_xp"], **defaults.get("stat_xp", {})}
    defaults["achievements"] = list(defaults.get("achievements") or [])
    return defaults


def save_profile(profile: dict[str, Any], root: Path | None = None) -> None:
    write_yaml(require_initialized(root) / "profile.yaml", profile)


def load_config(root: Path | None = None) -> dict[str, Any]:
    base = require_initialized(root)
    config = read_yaml(base / "config.yaml", default_config())
    defaults = default_config()
    defaults.update(config)
    defaults["llm"] = {**default_config()["llm"], **(defaults.get("llm") or {})}
    defaults["ai_review"] = {**default_config()["ai_review"], **(defaults.get("ai_review") or {})}
    return defaults


def save_config(config: dict[str, Any], root: Path | None = None) -> None:
    write_yaml(require_initialized(root) / "config.yaml", config)


def load_project_profile(root: Path | None = None) -> dict[str, Any]:
    base = require_initialized(root)
    project = read_yaml(base / "project.yaml", default_project_profile())
    defaults = default_project_profile()
    defaults.update(project)
    return defaults


def save_project_profile(project: dict[str, Any], root: Path | None = None) -> None:
    current = default_project_profile()
    current.update(project)
    current["updated_at"] = now_iso()
    write_yaml(require_initialized(root) / "project.yaml", current)


def load_log(root: Path | None = None) -> list[dict[str, Any]]:
    return read_yaml(require_initialized(root) / "log.yaml", [])


def save_log(entries: list[dict[str, Any]], root: Path | None = None) -> None:
    write_yaml(require_initialized(root) / "log.yaml", entries)


def append_log(event: str, message: str, root: Path | None = None, quest_id: str | None = None) -> None:
    entries = load_log(root)
    entry = {"timestamp": now_iso(), "event": event, "message": message}
    if quest_id:
        entry["quest_id"] = quest_id
    entries.append(entry)
    save_log(entries, root)


def quest_dir(root: Path | None = None) -> Path:
    return require_initialized(root) / "quests"


def quest_path(quest_id: str, root: Path | None = None) -> Path:
    return quest_dir(root) / f"{quest_id}.yaml"


def load_quest(quest_id: str, root: Path | None = None) -> dict[str, Any]:
    path = quest_path(quest_id, root)
    if not path.exists():
        raise FileNotFoundError(f"Quest not found: {quest_id}")
    return read_yaml(path, {})


def save_quest(quest: dict[str, Any], root: Path | None = None) -> Path:
    path = quest_path(quest["id"], root)
    write_yaml(path, quest)
    return path


def load_all_quests(root: Path | None = None) -> list[dict[str, Any]]:
    quests: list[dict[str, Any]] = []
    qdir = quest_dir(root)
    for path in sorted(qdir.glob("*.yaml")):
        quest = read_yaml(path, {})
        if quest:
            quests.append(quest)
    return quests
