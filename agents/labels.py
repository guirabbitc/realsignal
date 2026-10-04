"""Map a transcript's speaker labels onto the two the analyzer reads: `Founder:` and `Customer:`.

Mirrors apps/web/components/upload/checks.ts, which does the same for the upload form. Only the
labels are rewritten; everything after each colon is kept byte for byte, so quotes stay verbatim.
"""
import re

# "Name:" or "First Last:" at the start of a line, up to 3 words, followed by a space or the line end
# (so "http://" and "10:30" are not speakers).
LABEL_LINE = re.compile(r"^([ \t]*)([A-Za-z][\w.'’&-]*(?: [\w.'’&-]+){0,2}):(?=\s|$)")
STANDARD = {"founder", "customer"}
INTERVIEWER = {"interviewer", "you", "me", "i", "q", "host"}
INTERVIEWEE = {"customer", "interviewee", "client", "user", "a", "guest", "prospect"}


def detect_speakers(transcript: str) -> list[str]:
    """Speaker labels as first written, in order of appearance."""
    found: dict[str, str] = {}
    for line in transcript.splitlines():
        match = LABEL_LINE.match(line)
        if match:
            found.setdefault(match.group(2).lower(), match.group(2))
    return list(found.values())


def guess_roles(speakers: list[str]) -> dict[str, str]:
    """`Founder:` is the interviewer unless another label already is. Unknown names: the first to speak
    is the interviewer."""
    keys = [s.lower() for s in speakers]
    has_interviewer_word = any(k in INTERVIEWER for k in keys)
    roles: dict[str, str] = {}
    for key in keys:
        if key in INTERVIEWEE:
            roles[key] = "customer"
        elif key in INTERVIEWER:
            roles[key] = "founder"
        elif key == "founder":
            roles[key] = "customer" if has_interviewer_word else "founder"
    founder_taken = "founder" in roles.values()
    for key in keys:
        if key not in roles:
            roles[key] = "customer" if founder_taken else "founder"
            founder_taken = True
    return roles


def relabel(transcript: str, roles: dict[str, str]) -> str:
    def swap(match: re.Match) -> str:
        role = roles.get(match.group(2).lower())
        return f"{match.group(1)}{role.capitalize()}:" if role else match.group(0)

    return "\n".join(LABEL_LINE.sub(swap, line) for line in transcript.split("\n"))


def prepare_transcript(text: str) -> tuple[str, str]:
    """Return (transcript labelled Founder:/Customer:, a note on how the speakers were mapped)."""
    speakers = detect_speakers(text)
    if not speakers:
        raise ValueError(
            "I could not tell who is speaking. Start every turn with the speaker's name and a colon, "
            "for example `Founder: ...` and `Customer: ...`."
        )
    roles = guess_roles(speakers)
    if "customer" not in roles.values():
        raise ValueError("I only found one speaker. I need both sides: your questions and the customer's answers.")
    if all(s.lower() in STANDARD for s in speakers):
        return text, ""
    founders = [s for s in speakers if roles[s.lower()] == "founder"]
    customers = [s for s in speakers if roles[s.lower()] == "customer"]
    note = f"I read {', '.join(founders)} as you (the interviewer) and {', '.join(customers)} as the customer."
    return relabel(text, roles), note
