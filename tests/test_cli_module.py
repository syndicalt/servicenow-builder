import os
import subprocess
import sys


def test_cli_module_execution_prints_version() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, "-m", "jedi_devproject.cli", "--version"],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert completed.returncode == 0
    assert "jedi-devproject-0" in completed.stdout
