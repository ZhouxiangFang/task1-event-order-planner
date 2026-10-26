"""The verifier, called as NanoAgent's sandbox calls it, with contract instances built from JSON: every answer to the
task and every tool output, judged against the definition of a valid order and the data."""

from __future__ import annotations

import random
from itertools import permutations
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output
from test_graphs import NAMES, UNKNOWN, UNSOLVABLE, an_order, is_valid_order

import verifier
from contract import TOOLS, EventOrderOutput, EventsInput, PlanInput, PrerequisitesInput, Tool
from plugin.graphs import get_prerequisites, list_events
from verifier.data import GRAPHS

SMALL = [graph for graph in NAMES if len(GRAPHS[graph]) <= 8]
LARGE_SOLVABLE = [graph for graph in NAMES if graph not in SMALL and graph not in UNSOLVABLE]
G03 = ["S", "AB", "H", "E"]  # a valid order of g03


def verify(graph: str, status: str, order, workspace: Path) -> dict:
    """The verdict on an answer to the task for the graph named ``graph``; there is no reference."""
    output = build_output({"status": status, "order": list(order)}, EventOrderOutput)
    arguments = build_output({"graph": graph}, PlanInput)
    return verifier.verify_task("plan-event-order", arguments, output, None, str(workspace))


@pytest.mark.parametrize("graph", SMALL)
def test_accepts_exactly_the_valid_orders_of_a_small_graph(graph: str, tmp_path: Path) -> None:
    # Every order of each graph of at most 8 events; for a graph with none valid, this proves it has none.
    prerequisites = GRAPHS[graph]
    valid = 0
    for order in permutations(prerequisites):
        expected = is_valid_order(prerequisites, list(order))
        valid += expected
        assert verify(graph, "ordered", order, tmp_path)["valid"] is expected, order
    assert (valid > 0) is (graph not in UNSOLVABLE)


@pytest.mark.parametrize("graph", LARGE_SOLVABLE)
def test_agrees_with_the_definition_on_sampled_orders_of_a_large_graph(graph: str, tmp_path: Path) -> None:
    prerequisites = GRAPHS[graph]
    rng = random.Random(580)
    for _ in range(300):
        order = an_order(prerequisites, rng.choice)
        assert verify(graph, "ordered", order, tmp_path)["valid"] is True
        i = rng.randrange(len(order) - 1)
        swapped = order[:i] + [order[i + 1], order[i]] + order[i + 2 :]
        assert verify(graph, "ordered", swapped, tmp_path)["valid"] is is_valid_order(prerequisites, swapped)
        shuffled = rng.sample(order, len(order))
        assert verify(graph, "ordered", shuffled, tmp_path)["valid"] is is_valid_order(prerequisites, shuffled)


@pytest.mark.parametrize("graph", NAMES)
def test_accepts_no_valid_order_only_for_a_graph_without_one(graph: str, tmp_path: Path) -> None:
    none = graph in UNSOLVABLE
    verdict = verify(graph, "no_valid_order", [], tmp_path)
    assert verdict["valid"] is none and verdict["score"] == float(none)
    # A bundled graph is never "no graph found".
    assert verify(graph, "no_graph_found", [], tmp_path)["valid"] is False
    if none:
        events = sorted(GRAPHS[graph])
        assert verify(graph, "ordered", events, tmp_path)["valid"] is False
        assert verify(graph, "ordered", [], tmp_path)["valid"] is False
        verdict = verify(graph, "no_valid_order", events, tmp_path)
        assert verdict["valid"] is False and "empty" in verdict["message"]


@pytest.mark.parametrize("name", UNKNOWN)
def test_accepts_no_graph_found_only_for_a_name_no_graph_has(name: str, tmp_path: Path) -> None:
    verdict = verify(name, "no_graph_found", [], tmp_path)
    assert verdict["valid"] is True and verdict["score"] == 1.0
    assert verify(name, "ordered", G03, tmp_path)["valid"] is False
    assert verify(name, "ordered", [], tmp_path)["valid"] is False
    assert verify(name, "no_valid_order", [], tmp_path)["valid"] is False
    verdict = verify(name, "no_graph_found", G03, tmp_path)
    assert verdict["valid"] is False and "empty" in verdict["message"]


