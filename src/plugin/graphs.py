"""The tools that read the event graphs, from verifier/data.py: the one copy, which the verifier also judges by."""

from __future__ import annotations

from pathlib import Path

from contract import EventsInput, EventsOutput, PrerequisitesInput, PrerequisitesOutput
from verifier.data import GRAPHS


def _graph(name: str) -> dict[str, list[str]]:
    if name not in GRAPHS:
        raise ValueError(f"no graph found: {name!r} is not one of the bundled graphs, g01 to g20")
    return GRAPHS[name]


def list_events(given: EventsInput, workspace: Path) -> EventsOutput:
    return EventsOutput(graph=given.graph, events=sorted(_graph(given.graph)))


def get_prerequisites(given: PrerequisitesInput, workspace: Path) -> PrerequisitesOutput:
    prerequisites = _graph(given.graph)
    if given.event not in prerequisites:
        raise ValueError(f"{given.event!r} is not an event of {given.graph}: list_events gives its events")
    return PrerequisitesOutput(event=given.event, prerequisites=sorted(prerequisites[given.event]))
