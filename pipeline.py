import os
import logging
import pydicom
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Step 1: Data Ingestion
# 1.1 Load Dataset
def load_dataset(dataset_dir):
    files = []
    for root, _, filenames in os.walk(dataset_dir):
        for filename in filenames:
            if filename.endswith('.dcm'):
                files.append(os.path.join(root, filename))
    logging.info(f"Total DICOM files found: {len(files)}")
    return files

# 1.2 Validation
def validate_files(files):
    valid_files = []
    for file in files:
        try:
            ds = pydicom.dcmread(file)
            valid_files.append(file)
        except Exception as e:
            logging.warning(f"Invalid DICOM file: {file}, Error: {e}")
    logging.info(f"Valid DICOM files: {len(valid_files)}")
    return valid_files

# Step 2: Metadata Extraction

# 2.1 DICOM Headers
def extract_metadata(files):
    metadata = []
    for file in files:
        try:
            ds = pydicom.dcmread(file)
            metadata.append({
                'PatientID': ds.get('PatientID', 'Unknown'),
                'StudyInstanceUID': ds.get('StudyInstanceUID', 'Unknown'),
                'SeriesInstanceUID': ds.get('SeriesInstanceUID', 'Unknown'),
                'SliceThickness': ds.get('SliceThickness', 'Unknown'),
                'PixelSpacing': ds.get('PixelSpacing', 'Unknown'),
                'StudyDate': ds.get('StudyDate', 'Unknown'),
                'FilePath': file
            })
        except Exception as e:
            logging.error(f"Error reading file {file}: {e}")
    return metadata

# 2.2 Transformation
def organize_files(metadata, base_dir):
    for entry in metadata:
        patient_dir = os.path.join(base_dir, entry['PatientID'])
        study_dir = os.path.join(patient_dir, entry['StudyInstanceUID'])
        series_dir = os.path.join(study_dir, entry['SeriesInstanceUID'])
        os.makedirs(series_dir, exist_ok=True)
        new_path = os.path.join(series_dir, os.path.basename(entry['FilePath']))
        os.rename(entry['FilePath'], new_path)

# Step 3: Data Storage

# 3.1 Design a Schema
def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            PatientID TEXT PRIMARY KEY NOT NULL,
            PatientName TEXT,
            PatientBirthDate TEXT
        )
    ''')
    
    # Create Studies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS studies (
            StudyInstanceUID TEXT PRIMARY KEY NOT NULL,
            PatientID TEXT NOT NULL,
            StudyDate TEXT,
            FOREIGN KEY (PatientID) REFERENCES patients(PatientID)
        )
    ''')
    
    # Create Series table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series (
            SeriesInstanceUID TEXT PRIMARY KEY NOT NULL,
            StudyInstanceUID TEXT NOT NULL,
            SliceThickness TEXT,
            PixelSpacing TEXT,
            FilePath TEXT NOT NULL,
            FOREIGN KEY (StudyInstanceUID) REFERENCES studies(StudyInstanceUID)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_patient_id ON studies(PatientID)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_study_uid ON series(StudyInstanceUID)')
    
    conn.commit()
    return conn


# 3.2 Populate the Schema
def insert_metadata(conn, metadata):
    cursor = conn.cursor()
    try:
        for entry in metadata:
            # Insert into patients table
            cursor.execute('''
                INSERT OR IGNORE INTO patients (PatientID) 
                VALUES (?)
            ''', (entry['PatientID'],))
            
            # Insert into studies table
            cursor.execute('''
                INSERT OR IGNORE INTO studies (StudyInstanceUID, PatientID, StudyDate)
                VALUES (?, ?, ?)
            ''', (entry['StudyInstanceUID'], entry['PatientID'], entry['StudyDate']))
            
            # Insert into series table
            cursor.execute('''
                INSERT OR IGNORE INTO series (SeriesInstanceUID, StudyInstanceUID, 
                                              SliceThickness, PixelSpacing, FilePath)
                VALUES (?, ?, ?, ?, ?)
            ''', (entry['SeriesInstanceUID'], entry['StudyInstanceUID'], 
                  entry['SliceThickness'], str(entry['PixelSpacing']), entry['FilePath']))
        
        # Committing
        conn.commit()
    except Exception as e:
        logging.error(f"Error inserting metadata: {e}")
        conn.rollback() 



# Step 4: Basic Reporting

# 4.1 Summary Statistics
def generate_summary(conn):
    cursor = conn.cursor()

    # Total number of unique studies
    cursor.execute("SELECT COUNT(DISTINCT StudyInstanceUID) FROM series")
    total_studies = cursor.fetchone()[0] or 0

    # Total number of slices
    cursor.execute("SELECT COUNT(*) FROM series")
    total_slices = cursor.fetchone()[0] or 0

    # Average number of slices per study
    cursor.execute("""
        SELECT AVG(slice_count) 
        FROM (
            SELECT COUNT(*) AS slice_count 
            FROM series 
            GROUP BY StudyInstanceUID
        )
    """)
    avg_slices_per_study = cursor.fetchone()[0] or 0.0

    # Distribution of slice thickness
    cursor.execute("SELECT SliceThickness FROM series WHERE SliceThickness IS NOT NULL AND SliceThickness != 'Unknown'")
    slice_thickness = [float(row[0]) for row in cursor.fetchall()]

    print("Summary Statistics:")
    print(f"- Total Studies: {total_studies}")
    print(f"- Total Slices: {total_slices}")
    print(f"- Average Slices per Study: {avg_slices_per_study:.2f}")

    if slice_thickness:
        print(f"- Slice Thickness: Min = {min(slice_thickness):.2f}, Max = {max(slice_thickness):.2f}, Mean = {np.mean(slice_thickness):.2f}")
    else:
        print("- Slice Thickness: No valid data available.")




# 4.2 Visualization 
def visualize_data(conn):
    cursor = conn.cursor()
    
    # Fetch SliceThickness data
    cursor.execute("SELECT SliceThickness FROM series WHERE SliceThickness != 'Unknown'")
    slice_thickness = [float(row[0]) for row in cursor.fetchall() if row[0].replace('.', '', 1).isdigit()]
    if slice_thickness:
        sns.histplot(slice_thickness, kde=False, bins=10, color='blue')
        plt.title("Distribution of Slice Thickness")
        plt.xlabel("Slice Thickness (mm)")
        plt.ylabel("Frequency")
        plt.grid(True, alpha=0.5)
        plt.show()
    else:
        print("No valid Slice Thickness data available for visualization.")




# Main Execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Define paths
    dataset_dir = "lidc_small_dset"
    db_path = os.path.abspath("enhanced_metadata.db")  # Use absolute path for clarity

    # Step 1: Data Ingestion
    files = load_dataset(dataset_dir)
    valid_files = validate_files(files)

    # Step 2: Metadata Extraction
    metadata = extract_metadata(valid_files)
    organize_files(metadata, base_dir="organized")

    # Step 3: Data Storage with Constraints
    conn = create_database(db_path)
    insert_metadata(conn, metadata)

    # Step 4: Basic Reporting
    generate_summary(conn)
    visualize_data(conn)

    conn.close()
