"""Regression checks for the package retirement notice and metadata."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_retirement_notice_and_metadata():
    """Keep the public retirement statement and packaging metadata aligned."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    readme = (ROOT / "README.md").read_text()

    project = pyproject["project"]
    assert project["description"].startswith("Deprecated")
    assert "Development Status :: 7 - Inactive" in project["classifiers"]

    first_section = readme.split("\n## ", 1)[0]
    assert "Deprecated (2026-08-27)" in first_section
    for replacement in ("agent-browser", "transcytosis", "tegument"):
        assert replacement in first_section
