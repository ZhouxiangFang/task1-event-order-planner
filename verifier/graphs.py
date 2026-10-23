"""Whether a graph has a valid order, decided from the data in data.py."""


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
