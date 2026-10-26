"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
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
EVENTS = "Every event of the graph, each once; an event's name is capital letters, e.g. A or PC"
SOLVABLE = "Whether some order has every event exactly once, each after all of its prerequisites"


@dataclass
class PlanInput(Output):
    graph: Annotated[Graph, GRAPH]
    events: Annotated[list[str], EVENTS]


@dataclass
class PrerequisitesInput(Output):
    graph: Annotated[Graph, "The graph ID from the task input; use the same ID for every prerequisite lookup"]
    event: Annotated[str, "The exact, case-sensitive name of one event from the task input's events list"]


@dataclass
class PrerequisitesOutput(Output):
    event: Annotated[str, "The requested event name, unchanged"]
    prerequisites: Annotated[
        list[str],
        "Direct prerequisites, sorted by name: each must appear strictly before the requested event. "
        "Empty means no prerequisites. May include the event itself or a name absent from the task's events list.",
    ]


@dataclass
class EventOrderOutput(Output):
    solvable: Annotated[bool, SOLVABLE]
    order: Annotated[
        list[str], "Every event exactly once, each after all of its prerequisites; empty when solvable is false"
    ]


TOOLS = {Tool.GET_PREREQUISITES: (PrerequisitesInput, PrerequisitesOutput)}
TASKS = {Task.PLAN_EVENT_ORDER: (PlanInput, EventOrderOutput)}
