import pydicom
from pydicom.dataset import Dataset
import numpy as np
from PIL import Image
import io
import os

from pydicom.uid import generate_uid, JPEGExtended
from pydicom._storage_sopclass_uids import SecondaryCaptureImageStorage
import random #for generating fake data
from decimal import * #for correct precision for fractional DateTime DT

# Reads all PNG files in the local directory and write them to a PA file.
# If all PNG files are not the same size, program will exit.
# Prior to running:
# - Update output_file name.
# - Update color for color or monochrome output.
# - Update resize_img, resize_rows, resize_cols if scaling images.
# - Update any DICOM tags of interest (name, date, UIDs, etc).

# Original idea for writing:
# https://stackoverflow.com/questions/58518357/how-to-create-jpeg-compressed-dicom-dataset-using-pydicom

output_file = "oacombined-col-trsp-pa.dcm"

color = True
if color:
    print("Writing as YBR_FULL_422.")
else:
    print("Writing as MONOCHROME2.")

# If resizing, set to dimensions of smaller data set
resize_img = False
# Currently these are the OA dataset image dimensions
resize_rows = 384
resize_cols = 480
resize_dims = (resize_cols, resize_rows)

if resize_img:
    print("Resizing image to less than or equal to {} rows by {} cols.".format(resize_rows,resize_cols))

ds = Dataset()
ds.is_little_endian = True
ds.is_implicit_VR = True
# First temporarily as 3DUS, then convert to PA
# Enhanced US Volume Storage
ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.6.2"
ds.Modality = "US"

# Set/add some required tags
ds.PatientName="PA^Frames"
ds.ManufacturerModelName="Test"
ds.StudyDescription=ds.ManufacturerModelName
ds.SeriesDescription='PA Multiframe'
ds.PatientID="20221228-1"
ds.SeriesNumber=1
ds.StudyID="2022122802"
ds.PatientBirthDate=""
ds.PatientSex=""
ds.ReferringPhysicianName=""
ds.AccessionNumber=""
ds.Laterality=""
ds.PositionReferenceIndicator=""
ds.SynchronizationTrigger="NO TRIGGER"
ds.AcquisitionTimeSynchronized="N"
ds.Manufacturer="Seno"
ds.ManufacturerModelName="Test PA"
ds.DeviceSerialNumber="Any"
ds.SoftwareVersions="20221228-1"
ds.InstanceNumber=1
ds.PatientOrientation=""
ds.BurnedInAnnotation="NO"
ds.Laterality = 'L'
ds.AcquisitionDateTime='20221228150251.105768'
ds.StudyDate='20221228'
ds.ContentDate='20221228'
ds.StudyTime='150115'
ds.ContentTime='150251'

ds.PlanarConfiguration = 0
if color:
    ds.SamplesPerPixel = 3
else:
    ds.SamplesPerPixel = 1
ds.BitsAllocated = 8
ds.BitsStored = 8
ds.HighBit = 7
ds.PixelRepresentation = 0
if color:
    ds.PhotometricInterpretation = "YBR_FULL_422"
else: 
    ds.PhotometricInterpretation = "MONOCHROME2"

# Set up PA attributes 
ds.DimensionIndexSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.DimensionIndexSequence[0].DimensionIndexPointer=pydicom.tag.Tag((0x0020,0x930d))
ds.DimensionIndexSequence[0].FunctionalGroupPointer=pydicom.tag.Tag((0x0020,0x9310))
ds.DimensionIndexSequence.append(pydicom.dataset.Dataset())
ds.DimensionIndexSequence[1].DimensionIndexPointer=pydicom.tag.Tag((0x0020,0x9301))
ds.DimensionIndexSequence[1].FunctionalGroupPointer=pydicom.tag.Tag((0x0020,0x930e))
ds.DimensionIndexSequence.append(pydicom.dataset.Dataset())
ds.DimensionIndexSequence[2].DimensionIndexPointer=pydicom.tag.Tag((0x3401,0x1093))

