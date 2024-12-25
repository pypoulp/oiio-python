import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()


def _run_tool(tool_name: str) -> None:
    tool_path = HERE / "tools" / tool_name
    env = os.environ.copy()
    try:
        subprocess.run([str(tool_path)] + sys.argv[1:], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error: {tool_name} failed with return code {e.returncode}.")


def ocioarchive() -> None:
    _run_tool("ocioarchive")


def ociobakelut() -> None:
    _run_tool("ociobakelut")


def ociocheck() -> None:
    _run_tool("ociocheck")


def ociochecklut() -> None:
    _run_tool("ociochecklut")


def ocioconvert() -> None:
    _run_tool("ocioconvert")


def ociolutimage() -> None:
    _run_tool("ociolutimage")


def ociomakeclf() -> None:
    _run_tool("ociomakeclf")


def ocioperf() -> None:
    _run_tool("ocioperf")


def ociowrite() -> None:
    _run_tool("ociowrite")
