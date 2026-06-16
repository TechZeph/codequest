from codequest.verifier import verify_quest


def test_verifier_detects_missing_expected_path(tmp_path):
    quest = {"verification": {"expected_paths": ["missing.txt"]}}

    result = verify_quest(quest, tmp_path)

    assert result.passed is False
    assert result.failures[0].message == "Missing expected path: missing.txt"


def test_verifier_passes_when_expected_path_exists(tmp_path):
    (tmp_path / "present.txt").write_text("ok", encoding="utf-8")
    quest = {"verification": {"expected_paths": ["present.txt"]}}

    result = verify_quest(quest, tmp_path)

    assert result.passed is True
    assert not result.failures

