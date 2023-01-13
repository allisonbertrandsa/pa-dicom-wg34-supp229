import pydicom
import random #for generating fake data
from decimal import * #for correct precision for fractional DateTime DT

# Commands to add PA DICOM Proposed Tags
#
# These commands should be cherry-picked and run as needed - not set up
#  as a full-fledged script.
#
# 28-Dec-22: Tags added as private tags until permanent assignment.
#   See: Private_Tag_Model_PC_v1.xlsx for tag and code temporary assignments.
#
#   Private dictionary for DCMTk (like dcmdump) can be added using the 
#    PA private.dic dictionary file and the following environment variable 
#    dicom.dic is the standard DCMTk example dictionary, copied from the
#    share\dcmtk folder where DCMTk is installed on your system.
#   export DCMDICTPATH="./dicom.dic;./private.dic" 
#
#   For pydicom, the following command adds to private dictionary, will translate
#   when printing tag.
#>>> pydicom.datadict.add_private_dict_entry('WG-34 PA Proposed Tags',0x34011005,'FL','ExcitationWavelength')
#>>> block[0x05]
#(3401, 1005) [ExcitationWavelength]              FL: 1
#

# Assumes starting with a file in a format similar to Enhanced US Volume (3DUS).
ds = pydicom.dcmread('non_PA_file.dcm')
# Some tags may need to be deleted to make the file compatible.  Not covered here.
# Recommend working with dciodvfy and several viewers to see what might be missing.

# PA Dimension Indexing
# Temporal Position Time Offset (0020,930d) 
# Image Position (Volume) (0020,9301)
# PA Dimension Index Id (gggg,ee93) => temporary private tag = (3401,1093) 
ds.DimensionIndexSequence[0].DimensionIndexPointer=pydicom.tag.Tag((0x0020,0x930d))
ds.DimensionIndexSequence[0].FunctionalGroupPointer=pydicom.tag.Tag((0x0020,0x9310))
ds.DimensionIndexSequence[1].DimensionIndexPointer=pydicom.tag.Tag((0x0020,0x9301))
ds.DimensionIndexSequence[1].FunctionalGroupPointer=pydicom.tag.Tag((0x0020,0x930e))
ds.DimensionIndexSequence[2].DimensionIndexPointer=pydicom.tag.Tag((0x3401,0x1093))
del ds.DimensionIndexSequence[2].FunctionalGroupPointer

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

ds.DimensionOrganizationSequence[0].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[0].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[1].DimensionOrganizationUID = dim_uid
ds.DimensionIndexSequence[2].DimensionOrganizationUID = dim_uid

ds.FrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.3.111.")
#ds.SynchronizationFrameOfReferenceUID = '1.2.840.10008.15.1.1'
ds.VolumeFrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.3.222.")

#pydicom save_as with write_like_original=False sets MediaStorageSOPInstanceUID 
# - Trying to set MediaStorageSOPInstanceUID to SOPInstanceUID explicitely causes an
#   error when saving file. 

# This example is a manually scanned acquisition.
#  There are 449 frames acquired, each at a different image position and time
#  There is one PA Dimension Index ID for the entire image
padimidx = 1
dataframes = 449

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

start = Decimal('20221228150251.105768')
for i in range(dataframes):
    ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].DimensionIndexValues=[i+1,i+1,padimidx]
    ds.PerFrameFunctionalGroupsSequence[i].PlanePositionVolumeSequence[0].ImagePositionVolume=[1,1,i*0.5]
    ds.PerFrameFunctionalGroupsSequence[i].TemporalPositionSequence[0].TemporalPositionTimeOffset = i*0.01
    ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameAcquisitionDateTime = str(start + Decimal(ds.PerFrameFunctionalGroupsSequence[i].TemporalPositionSequence[0].TemporalPositionTimeOffset).quantize(Decimal('.000001'), rounding=ROUND_HALF_DOWN))
    ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameReferenceDateTime = str(Decimal(ds.PerFrameFunctionalGroupsSequence[i].FrameContentSequence[0].FrameAcquisitionDateTime) + Decimal('0.05'))
    ds.PerFrameFunctionalGroupsSequence[i].ImageDataTypeSequence[0].DataType = 'TISSUE_INTENSITY'

#### Private Tags
# PyDICOM has some functions to help handle private tags, for example:
# >>> block = ds.private_block(0x3401, "WG-34 PA Proposed Tags", create=True)
# >>> block.add_new(0x93,'FL',1)
# >>> block[0x93].value
# 1
# >>> ds[0x34011093]
# (3401, 1093) Private tag data                    FL: 1
# After re-opening DICOM file, must redeclare (but not create) block:
# block = ds.private_block(0x3401, "WG-34 PA Proposed Tags")
# >>> block[0x93]
# (3401, 1093) [PADimensionIndexID]                FL: 1.0
# >>> ds[0x34011093]
# (3401, 1093) [PADimensionIndexID]                FL: 1.0

#### PA Private Tags (Global, 0x3401)
block = ds.private_block(0x3401, "WG-34 PA Proposed Tags", create=True)

#### PADimensionIndexID FL  1   (3401, 1093)
block.add_new(0x93,'FL',1)

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
ds[0x34011017].value[0].add_new((0x3431,0x1098),'UL',10)
ds[0x34011017].value[0].add_new((0x3431,0x1097),'UL','')
ds[0x34011017].value[0].add_new((0x3431,0x1096),'UL','')
ds[0x34011017].value[0].add_new((0x3431,0x1095),'UL','')

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
#### PAImageFrameTypeSequence   SQ  1   (3411, 10a1)
# for i in range(dataframes):
    # del ds.PerFrameFunctionalGroupsSequence[i].USImageDescriptionSequence[0]
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
dataframes=449
for i in range(dataframes):
    pfg=ds.PerFrameFunctionalGroupsSequence[i]
    pfg.add_new((0x3411,0x0010),'LO','WG-34 PA Per-Frame Seq')
    pfg.add_new((0x3411,0x1001),'SQ',[])
    pfg[0x34111001].value.append(pydicom.dataset.Dataset())
    #Private Creator required inside sequence
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

# Explicit so the private VRs are written to the file    
ds.is_implicit_VR = False

ds.save_as('PA_attr_output.dcm', write_like_original=False)

