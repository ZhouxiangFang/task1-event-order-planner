"""The tools that read the event graphs, from verifier/data.py: the one copy, which the verifier also judges by."""

from __future__ import annotations

from pathlib import Path

from contract import EventsOutput, GraphInput, PrerequisitesInput, PrerequisitesOutput
from verifier.data import GRAPHS


def list_events(given: GraphInput, workspace: Path) -> EventsOutput:
    return EventsOutput(graph=given.graph, events=sorted(GRAPHS[given.graph.value]))


def get_prerequisites(given: PrerequisitesInput, workspace: Path) -> PrerequisitesOutput:
    prerequisites = GRAPHS[given.graph.value]
    if given.event not in prerequisites:
        raise ValueError(f"{given.event!r} is not an event of {given.graph.value}: list_events names its events")
    return PrerequisitesOutput(event=given.event, prerequisites=sorted(prerequisites[given.event]))
