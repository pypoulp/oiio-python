import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.dist import Distribution

here = Path(__file__).parent.resolve()


def conan_profile_ensure() -> None:
    # Check if the default profile exists by listing profiles
    list_profiles_output = subprocess.run(
        ["conan", "profile", "list", "--path"], capture_output=True, text=True, check=True
    )
    profiles = list_profiles_output.stdout.strip().splitlines()
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
        detect_output = subprocess.run(detect_command, capture_output=True, text=True, check=True)
        if detect_output.returncode == 0:
            print("Conan Profile detected successfully.")
        else:
            print("Error detecting Conan profile:", detect_output.stderr)
    else:
        print("Default Conan profile already exists.")
    
    print("\n--- Conan Profile Details ---\n")
    profile_show_output = subprocess.run(
        ["conan", "profile", "show"], capture_output=True, text=True, check=True
    )
    print(profile_show_output.stdout)
    print("\n--- End of Profile Details ---\n")

def conan_install_package(
    root_folder: Path,
    version: str,
    profile: str,
    source: bool = True,
    export: bool = True,
    to_build=None,
) -> None:

    source_cmd = ["conan", "source", root_folder.as_posix(), "--version", version]
    if to_build is None:
        to_build = ["missing"]
    build_arg_list = []
    if platform.system() == "Linux":
        # Build everything on Linux to maximize compatibility on ManyLinux
        build_arg_list.append("--build=*")
    else:
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

    build_cmd = ["conan", "build", root_folder.as_posix(), "--version", version, "--profile", profile]
    export_cmd = ["conan", "export-pkg", root_folder.as_posix(), "--version", version]
    if source:
        subprocess.run(source_cmd, check=True)
    subprocess.run(install_cmd, check=True)
    subprocess.run(build_cmd, check=True)
    if export:
        subprocess.run(export_cmd, check=True)


def is_executable(file_path: Path):
    """Check if the given file is executable."""
    return file_path.is_file() and os.access(file_path, os.X_OK)


def build_packages(static_build: bool = False) -> None:
    ocio_pkg_dir = here / "oiio_python" / "PyOpenColorIO"
    oiio_pkg_dir = here / "oiio_python" / "OpenImageIO"

    for package_dir in [ocio_pkg_dir, oiio_pkg_dir]:
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()

    libs_dir = here / "oiio_python" / "libs"
    if libs_dir.exists():
        shutil.rmtree(libs_dir)
    libs_dir.mkdir()

    os.environ["OCIO_PKG_DIR"] = ocio_pkg_dir.as_posix()
    os.environ["OIIO_PKG_DIR"] = oiio_pkg_dir.as_posix()
    os.environ["OIIO_LIBS_DIR"] = libs_dir.as_posix()

    subprocess.run(["conan", "profile", "detect", "--force"], check=True)
    profile_name = "default"

    # LibRaw
    libraw_dep_dir = here / "oiio_python" / "recipes" / "dependencies" / "libraw"
    libraw_version = "0.21.2"

    conan_install_package(libraw_dep_dir, libraw_version, profile=profile_name)

    # OpenColorIO
    ocio_dep_dir = here / "oiio_python" / "recipes" / "opencolorio"
    ocio_version = "2.2.1"

    conan_install_package(ocio_dep_dir, ocio_version, profile=profile_name)

    # OpenImageIO
    oiio_dir = here / "oiio_python" / "recipes" / "openimageio"
    oiio_version = "2.5.12.0"

    conan_install_package(oiio_dir, oiio_version, profile=profile_name)

    # Copy loaders
    loaders_dir = here / "oiio_python" / "loaders"

    if (oiio_pkg_dir / "__init__.py").exists():
        os.remove(oiio_pkg_dir / "__init__.py")

    if (ocio_pkg_dir / "__init__.py").exists():
        os.remove(ocio_pkg_dir / "__init__.py")

    # Copy loaders
    if platform.system() == "Windows":
        shutil.copyfile(loaders_dir / "ocio_loader_win.py", ocio_pkg_dir / "__init__.py")
        shutil.copyfile(loaders_dir / "oiio_loader_win.py", oiio_pkg_dir / "__init__.py")
    else:
        shutil.copyfile(loaders_dir / "ocio_loader.py", ocio_pkg_dir / "loaders.py")
        shutil.copyfile(loaders_dir / "oiio_loader.py", oiio_pkg_dir / "loaders.py")

    if not static_build:
        # Copy tool wrappers
        wrappers_dir = here / "oiio_python" / "tool_wrappers"
        if platform.system() == "Windows":
            shutil.copyfile(wrappers_dir / "oiio_tools_win.py", oiio_pkg_dir / "_tool_wrapper.py")
            shutil.copyfile(wrappers_dir / "ocio_tools_win.py", ocio_pkg_dir / "_tool_wrapper.py")
        else:
            shutil.copyfile(wrappers_dir / "oiio_tools.py", oiio_pkg_dir / "_tool_wrapper.py")
            shutil.copyfile(wrappers_dir / "ocio_tools.py", ocio_pkg_dir / "_tool_wrapper.py")

    # Clean build dirs
    shutil.rmtree(oiio_dir / "build")
    shutil.rmtree(oiio_dir / "src")
    shutil.rmtree(ocio_dep_dir / "build")
    shutil.rmtree(ocio_dep_dir / "src")
    shutil.rmtree(libraw_dep_dir / "build")
    shutil.rmtree(libraw_dep_dir / "src")
    shutil.rmtree(ocio_dep_dir / "test_package" / "build")
    os.remove(ocio_dep_dir / "test_package" / "CMakeUserPresets.json")
    shutil.rmtree(oiio_dir / "test_package" / "build")
    os.remove(oiio_dir / "test_package" / "CMakeUserPresets.json")
    shutil.rmtree(libraw_dep_dir / "test_package" / "build")
    os.remove(libraw_dep_dir / "test_package" / "CMakeUserPresets.json")


