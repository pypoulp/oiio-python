import subprocess
from pathlib import Path

here = Path(__file__).parent.resolve()

def check_and_add_rpath(binary_path, rpath):
    """Check and add an LC_RPATH entry if not already present."""
    try:
        result = subprocess.run(
            ["otool", "-l", str(binary_path)], capture_output=True, text=True, check=True
        )
        if rpath in result.stdout:
            print(f"RPATH '{rpath}' already exists in {binary_path}")
        else:
            subprocess.run(
                ["install_name_tool", "-add_rpath", rpath, str(binary_path)], check=True
            )
            print(f"Added RPATH '{rpath}' to {binary_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking or adding RPATH: {e}")

def update_rpath_references(libs_dir, target_names):
    """
    Update all `@rpath` references to `@loader_path` for a list of target library names.
    """
    libs_dir = Path(libs_dir)
    for dylib in libs_dir.glob("*.dylib"):
        try:
            result = subprocess.run(["otool", "-L", str(dylib)], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                for target_name in target_names:
                    if target_name in line:
                        old_path = line.split()[0]
                        new_path = f"@loader_path/{Path(old_path).name}"
                        subprocess.run(["install_name_tool", "-change", old_path, new_path, str(dylib)], check=True)
                        print(f"Updated {old_path} -> {new_path} in {dylib}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {dylib}: {e}")

def ensure_rpaths(binaries, rpath):
    """Ensure LC_RPATH for a list of binaries."""
    for binary in binaries:
        check_and_add_rpath(binary, rpath)

def relink_and_delocate():
    try:
        base_path = here / "oiio_python"
        libs_dir = base_path / "libs"
        libs_dir.mkdir(parents=True, exist_ok=True)

        # Define paths for libraries and modules
        oiio_so = next((base_path / "OpenImageIO").glob("*.so"))
        ocio_so = next((base_path / "PyOpenColorIO").glob("*.so"))

        lib_oiio = max((f for f in libs_dir.glob("libOpenImageIO.*.dylib") if not f.is_symlink()),
                       key=lambda f: f.stat().st_size)
        lib_ocio = max((f for f in libs_dir.glob("libOpenColorIO.*.dylib") if not f.is_symlink()),
                       key=lambda f: f.stat().st_size)
        lib_tbb = libs_dir / "libtbb.12.10.dylib"

        # Check required files exist
        required_files = [oiio_so, ocio_so, lib_oiio, lib_ocio, lib_tbb]
        for path in required_files:
            if not path.is_file():
                raise FileNotFoundError(f"Required file '{path}' does not exist.")

        # Update RPATH references
        update_rpath_references(libs_dir, [
            "libtbb", "libtbbmalloc", "libtbbmalloc_proxy",
            "libOpenImageIO", "libOpenColorIO", "libOpenImageIO_Util"
        ])

        # Ensure LC_RPATH for all binaries
        ensure_rpaths([oiio_so, ocio_so, lib_oiio, lib_ocio, lib_tbb], "@loader_path")
        ensure_rpaths([oiio_so, ocio_so], "@loader_path/../../.dylibs")

        print("Relinking and RPATH configuration completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error during relinking or RPATH configuration: {e}")
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    relink_and_delocate()
