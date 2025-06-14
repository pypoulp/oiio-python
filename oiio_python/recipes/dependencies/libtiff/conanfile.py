import os

from conan import ConanFile
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
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class LibtiffConan(ConanFile):
    name = "libtiff"
    description = "Library for Tag Image File Format (TIFF)"
    url = "https://github.com/conan-io/conan-center-index"
    license = "libtiff"
    homepage = "http://www.simplesystems.org/libtiff"
    topics = ("tiff", "image", "bigtiff", "tagged-image-file-format")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cxx": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cxx": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.cxx:
            self.settings.rm_safe("compiler.cppstd")
            self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

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

        if self.dont_use_jpeg_turbo:
            self.requires("libjpeg/9e")
        else:
            self.requires("libjpeg-turbo/3.0.4")

        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("libdeflate/1.19")
        self.requires("xz_utils/[>=5.4.5 <6]")
        self.requires("jbig/20160605")
        self.requires("zstd/1.5.5")
        self.requires("libwebp/1.4.0")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["lzma"] = True
        tc.variables["jpeg"] = True
        tc.variables["jpeg12"] = False
        tc.variables["jbig"] = True
        tc.variables["zlib"] = True
        tc.variables["libdeflate"] = True
        tc.variables["zstd"] = True
        tc.variables["webp"] = True
        tc.variables["lerc"] = (
            False  # TODO: add lerc support for libtiff versions >= 4.3.0
        )
        # Disable tools, test, contrib, man & html generation
        tc.variables["tiff-tools"] = False
        tc.variables["tiff-tests"] = False
        tc.variables["tiff-contrib"] = False
        tc.variables["tiff-docs"] = False
        tc.variables["cxx"] = self.options.cxx
        # BUILD_SHARED_LIBS must be set in command line because defined upstream before project()
        tc.cache_variables["BUILD_SHARED_LIBS"] = bool(self.options.shared)
        tc.cache_variables["CMAKE_FIND_PACKAGE_PREFER_CONFIG"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("jbig", "cmake_target_name", "JBIG::JBIG")
        deps.set_property("xz_utils", "cmake_target_name", "liblzma::liblzma")
        deps.set_property("libdeflate", "cmake_file_name", "Deflate")
        deps.set_property("libdeflate", "cmake_target_name", "Deflate::Deflate")
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        # remove FindXXXX for conan dependencies
        for module in [
            "Deflate",
            "JBIG",
            "JPEG",
            "LERC",
            "WebP",
            "ZSTD",
            "liblzma",
            "LibLZMA",
        ]:
            rm(self, f"Find{module}.cmake", os.path.join(self.source_folder, "cmake"))

        # Export symbols of tiffxx for msvc shared
        replace_in_file(
            self,
            os.path.join(self.source_folder, "libtiff", "CMakeLists.txt"),
            "set_target_properties(tiffxx PROPERTIES SOVERSION ${SO_COMPATVERSION})",
            "set_target_properties(tiffxx PROPERTIES SOVERSION ${SO_COMPATVERSION} WINDOWS_EXPORT_ALL_SYMBOLS ON)",
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        license_file = "LICENSE.md"
        copy(
            self,
            license_file,
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            ignore_case=True,
            keep_path=False,
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "TIFF")
        self.cpp_info.set_property("cmake_target_name", "TIFF::TIFF")
        self.cpp_info.set_property(
            "pkg_config_name", f"libtiff-{Version(self.version).major}"
        )
        suffix = "d" if is_msvc(self) and self.settings.build_type == "Debug" else ""
        if self.options.cxx:
            self.cpp_info.libs.append(f"tiffxx{suffix}")
        self.cpp_info.libs.append(f"tiff{suffix}")
        if self.settings.os in ["Linux", "Android", "FreeBSD", "SunOS", "AIX"]:
            self.cpp_info.system_libs.append("m")

        self.cpp_info.requires = []

        self.cpp_info.requires.append("libdeflate::libdeflate")
        self.cpp_info.requires.append("xz_utils::xz_utils")
        # Dependencies
        if self.dont_use_jpeg_turbo:
            self.cpp_info.requires.append("libjpeg::libjpeg")
        else:
            self.cpp_info.requires.append("libjpeg-turbo::libjpeg-turbo")

        self.cpp_info.requires.append("zlib::zlib")
        self.cpp_info.requires.append("jbig::jbig")
        self.cpp_info.requires.append("zstd::zstd")
        self.cpp_info.requires.append("libwebp::libwebp")

        # TODO: to remove in conan v2 once cmake_find_package* & pkg_config generators removed
        self.cpp_info.names["cmake_find_package"] = "TIFF"
        self.cpp_info.names["cmake_find_package_multi"] = "TIFF"
