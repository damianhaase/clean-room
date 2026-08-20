"""Offline routing evaluation and route-score helpers."""

import json
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable

from .router import ROUTE_SCORE_THRESHOLD, build_profiles, route

Assertion = tuple[str, str, bool]


@dataclass(frozen=True)
class Evaluation:
    matched: int
    total: int
    text: str

    @property
    def score(self) -> float:
        return self.matched / self.total if self.total else 0.0


def load_assertions(path: Path) -> list[Assertion]:
    """Load `{agent, query, should_trigger}` assertions from JSON."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("eval file must contain a list")
    return [
        (str(item["agent"]), str(item["query"]), bool(item["should_trigger"]))
        for item in payload
    ]


def load_agent_documents(agents_dir: Path) -> dict[str, str]:
    """Load simple agent bodies keyed by their markdown stem."""
    directory = Path(agents_dir)
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    return {
        path.name.removesuffix(".agent.md"): path.read_text(encoding="utf-8")
        for path in sorted(directory.glob("*.agent.md"))
    }


def evaluate(agent_documents: dict[str, str], assertions: Iterable[Assertion]) -> Evaluation:
    """Evaluate assertions and produce per-agent plus overall report text."""
    profiles = build_profiles(agent_documents) if agent_documents else {}
    grouped: dict[str, list[bool]] = {}
    for owner, query, should_trigger in assertions:
        prediction = route(query, profiles) if profiles else None
        passed = bool(profiles) and ((prediction == owner) if should_trigger else (prediction != owner))
        grouped.setdefault(owner, []).append(passed)
    lines: list[str] = []
    matched = sum(sum(results) for results in grouped.values())
    total = sum(len(results) for results in grouped.values())
    for owner in sorted(grouped):
        passed = sum(grouped[owner])
        state = "PASS" if passed == len(grouped[owner]) else "FAIL"
        lines.append(f"{state} {owner}: {passed}/{len(grouped[owner])}")
    score = matched / total if total else 0.0
    lines.append(f"overall accuracy {score:.3f}")
    return Evaluation(matched, total, "\n".join(lines))


def route_score(agent_documents: dict[str, str], assertions: Iterable[Assertion]) -> float:
    """Return aggregate matched/total accuracy, or zero for empty inputs."""
    return evaluate(agent_documents, assertions).score


def threshold_passes(value: float) -> bool:
    """Apply the inclusive documented route-score threshold."""
    return value >= ROUTE_SCORE_THRESHOLD