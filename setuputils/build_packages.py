"""Build script for OpenImageIO and OpenColorIO Python packages."""

import os
import platform
import shutil
from pathlib import Path

from setuputils.build_utils import (
    build_cleanup,
    conan_install_package,
    conan_profile_ensure,
)

project = Path(__file__).parent.parent.resolve()


def build_packages(build_static_version: bool = False) -> None:
    """Build OpenImageIO and OpenColorIO packages using conan."""

    if platform.system() == "Windows":
        conan_profile_ensure(cpp_std="17")
    else:
        conan_profile_ensure(cpp_std="gnu17")

    profile_name = "default_oiio_build"

    ocio_pkg_dir = project / "oiio_python" / "PyOpenColorIO"
    oiio_pkg_dir = project / "oiio_python" / "OpenImageIO"

    for package_dir in [ocio_pkg_dir, oiio_pkg_dir]:
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()

    libs_dir = project / "oiio_python" / "libs"
    if libs_dir.exists():
        shutil.rmtree(libs_dir)
    libs_dir.mkdir()

    os.environ["OCIO_PKG_DIR"] = ocio_pkg_dir.as_posix()
    os.environ["OIIO_PKG_DIR"] = oiio_pkg_dir.as_posix()
    os.environ["OIIO_LIBS_DIR"] = libs_dir.as_posix()

    # OpenColorIO
    ocio_dep_dir = project / "oiio_python" / "recipes" / "opencolorio"
    ocio_version = "2.4.0"
    conan_install_package(ocio_dep_dir, ocio_version, profile=profile_name)
    build_cleanup(ocio_dep_dir)

    # OpenImageIO
    oiio_dir = project / "oiio_python" / "recipes" / "openimageio"
    oiio_version = "3.0.1.0"
    conan_install_package(oiio_dir, oiio_version, profile=profile_name)
    build_cleanup(oiio_dir)

    # Clean loaders
    loaders_dir = project / "oiio_python" / "loaders"
    if (oiio_pkg_dir / "__init__.py").exists():
        os.remove(oiio_pkg_dir / "__init__.py")

    if (ocio_pkg_dir / "__init__.py").exists():
        os.remove(ocio_pkg_dir / "__init__.py")
    # Copy loaders
    if platform.system() == "Windows":
        shutil.copyfile(loaders_dir / "ocio_loader_win.py", ocio_pkg_dir / "__init__.py")
        shutil.copyfile(loaders_dir / "oiio_loader_win.py", oiio_pkg_dir / "__init__.py")
    else:
        shutil.copyfile(loaders_dir / "ocio_loader.py", ocio_pkg_dir / "__init__.py")
        shutil.copyfile(loaders_dir / "oiio_loader.py", oiio_pkg_dir / "__init__.py")

    if not build_static_version:
        # Copy tool wrappers
        wrappers_dir = project / "oiio_python" / "tool_wrappers"
        if platform.system() == "Windows":
            shutil.copyfile(wrappers_dir / "oiio_tools_win.py", oiio_pkg_dir / "_tool_wrapper.py")
            shutil.copyfile(wrappers_dir / "ocio_tools_win.py", ocio_pkg_dir / "_tool_wrapper.py")
        else:
            shutil.copyfile(wrappers_dir / "oiio_tools.py", oiio_pkg_dir / "_tool_wrapper.py")
            shutil.copyfile(wrappers_dir / "ocio_tools.py", ocio_pkg_dir / "_tool_wrapper.py")
