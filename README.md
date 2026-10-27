# Event Order Planner

Choose a graph from `g01` to `g20`. The agent looks up its events and prerequisites, then returns
an order with every prerequisite first. It reports an unknown graph or an impossible order when needed.
A deterministic verifier accepts any valid order.

## Tools

| Tool | Purpose |
|---|---|
| `list_events` | List a graph's events, or report an unknown graph. |
| `get_prerequisites` | List the events that must come before a given event. |

The `plan-event-order` task uses both tools to produce and verify an order.

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
