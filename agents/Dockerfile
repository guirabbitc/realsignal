# The Fetch.ai agent team as one Railway service. Built from the repo root because agents/pyproject.toml
# depends on ../services/analyzer by path (the agents run the analyzer pipeline in-process).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

WORKDIR /app
COPY services/analyzer services/analyzer
COPY agents agents
RUN uv sync --project agents --frozen --no-dev

# Front agent on 8001 (the only port the web app calls), specialists on 8002-8004.
EXPOSE 8001
CMD ["uv", "run", "--project", "agents", "--no-sync", "python", "agents/run_team.py"]
