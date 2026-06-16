from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from .ai_review import review_quest
from .llm import OllamaClient, check_ollama, LLMError
from .models import QUEST_MODES, QUEST_STATUSES, STAT_KEYS, default_quest
from .questionnaire import ask_project_profile
from .quest_generation import QuestGenerationError, generate_quests
from .repo_analyzer import analyze_repo
from .scoring import apply_quest_xp, calculate_total_xp, unlock_achievements, xp_until_next_level
from .storage import (
    append_log,
    cq_dir,
    init_storage,
    load_all_quests,
    load_config,
    load_log,
    load_profile,
    load_project_profile,
    load_quest,
    save_config,
    save_profile,
    save_project_profile,
    save_quest,
)
from .verifier import verify_quest
from .vscode import install_tasks


BOSSES = {
    "repo-init-lite": {
        "description": "Build a small project initializer that creates folders and README files safely.",
        "required_skills": ["cli", "files", "logic"],
        "unlock_suggestion": "Complete a beginner green quest that writes files from a CLI.",
        "suggested_quest_chain": ["Create a README generator", "Add --force safety", "Write file existence tests"],
    },
    "obsidian-link-scanner": {
        "description": "Scan Markdown notes and report broken wiki-style links.",
        "required_skills": ["files", "data", "testing"],
        "unlock_suggestion": "Practice reading directories, parsing text, and writing tests.",
        "suggested_quest_chain": ["Read Markdown files", "Extract links", "Report missing targets"],
    },
    "github-repo-fetcher": {
        "description": "Fetch repository metadata from GitHub and save a local report.",
        "required_skills": ["web", "data", "cli"],
        "unlock_suggestion": "Complete quests using JSON APIs and command-line arguments.",
        "suggested_quest_chain": ["Call an HTTP API", "Parse JSON", "Render a report"],
    },
}


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "quest"


def prompt_list(label: str) -> list[str]:
    print(f"{label} Enter one per line. Leave blank when done.")
    values: list[str] = []
    while True:
        value = input("> ").strip()
        if not value:
            return values
        values.append(value)


def prompt_skills() -> dict[str, int]:
    print("Skill XP rewards. Leave blank for 0.")
    skills: dict[str, int] = {}
    for skill in STAT_KEYS:
        raw = input(f"{skill}: ").strip()
        if raw:
            try:
                skills[skill] = max(0, int(raw))
            except ValueError:
                print(f"Ignoring invalid XP for {skill}: {raw}")
    return skills


def command_init(args: argparse.Namespace) -> int:
    changed = init_storage(force=args.force, username=args.username)
    if changed:
        print("CodeQuest initialized.")
        for path in changed:
            print(f"  wrote {path}")
    else:
        print("CodeQuest already initialized. Use --force to recreate default files.")
    return 0


def command_quest_new(_: argparse.Namespace) -> int:
    title = input("Quest title: ").strip()
    if not title:
        print("Quest title is required.", file=sys.stderr)
        return 2

    quest_id = input(f"Quest id [{slugify_title(title)}]: ").strip() or slugify_title(title)
    quest = default_quest(title, quest_id)
    quest["summary"] = input("Summary: ").strip()
    quest["difficulty"] = input("Difficulty [beginner]: ").strip() or "beginner"

    mode = input("Mode [green/amber/red] (green): ").strip() or "green"
    if mode not in QUEST_MODES:
        print(f"Unknown mode '{mode}', using green.")
        mode = "green"
    quest["mode"] = mode

    quest["skills"] = prompt_skills()
    quest["requirements"] = prompt_list("Requirements.")
    quest["verification"]["commands"] = prompt_list("Verification commands.")
    quest["verification"]["expected_paths"] = prompt_list("Expected files/paths.")
    quest["verification"]["changed_files"] = prompt_list("Changed files that must exist.")
    quest["verification"]["forbidden"] = prompt_list("Forbidden behaviours or constraints.")

    enable_ai = input("Enable optional AI review? [y/N]: ").strip().lower()
    quest["ai_review"]["enabled"] = enable_ai in {"y", "yes"}

    path = save_quest(quest)
    append_log("quest_created", f"Created quest {quest_id}.", quest_id=quest_id)
    print(f"Created quest {quest_id} at {path}")
    return 0


