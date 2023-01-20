import pydicom
from pydicom.dataset import Dataset
from pydicom.pixel_data_handlers.util import convert_color_space
import numpy as np
from PIL import Image
import io

# Read in a multi-frame DICOM file and write it back out (sounds easy, right?!).

# Basic idea for multi-frame writing from here:
# https://stackoverflow.com/questions/58518357/how-to-create-jpeg-compressed-dicom-dataset-using-pydicom

# Read DICOM input file
ds = pydicom.dcmread('./input-geom-jpeg.dcm')
print(ds.file_meta)

# Give a PlanarConfiguration to satisfy the decompression code
# Only needed for these generated datasets, most normal files should have this
ds.PlanarConfiguration = 0
arr = ds.pixel_array

# If reading in YBR color space (GDCM), need to convert back to RGB
# https://github.com/pydicom/pydicom/issues/826#issuecomment-519740593
#arr = convert_color_space(arr, 'YBR_FULL', 'RGB')
num_frames = ds.NumberOfFrames

# Convert to PIL
imlist = []
for i in range(num_frames):   # convert the multiframe image into RGB of single frames (Required for compression)
    tmp = arr[i]
    imlist.append(Image.fromarray(tmp))

# Save the multipage tiff with jpeg compression
f = io.BytesIO()
imlist[0].save(f, format='tiff', append_images=imlist[1:], save_all=True, compression='jpeg')
# Current settings match original image; can save at higher quality with quality=100, subsampling=0
# The BytesIO object cursor is at the end of the object, so tell it to go back to the front
f.seek(0)
img = Image.open(f)

# Get each one of the frames converted to even numbered bytes
img_byte_list = []
for i in range(num_frames):
    try:
        img.seek(i)
        with io.BytesIO() as output:
            img.save(output, format='jpeg')
            img_byte_list.append(output.getvalue())
    except EOFError:
         # Not enough frames in img
         break

ds.PixelData = pydicom.encaps.encapsulate([x for x in img_byte_list])

# If JPEG-LS dataset was modified in pydicom, must change output type to JPEG 
# Pydicom reads other JPEG flavors, but support for writing JPEG-LS, etc appears to be missing
# Weasis will read a conflicting DICOM/JPEG file type without complaining, but other viewers
# like Aliza will not.
ds.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.50'
ds.LossyImageCompression = '01'
ds.LossyImageCompressionRatio = 1
ds.LossyImageCompressionMethod = 'ISO_10918_1'
ds.DerivationDescription = 'PyDICOM JPEG-LS lossless to JPEG'

ds.save_as("output-geom-jpeg.dcm", write_like_original=False)