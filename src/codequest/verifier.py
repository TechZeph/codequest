from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    stdout: str = ""
    stderr: str = ""


@dataclass
class VerificationResult:
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def failures(self) -> list[CheckResult]:
        return [check for check in self.checks if not check.passed]


def _path_exists(path: str, root: Path) -> CheckResult:
    target = root / path
    if target.exists():
        return CheckResult("path_exists", True, f"Found {path}")
    return CheckResult("path_exists", False, f"Missing expected path: {path}")


def _run_command(command: str, root: Path, timeout: int = 30) -> CheckResult:
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            "command",
            False,
            f"Command timed out after {timeout}s: {command}",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        )

    passed = completed.returncode == 0
    message = f"Command passed: {command}" if passed else f"Command failed ({completed.returncode}): {command}"
    return CheckResult("command", passed, message, completed.stdout, completed.stderr)


def verify_quest(quest: dict[str, Any], root: Path | None = None) -> VerificationResult:
    project_root = root or Path.cwd()
    verification = quest.get("verification", {}) or {}
    checks: list[CheckResult] = []

    for changed_file in verification.get("changed_files", []) or []:
        checks.append(_path_exists(changed_file, project_root))

    for command in verification.get("commands", []) or []:
        checks.append(_run_command(command, project_root))

    for expected_path in verification.get("expected_paths", []) or []:
        checks.append(_path_exists(expected_path, project_root))

    return VerificationResult(passed=all(check.passed for check in checks), checks=checks)

