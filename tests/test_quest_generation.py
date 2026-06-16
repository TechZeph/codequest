import json

import pytest

from codequest.quest_generation import (
    QuestGenerationError,
    build_generation_prompt,
    generate_quests,
    parse_generated_quests,
)


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.prompt = ""

    def generate(self, prompt):
        self.prompt = prompt
        return self.response


def generated_response():
    return json.dumps(
        {
            "quests": [
                {
                    "title": "Add a project status command",
                    "summary": "Create a CLI command that prints current project status.",
                    "difficulty": "beginner",
                    "mode": "green",
                    "skills": {"cli": 10, "logic": 10, "unknown": 99},
                    "requirements": ["Add the command", "Cover it with a test"],
                    "verification": {
                        "changed_files": ["src/demo/cli.py"],
                        "commands": ["pytest"],
                        "expected_paths": ["src/demo/cli.py"],
                        "forbidden": ["Do not ask AI to write the full implementation"],
                    },
                    "notes": "Look at the existing parser setup.",
                }
            ]
        }
    )


def test_parse_generated_quests_normalizes_valid_model_output():
    quests = parse_generated_quests(generated_response(), existing_quests=[{"id": "add-a-project-status-command"}])

    assert quests[0]["id"] == "add-a-project-status-command-2"
    assert quests[0]["status"] == "not_started"
    assert quests[0]["skills"] == {"cli": 10, "logic": 10}
    assert quests[0]["verification"]["commands"] == ["pytest"]


def test_parse_generated_quests_rejects_quests_without_deterministic_verification():
    response = json.dumps(
        {
            "quests": [
                {
                    "title": "Think about architecture",
                    "requirements": ["Write down an idea"],
                    "verification": {"commands": [], "expected_paths": []},
                }
            ]
        }
    )

    with pytest.raises(QuestGenerationError, match="no deterministic verification"):
        parse_generated_quests(response)


def test_generate_quests_uses_prompt_context_and_provider():
    llm = FakeLLM(generated_response())
    project = {"project_name": "Demo", "learner_level": "beginner"}
    repo = {"languages": {"Python": 2}, "manifests": ["pyproject.toml"], "source_paths": ["src/demo/cli.py"]}

    quests = generate_quests(llm, project, repo, [], quest_count=1)

    assert quests[0]["title"] == "Add a project status command"
    assert "Demo" in llm.prompt
    assert "Python" in llm.prompt


def test_generation_prompt_requests_scaling_difficulty():
    prompt = build_generation_prompt({}, {"languages": {}}, [], quest_count=3)

    assert "Create 3 quests" in prompt
    assert "Make each quest harder than the previous one" in prompt

