"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    LIST_EVENTS = "list_events"
    GET_PREREQUISITES = "get_prerequisites"


class Task(Enum):
    PLAN_EVENT_ORDER = "plan-event-order"


class Graph(Enum):
    G01 = "g01"
    G02 = "g02"
    G03 = "g03"
    G04 = "g04"
    G05 = "g05"
    G06 = "g06"
    G07 = "g07"
    G08 = "g08"
    G09 = "g09"
    G10 = "g10"
    G11 = "g11"
    G12 = "g12"
    G13 = "g13"
    G14 = "g14"
    G15 = "g15"
    G16 = "g16"
    G17 = "g17"
    G18 = "g18"
    G19 = "g19"
    G20 = "g20"


GRAPH = "One of the bundled event graphs, g01 to g20"
EVENTS = "Every event in the graph, sorted by name; an event's name is capital letters, e.g. A or PC"
SOLVABLE = "Whether some order has every event exactly once, each after all of its prerequisites"


@dataclass
class GraphInput(Output):
    graph: Annotated[Graph, GRAPH]


@dataclass
class EventsOutput(Output):
    graph: Annotated[Graph, "The graph, as given"]
    events: Annotated[list[str], EVENTS]


@dataclass
class PrerequisitesInput(Output):
    graph: Annotated[Graph, GRAPH]
    event: Annotated[str, "One event of the graph, as list_events returned it"]


@dataclass
class PrerequisitesOutput(Output):
    event: Annotated[str, "The event, as given"]
    prerequisites: Annotated[list[str], "The events that must happen before it, sorted by name; empty when it has none"]


@dataclass
class EventOrderOutput(Output):
    solvable: Annotated[bool, SOLVABLE]
    order: Annotated[
        list[str], "Every event exactly once, each after all of its prerequisites; empty when solvable is false"
    ]


TOOLS = {
    Tool.LIST_EVENTS: (GraphInput, EventsOutput),
    Tool.GET_PREREQUISITES: (PrerequisitesInput, PrerequisitesOutput),
}
TASKS = {Task.PLAN_EVENT_ORDER: (GraphInput, EventOrderOutput)}
