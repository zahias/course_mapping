import sys
from pathlib import Path

import pytest


sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import cell_color  # noqa: E402


@pytest.mark.parametrize(
    "value, expected",
    [
        ("c", "background-color: lightgreen"),
        ("cr", "background-color: #FFFACD"),
        ("nc", "background-color: pink"),
        (" C ", "background-color: lightgreen"),
        ("CR | 3", "background-color: #FFFACD"),
    ],
)
def test_cell_color_collapsed_and_full_values(value, expected):
    assert cell_color(value) == expected


def test_cell_color_non_string_returns_blank():
    assert cell_color(None) == ""