#Correct UIDs as needed
#If also writing US files, ensure PA and US files have different 
# Dimension Organization UIDs from eachother
##Reuse study UID for all files
s_uid = pydicom.uid.generate_uid(prefix="1.2.3.123.")
#Reuse dimension UID for PA files (change for US files)
dim_uid = pydicom.uid.generate_uid(prefix="1.2.3.333.")

ds.SOPInstanceUID = pydicom.uid.generate_uid(prefix="1.2.3.123.")
ds.StudyInstanceUID = s_uid
ds.SeriesInstanceUID = pydicom.uid.generate_uid(prefix="1.2.3.123.")
ds.fix_meta_info()

ds.DimensionOrganizationSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.DimensionOrganizationSequence[0].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[0].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[1].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[2].DimensionOrganizationUID = dim_uid

ds.FrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.3.111.")
ds.VolumeFrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.3.222.")

# Convert to PIL
imlist = []

i=0
# Single frames required for compression
for file in os.listdir("./"):
    if file.endswith(".png"):
        img_file = os.path.join("./", file)
        jpg_img = Image.open(img_file)
        
        if resize_img:
            # Resize image in place to max of resize_dims (aspect ration maintained)
            # LANCZOS moves to Image.Resampling in later PIL versions.  Humph.
            jpg_img.thumbnail(resize_dims, Image.LANCZOS)
        
        if i == 0:
            # Read dimensions of first image
            img_cols, img_rows = jpg_img.size

        else:
            # If dimensions change, squawk
            tc, tr = jpg_img.size
            if (tc != img_cols) or (tr != img_rows):
                print("ERROR - Image dimensions changed from {},{} to {},{} in file {}".format(img_cols,img_rows,tc,tr,img_file))
                exit()
        
        if color:
            # Remove Alpha Channel if RGBA  
            if jpg_img.mode in ("RGBA", "P"): 
                jpg_img = jpg_img.convert("RGBA")
                new_img = Image.new("RGBA",jpg_img.size,"BLACK")
                new_img.paste(jpg_img, mask=jpg_img)
                jpg_img = new_img.convert("RGB")
        else:
            # Convert to monochrome
            jpg_img = jpg_img.convert("L")
        
        imlist.append(jpg_img)
        i=i+1

print("Number of frames: {}".format(i))

# Rows, Cols, Number of frames from number of PNG files read in directory
ds.Rows = img_rows
ds.Columns = img_cols
ds.NumberOfFrames = num_frames = i

# More PA attributes
#  For this example each frame is assumed to be at a different image position and time
#  There is one PA Reconstruction Index for the entire image
padimidx = 1

# Script hints:
# PyDICOM: must ADD sequences if not already present:
#     mySequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
# By convention, DICOM sequences are indexed starting from zero
# By convention, DICOM IDs and indexes are indexed starting from one

ds.ImageType=['ORIGINAL','PRIMARY','VOLUME','NONE']

# Set per-frame dimension values; modify as appropriate for acquisition geometry
# DT - DICOM DateTime VR, YYYYMMDDHHMMSS.FFFFFF
# - FFFFFF - fractional second, one millionth of a second
# - One millisecond is 0.001000

start = Decimal('20230214150251.105768')

pfg = ds.PerFrameFunctionalGroupsSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])

for i in range(num_frames):
    # Create one per-frame group per frame
    if i>0: 
        pfg.append(pydicom.dataset.Dataset())

    pfg[i].PlanePositionVolumeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
    pfg[i].FrameContentSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
    pfg[i].TemporalPositionSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
    pfg[i].ImageDataTypeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])

    pfg[i].FrameContentSequence[0].DimensionIndexValues=[i+1,i+1,padimidx]
    pfg[i].PlanePositionVolumeSequence[0].ImagePositionVolume=[1,1,i*0.5]
    pfg[i].TemporalPositionSequence[0].TemporalPositionTimeOffset = i*0.01
    pfg[i].FrameContentSequence[0].FrameAcquisitionDateTime = str(start + Decimal(ds.PerFrameFunctionalGroupsSequence[i].TemporalPositionSequence[0].TemporalPositionTimeOffset).quantize(Decimal('.000001'), rounding=ROUND_HALF_DOWN))
    pfg[i].FrameContentSequence[0].FrameReferenceDateTime = str(Decimal(ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameAcquisitionDateTime) + Decimal('0.05'))
    pfg[i].ImageDataTypeSequence[0].DataType = 'TISSUE_INTENSITY'

