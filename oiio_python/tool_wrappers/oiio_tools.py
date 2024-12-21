import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()


def _run_tool(tool_name: str) -> None:
    tool_path = HERE / "tools" / tool_name
    env = os.environ.copy()
    subprocess.run([str(tool_path)] + sys.argv[1:], check=True, env=env)


def iconvert() -> None:
    _run_tool("iconvert")


def idiff() -> None:
    _run_tool("idiff")


def igrep() -> None:
    _run_tool("igrep")


def iinfo() -> None:
    _run_tool("iinfo")


def maketx() -> None:
    _run_tool("maketx")


def oiiotool() -> None:
    _run_tool("oiiotool")
