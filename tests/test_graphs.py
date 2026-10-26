"""The data and the tools: every graph well formed, whether it has a valid order worked out three ways (by hand, by the
verifier's Kahn's algorithm and by Python's graphlib), the seeded graphs reproducible, and the tools true to the data."""

from __future__ import annotations

import re
from graphlib import CycleError, TopologicalSorter
from itertools import pairwise, permutations
from pathlib import Path

import pytest
from generate_graphs import generate

from contract import EventsInput, PrerequisitesInput
from plugin.graphs import get_prerequisites, list_events
from verifier.checks import has_valid_order
from verifier.data import GRAPHS

NAMES = sorted(GRAPHS)
# Worked out by hand from each graph, apart from the code that computes it.
UNSOLVABLE = {"g01", "g02", "g08", "g09", "g13", "g14"}
# Names no bundled graph has: out of range, the wrong case, unpadded, padded with spaces, or empty.
UNKNOWN = ["g00", "g21", "g99", "G03", "g3", " g03", "graph g03", ""]


def is_valid_order(prerequisites: dict[str, list[str]], order: list[str]) -> bool:
    """The definition, read straight off the data: every event once, each with all its prerequisites done first."""
    if sorted(order) != sorted(prerequisites):
        return False
    done: set[str] = set()
    for event in order:
        if not set(prerequisites[event]) <= done:
            return False
        done.add(event)
    return True


def an_order(prerequisites: dict[str, list[str]], pick) -> list[str]:
    """A valid order, taking ``pick`` of the events whose prerequisites are all placed each time."""
    order: list[str] = []
    while len(order) < len(prerequisites):
        order.append(pick([e for e, needs in prerequisites.items() if e not in order and set(needs) <= set(order)]))
    return order


def graphlib_solvable(prerequisites: dict[str, list[str]]) -> bool:
    if any(needed not in prerequisites for needs in prerequisites.values() for needed in needs):
        return False
    try:
        tuple(TopologicalSorter(prerequisites).static_order())
    except CycleError:
        return False
    return True


def test_has_twenty_well_formed_graphs_named_g01_to_g20() -> None:
    assert NAMES == [f"g{number:02d}" for number in range(1, 21)]
    for prerequisites in GRAPHS.values():
        for event, needs in prerequisites.items():
            assert re.fullmatch(r"[A-Z]+", event) and all(re.fullmatch(r"[A-Z]+", needed) for needed in needs)
            assert needs == sorted(set(needs))


@pytest.mark.parametrize("graph", NAMES)
def test_knows_which_graphs_have_a_valid_order(graph: str) -> None:
    prerequisites = GRAPHS[graph]
    assert has_valid_order(prerequisites) is graphlib_solvable(prerequisites) is (graph not in UNSOLVABLE)


def test_the_random_graphs_are_the_seeded_generator_s() -> None:
    graphs, cycle = generate()
    assert graphs == {name: GRAPHS[name] for name in ("g01", "g06", "g15")}
    sizes = {name: (len(graph), sum(map(len, graph.values()))) for name, graph in graphs.items()}
    assert sizes == {"g15": (16, 28), "g06": (26, 51), "g01": (20, 31)}
    # g01's planted cycle is in the data, each event needing the one before it.
    assert all(before in GRAPHS["g01"][after] for before, after in pairwise([*cycle, cycle[0]]))


def test_graphs_have_the_number_of_valid_orders_the_readme_says() -> None:
    def count(name: str) -> int:
        return sum(is_valid_order(GRAPHS[name], list(order)) for order in permutations(GRAPHS[name]))

    assert {name: count(name) for name in ("g03", "g10", "g12", "g17", "g20")} == {
        "g03": 2,
        "g10": 1,
        "g12": 1,
        "g17": 1,
        "g20": 6,
    }


@pytest.mark.parametrize("graph", NAMES)
def test_lists_every_event_of_a_graph(graph: str, tmp_path: Path) -> None:
    listed = list_events(EventsInput(graph=graph), tmp_path)
    assert listed.graph == graph and listed.events == sorted(GRAPHS[graph])


def test_gives_each_event_s_prerequisites(tmp_path: Path) -> None:
    assert get_prerequisites(PrerequisitesInput(graph="g03", event="E"), tmp_path).prerequisites == ["AB", "H"]
    assert get_prerequisites(PrerequisitesInput(graph="g03", event="S"), tmp_path).prerequisites == []


@pytest.mark.parametrize("name", UNKNOWN)
def test_says_no_graph_found_for_a_name_no_graph_has(name: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no graph found"):
        list_events(EventsInput(graph=name), tmp_path)
    with pytest.raises(ValueError, match="no graph found"):
        get_prerequisites(PrerequisitesInput(graph=name, event="A"), tmp_path)


def test_refuses_an_event_the_graph_does_not_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not an event of g03"):
        get_prerequisites(PrerequisitesInput(graph="g03", event="Z"), tmp_path)
    # g02's C needs G, which the graph does not list.
    assert "G" in get_prerequisites(PrerequisitesInput(graph="g02", event="C"), tmp_path).prerequisites
    with pytest.raises(ValueError, match="not an event of g02"):
        get_prerequisites(PrerequisitesInput(graph="g02", event="G"), tmp_path)
