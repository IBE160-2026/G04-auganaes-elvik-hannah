"""Story 1.6 (FR-22, AD-15): .env.example lists exactly the variables the app reads."""

import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "backend" / "app"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

# Set by the hosting platform, never by us, so not listed as a key.
PLATFORM_SET = {"VERCEL"}


def read_env_names() -> set[str]:
    """Every literal name passed to config._env(...) anywhere in app/."""
    names: set[str] = set()
    for path in APP_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if called != "_env":
                continue
            arg = node.args[0] if node.args else None
            assert isinstance(arg, ast.Constant) and isinstance(arg.value, str), (
                f"{path.relative_to(REPO_ROOT)}:{node.lineno}: _env() må få et navn som streng"
            )
            names.add(arg.value)
    return names


def example_keys() -> set[str]:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Z][A-Z0-9_]*)=", text, flags=re.MULTILINE))


def test_app_reads_variables() -> None:
    # Guards the AST walk itself: an empty set would make the checks below pass trivially.
    assert {"DATABASE_URL", "VERCEL"} <= read_env_names()


def test_every_read_variable_is_in_env_example() -> None:
    missing = read_env_names() - example_keys() - PLATFORM_SET
    assert not missing, f"Mangler i .env.example: {sorted(missing)}"


def test_every_env_example_key_is_read() -> None:
    unread = example_keys() - read_env_names()
    assert not unread, f"Står i .env.example, men leses ikke av appen: {sorted(unread)}"


def test_env_is_gitignored() -> None:
    if shutil.which("git") is None or not (REPO_ROOT / ".git").exists():
        pytest.skip("git eller .git mangler")
    result = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=REPO_ROOT, check=False)
    assert result.returncode == 0, ".env er ikke ignorert av git"
