# Phoenicia University Student Progress Tracker

## Overview
The **Phoenicia University Student Progress Tracker** is an interactive web application built with Streamlit, designed to assist in managing, analyzing, and visualizing student academic progress. It streamlines the process of tracking required and intensive courses, customizing grading systems, and generating insightful reports.

The system was developed by **Dr. Zahi Abdul Sater** to improve academic tracking efficiency and enhance the decision-making process for students and administrators alike.

---

## Key Features

### **1. Student Progress Tracking**
- Upload a student progress report and process data seamlessly.
- Visualize academic journeys for individual students by semester and year.
- Filter results by semester, year range, and course name.

### **2. Customization Options**
- Customize required and intensive courses.
- Define grading systems by categorizing grades as counted or not counted.
- Upload equivalent course mappings for automatic data processing.

### **3. Data Visualization**
- Interactive bar charts to display student course loads by semester and year.
- Visual color coding for completed, in-progress, and missing courses.

### **4. Assignments and Course Mapping**
- Assign special course equivalencies (S.C.E.) and field elective courses (F.E.C.) interactively.
- Save assignments to Google Drive for persistence across sessions.

### **5. Enhanced User Interface**
- Tooltips to guide users through the application.
- Collapsible menus and sections for intuitive navigation.
- Multi-page layout for streamlined workflows:
  - **Upload Data**
  - **Customize Courses**
  - **View Reports**
  - **Student Profiles**

### **6. Google Drive Integration**
- Automatically sync equivalent courses and assignments with Google Drive.
- Support for uploading and managing data files directly from the app.

### **7. Reporting**
- Generate downloadable Excel reports with formatted data.
- Highlight completed, in-progress, and missing courses with color-coded visuals.

### **8. Built-In Error Handling**
- Validation for uploaded files and required columns.
- Notifications for missing or invalid data entries.

---

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/zahias/course_mapping.git
   cd course_mapping
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run main.py
   ```
4. Open the application in your browser (default: `http://localhost:8501`).

---

## Usage Instructions

### **1. Upload Data**
- Upload a student progress report in the required format.
- Ensure the file contains necessary columns: `ID`, `NAME`, `Year`, `Semester`, `Course`, `Grade`.
- The app automatically processes and validates the uploaded file.

### **2. Customize Courses**
- Define required and intensive courses via sidebar options.
- Upload a custom course list in CSV format if needed.
- Customize grading systems by selecting counted and non-counted grades.

### **3. View Reports**
- Review processed data in tabular format.
- Use filters and search options to refine displayed data.
- Generate and download formatted reports.

### **4. Student Profiles**
- Select a student by name to view their academic journey.
- Visualize semester-by-semester progress with charts and tables.
- Apply filters to refine results by semester or year.

---

## Project Structure
```
course_mapping/
│
├── main.py               # Main application file
├── requirements.txt      # Python dependencies
├── utilities.py          # Helper functions (file processing, database, etc.)
├── ui_components.py      # User interface components
├── data_processing.py    # Data transformation and analysis logic
├── google_drive_utils.py # Google Drive integration utilities
├── config.py             # Default configurations for courses and grading
├── pages/                # Streamlit multipage setup
│   ├── 1_Upload_Data.py
│   ├── 2_Customize_Courses.py
│   ├── 3_View_Reports.py
│   └── 4_Student_Profiles.py
└── assets/               # Static assets (e.g., logos, templates)
```

---

## Contribution Guidelines
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch for your feature:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature name"
   ```
4. Push to your fork:
   ```bash
   git push origin feature-name
   ```
5. Open a Pull Request.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgments
- Developed by **Dr. Zahi Abdul Sater**.
---

## Contact
For questions or suggestions, please contact **Dr. Zahi Abdul Sater** at zahi.abdulsater@pu.edu.lb

---
