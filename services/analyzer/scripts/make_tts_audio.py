"""Stand-in fixture audio until the team records real voices: macOS text-to-speech reads a text fixture with
two voices (founder and customer). Manual run only, macOS only, never in CI. Synthetic voices are easier to
tell apart than real ones, so a pass here is weaker evidence than a pass on a human recording.

    uv run python scripts/make_tts_audio.py real_pain polite --out /tmp/audio

Writes <name>.wav (16-bit mono, for Chromium's fake microphone) and <name>.m4a (AAC, for upload).
"""

import argparse
import re
import subprocess
import tempfile
import wave
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"
VOICES = {"founder": "Daniel", "customer": "Samantha"}
RATE = 22050
GAP_SECONDS = 0.6
_LABEL = re.compile(r"^\s*(founder|customer)\s*:\s*", re.IGNORECASE)


def turns(transcript: str) -> list[tuple[str, str]]:
    """(role, text) per turn, read the way split.py reads them: unlabelled lines continue the previous turn."""
    out: list[tuple[str, str]] = []
    for line in transcript.splitlines():
        match = _LABEL.match(line)
        if match:
            out.append((match.group(1).lower(), line[match.end():].strip()))
        elif out and line.strip():
            out[-1] = (out[-1][0], f"{out[-1][1]} {line.strip()}")
    return out


def speak(text: str, voice: str, path: Path) -> None:
    subprocess.run(["say", "-v", voice, "-o", str(path), "--file-format=WAVE", f"--data-format=LEI16@{RATE}", text],
                   check=True)


def build(name: str, out_dir: Path) -> None:
    silence = b"\x00\x00" * int(RATE * GAP_SECONDS)
    wav_path, m4a_path = out_dir / f"{name}.wav", out_dir / f"{name}.m4a"
    with tempfile.TemporaryDirectory() as tmp, wave.open(str(wav_path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        for index, (role, text) in enumerate(turns((FIXTURES / f"{name}.txt").read_text())):
            part = Path(tmp) / f"{index}.wav"
            speak(text, VOICES[role], part)
            with wave.open(str(part), "rb") as spoken:
                out.writeframes(spoken.readframes(spoken.getnframes()))
            out.writeframes(silence)
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", str(wav_path), str(m4a_path)], check=True)
    print(f"{name}: {wav_path} ({wav_path.stat().st_size // 1024} KB), {m4a_path} ({m4a_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fixtures", nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for fixture in args.fixtures:
        build(fixture, args.out)
