"""Utility functions for building and managing Conan packages."""

import os
import time
import platform
import shutil
import subprocess
from pathlib import Path

project = Path(__file__).parent.resolve()


def conan_profile_ensure(cpp_std: str = "14") -> None:
    """Ensure Conan profile exists and set the C++ standard."""
    # Check if the default profile exists by listing profiles
    list_profiles_output = subprocess.run(
        ["conan", "profile", "list", "--path"],
        capture_output=True,
        text=True,
        check=True,
    )
    profiles = list_profiles_output.stdout.strip().splitlines()
    print(profiles)
    if "default" not in profiles:

        system = platform.system()
        machine = platform.machine()

        print("Default Conan profile not found. Running 'conan profile detect'.")

        if system == "Darwin" and machine == "arm64":
            print("Running Conan profile detection for macOS ARM64.")
            detect_command = ["arch", "-arm64", "conan", "profile", "detect", "--force"]
        else:
            print(f"Running Conan profile detection for {system} on {machine}.")
            detect_command = ["conan", "profile", "detect", "--force"]

        # Run 'conan profile detect'
        detect_output = subprocess.run(
            detect_command, capture_output=True, text=True, check=True
        )
        if detect_output.returncode == 0:
            print("Conan Profile detected successfully.")
        else:
            print("Error detecting Conan profile:", detect_output.stderr)
    else:
        print("Default Conan profile already exists.")

    home_folder = Path(os.path.expanduser("~"))
    profile_path = home_folder / ".conan2" / "profiles" / "default"

    # Read the profile file
    profile_content = profile_path.read_text(encoding="utf8")
    lines = profile_content.splitlines()

    new_lines = []
    for line in lines:
        if line.startswith("compiler.cppstd"):
            new_lines.append(f"compiler.cppstd={cpp_std}")
        else:
            new_lines.append(line)

    # Write the updated profile file
    new_profile = profile_path.with_name("default_oiio_build")
    new_profile.write_text("\n".join(new_lines), encoding="utf8")
    profile_content = new_profile.read_text(encoding="utf8")


def build_cleanup(recipe_dir: Path) -> None:
    """Clean build artifacts from a Conan recipe directory."""
    retry = 0
    while retry < 4:
        try:
            build_dir = recipe_dir / "build"
            if build_dir.exists():
                shutil.rmtree(build_dir)

            src_dir = recipe_dir / "src"
            if src_dir.exists():
                shutil.rmtree(src_dir)

            cmake_presets = recipe_dir / "CMakeUserPresets.json"

            if cmake_presets.exists():
                cmake_presets.unlink()

            test_package_dir = recipe_dir / "test_package"
            if test_package_dir.exists():
                test_build = test_package_dir / "build"

                if test_build.exists():
                    shutil.rmtree(test_build)

                test_cmake_presets = test_package_dir / "CMakeUserPresets.json"
                if test_cmake_presets.exists():
                    test_cmake_presets.unlink()
        except PermissionError:
            time.sleep(1)
            retry += 1


def conan_install_package(
    root_folder: Path,
    version: str,
    profile: str,
    source: bool = True,
    export: bool = True,
    to_build=None,
) -> None:
    """Build and install a Conan package with specified version and profile."""

    source_cmd = [
        "conan",
        "source",
        root_folder.as_posix(),
        "--version",
        version,
        # "-vwarning",
    ]
    if to_build is None:
        to_build = ["missing"]
    build_arg_list = []
    # Without boost, build=missing seems to work on linux!
    for b in to_build:
        build_arg = f"--build={b}"
        build_arg_list.append(build_arg)

    install_cmd = [
        "conan",
        "install",
        root_folder.as_posix(),
        "--version",
        version,
        "--profile",
        profile,
    ]

    install_cmd += build_arg_list

    build_cmd = [
        "conan",
        "build",
        root_folder.as_posix(),
        "--version",
        version,
        "--profile",
        profile,
    ]
    export_cmd = [
        "conan",
        "export-pkg",
        root_folder.as_posix(),
        "--version",
        version,
        "--profile",
        profile,
        # "-vwarning",
    ]
    if source:
        subprocess.run(source_cmd, check=True)
    subprocess.run(install_cmd, check=True)
    subprocess.run(build_cmd, check=True)
    if export:
        subprocess.run(export_cmd, check=True)
