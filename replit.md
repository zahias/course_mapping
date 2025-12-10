# Phoenicia University Student Progress Tracker

## Overview
A Streamlit-based web application for tracking student academic progress at Phoenicia University. The app allows users to upload and manage student progress reports, customize courses, and view academic reports.

## Project Structure
- `main.py` - Main Streamlit application entry point
- `pages/` - Streamlit multipage app pages:
  - `2_Customize_Courses.py` - Course customization page
  - `3_View_Reports.py` - Reports viewing page
  - `4_Student_Progress.py` - Individual student progress page
- `config.py` - Configuration settings and utility functions
- `data_processing.py` - Data processing utilities
- `database_utils.py` - Database utility functions
- `utilities.py` - General utility functions
- `google_drive_utils.py` - Google Drive integration utilities
- `ui_components.py` - Reusable UI components
- `assignment_utils.py` - Assignment-related utilities
- `completion_utils.py` - Completion tracking utilities
- `logging_utils.py` - Logging configuration

## Configuration
- **Port**: 5000 (Streamlit server)
- **Host**: 0.0.0.0

## Running the Application
The app runs via Streamlit:
```
streamlit run main.py --server.port=5000 --server.address=0.0.0.0 --server.headless=true
```

## Dependencies
See `requirements.txt` for Python dependencies:
- streamlit
- pandas
- openpyxl
- plotly
- google-auth, google-auth-oauthlib, google-api-python-client
- numpy
- streamlit-aggrid

## Data Files
- `equivalent_courses.csv` - Course equivalency mappings
- `target_courses.csv` - Target course configurations
- `sce_fec_assignments.csv` - SCE/FEC assignment data
- `uploads/` - User uploaded files directory
- `PBHL/`, `SPTH/` - Major-specific data folders

## Recent Changes
- December 2025: Initial Replit environment setup
