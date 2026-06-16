# CodeQuest Agent Guide

## Project Context

CodeQuest is a local-first game for learning to code through real project work. It turns a learner's current repository into quests, XP, levels, achievements, and boss fights.

The intended product direction is:
- Non-technical users should be able to start with one simple command.
- The core launch path is the CLI command `cq play`.
- A questionnaire identifies what the learner is building and what they want to learn.
- Repository analysis and local LLM generation create quests that apply directly to the user's project.
- Quest difficulty should scale over time.
- Deterministic verification remains the source of truth for awarding XP.
- IDE integrations should build on top of the CLI rather than duplicating core logic.

## Current Architecture

The repo is a Python 3.11 package installed as the `cq` CLI.

Important modules:
- `src/codequest/cli.py`: argparse command surface and command orchestration.
- `src/codequest/storage.py`: `.codequest/` YAML storage, config, profile, project profile, logs, and quests.
- `src/codequest/models.py`: shared quest/profile defaults and constants.
- `src/codequest/verifier.py`: deterministic quest verification.
- `src/codequest/scoring.py`: XP, levels, ranks, achievements.
- `src/codequest/questionnaire.py`: guided project questionnaire used by `cq play`.
- `src/codequest/repo_analyzer.py`: local repository summarization for generation context.
- `src/codequest/llm.py`: local Ollama client and health checks.
- `src/codequest/quest_generation.py`: LLM prompt construction, JSON parsing, quest normalization, and validation.
- `src/codequest/vscode.py`: task-based VS Code integration, not a full extension.
- `src/codequest/ai_review.py`: optional AI review stub; quest generation uses `llm.py`.

Local project state is stored under `.codequest/` and is intentionally ignored by Git.

## CLI Workflow

Primary non-technical path:

```bash
cq play
```

Manual and advanced commands:

```bash
cq init
cq generate
cq quest new
cq quest list
cq quest show <quest_id>
cq quest start <quest_id>
cq quest finish <quest_id>
cq status
cq achievements
cq config llm --provider ollama --model llama3.1
cq doctor
cq vscode install
```

When working from source without installing the package, use:

```bash
PYTHONPATH=src python -m codequest.cli doctor
```

## LLM Scope

The first implemented quest-generation provider is local Ollama.

Default config:
- Provider: `ollama`
- URL: `http://localhost:11434`
- Model: `llama3.1`
- Quest count: `5`

Generated quests must be parsed as structured JSON and validated before saving. Do not save raw model output directly. Every generated quest must include deterministic verification through commands or expected paths.

AI review is separate from quest generation and remains optional. Do not make XP depend on LLM review unless the product direction explicitly changes.

## Testing

Run the full test suite before handing off changes:

```bash
pytest -q
```

Tests currently cover:
- Storage initialization and config defaults.
- Project profile persistence.
- Scoring and achievement behavior.
- Verifier path checks.
- Repo analysis.
- Quest generation parsing and validation.
- CLI command wiring.

Add tests for new behavior, especially around:
- CLI commands.
- YAML storage compatibility.
- Generated quest validation.
- LLM error handling.
- Verification and XP award boundaries.

## Engineering Guardrails

Keep the project local-first and beginner-friendly.

Prefer:
- Small Python modules with testable functions.
- YAML/JSON-compatible data structures.
- Deterministic checks before XP changes.
- Clear CLI errors that explain what the user should do next.
- Backward-compatible loading of existing `.codequest/` files.

Avoid:
- Requiring a hosted API key for the main workflow.
- Writing generated quests without validation.
- Moving core game logic into an IDE extension.
- Making tests require Ollama or network access.
- Adding a database before file-based storage is clearly insufficient.
- Rewriting unrelated code while implementing focused changes.

## Local Agent Work Log

Use `agent-work.log` at the repo root for local agentic work notes. It is ignored by Git and should not be committed.

Suggested entry format:

```text
2026-06-16T12:35:07+01:00 | agent | action | files/commands | outcome
```

Record meaningful steps such as:
- Files changed.
- Tests run.
- Commands that failed.
- Local environment issues.
- Reasons for choosing a fallback.
- Any point where behavior diverged from expectations.

Do not store secrets, API keys, personal data, or large command outputs in the log.
