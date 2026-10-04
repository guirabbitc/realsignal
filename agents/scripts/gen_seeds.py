"""Fill .env with one fixed seed per agent and the address derived from it.

Existing seeds are kept, so running this twice never changes an address.
"""
import secrets
import shutil
from pathlib import Path

from uagents_core.identity import Identity

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / ".env"
AGENTS = ["FRONT", "INTAKE", "ANALYST", "MARKET", "STRATEGIST"]


def main() -> None:
    if not ENV.exists():
        shutil.copy(ROOT / ".env.example", ENV)

    lines = ENV.read_text().splitlines()
    values = dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))

    for name in AGENTS:
        seed = values.get(f"{name}_AGENT_SEED") or f"realsignal-{name.lower()}-{secrets.token_hex(16)}"
        values[f"{name}_AGENT_SEED"] = seed
        values[f"{name}_AGENT_ADDRESS"] = Identity.from_seed(seed, 0).address

    out = []
    for line in lines:
        if "=" in line and not line.startswith("#"):
            key = line.split("=", 1)[0]
            line = f"{key}={values[key]}"
        out.append(line)
    ENV.write_text("\n".join(out) + "\n")

    for name in AGENTS:
        print(f"{name:<11}{values[f'{name}_AGENT_ADDRESS']}")


if __name__ == "__main__":
    main()
