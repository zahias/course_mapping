Rulebook
1. Uploading Data
Progress Report File:

The app requires an Excel file containing a "Progress Report" sheet.
The following columns are required: ID, NAME, Course, Grade, Year, Semester.
If any required columns are missing, the app displays an error message.
The user uploads this file from the main interface.
Data is read and validated through read_progress_report.
Custom Course List (Optional):

A custom course list in CSV format can be uploaded via the sidebar.
Required columns for the custom course list are Course and Credits.
This custom list overrides the default target courses.
If the CSV is properly formatted, the app updates the target courses accordingly.
Equivalent Courses:

The equivalent courses are stored in a CSV file (equivalent_courses.csv) on Google Drive.
The app automatically loads this file at startup.
Any changes made directly to equivalent_courses.csv on Google Drive are reflected when the app restarts or when "Reload Equivalent Courses" is clicked.
No direct file upload for equivalent courses is needed through the app.
2. Course Classification
Required Courses:

Defined by default in config.py.
Can be overridden by a custom target courses CSV.
Displayed in the "Required Courses" tab.
Include potential S.C.E. and F.E.C. assignments.
Intensive Courses:

Defined in config.py.
Displayed separately in the "Intensive Courses" tab.
Extra Courses:

Any course not classified as required or intensive is considered an extra course.
Displayed in the "Extra Courses" tab for detailed review and potential S.C.E./F.E.C. assignment.
Equivalent Courses:

Mapped during processing.
For example, if MNGT402 is equivalent to INFO404, it is recognized as INFO404 during data processing.
The mapping is loaded from equivalent_courses.csv on Google Drive and updated via the "Reload Equivalent Courses" button.
3. Grading Rules
Counted vs. Not Counted Grades:

Defined in config.py.
Counted grades (e.g., A, B, C, D, P) contribute to completed credits.
Not counted grades (e.g., F, R, W, WF, I) do not contribute to completed credits.
Grade Display Options:

"Show All Grades" Toggle OFF:
Only the primary counted grade is displayed.
The primary counted grade is determined by a hierarchy: A+ > A > A- > B+ > B > B- > C+ > C > C- > D+ > D > D- > T > F.
If no counted grades exist, the first uncounted grade is displayed.

"Show All Grades" Toggle ON:
All grades for a given course are displayed (e.g., "F, F, D | 3").

4. Assigning S.C.E. and F.E.C. Courses
Assignment Process:

Users can interactively assign S.C.E. (Special Course Equivalent) and F.E.C. (Field Elective Course) via the "Assign S.C.E. and F.E.C. Courses" section.
Assignments are made using a data editor interface.
Each student can have at most one S.C.E. and one F.E.C. assigned.
Data Persistence:

Assignments are stored in sce_fec_assignments.csv on Google Drive.
Saving assignments updates the existing file, ensuring that previous assignments are preserved.
A "Reset All Assignments" button clears all assignments both locally and on Google Drive.
5. Credits Calculation
For each required and intensive course, credits are assigned based on course definitions in config.py or a custom target courses CSV.

Categories:

Completed Credits:
Credits from courses where at least one counted grade is present (e.g., A, B, C, D, P).
Registered Credits:
Credits from courses with "CR" (Currently Registered) status.
Remaining Credits:
Credits from courses not yet registered ("NR") or courses that have only failing/not-counted grades and thus are not completed.
Total Credits:
The sum of credits for all required or intensive courses.
Logic (as implemented in calculate_credits):

If a course is "CR" or represented as 'c' in the completed-only view, it counts as registered credits.
If a course is "NR", it counts as remaining.
If a course has a counted grade, it contributes to completed credits.
If no counted grade and not CR/NR, it's considered remaining.
Total credits are the sum of all required (or intensive) course credits.
Hierarchy of Grades:

For grading and completion logic, counted grades determine if credits are completed.
Uncounted grades (F, R, W, WF, I) do not fulfill the requirement and thus result in remaining credits.
6. Data Processing Rules
Mapping Courses:

Equivalent courses mapping is applied first, converting known equivalents (e.g., MNGT402) to their primary course (e.g., INFO404).
If S.C.E. or F.E.C. assignments exist, the process_progress_report function updates the mapped course to 'S.C.E' or 'F.E.C' accordingly.
Pivot Tables:

Required and intensive courses are displayed using pivot tables (ID/NAME as rows, courses as columns, grades as values).
Extra courses remain in a flat list format for easy review and assignment.
Duplicate Columns:

The app ensures that no duplicate columns exist after pivoting, thus maintaining data integrity.
7. Saving and Exporting
Assignments and Equivalent Courses:

Assignments are saved to sce_fec_assignments.csv on Google Drive.
Equivalent courses are read from equivalent_courses.csv on Google Drive.
Both files persist across sessions, and changes on Google Drive are reflected in the app.
Exported Report:

Users can download a processed Excel report.
The report includes "Required Courses" and "Intensive Courses" sheets.
Formatting (color coding, headers) is preserved in the downloaded file.
8. Formatting and Visuals
Color Coding:

Completed or currently registered courses: Green background.
Missing or not registered courses: Pink background.
This color scheme applies to both "Required Courses" and "Intensive Courses" tabs.
Interactive Editing:

S.C.E. and F.E.C. assignments are made interactively in the UI.
After editing assignments, users can save them to Google Drive.
Download Button:

The processed report can be downloaded in Excel format at any time.
9. Error Handling
Missing Columns:

If required columns are missing from the progress report, the app displays an error and does not process the data.
Invalid Files:

If CSV files (assignments or equivalents) are empty or invalid, warnings or errors are displayed.
Duplicate Courses:

The app handles duplicate courses gracefully by deduplicating and ensuring a consistent view.
10. Debugging and Logs
Action Logging:

All significant actions (assignments saved, report generated) are logged.
Logs are stored in app.log for debugging and tracking purposes.