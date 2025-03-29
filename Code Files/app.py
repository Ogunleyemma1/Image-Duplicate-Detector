import streamlit as st
import os
from PIL import Image
import pandas as pd
from io import BytesIO
from sqlalchemy import create_engine
from main import IMDEDU, ImageMetadata, recreate_table  # Backend import
import time

# Initialize image processing class
image_processor = IMDEDU()

# Set Streamlit page configuration
st.set_page_config(
    page_title="IMDEDU - Image Deduplication", 
    page_icon="🖼️", 
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
    <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            border-radius: 10px;
            padding: 8px 16px;
        }
        .stFileUploader label, .stSlider label {
            font-size: 16px;
            font-weight: bold;
        }
        .image-box {
            border: 2px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .similar-images-box {
            border: 2px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            background-color: #f9f9f9;
            margin-top: 20px;
            height: auto;
            max-height: 300px;
            overflow-y: auto;
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-start;
            align-items: center;
            gap: 10px;
        }
        .matching-images img {
            border-radius: 8px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
            width: 100px;
            height: auto;
            margin: 5px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📷 IMDEDU - Image Deduplication")
st.markdown("Compare images using perceptual hashes and Hamming distances.")

# Layout as per provided sketch
left_col, right_col = st.columns([2, 3])

with left_col:
    # File Path Input
    st.header("📂 File Path")
    folder_path = st.text_input("Enter folder path:", placeholder="e.g., /path/to/images")
    if st.button("🚀 Process Folder"):
        if os.path.exists(folder_path):
            image_processor.set_directory_path(folder_path)
            image_paths = image_processor.load_images_from_directory()
            if image_paths:
                st.success(f"✅ Loaded {len(image_paths)} images successfully!")
                progress_bar = st.progress(0)
                for i, image_path in enumerate(image_paths):
                    time.sleep(0.1)  # Simulate processing (remove in production)
                    progress_bar.progress((i + 1) / len(image_paths))
                
                db_name = "image_metadata.db"
                engine = create_engine(f"sqlite:///{db_name}", connect_args={"check_same_thread": False})
                recreate_table(engine)
                session = image_processor.initialize_db(db_name)
                image_processor.clear_existing_data(session)
                image_processor.process_images_and_populate_db(session, image_paths)
                st.success("🎉 Database updated with image metadata!")

                # Generate CSV file with all metadata (excluding Hamming distance)
                all_metadata = []
                for image_path in image_paths:
                    # Query the full metadata for the image from the database using the file_location
                    image_record = session.query(ImageMetadata).filter(ImageMetadata.file_location == os.path.abspath(image_path)).first()
                    if image_record:
                        # Add all metadata fields to the list (excluding hamming_distance)
                        metadata = {
                            "filename": image_record.filename,
                            "file_location": image_record.file_location,
                            "file_size": image_record.file_size,
                            "image_width": image_record.image_width,
                            "image_height": image_record.image_height,
                            "file_creation_date": str(image_record.file_creation_date),  # Convert to string for CSV compatibility
                            "file_extension": image_record.file_extension,
                            "cryptographic_hash": image_record.cryptographic_hash,
                            "perceptual_hash": image_record.perceptual_hash,
                            "perceptual_hash_rotation_15degrees_cw": image_record.perceptual_hash_rotation_15degrees_cw,
                            "perceptual_hash_rotation_15deg_ccw": image_record.perceptual_hash_rotation_15deg_ccw,
                            "perceptual_hash_shear_low_difference": image_record.perceptual_hash_shear_low_difference,
                        }
                        all_metadata.append(metadata)

                # Convert to DataFrame
                df = pd.DataFrame(all_metadata)

                # Export all metadata to CSV
                csv_file = BytesIO()
                df.to_csv(csv_file, index=False)
                csv_file.seek(0)
                st.download_button(
                    "📥 Download All Image Metadata as CSV", 
                    data=csv_file, 
                    file_name="all_image_metadata.csv", 
                    mime="text/csv"
                )
        else:
            st.error("⚠️ The specified folder does not exist.")
    
    # Image Upload Section
    st.header("📤 Upload Image")
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        uploaded_image = Image.open(uploaded_file)
        st.image(uploaded_image, caption="Uploaded Image", width=350)
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_image_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Hamming Distance Slider (Moved to Left Panel)
        st.subheader("🎚️ Hamming Distance Threshold")
        threshold = st.slider("Adjust similarity threshold", 0, 32, 10)

# Right Column - Displaying Best Match and Similar Images
with right_col:
    st.header("🏆 Best Matching Image")
    db_name = "image_metadata.db"
    if uploaded_file and os.path.exists(db_name):
        engine = create_engine(f"sqlite:///{db_name}", connect_args={"check_same_thread": False})
        session = image_processor.initialize_db(db_name)
        hamming_distances = image_processor.compute_hamming_distance_to_uploaded_image(temp_image_path, session)
        
        if hamming_distances:
            # Create a list to store all metadata for each image
            all_metadata = []
            for image in hamming_distances:
                # Query the full metadata for the image from the database using the filename or file_location
                image_record = session.query(ImageMetadata).filter(ImageMetadata.file_location == image["file_location"]).first()
                if image_record:
                    # Add all metadata fields to the list
                    metadata = {
                        "filename": image_record.filename,
                        "hamming_distance": image["hamming_distance"],
                        "file_location": image_record.file_location,
                        "file_size": image_record.file_size,
                        "image_width": image_record.image_width,
                        "image_height": image_record.image_height,
                        "file_creation_date": image_record.file_creation_date,
                        "file_extension": image_record.file_extension,
                        "cryptographic_hash": image_record.cryptographic_hash,
                        "perceptual_hash": image_record.perceptual_hash,
                        "perceptual_hash_rotation_15degrees_cw": image_record.perceptual_hash_rotation_15degrees_cw,
                        "perceptual_hash_rotation_15deg_ccw": image_record.perceptual_hash_rotation_15deg_ccw,
                        "perceptual_hash_shear_low_difference": image_record.perceptual_hash_shear_low_difference,
                    }
                    all_metadata.append(metadata)

            # Convert to DataFrame
            df = pd.DataFrame(all_metadata)
            best_match = df.nsmallest(1, "hamming_distance").iloc[0]
            try:
                best_img = Image.open(best_match["file_location"])
                st.image(best_img, caption=f"Best Match: {best_match['filename']} (Dist: {best_match['hamming_distance']})", width=400)
                
                # Display additional metadata for the best match
                st.markdown(f"""
                    **File Name:** {best_match['filename']}  
                    **Hamming Distance:** {best_match['hamming_distance']}  
                    **Dimensions:** {best_match['image_width']}x{best_match['image_height']}  
                    **File Size:** {best_match['file_size'] // 1024} KB  
                    **File Creation Date:** {best_match['file_creation_date']}  
                    **File Extension:** {best_match['file_extension']}
                """)
            except:
                st.warning("Could not load the best matching image.")
            
            # Filter similar images based on the Hamming distance threshold
            filtered_df = df[df["hamming_distance"] <= threshold]
            
            st.subheader("🖼️ Similar Images")
            if not filtered_df.empty:
                # Create a grid of 4 columns
                cols = st.columns(4)
                for idx, row in filtered_df.iterrows():
                    try:
                        simg = Image.open(row["file_location"])
                        cols[idx % 4].image(simg, caption=f"{row['filename']} (Dist: {row['hamming_distance']})", use_container_width=True)
                    except:
                        pass
            else:
                st.warning("No similar images found.")
            
            # Export all metadata to CSV
            csv_file = BytesIO()
            filtered_df.to_csv(csv_file, index=False)
            csv_file.seek(0)
            st.download_button(
                "📥 Download Results as CSV", 
                data=csv_file, 
                file_name="image_metadata_results.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No images found in the database to compare.")
    elif uploaded_file:
        st.error("Database not found. Process a folder first!")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: gray;">
         Image Similarity Finder
    </div>
""", unsafe_allow_html=True)

