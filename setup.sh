#!/bin/bash
# Setup script for Grant Assistant (Unix/Mac)

# (Optional) Create virtual environment
# python3 -m venv venv
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install pytest for testing
pip install pytest

# Download spaCy model (optional, uncomment if needed)
# python -m spacy download en_core_web_md

# Run tests (optional, uncomment if you want to run tests after setup)
# pytest

# Run the app
streamlit run "Idea2Impact Studio.py" 