#### PA Private Tags (Global, 0x3401)
block = ds.private_block(0x3401, "WG-34 PA Proposed Tags", create=True)

#### PAReconstructionIndex UL  1   (3401, 1093)
block.add_new(0x93,'UL',1)

#### ExcitationWavelengthSequence   SQ  1   (3401, 1094)
ds.add_new((0x3401,0x1094),'SQ',[])
ds[0x34011094].value.append(pydicom.dataset.Dataset())
#Private Creator required inside sequence dataset
ds[0x34011094].value[0].add_new((0x3441,0x0010),'LO','WG-34 PA Excitation WL')
ds[0x34011094].value[0].add_new((0x3441,0x1005),'FL',757.0)
ds[0x34011094].value.append(pydicom.dataset.Dataset())
#Private Creator required inside sequence dataset
ds[0x34011094].value[1].add_new((0x3441,0x0010),'LO','WG-34 PA Excitation WL')
ds[0x34011094].value[1].add_new((0x3441,0x1005),'FL',1064.0)

#### IlluminationTranslationFlag    CS  1   (3401, 1092)
block.add_new(0x92,'CS','NO')

#### IlluminationTypeCodeSequence   SQ  1   (3401, 1006)
# Code Value    (0008,0100) SH  0006    103401
# Coding Scheme Designator  (0008,0102) SH  0004    DCM
# Code Meaning  (0008,0104) LO  0016    Single-side illumination
ds.add_new((0x3401,0x1006),'SQ',[])
ds[0x34011006].value.append(pydicom.dataset.Dataset())
ds[0x34011006].value[0].add_new((0x0008,0x0100),'SH','103401')
ds[0x34011006].value[0].add_new((0x0008,0x0102),'SH','DCM')
ds[0x34011006].value[0].add_new((0x0008,0x0104),'LO','Single-side illumination')

#### AcousticCouplingMediumFlag CS  1   (3401, 1099)
block.add_new(0x99,'CS','YES')

#### AcousticCouplingMediumCodeSequence SQ  1   (3401, 1007)
ds.add_new((0x3401,0x1007),'SQ',[])
ds[0x34011007].value.append(pydicom.dataset.Dataset())
ds[0x34011007].value[0].add_new((0x0008,0x0100),'SH','1004163002')
ds[0x34011007].value[0].add_new((0x0008,0x0102),'SH','SCT')
ds[0x34011007].value[0].add_new((0x0008,0x0104),'LO','Ultrasound Coupling Gel')

#### CouplingMediumTemperature  FL  1   (3401, 1008)
block.add_new(0x08,'FL',30)

#### TransducerResponseSequence SQ  1   (3401, 1017)
ds.add_new((0x3401,0x1017),'SQ',[])
ds[0x34011017].value.append(pydicom.dataset.Dataset())
#Private Creator required inside sequence
ds[0x34011017].value[0].add_new((0x3431,0x0010),'LO','WG-34 PA Transducer Response')
ds[0x34011017].value[0].add_new((0x3431,0x1098),'FL',10)
ds[0x34011017].value[0].add_new((0x3431,0x1097),'FL','')
ds[0x34011017].value[0].add_new((0x3431,0x1096),'FL','')
ds[0x34011017].value[0].add_new((0x3431,0x1095),'FL','')

