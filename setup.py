# pylint: disable=wrong-import-position,missing-module-docstring,missing-function-docstring,missing-class-docstring,invalid-name
import os
import platform
import shutil
import sys
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.dist import Distribution

sys.path.insert(0, os.path.dirname(__file__))
from setuputils import build_dependencies, build_packages, relink_and_delocate

here = Path(__file__).parent.resolve()


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


if __name__ == "__main__":

    license_files_paths = list((here / "licenses").glob("*"))
    license_files = [
        license_file_path.relative_to(here).as_posix()
        for license_file_path in license_files_paths
    ]

    print("including license files:")
    for license_file in license_files:
        print(license_file)

    oiio_static = os.getenv("OIIO_STATIC")
    static_build = str(oiio_static) == "1"

    print("=" * 80)
    if static_build:
        license_files.append("LICENSE-GPL")
        print("Building static libraries.")
    else:
        license_files.append("LICENSE")
        print("Building shared libraries.")
    print("=" * 80)

    if "bdist_wheel" in sys.argv:
        # When running on Cibuildwheel, avoid rebuilding dependencies for each version.
        if os.getenv("CIBUILDWHEEL") != "1":
            build_dependencies()
        # Build OpenColorIO and OpenImageIO
        build_packages(static_build)
        # Fix shared libraries on macos
        if platform.system() == "Darwin":
            relink_and_delocate()
        # Include tools if using shared libraries version
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
            tools_dir = [
                here / "oiio_python" / "OpenImageIO" / "tools",
                here / "oiio_python" / "PyOpenColorIO" / "tools",
            ]

            package_data = {
                "OpenImageIO": ["*.*", "tools/*", "licenses/*.*"],
                "PyOpenColorIO": ["*.*", "tools/*", "licenses/*.*"],
            }

        include_data = True
        zip_safe = False

        # Define scripts based on the build type
        scripts_list = []
        if not static_build:
            oiio_tools = ["iconvert", "idiff", "igrep", "iinfo", "maketx", "oiiotool"]
            ocio_tools = [
                "ocioarchive",
                "ociobakelut",
                "ociocheck",
                "ociochecklut",
                "ocioconvert",
                "ociolutimage",
                "ociomakeclf",
                "ocioperf",
                "ociowrite",
            ]

            scripts = dict()

            for tool in oiio_tools:
                scripts[tool] = f"OpenImageIO._tool_wrapper:{tool}"

            for tool in ocio_tools:
                scripts[tool] = f"PyOpenColorIO._tool_wrapper:{tool}"

            for script_name, script_path in scripts.items():
                scripts_list.append(f"{script_name}={script_path}")

    else:
        scripts_list = []
        package_data = {}
        scripts = {}
        include_data = False
        zip_safe = True
        license_files += ["LICENSE-GPL", "LICENSE"]

    package_name = "oiio-static-python" if static_build else "oiio-python"

    long_description = (here / "README.md").read_text(encoding="utf8")

    setup(
        name=package_name,
        version="3.0.8.1.1",
        license_files=tuple(license_files),
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
        description="Unofficial OpenImageIO Python wheels, including OpenColorIO",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="Paul Parneix",
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
            "Programming Language :: Python :: 3.13",
            "Programming Language :: C++",
            "Programming Language :: Python :: Implementation :: CPython",
            "License :: OSI Approved :: Apache Software License",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        ],
        python_requires=">=3.8,<3.14",
        install_requires=[
            "numpy>=1.21.2,<2.3.0",
        ],
        extras_require={
            "dev": [
                "twine",
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
