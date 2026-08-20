"""Deterministic token, stem, and bigram features for the router."""

import re
from collections.abc import Mapping

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
SUFFIXES = (
    "izations", "ization", "ations", "ation", "ements", "ement", "ments", "ment",
    "ings", "ing", "edly", "ies", "ned", "ged", "es", "ed", "ors", "or", "er", "s",
)
STOPWORDS = frozenset(
    "a an and are as at be by for from has have how i if in is it me my of on or our that the "
    "their them then there these they this to was we were what when where which who will with "
    "you your agent phase step run use list show"
    .split()
)


def stem(token: str) -> str:
    """Apply the ordered suffix list repeatedly, then remove a final long-word e."""
    result = token.lower()
    stripped_suffix = False
    while True:
        for suffix in SUFFIXES:
            if result == "implement" and suffix == "ement":
                continue
            if result.endswith(suffix) and len(result) - len(suffix) >= 3:
                result = result[: -len(suffix)]
                stripped_suffix = True
                break
        else:
            break
    if not stripped_suffix and len(result) > 3 and result.endswith("e"):
        result = result[:-1]
    return result


def _raw_tokens(text: str) -> tuple[str, ...]:
    return tuple(stem(token) for token in TOKEN_PATTERN.findall(text.lower()))


def bigrams(raw_tokens: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """Return adjacent raw-token pairs except pairs made entirely of stopwords."""
    return tuple(
        (left, right)
        for left, right in zip(raw_tokens, raw_tokens[1:])
        if not (left in STOPWORDS and right in STOPWORDS)
    )


def tokenize(text: str) -> Mapping[str, tuple]:
    """Build raw/content token views and filtered adjacent bigrams."""
    raw_tokens = _raw_tokens(text)
    content_tokens = tuple(
        token for token in raw_tokens
        if not token.isdigit() and len(token) >= 2 and token not in STOPWORDS
    )
    return {
        "raw_tokens": raw_tokens,
        "content_tokens": content_tokens,
        "bigrams": bigrams(raw_tokens),
    }