#### TransducerTechnologySequence   SQ  1   (3401, 1010)
ds.add_new((0x3401,0x1010),'SQ',[])
ds[0x34011010].value.append(pydicom.dataset.Dataset())
ds[0x34011010].value[0].add_new((0x0008,0x0100),'SH','103413')
ds[0x34011010].value[0].add_new((0x0008,0x0102),'SH','DCM')
ds[0x34011010].value[0].add_new((0x0008,0x0104),'LO','Piezocomposite Transducer')

#### SoundSpeedCorrectionMechanismCodeSequence  SQ  1   (3401, 1014)
# Code Sequence Macro
# ObjectSoundSpeed  FL  1   (3421, 1015)
ds.add_new((0x3401,0x1014),'SQ',[])
ds[0x34011014].value.append(pydicom.dataset.Dataset())
ds[0x34011014].value[0].add_new((0x0008,0x0100),'SH','103416')
ds[0x34011014].value[0].add_new((0x0008,0x0102),'SH','DCM')
ds[0x34011014].value[0].add_new((0x0008,0x0104),'LO','Uniform Speed of Sound Correction')
#Private Creator required inside sequence
ds[0x34011014].value[0].add_new((0x3421,0x0010),'LO','WG-34 PA Sound Speed')
ds[0x34011014].value[0].add_new((0x3421,0x1015),'FL',1480.0)

#### Per-Frame Updates

# US Image Description Sequence has the same attributes as PA Image Frame Type Sequence
# Leaving the US group in place of the PA group temporarily - may impact viewers if removed
#>>> ds.PerFrameFunctionalGroupsSequence[0].USImageDescriptionSequence[0]
#(0008, 9007) Frame Type                          CS: ['ORIGINAL', 'PRIMARY', 'VOLUME', 'NONE']
#(0008, 9206) Volumetric Properties               CS: 'VOLUME'
#(0008, 9207) Volume Based Calculation Technique  CS: 'NONE'
#
for i in range(num_frames):
    ds.PerFrameFunctionalGroupsSequence[i].USImageDescriptionSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
    pfg=ds.PerFrameFunctionalGroupsSequence[i].USImageDescriptionSequence[0]
    pfg.FrameType = ['ORIGINAL','PRIMARY','VOLUME','NONE']
    pfg.VolumetricProperties = 'VOLUME'
    pfg.VolumeBasedCalculationTechnique = 'NONE'

for i in range(num_frames):
    ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameAcquisitionDuration = 100

#### PAImageFrameTypeSequence   SQ  1   (3411, 10a1)
# for i in range(num_frames):
    # pfg=ds.PerFrameFunctionalGroupsSequence[i]
    # pfg.add_new((0x3461,0x0010),'LO','WG-34 PA Image Frame Seq')
    # pfg.add_new((0x3461,0x10A1),'SQ',[])
    # pfg[0x346110A1].value.append(pydicom.dataset.Dataset())
    # pfg[0x346110A1].value[0].add_new((0x0008,0x9007),'CS',['ORIGINAL','PRIMARY','VOLUME','NONE'])
    # pfg[0x346110A1].value[0].add_new((0x0008,0x9206),'CS','VOLUME')
    # pfg[0x346110A1].value[0].add_new((0x0008,0x9207),'CS','NONE')

# ds.Modality='PA'
## SOPClassUID=PhotoacousticImageStorage in Supp229, temporary value of 1.2.840.10008.5.1.2.3.45
# ds.SOPClassUID='1.2.840.10008.5.1.2.3.45'

# Direct sequence additions example: https://github.com/pydicom/pydicom/issues/474

#### PA Private Tags (Per-Frame)

#### PAExcitationCharacteristicsSequence    SQ  1   (3411, 1001)
# ExcitationSpectralWidth   FL  1   (3451, 1002)
# ExcitationEnergy  FL  1   (3451, 1003)
# ExcitationPulseDuration   FL  1   (3451, 1004)

