"""Fill agents/.env with one fixed seed per agent and print each agent's address.

Existing seeds are kept, so running this twice never changes an address.
"""
import secrets
from pathlib import Path

from uagents_core.identity import Identity

ENV = Path(__file__).resolve().parents[1] / ".env"
ROLES = ["FRONT", "INTAKE", "ANALYST", "STRATEGIST"]


def main() -> None:
    lines = ENV.read_text().splitlines() if ENV.exists() else []
    values = dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))
    for role in ROLES:
        key = f"AGENT_SEED_{role}"
        if not values.get(key):
            values[key] = f"validate-{role.lower()}-{secrets.token_hex(16)}"
            lines = [line for line in lines if not line.startswith(f"{key}=")] + [f"{key}={values[key]}"]
    ENV.write_text("\n".join(lines) + "\n")
    for role in ROLES:
        print(f"{role:<11}{Identity.from_seed(values[f'AGENT_SEED_{role}'], 0).address}")


if __name__ == "__main__":
    main()
