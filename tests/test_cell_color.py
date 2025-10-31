import sys
from pathlib import Path

import pytest


sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import cell_color, COMPLETION_COLOR_MAP  # noqa: E402


@pytest.mark.parametrize(
    "value, expected",
    [
        ("c", COMPLETION_COLOR_MAP["c"]),
        ("cr", COMPLETION_COLOR_MAP["cr"]),
        ("nc", COMPLETION_COLOR_MAP["nc"]),
        (" C ", COMPLETION_COLOR_MAP["c"]),
        ("CR | 3", COMPLETION_COLOR_MAP["cr"]),
    ],
)
def test_cell_color_collapsed_and_full_values(value, expected):
    assert cell_color(value) == expected


def test_cell_color_non_string_returns_blank():
    assert cell_color(None) == ""
