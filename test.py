import os
import subprocess

import numpy as np
import OpenImageIO as oiio
import PyOpenColorIO as ocio


def test_tools():
    tools = [
        ["iconvert", "--help"],
        ["idiff", "--help"],
        ["igrep", "--help"],
        ["iinfo", "--help"],
        ["maketx", "--help"],
        ["oiiotool", "--help"],
        ["ocioarchive", "--h"],
        ["ociobakelut", "--h"],
        ["ociocheck", "--h"],
        ["ociochecklut", "--h"],
        ["ocioconvert", "--h"],
        ["ociolutimage", "--h"],
        ["ociomakeclf", "--h"],
        ["ocioperf", "--h"],
        ["ociowrite", "--v"],
    ]

    for tool in tools:
        subprocess.run(tool, check=True)


def main():
    # Test tools
    if os.getenv("OIIO_STATIC") == "1":
        test_tools()

    config = ocio.GetCurrentConfig()
    print("Config: ", config)
    colorSpaceNames = [cs.getName() for cs in config.getColorSpaces()]
    print("Color Spaces: ", colorSpaceNames)

    img_a = np.random.rand(100, 100).astype(np.float32)

    buf = oiio.ImageBuf(img_a)
    buf.write("test.exr")

    # Print version
    print("OpenImageIO Version: ", oiio.__version__)
    print("OpenColorIO Version: ", ocio.__version__)


if __name__ == "__main__":
    main()
