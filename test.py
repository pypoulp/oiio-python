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


def test_numpy():
    rand_img = np.random.rand(128, 128, 3).astype(np.float32)
    buf = oiio.ImageBuf(rand_img)
    pixels = buf.get_pixels(oiio.FLOAT, oiio.ROI(0, 128, 0, 128, 0, 1))
    assert np.allclose(pixels, rand_img)
    buf = oiio.ImageBuf(pixels)


def main():
    # Test tools
    if os.getenv("OIIO_STATIC") != "1":
        test_tools()

    test_numpy()

    config = ocio.GetCurrentConfig()
    print("Config: ", config)
    colorSpaceNames = [cs.getName() for cs in config.getColorSpaces()]
    print("Color Spaces: ", colorSpaceNames)

    # Print version
    print("OpenImageIO Version: ", oiio.__version__)
    print("OpenColorIO Version: ", ocio.__version__)


if __name__ == "__main__":
    main()
