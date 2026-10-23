from __future__ import annotations

import re
from pathlib import Path

import pytest

from contract import Graph, GraphInput, PrerequisitesInput
from plugin.graphs import get_prerequisites, list_events
from verifier.data import GRAPHS
from verifier.graphs import has_valid_order

# Worked out by hand from each graph, apart from the code that computes it.
UNSOLVABLE = {"g01", "g02", "g08", "g09", "g13", "g14"}


def test_has_one_graph_per_contract_graph() -> None:
    assert set(GRAPHS) == {graph.value for graph in Graph}
    assert len(GRAPHS) == 20


@pytest.mark.parametrize("graph", list(Graph))
def test_names_are_capital_letters_listed_sorted_and_once(graph: Graph) -> None:
    for event, needs in GRAPHS[graph.value].items():
        assert re.fullmatch(r"[A-Z]+", event)
        assert all(re.fullmatch(r"[A-Z]+", needed) for needed in needs)
        assert needs == sorted(set(needs))


@pytest.mark.parametrize("graph", list(Graph))
def test_knows_which_graphs_have_a_valid_order(graph: Graph) -> None:
    assert has_valid_order(GRAPHS[graph.value]) is (graph.value not in UNSOLVABLE)


def test_lists_events_and_their_prerequisites(tmp_path: Path) -> None:
    assert list_events(GraphInput(graph=Graph.G03), tmp_path).events == ["AB", "E", "H", "S"]
    assert get_prerequisites(PrerequisitesInput(graph=Graph.G03, event="E"), tmp_path).prerequisites == ["AB", "H"]
    assert get_prerequisites(PrerequisitesInput(graph=Graph.G03, event="S"), tmp_path).prerequisites == []


def test_refuses_an_event_the_graph_does_not_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not an event of g03"):
        get_prerequisites(PrerequisitesInput(graph=Graph.G03, event="Z"), tmp_path)
    # g02's C needs G, which the graph does not list.
    assert "G" in get_prerequisites(PrerequisitesInput(graph=Graph.G02, event="C"), tmp_path).prerequisites
    with pytest.raises(ValueError, match="not an event of g02"):
        get_prerequisites(PrerequisitesInput(graph=Graph.G02, event="G"), tmp_path)
