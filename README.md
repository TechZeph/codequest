# CodeQuest

CodeQuest is a local CLI that turns real programming projects into quests, XP,
levels, achievements, and boss fights.

It exists for learners who often use AI-written code and want to rebuild the
habit of reading, writing, debugging, and understanding code by hand. The tool
rewards verified learning behaviours, not passive time spent.

## Install Locally

CodeQuest requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

This installs the `cq` command in your virtual environment.

## Quick Start

Run this inside the project you want to learn through:

```bash
cq play
```

`cq play` initializes CodeQuest if needed, asks what you are building, analyzes
the current repository, asks a local LLM for a scaling quest chain, saves the
quests, and offers to start the first quest.

For local quest generation, CodeQuest expects Ollama to be running:

```bash
ollama serve
ollama pull llama3.1
cq doctor
```

You can change the local model with:

```bash
cq config llm --provider ollama --model llama3.1
```

CodeQuest still works without an LLM by creating quests manually:

```bash
cq quest new
```

## Initialize CodeQuest Manually

Run this in the project where you want to track practice:

```bash
cq init
```

This creates:

```text
.codequest/
  config.yaml
  project.yaml
  profile.yaml
  log.yaml
  quests/
```

Existing files are not overwritten unless you run:

```bash
cq init --force
```

## Create A Quest

```bash
cq quest new
```

The interactive prompt asks for a title, summary, difficulty, mode, XP rewards,
requirements, verification commands, expected paths, and optional AI review.

Quest files are stored as YAML in `.codequest/quests/`.

## Generate Quests

After setup, generate more project-specific quests with:

```bash
cq generate
```

The generator combines your questionnaire answers, repository structure, README,
detected languages, tests, and completed quest history. Generated quests are
validated before they are saved. Each generated quest must include deterministic
verification, such as expected paths or local commands.

## Start And Finish A Quest

```bash
cq quest list
cq quest start repo-init-001
# manually write the code
cq quest finish repo-init-001
cq status
```

When a quest finishes successfully, CodeQuest awards XP, updates your level and
rank, unlocks achievements, and writes a log entry.

## Verification

`cq quest finish <quest_id>` runs deterministic checks before XP is awarded:

- changed files listed in the quest must exist
- expected files or paths must exist
- verification commands must exit with status code `0`
- stdout and stderr are captured and shown when useful

If verification fails, the quest stays active so you can fix the problem and run
the finish command again.

## AI Review

AI review is optional. CodeQuest works without any AI API key.

Each quest can set:

```yaml
ai_review:
  enabled: false
  provider: none
```

For the MVP, AI review is a clean stub for future providers. Quest generation
uses the local Ollama provider configured under `llm` in `.codequest/config.yaml`.

Recognized AI review providers:

- `none`
- `openai`
- `ollama`

If a quest enables AI review but no provider is configured, CodeQuest prints:

```text
AI review skipped: no provider configured.
```

Deterministic verification always runs first. AI review is never required to use
the tool.

## Modes

- `green`: no AI-generated full code; docs and notes are allowed
- `amber`: AI can explain, review, and give hints, but should not write the full solution
- `red`: AI can generate or refactor code; use for larger projects only

## VS Code Tasks

Run:

```bash
cq vscode install
```

This creates or updates `.vscode/tasks.json` with tasks for:

- CodeQuest Status
- CodeQuest List Quests
- CodeQuest Finish Current Quest

If an existing `tasks.json` is present, CodeQuest creates a `.bak` backup and
merges in missing tasks.

## Example Workflow

```bash
cq play
cq quest list
cq quest start repo-init-001
# user manually writes code
cq quest finish repo-init-001
cq status
```

## Boss Fights

List MVP boss fights:

```bash
cq boss list
```

Included bosses:

- `repo-init-lite`
- `obsidian-link-scanner`
- `github-repo-fetcher`

## Development

Run tests:

```bash
pytest
```

The MVP intentionally avoids a database, web app, or full IDE extension. The
goal is a small, readable CLI that can later grow into editor integrations.