def _llm_from_config(config: dict[str, Any]) -> OllamaClient:
    llm_config = config.get("llm", {}) or {}
    provider = llm_config.get("provider", "ollama")
    if provider != "ollama":
        raise ValueError(f"Quest generation provider '{provider}' is not implemented. Use `cq config llm --provider ollama`.")
    return OllamaClient(
        model=str(llm_config.get("ollama_model") or "llama3.1"),
        base_url=str(llm_config.get("ollama_url") or "http://localhost:11434"),
    )


def _generate_and_save_quests(count: int | None = None) -> list[dict[str, Any]]:
    config = load_config()
    llm_config = config.get("llm", {}) or {}
    quest_count = count or int(llm_config.get("quest_count", 5))
    project_profile = load_project_profile()
    repo_summary = analyze_repo(Path.cwd())
    existing_quests = load_all_quests()
    llm = _llm_from_config(config)
    quests = generate_quests(llm, project_profile, repo_summary, existing_quests, quest_count=quest_count)
    for quest in quests:
        save_quest(quest)
        append_log("quest_generated", f"Generated quest {quest['id']}.", quest_id=quest["id"])
    return quests


def command_generate(args: argparse.Namespace) -> int:
    try:
        quests = _generate_and_save_quests(args.count)
    except (LLMError, QuestGenerationError, ValueError) as exc:
        print(f"Could not generate quests: {exc}", file=sys.stderr)
        print("Run `cq doctor` to check local LLM setup, or use `cq quest new` to create a quest manually.", file=sys.stderr)
        return 1

    print(f"Generated {len(quests)} quests.")
    for quest in quests:
        print(f"  {quest['id']} - {quest['title']} ({quest['difficulty']}, {quest['mode']})")
    return 0


def command_play(args: argparse.Namespace) -> int:
    if not cq_dir().exists():
        changed = init_storage(username=args.username)
        print("CodeQuest initialized.")
        for path in changed:
            print(f"  wrote {path}")

    project = load_project_profile()
    project = ask_project_profile(project)
    save_project_profile(project)

    try:
        quests = _generate_and_save_quests(args.count)
    except (LLMError, QuestGenerationError, ValueError) as exc:
        print(f"Could not generate quests: {exc}", file=sys.stderr)
        print("You can run `cq doctor` to inspect setup, or `cq quest new` to create a quest manually.", file=sys.stderr)
        return 1

    print(f"\nGenerated {len(quests)} quests.")
    for quest in quests:
        print(f"  {quest['id']} - {quest['title']}")

    first = quests[0]
    answer = input(f"\nStart first quest now? [{first['id']}] [Y/n]: ").strip().lower()
    if answer in {"", "y", "yes"}:
        first["status"] = "active"
        save_quest(first)
        profile = load_profile()
        profile["current_quest"] = first["id"]
        save_profile(profile)
        append_log("quest_started", f"Started quest {first['id']}.", quest_id=first["id"])
        print(f"Started quest {first['id']}.")
    else:
        print("Run `cq quest start <quest_id>` when you are ready.")
    return 0


def command_quest_list(_: argparse.Namespace) -> int:
    quests = load_all_quests()
    grouped = {status: [] for status in QUEST_STATUSES}
    for quest in quests:
        grouped.setdefault(quest.get("status", "not_started"), []).append(quest)

    for status in QUEST_STATUSES:
        print(f"\n{status}")
        print("-" * len(status))
        if not grouped.get(status):
            print("  none")
            continue
        for quest in grouped[status]:
            print(f"  {quest.get('id')} - {quest.get('title')} ({quest.get('difficulty')}, {quest.get('mode')})")
    return 0


