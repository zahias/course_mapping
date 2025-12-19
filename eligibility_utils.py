"""
Graduation Eligibility Utilities

This module provides functions for checking student graduation eligibility
and identifying at-risk students.
"""

import pandas as pd
from config import extract_primary_grade_from_full_value, is_passing_grade
from data_processing import calculate_credits


def is_course_completed(processed_value: str, passing_grades: str) -> bool:
    """
    Checks if a course is completed based on processed value and passing grades.
    
    Args:
        processed_value: Processed grade value like "A | 3" or "F | 0"
        passing_grades: Comma-separated list of passing grades (e.g., "A+,A,A-,B+,B,B-")
    
    Returns:
        True if course is completed, False otherwise
    """
    if not processed_value or processed_value == "NR":
        return False
    
    # Extract primary grade
    primary_grade = extract_primary_grade_from_full_value(processed_value)
    
    # Check if it's a current registration
    if primary_grade.upper().startswith("CR"):
        return False
    
    # Extract just the grade part (before |)
    if "|" in primary_grade:
        grade_part = primary_grade.split("|")[0].strip()
    else:
        grade_part = primary_grade.strip()
    
    # Check if grade is passing
    return is_passing_grade(grade_part, passing_grades)


def check_graduation_eligibility(
    student_row: pd.Series,
    target_courses: dict,
    intensive_courses: dict,
    target_rules: dict,
    intensive_rules: dict
) -> dict:
    """
    Checks if a student meets graduation requirements.
    
    Args:
        student_row: Series representing a student row from the processed report
        target_courses: Dictionary mapping course codes to credits
        intensive_courses: Dictionary mapping intensive course codes to credits
        target_rules: Dictionary mapping course codes to rule lists
        intensive_rules: Dictionary mapping intensive course codes to rule lists
    
    Returns:
        Dictionary with eligibility status and details:
        {
            "eligible": bool,
            "completed_required": int,
            "total_required": int,
            "completed_intensive": int,
            "total_intensive": int,
            "missing_courses": list,
            "credits_completed": int,
            "credits_total": int,
            "credits_remaining": int
        }
    """
    completed_required = 0
    completed_intensive = 0
    missing_courses = []
    
    # Check required courses
    for course, credits in target_courses.items():
        course_value = student_row.get(course, "NR")
        
        # Get passing grades for this course
        passing_grades = ""
        if course in target_rules and target_rules[course]:
            passing_grades = target_rules[course][0].get("PassingGrades", "")
        
        if is_course_completed(str(course_value), passing_grades):
            completed_required += 1
        else:
            missing_courses.append(course)
    
    # Check intensive courses
    for course, credits in intensive_courses.items():
        course_value = student_row.get(course, "NR")
        
        # Get passing grades for this course
        passing_grades = ""
        if course in intensive_rules and intensive_rules[course]:
            passing_grades = intensive_rules[course][0].get("PassingGrades", "")
        
        if is_course_completed(str(course_value), passing_grades):
            completed_intensive += 1
    
    # Calculate credits
    credits_info = calculate_credits(student_row, {**target_courses, **intensive_courses})
    credits_completed = credits_info.get("# of Credits Completed", 0)
    credits_total = credits_info.get("Total Credits", 0)
    credits_remaining = credits_info.get("# Remaining", 0)
    
    # Student is eligible if all required courses are completed
    eligible = completed_required == len(target_courses)
    
    return {
        "eligible": eligible,
        "completed_required": completed_required,
        "total_required": len(target_courses),
        "completed_intensive": completed_intensive,
        "total_intensive": len(intensive_courses),
        "missing_courses": missing_courses,
        "credits_completed": credits_completed,
        "credits_total": credits_total,
        "credits_remaining": credits_remaining
    }


