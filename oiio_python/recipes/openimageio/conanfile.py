# pylint: disable=E1101,C0114,C0115,C0116

import os
import sys
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    rm,
    rmdir,
)
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version

here = Path(__file__).parent.resolve()


class OpenImageIOConan(ConanFile):
    name = "openimageio"
    description = (
        "OpenImageIO is a library for reading and writing images, and a bunch "
        "of related classes, utilities, and applications. There is a "
        "particular emphasis on formats and functionality used in "
        "professional, large-scale animation and visual effects work for film."
    )
    topics = ("vfx", "image", "picture")
    license = "Apache-2.0", "BSD-3-Clause"
    homepage = "http://www.openimageio.org/"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"

    tool_requires = "cmake/[>=3.16 <4]"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libjpeg": ["libjpeg", "libjpeg-turbo"],
        "with_libpng": [True, False],
        "with_freetype": [True, False],
        "with_hdf5": [True, False],
        "with_opencolorio": [True, False],
        "with_opencv": [True, False],
        "with_tbb": [True, False],
        "with_dicom": [True, False],
        "with_ffmpeg": [True, False],
        "with_giflib": [True, False],
        "with_libheif": [True, False],
        "with_raw": [True, False],
        "with_openjpeg": [True, False],
        "with_openvdb": [True, False],
        "with_ptex": [True, False],
        "with_libwebp": [True, False],
        "with_tools": [True, False],
    }
    default_options = {
        "shared": os.getenv("OIIO_STATIC") != "1",
        "fPIC": True,
        "with_libjpeg": "libjpeg",
        "with_libpng": True,
        "with_freetype": True,
        "with_hdf5": True,
        "with_opencolorio": True,
        "with_opencv": False,
        "with_tbb": True,
        "with_dicom": False,  # Heavy dependency, disabled by default
        "with_ffmpeg": False,
        "with_giflib": True,
        "with_libheif": False,
        "with_raw": True,  # libraw is available under CDDL-1.0 or LGPL-2.1, for this reason it is disabled by default
        "with_openjpeg": True,
        "with_openvdb": False,  # FIXME: broken on M1
        "with_ptex": True,
        "with_libwebp": True,
        "with_tools": os.getenv("OIIO_STATIC") != "1",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":  # pylint: disable=no-member
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        # Required libraries
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("pybind11/2.13.1")
        self.requires("boost/1.84.0")
        self.requires("libtiff/4.6.0")
        self.requires("imath/3.1.9", transitive_headers=True)
        self.requires("openexr/3.1.9")
        if self.options.with_libjpeg == "libjpeg":
            self.requires("libjpeg/9e")
        elif self.options.with_libjpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.2")
        self.requires("pugixml/1.14")
        self.requires("libsquish/1.15")
        self.requires("tsl-robin-map/1.2.1")
        if Version(self.version) >= "2.4.17.0":
            self.requires("fmt/10.2.1", transitive_headers=True)
        else:
            self.requires("fmt/9.1.0", transitive_headers=True)

        # Optional libraries
        if self.options.with_libpng:
            self.requires("libpng/1.6.42")
        if self.options.with_freetype:
            self.requires("freetype/2.13.2")
        if self.options.with_hdf5:
            self.requires("hdf5/1.14.3")
        if self.options.with_opencolorio:
            self.requires("opencolorio/2.2.1")
        if self.options.with_opencv:
            self.requires("opencv/4.8.1")
        if self.options.with_tbb:
            self.requires("onetbb/2021.10.0")
        if self.options.with_dicom:
            self.requires("dcmtk/3.6.7")
        if self.options.with_ffmpeg:
            self.requires("ffmpeg/6.1")
        # TODO: Field3D dependency
        if self.options.with_giflib:
            self.requires("giflib/5.2.1")
        if self.options.with_libheif:
            self.requires("libheif/1.16.2")
        if self.options.with_raw:
            self.requires("libraw/0.21.2")
        if self.options.with_openjpeg:
            self.requires("openjpeg/2.5.0")
        if self.options.with_openvdb:
            self.requires("openvdb/8.0.1")
        if self.options.with_ptex:
            self.requires("ptex/2.4.2")
        if self.options.with_libwebp:
            self.requires("libwebp/1.3.2")
        # TODO: R3DSDK dependency
        # TODO: Nuke dependency

    def validate(self):
        if self.settings.compiler.cppstd:  # pylint: disable=no-member
            check_min_cppstd(self, 14)
        if is_msvc(self) and is_msvc_static_runtime(self) and self.options.shared:
            raise ConanInvalidConfiguration(
                "Building shared library with static runtime is not supported!"
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        # CMake options
        tc.variables["Python_EXECUTABLE"] = Path(sys.executable).as_posix()
        tc.variables["USE_PYTHON"] = True
        tc.variables["PYTHON_SITE_DIR"] = (
            Path(__file__).parents[2] / "OpenImageIO"
        ).as_posix()
        tc.variables["CMAKE_DEBUG_POSTFIX"] = ""  # Needed for 2.3.x.x+ versions
        tc.variables["OIIO_BUILD_TOOLS"] = self.options.with_tools
        tc.variables["OIIO_BUILD_TESTS"] = False
        tc.variables["BUILD_DOCS"] = False
        tc.variables["INSTALL_DOCS"] = False
        tc.variables["INSTALL_FONTS"] = False
        tc.variables["INSTALL_CMAKE_HELPER"] = False
        tc.variables["EMBEDPLUGINS"] = True

        tc.variables["USE_EXTERNAL_PUGIXML"] = True
        tc.variables["BUILD_MISSING_FMT"] = False

        # Conan is normally not used for testing, so fixing this option to not build the tests
        tc.variables["BUILD_TESTING"] = False

        # OIIO CMake files are patched to check USE_* flags to require or not use dependencies
        tc.variables["USE_JPEGTURBO"] = self.options.with_libjpeg == "libjpeg-turbo"
        tc.variables["USE_JPEG"] = (
            True  # Needed for jpeg.imageio plugin, libjpeg/libjpeg-turbo selection still works
        )
        tc.variables["USE_HDF5"] = self.options.with_hdf5
        tc.variables["USE_OPENCOLORIO"] = self.options.with_opencolorio
        tc.variables["USE_OPENCV"] = self.options.with_opencv
        tc.variables["USE_TBB"] = self.options.with_tbb
        tc.variables["USE_DCMTK"] = self.options.with_dicom
        tc.variables["USE_FFMPEG"] = self.options.with_ffmpeg
        tc.variables["USE_FIELD3D"] = False
        tc.variables["USE_GIF"] = self.options.with_giflib
        tc.variables["USE_LIBHEIF"] = self.options.with_libheif
        tc.variables["USE_LIBRAW"] = self.options.with_raw
        tc.variables["USE_OPENVDB"] = self.options.with_openvdb
        tc.variables["USE_PTEX"] = self.options.with_ptex
        tc.variables["USE_R3DSDK"] = False
        tc.variables["USE_NUKE"] = False
        tc.variables["USE_OPENGL"] = False
        tc.variables["USE_QT"] = False
        tc.variables["USE_LIBPNG"] = self.options.with_libpng
        tc.variables["USE_FREETYPE"] = self.options.with_freetype
        tc.variables["USE_LIBWEBP"] = self.options.with_libwebp
        tc.variables["USE_OPENJPEG"] = self.options.with_openjpeg

        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

        for dep in self.dependencies.values():
            if len(dep.cpp_info.bindirs) == 0:
                continue
            lib_pattern = "*.so"
            if self.settings.compiler == "msvc":
                lib_pattern = "*.dll"

            copy(
                self,
                lib_pattern,
                src=dep.cpp_info.bindirs[0],
                dst=Path(self.source_folder) / "build" / "bin",
                keep_path=False,
            )

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE*.md",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        if self.settings.os == "Windows":  # pylint: disable=no-member
            for vc_file in ("concrt", "msvcp", "vcruntime"):
                rm(self, f"{vc_file}*.dll", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        # Copy python bindings & binaries
        py_package_folder = Path(os.environ["OIIO_PKG_DIR"])
        py_package_folder.mkdir(exist_ok=True)

        if self.settings.os == "Windows":  # pylint: disable=no-member
            py_lib_folder = py_package_folder
        else:
            py_lib_folder = Path(os.environ["OIIO_LIBS_DIR"])
            py_lib_folder.mkdir(exist_ok=True)

        bin_folder = Path(self.package_folder) / "bin"
        copy(self, "*OpenImageIO*", src=bin_folder, dst=py_lib_folder)

        if self.settings.os != "Windows":  # pylint: disable=no-member
            lib_folder = Path(self.package_folder) / "lib"
            copy(self, "*OpenImageIO*", src=lib_folder, dst=py_lib_folder)

        if os.getenv("OIIO_STATIC") != "1":
            # Copy tools
            tools_folder = py_package_folder / "tools"
            tools_folder.mkdir(exist_ok=True)

            oiio_tools = ["iconvert", "idiff", "igrep", "iinfo", "maketx", "oiiotool"]
            for tool in oiio_tools:
                copy(self, f"{tool}*", src=bin_folder, dst=tools_folder)

        license_folder = Path(self.package_folder) / "licenses"
        license_folder.mkdir(exist_ok=True)

        copy(self, "LICENSE*.md", src=self.source_folder, dst=license_folder)

        # Copy TBB binaries
        for dep in self.dependencies.values():
            if "onetbb" in str(dep):
                if self.settings.os == "Windows":

                    tbb_bin_folder = Path(dep.package_folder) / "bin"
                    copy(self, "tbb12*", src=tbb_bin_folder, dst=py_lib_folder)
                else:
                    tbb_lib_folder = Path(dep.package_folder) / "lib"
                    copy(self, "*libtbb.*", src=tbb_lib_folder, dst=py_lib_folder)

    @staticmethod
    def _conan_comp(name):
        return f"openimageio_{name.lower()}"

    def _add_component(self, name):
        component = self.cpp_info.components[self._conan_comp(name)]
        component.set_property("cmake_target_name", f"OpenImageIO::{name}")
        component.names["cmake_find_package"] = name
        component.names["cmake_find_package_multi"] = name
        return component

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenImageIO")
        self.cpp_info.set_property("pkg_config_name", "OpenImageIO")

        self.cpp_info.names["cmake_find_package"] = "OpenImageIO"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenImageIO"

        # OpenImageIO::OpenImageIO_Util
        open_image_io_util = self._add_component("OpenImageIO_Util")
        open_image_io_util.libs = ["OpenImageIO_Util"]
        open_image_io_util.requires = [
            "boost::filesystem",
            "boost::thread",
            "boost::system",
            "boost::regex",
            "imath::imath",
            "openexr::openexr",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            open_image_io_util.system_libs.extend(["dl", "m", "pthread"])
        if self.options.with_tbb:
            open_image_io_util.requires.append("onetbb::onetbb")

        # OpenImageIO::OpenImageIO
        open_image_io = self._add_component("OpenImageIO")
        open_image_io.libs = ["OpenImageIO"]
        open_image_io.requires = [
            "openimageio_openimageio_util",
            "zlib::zlib",
            "boost::thread",
            "boost::system",
            "boost::container",
            "boost::regex",
            "libtiff::libtiff",
            "pugixml::pugixml",
            "tsl-robin-map::tsl-robin-map",
            "libsquish::libsquish",
            "fmt::fmt",
            "imath::imath",
            "openexr::openexr",
            "pybind11::pybind11",
        ]

        if self.options.with_libjpeg == "libjpeg":
            open_image_io.requires.append("libjpeg::libjpeg")
        elif self.options.with_libjpeg == "libjpeg-turbo":
            open_image_io.requires.append("libjpeg-turbo::libjpeg-turbo")
        if self.options.with_libpng:
            open_image_io.requires.append("libpng::libpng")
        if self.options.with_freetype:
            open_image_io.requires.append("freetype::freetype")
        if self.options.with_hdf5:
            open_image_io.requires.append("hdf5::hdf5")
        if self.options.with_opencolorio:
            open_image_io.requires.append("opencolorio::opencolorio")
        if self.options.with_opencv:
            open_image_io.requires.append("opencv::opencv")
        if self.options.with_dicom:
            open_image_io.requires.append("dcmtk::dcmtk")
        if self.options.with_ffmpeg:
            open_image_io.requires.append("ffmpeg::ffmpeg")
        if self.options.with_giflib:
            open_image_io.requires.append("giflib::giflib")
        if self.options.with_libheif:
            open_image_io.requires.append("libheif::libheif")
        if self.options.with_raw:
            open_image_io.requires.append("libraw::libraw")
        if self.options.with_openjpeg:
            open_image_io.requires.append("openjpeg::openjpeg")
        if self.options.with_openvdb:
            open_image_io.requires.append("openvdb::openvdb")
        if self.options.with_ptex:
            open_image_io.requires.append("ptex::ptex")
        if self.options.with_libwebp:
            open_image_io.requires.append("libwebp::libwebp")
        if self.settings.os in ["Linux", "FreeBSD"]:
            open_image_io.system_libs.extend(["dl", "m", "pthread"])

        if not self.options.shared:
            open_image_io.defines.append("OIIO_STATIC_DEFINE")