def command_quest_show(args: argparse.Namespace) -> int:
    quest = load_quest(args.quest_id)
    print(f"{quest.get('id')}: {quest.get('title')}")
    print(f"Status: {quest.get('status')}")
    print(f"Difficulty: {quest.get('difficulty')}")
    print(f"Mode: {quest.get('mode')}")
    print(f"XP: {calculate_total_xp(quest.get('skills', {}) or {})}")
    print(f"\n{quest.get('summary', '')}")
    print("\nRequirements:")
    for requirement in quest.get("requirements", []) or []:
        print(f"  - {requirement}")
    return 0


def command_quest_start(args: argparse.Namespace) -> int:
    quest = load_quest(args.quest_id)
    quest["status"] = "active"
    save_quest(quest)

    profile = load_profile()
    profile["current_quest"] = args.quest_id
    save_profile(profile)
    append_log("quest_started", f"Started quest {args.quest_id}.", quest_id=args.quest_id)
    print(f"Started quest {args.quest_id}.")
    return 0


def command_quest_finish(args: argparse.Namespace) -> int:
    quest = load_quest(args.quest_id)
    result = verify_quest(quest, Path.cwd())
    for check in result.checks:
        marker = "PASS" if check.passed else "FAIL"
        print(f"[{marker}] {check.message}")
        if not check.passed and check.stderr:
            print(check.stderr.strip())

    if not result.passed:
        quest["status"] = "active"
        save_quest(quest)
        append_log("quest_verification_failed", f"Verification failed for {args.quest_id}.", quest_id=args.quest_id)
        print("Quest remains active. Fix the failures and run finish again.")
        return 1

    ai_result = review_quest(quest, load_config())
    print(ai_result.message)

    quest["status"] = "completed"
    save_quest(quest)

    profile = load_profile()
    profile = apply_quest_xp(profile, quest)
    if profile.get("current_quest") == args.quest_id:
        profile["current_quest"] = None

    completed_quests = [item for item in load_all_quests() if item.get("status") == "completed"]
    new_unlocks = unlock_achievements(profile, completed_quests)
    save_profile(profile)

    awarded = calculate_total_xp(quest.get("skills", {}) or {})
    append_log("quest_completed", f"Completed quest {args.quest_id} and earned {awarded} XP.", quest_id=args.quest_id)
    print(f"Completed quest {args.quest_id}. Awarded {awarded} XP.")
    if new_unlocks:
        print("New achievements:")
        for achievement in new_unlocks:
            print(f"  - {achievement}")
    return 0


def command_status(_: argparse.Namespace) -> int:
    profile = load_profile()
    print(f"Rank: {profile['rank']}")
    print(f"Level: {profile['level']}")
    print(f"Total XP: {profile['total_xp']}")
    print(f"XP until next level: {xp_until_next_level(profile['total_xp'])}")
    print(f"Current quest: {profile.get('current_quest') or 'none'}")
    print("\nStat XP:")
    for skill, xp in profile.get("stat_xp", {}).items():
        print(f"  {skill}: {xp}")
    print("\nRecent log:")
    for entry in load_log()[-5:]:
        print(f"  {entry.get('timestamp')} - {entry.get('message')}")
    return 0


def command_achievements(_: argparse.Namespace) -> int:
    achievements = load_profile().get("achievements", []) or []
    if not achievements:
        print("No achievements unlocked yet.")
        return 0
    for achievement in achievements:
        print(f"- {achievement}")
    return 0


def command_boss_list(_: argparse.Namespace) -> int:
    for boss_id, boss in BOSSES.items():
        print(f"\n{boss_id}")
        print(f"  {boss['description']}")
        print(f"  Required skills: {', '.join(boss['required_skills'])}")
        print(f"  Unlock: {boss['unlock_suggestion']}")
        print(f"  Quest chain: {' -> '.join(boss['suggested_quest_chain'])}")
    return 0


