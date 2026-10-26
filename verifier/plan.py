"""The plan-event-order task's check: any order that keeps every prerequisite passes, not one fixed answer."""

from contract import Status

from .checks import has_valid_order, order_problem, result
from .data import GRAPHS


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract EventOrderOutput, judged against the graph itself (the task has no reference tool)."""
    graph = arguments.graph
    prerequisites = GRAPHS.get(graph)
    if prerequisites is None:
        expected, fact = Status.NO_GRAPH_FOUND, f"there is no graph named {graph!r}"
    elif not has_valid_order(prerequisites):
        expected, fact = Status.NO_VALID_ORDER, f"{graph} has no valid order"
    else:
        expected, fact = Status.ORDERED, f"{graph} has a valid order"
    if output.status is not expected:
        return result(False, f"{fact}, but the answer says {output.status.value}")
    if expected is not Status.ORDERED:
        if output.order:
            return result(False, "the order must be empty unless status is ordered", order=output.order)
        return result(True, f"{fact}, as the answer says")
    problem = order_problem(output.order, list(prerequisites))
    if problem:
        return result(False, problem.pop("message"), **problem)
    position = {event: index for index, event in enumerate(output.order)}
    edges = [(needed, event) for event, needs in prerequisites.items() for needed in needs]
    broken = [f"{before} before {after}" for before, after in edges if position[before] > position[after]]
    if broken:
        return result(
            False,
            f"{len(broken)} of {len(edges)} prerequisites are out of order",
            score=1 - len(broken) / len(edges),
            broken=broken,
        )
    return result(True, f"all {len(edges)} prerequisites hold in the order of {len(output.order)} events")