def test_gives_partial_credit_for_an_order_that_breaks_some_prerequisites(tmp_path: Path) -> None:
    # g10 is the chain M C X A P H: swapping X and A breaks one of its five prerequisites.
    verdict = verify("g10", "ordered", ["M", "C", "A", "X", "P", "H"], tmp_path)
    assert verdict["valid"] is False and verdict["score"] == pytest.approx(0.8)
    assert verdict["details"]["broken"] == ["X before A"]
    # Alphabetical order is no shortcut.
    assert verify("g10", "ordered", ["A", "C", "H", "M", "P", "X"], tmp_path)["valid"] is False
    reverse = verify("g19", "ordered", ["U", "V", "W", "X", "Y", "Z"], tmp_path)
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
    verdict = verify("g03", "ordered", order, tmp_path)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["details"][field] == names


def test_boundary_graphs(tmp_path: Path) -> None:
    assert verify("g17", "ordered", ["K"], tmp_path)["valid"] is True  # one event
    assert verify("g17", "ordered", ["K", "K"], tmp_path)["valid"] is False
    assert verify("g20", "ordered", ["Q", "AF", "B"], tmp_path)["valid"] is True  # no prerequisites at all
    assert verify("g12", "ordered", ["D", "K", "P", "AE"], tmp_path)["valid"] is True  # the only valid order
    assert verify("g13", "no_valid_order", [], tmp_path)["valid"] is True  # an event needs itself
    assert verify("g02", "no_valid_order", [], tmp_path)["valid"] is True  # a prerequisite the graph lacks


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "ordered"},
        {"order": G03},
        {"status": None, "order": []},
        {"status": "ordered", "order": None},
        {"status": "yes", "order": []},
        {"status": "ORDERED", "order": G03},
        {"status": True, "order": []},
        {"status": "ordered", "order": "S,AB,H,E"},
        {"status": "ordered", "order": [1, 2]},
        {"status": "ordered", "order": ["S", None]},
        {"status": "ordered", "order": [["S"]]},
        {"status": "no_valid_order", "order": [], "reason": "a cycle"},
        {"solvable": True, "order": G03},
    ],
)
def test_a_malformed_answer_never_reaches_the_verifier(answer: dict) -> None:
    # NanoAgent builds every answer into its contract class first, and refuses one that does not fit.
    with pytest.raises(ValueError):
        build_output(answer, EventOrderOutput)


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"graph": None},
        {"graph": 3},
        {"graph": ["g03"]},
        {"graph": "g03", "events": ["AB", "E", "H", "S"]},
    ],
)
def test_a_malformed_task_input_is_refused(arguments: dict) -> None:
    with pytest.raises(ValueError):
        build_output(arguments, PlanInput)


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
    # Any graph name may be asked for: the tool says when no graph has it.
    for name in ["g03", *UNKNOWN]:
        assert check("list_events", {"graph": name}) is True


@pytest.mark.parametrize("graph", NAMES)
def test_approves_every_true_tool_output(graph: str, tmp_path: Path) -> None:
    given = {"graph": graph}
    assert check("list_events", given, plain_output(list_events(build_output(given, EventsInput), tmp_path)))
    for event in GRAPHS[graph]:
        given = {"graph": graph, "event": event}
        output = plain_output(get_prerequisites(build_output(given, PrerequisitesInput), tmp_path))
        assert check("get_prerequisites", given, output) is True


@pytest.mark.parametrize(
    ("tool", "given", "output"),
    [
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": ["S", "H", "E", "AB"]}),  # unsorted
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": ["AB", "E", "H"]}),  # one dropped
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": ["AB", "E", "H", "Q", "S"]}),  # made up
        ("list_events", {"graph": "g03"}, {"graph": "g03", "events": []}),  # none
        ("list_events", {"graph": "g03"}, {"graph": "g02", "events": ["AB", "E", "H", "S"]}),  # another name
        ("list_events", {"graph": "g99"}, {"graph": "g99", "events": []}),  # a graph that does not exist
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "E", "prerequisites": ["H", "AB"]}),  # unsorted
        ("get_prerequisites", {"graph": "g03", "event": "S"}, {"event": "S", "prerequisites": ["S"]}),  # made up
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "E", "prerequisites": []}),  # dropped
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "E", "prerequisites": ["AB"]}),  # one dropped
        ("get_prerequisites", {"graph": "g03", "event": "S"}, {"event": "S", "prerequisites": ["E"]}),  # made up
        ("get_prerequisites", {"graph": "g03", "event": "E"}, {"event": "H", "prerequisites": ["AB", "H"]}),
        ("get_prerequisites", {"graph": "g03", "event": "Z"}, {"event": "Z", "prerequisites": []}),  # no such event
        ("get_prerequisites", {"graph": "g99", "event": "A"}, {"event": "A", "prerequisites": []}),  # no such graph
    ],
)
def test_refuses_a_tool_output_that_is_not_what_the_graph_says(tool: str, given: dict, output: dict) -> None:
    assert check(tool, given, output) is False
