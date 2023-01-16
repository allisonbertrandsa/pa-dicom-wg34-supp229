This project is for the development of Photoacoustic/Optoacoustic DICOM
files (PA/OA).  This work follows DICOM WG-34 Supplement 229,
https://www.dicomstandard.org/news-dir/current/index.html#sup229

Current contents include:
- Example files
- Temporary DICOM tag assignments (final tags not yet assigned)
- Dictionary Files
- Utilities for modifying DICOM datasets to use the proposed PA attributes. 

Examples for Photoacoustic (PA) DICOM Supplement 229
----------------------------------------------------------
Directories named "XYZ-PA" have been converted to full PA modality images.  
Because some tools may not deal well with an unknown modality, a second
directory named "XYZ" is also included with ultrasound in place of PA for
Modality, SOP Class UID, and US Image Description Sequence.

Example Files Known Compatibility
----------------------------------
- Aliza (https://github.com/AlizaMedicalImaging) - Will read the XYZ files.  
  As of 15-Jan-23 Aliza source update - WILL read the XYZ-PA files!  
  Displays PA and US files as single-frame slices over time by default. To 
  display files as a volume, enable the "Skip 'Dimension Organization' in 
  enhanced multi-frame IODs" and possibly disable "Sort frames in enhanced 
  multi-frame IODs by IPP/IOP" prior to loading the data. 
- Slicer - Will read the XYZ files.  Will not read the XYZ-PA files.  Will 
  generate volumes of US and PA files.
- Weasis - Reads XYZ-PA and XYZ files.  Displays all files as a stack of images.
- dciodvfy - Will partially read the XYZ-PA files.  Will read the XYZ files. 
- dcmdump - Reads XYZ-PA and XYZ files.

New DICOM Tags
---------------
Temporary private tags are used for new PA attributes in these examples
until permanent tag assignment. See: 
- Private_Tag_Model_PC_v1.xlsx for tag and code temporary assignments
- private.dic for a DCMTk private dictionary which will translate tag names
for DCMTk tools such as dcmdump.  Note that dicom.dic is the standard DCMTk
example dictionary, copied from the share\dcmtk folder where DCMTk is 
installed on your system. Set the environment variable per your system, for 
example, export DCMDICTPATH="./dicom.dic;./private.dic" 

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

PyDICOM Helper Commands
------------------------------
utils/pa_dicom_private_tags.py contains example commands from the PyDICOM library
which were used to convert a file in a format similar to Enhanced US Volume 
(3DUS) to the proposed PA format and attributes.  These commands should be 
cherry-picked and run as needed; the commands are not set up as a 
full-fledged script.

Related Projects & Organizations
---------------------------------
https://www.dicomstandard.org/activity/wgs/wg-34 - Working Group contact
https://senomedical.com/ - Example 1 & Example 2 were provided by Seno Medical
https://github.com/IPASC - Metadata for the PA DICOM standard was derived from
IPASC metadata

