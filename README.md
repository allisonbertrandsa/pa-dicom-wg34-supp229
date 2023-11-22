This project is for the development of Photoacoustic/Optoacoustic DICOM
files (PA/OA).  This work follows DICOM WG-34 Supplement 229,
https://www.dicomstandard.org/news-dir/current/index.html#sup229

Current contents include:
- Example files
  - Final tags and codes assigned with DICOM 2023c release
- Dictionary Files for Letter Ballot version
- Utilities for modifying DICOM datasets to use the PA attributes. 

Revision History
-----------------
- 22-Nov-23: Update to Hanging Protocol example to use PA ImageDataTypeCodeSequence
- 31-Oct-23: Examples and script updated after release of PA IOD support in dciodvfy and other dicom3tools (tested with dicom3tools_winexe_1.00.snapshot.20231025083157)
- 20-Jul-23: Photoacoustic IOD (Supplement 229) released with DICOM 2023c. Examples and encap_PNG_to_PA.py util updated.
- 85e6027 - New Community example file from PhotoSound  
- After pa-dicom-wg34-supp229 72a817f - Letter Ballot version
  - PADimensionIndexID (FL) changed to PAReconstructionIndex (UL) 
  - Types for the TransducerResponseSequence changed from UL to FL
  - ExcitationWavelength was added as a required tag in 
  PAExcitationCharacteristicsSequence
- pa-dicom-wg34-supp229 72a817f - Public Comment version

Examples for Photoacoustic (PA) DICOM Supplement 229
----------------------------------------------------------
Directories named "XYZ-PA" have been converted to full PA modality images.  
Because some tools may not deal well with a new modality, a second
directory named "XYZ-US_modality" is also included with ultrasound in place of PA for
Modality, SOP Class UID, and US Image Description Sequence. 

Example Files Known Compatibility (as of Letter Ballot)
------------------------------------------------------
- Aeskulap (Debian, 2007), reads XYZ-PA as stack of frames.
- Aliza (https://github.com/AlizaMedicalImaging) - Supports the 2023c PA IOD. Will also read the XYZ files. Dictionary includes PA attributes. 
  Displays PA and US files as single-frame slices over time by default. To 
  display files as a volume, enable the "Skip 'Dimension Organization' in 
  enhanced multi-frame IODs" and possibly disable "Sort frames in enhanced 
  multi-frame IODs by IPP/IOP" prior to loading the data. 
- MedDream-DICOM-Viewer-8.1.0 - Will read the XYZ files.  Will read the Raw XYZ-PA file, but gives an undefined error on the Processed XYZ-PA file (TBR).
- Onis 3.0.3 - Reads XYZ-PA and XYZ files.  Displays all files as a stack of frames.
- Slicer - Will read the XYZ files.  Will not read the XYZ-PA files.  Will 
  generate volumes of US and PA files.
- Visus JiveX Viewer - Reads XYZ-PA and XYZ files.  Displays all files as a stack of frames.
- Weasis - Reads XYZ-PA and XYZ files.  Displays all files as a stack of frames. Dictionary includes PA attributes.
- dicom3tools including dciodvfy - Reads XYZ-PA files (2023c).  Will read the XYZ files. 
- dcmdump (dcmtk tools) - Reads XYZ-PA and XYZ files, but not yet supporting 2023c full PA definitions.

PA DICOM Tags
---------------
Temporary private tags are no longer in use for new PA attributes since official numbers have been assigned.
For information about what changed in the tags and codes since the Letter Ballot examples, see the yellow highlighted cells in Tag_updates_PC_to_FT_2023c.xlsx

See Supplement 229 for diagrams of the following examples.  Supplement 229
also includes a PA tomographic example (Example 3) which is TBD in this 
data set.

Example 1 PA Standalone Image
-------------------------------
Two PA files, each with data from a different PA wavelength.  Both PA
wavelengths were acquired for each frame of a freehand scan of one
target.

Example 2 PAUS Coupled Image
-------------------------------
Two PA files and one ultrasound file.  Two PA wavelengths and ultrasound were 
acquired for each frame of a freehand scan of one target.  One PA file 
contains data from one wavelength and the second PA file contains data from
two wavelengths combined algorithmically during the acquisition process.

Community Examples
------------------------------
Examples provided by the community as proof-of-concept of the PA standard.
- Not yet updated to 2023c final tags & codes.

PyDICOM Helper Commands
------------------------------
- utils/encap_PNG_to_PA.py is a basic example script which reads all PNG files
in the local directory and write them to a PA file.  It has options for scaling and color 
conversion (RGBA->RGB or RGBA->MONOCHROME2).  
- utils/pa_dicom_private_tags.py contains example commands from the PyDICOM library
which were used to convert a file in a format similar to Enhanced US Volume 
(3DUS) to the proposed PA format and attributes.  These commands should be 
cherry-picked and run as needed; the commands are not set up as a 
full-fledged script.

Related Projects & Organizations
---------------------------------
- https://www.dicomstandard.org/activity/wgs/wg-34 - Working Group contact
- https://senomedical.com/ - Example 1 & Example 2 were provided by Seno Medical
- https://www.photosound.com/ - Provided example file, see examples/Community/PhotoSound
- https://github.com/IPASC - Metadata for the PA DICOM standard was derived from
IPASC metadata

