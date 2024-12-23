# pylint: disable=W0718
"""
This module provides utilities for managing and updating library references and RPATHs
on macOS. It includes functions to check and modify RPATH entries, update library
references, and ensure proper relinking for binaries and dynamic libraries.

The script is particularly useful for projects that involve bundling shared libraries
and need precise control over their paths and dependencies.
"""

import subprocess
from pathlib import Path

project = Path(__file__).parent.resolve()


def check_and_add_rpath(binary_path, rpath):
    """
    Checks if an LC_RPATH entry exists in the given binary and adds it if missing.

    Args:
        binary_path (Path or str): The path to the binary or shared library.
        rpath (str): The RPATH to add.

    Raises:
        subprocess.CalledProcessError: If an error occurs while executing `otool` or `install_name_tool`.
    """
    try:
        result = subprocess.run(
            ["otool", "-l", str(binary_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        if rpath in result.stdout:
            print(f"RPATH '{rpath}' already exists in {binary_path}")
        else:
            subprocess.run(
                ["install_name_tool", "-add_rpath", rpath, str(binary_path)], check=True
            )
            print(f"Added RPATH '{rpath}' to {binary_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking or adding RPATH: {e}")


def update_rpath_references(libs_dir, target_names):
    """
    Updates `@rpath` references in dynamic libraries to use `@loader_path`.

    Args:
        libs_dir (Path or str): Directory containing the dynamic libraries to process.
        target_names (list of str): List of target library names to update.

    Raises:
        subprocess.CalledProcessError: If an error occurs while executing `otool` or `install_name_tool`.
    """
    libs_dir = Path(libs_dir)
    for dylib in libs_dir.glob("*.dylib"):
        try:
            result = subprocess.run(
                ["otool", "-L", str(dylib)], capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                for target_name in target_names:
                    if target_name in line:
                        old_path = line.split()[0]
                        new_path = f"@loader_path/{Path(old_path).name}"
                        subprocess.run(
                            [
                                "install_name_tool",
                                "-change",
                                old_path,
                                new_path,
                                str(dylib),
                            ],
                            check=True,
                        )
                        print(f"Updated {old_path} -> {new_path} in {dylib}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {dylib}: {e}")


def ensure_rpaths(binaries, rpath):
    """
    Ensures that the specified LC_RPATH exists in all provided binaries.

    Args:
        binaries (list of Path or str): List of binaries or shared libraries.
        rpath (str): The RPATH to ensure.

    Raises:
        subprocess.CalledProcessError: If an error occurs while adding the RPATH.
    """
    for binary in binaries:
        check_and_add_rpath(binary, rpath)


def relink_and_delocate():
    """
    Relinks binaries and shared libraries by updating RPATH references and ensuring
    proper LC_RPATH entries. This is the main function of the script, orchestrating
    the process for the project.

    Steps performed:
    1. Verify required files exist in the expected locations.
    2. Update `@rpath` references in dynamic libraries to use `@loader_path`.
    3. Ensure LC_RPATH entries for all binaries and libraries.

    Raises:
        FileNotFoundError: If required files are missing.
        subprocess.CalledProcessError: If an error occurs during subprocess execution.
        Exception: For any other unexpected errors.
    """
    try:
        base_path = project / "oiio_python"
        libs_dir = base_path / "libs"
        libs_dir.mkdir(parents=True, exist_ok=True)

        # Define paths for libraries and modules
        oiio_so = next((base_path / "OpenImageIO").glob("*.so"))
        ocio_so = next((base_path / "PyOpenColorIO").glob("*.so"))

        lib_oiio = max(
            (f for f in libs_dir.glob("libOpenImageIO.*.dylib") if not f.is_symlink()),
            key=lambda f: f.stat().st_size,
        )
        lib_ocio = max(
            (f for f in libs_dir.glob("libOpenColorIO.*.dylib") if not f.is_symlink()),
            key=lambda f: f.stat().st_size,
        )
        lib_tbb = libs_dir / "libtbb.12.10.dylib"

        # Check required files exist
        required_files = [oiio_so, ocio_so, lib_oiio, lib_ocio, lib_tbb]
        for path in required_files:
            if not path.is_file():
                raise FileNotFoundError(f"Required file '{path}' does not exist.")

        # Update RPATH references
        update_rpath_references(
            libs_dir,
            [
                "libtbb",
                "libtbbmalloc",
                "libtbbmalloc_proxy",
                "libOpenImageIO",
                "libOpenColorIO",
                "libOpenImageIO_Util",
            ],
        )

        # Ensure LC_RPATH for all binaries
        ensure_rpaths([oiio_so, ocio_so, lib_oiio, lib_ocio, lib_tbb], "@loader_path")
        ensure_rpaths([oiio_so, ocio_so], "@loader_path/../../.dylibs")

        print("Relinking and RPATH configuration completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error during relinking or RPATH configuration: {e}")
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    relink_and_delocate()
