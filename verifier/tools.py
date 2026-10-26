"""The tool calls' checks: an event name is well formed, and each output is exactly what the graph says."""

from contract import Tool

from .checks import EVENT, result
from .data import GRAPHS


def verify_input(tool, value):
    # Any graph name may be asked for: the tool itself says when no graph has it.
    if tool is Tool.GET_PREREQUISITES and not EVENT.fullmatch(value.event):
        return result(False, f"event {value.event!r} is not a name of capital letters")
    return result(True, "input is valid")


def verify_output(tool, input_value, output_value, workspace):
    graph = GRAPHS.get(input_value.graph)
    if graph is None:
        return result(False, f"there is no graph named {input_value.graph!r}, so the tool must fail, not answer")
    if tool is Tool.LIST_EVENTS:
        expected = sorted(graph)
        if output_value.graph != input_value.graph or output_value.events != expected:
            return result(False, f"the events of {input_value.graph} are {expected}", given=output_value.events)
        return result(True, "output is valid")
    if input_value.event not in graph:
        return result(False, f"{input_value.event} is not an event of {input_value.graph}, so the tool must fail")
    expected = sorted(graph[input_value.event])
    if output_value.event != input_value.event or output_value.prerequisites != expected:
        return result(
            False, f"the prerequisites of {input_value.event} are {expected}", given=output_value.prerequisites
        )
    return result(True, "output is valid")
