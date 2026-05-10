# -*- coding: utf-8 -*-
"""Publish a reviewed strategy into the Xuntou terminal strategy directory.

The command is dry-run by default. Add --execute to copy the file.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TERMINAL_STRATEGY_LINK = PROJECT_ROOT / "links" / "terminal-python-strategies"
BACKUP_DIR = PROJECT_ROOT / "strategies" / "archive" / "published_backups"


def compile_strategy(path: Path) -> None:
    data = path.read_bytes()
    compile(data, str(path), "exec")


def resolve_inside_project(path: Path) -> Path:
    resolved = path.resolve()
    project = PROJECT_ROOT.resolve()
    if not resolved.is_relative_to(project):
        raise ValueError(f"Source must be inside project: {resolved}")
    return resolved


def publish(source: Path, target_name: str, execute: bool) -> int:
    source = resolve_inside_project(source)
    if not source.exists():
        print(f"Missing source strategy: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() != ".py":
        print(f"Strategy source must be a .py file: {source}", file=sys.stderr)
        return 2
    if not TERMINAL_STRATEGY_LINK.exists():
        print(f"Missing terminal strategy link: {TERMINAL_STRATEGY_LINK}", file=sys.stderr)
        return 2

    compile_strategy(source)
    target = TERMINAL_STRATEGY_LINK / target_name
    backup = None
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = BACKUP_DIR / f"{target.stem}.{stamp}{target.suffix}"

    print(f"source: {source}")
    print(f"target: {target}")
    if backup:
        print(f"backup: {backup}")
    print(f"mode: {'execute' if execute else 'dry-run'}")

    if not execute:
        print("Dry-run only. Add --execute to publish.")
        return 0

    if backup:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
    shutil.copy2(source, target)
    print("Published.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Strategy file under this project")
    parser.add_argument("--name", required=True, help="Target filename in Xuntou strategy directory")
    parser.add_argument("--execute", action="store_true", help="Actually copy after dry-run review")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return publish(args.source, args.name, args.execute)


if __name__ == "__main__":
    raise SystemExit(main())
