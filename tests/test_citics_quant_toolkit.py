from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import citics_quant_toolkit as toolkit  # noqa: E402


def test_load_config_uses_example_when_project_config_is_absent():
    config = toolkit.load_config(PROJECT_ROOT / "config.example.json")

    assert config["xuntou_root"].endswith("迅投极速交易终端睿智融科版")
    assert config["strategy_file"].endswith("STOCK_FACTOR_BASELINE.py")


def test_find_skill_locates_xtquant_strategy():
    path = toolkit.find_skill("xtquant-strategy")

    assert path is not None
    assert (path / "SKILL.md").exists()


def test_inspect_python_packages_reports_expected_shape():
    report = toolkit.inspect_python_packages(["json"])

    assert report["json"]["ok"] is True
    assert "origin" in report["json"]


def test_find_factor_python_prefers_configured_path():
    expected = PROJECT_ROOT / "fake-python.exe"
    config = {
        "xuntou_root": str(PROJECT_ROOT),
        "factor_python": str(expected),
    }

    assert toolkit.find_factor_python(config) == expected


def test_parser_accepts_doctor_command():
    parser = toolkit.build_parser()
    args = parser.parse_args(["doctor"])

    assert args.command == "doctor"
