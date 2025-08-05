@echo off
REM Setup script for Grant Assistant (Windows)

REM (Optional) Create virtual environment
REM python -m venv venv
REM call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Install pytest for testing
pip install pytest

REM Download spaCy model (optional, uncomment if needed)
REM python -m spacy download en_core_web_md

REM Run tests (optional, uncomment if you want to run tests after setup)
REM pytest

REM Run the app
streamlit run "Idea2Impact Studio.py" 