def identify_at_risk_students(
    df: pd.DataFrame,
    target_courses: dict,
    intensive_courses: dict,
    target_rules: dict,
    intensive_rules: dict,
    min_failing_grades: int = 2,
    min_incomplete_courses: int = 3
) -> pd.DataFrame:
    """
    Identifies at-risk students based on multiple criteria.
    
    Args:
        df: Processed report DataFrame
        target_courses: Dictionary mapping course codes to credits
        intensive_courses: Dictionary mapping intensive course codes to credits
        target_rules: Dictionary mapping course codes to rule lists
        intensive_rules: Dictionary mapping intensive course codes to rule lists
        min_failing_grades: Minimum number of failing grades to be considered at-risk
        min_incomplete_courses: Minimum number of incomplete courses to be considered at-risk
    
    Returns:
        DataFrame with at-risk students and their risk factors
    """
    at_risk_students = []
    
    for idx, row in df.iterrows():
        student_id = row.get("ID")
        student_name = row.get("NAME")
        risk_factors = []
        
        # Check graduation eligibility
        eligibility = check_graduation_eligibility(
            row, target_courses, intensive_courses, target_rules, intensive_rules
        )
        
        # Count failing grades
        failing_count = 0
        incomplete_count = 0
        
        all_courses = {**target_courses, **intensive_courses}
        for course in all_courses:
            course_value = str(row.get(course, "NR"))
            
            # Check for failing grades
            if "F" in course_value.upper() or "FAIL" in course_value.upper():
                failing_count += 1
            
            # Check for incomplete courses
            if course_value == "NR" or course_value == "":
                incomplete_count += 1
        
        # Determine risk level
        if not eligibility["eligible"]:
            risk_factors.append("Not eligible for graduation")
        
        if failing_count >= min_failing_grades:
            risk_factors.append(f"{failing_count} failing grades")
        
        if incomplete_count >= min_incomplete_courses:
            risk_factors.append(f"{incomplete_count} incomplete courses")
        
        if eligibility["credits_remaining"] > eligibility["credits_total"] * 0.3:
            risk_factors.append("More than 30% credits remaining")
        
        if risk_factors:
            at_risk_students.append({
                "ID": student_id,
                "NAME": student_name,
                "Risk Factors": "; ".join(risk_factors),
                "Failing Grades": failing_count,
                "Incomplete Courses": incomplete_count,
                "Credits Completed": eligibility["credits_completed"],
                "Credits Remaining": eligibility["credits_remaining"],
                "Completion %": round((eligibility["credits_completed"] / eligibility["credits_total"] * 100) if eligibility["credits_total"] > 0 else 0, 1)
            })
    
    if at_risk_students:
        return pd.DataFrame(at_risk_students)
    else:
        return pd.DataFrame(columns=["ID", "NAME", "Risk Factors", "Failing Grades", "Incomplete Courses", 
                                     "Credits Completed", "Credits Remaining", "Completion %"])


def get_eligibility_summary(
    df: pd.DataFrame,
    target_courses: dict,
    intensive_courses: dict,
    target_rules: dict,
    intensive_rules: dict
) -> dict:
    """
    Gets summary statistics for graduation eligibility across all students.
    
    Args:
        df: Processed report DataFrame
        target_courses: Dictionary mapping course codes to credits
        intensive_courses: Dictionary mapping intensive course codes to credits
        target_rules: Dictionary mapping course codes to rule lists
        intensive_rules: Dictionary mapping intensive course codes to rule lists
    
    Returns:
        Dictionary with summary statistics
    """
    eligible_count = 0
    total_students = len(df)
    eligibility_results = []
    
    for idx, row in df.iterrows():
        eligibility = check_graduation_eligibility(
            row, target_courses, intensive_courses, target_rules, intensive_rules
        )
        eligibility_results.append(eligibility)
        if eligibility["eligible"]:
            eligible_count += 1
    
    if total_students == 0:
        return {}
    
    avg_completion = sum(e["completed_required"] for e in eligibility_results) / total_students if total_students > 0 else 0
    avg_credits_completed = sum(e["credits_completed"] for e in eligibility_results) / total_students if total_students > 0 else 0
    
    return {
        "total_students": total_students,
        "eligible_students": eligible_count,
        "eligibility_rate": round((eligible_count / total_students * 100) if total_students > 0 else 0, 1),
        "avg_courses_completed": round(avg_completion, 1),
        "avg_credits_completed": round(avg_credits_completed, 1)
    }

