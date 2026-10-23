from __future__ import annotations

import re
from pathlib import Path

import pytest

from contract import Edge, Graph, GraphInput, PrerequisitesInput
from plugin.graphs import get_prerequisites, list_events, load_graphs, read_graph

# Worked out by hand from each graph, apart from the code that computes it.
UNSOLVABLE = {"g15", "g16", "g17", "g18", "g19", "g20"}


def test_bundles_one_graph_per_contract_graph() -> None:
    assert set(load_graphs()) == {graph.value for graph in Graph}
    assert len(load_graphs()) == 20


@pytest.mark.parametrize("graph", list(Graph))
def test_names_are_capital_letters_listed_sorted_and_once(graph: Graph) -> None:
    for event, needs in load_graphs()[graph.value].items():
        assert re.fullmatch(r"[A-Z]+", event)
        assert all(re.fullmatch(r"[A-Z]+", needed) for needed in needs)
        assert needs == sorted(set(needs))


@pytest.mark.parametrize("graph", list(Graph))
def test_the_answer_key_says_which_graphs_have_a_valid_order(graph: Graph, tmp_path: Path) -> None:
    assert read_graph(GraphInput(graph=graph), tmp_path).solvable is (graph.value not in UNSOLVABLE)


def test_lists_events_and_their_prerequisites(tmp_path: Path) -> None:
    assert list_events(GraphInput(graph=Graph.G04), tmp_path).events == ["AB", "E", "H", "S"]
    assert get_prerequisites(PrerequisitesInput(graph=Graph.G04, event="E"), tmp_path).prerequisites == ["AB", "H"]
    assert get_prerequisites(PrerequisitesInput(graph=Graph.G04, event="S"), tmp_path).prerequisites == []


def test_refuses_an_event_the_graph_does_not_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not an event of g04"):
        get_prerequisites(PrerequisitesInput(graph=Graph.G04, event="Z"), tmp_path)
    # g18's C needs G, which the graph does not list.
    assert "G" in get_prerequisites(PrerequisitesInput(graph=Graph.G18, event="C"), tmp_path).prerequisites
    with pytest.raises(ValueError, match="not an event of g18"):
        get_prerequisites(PrerequisitesInput(graph=Graph.G18, event="G"), tmp_path)


def test_the_answer_key_holds_every_prerequisite_as_an_edge(tmp_path: Path) -> None:
    key = read_graph(GraphInput(graph=Graph.G17), tmp_path)
    assert key.events == ["A", "B", "C"]
    assert key.edges == [Edge(before="A", after="B"), Edge(before="B", after="B"), Edge(before="B", after="C")]
