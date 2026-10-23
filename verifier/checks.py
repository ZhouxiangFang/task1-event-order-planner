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


def has_valid_order(prerequisites):
    """Whether every event fits in one order after all of its prerequisites (Kahn's algorithm): no prerequisite is
    missing from the graph and no prerequisites form a cycle."""
    if any(needed not in prerequisites for needs in prerequisites.values() for needed in needs):
        return False
    waiting = {event: len(set(needs)) for event, needs in prerequisites.items()}
    needed_by = {event: [] for event in prerequisites}
    for event, needs in prerequisites.items():
        for needed in set(needs):
            needed_by[needed].append(event)
    ready = [event for event, count in waiting.items() if count == 0]
    placed = 0
    while ready:
        placed += 1
        for event in needed_by[ready.pop()]:
            waiting[event] -= 1
            if waiting[event] == 0:
                ready.append(event)
    return placed == len(prerequisites)
