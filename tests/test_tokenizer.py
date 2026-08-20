from dh_skills.tokenizer import STOPWORDS, bigrams, stem, tokenize


def test_token_extraction_is_lowercase_alphanumeric_and_deterministic():
    assert tokenize("Design API v2.0 -- REVIEW!") == {
        "raw_tokens": ("design", "api", "v2", "0", "review"),
        "content_tokens": ("design", "api", "v2", "review"),
        "bigrams": (("design", "api"), ("api", "v2"), ("v2", "0"), ("0", "review")),
    }


def test_ordered_suffix_stemmer_matches_spec_examples():
    assert stem("implementation") == "imple"
    assert stem("tests") == "test"
    assert stem("testing") == "test"
    assert stem("code") == "cod"
    assert stem("coding") == "cod"


def test_stemmer_repeats_first_matching_suffix_and_preserves_short_words():
    assert stem("organizations") == "organ"
    assert stem("is") == "is"
    assert stem("use") == "use"


def test_content_tokens_drop_stopwords_digits_and_short_results():
    assert "agent" in STOPWORDS
    result = tokenize("The agent will run phase 12 and use a tool")

    assert result["raw_tokens"] == ("the", "agent", "will", "run", "phas", "12", "and", "use", "a", "tool")
    assert result["content_tokens"] == ("phas", "tool")


def test_bigrams_keep_function_words_but_drop_stopword_only_pairs():
    result = tokenize("the and agent design")

    assert result["bigrams"] == (("agent", "design"),)
