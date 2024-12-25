import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, get, rmdir


class LibultrahdrConan(ConanFile):
    name = "libuhdr"
    description = (
        "Library for storing and distributing HDR images using gain map technology"
    )
    license = "Apache-2.0"
    url = "https://github.com/google/libultrahdr"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    generators = "CMakeDeps"

    tool_requires = "cmake/[>=3.15]"

    def config_options(self):
        if self.settings.os == "Windows":  # pylint: disable=no-member
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        check_min_cppstd(self, "14")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

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

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["UHDR_BUILD_DEPS"] = False
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["ULTRAHDR_BUILD_TESTS"] = False
        tc.variables["UHDR_BUILD_EXAMPLES"] = False
        tc.variables["UHDR_ENABLE_INSTALL"] = True
        tc.variables["CMAKE_INSTALL_PREFIX"] = self.package_folder

        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        # For some reason, install fails on Windows.
        # Copy the files manually.
        copy(
            self,
            pattern="*.h",
            src=os.path.join(self.source_folder),
            dst=os.path.join(self.package_folder, "include"),
        )
        copy(
            self,
            pattern="*.lib",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "lib"),
            keep_path=False,
        )
        copy(
            self,
            pattern="*.dll",
            src=self.build_folder,
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

    def package_info(self):
        # Basic package information
        self.cpp_info.set_property("cmake_file_name", "libuhdr")
        self.cpp_info.set_property("cmake_target_name", "libuhdr::libuhdr")

        # # Library information
        self.cpp_info.libs.append("uhdr")
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]

        # Dependencies
        if self.dont_use_jpeg_turbo:
            self.cpp_info.requires = ["libjpeg::libjpeg"]
        else:
            self.cpp_info.requires = ["libjpeg-turbo::libjpeg-turbo"]
