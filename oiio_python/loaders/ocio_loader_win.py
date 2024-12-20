import os
from pathlib import Path

_ocio_site_dir = Path(__file__).parent.resolve()
with os.add_dll_directory(_ocio_site_dir.as_posix()):
    from .PyOpenColorIO import *
    from .PyOpenColorIO import __version__