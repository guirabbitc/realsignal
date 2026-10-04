import pytest
from labels import prepare_transcript


def test_standard_labels_are_left_alone():
    text = "Founder: How do you plan?\nCustomer: I use a list."
    assert prepare_transcript(text) == (text, "")


def test_names_are_mapped_and_only_the_labels_change():
    text = "Interviewer: How do you plan?\nPriya: I paid 60 dollars: twice.\nand more\nInterviewer: Ok."
    transcript, note = prepare_transcript(text)
    assert transcript == "Founder: How do you plan?\nCustomer: I paid 60 dollars: twice.\nand more\nFounder: Ok."
    assert "Interviewer as you" in note and "Priya as the customer" in note


def test_unknown_names_take_the_first_speaker_as_the_interviewer():
    transcript, _ = prepare_transcript("Ana: Do you cook?\nBo: Yes I do.")
    assert transcript == "Founder: Do you cook?\nCustomer: Yes I do."


@pytest.mark.parametrize("text", ["just a paragraph with no speakers at all", "Ana: only one person speaks here"])
def test_unusable_transcripts_are_refused_with_a_clear_message(text):
    with pytest.raises(ValueError):
        prepare_transcript(text)
