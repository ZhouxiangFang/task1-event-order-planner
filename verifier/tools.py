"""Each tool call's checks: what the types cannot say about its input and output."""

from contract import Tool

from .checks import EVENT, names_problem, result


def verify_input(tool, value):
    if tool is Tool.GET_PREREQUISITES and not EVENT.fullmatch(value.event):
        return result(False, f"event {value.event!r} is not a name of capital letters")
    return result(True, "input is valid")


def verify_output(tool, input_value, output_value, workspace):
    if tool is Tool.LIST_EVENTS:
        problem = names_problem(output_value.events, "events")
        if output_value.graph != input_value.graph:
            problem = "the events are of another graph"
        if not output_value.events:
            problem = "a graph has at least one event"
    elif tool is Tool.GET_PREREQUISITES:
        problem = names_problem(output_value.prerequisites, "prerequisites")
        if output_value.event != input_value.event:
            problem = "the prerequisites are of another event"
    else:
        problem = names_problem(output_value.events, "events")
        if output_value.graph != input_value.graph:
            problem = "the answer key is of another graph"
        if any(edge.after not in output_value.events for edge in output_value.edges):
            problem = "an edge's after event is not an event of the graph"
    if problem:
        return result(False, problem)
    return result(True, "output is valid")
