from __future__ import annotations

from itertools import permutations
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output
from test_graphs import UNSOLVABLE

import verifier
from contract import TOOLS, EventOrderOutput, Graph, GraphInput, PrerequisitesInput, Tool
from plugin.graphs import get_prerequisites, list_events
from verifier.graphs import GRAPHS

SOLVABLE = [graph for graph in Graph if graph.value not in UNSOLVABLE]
NO_ORDER = [graph for graph in Graph if graph.value in UNSOLVABLE]


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON; the task has no reference.
def verify(graph: Graph, solvable: bool, order: list[str], workspace: Path) -> dict:
    output = build_output({"solvable": solvable, "order": order}, EventOrderOutput)
    arguments = build_output({"graph": graph.value}, GraphInput)
    return verifier.verify_task("plan-event-order", arguments, output, None, str(workspace))


def an_order(graph: Graph, pick) -> list[str]:
    """A valid order of ``graph``, taking ``pick`` of the events whose prerequisites are all placed."""
    prerequisites = GRAPHS[graph.value]
    order: list[str] = []
    while len(order) < len(prerequisites):
        ready = [e for e, needs in prerequisites.items() if e not in order and set(needs) <= set(order)]
        order.append(pick(ready))
    return order


@pytest.mark.parametrize("graph", SOLVABLE)
def test_approves_any_order_that_keeps_every_prerequisite(graph: Graph, tmp_path: Path) -> None:
    for order in (an_order(graph, min), an_order(graph, max)):
        verdict = verify(graph, True, order, tmp_path)
        assert verdict["valid"] is True and verdict["score"] == 1.0, verdict


def test_graphs_with_many_valid_orders_accept_each_of_them(tmp_path: Path) -> None:
    assert an_order(Graph.G03, min) != an_order(Graph.G03, max)
    assert all(verify(Graph.G20, True, list(order), tmp_path)["valid"] for order in permutations(["AF", "B", "Q"]))


@pytest.mark.parametrize("graph", NO_ORDER)
def test_approves_saying_no_order_exists_only_when_none_does(graph: Graph, tmp_path: Path) -> None:
    assert verify(graph, False, [], tmp_path)["valid"] is True
    events = sorted(GRAPHS[graph.value])
    assert verify(graph, True, events, tmp_path)["valid"] is False
    assert verify(graph, True, [], tmp_path)["valid"] is False
    verdict = verify(graph, False, events, tmp_path)
    assert verdict["valid"] is False and "empty" in verdict["message"]


@pytest.mark.parametrize("graph", SOLVABLE)
def test_refuses_saying_no_order_exists_when_one_does(graph: Graph, tmp_path: Path) -> None:
    verdict = verify(graph, False, [], tmp_path)
    assert verdict["valid"] is False and verdict["score"] == 0.0


def test_refuses_an_order_that_breaks_a_prerequisite_with_partial_credit(tmp_path: Path) -> None:
    # g10 is the chain M C X A P H: swapping X and A breaks one of its five prerequisites.
    assert verify(Graph.G10, True, ["M", "C", "X", "A", "P", "H"], tmp_path)["valid"] is True
    verdict = verify(Graph.G10, True, ["M", "C", "A", "X", "P", "H"], tmp_path)
    assert verdict["valid"] is False and verdict["score"] == pytest.approx(0.8)
    assert verdict["details"]["broken"] == ["X before A"]
    # Alphabetical order is no shortcut.
    assert verify(Graph.G10, True, sorted(["M", "C", "X", "A", "P", "H"]), tmp_path)["valid"] is False
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


def test_boundary_graphs(tmp_path: Path) -> None:
    assert verify(Graph.G17, True, ["K"], tmp_path)["valid"] is True  # one event
    assert verify(Graph.G17, True, ["K", "K"], tmp_path)["valid"] is False
    assert verify(Graph.G12, True, ["D", "K", "P", "AE"], tmp_path)["valid"] is True  # the only order
    assert verify(Graph.G12, True, ["D", "P", "K", "AE"], tmp_path)["valid"] is False
    assert verify(Graph.G13, False, [], tmp_path)["valid"] is True  # an event needs itself
    assert verify(Graph.G02, False, [], tmp_path)["valid"] is True  # a prerequisite the graph lacks
    assert verify(Graph.G02, True, ["A", "B", "C", "D"], tmp_path)["valid"] is False


def test_the_same_answer_always_gets_the_same_verdict(tmp_path: Path) -> None:
    order = an_order(Graph.G06, max)
    assert verify(Graph.G06, True, order, tmp_path) == verify(Graph.G06, True, list(order), tmp_path)


def check(tool: str, value: dict, output: dict | None = None) -> bool:
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
        assert check(
            "get_prerequisites",
            given,
            plain_output(get_prerequisites(build_output(given, PrerequisitesInput), tmp_path)),
        )


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
