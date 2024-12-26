"""
This script automates the process of cleaning a Python repository, building a source distribution (sdist),
and publishing the package to PyPI or Test PyPI. It provides a simple CLI interface to toggle between
release and test modes.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent.resolve()


def run_command(command):
    """Run a shell command and handle errors gracefully."""
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running command: {e.cmd}")
        sys.exit(1)


def cleanup():
    """
    Clean the repository by removing build artifacts and temporary files.

    Deletes directories like `build`, `dist`, and other generated folders/files
    during the build process to ensure a clean state.
    """
    package_dir = here / "oiio_python"

    to_remove = [
        here / "build",
        here / "dist",
        package_dir / "oiio_python.egg-info",
        package_dir / "oiio_static_python.egg-info",
        package_dir / "OpenImageIO",
        package_dir / "PyOpenColorIO",
        package_dir / "libs",
    ]

    for folder in to_remove:
        if folder.exists():
            if folder.is_dir():
                shutil.rmtree(folder)
            else:
                folder.unlink()


def build_sdist():
    """
    Build the source distribution (sdist) for the Python package.

    This creates a tarball of the source code in the `dist` directory, which can be
    uploaded to PyPI.
    """
    print("Building the source distribution...")
    run_command("python setup.py sdist")


def publish_to_pypi(repository_url, static):
    """
    Publish the package to the specified PyPI repository.

    Lists all files in the `dist` directory to be uploaded and asks for user confirmation
    before proceeding with the upload.
    """
    print(f"Publishing to {repository_url}...")

    dist_files = list((here / "dist").glob("*"))

    if static:
        wheelhouse = "wheelhouse_static"
    else:
        wheelhouse = "wheelhouse"

    if not (here / wheelhouse).exists():
        print(f"Wheelhouse directory not found: {wheelhouse}")
        sys.exit(1)

    wheel_files = list((here / wheelhouse).glob("*.whl"))

    print("=" * 80)
    print(
        f"Publishing {len(dist_files) + len(wheel_files)} files to PyPI: {repository_url}"
    )
    for file in dist_files:
        print(file)
    for file in wheel_files:
        print(file)
    print("=" * 80)

    confirm = (
        input("Are you sure you want to publish to PyPI? (yes/no): ").strip().lower()
    )
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)

    dist_empty = len(dist_files) == 0
    wheel_empty = len(wheel_files) == 0
    if dist_empty and wheel_empty:
        print("No files to publish.")
        sys.exit(0)

    if not dist_empty:
        run_command(f"twine upload --verbose --repository {repository_url} dist/*")
    if not wheel_empty:
        run_command(f"twine upload --verbose --repository {repository_url} {wheelhouse}/*")


def main():
    """
    Main entry point for the script.

    Parses command-line arguments to determine the mode (release or test) and
    performs cleanup, builds the source distribution, and publishes it to PyPI.
    """
    parser = argparse.ArgumentParser(description="Publish Python packages to PyPI.")
    parser.add_argument(
        "--release", action="store_true", help="Publish to PyPI instead of Test PyPI."
    )
    parser.add_argument(
        "--static", action="store_true", help="Publish oiio-static-python."
    )
    parser.add_argument(
        "--nosdist", action="store_true", help="Skip building source distribution."
    )
    args = parser.parse_args()

    if args.static:
        os.environ["OIIO_STATIC"] = "1"
    else:
        os.environ["OIIO_STATIC"] = "0"

    if args.release:
        confirm = (
            input("Using RELEASE mode, do you want to continue? (yes/no): ")
            .strip()
            .lower()
        )
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)
        repository_url = "pypi"
    else:
        repository_url = "testpypi"

    # Clean, build, and publish
    cleanup()
    if not args.nosdist:
        build_sdist()
    publish_to_pypi(repository_url, args.static)


if __name__ == "__main__":
    main()
