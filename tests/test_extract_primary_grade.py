import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import extract_primary_grade_from_full_value

@pytest.mark.parametrize("value,expected", [
    ("F | 0, CR | 3", "CR | 3"),
    ("B- | 0, A | 3", "A | 3"),
])
def test_extract_primary_grade(value, expected):
    assert extract_primary_grade_from_full_value(value) == expected

