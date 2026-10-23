"""The plan-event-order task's check: any order that keeps every prerequisite passes, not one fixed answer."""

from .checks import has_valid_order, order_problem, result
from .data import GRAPHS


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract EventOrderOutput, judged against the graph itself (the task has no reference tool)."""
    graph = arguments.graph.value
    prerequisites = GRAPHS[graph]
    if sorted(arguments.events) != sorted(prerequisites):
        return result(False, f"the task's events are not those of {graph}", given=arguments.events)
    if not has_valid_order(prerequisites):
        if output.solvable:
            return result(False, f"{graph} has no valid order, but the answer gives one")
        if output.order:
            return result(False, "the order must be empty when solvable is false", order=output.order)
        return result(True, f"{graph} has no valid order, as the answer says")
    if not output.solvable:
        return result(False, f"{graph} has a valid order, but the answer says it has none")
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