if platform.system() == "Windows":
    lib_ext = ".dll"
    pylib_ext = ".pyd"
elif platform.system() == "Darwin":
    lib_ext = ".dylib"
    pylib_ext = ".so"
else:
    lib_ext = ".so"
    pylib_ext = ".so"


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


def debug_repair_library() -> None:
    """
    Print the contents of the REPAIR_LIBRARY directory and their architectures.
    """
    libs_dir = Path(os.getenv("OIIO_LIBS_DIR", "$PWD/oiio_python/libs"))
    print("$PWD", os.getenv("PWD"))
    print("$PROJECT_ROOT", os.getenv("PROJECT_ROOT"))
    print("$OIIO_LIBS_DIR", os.getenv("OIIO_LIBS_DIR"))

    print("\n" + "=" * 80)
    print("DEBUG: Inspecting libraries in REPAIR_LIBRARY:")
    if not libs_dir.exists():
        print(f"ERROR: REPAIR_LIBRARY path does not exist: {libs_dir}")
        print("=" * 80 + "\n")
        return

    for lib_path in libs_dir.glob("*"):
        print(f"Inspecting: {lib_path}")
        if lib_path.is_file():
            try:
                result = subprocess.run(
                    ["lipo", "-info", str(lib_path)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"  -> Architecture(s): {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"  -> ERROR inspecting {lib_path}: {e.stderr.strip()}")
        else:
            print(f"  -> Skipping non-file: {lib_path}")
    print("=" * 80 + "\n")


if __name__ == "__main__":

    static_build = os.getenv("OIIO_STATIC") == "1"

    print("=" * 80)
    if static_build:
        print("Building static libraries.")
    else:
        print("Building shared libraries.")
    print("=" * 80)

    if "bdist_wheel" in sys.argv:
        conan_profile_ensure()
        build_packages(static_build)

        if platform.system() == "Darwin":
            debug_repair_library()

        # Fix shared libraries on macos
        if not static_build and platform.system() == "Darwin":
            cmd = [sys.executable, (here / "macos_fix_shared_libs.py").as_posix()]
            subprocess.run(cmd, check=True)

        if static_build:
            # Cleanup tools directories if needed
            tool_dirs = [
                here / "oiio_python" / "OpenImageIO" / "tools",
                here / "oiio_python" / "PyOpenColorIO" / "tools",
            ]

            for tool_dir in tool_dirs:
                if tool_dir.exists():
                    shutil.rmtree(tool_dir)

            package_data = {
                "OpenImageIO": ["*.*", "licenses/*.*"],
                "PyOpenColorIO": ["*.*", "licenses/*.*"],
            }
        else:
            package_data = {
                "OpenImageIO": ["*.*", "tools/*.*", "licenses/*.*"],
                "PyOpenColorIO": ["*.*", "tools/*.*", "licenses/*.*"],
            }

        include_data = True
        zip_safe = False

        # Define scripts based on the build type
        scripts_list = []
        if not static_build:
            scripts = {
                "ocioarchive": "PyOpenColorIO._tool_wrapper:ocioarchive",
                "oiiotool": "OpenImageIO._tool_wrapper:oiiotool",
            }

            for script_name, script_path in scripts.items():
                scripts_list.append(f"{script_name}={script_path}")

    else:
        scripts_list = []
        package_data = {}
        scripts = {}
        include_data = False
        zip_safe = True

    package_name = "oiio-python-static" if static_build else "oiio-python"

    setup(
        name=package_name,
        version="2.5.12.0",
        package_dir={"": "oiio_python"},
        packages=find_packages(where="oiio_python"),
        package_data=package_data,
        include_package_data=include_data,
        ext_modules=[],
        distclass=BinaryDistribution,
        entry_points={
            "console_scripts": scripts_list,
        },
        zip_safe=zip_safe,  # Required for including DLLs and PYDs in wheel
        long_description_content_type="text/markdown",
        description="Unofficial OpenImageIO Python wheels, including OpenColorIO",
        author="Paul Parneix",
        author_email="thepoulp@pm.me",
        url="https://github.com/pypoulp/oiio-python",
        classifiers=[
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: C++",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
        python_requires=">=3.8,<3.13",
        install_requires=[
            "numpy>=1.21.2,<2.0.0",  # Dependencies from pyproject.toml
        ],
        extras_require={
            "dev": [
                "black==24.2.0",
                "isort==5.13.2",
            ],
        },
        keywords=[
            "OpenImageIO",
            "OpenColorIO",
            "image",
            "processing",
            "oiio",
            "ocio",
            "python",
            "wrapper",
            "binding",
            "library",
        ],
    )
