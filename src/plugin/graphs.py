"""The bundled event graphs (graphs.json) and the tools that read them."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from contract import (
    Edge,
    EventsOutput,
    Graph,
    GraphInput,
    GraphOutput,
    PrerequisitesInput,
    PrerequisitesOutput,
)

GRAPHS = Path(__file__).with_name("graphs.json")


@cache
def load_graphs() -> dict[str, dict[str, list[str]]]:
    """Each graph's id -> each of its events -> the events that must happen before it."""
    return {name: entry["prerequisites"] for name, entry in json.loads(GRAPHS.read_text()).items()}


def prerequisites_of(graph: Graph) -> dict[str, list[str]]:
    return load_graphs()[graph.value]


def solvable(prerequisites: dict[str, list[str]]) -> bool:
    """Whether every event fits in one order after all of its prerequisites (Kahn's algorithm):
    no prerequisite is missing from the graph and no prerequisites form a cycle."""
    if any(needed not in prerequisites for needs in prerequisites.values() for needed in needs):
        return False
    waiting = {event: len(set(needs)) for event, needs in prerequisites.items()}
    needed_by: dict[str, list[str]] = {event: [] for event in prerequisites}
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


def list_events(given: GraphInput, workspace: Path) -> EventsOutput:
    return EventsOutput(graph=given.graph, events=sorted(prerequisites_of(given.graph)))


def get_prerequisites(given: PrerequisitesInput, workspace: Path) -> PrerequisitesOutput:
    prerequisites = prerequisites_of(given.graph)
    if given.event not in prerequisites:
        raise ValueError(f"{given.event!r} is not an event of {given.graph.value}: list_events names its events")
    return PrerequisitesOutput(event=given.event, prerequisites=sorted(prerequisites[given.event]))


def read_graph(given: GraphInput, workspace: Path) -> GraphOutput:
    """The task's answer key, run before the agent and never shown to it: the whole graph and whether it has a valid
    order."""
    prerequisites = prerequisites_of(given.graph)
    edges = [
        Edge(before=needed, after=event) for event in sorted(prerequisites) for needed in sorted(prerequisites[event])
    ]
    return GraphOutput(graph=given.graph, events=sorted(prerequisites), edges=edges, solvable=solvable(prerequisites))
