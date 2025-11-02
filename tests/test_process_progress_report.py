import pandas as pd

from data_processing import process_progress_report


def test_intensive_results_include_students_without_intensive_rows():
    df = pd.DataFrame(
        [
            {
                "ID": "123",
                "NAME": "Alice Example",
                "Course": "REQ101",
                "Grade": "A",
                "Year": "2023",
                "Semester": "Fall",
            }
        ]
    )

    target_courses = {"REQ101": 3}
    intensive_courses = {"INT101": 0, "INT202": 0}
    target_rules = {
        "REQ101": [
            {
                "Credits": 3,
                "PassingGrades": "A,B",
                "FromOrd": 0,
                "ToOrd": 99,
            }
        ]
    }
    intensive_rules = {
        "INT101": [
            {
                "Credits": 0,
                "PassingGrades": "P",
                "FromOrd": 0,
                "ToOrd": 99,
            }
        ],
        "INT202": [
            {
                "Credits": 0,
                "PassingGrades": "P",
                "FromOrd": 0,
                "ToOrd": 99,
            }
        ],
    }

    _, intensive_df, _, _ = process_progress_report(
        df,
        target_courses,
        intensive_courses,
        target_rules,
        intensive_rules,
    )

    assert list(intensive_df.columns) == ["ID", "NAME", "INT101", "INT202"]
    assert intensive_df.loc[0, "INT101"] == "NR"
    assert intensive_df.loc[0, "INT202"] == "NR"
