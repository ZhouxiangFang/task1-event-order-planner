"""Each tool call's checks: the input is well formed, and the output is exactly what the graph says."""

from contract import Tool

from .checks import EVENT, result
from .graphs import GRAPHS


def verify_input(tool, value):
    if tool is Tool.GET_PREREQUISITES and not EVENT.fullmatch(value.event):
        return result(False, f"event {value.event!r} is not a name of capital letters")
    return result(True, "input is valid")


def verify_output(tool, input_value, output_value, workspace):
    graph = GRAPHS[input_value.graph.value]
    if tool is Tool.LIST_EVENTS:
        expected = sorted(graph)
        if output_value.graph != input_value.graph or output_value.events != expected:
            return result(False, f"the events of {input_value.graph.value} are {expected}", given=output_value.events)
    else:
        expected = sorted(graph.get(input_value.event, []))
        if output_value.event != input_value.event or output_value.prerequisites != expected:
            return result(
                False, f"the prerequisites of {input_value.event} are {expected}", given=output_value.prerequisites
            )
    return result(True, "output is valid")
