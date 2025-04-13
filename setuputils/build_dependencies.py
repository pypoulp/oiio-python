"""Build script for installing and building dependencies using Conan."""

import platform
import subprocess
import sys
from pathlib import Path

project = Path(__file__).parent.parent.resolve()
sys.path.insert(0, project.as_posix())

from setuputils.build_utils import build_cleanup  # pylint: disable=C0413
from setuputils.build_utils import conan_install_package, conan_profile_ensure


def build_dependencies() -> None:
    """Build all required dependencies using Conan with appropriate profile."""
    if platform.system() == "Windows":
        conan_profile_ensure(cpp_std="17")
    else:
        conan_profile_ensure(cpp_std="gnu17")

    profile_name = "default_oiio_build"

    # LibRaw
    libraw_dep_dir = project / "oiio_python" / "recipes" / "dependencies" / "libraw"
    libraw_version = "0.21.3"
    conan_install_package(libraw_dep_dir, libraw_version, profile=profile_name)
    build_cleanup(libraw_dep_dir)

    # LibTiff
    libtiff_dep_dir = project / "oiio_python" / "recipes" / "dependencies" / "libtiff"
    libtiff_version = "4.7.0"
    conan_install_package(libtiff_dep_dir, libtiff_version, profile=profile_name)
    build_cleanup(libtiff_dep_dir)

    # Libultrahdr
    libuhdr_dep_dir = project / "oiio_python" / "recipes" / "dependencies" / "libuhdr"
    libuhdr_version = "1.3.0"
    conan_install_package(libuhdr_dep_dir, libuhdr_version, profile=profile_name)
    build_cleanup(libuhdr_dep_dir)

    # libjxl
    libuhdr_dep_dir = project / "oiio_python" / "recipes" / "dependencies" / "libjxl"
    libuhdr_version = "0.10.2"
    conan_install_package(libuhdr_dep_dir, libuhdr_version, profile=profile_name)
    build_cleanup(libuhdr_dep_dir)

    # bzip2 on linux
    if platform.system() == "Linux":
        bzip2_dep_dir = project / "oiio_python" / "recipes" / "dependencies" / "bzip2"
        bzip2_version = "1.0.8"
        conan_install_package(bzip2_dep_dir, bzip2_version, profile=profile_name)
        build_cleanup(bzip2_dep_dir)


def _main() -> None:
    python_exe = sys.executable
    cmd = [python_exe, "-m", "pip", "install", "conan==2.4.0"]
    subprocess.run(cmd, check=True)
    build_dependencies()


if __name__ == "__main__":
    _main()
