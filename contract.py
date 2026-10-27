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


class Status(Enum):
    ORDERED = "ordered"
    NO_VALID_ORDER = "no_valid_order"
    NO_GRAPH_FOUND = "no_graph_found"


GRAPH = "The graph name from the task input, unchanged"
STATUS = (
    "ordered: valid event order; no_valid_order: prerequisites cannot be satisfied; no_graph_found: unknown graph"
)


@dataclass
class PlanInput(Output):
    graph: Annotated[str, "Graph name, g01 to g20; other names return no_graph_found"]


@dataclass
class EventsInput(Output):
    graph: Annotated[str, GRAPH]


@dataclass
class EventsOutput(Output):
    graph: Annotated[str, "The graph name, unchanged"]
    events: Annotated[list[str], "Every event of the graph, sorted by name; a name is capital letters, e.g. A or PC"]


@dataclass
class PrerequisitesInput(Output):
    graph: Annotated[str, GRAPH]
    event: Annotated[str, "The exact, case-sensitive name of one event that list_events returned"]


@dataclass
class PrerequisitesOutput(Output):
    event: Annotated[str, "The requested event name, unchanged"]
    prerequisites: Annotated[
        list[str],
        "Direct prerequisites, sorted by name: each must appear strictly before the requested event. "
        "Empty means no prerequisites. May include the event itself or a name list_events did not return.",
    ]


@dataclass
class EventOrderOutput(Output):
    status: Annotated[Status, STATUS]
    order: Annotated[
        list[str], "Every event exactly once, each after all of its prerequisites; empty unless status is ordered"
    ]


TOOLS = {
    Tool.LIST_EVENTS: (EventsInput, EventsOutput),
    Tool.GET_PREREQUISITES: (PrerequisitesInput, PrerequisitesOutput),
}
TASKS = {Task.PLAN_EVENT_ORDER: (PlanInput, EventOrderOutput)}
