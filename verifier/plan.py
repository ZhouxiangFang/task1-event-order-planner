"""The plan-event-order task's check: any order that keeps every prerequisite passes, not one fixed answer."""

from .checks import order_problem, result


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract EventOrderOutput; ``reference``: read_graph's GraphOutput for the same graph."""
    graph = arguments.graph.value
    if reference.graph != arguments.graph:
        return result(False, f"the answer key is not of {graph}")
    if not reference.solvable:
        if output.solvable:
            return result(False, f"{graph} has no valid order, but the answer gives one")
        if output.order:
            return result(False, "the order must be empty when solvable is false", order=output.order)
        return result(True, f"{graph} has no valid order, as the answer says")
    if not output.solvable:
        return result(False, f"{graph} has a valid order, but the answer says it has none")
    problem = order_problem(output.order, reference.events)
    if problem:
        return result(False, problem.pop("message"), **problem)
    position = {event: index for index, event in enumerate(output.order)}
    broken = [
        f"{edge.before} before {edge.after}" for edge in reference.edges if position[edge.before] > position[edge.after]
    ]
    edges = len(reference.edges)
    if broken:
        return result(
            False,
            f"{len(broken)} of {edges} prerequisites are out of order",
            score=1 - len(broken) / edges,
            broken=broken,
        )
    return result(True, f"all {edges} prerequisites hold in the order of {len(output.order)} events")
