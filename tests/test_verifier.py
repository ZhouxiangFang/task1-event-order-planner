"""The verifier, called as NanoAgent's sandbox calls it, with contract instances built from JSON: every answer to the
task and every tool output, judged against the definition of a valid order and the data."""

from __future__ import annotations

import random
from itertools import permutations
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output
from test_graphs import UNSOLVABLE, an_order, is_valid_order

import verifier
from contract import TOOLS, EventOrderOutput, Graph, GraphInput, PrerequisitesInput, Tool
from plugin.graphs import get_prerequisites, list_events
from verifier.data import GRAPHS

SMALL = [graph for graph in Graph if len(GRAPHS[graph.value]) <= 8]
LARGE_SOLVABLE = [graph for graph in Graph if graph not in SMALL and graph.value not in UNSOLVABLE]


def verify(graph: Graph, solvable: bool, order, workspace: Path) -> dict:
    """The verdict on an answer; the task has no reference tool."""
    output = build_output({"solvable": solvable, "order": list(order)}, EventOrderOutput)
    arguments = build_output({"graph": graph.value}, GraphInput)
    return verifier.verify_task("plan-event-order", arguments, output, None, str(workspace))


@pytest.mark.parametrize("graph", SMALL)
def test_accepts_exactly_the_valid_orders_of_a_small_graph(graph: Graph, tmp_path: Path) -> None:
    # Every order of each graph of at most 8 events; for a graph with none valid, this proves it has none.
    prerequisites = GRAPHS[graph.value]
    valid = 0
    for order in permutations(prerequisites):
        expected = is_valid_order(prerequisites, list(order))
        valid += expected
        assert verify(graph, True, order, tmp_path)["valid"] is expected, order
    assert (valid > 0) is (graph.value not in UNSOLVABLE)


@pytest.mark.parametrize("graph", LARGE_SOLVABLE)
def test_agrees_with_the_definition_on_sampled_orders_of_a_large_graph(graph: Graph, tmp_path: Path) -> None:
    prerequisites = GRAPHS[graph.value]
    rng = random.Random(580)
    for _ in range(300):
        order = an_order(prerequisites, rng.choice)
        assert verify(graph, True, order, tmp_path)["valid"] is True
        i = rng.randrange(len(order) - 1)
        swapped = order[:i] + [order[i + 1], order[i]] + order[i + 2 :]
        assert verify(graph, True, swapped, tmp_path)["valid"] is is_valid_order(prerequisites, swapped)
        shuffled = rng.sample(order, len(order))
        assert verify(graph, True, shuffled, tmp_path)["valid"] is is_valid_order(prerequisites, shuffled)


@pytest.mark.parametrize("graph", list(Graph))
def test_accepts_no_solution_only_for_a_graph_without_a_valid_order(graph: Graph, tmp_path: Path) -> None:
    none = graph.value in UNSOLVABLE
    verdict = verify(graph, False, [], tmp_path)
    assert verdict["valid"] is none and verdict["score"] == float(none)
    if none:
        events = sorted(GRAPHS[graph.value])
        assert verify(graph, True, events, tmp_path)["valid"] is False
        assert verify(graph, True, [], tmp_path)["valid"] is False
        verdict = verify(graph, False, events, tmp_path)
        assert verdict["valid"] is False and "empty" in verdict["message"]


def test_gives_partial_credit_for_an_order_that_breaks_some_prerequisites(tmp_path: Path) -> None:
    # g10 is the chain M C X A P H: swapping X and A breaks one of its five prerequisites.
    verdict = verify(Graph.G10, True, ["M", "C", "A", "X", "P", "H"], tmp_path)
    assert verdict["valid"] is False and verdict["score"] == pytest.approx(0.8)
    assert verdict["details"]["broken"] == ["X before A"]
    # Alphabetical order is no shortcut.
    assert verify(Graph.G10, True, ["A", "C", "H", "M", "P", "X"], tmp_path)["valid"] is False
    reverse = verify(Graph.G19, True, ["U", "V", "W", "X", "Y", "Z"], tmp_path)
    assert reverse["valid"] is False and reverse["score"] == 0.0


