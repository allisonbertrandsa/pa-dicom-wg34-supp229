import pydicom
from pydicom.dataset import Dataset
import numpy as np
from PIL import Image
import io
import os

from natsort import natsorted #for sorting os dir with numbered files
from pydicom.uid import generate_uid, JPEGExtended
from pydicom._storage_sopclass_uids import SecondaryCaptureImageStorage
import random #for generating fake data
from decimal import * #for correct precision for fractional DateTime DT

# Reads all PNG files in the local directory and write them to a PA file.
# Based on DICOM 2023c release.
# If all PNG files are not the same size, program will exit.
# Prior to running:
# - Update output_file name.
# - Update color for color or monochrome output.
# - Update resize_img, resize_rows, resize_cols if scaling images.
# - Update any DICOM tags of interest (name, date, UIDs, etc).

# Original idea for writing:
# https://stackoverflow.com/questions/58518357/how-to-create-jpeg-compressed-dicom-dataset-using-pydicom

output_file = "oacombined-bw-pa-2023c.dcm"

color = False
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

ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.6.3"
ds.Modality = "PA"

# May want to write as 3DUS for tools not yet supporting PA
# Enhanced US Volume Storage
#ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.6.2"
#ds.Modality = "US"

# Set/add some required tags
ds.PatientName="PA^Frames"
ds.ManufacturerModelName="Test"
ds.StudyDescription=ds.ManufacturerModelName
ds.SeriesDescription='PA Multiframe'
ds.PatientID="20230711-1"
ds.SeriesNumber=1
ds.StudyID="2023071102"
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
ds.SoftwareVersions="20230711-1"
ds.InstanceNumber=1
ds.PatientOrientation=""
ds.BurnedInAnnotation="NO"
ds.Laterality = 'L'
ds.AcquisitionDateTime='20230711150251.105768'
ds.StudyDate='20230711'
ds.ContentDate='20230711'
ds.StudyTime='150115'
ds.ContentTime='150251'

if color:
    ds.SamplesPerPixel = 3
    ds.PhotometricInterpretation = "YBR_FULL_422"
    ds.PixelPresentation = "TRUE_COLOR"
    # PlanarConfiguration only allowed if SamplesPerPixel GT 1
    ds.PlanarConfiguration = 0
    # TODO: TRUE_COLOR will also need ICC Profile
else: 
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelPresentation = "MONOCHROME"
    ds.PresentationLUTShape = "IDENTITY"

ds.VolumetricProperties = 'VOLUME'
ds.VolumeBasedCalculationTechnique = 'NONE'
ds.BitsAllocated = 8
ds.BitsStored = 8
ds.HighBit = 7
ds.PixelRepresentation = 0
ds.PositionMeasuringDeviceUsed='FREEHAND'

# PA Dimension Index Sequence 
ds.DimensionIndexSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
# Temporal Position Time Offset 
ds.DimensionIndexSequence[0].DimensionIndexPointer=pydicom.tag.Tag((0x0020,0x930d))
ds.DimensionIndexSequence[0].FunctionalGroupPointer=pydicom.tag.Tag((0x0020,0x9310))
ds.DimensionIndexSequence.append(pydicom.dataset.Dataset())
# Image Position (Volume)
ds.DimensionIndexSequence[1].DimensionIndexPointer=pydicom.tag.Tag((0x0020,0x9301))
ds.DimensionIndexSequence[1].FunctionalGroupPointer=pydicom.tag.Tag((0x0020,0x930e))
ds.DimensionIndexSequence.append(pydicom.dataset.Dataset())
# Image Data Type Sequence
ds.DimensionIndexSequence[2].DimensionIndexPointer=pydicom.tag.Tag((0x0018,0x9807))

#Correct UIDs as needed
#If also writing US files, ensure PA and US files have different 
# Dimension Organization UIDs from eachother
##Reuse study UID for all files
s_uid = pydicom.uid.generate_uid(prefix="1.2.3.123.")
# Reuse dimension UID for PA files (change for US files)
dim_uid = pydicom.uid.generate_uid(prefix="1.2.3.333.")
# Reuse synchronization UID if PA and US are connected
synch_uid = pydicom.uid.generate_uid(prefix="1.2.3.456.")

