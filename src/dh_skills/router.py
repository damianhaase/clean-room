"""Deterministic lexical router scoring and calibration."""

import math
from collections import Counter
from dataclasses import dataclass
from collections.abc import Mapping

from .tokenizer import bigrams, stem, tokenize

BIGRAM_WEIGHT = 2.2
NAME_BONUS = 0.45
SIGNAL_BONUS = 0.55
ROUTE_SCORE_THRESHOLD = 0.95

COORDINATOR_PHRASES = (
    "the agents", "end-to-end", "the pipeline", "orchestrate", "pr comments", "through release",
)
ROLE_ALIASES = {
    "dh-planning": ("decompose", "scaffold", "breakdown"),
    "dh-test": ("verification", "coverage", "suite"),
    "dh-release": ("ship", "deploy"),
    "dh-kb": ("knowledge", "index", "embeddings"),
}
STRONG_SIGNALS = {
    "dh-release": ("rebase", "squash", "jar", "deploy"),
    "dh-kb": ("embeddings", "reindex"),
    "dh-test": ("pytest", "coverage"),
}
PHRASE_SIGNALS = {
    "dh-planning": ("implementation plan",),
    "dh-kb": ("knowledge base", "db index"),
}
VETO_PHRASES = {
    "dh-kb": ("ask the knowledge", "how does the knowledge"),
}


@dataclass(frozen=True)
class AgentProfile:
    key: str
    unigrams: frozenset[str]
    bigrams: frozenset[tuple[str, str]]
    role_stem: str
    signal_stems: frozenset[str]
    phrase_signals: tuple[str, ...]


def idf(agent_count: int, document_frequency: int) -> float:
    """Return smoothed inverse document frequency."""
    return math.log((agent_count + 1) / (document_frequency + 1)) + 1


def build_profiles(agent_documents: Mapping[str, str]) -> dict[str, AgentProfile]:
    """Build lexical profiles from agent keys and descriptions."""
    profiles: dict[str, AgentProfile] = {}
    for key, description in agent_documents.items():
        features = tokenize(f"{key} {description}")
        aliases = {stem(term) for term in ROLE_ALIASES.get(key, ())}
        role = stem(key.rsplit("-", 1)[-1])
        signals = frozenset(stem(term) for term in STRONG_SIGNALS.get(key, ()))
        profiles[key] = AgentProfile(
            key=key,
            unigrams=frozenset(features["content_tokens"]) | aliases,
            bigrams=frozenset(features["bigrams"]),
            role_stem=role,
            signal_stems=signals,
            phrase_signals=tuple(PHRASE_SIGNALS.get(key, ())),
        )
    if not profiles:
        raise ValueError("router requires at least one agent")
    return profiles


def _idf_maps(profiles: Mapping[str, AgentProfile]) -> tuple[dict[str, float], dict[tuple[str, str], float]]:
    unigram_df = Counter(term for profile in profiles.values() for term in profile.unigrams)
    bigram_df = Counter(term for profile in profiles.values() for term in profile.bigrams)
    count = len(profiles)
    return (
        {term: idf(count, frequency) for term, frequency in unigram_df.items()},
        {term: idf(count, frequency) for term, frequency in bigram_df.items()},
    )


def score(query: str, profiles: Mapping[str, AgentProfile]) -> dict[str, float]:
    """Return the weighted lexical score for every agent profile."""
    features = tokenize(query)
    query_unigrams = set(features["content_tokens"])
    query_bigrams = set(features["bigrams"])
    unigram_idf, bigram_idf = _idf_maps(profiles)
    query_unigram_weights = {term: unigram_idf.get(term, 1.0) for term in query_unigrams}
    query_bigram_weights = {term: BIGRAM_WEIGHT * bigram_idf.get(term, 1.0) for term in query_bigrams}
    query_norm = max(1.0, math.sqrt(sum(weight * weight for weight in query_unigram_weights.values()) + sum(weight * weight for weight in query_bigram_weights.values())))
    lower_query = query.lower()
    scores: dict[str, float] = {}
    for key, profile in profiles.items():
        agent_unigram_weights = {term: unigram_idf.get(term, 1.0) for term in profile.unigrams}
        agent_bigram_weights = {term: BIGRAM_WEIGHT * bigram_idf.get(term, 1.0) for term in profile.bigrams}
        agent_norm = max(1.0, math.sqrt(sum(weight * weight for weight in agent_unigram_weights.values()) + sum(weight * weight for weight in agent_bigram_weights.values())))
        dot = sum(query_unigram_weights[term] ** 2 for term in query_unigrams & profile.unigrams)
        dot += sum(query_bigram_weights[term] ** 2 for term in query_bigrams & profile.bigrams)
        value = dot / (query_norm * agent_norm)
        if profile.role_stem in query_unigrams:
            value += NAME_BONUS
        value += SIGNAL_BONUS * len(query_unigrams & profile.signal_stems)
        value += SIGNAL_BONUS * sum(phrase in lower_query for phrase in profile.phrase_signals)
        scores[key] = value
    return scores


def route(query: str, profiles: Mapping[str, AgentProfile]) -> str | None:
    """Choose a deterministic agent, applying coordinator and veto rules."""
    if not query.strip():
        return None
    lower_query = query.lower()
    coordinators = sorted(key for key in profiles if key.endswith("coordinator"))
    if coordinators and any(phrase in lower_query for phrase in COORDINATOR_PHRASES):
        return coordinators[0]
    scores = score(query, profiles)
    for key, phrases in VETO_PHRASES.items():
        if key in scores and any(phrase in lower_query for phrase in phrases):
            scores[key] = -1.0
    winner = max(sorted(scores), key=lambda key: scores[key])
    return winner if scores[winner] > 0.0 else None