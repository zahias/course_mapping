"""Utilities for normalizing grade values in completion views."""


def collapse_pass_fail_value(val):
    """Normalize grade strings to completion shorthand for the toggle view."""
    if not isinstance(val, str):
        return val

    parts = [p.strip() for p in val.split("|")]
    if parts and parts[0].upper() == "CR":
        return "cr"

    if len(parts) == 1 and parts[0].upper() == "NR":
        return "nc"

    if len(parts) == 2:
        credit_str = parts[1]
        try:
            return "c" if int(credit_str) > 0 else "nc"
        except ValueError:
            normalized_credit = credit_str.upper()
            if normalized_credit == "PASS":
                return "c"
            if normalized_credit == "FAIL":
                return "nc"

    return val