def command_vscode_install(_: argparse.Namespace) -> int:
    path = install_tasks()
    print(f"Installed VS Code tasks at {path}")
    return 0


def command_config_llm(args: argparse.Namespace) -> int:
    config = load_config()
    config.setdefault("llm", {})
    if args.provider:
        config["llm"]["provider"] = args.provider
    if args.model:
        config["llm"]["ollama_model"] = args.model
    if args.url:
        config["llm"]["ollama_url"] = args.url
    if args.count is not None:
        config["llm"]["quest_count"] = args.count
    save_config(config)
    llm_config = config["llm"]
    print("LLM configuration updated.")
    print(f"  provider: {llm_config.get('provider')}")
    print(f"  ollama_model: {llm_config.get('ollama_model')}")
    print(f"  ollama_url: {llm_config.get('ollama_url')}")
    print(f"  quest_count: {llm_config.get('quest_count')}")
    return 0


def command_doctor(_: argparse.Namespace) -> int:
    print(f"Python: {sys.version.split()[0]}")
    initialized = cq_dir().exists()
    print(f"CodeQuest project: {'initialized' if initialized else 'not initialized'}")

    config = load_config() if initialized else {"llm": {"provider": "ollama", "ollama_url": "http://localhost:11434"}}
    llm_config = config.get("llm", {}) or {}
    provider = llm_config.get("provider", "ollama")
    print(f"Quest generation provider: {provider}")
    if provider == "ollama":
        ok, message = check_ollama(str(llm_config.get("ollama_url") or "http://localhost:11434"))
        print(f"Ollama: {'ok' if ok else 'not ready'} - {message}")
    else:
        print("Ollama: skipped")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cq", description="CodeQuest manual coding practice CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    play = subparsers.add_parser("play", help="Run guided setup and generate project quests.")
    play.add_argument("--username", default="learner")
    play.add_argument("--count", type=int, default=None, help="Number of quests to generate.")
    play.set_defaults(func=command_play)

    generate = subparsers.add_parser("generate", help="Generate quests from the saved project profile.")
    generate.add_argument("--count", type=int, default=None, help="Number of quests to generate.")
    generate.set_defaults(func=command_generate)

    init = subparsers.add_parser("init")
    init.add_argument("--force", action="store_true", help="Overwrite default CodeQuest files.")
    init.add_argument("--username", default="learner")
    init.set_defaults(func=command_init)

    quest = subparsers.add_parser("quest")
    quest_sub = quest.add_subparsers(dest="quest_command", required=True)
    quest_sub.add_parser("new").set_defaults(func=command_quest_new)
    quest_sub.add_parser("list").set_defaults(func=command_quest_list)

    show = quest_sub.add_parser("show")
    show.add_argument("quest_id")
    show.set_defaults(func=command_quest_show)

    start = quest_sub.add_parser("start")
    start.add_argument("quest_id")
    start.set_defaults(func=command_quest_start)

    finish = quest_sub.add_parser("finish")
    finish.add_argument("quest_id")
    finish.set_defaults(func=command_quest_finish)

    subparsers.add_parser("status").set_defaults(func=command_status)
    subparsers.add_parser("achievements").set_defaults(func=command_achievements)

    boss = subparsers.add_parser("boss")
    boss_sub = boss.add_subparsers(dest="boss_command", required=True)
    boss_sub.add_parser("list").set_defaults(func=command_boss_list)

    vscode = subparsers.add_parser("vscode")
    vscode_sub = vscode.add_subparsers(dest="vscode_command", required=True)
    vscode_sub.add_parser("install").set_defaults(func=command_vscode_install)

    config = subparsers.add_parser("config")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    llm = config_sub.add_parser("llm")
    llm.add_argument("--provider", choices=["ollama", "none"])
    llm.add_argument("--model")
    llm.add_argument("--url")
    llm.add_argument("--count", type=int)
    llm.set_defaults(func=command_config_llm)

    subparsers.add_parser("doctor").set_defaults(func=command_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