ds.SOPInstanceUID = pydicom.uid.generate_uid(prefix="1.2.3.123.")
ds.StudyInstanceUID = s_uid
ds.SeriesInstanceUID = pydicom.uid.generate_uid(prefix="1.2.3.123.")
ds.fix_meta_info()

ds.DimensionOrganizationType = "3D"
ds.DimensionOrganizationSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.DimensionOrganizationSequence[0].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[0].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[1].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[2].DimensionOrganizationUID = dim_uid

ds.FrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.3.111.")
ds.VolumeFrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.3.222.")

ds.SynchronizationFrameOfReferenceUID = synch_uid
ds.SynchronizationTrigger = "SOURCE"
ds.AcquisitionTimeSynchronized = "N"
# Acquisition Context Sequence - required even if empty
ds.add_new((0x0040,0x0555),'SQ',[])

# Convert to PIL
imlist = []

i=0
# Single frames required for compression
for file in natsorted(os.listdir("./")):
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

# C.8.24.2 Ultrasound Frame of Reference Module
# https://dicom.nema.org/medical/Dicom/current/output/chtml/part03/sect_C.8.24.2.html
ds.UltrasoundAcquisitionGeometry = "APEX"
x_offset = float(ds.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing[0])*ds.Columns/2
ds.ApexPosition = [x_offset,-5.0,0.0]
# https://dicom.nema.org/medical/Dicom/current/output/chtml/part03/sect_C.8.24.2.2.html
ds.VolumeToTransducerMappingMatrix = [0,0,0,x_offset,0,0,0,0,0,0,0,0,0,0,0,1]

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

start = Decimal('20230711150251.105768')

pfg = ds.PerFrameFunctionalGroupsSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])

#  For this example each frame is assumed to be at a different image position and time
#  There is one ImageDataTypeSequence Dimension Index for the entire image
padimidx = 1

for i in range(num_frames):
    # Create one per-frame group per frame
    if i>0: 
        pfg.append(pydicom.dataset.Dataset())
        
    # Add dimension index values for time and volume; the third index is a Shared 
    # Functional Group, constant for all frames (ImageDataTypeSequence)
    pfg[i].PlanePositionVolumeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
    pfg[i].FrameContentSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
    pfg[i].TemporalPositionSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])

    pfg[i].FrameContentSequence[0].DimensionIndexValues=[i+1,i+1,padimidx]
    pfg[i].PlanePositionVolumeSequence[0].ImagePositionVolume=[1,1,i*0.07]
    pfg[i].TemporalPositionSequence[0].TemporalPositionTimeOffset = i*0.01
    pfg[i].FrameContentSequence[0].FrameAcquisitionDateTime = str(start + Decimal(ds.PerFrameFunctionalGroupsSequence[i].TemporalPositionSequence[0].TemporalPositionTimeOffset).quantize(Decimal('.000001'), rounding=ROUND_HALF_DOWN))
    pfg[i].FrameContentSequence[0].FrameReferenceDateTime = str(Decimal(ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameAcquisitionDateTime) + Decimal('0.05'))
    
#### ExcitationWavelengthSequence   SQ  1   (0018,9825)
# ExcitationWavelength    FD   1   (0018,9826)
ds.add_new((0x0018,0x9825),'SQ',[])
# Two wavelengths for this example
ds[0x00189825].value.append(pydicom.dataset.Dataset())
ds[0x00189825].value[0].add_new((0x0018,0x9826),'FD',757.0)
ds[0x00189825].value.append(pydicom.dataset.Dataset())
ds[0x00189825].value[1].add_new((0x0018,0x9826),'FD',1064.0)

#### IlluminationTranslationFlag    CS  1   (0018,9828)
ds.add_new((0x0018,0x9828),'CS','NO')

#### IlluminationTypeCodeSequence   SQ  1   (0022,0016)
# Code Value    (0008,0100) SH  0006    103401
# Coding Scheme Designator  (0008,0102) SH  0004    DCM
# Code Meaning  (0008,0104) LO  0016    Single-side illumination
ds.add_new((0x0022,0x0016),'SQ',[])
ds[0x00220016].value.append(pydicom.dataset.Dataset())
ds[0x00220016].value[0].add_new((0x0008,0x0100),'SH','103401')
ds[0x00220016].value[0].add_new((0x0008,0x0102),'SH','DCM')
ds[0x00220016].value[0].add_new((0x0008,0x0104),'LO','Single-side illumination')

