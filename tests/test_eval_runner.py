import json
from pathlib import Path

from dh_skills.cli import main
from dh_skills.eval_runner import ROUTE_SCORE_THRESHOLD, evaluate, route_score


def profiles():
    return {
        "dh-design": "Design APIs and interfaces.",
        "dh-test": "Verify tests and coverage.",
    }


def test_route_score_counts_exact_matches_and_empty_cases():
    assertions = [
        ("dh-design", "design API", True),
        ("dh-test", "test coverage", True),
        ("dh-test", "design API", False),
        ("dh-design", "test coverage", False),
    ]

    assert route_score(profiles(), assertions) == 1.0
    assert route_score(profiles(), []) == 0.0
    assert route_score({}, assertions) == 0.0


def test_unknown_agent_positive_fails_and_negative_passes():
    assert route_score(profiles(), [("dh-missing", "anything", True)]) == 0.0
    assert route_score(profiles(), [("dh-missing", "anything", False)]) == 1.0


def test_evaluate_reports_per_agent_and_overall_accuracy():
    report = evaluate(profiles(), [
        ("dh-design", "design API", True),
        ("dh-test", "design API", True),
    ])

    assert report.matched == 1
    assert report.total == 2
    assert "PASS dh-design: 1/1" in report.text
    assert "FAIL dh-test: 0/1" in report.text
    assert "overall accuracy 0.500" in report.text


def test_route_score_threshold_includes_exact_boundary():
    assert ROUTE_SCORE_THRESHOLD == 0.95
    assertions = [("dh-design", "design API", True)] * 20
    assertions[-1] = ("dh-test", "design API", False)
    assert route_score(profiles(), assertions) >= ROUTE_SCORE_THRESHOLD


def test_cli_eval_and_route_score_use_json_fixture(tmp_path, capsys):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "dh-design.agent.md").write_text("design APIs", encoding="utf-8")
    (agents_dir / "dh-test.agent.md").write_text("test coverage", encoding="utf-8")
    eval_file = tmp_path / "eval.json"
    eval_file.write_text(json.dumps([
        {"agent": "dh-design", "query": "design API", "should_trigger": True},
        {"agent": "dh-test", "query": "test coverage", "should_trigger": True},
    ]), encoding="utf-8")

    assert main(["eval", "--agents-dir", str(agents_dir), "--eval-file", str(eval_file)]) == 0
    assert "overall accuracy 1.000" in capsys.readouterr().out
    assert main(["route-score", "--agents-dir", str(agents_dir), "--eval-file", str(eval_file)]) == 0
    assert "routing accuracy 1.000" in capsys.readouterr().out


def test_cli_route_score_fails_below_threshold_and_missing_agents_is_usage_error(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "dh-design.agent.md").write_text("design APIs", encoding="utf-8")
    eval_file = tmp_path / "eval.json"
    eval_file.write_text(json.dumps([
        {"agent": "dh-design", "query": "unrelated", "should_trigger": True},
    ]), encoding="utf-8")

    assert main(["route-score", "--agents-dir", str(agents_dir), "--eval-file", str(eval_file)]) == 1
    assert main(["route-score", "--agents-dir", str(tmp_path / "missing"), "--eval-file", str(eval_file)]) == 2
