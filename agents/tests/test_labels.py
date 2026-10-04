import pytest
from labels import prepare_transcript, restore_turns


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


def test_a_transcript_delivered_on_one_line_gets_its_turns_back():
    """ASI:One sometimes delivers a pasted transcript with every line break turned into a space."""
    lines = [
        "Interviewer: Jamal, what's your day job?",
        "Jamal: I work as a software developer.",
        "Interviewer: How do you handle dinner?",
        "Jamal: Last month we spent nine hundred dollars on delivery.",
        "Jamal: Please send me the beta link tonight.",
    ]
    transcript, note = prepare_transcript(" ".join(lines))
    assert transcript.split("\n") == [
        line.replace("Interviewer:", "Founder:").replace("Jamal:", "Customer:") for line in lines
    ]
    assert "Jamal as the customer" in note


def test_restoring_turns_leaves_other_text_alone():
    with_breaks = "Ana: Do you cook?\nBo: Yes. Note: only on weekends."
    assert restore_turns(with_breaks) == with_breaks
    # one line, but "Note:" is said once and is not a role word, so it is not a speaker
    one_line = "Ana: Do you cook? Bo: Yes. Note: only on weekends. Ana: Why? Bo: No time."
    assert restore_turns(one_line) == "Ana: Do you cook?\nBo: Yes. Note: only on weekends.\nAna: Why?\nBo: No time."
    assert restore_turns("One sentence. Another: with a colon.") == "One sentence. Another: with a colon."
