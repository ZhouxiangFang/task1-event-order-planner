"""Checks shared by the verifiers. Pure functions of their arguments."""

import re
from collections import Counter

EVENT = re.compile(r"^[A-Z]+$")


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def names_problem(names, what):
    """What is wrong with a list of event names a tool returns (capital letters, sorted, each once), or None."""
    bad = [name for name in names if not EVENT.fullmatch(name)]
    if bad:
        return f"{what} holds names that are not capital letters: {bad}"
    if names != sorted(set(names)):
        return f"{what} must be sorted and name each event once"
    return None


def order_problem(order, events):
    """Details of how ``order`` fails to hold every event of ``events`` exactly once, or None."""
    counts = Counter(order)
    unknown = sorted(set(order) - set(events))
    repeated = sorted(event for event, count in counts.items() if count > 1)
    missing = sorted(set(events) - set(order))
    if not unknown and not repeated and not missing:
        return None
    return {
        "message": "the order must hold every event of the graph exactly once",
        "unknown": unknown,
        "repeated": repeated,
        "missing": missing,
    }
