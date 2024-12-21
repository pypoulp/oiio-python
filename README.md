# 🐍 **oiio-python**

**OpenImageIO on wheels!**

This project provides (unofficial) multiplatform wheels for [OpenImageIO](https://github.com/AcademySoftwareFoundation/OpenImageIO) Python bindings, simplifying installation and integration into Python projects.

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

## **What's Included**

This package integrates the following features and dependencies:

- **[OpenColorIO](https://opencolorio.org/)**: Python bindings included for seamless color management.
- **LibRaw**: Adds RAW image support.
- **Freetype**: Enables text rendering.
- **TBB**: Multithreading support.
- **LibWebP**: WebP image support.
- **LibPNG** and **LibJPEG/OpenJPEG**: For PNG and JPEG support.
- **Giflib**: GIF support.
- **HDF5**: High-performance data storage support.
- **Ptex**: Ptex texture mapping.

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

## **Building the Wheels Yourself**

Although the primary target is automated builds on GitHub Actions, you can also build the wheels locally.

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
    export MACOSX_DEPLOYMENT_TARGET=10.13  # For x86_64 builds
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

6. run provided `macos_fix_shared_libs.py`

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
    export CIBW_ENVIRONMENT="OIIO_STATIC=1"  # For the static version
    # Optional: Specify target docker image / platform
    export CIBW_BUILD="*manylinux_x86*"
    python -m pip install cibuildwheel
    cibuildwheel
    ```

3. To build for the current Python version and distribution:

    - Ensure Perl is installed (required for dependencies).
    - Use `linux_before_all.sh` if needed.

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

 - A Github Action exists to build on Linux aarch64 using QEMU emulation, but it's way too slow and reach timeout. Current aarch64 wheels are built locally on a Raspberry Pi 5, only for ManyLinux.

 - I'm not an expert in Conan, CMake, or Cibuildwheel. Feedback and suggestions for improvement are highly appreciated.

 - Optimizing the build process to avoid rebuilding LibOpenImageIO for each Python version is a potential area for improvement.

 - Although Conan may not be ideal for building wheels, it's currently used here due to the complexity of dependencies and the need to build from scratch for ManyLinux/Musllinux compatibility.