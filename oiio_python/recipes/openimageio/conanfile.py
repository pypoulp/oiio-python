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
    replace_in_file,
    rm,
    rmdir,
)
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

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

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_tools": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "with_tools": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":  # pylint: disable=no-member
            del self.options.fPIC

        if os.getenv("MUSLLINUX_BUILD") == "1":
            # Meson build fails on musllinux
            self.options["freetype"].with_png = False
            self.options["freetype"].with_brotli = False

        if os.getenv("OIIO_STATIC") == "1":
            self.options.shared = False
            self.options.with_tools = False
            self.options["libraw"].shared = False
            self.options["libheif"].shared = False

        else:
            self.options.shared = True
            self.options.with_tools = True
            self.options["libraw"].shared = True
            self.options["libheif"].shared = True

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    @property
    def dont_use_jpeg_turbo(self):
        if os.getenv("MUSLLINUX_BUILD") == "1":
            return True
        elif os.getenv("OIIO_STATIC") == "1" and self.settings.os in [
            "Linux",
            "FreeBSD",
        ]:
            return True
        return False

    def requirements(self):
        # Required libraries
        self.requires("libjxl/0.10.2")
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("pybind11/2.13.6")
        self.requires("libtiff/4.7.0")
        self.requires("imath/3.1.9", transitive_headers=True)
        self.requires("openexr/3.3.1")
        if self.dont_use_jpeg_turbo:
            self.requires("libjpeg/9e")
        else:
            self.requires("libjpeg-turbo/3.0.4")
        self.requires("pugixml/1.14")
        self.requires("libsquish/1.15")
        self.requires("tsl-robin-map/1.2.1")
        self.requires("fmt/10.2.1", transitive_headers=True)
        # Optional libraries
        self.requires("libuhdr/1.3.0")
        self.requires("libpng/1.6.44")
        self.requires("freetype/2.13.0")
        self.requires("hdf5/1.14.3")
        self.requires("opencolorio/2.4.0")
        # self.requires("opencv/4.8.1")
        self.requires("onetbb/2021.10.0")
        # self.requires("dcmtk/3.6.7")
        # self.requires("ffmpeg/6.1")
        # TODO: Field3D dependency
        self.requires("giflib/5.2.1")
        self.requires("libheif/1.16.2")
        self.requires("libraw/0.21.3")
        self.requires("openjpeg/2.5.0")
        # self.requires("openvdb/11.0.0")
        self.requires("ptex/2.4.2")
        self.requires("libwebp/1.4.0")
        # TODO: R3DSDK dependency
        # TODO: Nuke dependency

    def validate(self):
        if self.settings.compiler.cppstd:  # pylint: disable=no-member
            check_min_cppstd(self, 17)
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
        # if self.settings.os == "Linux":
        #     tc.variables["DCOMPILER_SUPPORTS_ATOMIC_WITHOUT_LIBATOMIC_EXITCODE"] = 0

        print(Path(sys.executable).as_posix())
        tc.variables["Python_EXECUTABLE"] = Path(sys.executable).as_posix()
        tc.variables["Python3_EXECUTABLE"] = Path(sys.executable).as_posix()

        tc.variables["USE_PYTHON"] = True
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
        tc.variables["USE_JPEGTURBO"] = not self.dont_use_jpeg_turbo
        tc.variables["USE_JPEG"] = (
            True  # Needed for jpeg.imageio plugin, libjpeg/libjpeg-turbo selection still works
        )
        tc.variables["USE_HDF5"] = True
        tc.variables["USE_OPENCOLORIO"] = True
        tc.variables["USE_OPENCV"] = False
        tc.variables["USE_TBB"] = False
        tc.variables["USE_DCMTK"] = False
        tc.variables["USE_FFMPEG"] = False
        tc.variables["USE_FIELD3D"] = False
        tc.variables["USE_GIF"] = True
        tc.variables["USE_LIBHEIF"] = True
        tc.variables["USE_LIBRAW"] = True
        tc.variables["USE_OPENVDB"] = False
        tc.variables["USE_PTEX"] = True
        tc.variables["USE_R3DSDK"] = False
        tc.variables["USE_NUKE"] = False
        tc.variables["USE_OPENGL"] = False
        tc.variables["USE_QT"] = False
        tc.variables["USE_LIBPNG"] = True
        tc.variables["USE_FREETYPE"] = True
        tc.variables["USE_LIBWEBP"] = True
        tc.variables["USE_OPENJPEG"] = True

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

        oiio_lib_folder = Path(self.package_folder) / "lib"
        oiio_py_folder = list(oiio_lib_folder.glob("py*"))[0]
        oiio_sp_folder = oiio_py_folder / "site-packages" / "OpenImageIO"
        copy(self, "*OpenImageIO*", src=oiio_sp_folder, dst=py_package_folder)

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
            copy(self, "libOpenImageIO*", src=lib_folder, dst=py_lib_folder)

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

            if os.getenv("OIIO_STATIC") != "1":
                if "raw" in str(dep):
                    if self.settings.os == "Windows":
                        raw_lib_folder = Path(dep.package_folder) / "bin"
                        copy(self, "*raw.*", src=raw_lib_folder, dst=py_lib_folder)
                    else:
                        raw_lib_folder = Path(dep.package_folder) / "lib"
                        copy(self, "*raw.*", src=raw_lib_folder, dst=py_lib_folder)
                if "heif" in str(dep):
                    if self.settings.os == "Windows":
                        heif_lib_folder = Path(dep.package_folder) / "bin"
                        copy(self, "*heif.*", src=heif_lib_folder, dst=py_lib_folder)
                    else:
                        heif_lib_folder = Path(dep.package_folder) / "lib"
                        copy(self, "*heif.*", src=heif_lib_folder, dst=py_lib_folder)

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
        if self.settings.os in ["Linux", "FreeBSD"]:
            open_image_io_util.system_libs.extend(["dl", "m", "pthread"])
            open_image_io_util.requires.append("onetbb::onetbb")

        # OpenImageIO::OpenImageIO
        open_image_io = self._add_component("OpenImageIO")
        open_image_io.libs = ["OpenImageIO"]
        open_image_io.requires = [
            "openimageio_openimageio_util",
            "zlib::zlib",
            "libtiff::libtiff",
            "pugixml::pugixml",
            "tsl-robin-map::tsl-robin-map",
            "libsquish::libsquish",
            "fmt::fmt",
            "imath::imath",
            "openexr::openexr",
            "pybind11::pybind11",
            "libjxl::libjxl",
            "onetbb::onetbb",
            "libuhdr::libuhdr",
        ]

        if self.dont_use_jpeg_turbo:
            self.cpp_info.requires.append("libjpeg::libjpeg")
        else:
            self.cpp_info.requires.append("libjpeg-turbo::libjpeg-turbo")
        open_image_io.requires.append("libpng::libpng")
        open_image_io.requires.append("freetype::freetype")
        open_image_io.requires.append("hdf5::hdf5")
        open_image_io.requires.append("opencolorio::opencolorio")
        # open_image_io.requires.append("opencv::opencv")
        # open_image_io.requires.append("dcmtk::dcmtk")
        # open_image_io.requires.append("ffmpeg::ffmpeg")
        open_image_io.requires.append("giflib::giflib")
        open_image_io.requires.append("libheif::libheif")
        open_image_io.requires.append("libraw::libraw")
        open_image_io.requires.append("openjpeg::openjpeg")
        # open_image_io.requires.append("openvdb::openvdb")
        open_image_io.requires.append("ptex::ptex")
        open_image_io.requires.append("libwebp::libwebp")

        if self.settings.os in ["Linux", "FreeBSD"]:
            open_image_io.system_libs.extend(["dl", "m", "pthread"])

        if not self.options.shared:
            open_image_io.defines.append("OIIO_STATIC_DEFINE")