@pytest.mark.parametrize(
    ("order", "field", "names"),
    [
        (["S", "H", "AB"], "missing", ["E"]),  # an event left out
        (["S", "H", "AB", "E", "H"], "repeated", ["H"]),  # an event twice
        (["S", "H", "AB", "E", "Q"], "unknown", ["Q"]),  # an event the graph does not have
        (["s", "H", "AB", "E"], "unknown", ["s"]),  # a malformed name
        ([], "missing", ["AB", "E", "H", "S"]),  # nothing at all
    ],
)
def test_refuses_an_order_that_is_not_every_event_once(order, field, names, tmp_path: Path) -> None:
    verdict = verify(Graph.G03, True, order, tmp_path)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["details"][field] == names


def test_boundary_graphs(tmp_path: Path) -> None:
    assert verify(Graph.G17, True, ["K"], tmp_path)["valid"] is True  # one event
    assert verify(Graph.G17, True, ["K", "K"], tmp_path)["valid"] is False
    assert verify(Graph.G20, True, ["Q", "AF", "B"], tmp_path)["valid"] is True  # no prerequisites at all
    assert verify(Graph.G12, True, ["D", "K", "P", "AE"], tmp_path)["valid"] is True  # the only valid order
    assert verify(Graph.G13, False, [], tmp_path)["valid"] is True  # an event needs itself
    assert verify(Graph.G02, False, [], tmp_path)["valid"] is True  # a prerequisite the graph lacks


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"solvable": True},
        {"order": ["S", "H", "AB", "E"]},
        {"solvable": None, "order": []},
        {"solvable": True, "order": None},
        {"solvable": "yes", "order": []},
        {"solvable": 1, "order": []},
        {"solvable": True, "order": "S,H,AB,E"},
        {"solvable": True, "order": [1, 2]},
        {"solvable": True, "order": ["S", None]},
        {"solvable": True, "order": [["S"]]},
        {"solvable": False, "order": [], "reason": "a cycle"},
    ],
)
def test_a_malformed_answer_never_reaches_the_verifier(answer: dict) -> None:
    # NanoAgent builds every answer into its contract class first, and refuses one that does not fit.
    with pytest.raises(ValueError):
        build_output(answer, EventOrderOutput)


@pytest.mark.parametrize("arguments", [{}, {"graph": "g99"}, {"graph": "G01"}, {"graph": None}])
def test_a_malformed_task_input_is_refused(arguments: dict) -> None:
    with pytest.raises(ValueError):
        build_output(arguments, GraphInput)


def check(tool: str, value: dict, output: dict | None = None) -> bool:
    """Whether verify_input (without ``output``) or verify_output (with it) approves a tool call."""
    given, made = TOOLS[Tool(tool)]
    if output is None:
        return verifier.verify_input(tool, build_output(value, given))["valid"]
    return verifier.verify_output(tool, build_output(value, given), build_output(output, made), ".")["valid"]


def test_checks_tool_inputs() -> None:
    assert check("get_prerequisites", {"graph": "g03", "event": "AB"}) is True
    assert check("get_prerequisites", {"graph": "g03", "event": "ab"}) is False
    assert check("get_prerequisites", {"graph": "g03", "event": ""}) is False


@pytest.mark.parametrize("graph", list(Graph))
def test_approves_every_true_tool_output(graph: Graph, tmp_path: Path) -> None:
    events = plain_output(list_events(GraphInput(graph=graph), tmp_path))
    assert check("list_events", {"graph": graph.value}, events) is True
    for event in events["events"]:
        given = {"graph": graph.value, "event": event}
        output = plain_output(get_prerequisites(build_output(given, PrerequisitesInput), tmp_path))
        assert check("get_prerequisites", given, output) is True


@pytest.mark.parametrize(
    ("tool", "given", "output"),
    [
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": ["ZZ"]}),  # made-up events
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": ["AB", "E", "H"]}),  # one left out
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": ["S", "AB", "E", "H"]}),  # unsorted
        ("list_events", {"graph": "g03"}, {"graph": "g05", "events": ["AB", "E", "H", "S"]}),  # another graph
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "E", "prerequisites": []}),  # dropped
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "E", "prerequisites": ["AB"]}),  # one dropped
        ("get_prerequisites", {"graph": "g03", "event": "S"}, {"event": "S", "prerequisites": ["E"]}),  # made up
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "H", "prerequisites": ["AB", "H"]}),
    ],
)
def test_refuses_a_tool_output_that_is_not_what_the_graph_says(tool: str, given: dict, output: dict) -> None:
    assert check(tool, given, output) is False
