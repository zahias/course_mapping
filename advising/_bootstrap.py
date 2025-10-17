# advising/_bootstrap.py

# This shim lets modules inside the 'advising' package keep their original imports
# like "from utils import ..." by aliasing them to "advising.utils" at import time.

import sys

# Only alias if not already provided by the app
try:
    from . import utils as _utils
    sys.modules.setdefault('utils', _utils)
except Exception:
    pass

try:
    from . import reporting as _reporting
    sys.modules.setdefault('reporting', _reporting)
except Exception:
    pass

try:
    from . import google_drive as _gdrive
    sys.modules.setdefault('google_drive', _gdrive)
except Exception:
    pass

try:
    from . import course_exclusions as _ce
    sys.modules.setdefault('course_exclusions', _ce)
except Exception:
    pass

try:
    from . import data_upload as _du
    sys.modules.setdefault('data_upload', _du)
except Exception:
    pass