#### AcousticCouplingMediumFlag CS  1   (0018,9829)
ds.add_new((0x0018,0x9829),'CS','YES')

#### AcousticCouplingMediumCodeSequence SQ  1   (0018,982A)
ds.add_new((0x0018,0x982A),'SQ',[])
ds[0x0018982A].value.append(pydicom.dataset.Dataset())
ds[0x0018982A].value[0].add_new((0x0008,0x0100),'SH','1004163002')
ds[0x0018982A].value[0].add_new((0x0008,0x0102),'SH','SCT')
ds[0x0018982A].value[0].add_new((0x0008,0x0104),'LO','Ultrasound Coupling Gel')

#### AcousticCouplingMediumTemperature  FD  1   (0018,982B)
ds.add_new((0x0018,0x982B),'FD',30)

#### Transducer Geometry Code Sequence  (0018,980D)
ds.TransducerGeometryCodeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
ds.TransducerGeometryCodeSequence[0].CodeValue='125252'
ds.TransducerGeometryCodeSequence[0].CodingSchemeDesignator='DCM'
ds.TransducerGeometryCodeSequence[0].CodeMeaning='Linear ultrasound transducer geometry'

#### TransducerResponseSequence SQ  1   (0018,982C)
ds.add_new((0x0018,0x982C),'SQ',[])
ds[0x0018982C].value.append(pydicom.dataset.Dataset())
ds[0x0018982C].value[0].add_new((0x0018,0x982D),'FD',10)
ds[0x0018982C].value[0].add_new((0x0018,0x982E),'FD','')
ds[0x0018982C].value[0].add_new((0x0018,0x982F),'FD','')
ds[0x0018982C].value[0].add_new((0x0018,0x9830),'FD','')

#### TransducerTechnologySequence   SQ  1   (0018,9831)
ds.add_new((0x0018,0x9831),'SQ',[])
ds[0x00189831].value.append(pydicom.dataset.Dataset())
ds[0x00189831].value[0].add_new((0x0008,0x0100),'SH','130815')
ds[0x00189831].value[0].add_new((0x0008,0x0102),'SH','DCM')
ds[0x00189831].value[0].add_new((0x0008,0x0104),'LO','Piezocomposite Transducer')

#### SoundSpeedCorrectionMechanismCodeSequence  SQ  1   (0018,9832)
# Code Sequence Macro
# ObjectSoundSpeed  FD  1   (0018,9833)
ds.add_new(((0x0018,0x9832)),'SQ',[])
ds[0x00189832].value.append(pydicom.dataset.Dataset())
ds[0x00189832].value[0].add_new((0x0008,0x0100),'SH','130818')
ds[0x00189832].value[0].add_new((0x0008,0x0102),'SH','DCM')
ds[0x00189832].value[0].add_new((0x0008,0x0104),'LO','Uniform Speed of Sound Correction')
ds[0x00189832].value[0].add_new((0x0018,0x9833),'FD',1540)

# Direct sequence additions example: https://github.com/pydicom/pydicom/issues/474

#### Per-Frame Attributes

#### PhotoacousticExcitationCharacteristicsSequence    SQ  1   (0018,9821)
# ExcitationWavelength    FD   1   (0018,9826)
# ExcitationSpectralWidth   FD  1   (0018,9822)
# ExcitationEnergy  FD  1   (0018,9823)
# ExcitationPulseDuration   FD  1   (0018,9824)

for i in range(num_frames):
    ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameAcquisitionDuration = 100
    pfg=ds.PerFrameFunctionalGroupsSequence[i]
    pfg.add_new((0x0018,0x9821),'SQ',[])
    pfg[0x00189821].value.append(pydicom.dataset.Dataset())
    pfg[0x00189821].value[0].add_new((0x0018,0x9826),'FD',757.0)
    pfg[0x00189821].value[0].add_new((0x0018,0x9822),'FD',2+round(random.random(),2))
    pfg[0x00189821].value[0].add_new((0x0018,0x9823),'FD',11+round(random.random(),2))
    pfg[0x00189821].value[0].add_new((0x0018,0x9824),'FD',8+round(random.random(),2))
    pfg[0x00189821].value.append(pydicom.dataset.Dataset())
    pfg[0x00189821].value[1].add_new((0x0018,0x9826),'FD',1064.0)
    pfg[0x00189821].value[1].add_new((0x0018,0x9822),'FD',2+round(random.random(),2))
    pfg[0x00189821].value[1].add_new((0x0018,0x9823),'FD',11+round(random.random(),2))
    pfg[0x00189821].value[1].add_new((0x0018,0x9824),'FD',8+round(random.random(),2))

