# -*- coding: utf-8 -*-
"""Local command hub for the CITICS/XtQuant competition workspace.

The commands here are deliberately read-only. They inspect the local Codex
skills, Python environment, Xuntou terminal, strategy file, logs, and XtData
service without placing orders.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config.json"
EXAMPLE_CONFIG = PROJECT_ROOT / "config.example.json"

DEFAULT_SKILLS = [
    "xtquant-strategy",
    "systematic-debugging",
    "test-driven-development",
    "jupyter-notebook",
    "spreadsheet",
    "pdf",
    "doc",
    "awesome-ai-research-writing",
]

DEFAULT_PYTHON_PACKAGES = [
    "numpy",
    "pandas",
    "matplotlib",
    "openpyxl",
    "jupyter",
    "pytest",
    "pdfplumber",
    "pypdf",
    "docx",
]


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load config.json when present, otherwise config.example.json."""
    selected = path or (DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else EXAMPLE_CONFIG)
    if not selected.exists():
        raise FileNotFoundError(f"Config file not found: {selected}")
    config = _read_json(selected)
    config["_config_path"] = str(selected)
    return config


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def candidate_skill_dirs(name: str) -> list[Path]:
    """Return likely install locations for a Codex skill."""
    home = Path.home()
    roots = [
        _codex_home() / "skills",
        home / ".codex" / "skills",
        home / ".agents" / "skills",
        home / ".codex" / "skills" / ".system",
        home / ".agents" / "skills" / ".system",
    ]
    return [root / name for root in roots]


def find_skill(name: str) -> Path | None:
    for path in candidate_skill_dirs(name):
        if (path / "SKILL.md").exists():
            return path
    return None


