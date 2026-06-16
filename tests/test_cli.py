from codequest import cli
from codequest.storage import init_storage, load_config


def test_config_llm_updates_saved_config(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    init_storage(tmp_path)

    result = cli.main(["config", "llm", "--provider", "ollama", "--model", "mistral", "--count", "3"])

    assert result == 0
    config = load_config(tmp_path)
    assert config["llm"]["provider"] == "ollama"
    assert config["llm"]["ollama_model"] == "mistral"
    assert config["llm"]["quest_count"] == 3
    assert "LLM configuration updated" in capsys.readouterr().out


def test_generate_command_prints_generated_quests(monkeypatch, capsys):
    def fake_generate(count=None):
        assert count == 1
        return [{"id": "demo-quest", "title": "Demo quest", "difficulty": "beginner", "mode": "green"}]

    monkeypatch.setattr(cli, "_generate_and_save_quests", fake_generate)

    result = cli.main(["generate", "--count", "1"])

    assert result == 0
    assert "demo-quest - Demo quest" in capsys.readouterr().out

