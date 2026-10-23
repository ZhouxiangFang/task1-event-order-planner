"""The 20 event graphs, each event -> the events that must happen before it, and whether a graph has a valid order.

This is the one copy of the data. The plugin's tools read it, and the verifier judges every tool output and every answer
against it, so no verdict trusts what a tool returned. Graph ids are shuffled (seed 580) so an id says nothing about the
answer. Three graphs (g01, g06, g15) come from tests/generate_graphs.py; the rest are written by hand, one per case.
"""

GRAPHS = {
    # no valid order: a cycle of six hidden among 20 events
    "g01": {
        "AW": [],
        "DB": ["XT"],
        "DC": ["DB", "WG"],
        "DS": [],
        "FE": ["IV"],
        "GH": ["FE", "UO"],
        "IV": ["OJ", "ZI", "ZM"],
        "LQ": ["UO"],
        "OJ": ["AW", "RM", "ZI"],
        "QR": [],
        "RM": ["DB", "LQ", "UO", "WG", "WZ"],
        "RR": ["UO", "ZM"],
        "SF": ["UO"],
        "TY": ["OJ", "ZM"],
        "UO": ["IV", "TY"],
        "WG": ["GH", "RR", "WZ"],
        "WZ": [],
        "XT": ["UO"],
        "ZI": [],
        "ZM": ["DS", "WZ"],
    },
    # no valid order: C needs G, which is not an event of the graph
    "g02": {"A": [], "B": ["A"], "C": ["B", "G"], "D": []},
    # a diamond: two valid orders
    "g03": {"AB": ["S"], "E": ["AB", "H"], "H": ["S"], "S": []},
    # two-letter names
    "g04": {"AA": ["AC", "PC"], "AC": [], "BQ": ["XX"], "PC": [], "XX": [], "ZB": ["AA", "BQ"]},
    # six events before one
    "g05": {"B": [], "CC": [], "H": [], "M": [], "O": ["B", "CC", "H", "M", "S", "Y"], "S": [], "Y": []},
    # 26 events with two-letter names, 51 prerequisites
    "g06": {
        "AQ": ["JK", "SZ", "TH"],
        "AR": ["GT", "ZW"],
        "BS": ["EW"],
        "CT": ["KX", "SZ", "WF"],
        "DD": ["HP", "MY", "RJ", "UO"],
        "EW": ["FB", "HL", "NB", "ZA"],
        "FB": ["QR", "ZA"],
        "GT": ["JK", "RH"],
        "HL": [],
        "HP": ["SZ"],
        "JK": [],
        "KD": [],
        "KX": ["SZ", "TH"],
        "LP": ["AR", "NB"],
        "MY": ["BS", "LP", "TH"],
        "NB": ["GT", "QR"],
        "QR": ["HL", "KD"],
        "RH": [],
        "RJ": ["SZ", "TH"],
        "SZ": ["EW", "RH"],
        "TH": ["EW", "GT", "LP", "UO"],
        "UO": ["ZA", "ZW"],
        "WF": ["BS", "SZ", "UO"],
        "ZA": ["RH"],
        "ZW": ["RH"],
        "ZZ": ["GT", "TH", "WF"],
    },
    # one event before six others
    "g07": {"A": ["R"], "AA": ["R"], "F": ["R"], "L": ["R"], "P": ["R"], "R": [], "U": ["R"]},
    # no valid order: a cycle of three with events before and after it
    "g08": {"A": [], "B": ["A", "D"], "C": ["B"], "D": ["C"], "E": ["D"]},
    # no valid order: one of three groups is a cycle
    "g09": {"K": [], "L": ["K"], "M": ["L"], "T": [], "W": ["Y"], "X": ["W"], "Y": ["X"]},
    # a chain not in alphabetical order: one valid order
    "g10": {"A": ["X"], "C": ["M"], "H": ["P"], "M": [], "P": ["A"], "X": ["C"]},
    # three unconnected groups
    "g11": {"D": ["K"], "K": [], "QA": [], "QB": ["QA"], "Y": [], "Z": ["D"]},
    # redundant prerequisites: every pair is ordered, one valid order
    "g12": {"AE": ["D", "K", "P"], "D": [], "K": ["D"], "P": ["D", "K"]},
    # no valid order: an event needs itself
    "g13": {"A": [], "B": ["A", "B"], "C": ["B"]},
    # no valid order: two events need each other
    "g14": {"A": [], "P": ["A", "Q"], "Q": ["P"], "R": ["Q"]},
    # 16 events, 28 prerequisites
    "g15": {
        "C": ["L", "Q"],
        "D": ["J"],
        "E": ["L", "Q"],
        "J": ["T", "U"],
        "K": ["E", "J"],
        "L": [],
        "N": ["E", "J", "Q"],
        "O": ["Q"],
        "Q": [],
        "S": ["L", "Q"],
        "T": ["L", "Q"],
        "U": ["L", "Q"],
        "V": ["J", "Q"],
        "X": ["D", "V"],
        "Y": ["K", "N", "S", "Z"],
        "Z": ["Q"],
    },
    # each of three events before each of three others
    "g16": {"C": [], "F": [], "J": [], "V": ["C", "F", "J"], "X": ["C", "F", "J"], "Z": ["C", "F", "J"]},
    # one event, no prerequisites
    "g17": {"K": []},
    # two roots that merge
    "g18": {"G": [], "J": ["G"], "N": ["G", "T"], "R": ["J", "W"], "T": [], "W": ["N"]},
    # a chain in reverse alphabetical order
    "g19": {"U": ["V"], "V": ["W"], "W": ["X"], "X": ["Y"], "Y": ["Z"], "Z": []},
    # three events, no prerequisites: every order is valid
    "g20": {"AF": [], "B": [], "Q": []},
}


def has_valid_order(prerequisites):
    """Whether every event fits in one order after all of its prerequisites (Kahn's algorithm): no prerequisite is
    missing from the graph and no prerequisites form a cycle."""
    if any(needed not in prerequisites for needs in prerequisites.values() for needed in needs):
        return False
    waiting = {event: len(set(needs)) for event, needs in prerequisites.items()}
    needed_by = {event: [] for event in prerequisites}
    for event, needs in prerequisites.items():
        for needed in set(needs):
            needed_by[needed].append(event)
    ready = [event for event, count in waiting.items() if count == 0]
    placed = 0
    while ready:
        placed += 1
        for event in needed_by[ready.pop()]:
            waiting[event] -= 1
            if waiting[event] == 0:
                ready.append(event)
    return placed == len(prerequisites)
