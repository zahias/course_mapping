"""
GPA Calculation Utilities

This module provides functions for calculating student GPAs based on their grades.
Supports different grading scales and credit-based calculations.
"""

import pandas as pd
from config import GRADE_ORDER, extract_primary_grade_from_full_value


# Standard 4.0 GPA scale mapping
GRADE_POINTS_4_0 = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "D-": 0.7,
    "F": 0.0,
    "P": None,  # Pass - doesn't count in GPA
    "CR": None,  # Current Registration - doesn't count in GPA
    "NR": None,  # Not Registered - doesn't count in GPA
    "PASS": None,  # Pass - doesn't count in GPA
    "FAIL": 0.0,
}


def grade_to_points(grade: str, scale: dict = None) -> float | None:
    """
    Converts a letter grade to GPA points.
    
    Args:
        grade: Letter grade (e.g., "A+", "B-", "F")
        scale: Dictionary mapping grades to points. Defaults to 4.0 scale.
    
    Returns:
        GPA points (float) or None if grade doesn't count toward GPA
    """
    if scale is None:
        scale = GRADE_POINTS_4_0
    
    grade_upper = str(grade).strip().upper()
    
    # Handle grades with credit info (e.g., "A | 3")
    if "|" in grade_upper:
        grade_part = grade_upper.split("|")[0].strip()
    else:
        grade_part = grade_upper
    
    # Handle comma-separated multiple attempts (take the best grade)
    if "," in grade_part:
        grades = [g.strip() for g in grade_part.split(",")]
        # Extract primary grade from the list
        full_value = extract_primary_grade_from_full_value(grade)
        if "|" in full_value:
            grade_part = full_value.split("|")[0].strip().upper()
        else:
            grade_part = full_value.strip().upper()
    
    return scale.get(grade_part)


def calculate_gpa(df: pd.DataFrame, grade_col: str = "Grade", credits_col: str = None, 
                  course_credits_dict: dict = None, scale: dict = None) -> pd.Series:
    """
    Calculates GPA for each student in a DataFrame.
    
    Args:
        df: DataFrame with student grades. Must have columns: ID, NAME, and grade_col
        grade_col: Name of the column containing grades
        credits_col: Name of the column containing credits (if available)
        course_credits_dict: Dictionary mapping course codes to credits (if credits_col not available)
        scale: Dictionary mapping grades to GPA points. Defaults to 4.0 scale.
    
    Returns:
        Series with GPA for each student (indexed by student ID)
    """
    if scale is None:
        scale = GRADE_POINTS_4_0
    
    results = {}
    
    for student_id, student_df in df.groupby("ID"):
        total_points = 0.0
        total_credits = 0.0
        
        for _, row in student_df.iterrows():
            grade = row[grade_col]
            
            # Get credit hours for this course
            credits = 0.0
            if credits_col and credits_col in row:
                try:
                    credits = float(row[credits_col])
                except (ValueError, TypeError):
                    credits = 0.0
            elif course_credits_dict:
                course = row.get("Course", "")
                credits = course_credits_dict.get(course, 0.0)
            
            # Convert grade to points
            points = grade_to_points(grade, scale)
            
            # Only count if grade has points and credits > 0
            if points is not None and credits > 0:
                total_points += points * credits
                total_credits += credits
        
        # Calculate GPA
        if total_credits > 0:
            gpa = total_points / total_credits
            results[student_id] = round(gpa, 2)
        else:
            results[student_id] = None
    
    return pd.Series(results, name="GPA")


def calculate_gpa_from_processed_value(processed_value: str, credits: float) -> float | None:
    """
    Calculates GPA contribution from a processed value string (e.g., "A | 3" or "B+ | 0").
    
    Args:
        processed_value: Processed grade value like "A | 3" or "B+ | 0"
        credits: Credit hours for the course
    
    Returns:
        GPA points contribution (points * credits) or None if not applicable
    """
    if not processed_value or credits <= 0:
        return None
    
    # Extract primary grade
    primary_grade = extract_primary_grade_from_full_value(processed_value)
    
    # Get points for the grade
    points = grade_to_points(primary_grade)
    
    if points is not None:
        return points * credits
    
    return None


def get_gpa_summary(df: pd.DataFrame, gpa_col: str = "GPA") -> dict:
    """
    Gets summary statistics for GPAs in a DataFrame.
    
    Args:
        df: DataFrame with GPA column
        gpa_col: Name of the GPA column
    
    Returns:
        Dictionary with summary statistics
    """
    if gpa_col not in df.columns:
        return {}
    
    gpa_series = df[gpa_col].dropna()
    
    if len(gpa_series) == 0:
        return {}
    
    return {
        "mean": round(gpa_series.mean(), 2),
        "median": round(gpa_series.median(), 2),
        "min": round(gpa_series.min(), 2),
        "max": round(gpa_series.max(), 2),
        "std": round(gpa_series.std(), 2),
        "count": len(gpa_series)
    }

