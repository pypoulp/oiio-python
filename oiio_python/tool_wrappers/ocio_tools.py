import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()


def _run_tool(tool_name: str) -> None:
    tool_path = HERE / "tools" / tool_name
    ocio_bin_path = HERE
    env = os.environ.copy()
    env["PATH"] = os.environ["PATH"] + os.pathsep + str(ocio_bin_path)
    subprocess.run([str(tool_path)] + sys.argv[1:], check=True, env=env)


def ocioarchive() -> None:
    _run_tool("ocioarchive")
