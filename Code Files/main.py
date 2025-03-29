import hashlib
from PIL import Image
import imagehash
import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from functools import cache

# Base for SQLAlchemy models
Base = declarative_base()

# Database schema for image metadata
class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    ID = Column(Integer, primary_key=True, nullable=False)
    filename = Column(String, nullable=False)
    cryptographic_hash = Column(String, nullable=False)
    perceptual_hash = Column(String, nullable=False)
    file_location = Column(String, nullable=False)
    file_size = Column(Float, nullable=False)
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    file_creation_date = Column(DateTime, nullable=False)
    file_extension = Column(String, nullable=False)
    perceptual_hash_rotation_15degrees_cw = Column(String, nullable=False)
    perceptual_hash_rotation_15deg_ccw = Column(String, nullable=False)
    perceptual_hash_shear_low_difference = Column(String, nullable=False)

# Main class for image processing and database operations
class IMDEDU:
    def __init__(self):
        self.directory_path = None  # Directory path is dynamically set

    def set_directory_path(self, path):
        """
        Set the directory path for image processing.
        """
        if os.path.exists(path):
            self.directory_path = path
        else:
            raise FileNotFoundError(f"The specified path '{path}' does not exist.")

    def load_images_from_directory(self):
        """
        Load images from the specified directory.
        """
        if not self.directory_path:
            raise ValueError("Directory path is not set. Use set_directory_path() to specify it.")

        images = []
        failed_files = []

        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                try:
                    img = Image.open(file_path)
                    img.verify()
                    images.append(file_path)
                    print(f"Loaded: {filename}")
                except Exception as e:
                    failed_files.append((filename, str(e)))
                    print(f"Error loading {filename}: {e}")

        print("\nSummary:")
        print(f"Total images loaded: {len(images)}")
        print(f"Failed to load: {len(failed_files)}")
        if failed_files:
            print("\nFailed Files:")
            for file, error in failed_files:
                print(f"{file}: {error}")

        return images

    def compute_cryptographic_hash(self, image_path):
        """
        Compute the SHA-256 hash of an image file.
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(image_path, 'rb') as img_file:
                while chunk := img_file.read(8192):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error computing hash for {image_path}: {e}")
            return None

    def compute_perceptual_hash(self, image):
        """
        Compute the perceptual hash of an image.
        """
        try:
            image = image.convert('RGB')
            perceptual_hash = imagehash.average_hash(image)
            return str(perceptual_hash)  # Convert to string for storage
        except Exception as e:
            print(f"Error computing perceptual hash: {e}")
            return None

    def create_image_instances_and_hashes(self, image):
        """
        Create modified versions of the image and compute their perceptual hashes.
        """
        try:
            rotation_15degrees_cw = image.rotate(15, resample=Image.NEAREST)
            hash_rotation_15degrees_cw = self.compute_perceptual_hash(rotation_15degrees_cw)

            rotation_15degrees_ccw = image.rotate(-15, resample=Image.NEAREST)
            hash_rotation_15degrees_ccw = self.compute_perceptual_hash(rotation_15degrees_ccw)

            width, height = image.size
            shear_matrix = (1, 0.05, 0, 0.05, 1, 0)
            shear_low_diff = image.transform((width, height), Image.AFFINE, shear_matrix, resample=Image.NEAREST)
            hash_shear_low_diff = self.compute_perceptual_hash(shear_low_diff)

            return {
                "rotation_15degrees_Clockwise": hash_rotation_15degrees_cw,
                "rotation_15degrees_CounterClockwise": hash_rotation_15degrees_ccw,
                "Shear_Low_Difference": hash_shear_low_diff,
            }
        except Exception as e:
            print(f"Error creating image instances and hashes: {e}")
            return {}

    def initialize_db(self, db_name):
        """
        Initialize the SQLite database and create tables.
        """
        engine = create_engine(f'sqlite:///{db_name}', connect_args={'check_same_thread': False})
        Base.metadata.create_all(engine)
        Session = scoped_session(sessionmaker(bind=engine))
        return Session

    def clear_existing_data(self, session):
        """
        Clear existing data from the database.
        """
        try:
            session.query(ImageMetadata).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error clearing data: {e}")

    def insert_image_metadata(self, session, image_metadata):
        """
        Insert image metadata into the database.
        """
        try:
            session.add(image_metadata)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error inserting data: {e}")

    @cache
    def calculate_hamming_distance(self, hash1, hash2):
        """
        Calculate the Hamming distance between two perceptual hashes.
        """
        if hash1 and hash2:
            return hash1 - hash2  # Use subtraction for ImageHash objects, which supports this operation
        return 0  # Default to 0 if either hash is None or invalid

    def compute_hamming_distance_to_uploaded_image(self, uploaded_image_path, session):
        """
        Compute Hamming distance between the uploaded image and all images in the folder.
        """
        try:
            with Image.open(uploaded_image_path) as uploaded_img:
                uploaded_perceptual_hash = self.compute_perceptual_hash(uploaded_img)

                # Get all images from the database
                images = session.query(ImageMetadata).all()

                hamming_distances = []

                for image in images:
                    image_perceptual_hash = image.perceptual_hash
                    distance = self.calculate_hamming_distance(
                        imagehash.hex_to_hash(uploaded_perceptual_hash),
                        imagehash.hex_to_hash(image_perceptual_hash)
                    )
                    hamming_distances.append({
                        "filename": image.filename,
                        "hamming_distance": distance,
                        "file_location": image.file_location
                    })

                return hamming_distances
        except Exception as e:
            print(f"Error computing Hamming distance: {e}")
            return []

    def process_images_and_populate_db(self, session, image_paths):
        """
        Process images, compute hashes, and store metadata in the database.
        """
        for image_path in image_paths:
            try:
                with Image.open(image_path) as img:
                    cryptographic_hash = self.compute_cryptographic_hash(image_path)
                    perceptual_hash = self.compute_perceptual_hash(img)

                    image_hashes = self.create_image_instances_and_hashes(img)
                    ph_rot_cw = image_hashes.get("rotation_15degrees_Clockwise", "NA")
                    ph_rot_ccw = image_hashes.get("rotation_15degrees_CounterClockwise", "NA")
                    ph_shear = image_hashes.get("Shear_Low_Difference", "NA")

                    file_location = os.path.abspath(image_path)
                    file_size = os.path.getsize(image_path)
                    width, height = img.size
                    creation_date = datetime.datetime.fromtimestamp(os.path.getctime(image_path))
                    file_extension = os.path.splitext(image_path)[1].lower()

                    image_metadata = ImageMetadata(
                        filename=os.path.basename(image_path),
                        cryptographic_hash=cryptographic_hash,
                        perceptual_hash=perceptual_hash,
                        file_location=file_location,
                        file_size=file_size,
                        image_width=width,
                        image_height=height,
                        file_creation_date=creation_date,
                        file_extension=file_extension,
                        perceptual_hash_rotation_15degrees_cw=ph_rot_cw,
                        perceptual_hash_rotation_15deg_ccw=ph_rot_ccw,
                        perceptual_hash_shear_low_difference=ph_shear,
                    )

                    session.add(image_metadata)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error processing image {image_path}: {e}")

def recreate_table(engine):
    """
    Drop and recreate the database tables.
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database tables recreated successfully.")

