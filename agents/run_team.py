"""Start the agents in one terminal. Ctrl+C stops them all.

    uv run --project agents python agents/run_team.py                  # all four
    uv run --project agents python agents/run_team.py intake analyst   # only these

Each agent is its own process with its own address, port and mailbox.
"""
import signal
import subprocess
import sys
import time
from pathlib import Path

AGENTS = ["front", "intake", "analyst", "strategist"]
HERE = Path(__file__).resolve().parent


def main() -> None:
    names = sys.argv[1:] or AGENTS
    unknown = [n for n in names if n not in AGENTS]
    if unknown:
        raise SystemExit(f"Unknown agent(s): {', '.join(unknown)}. Choose from: {', '.join(AGENTS)}")

    processes = {
        name: subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / name / "agent.py")])
        for name in names
    }
    # Children get Ctrl+C from the terminal too; ignore it here so we can wait for them to finish.
    signal.signal(signal.SIGINT, lambda *_: None)

    def stop_all(*_):
        for process in processes.values():
            process.terminate()

    signal.signal(signal.SIGTERM, stop_all)
    try:
        while processes:
            for name, process in list(processes.items()):
                if process.poll() is not None:
                    print(f"[run_team] {name} stopped (exit code {process.returncode})", flush=True)
                    del processes[name]
            time.sleep(0.5)
    finally:
        for process in processes.values():
            process.terminate()


if __name__ == "__main__":
    main()
