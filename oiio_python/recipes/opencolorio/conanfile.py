# pylint: disable=E1101,C0114,C0115,C0116

import os
import sys
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, default_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    rm,
    rmdir,
)
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version


class OpenColorIOConan(ConanFile):
    name = "opencolorio"
    description = "A color management framework for visual effects and animation."
    license = "BSD-3-Clause"
    homepage = "https://opencolorio.org/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("colors", "visual", "effects", "animation")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_sse": [True, False],
    }
    default_options = {
        "shared": os.getenv("OIIO_STATIC") != "1",
        "fPIC": True,
        "use_sse": True,
    }
    # tool_requires = "cmake/[>=3.16 <4]"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":  # pylint: disable=no-member
            del self.options.fPIC
        if self.settings.arch not in ["x86", "x86_64"]:  # pylint: disable=no-member
            del self.options.use_sse

        # Use static libraries for dependencies
        self.options["expat"].shared = False
        self.options["openexr"].shared = False
        self.options["yaml-cpp"].shared = False
        self.options["pystring"].shared = False
        self.options["lcms"].shared = False

        # Set minizip-ng options for macOS
        if is_apple_os(self):
            self.options["minizip-ng"].with_zlib = True
            self.options["minizip-ng"].with_libcomp = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("expat/[>=2.6.2 <3]")
        self.requires("openexr/3.3.1")
        self.requires("imath/3.1.9")

        self.requires("pystring/1.1.4")
        self.requires("yaml-cpp/0.8.0")
        self.requires("pybind11/2.13.6")
        self.requires("minizip-ng/4.0.3")

        # for tools only
        self.requires("lcms/2.16")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):  # pylint: disable=no-member
            check_min_cppstd(self, 11)
        if (
            Version(self.version) >= "2.3.0"
            and self.settings.compiler == "gcc"  # pylint: disable=no-member
            and Version(self.settings.compiler.version)
            < "6.0"  # pylint: disable=no-member
        ):
            raise ConanInvalidConfiguration(f"{self.ref} requires gcc >= 6.0")

        if (
            Version(self.version) >= "2.3.0"
            and self.settings.compiler == "clang"
            and self.settings.compiler.libcxx == "libc++"
        ):  # pylint: disable=no-member
            raise ConanInvalidConfiguration(
                f"{self.ref} deosn't support clang with libc++"
            )

        # opencolorio>=2.2.0 requires minizip-ng with with_zlib
        if Version(self.version) >= "2.2.0" and not self.dependencies[
            "minizip-ng"
        ].options.get_safe("with_zlib", False):
            raise ConanInvalidConfiguration(
                f"{self.ref} requires minizip-ng with with_zlib = True. On Apple platforms with_libcomp = False is also needed to enable the with_zlib option."
            )

        if (
            Version(self.version) >= "2.2.1"
            and self.options.shared
            and self.dependencies["minizip-ng"].options.shared
        ):
            raise ConanInvalidConfiguration(
                f"{self.ref} requires static build minizip-ng"
            )

    def source(self):
        get(
            self, **self.conan_data["sources"][self.version], strip_root=True
        )  # pylint: disable=no-member

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cppstd = default_cppstd(self)

        tc.variables["Python_EXECUTABLE"] = Path(sys.executable).as_posix()
        tc.variables["Python3_EXECUTABLE"] = Path(sys.executable).as_posix()

        tc.variables["OCIO_BUILD_PYTHON"] = True
        tc.variables["CMAKE_VERBOSE_MAKEFILE"] = True
        tc.variables["OCIO_USE_SSE"] = self.options.get_safe("use_sse", False)

        # openexr 2.x provides Half library
        tc.variables["OCIO_USE_OPENEXR_HALF"] = True
        tc.variables["OCIO_BUILD_APPS"] = os.getenv("OIIO_STATIC") != "1"
        tc.variables["OCIO_BUILD_DOCS"] = False
        tc.variables["OCIO_BUILD_TESTS"] = False
        tc.variables["OCIO_BUILD_GPU_TESTS"] = False
        tc.variables["OCIO_USE_BOOST_PTR"] = False

        # avoid downloading dependencies
        tc.variables["OCIO_INSTALL_EXT_PACKAGE"] = "NONE"

        if is_msvc(self) and not self.options.shared:
            # define any value because ifndef is used
            tc.variables["OpenColorIO_SKIP_IMPORTS"] = True

        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        for module in ("expat", "lcms2", "pystring", "yaml-cpp", "Imath", "minizip-ng"):
            rm(
                self,
                "Find" + module + ".cmake",
                os.path.join(self.source_folder, "share", "cmake", "modules"),
            )

    def build(self):
        self._patch_sources()

        cm = CMake(self)
        cm.configure()
        cm.build()

    def package(self):
        cm = CMake(self)
        cm.install()

        if not self.options.shared:
            copy(
                self,
                "*",
                src=os.path.join(self.package_folder, "lib", "static"),
                dst=os.path.join(self.package_folder, "lib"),
            )
            rmdir(self, os.path.join(self.package_folder, "lib", "static"))

        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "OpenColorIOConfig*.cmake", self.package_folder)
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        copy(
            self,
            pattern="LICENSE",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )

        # Copy python bindings & binaries
        py_package_folder = Path(os.environ["OCIO_PKG_DIR"])
        py_package_folder.mkdir(exist_ok=True)

        if self.settings.os == "Windows":  # pylint: disable=no-member
            py_lib_folder = py_package_folder
        else:
            py_lib_folder = Path(os.environ["OIIO_LIBS_DIR"])
            py_lib_folder.mkdir(exist_ok=True)

        bin_dir = Path(self.package_folder) / "bin"

        copy(self, "*OpenColorIO*", src=bin_dir, dst=py_lib_folder)

        if self.settings.os != "Windows":  # pylint: disable=no-member
            lib_dir = Path(self.package_folder) / "lib"
            copy(self, "*OpenColorIO*", src=lib_dir, dst=py_lib_folder)

        if os.getenv("OIIO_STATIC") != "1":
            tools_dir = py_package_folder / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)

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

            for tool in ocio_tools:
                copy(self, f"{tool}*", src=bin_dir, dst=tools_dir)

        if self.settings.os == "Windows":  # pylint: disable=no-member
            ocio_sp_folder = (
                Path(self.package_folder) / "lib" / "site-packages" / "PyOpenColorIO"
            )
            copy(self, "*PyOpenColorIO*", src=ocio_sp_folder, dst=py_package_folder)
        else:
            ocio_lib_folder = Path(self.package_folder) / "lib"
            ocio_py_folder = list(ocio_lib_folder.glob("py*"))[0]
            ocio_sp_folder = ocio_py_folder / "site-packages"
            copy(self, "*PyOpenColorIO*", src=ocio_sp_folder, dst=py_package_folder)

        license_folder = Path(self.package_folder) / "licenses"
        license_folder.mkdir(exist_ok=True)
        copy(self, pattern="LICENSE", dst=license_folder, src=self.source_folder)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenColorIO")
        self.cpp_info.set_property("cmake_target_name", "OpenColorIO::OpenColorIO")
        self.cpp_info.set_property("pkg_config_name", "OpenColorIO")

        self.cpp_info.libs = ["OpenColorIO"]

        if is_apple_os(self):
            self.cpp_info.frameworks.extend(
                ["Foundation", "IOKit", "ColorSync", "CoreGraphics"]
            )
            if Version(self.version) == "2.1.0":
                self.cpp_info.frameworks.extend(["Carbon", "CoreFoundation"])

        if is_msvc(self) and not self.options.shared:
            self.cpp_info.defines.append("OpenColorIO_SKIP_IMPORTS")

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH env var with: {bin_path}")
        self.env_info.PATH.append(bin_path)
