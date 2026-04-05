"""Install trogocytosis skills into an AI coding tool's skill directory.

Supports: Claude Code, Gemini CLI, Copilot CLI, Codex.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Platform → default skill install directory
SKILL_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "gemini": Path.home() / ".gemini" / "skills",
    "copilot": Path.home() / ".copilot" / "skills",
    "codex": Path.home() / ".codex" / "skills",
}


def _find_skills_source() -> Path:
    """Locate the skills/ directory shipped with this package."""
    pkg_dir = Path(__file__).resolve().parent
    for candidate in [
        pkg_dir / "_skills",                 # wheel install (via force-include)
        pkg_dir.parent.parent.parent / "skills",  # dev install (editable)
        pkg_dir.parent.parent / "skills",    # alternate dev layout
    ]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("skills/ directory not found in package")


def install_skills(target: Path, *, force: bool = False) -> list[str]:
    """Copy SKILL.md files into target directory. Returns list of installed skill names."""
    source = _find_skills_source()
    target.mkdir(parents=True, exist_ok=True)

    installed = []
    for skill_dir in sorted(source.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        dest_dir = target / skill_dir.name
        dest_file = dest_dir / "SKILL.md"

        if dest_file.exists() and not force:
            print(f"SKIP: {skill_dir.name} (exists, use --force to overwrite)", file=sys.stderr)
            continue

        dest_dir.mkdir(exist_ok=True)
        shutil.copy2(skill_file, dest_file)
        installed.append(skill_dir.name)

    return installed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trogocytosis install-skills",
        description="Install trogocytosis skills into your AI coding tool",
    )
    parser.add_argument(
        "--target",
        choices=list(SKILL_DIRS.keys()) + ["all"],
        default="claude",
        help="Which tool to install into (default: claude)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Custom skill directory (overrides --target)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing skills",
    )
    args = parser.parse_args(argv)

    if args.path:
        targets = [args.path]
    elif args.target == "all":
        targets = [d for d in SKILL_DIRS.values() if d.parent.exists()]
        if not targets:
            print("No AI tool directories found (~/.claude, ~/.gemini, etc.)", file=sys.stderr)
            return 1
    else:
        targets = [SKILL_DIRS[args.target]]

    for target in targets:
        print(f"Installing to {target}")
        installed = install_skills(target, force=args.force)
        if installed:
            print(f"  {len(installed)} skills installed: {', '.join(installed)}")
        else:
            print("  nothing to install (all skills exist, use --force to overwrite)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
