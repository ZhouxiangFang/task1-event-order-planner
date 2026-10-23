# Task1 Event Order Planner

A `nanoagent.plugin/v0001` plugin. The agent is given one of 20 bundled event
graphs. It reads each event's prerequisites and returns an order in which
every event comes after all of its prerequisites, or says that no such order
exists. A deterministic verifier accepts **any** order that keeps every
prerequisite, so graphs with many valid orders are judged fairly.

## Tools

| Tool | Does | Code |
|---|---|---|
| `list_events` | Lists every event of a graph, sorted by name | `src/plugin/graphs.py` |
| `get_prerequisites` | Gives the events that must happen before one event; refuses an event the graph does not list | `src/plugin/graphs.py` |
| `read_graph` | The answer key: every event and prerequisite of a graph, and whether it has a valid order. It runs before the agent as the task's `reference` and is never one of the agent's tools | `src/plugin/graphs.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `plan-event-order` | Orders a graph's events so each comes after its prerequisites, or says no order exists | `agent`, with `list_events` and `get_prerequisites`; reference `read_graph` |

The input is `{"graph": "g01"}` … `{"graph": "g20"}`. The ids are neutral on
purpose, so the id never hints at the answer. The agent submits
`{"solvable": true, "order": [...]}`, or `{"solvable": false, "order": []}`
when no valid order exists. It does not give a reason.

### Graphs

Events are named by capital letters, not always consecutive (`B`, `Q`, `AF`, `PC`, …).
`X → Y` means X must happen before Y. The data is in `src/plugin/graphs.json`.

| Graph | Prerequisites | Case | Valid order? |
|---|---|---|---|
| g01 | `K` alone | one event | yes |
| g02 | `AF`, `B`, `Q`, no edges | every order is valid | yes |
| g03 | M→C→X→A→P→H | chain not in alphabetical order; one valid order | yes |
| g04 | S→H, S→AB, H→E, AB→E | diamond; two valid orders | yes |
| g05 | T→N, G→N, N→W, G→J, W→R, J→R | two roots that merge | yes |
| g06 | K→D→Z; QA→QB; Y | three unconnected groups | yes |
| g07 | Z→Y→X→W→V→U | chain in reverse alphabetical order | yes |
| g08 | R→A, AA, F, L, P, U | one event before six | yes |
| g09 | B, CC, H, M, S, Y→O | six events before one | yes |
| g10 | D→K→P→AE, plus D→P, D→AE, K→AE | redundant edges; one valid order | yes |
| g11 | AC→AA, PC→AA, XX→BQ, AA→ZB, BQ→ZB | two-letter names | yes |
| g12 | each of C, F, J → each of V, X, Z | complete bipartite | yes |
| g13 | 16 events, 28 edges | medium layered graph | yes |
| g14 | 26 two-letter events, 51 edges | large layered graph | yes |
| g15 | A→P, P→Q, Q→P, Q→R | two events need each other | **no** |
| g16 | A→B→C→D→B, D→E | cycle of three with tails | **no** |
| g17 | A→B, B→B, B→C | an event needs itself | **no** |
| g18 | A→B→C, G→C, D; G is not listed | missing prerequisite | **no** |
| g19 | K→L→M; X→Y→W→X; T | one of three groups is a cycle | **no** |
| g20 | 20 events, 31 edges; OJ→TY→UO→GH→WG→RM→OJ | cycle of six hidden in a large graph | **no** |

## Layout

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs (none)
├── src/plugin/      # the MCP server (__main__.py, its IMPLEMENTATIONS), the tools (graphs.py) and the data (graphs.json)
├── tests/           # test_graphs.py (tools, data), test_verifier.py (verifier), test_oracle.py (independent checks), generate_graphs.py
├── ui/              # outputs are drawn from their JSON Schema
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier: tools.py checks each tool call, plan.py the task
```

`verifier/plan.py` judges the submitted answer against the pinned `read_graph`
output:

- **No valid order exists.** The answer passes only with `solvable: false` and an empty order.
- **A valid order exists.** `solvable: false` fails. The order must hold every event exactly
  once. Any unknown, repeated or missing event fails with score 0, and the verdict lists it.
  Then every edge `before → after` must have `before` earlier in the order. If some edges are
  broken, the answer fails with score = the fraction of edges kept, and the verdict lists the
  broken edges.

The verifier uses only the Python standard library: no model, network,
randomness or file access, so the same answer always gets the same verdict.
The data and the verifier are checked by tests that don't rely on the plugin's
own code (`tests/test_oracle.py`):

- The answer key's `solvable` (Kahn's algorithm in `src/plugin/graphs.py`)
  matches hand-worked labels and Python's standard `graphlib` for all 20 graphs.
- 17 graphs have at most 8 events. For each of them, the verifier is run on
  **every** possible order and must accept exactly the orders that meet the
  definition: each event once, and all of its prerequisites earlier. For the
  graphs with no solution, trying every order proves that none exists.
- For the large graphs g13 and g14, 300 random valid orders must pass. Swapped
  and shuffled variants must get the same verdict as the definition gives.
- g13, g14 and g20 come from the seeded generator `tests/generate_graphs.py`
  (seed 580, with a cycle planted in g20). A test checks that `graphs.json`
  still holds exactly what it generates. The other 17 graphs are written by
  hand, one per case.

## Develop and run

Needs Git, [uv](https://docs.astral.sh/uv/) and Python 3.12 or later (uv fetches one if needed). No network access or API key at run time.

```bash
git clone https://github.com/ZhouxiangFang/task1-event-order-planner.git
cd task1-event-order-planner
uv sync --extra dev
uv run pytest -v        # tools, data and verifier: correct, incorrect, missing, malformed and boundary answers
uv run ruff check .
```

To check the plugin against every NanoAgent publishing rule:

```bash
uvx --from "git+https://github.com/RUSH-LAB/nanoagent#subdirectory=nanoagent" nanoagent plugin inspect .
```

On RUSH Lab, open the plugin and ask its chat, for example, "Plan the event
order for graph g05". The result card shows the verifier's verdict.
