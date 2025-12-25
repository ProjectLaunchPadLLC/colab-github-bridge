"""
tests/test_process.py

Unit tests for src/process.py using pytest.

These tests run the processing script in a temporary repository workspace,
create an input file, execute the script as a subprocess, and assert that
the expected output file is created with the correct transformed content.
"""

import subprocess
import sys
from pathlib import Path
import textwrap


def run_process_in_dir(work_dir: Path) -> subprocess.CompletedProcess:
    """
    Run the processing script as a module in the given working directory.
    Returns the CompletedProcess result.
    """
    # Use -m to run the package module so imports resolve correctly
    cmd = [sys.executable, "-m", "src.process"]
    return subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True)


def test_process_creates_output(tmp_path: Path):
    """
    Given a data/input.txt with sample lines, src/process.py should create
    data/output.txt containing the uppercased lines and a timestamp header.
    """
    # Arrange: create minimal repo layout expected by src/process.py
    repo_root = tmp_path
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    input_text = textwrap.dedent(
        """\
        hello world
        this is a test

        mixed Case Line
        """
    )
    (data_dir / "input.txt").write_text(input_text, encoding="utf-8")

    # Act: run the process script
    result = run_process_in_dir(repo_root)

    # Assert: script exited successfully
    assert result.returncode == 0, f"process.py failed: stdout={result.stdout} stderr={result.stderr}"

    output_file = data_dir / "output.txt"
    assert output_file.exists(), "Expected data/output.txt to be created"

    content = output_file.read_text(encoding="utf-8").splitlines()
    # First line should be a timestamp header
    assert content, "Output file is empty"
    assert content[0].startswith("# Generated at "), "Output header missing or malformed"

    # Remaining lines should be the uppercased, non-empty transformed lines
    transformed_lines = content[1:]
    # Remove any empty lines that might appear
    transformed_lines = [ln for ln in transformed_lines if ln.strip() != ""]
    expected = ["HELLO WORLD", "THIS IS A TEST", "MIXED CASE LINE"]
    assert transformed_lines == expected, f"Unexpected transformed content: {transformed_lines}"


def test_process_handles_no_input(tmp_path: Path):
    """
    When no input file exists, src/process.py should still create data/output.txt
    and write the sentinel 'NO_INPUT' after the timestamp header.
    """
    repo_root = tmp_path
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Ensure no input file
    input_file = data_dir / "input.txt"
    if input_file.exists():
        input_file.unlink()

    result = run_process_in_dir(repo_root)
    assert result.returncode == 0, f"process.py failed: stdout={result.stdout} stderr={result.stderr}"

    output_file = data_dir / "output.txt"
    assert output_file.exists(), "Expected data/output.txt to be created when no input exists"

    content = output_file.read_text(encoding="utf-8").splitlines()
    assert content[0].startswith("# Generated at "), "Output header missing or malformed"
    # After header, the file should contain the sentinel NO_INPUT
    assert any("NO_INPUT" in line for line in content[1:]), "Expected 'NO_INPUT' in output when no input provided"
