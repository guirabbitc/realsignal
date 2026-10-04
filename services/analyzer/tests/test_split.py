import pytest

from app.errors import TranscriptTooLong, UnlabelledTranscript
from app.pipeline.split import split_transcript

EXAMPLE = (
    "Founder: How do you handle reservations today?\n"
    "Customer: Honestly it's a mess. I pay someone $300 a month to do it by hand."
)


def test_positions_count_all_sentences_in_order():
    r = split_transcript(EXAMPLE, 80000)
    assert [(c.position, c.text) for c in r.customer_sentences] == [
        (2, "Honestly it's a mess."),
        (3, "I pay someone $300 a month to do it by hand."),
    ]


def test_founder_question_is_previous_founder_turn():
    r = split_transcript(EXAMPLE, 80000)
    assert r.customer_sentences[1].founder_question == "How do you handle reservations today?"


def test_every_quote_is_a_verbatim_substring():
    text = "Founder: Hi.\nCustomer:   We lost  900 dollars.\nIt happens   every week!\nFounder: Ok."
    for s in split_transcript(text, 80000).sentences:
        assert s.text in text


def test_unlabelled_lines_continue_the_previous_turn():
    r = split_transcript("Customer: First line.\nSecond line here.\nFounder: Q?", 80000)
    assert r.turns[0].text == "First line.\nSecond line here."


def test_labels_are_case_insensitive():
    r = split_transcript("FOUNDER: q?\ncustomer: a.", 80000)
    assert [t.speaker for t in r.turns] == ["founder", "customer"]


def test_talk_ratio_is_founder_words_over_all_words():
    r = split_transcript("Founder: one two three\nCustomer: four", 80000)
    assert r.founder_talk_ratio == pytest.approx(3 / 4)


def test_no_labels_is_rejected():
    with pytest.raises(UnlabelledTranscript):
        split_transcript("We talked about reservations.", 80000)


def test_too_long_is_rejected():
    with pytest.raises(TranscriptTooLong):
        split_transcript("Customer: " + "a" * 100, 50)
