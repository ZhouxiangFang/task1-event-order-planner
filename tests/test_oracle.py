"""Checks of the data and the verifier that do not trust the plugin's own code: Python's graphlib, the seeded generator,
and, for every graph of at most 8 events, every possible order against the definition of a valid order."""

from __future__ import annotations

import random
from graphlib import CycleError, TopologicalSorter
from itertools import permutations
from pathlib import Path

import pytest
from generate_graphs import generate

import verifier
from contract import EventOrderOutput, Graph, GraphInput
from verifier.data import GRAPHS
from verifier.graphs import has_valid_order

SMALL = [graph for graph in Graph if len(GRAPHS[graph.value]) <= 8]
LARGE = [graph for graph in Graph if graph not in SMALL]


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


def graphlib_solvable(prerequisites: dict[str, list[str]]) -> bool:
    if any(needed not in prerequisites for needs in prerequisites.values() for needed in needs):
        return False
    try:
        tuple(TopologicalSorter(prerequisites).static_order())
    except CycleError:
        return False
    return True


def judge(graph: Graph, tmp_path: Path):
    """The verifier's verdict on (solvable, order) for ``graph``."""
    arguments = GraphInput(graph=graph)
    return lambda solvable, order: verifier.verify_task(
        "plan-event-order", arguments, EventOrderOutput(solvable=solvable, order=list(order)), None, str(tmp_path)
    )


@pytest.mark.parametrize("graph", list(Graph))
def test_the_verifier_s_solvability_agrees_with_graphlib(graph: Graph) -> None:
    prerequisites = GRAPHS[graph.value]
    assert has_valid_order(prerequisites) is graphlib_solvable(prerequisites)


def test_the_random_graphs_are_the_seeded_generator_s() -> None:
    graphs, cycle = generate()
    assert graphs == {name: GRAPHS[name] for name in ("g01", "g06", "g15")}
    sizes = {name: (len(graph), sum(map(len, graph.values()))) for name, graph in graphs.items()}
    assert sizes == {"g15": (16, 28), "g06": (26, 51), "g01": (20, 31)}
    # g01's planted cycle is in the data, each event needing the one before it.
    g01 = GRAPHS["g01"]
    assert all(before in g01[after] for before, after in zip(cycle, cycle[1:] + cycle[:1]))


@pytest.mark.parametrize("graph", SMALL)
def test_the_verifier_accepts_exactly_the_valid_orders_of_a_small_graph(graph: Graph, tmp_path: Path) -> None:
    prerequisites = GRAPHS[graph.value]
    verify = judge(graph, tmp_path)
    valid = 0
    for order in permutations(prerequisites):
        expected = is_valid_order(prerequisites, list(order))
        valid += expected
        assert verify(True, order)["valid"] is expected, order
    # No order passing the definition proves, by trying them all, that the graph has none.
    assert (valid > 0) is graphlib_solvable(prerequisites)
    assert verify(False, [])["valid"] is (valid == 0)


def test_graphs_have_the_number_of_valid_orders_the_readme_says() -> None:
    def count(name: str) -> int:
        prerequisites = GRAPHS[name]
        return sum(is_valid_order(prerequisites, list(order)) for order in permutations(prerequisites))

    assert {name: count(name) for name in ("g03", "g10", "g12", "g17", "g20")} == {
        "g03": 2,
        "g10": 1,
        "g12": 1,
        "g17": 1,
        "g20": 6,
    }


def random_valid_order(prerequisites: dict[str, list[str]], rng: random.Random) -> list[str]:
    order: list[str] = []
    while len(order) < len(prerequisites):
        order.append(
            rng.choice([e for e, needs in prerequisites.items() if e not in order and set(needs) <= set(order)])
        )
    return order


@pytest.mark.parametrize("graph", [graph for graph in LARGE if graph is not Graph.G01])
def test_the_verifier_agrees_with_the_definition_on_sampled_orders_of_a_large_graph(
    graph: Graph, tmp_path: Path
) -> None:
    prerequisites = GRAPHS[graph.value]
    verify = judge(graph, tmp_path)
    rng = random.Random(580)
    assert verify(True, TopologicalSorter(prerequisites).static_order())["valid"] is True
    for _ in range(300):
        order = random_valid_order(prerequisites, rng)
        assert verify(True, order)["valid"] is True
        i = rng.randrange(len(order) - 1)
        swapped = order[:i] + [order[i + 1], order[i]] + order[i + 2 :]
        assert verify(True, swapped)["valid"] is is_valid_order(prerequisites, swapped)
        shuffled = rng.sample(order, len(order))
        assert verify(True, shuffled)["valid"] is is_valid_order(prerequisites, shuffled)


def test_graphlib_finds_a_cycle_in_g01(tmp_path: Path) -> None:
    with pytest.raises(CycleError):
        tuple(TopologicalSorter(GRAPHS["g01"]).static_order())
    verify = judge(Graph.G01, tmp_path)
    assert verify(False, [])["valid"] is True
    assert verify(True, sorted(GRAPHS["g01"]))["valid"] is False
