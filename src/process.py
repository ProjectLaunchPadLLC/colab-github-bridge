"""
src/process.py

Minimal example processing script used by the Colab notebook.
This script demonstrates a safe, deterministic operation that the notebook
can run before committing results back to the repository.

Behavior:
- Reads an optional input file `data/input.txt` (if present).
- Produces or updates `data/output.txt` with a timestamp and a simple
  transformation of the input (uppercased lines).
- Exits with code 0 on success.
"""

from pathlib import Path
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INPUT_FILE = DATA_DIR / "input.txt"
OUTPUT_FILE = DATA_DIR / "output.txt"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_input() -> list:
    if not INPUT_FILE.exists():
        return []
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def transform(lines: list) -> list:
    # Simple deterministic transformation: uppercase each non-empty line
    return [line.upper() for line in lines if line.strip() != ""]


def write_output(transformed: list) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write(f"# Generated at {now}\n")
        if transformed:
            f.write("\n".join(transformed) + "\n")
        else:
            f.write("NO_INPUT\n")


def main() -> int:
    try:
        ensure_data_dir()
        lines = read_input()
        transformed = transform(lines)
        write_output(transformed)
        print(f"Wrote {OUTPUT_FILE} (lines: {len(transformed)})")
        return 0
    except Exception as e:
        print(f"Error in process.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
