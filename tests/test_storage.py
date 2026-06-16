from codequest.storage import init_storage


def test_storage_init_creates_expected_files(tmp_path):
    init_storage(tmp_path)

    assert (tmp_path / ".codequest").is_dir()
    assert (tmp_path / ".codequest" / "config.yaml").is_file()
    assert (tmp_path / ".codequest" / "profile.yaml").is_file()
    assert (tmp_path / ".codequest" / "log.yaml").is_file()
    assert (tmp_path / ".codequest" / "quests").is_dir()


def test_storage_init_does_not_overwrite_without_force(tmp_path):
    init_storage(tmp_path)
    profile = tmp_path / ".codequest" / "profile.yaml"
    profile.write_text("username: custom\n", encoding="utf-8")

    init_storage(tmp_path)

    assert profile.read_text(encoding="utf-8") == "username: custom\n"

