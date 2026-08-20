import math

from dh_skills.router import (
    BIGRAM_WEIGHT,
    NAME_BONUS,
    ROUTE_SCORE_THRESHOLD,
    SIGNAL_BONUS,
    AgentProfile,
    build_profiles,
    idf,
    route,
    score,
)


def test_idf_uses_smoothed_formula():
    assert idf(4, 1) == math.log(5 / 2) + 1


def test_profiles_include_role_stem_aliases_and_bigrams():
    profiles = build_profiles({"dh-planning": "Break work into an implementation plan."})
    profile = profiles["dh-planning"]

    assert profile.role_stem == "plann"
    assert "decompos" in profile.unigrams
    assert ("imple", "plan") in profile.bigrams


def test_score_uses_cosine_and_name_bonus():
    profiles = {
        "dh-design": AgentProfile(
            key="dh-design",
            unigrams=frozenset({"api"}),
            bigrams=frozenset(),
            role_stem="design",
            signal_stems=frozenset(),
            phrase_signals=(),
        ),
    }

    scores = score("design api", profiles)

    assert scores["dh-design"] > NAME_BONUS
    assert scores["dh-design"] <= 1.0 + NAME_BONUS
    assert BIGRAM_WEIGHT == 2.2


def test_signal_and_phrase_bonuses_are_added():
    profiles = {
        "dh-release": AgentProfile(
            key="dh-release",
            unigrams=frozenset({"deploy"}),
            bigrams=frozenset(),
            role_stem="releas",
            signal_stems=frozenset({"deploy"}),
            phrase_signals=("ship it",),
        ),
    }

    scores = score("deploy and ship it", profiles)

    assert scores["dh-release"] >= SIGNAL_BONUS * 2


def test_route_tie_breaks_by_ascending_agent_name():
    profiles = {
        "dh-zeta": AgentProfile("dh-zeta", frozenset({"api"}), frozenset(), "zeta", frozenset(), ()),
        "dh-alpha": AgentProfile("dh-alpha", frozenset({"api"}), frozenset(), "alpha", frozenset(), ()),
    }

    assert route("api", profiles) == "dh-alpha"


def test_route_coordinator_override_and_veto():
    profiles = build_profiles({
        "dh-coordinator": "Coordinates all agents end-to-end.",
        "dh-kb": "Maintains the knowledge base index.",
    })

    assert route("orchestrate the agents", profiles) == "dh-coordinator"
    assert route("ask the knowledge base", profiles) != "dh-kb"


def test_empty_query_returns_none_and_threshold_is_documented():
    profiles = build_profiles({"dh-design": "Design APIs."})

    assert route("", profiles) is None
    assert ROUTE_SCORE_THRESHOLD == 0.95
