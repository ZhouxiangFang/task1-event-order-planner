"""How g15, g06 and g01 in verifier/graphs.py were made: seeded random layered graphs, g01 with a planted cycle.

The other 17 graphs are written by hand, one per case (see the README). `uv run python tests/generate_graphs.py`
prints the three; tests/test_oracle.py checks that verifier/graphs.py still holds exactly them.
"""

import json
import random
import string
from itertools import pairwise

SEED = 580


def names(rng: random.Random, count: int, two_letter: bool) -> list[str]:
    letters = string.ascii_uppercase
    return rng.sample([a + b for a in letters for b in letters] if two_letter else list(letters), count)


def layered(rng: random.Random, events: list[str], layers: int, extra: int) -> tuple[dict, list[list[str]]]:
    """An acyclic graph: ``events`` split into ``layers``, each event needing one or two of the layer before, plus
    ``extra`` prerequisites from any earlier layer."""
    rng.shuffle(events)
    cuts = sorted(rng.sample(range(1, len(events)), layers - 1))
    groups = [events[start:end] for start, end in zip([0, *cuts], [*cuts, len(events)])]
    needs: dict[str, set[str]] = {event: set() for event in events}
    for k in range(1, len(groups)):
        for event in groups[k]:
            needs[event] |= set(rng.sample(groups[k - 1], min(len(groups[k - 1]), rng.choice([1, 2]))))
    flat = [(k, event) for k, group in enumerate(groups) for event in group]
    added = 0
    while added < extra:
        (ka, a), (kb, b) = rng.sample(flat, 2)
        if ka < kb and a not in needs[b]:
            needs[b].add(a)
            added += 1
    return needs, groups


def generate() -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """The three graphs, each event's prerequisites sorted, and g01's planted cycle."""
    rng = random.Random(SEED)
    medium, _ = layered(rng, names(rng, 16, False), 5, 8)
    large, _ = layered(rng, names(rng, 26, True), 7, 16)
    cyclic, groups = layered(rng, names(rng, 20, True), 7, 6)
    # One event of each of layers 1 to 6 in a path, each needing the one before, and the first needing the last.
    cycle = [groups[k][0] for k in range(1, 7)]
    for before, after in pairwise(cycle):
        cyclic[after].add(before)
    cyclic[cycle[0]].add(cycle[-1])
    # Named by the shuffled ids the graphs have in verifier/graphs.py.
    graphs = {"g15": medium, "g06": large, "g01": cyclic}
    return {
        name: {event: sorted(needs) for event, needs in sorted(graph.items())} for name, graph in graphs.items()
    }, cycle


if __name__ == "__main__":
    print(json.dumps(generate()[0], indent=2))
