from app.pipeline.verify import is_verifiable, unverifiable_quotes

T = "Customer: I pay someone $300 a month to do it by hand. It's a mess."


def test_verbatim_quote_passes():
    assert is_verifiable('They said "I pay someone $300 a month" [#3].', T)


def test_paraphrase_fails():
    assert unverifiable_quotes('They said "I pay a person $300 monthly".', T) == ["I pay a person $300 monthly"]


def test_curly_quotes_and_whitespace_are_normalised():
    assert is_verifiable("“I  pay someone\n$300 a month”", T)
    assert is_verifiable("“It’s a mess.”", T)


def test_short_spans_are_ignored():
    assert is_verifiable('The "new angle" verdict.', T)


def test_text_without_quotes_passes():
    assert is_verifiable("They described a real cost [#3].", T)
