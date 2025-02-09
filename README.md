# qure.ai_dicom_ETl-and-summary
A modular pipeline to process medical imaging data (DICOM format) from the LIDC-IDRI dataset. Includes data ingestion, metadata extraction, file organization, database storage, and reporting with summary statistics and visualizations

*key feature:*

1. Download and validate DICOM files from a dataset directory or S3 bucket
2. Extract metadata such as Patient ID, Study Instance UID, and Slice Thickness
3. Organize DICOM files into a logical folder structure
4. Store metadata in an SQLite database
5. Generate summary statistics and visualizations

*Table Description:*
Patients Table-

This table contains patient-level metadata

Studies Table-

This table stores metadata about studies conducted for each patient
Each study is linked to a patient through the PatientID foreign key

Series Table -

This table stores detailed metadata for each series in a study
Each series is linked to a study through the StudyInstanceUID foreign key

Summary Report:
INFO:root:Total DICOM files found: 2696
INFO:root:Valid DICOM files: 2696
Summary Statistics:
- Total Studies: 10
- Total Slices: 10
- Average Slices per Study: 1.00
- Slice Thickness: Min = 1.25, Max = 2.50, Mean = 1.75


