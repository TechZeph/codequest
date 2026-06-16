from codequest.repo_analyzer import analyze_repo, format_repo_summary


def test_analyze_repo_detects_python_project_shape(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\nBuilds useful things.\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

    summary = analyze_repo(tmp_path)

    assert summary["manifests"] == ["pyproject.toml"]
    assert summary["languages"]["Python"] == 2
    assert summary["has_tests"] is True
    assert "Builds useful things" in summary["readme_excerpt"]
    assert "Languages: Python (2)" in format_repo_summary(summary)

