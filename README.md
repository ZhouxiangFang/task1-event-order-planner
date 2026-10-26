# Event Order Planner

A `nanoagent.plugin/v0001` plugin. The agent is given the name of one of 20
bundled event graphs. It lists the graph's events, looks up each event's
prerequisites, then returns an order in which every event comes after all of its
prerequisites, or says that no such order exists, or that no graph has that
name. A deterministic verifier, with no model, accepts any order that keeps
every prerequisite.

## Tools

| Tool | Does |
|---|---|
| `list_events` | Gives every event of a graph; fails with "no graph found" for a name no graph has |
| `get_prerequisites` | Gives the events that must happen before one event of a graph |

| Task | Does |
|---|---|
| `plan-event-order` | Orders a graph's events so each comes after its prerequisites, or says no order exists or no graph has that name. Runner `agent`, with `list_events` and `get_prerequisites` |

Input: `{"graph": "g18"}`, a name from `g01` to `g20`.
Output: `{"status": "ordered", "order": [...]}`, `{"status": "no_valid_order", "order": []}`,
or `{"status": "no_graph_found", "order": []}`.

## Layout

```text
.
├── nanoagent.yaml   # manifest: tools, tasks, permissions
├── contract.py      # each tool's and task's typed input and output
├── src/plugin/      # the MCP server and the tool
├── verifier/        # the deterministic verifier and the graph data
├── tests/           # tests for the data, the tool and the verifier
├── ui/              # how results are drawn
└── product/         # the product page
```

## Develop and run

Needs Git, [uv](https://docs.astral.sh/uv/) and Python 3.12 or later (uv fetches one if needed). No network access or API key at run time.

```bash
git clone https://github.com/ZhouxiangFang/task1-event-order-planner.git
cd task1-event-order-planner
uv sync --extra dev
uv run pytest
uv run ruff check .
```

To check the plugin against every NanoAgent publishing rule:

```bash
uvx --from "git+https://github.com/RUSH-LAB/nanoagent#subdirectory=nanoagent" nanoagent plugin inspect .
```

On RUSH Lab, open the plugin and ask its chat, for example, "Order the events of
graph g18". The result card shows the verifier's verdict.