### Shared frame DICOM metadata
ds.SharedFunctionalGroupsSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
sfg = ds.SharedFunctionalGroupsSequence[0]
sfg.PixelMeasuresSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
sfg.PixelMeasuresSequence[0].SliceThickness = 0.089
sfg.PixelMeasuresSequence[0].PixelSpacing = [0.089, 0.089]
sfg.PixelMeasuresSequence[0].SpacingBetweenSlices = 0.089
sfg.PlaneOrientationVolumeSequence = pydicom.sequence.Sequence([pydicom.dataset.Dataset()])
sfg.PlaneOrientationVolumeSequence[0].ImageOrientationVolume = [1, 0, 0, 0, 1, 0]

### Shared frame PA attributes

### PhotoacousticImageFrameTypeSequence (0018,9835)
### FrameType (0008,9007)
### Table C.8-131. Common CT/MR and Photoacoustic Image Description Macro Attributes
sfg.add_new((0x0018,0x9835),'SQ',[])
sfg[0x00189835].value.append(pydicom.dataset.Dataset())
sfg[0x00189835].value[0].add_new((0x0008,0x9007),'CS',['ORIGINAL','PRIMARY','VOLUME','NONE'])
sfg[0x00189835].value[0].add_new((0x0008,0x9205),'CS',ds.PixelPresentation)
sfg[0x00189835].value[0].add_new((0x0008,0x9206),'CS','VOLUME')
sfg[0x00189835].value[0].add_new((0x0008,0x9207),'CS','NONE')

### ImageDataTypeSequence	SQ  1 (0018,9807)
### ImageDataTypeCodeSequence	SQ	1		(0018,9836)
sfg.add_new((0x0018,0x9807),'SQ',[])
sfg[0x00189807].value.append(pydicom.dataset.Dataset())
sfg[0x00189807].value[0].add_new((0x0018,0x9836),'SQ',[])
sfg[0x00189807].value[0][0x00189836].value.append(pydicom.dataset.Dataset())
sfg[0x00189807].value[0][0x00189836].value[0].add_new((0x0008,0x0100),'SH','110819')
sfg[0x00189807].value[0][0x00189836].value[0].add_new((0x0008,0x0102),'SH','DCM')
sfg[0x00189807].value[0][0x00189836].value[0].add_new((0x0008,0x0104),'LO','Blood Oxygenation Level')

# If using a custom code, recommend adding Coding Scheme Identification Sequence
# https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_8.2.html#sect_8.2
# ds.add_new((0x0008,0x0110),'SQ',[])
# ds[0x00080110].value.append(pydicom.dataset.Dataset())
# ds[0x00080110].value[0].add_new((0x0008,0x0102),'SH','99SENO')
# ds.CodingSchemeIdentifcationSequence[0]

### Reconstruction Algorithm Sequence  (0018,993D)
### Algorithm Family Code Sequence (0066,002F) 
### Algorithm Name (0066,0036)
### Algorithm Version (0066,0031)
sfg.add_new((0x0018,0x993D),'SQ',[])
sfg[0x0018993D].value.append(pydicom.dataset.Dataset())
sfg[0x0018993D].value[0].add_new((0x0066,0x0036),'LO','WaveLength1-Wavelength2-Relative')
sfg[0x0018993D].value[0].add_new((0x0066,0x0031),'LO','1.0.0')
sfg[0x0018993D].value[0].add_new((0x0066,0x002F),'SQ',[])
sfg[0x0018993D].value[0][0x0066002F].value.append(pydicom.dataset.Dataset())
sfg[0x0018993D].value[0][0x0066002F].value[0].add_new((0x0008,0x0100),'SH','130821')
sfg[0x0018993D].value[0][0x0066002F].value[0].add_new((0x0008,0x0102),'SH','DCM')
sfg[0x0018993D].value[0][0x0066002F].value[0].add_new((0x0008,0x0104),'LO','Spherical Back Projection')

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
