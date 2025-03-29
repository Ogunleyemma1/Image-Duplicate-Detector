# 🖼️ Image Duplicate Detector (IMDEDU)

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://www.python.org/) [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4-green)](https://www.sqlalchemy.org/) [![Streamlit](https://img.shields.io/badge/Streamlit-1.42.0-orange)](https://streamlit.io/)

## 🌟 Overview

**IMDEDU** (Image Deduplication) is a powerful tool designed to detect duplicate and near-duplicate images in large datasets. By leveraging cryptographic hashes (SHA-256) for unique identification and perceptual hashes (aHash) for visual similarity detection, this project provides an efficient solution for managing image collections. Whether you're organizing family photos, cleaning up storage drives, or curating digital archives, IMDEDU ensures that only the best-quality versions of similar images are retained.

This repository contains the implementation of the IMDEDU system, including backend processing scripts (`main.py`) and a user-friendly graphical interface (`app.py`) built with Streamlit.

---

## 🚀 Features

✨ **Key Capabilities**:
- **Cryptographic Hashing**: Ensures each image has a unique identifier using SHA-256.
- **Perceptual Hashing**: Detects visually similar images using Average Hash (aHash).
- **Geometric Transformations**: Handles rotations and shears to improve robustness against minor modifications.
- **Hamming Distance Calculation**: Measures similarity between images efficiently.
- **Database Integration**: Stores metadata and hash values in an SQLite database for fast retrieval and querying.
- **Interactive GUI**: Built with Streamlit for seamless user interaction, including folder processing and similarity detection.

---

## 📂 Repository Structure

```plaintext
├── main.py                # Core script for image processing and database operations
├── app.py                 # Streamlit-based GUI for user interaction
├── image_metadata.db      # SQLite database for storing image metadata
├── requirements.txt       # Python dependencies for the project
├── README.md              # This file!
└── assets/                # Example images and visualization outputs



📈 Performance Metrics
Cryptographic Hash Time
~0.01s per image
Perceptual Hash Time
~0.02s per image
Database Query Speed
<1ms per query
Supported Formats
PNG, JPG, JPEG, GIF, BMP

🌐 Applications
IMDEDU is versatile and can be applied in various domains:

Digital Archiving : Organize and deduplicate large photo collections.
Social Media Moderation : Identify reposted or edited content.
E-commerce : Detect duplicate product images.
Forensics : Analyze image datasets for tampering or reuse.
🤝 Future Work
While IMDEDU is already a robust tool, there’s always room for improvement:

Enhanced Hashing Techniques : Explore pHash or machine learning-based hashing for better accuracy.
Larger Datasets : Test on diverse datasets, such as social media images or scientific data.
Advanced GUI Features : Add batch processing, export options, and more customization.
🙏 Acknowledgments
We would like to thank the following libraries and tools for making this project possible:

Pillow for image handling.
imagehash for perceptual hashing.
SQLAlchemy for database management.
Streamlit for building the GUI.
Seaborn and Matplotlib for visualization.
📝 License
This project is licensed under the MIT License . See the LICENSE file for details.

📧 Contact
For questions, feedback, or collaboration opportunities, feel free to reach out:

Authors : Olubunmi Emmanuel Ogunleye
Email : [ogunleyemma1@gmail.com ]
GitHub : @ogunleyemma1
