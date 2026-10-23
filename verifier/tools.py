"""The get_prerequisites call's checks: the event name is well formed, and the output is exactly what the graph says."""

from .checks import EVENT, result
from .data import GRAPHS


def verify_input(tool, value):
    if not EVENT.fullmatch(value.event):
        return result(False, f"event {value.event!r} is not a name of capital letters")
    return result(True, "input is valid")


def verify_output(tool, input_value, output_value, workspace):
    expected = sorted(GRAPHS[input_value.graph.value].get(input_value.event, []))
    if output_value.event != input_value.event or output_value.prerequisites != expected:
        return result(
            False, f"the prerequisites of {input_value.event} are {expected}", given=output_value.prerequisites
        )
    return result(True, "output is valid")
