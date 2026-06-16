from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


IGNORED_DIRS = {
    ".codequest",
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}

LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
}

MANIFESTS = [
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Gemfile",
]


def _iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _read_readme(root: Path, max_chars: int = 1200) -> str:
    for name in ("README.md", "README.rst", "README.txt", "readme.md"):
        path = root / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")[:max_chars].strip()
    return ""


def analyze_repo(root: Path | None = None) -> dict[str, Any]:
    project_root = root or Path.cwd()
    files = _iter_project_files(project_root)
    suffixes = Counter(path.suffix for path in files if path.suffix)
    languages = Counter()
    for suffix, count in suffixes.items():
        language = LANGUAGE_BY_SUFFIX.get(suffix)
        if language:
            languages[language] += count

    manifests = [name for name in MANIFESTS if (project_root / name).exists()]
    test_paths = [
        str(path.relative_to(project_root))
        for path in files
        if "test" in path.name.lower() or "tests" in path.relative_to(project_root).parts
    ][:20]

    source_paths = [
        str(path.relative_to(project_root))
        for path in files
        if path.suffix in LANGUAGE_BY_SUFFIX
    ][:40]

    return {
        "root": str(project_root),
        "file_count": len(files),
        "manifests": manifests,
        "languages": dict(languages.most_common()),
        "source_paths": source_paths,
        "test_paths": test_paths,
        "has_tests": bool(test_paths),
        "readme_excerpt": _read_readme(project_root),
    }


def format_repo_summary(summary: dict[str, Any]) -> str:
    languages = ", ".join(f"{name} ({count})" for name, count in summary.get("languages", {}).items()) or "unknown"
    manifests = ", ".join(summary.get("manifests", [])) or "none"
    tests = "yes" if summary.get("has_tests") else "no"
    return (
        f"Languages: {languages}\n"
        f"Manifests: {manifests}\n"
        f"Tests present: {tests}\n"
        f"Source examples: {', '.join(summary.get('source_paths', [])[:10]) or 'none'}\n"
        f"README excerpt:\n{summary.get('readme_excerpt') or '(none)'}"
    )

