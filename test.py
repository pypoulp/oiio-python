import OpenImageIO as oiio
import PyOpenColorIO as ocio

print("OpenImageIO Version: ", oiio.__version__)
print("OpenColorIO Version: ", ocio.__version__)

spec = oiio.ImageSpec()
