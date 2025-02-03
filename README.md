# **oiio-python**

**🐍 OpenImageIO on wheels!**

This project provides (unofficial) multiplatform wheels for [OpenImageIO](https://github.com/AcademySoftwareFoundation/OpenImageIO) Python bindings, simplifying installation and integration into Python projects.

[![PyPI Downloads](https://static.pepy.tech/badge/oiio-python/month)](https://pepy.tech/projects/oiio-python)

Check [types-oiio-python](https://github.com/pypoulp/types-oiio-python) if you want type hints & auto-completion for oiio-python.

[![Build Static Multiplatform Wheels](https://github.com/pypoulp/oiio-python/actions/workflows/build_static_wheels.yml/badge.svg)](https://github.com/pypoulp/oiio-python/actions/workflows/build_static_wheels.yml)
[![Build Multiplatform Wheels](https://github.com/pypoulp/oiio-python/actions/workflows/build_wheels.yml/badge.svg)](https://github.com/pypoulp/oiio-python/actions/workflows/build_wheels.yml)
[![Build Linux Wheels](https://github.com/pypoulp/oiio-python/actions/workflows/build_linux_wheels.yml/badge.svg)](https://github.com/pypoulp/oiio-python/actions/workflows/build_linux_wheels.yml)


**Note:** Official wheels are now available 🎉 ! I'll continue to maintain these builds aside cos they still provide some extra stuff, like integrated PyOpenColorIO, and more enabled features.

---

## **Features**

- **🚀 Easy Installation**: Install via pip—no need to compile.
- **🌐 Multiplatform**: Supports Windows (x86_64), macOS (x86_64 and arm64), and Linux (x86_64 and aarch64).
  
- **🎨 Integrated OpenColorIO**: Includes PyOpenColorIO for seamless color management.
- **⚙️ Automated Builds**: Built using [Conan](https://docs.conan.io/2/), [Cibuildwheel](https://cibuildwheel.pypa.io/en/stable/), and [GitHub Actions](https://github.com/features/actions).
- **📦 Flexible Libraries**: Choose between static and shared libraries to suit your needs.

---


## **Installation**

```bash
# ensure pip is up-to-date:
python -m pip install --upgrade pip

# Install the shared libraries variant:
pip install oiio-python

# Install the static libraries variant:
pip install oiio-static-python
```

This project avoids using the `openimageio` package name because the ASWF may release official wheels in the future.

You do NOT need to have OpenImageIO installed on your system. `oiio-python` ship with all necessary shared library.

## **What's Included**

The goal is to enable as many features as possible to make the wheel flexible, while keeping the package size reasonable.

OpenImageIO wheels are built with the following features enabled:

- **[OpenColorIO](https://opencolorio.org/)**: With Python bindings included for seamless color management.
- **LibRaw**: Adds RAW image support.
- **OpenEXR**: High dynamic range image support.
- **Ptex**: Ptex texture mapping support.
- **OneTBB**: Multithreading support.
- **FreeType**: Enables text rendering.
- **TBB**: Multithreading support with Intel TBB. Disabled in musllinux/static MacOS builds.
- **libwebp**: WebP image support.
- **libpng**: PNG image support.
- **libjpeg**: Support with libjpeg on musllinux, and manylinux static builds, libjpeg-turbo on other platforms.
- **giflib**: GIF support.
- **hdf5**: HDF5 data storage support.
- **libheif**: HEIF/AVIF image support.
- **libtiff**: TIFF image support.
- **libjxl**: JPEG XL image support.
- **libultrahdr**: Adds support for UltraHDR images.
- **OpenJPEG**: JPEG 2000 support.

*FFmpeg is not included due to potential licensing issues and package size.*

*DICOM support is also not enabled because of large package size.*

*Volumetric format support like **OpenVDB** are not included for now but could be in the future if requested.*

---

## **oiio-python vs oiio-static-python**

This project builds two variants of the OpenImageIO Python bindings:

- **`oiio-python`**: 
  - Links against shared OpenImageIO and OpenColorIO libraries.
  - Generally smaller package size.
  - Includes tools like `oiiotool` and `ociobakelut`.

- **`oiio-static-python`**:
  - Uses statically linked dependencies.
  - Generally larger package size.
  - Does **not** include OpenImageIO and OpenColorIO tools.
  - **Ideal for avoiding DLL conflicts**, especially when using Python embedded in applications like DCC tools that already use OpenImageIO.

`oiio-python` versions match the original OpenImageIO release version, with an additional build number for the Python bindings. Example oiio-python 2.5.12.0.x is built from OpenImageIO 2.5.12

## License

Code in this repository is licensed under the [Apache 2.0 License](LICENSE) to match the original OpenImageIO license.  
Third-party libraries are licensed under their respective licenses. Copies of these licenses can be found in the [licenses](licenses) folder.

#### Statically Linked Libraries in Binary Wheels

The binary wheels may include LGPL statically linked libraries, including:

- **[LibRaw](https://github.com/LibRaw/LibRaw)** (LGPL 2.1)
- **[LibHeif](https://github.com/strukturag/libheif)** (LGPL 3.0)

#### Licensing for Versions Before 3.0.1.0

Before version 3.0.1.0, the distributed wheels are licensed under the [GPL 3.0 License](LICENSE-GPL).

#### Licensing for Versions 3.0.1.0 and Above

For version 3.0.1.0 and above:

- **`oiio-static-python` wheels** are licensed under the [GPL 3.0 License](LICENSE-GPL).
- **`oiio-python` wheels** are licensed under the [Apache 2.0 License](LICENSE) and include shared libraries for LibRaw and LibHeif.


## **Building the Wheels Yourself**

Although the primary target is automated builds on GitHub Actions, you can also build the wheels locally.

**Note:** Build system will use your `default` Conan profile to create a new `default_oiio_build` profile, make sure it's configured correctly.

### **Windows**

1. Install Python (3.11+ recommended), CMake, and Visual Studio.
2. To build wheels for multiple Python versions:

    ```powershell
    # For the static variant:
    set OIIO_STATIC=1
    python -m pip install cibuildwheel
    cibuildwheel --platform windows
    ```

3. To only build for your current Python version:

    ```powershell
    python -m pip install build
    python -m build --wheel
    ```

### **MacOS**

1. Install Python (3.11+ recommended), Homebrew, and Xcode.
2. Set environment variables before building:

    ```bash
    # If you want to build the static variant:
    export OIIO_STATIC=1
    # Set Deployment target according to your macOS version
    export MACOSX_DEPLOYMENT_TARGET=10.15  # For x86_64 builds
    export MACOSX_DEPLOYMENT_TARGET=14.0  # For arm64 builds
    # Set Project root directory to the root of the repository
    export PROJECT_ROOT="/path/to/oiio-python"
    ```

3. To run cibuildwheel and build wheels for multiple python versions:

    ```bash
    python -m pip install cibuildwheel
    cibuildwheel --platform macos
    ```

4. To only build for your current Python version:

    ```bash
    python -m pip install build
    python -m build --wheel
    ```

5. If not building with cibuildwheel, you'll need to manually "repair" the wheel with delocate after build:

6. run provided `setuputils/macos_fix_shared_libs.py`

7. then use `delocate-wheel` to copy the shared libraries into the wheel:

    ```bash
    python -m pip install delocate

    export REPAIR_LIBRARY=$PROJECT_ROOT/oiio_python/libs:$DYLD_LIBRARY_PATH
    DYLD_LIBRARY_PATH=$REPAIR_LIBRARY delocate-wheel -w /repaired/out/folder -v /path/to/wheel -e $HOME/.conan2
    ```

### **Linux**

1. Linux builds use Docker containers via cibuildwheel for compatibility.
2. Install Docker and build:

    ```bash
    # If building on musl (Alpine) Linux, set the following environment variable:
    export MUSLLINUX_BUILD=1
    export CIBW_ENVIRONMENT="OIIO_STATIC=1"  # For the static version
    # Optional: Specify target docker image / platform
    export CIBW_BUILD="*manylinux_x86*"
    python -m pip install cibuildwheel
    cibuildwheel
    ```

3. To build for the current Python version and distribution:

    - Ensure Perl is installed (required for dependencies).
    - Use `setuputils/linux_before_all.sh` if needed.


        ```bash
        python -m pip install build
        python -m build --wheel
        ```

4. If not building with cibuildwheel, you'll need to manually "repair" the wheel with auditwheel after build:

    ```bash	
    python -m pip install auditwheel

    export LD_LIBRARY_PATH=/path/to/oiio_python/libs:$LD_LIBRARY_PATH
    auditwheel repair -w /repaired/out/folder /path/to/wheel 
    ```

### **Notes**

 - I'm not an expert in Conan, CMake, or Cibuildwheel. Feedback and suggestions for improvement are highly appreciated.