# Additional code for triangular matrix plot (appended at the end)
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from main import IMDEDU, ImageMetadata  # Self-reference for imports

# Initialize IMDEDU and database
image_processor = IMDEDU()
db_name = "image_metadata.db"
engine = create_engine(f"sqlite:///{db_name}", connect_args={"check_same_thread": False})
session = image_processor.initialize_db(db_name)

# Get all images from the database
images = session.query(ImageMetadata).all()

# Compute pairwise Hamming distances (example implementation; adjust as needed)
pairwise_hamming_distances = {}
for i, img1 in enumerate(images):
    for j, img2 in enumerate(images):
        if i < j:  # Avoid duplicate comparisons and self-comparisons
            hash1 = imagehash.hex_to_hash(img1.perceptual_hash)
            hash2 = imagehash.hex_to_hash(img2.perceptual_hash)
            distance = image_processor.calculate_hamming_distance(hash1, hash2)
            pairwise_hamming_distances[(img1.filename, img2.filename)] = distance

# Extract the keys (image pairs) and convert the pairwise distances into a matrix
keys = list(set([key[0] for key in pairwise_hamming_distances.keys()] + 
                [key[1] for key in pairwise_hamming_distances.keys()]))
distance_matrix = np.zeros((len(keys), len(keys)))

# Fill the matrix with the pairwise distances
for (image_A, image_B), distance in pairwise_hamming_distances.items():
    i = keys.index(image_A)
    j = keys.index(image_B)
    distance_matrix[i, j] = distance
    distance_matrix[j, i] = distance  # Since Hamming distance is symmetric

# Mask the lower triangular part of the matrix (set NaN for lower triangle)
mask_lower = np.tril(np.ones_like(distance_matrix, dtype=bool), k=0)  # Mask lower triangle
distance_matrix[mask_lower] = np.nan  # Set lower triangle to NaN (no annotation)

# Plot the distance matrix as a heatmap with binary color map
plt.figure(figsize=(10, 8))

# Set the color map to 'binary' and annotate only for the upper triangle
sns.heatmap(distance_matrix, 
            xticklabels=keys,  # Label X-axis with filenames
            yticklabels=keys,  # Label Y-axis with filenames
            cmap="binary", 
            annot=True, 
            annot_kws={'size': 10}, 
            cbar=True, 
            mask=mask_lower,  # Mask lower triangle
            square=True)

# Adding labels and title
plt.title("Pairwise Minimum Hamming Distances between Images")
plt.xlabel("Images")
plt.ylabel("Images")

# Show the plot in the VS Code terminal/output
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()