def inspect_skills(skills: list[str] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in skills or DEFAULT_SKILLS:
        path = find_skill(name)
        result[name] = {
            "ok": path is not None,
            "path": str(path) if path else "",
        }
    return result


def inspect_python_packages(packages: list[str] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in packages or DEFAULT_PYTHON_PACKAGES:
        spec = importlib.util.find_spec(name)
        result[name] = {
            "ok": spec is not None,
            "origin": getattr(spec, "origin", "") if spec else "",
        }
    return result


def inspect_workspace(config: dict[str, Any]) -> dict[str, Any]:
    root = Path(config["xuntou_root"])
    strategy_file = Path(config["strategy_file"])
    log_dir = Path(config["log_dir"])
    skill_root = Path(config.get("skill_root", ""))
    return {
        "project_root": str(PROJECT_ROOT),
        "config_path": config.get("_config_path", ""),
        "xuntou_root": {
            "path": str(root),
            "ok": root.exists(),
        },
        "strategy_file": {
            "path": str(strategy_file),
            "ok": strategy_file.exists(),
            "size": strategy_file.stat().st_size if strategy_file.exists() else None,
        },
        "log_dir": {
            "path": str(log_dir),
            "ok": log_dir.exists(),
        },
        "xtquant_skill_root": {
            "path": str(skill_root),
            "ok": (skill_root / "SKILL.md").exists(),
        },
    }


def _run_python_script(script: Path, args: list[str]) -> int:
    if not script.exists():
        print(f"Missing script: {script}", file=sys.stderr)
        return 2
    command = [sys.executable, str(script)] + args
    return subprocess.call(command, cwd=str(PROJECT_ROOT))


def _run_script_with_python(python_exe: Path, script: Path, args: list[str]) -> int:
    if not script.exists():
        print(f"Missing script: {script}", file=sys.stderr)
        return 2
    if not python_exe.exists():
        print(f"Missing Python executable: {python_exe}", file=sys.stderr)
        return 2
    command = [str(python_exe), str(script)] + args
    return subprocess.call(command, cwd=str(PROJECT_ROOT))


def _xtquant_script(config: dict[str, Any], script_name: str) -> Path:
    skill_root = Path(config["skill_root"])
    return skill_root / "scripts" / script_name


def find_factor_python(config: dict[str, Any]) -> Path:
    configured_value = config.get("factor_python", "")
    if configured_value:
        configured = Path(configured_value)
        return configured
    return Path(config["xuntou_root"]) / "bin.x64" / "因子版" / "python.exe"


def command_doctor(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    factor_python = find_factor_python(config)
    report = {
        "workspace": inspect_workspace(config),
        "factor_python": {
            "path": str(factor_python),
            "ok": factor_python.exists(),
        },
        "skills": inspect_skills(),
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "packages": inspect_python_packages(),
        },
        "plugins": {
            "Browser": {
                "ok": True,
                "note": "Enabled in the current Codex app session; use it for localhost/file UI checks.",
            },
            "Chrome": {
                "ok": True,
                "note": "Enabled in the current Codex app session; use it for logged-in web pages.",
            },
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    required_checks = [
        report["workspace"]["xuntou_root"]["ok"],
        report["workspace"]["log_dir"]["ok"],
        report["workspace"]["xtquant_skill_root"]["ok"],
        report["factor_python"]["ok"],
        all(item["ok"] for item in report["skills"].values()),
        all(item["ok"] for item in report["python"]["packages"].values()),
    ]
    return 0 if all(required_checks) else 1


def command_env(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    script = _xtquant_script(config, "inspect_xtquant_env.py")
    return _run_python_script(script, [config["xuntou_root"]])


def command_strategy(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    strategy = args.path or config["strategy_file"]
    return _run_python_script(_xtquant_script(config, "inspect_strategy.py"), [strategy])


def command_logs(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    command_args = ["--log-dir", config["log_dir"]]
    if args.pattern:
        command_args += ["--pattern", args.pattern]
    if args.tail_bytes:
        command_args += ["--tail-bytes", str(args.tail_bytes)]
    return _run_python_script(_xtquant_script(config, "read_latest_logs.py"), command_args)


def command_xtdata(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    factor_python = find_factor_python(config)
    command_args = [
        "--root",
        config["xuntou_root"],
        "--stock",
        args.stock or config.get("default_stock", "000001.SZ"),
        "--sector",
        args.sector or config.get("default_sector", "沪深A股"),
    ]
    if args.start:
        command_args += ["--start", args.start]
    if args.end:
        command_args += ["--end", args.end]
    return _run_script_with_python(
        factor_python,
        _xtquant_script(config, "xtdata_smoke_test.py"),
        command_args,
    )


def command_init_config(args: argparse.Namespace) -> int:
    target = Path(args.output or DEFAULT_CONFIG)
    if target.exists() and not args.force:
        print(f"Config already exists: {target}")
        return 0
    shutil.copyfile(EXAMPLE_CONFIG, target)
    print(f"Wrote {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="", help="Optional config JSON path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local deployment status")
    doctor.set_defaults(func=command_doctor)

    env = subparsers.add_parser("env", help="Inspect Xuntou/XtQuant Python environment")
    env.set_defaults(func=command_env)

    strategy = subparsers.add_parser("strategy", help="Inspect a terminal strategy file")
    strategy.add_argument("--path", default="", help="Strategy file path; defaults to config")
    strategy.set_defaults(func=command_strategy)

    logs = subparsers.add_parser("logs", help="Read latest Xuntou strategy logs")
    logs.add_argument("--pattern", default="", help="Optional substring filter")
    logs.add_argument("--tail-bytes", type=int, default=200000)
    logs.set_defaults(func=command_logs)

    xtdata = subparsers.add_parser("xtdata", help="Run read-only XtData smoke test")
    xtdata.add_argument("--stock", default="")
    xtdata.add_argument("--sector", default="")
    xtdata.add_argument("--start", default="")
    xtdata.add_argument("--end", default="")
    xtdata.set_defaults(func=command_xtdata)

    init_config = subparsers.add_parser("init-config", help="Create config.json from config.example.json")
    init_config.add_argument("--output", default="")
    init_config.add_argument("--force", action="store_true")
    init_config.set_defaults(func=command_init_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
