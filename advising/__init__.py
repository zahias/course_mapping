# advising/__init__.py

# IMPORTANT: bootstrap must run before importing modules that use top-level imports
from . import _bootstrap  # noqa: F401

# Re-export page entry points for convenience
from .eligibility_view import student_eligibility_view  # noqa: F401
from .full_student_view import full_student_view        # noqa: F401
from .advising_history import render_advising_history   # noqa: F401
