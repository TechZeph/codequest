from codequest.storage import init_storage, load_config, load_project_profile, save_project_profile


def test_storage_init_creates_expected_files(tmp_path):
    init_storage(tmp_path)

    assert (tmp_path / ".codequest").is_dir()
    assert (tmp_path / ".codequest" / "config.yaml").is_file()
    assert (tmp_path / ".codequest" / "project.yaml").is_file()
    assert (tmp_path / ".codequest" / "profile.yaml").is_file()
    assert (tmp_path / ".codequest" / "log.yaml").is_file()
    assert (tmp_path / ".codequest" / "quests").is_dir()


def test_storage_init_does_not_overwrite_without_force(tmp_path):
    init_storage(tmp_path)
    profile = tmp_path / ".codequest" / "profile.yaml"
    profile.write_text("username: custom\n", encoding="utf-8")

    init_storage(tmp_path)

    assert profile.read_text(encoding="utf-8") == "username: custom\n"


def test_project_profile_round_trips_with_defaults(tmp_path):
    init_storage(tmp_path)

    save_project_profile({"project_name": "Demo", "learner_level": "intermediate"}, tmp_path)
    project = load_project_profile(tmp_path)

    assert project["project_name"] == "Demo"
    assert project["learner_level"] == "intermediate"
    assert project["time_budget"] == "30 minutes"


def test_config_loads_llm_defaults(tmp_path):
    init_storage(tmp_path)

    config = load_config(tmp_path)

    assert config["llm"]["provider"] == "ollama"
    assert config["llm"]["ollama_url"] == "http://localhost:11434"


def test_config_tolerates_null_nested_sections(tmp_path):
    init_storage(tmp_path)
    (tmp_path / ".codequest" / "config.yaml").write_text("llm:\nai_review:\n", encoding="utf-8")

    config = load_config(tmp_path)

    assert config["llm"]["provider"] == "ollama"
    assert config["ai_review"]["provider"] == "none"