for i in range(num_frames):
    pfg=ds.PerFrameFunctionalGroupsSequence[i]
    pfg.add_new((0x3411,0x0010),'LO','WG-34 PA Per-Frame Seq')
    pfg.add_new((0x3411,0x1001),'SQ',[])
    pfg[0x34111001].value.append(pydicom.dataset.Dataset())
    #Private Creator required inside sequence
    pfg[0x34111001].value[0].add_new((0x3441,0x0010),'LO','WG-34 PA Excitation WL')
    pfg[0x34111001].value[0].add_new((0x3441,0x1005),'FL',757.0)
    pfg[0x34111001].value[0].add_new((0x3451,0x0010),'LO','WG-34 PA Per-Frame Tags')
    pfg[0x34111001].value[0].add_new((0x3451,0x1002),'FL',2+round(random.random(),2))
    pfg[0x34111001].value[0].add_new((0x3451,0x1003),'FL',11+round(random.random(),2))
    pfg[0x34111001].value[0].add_new((0x3451,0x1004),'FL',8+round(random.random(),2))

#### Position Measuring Device Used (0018,980C)
ds.PositionMeasuringDeviceUsed='FREEHAND'

#### Transducer Geometry Code Sequence  (0018,980D)
ds.TransducerGeometryCodeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.TransducerGeometryCodeSequence[0].CodeValue='125252'
ds.TransducerGeometryCodeSequence[0].CodingSchemeDesignator='DCM'
ds.TransducerGeometryCodeSequence[0].CodeMeaning='Linear ultrasound transducer geometry'

#### Reconstruction Algorithm Sequence  (0018,993D)
ds.ReconstructionAlgorithmSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.ReconstructionAlgorithmSequence[0].AlgorithmName='WaveLength1-Wavelength2-Relative'
ds.ReconstructionAlgorithmSequence[0].AlgorithmVersion='1.0.0'
ds.ReconstructionAlgorithmSequence[0].AlgorithmFamilyCodeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.ReconstructionAlgorithmSequence[0].AlgorithmFamilyCodeSequence[0].CodeValue='113961'
ds.ReconstructionAlgorithmSequence[0].AlgorithmFamilyCodeSequence[0].CodingSchemeDesignator='DCM'
ds.ReconstructionAlgorithmSequence[0].AlgorithmFamilyCodeSequence[0].CodeMeaning='Reconstruction Algorithm'

### Shared frame DICOM metadata
ds.FrameIncrementPointer = pydicom.tag.Tag((0x5200,0x9230)) #0x0020,0x0032))
ds.SharedFunctionalGroupsSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].SliceThickness="0.1"
ds.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing=[0.50251257030209, 0.5025125703020]
ds.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].SpacingBetweenSlices=0.50251257030209
ds.SharedFunctionalGroupsSequence[0].PlaneOrientationVolumeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.SharedFunctionalGroupsSequence[0].PlaneOrientationVolumeSequence[0].ImageOrientationVolume = [1, 0, 0, 0, 1, 0]


# Save the multipage tiff with jpeg compression
f = io.BytesIO()
imlist[0].save(f, format='tiff', append_images=imlist[1:], save_all=True, compression='jpeg')
# The BytesIO object cursor is at the end of the object, so I need to tell it to go back to the front
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

# From web example, but doesn't seem to change result here
#ds['PixelData'].is_undefined_length = True

# is_implicit_VR must be True above for the fix_meta_info() call
ds.is_implicit_VR = False
ds.LossyImageCompression = '01'
ds.LossyImageCompressionRatio = 10 # default jpeg

# JPEG Lossy Compression [ISO/IEC 10918-1]
ds.LossyImageCompressionMethod = 'ISO_10918_1'

# JPEG Baseline (Processes 2 & 4):
# Default Transfer Syntax for Lossy JPEG 12-bit Image Compression
# Process 4 only)
ds.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.51'

ds.save_as(output_file, write_like_original=False)
print("Output file: {}".format(output_file))
