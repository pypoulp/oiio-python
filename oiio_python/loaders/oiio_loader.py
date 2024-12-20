import os
import platform
from pathlib import Path

if platform.system() == "Windows":
    _oiio_site_dir: Path = Path(__file__).parent.resolve()
    _ocio_site_dir: Path = _oiio_site_dir.parent / "PyOpenColorIO"
    with os.add_dll_directory(_oiio_site_dir.as_posix()), os.add_dll_directory(_ocio_site_dir.as_posix()):
        from .OpenImageIO import *
        from .OpenImageIO import __version__
else:
    from .OpenImageIO import *
    from .OpenImageIO import __version__
