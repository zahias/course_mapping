"""
Chart and Visualization Utilities

This module provides functions for creating visualizations of student progress data.
Uses Plotly for interactive charts.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def create_progress_timeline(df: pd.DataFrame, student_id: str = None, student_name: str = None) -> go.Figure:
    """
    Creates a timeline chart showing course completion over time.
    
    Args:
        df: DataFrame with columns: ID, NAME, Year, Semester, Course, Grade
        student_id: Optional student ID to filter to a single student
        student_name: Optional student name for title
    
    Returns:
        Plotly figure object
    """
    if student_id:
        df = df[df["ID"].astype(str) == str(student_id)]
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Create term ordinal for sorting
    def term_to_ordinal(row):
        year = int(str(row["Year"])) if str(row["Year"]).isdigit() else 0
        sem = str(row["Semester"]).strip().upper()
        sem_map = {"SPRING": 1, "SUMMER": 2, "FALL": 3}
        return year * 10 + sem_map.get(sem, 0)
    
    df = df.copy()
    df["TermOrd"] = df.apply(term_to_ordinal, axis=1)
    df["Term"] = df["Semester"] + " " + df["Year"].astype(str)
    df = df.sort_values("TermOrd")
    
    # Count courses per term
    term_counts = df.groupby(["Term", "TermOrd"]).size().reset_index(name="Courses")
    term_counts = term_counts.sort_values("TermOrd")
    
    fig = px.line(
        term_counts,
        x="Term",
        y="Courses",
        markers=True,
        title=f"Course Completion Timeline{f' - {student_name}' if student_name else ''}",
        labels={"Courses": "Number of Courses", "Term": "Term"}
    )
    fig.update_traces(line_width=3, marker_size=10)
    fig.update_layout(
        xaxis_title="Term",
        yaxis_title="Number of Courses",
        hovermode='x unified',
        height=400
    )
    
    return fig


def create_grade_distribution_chart(df: pd.DataFrame, student_id: str = None) -> go.Figure:
    """
    Creates a bar chart showing grade distribution.
    
    Args:
        df: DataFrame with Grade column
        student_id: Optional student ID to filter to a single student
    
    Returns:
        Plotly figure object
    """
    if student_id:
        df = df[df["ID"].astype(str) == str(student_id)]
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    grade_counts = df["Grade"].value_counts().sort_index()
    
    fig = px.bar(
        x=grade_counts.index,
        y=grade_counts.values,
        title="Grade Distribution",
        labels={"x": "Grade", "y": "Count"},
        color=grade_counts.values,
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        xaxis_title="Grade",
        yaxis_title="Number of Courses",
        height=400,
        showlegend=False
    )
    
    return fig


def create_completion_heatmap(df: pd.DataFrame, courses: list, student_id: str = None) -> go.Figure:
    """
    Creates a heatmap showing course completion status.
    
    Args:
        df: DataFrame with Course and Grade columns
        courses: List of course codes to include
        student_id: Optional student ID to filter to a single student
    
    Returns:
        Plotly figure object
    """
    if student_id:
        df = df[df["ID"].astype(str) == str(student_id)]
    
    if df.empty or not courses:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Determine completion status (simplified - can be enhanced)
    def is_completed(grade):
        grade_str = str(grade).upper()
        if "CR" in grade_str or "NR" in grade_str:
            return "Not Completed"
        elif any(g in grade_str for g in ["F", "FAIL"]):
            return "Failed"
        elif any(g in grade_str for g in ["A", "B", "C", "D", "P", "PASS"]):
            return "Completed"
        return "Unknown"
    
    df = df.copy()
    df["Status"] = df["Grade"].apply(is_completed)
    
    # Create matrix
    completion_matrix = []
    for course in courses:
        course_data = df[df["Course"] == course]
        if not course_data.empty:
            status = course_data["Status"].iloc[0]
            completion_matrix.append({"Course": course, "Status": status})
        else:
            completion_matrix.append({"Course": course, "Status": "Not Taken"})
    
    matrix_df = pd.DataFrame(completion_matrix)
    
    # Map status to numeric for heatmap
    status_map = {"Completed": 2, "Failed": 1, "Not Completed": 0, "Not Taken": -1, "Unknown": 0}
    matrix_df["StatusValue"] = matrix_df["Status"].map(status_map)
    
    fig = go.Figure(data=go.Heatmap(
        z=[matrix_df["StatusValue"].tolist()],
        x=matrix_df["Course"].tolist(),
        y=["Completion Status"],
        colorscale=[[0, '#d32f2f'], [0.25, '#ff9800'], [0.5, '#fff9c4'], [0.75, '#c8e6c9'], [1, '#4caf50']],
        showscale=True,
        colorbar=dict(
            title="Status",
            tickvals=[-1, 0, 1, 2],
            ticktext=["Not Taken", "Not Completed", "Failed", "Completed"]
        )
    ))
    
    fig.update_layout(
        title="Course Completion Heatmap",
        xaxis_title="Course",
        height=200,
        yaxis=dict(showticklabels=True)
    )
    
    return fig


def create_gpa_trend_chart(df: pd.DataFrame, gpa_data: pd.Series, student_id: str = None) -> go.Figure:
    """
    Creates a line chart showing GPA trend over time.
    
    Args:
        df: DataFrame with Year and Semester columns
        gpa_data: Series with GPA values indexed by student ID
        student_id: Optional student ID to filter
    
    Returns:
        Plotly figure object
    """
    if student_id and student_id not in gpa_data.index:
        fig = go.Figure()
        fig.add_annotation(text="GPA data not available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # This is a simplified version - would need term-by-term GPA calculation for full implementation
    if student_id:
        gpa_value = gpa_data.get(student_id)
        if gpa_value:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=["Overall"],
                y=[gpa_value],
                mode='markers+lines',
                marker=dict(size=15, color='blue'),
                name="GPA"
            ))
            fig.update_layout(
                title="Student GPA",
                xaxis_title="",
                yaxis_title="GPA",
                yaxis=dict(range=[0, 4.0]),
                height=300
            )
            return fig
    
    # For all students, show distribution
    gpa_values = gpa_data.dropna()
    if len(gpa_values) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No GPA data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    fig = px.histogram(
        x=gpa_values.values,
        nbins=20,
        title="GPA Distribution",
        labels={"x": "GPA", "y": "Number of Students"}
    )
    fig.update_layout(height=400)
    
    return fig

