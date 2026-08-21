---
type: concept
entity_type: library
title: workflow
subsystem: Workflow System
tags: [workflow, work, buckets, results, pipelines, scheduling, task-queue, mongodb, pydantic, datatrail, baseband-converter, baseband-analysis, L4_databases, workflow-results, workflow-pipelines, workflow-web, frb-devops]
---

# workflow

Python library (`workflow.core` v1.12.0) that defines the CHIME/FRB task lifecycle.
It provides the `Work` model, HTTP clients for the backend services, and a CLI for
interacting with the workflow system from the command line. Pipelines deposit `Work`
objects into `buckets`; worker processes withdraw and execute them; results are
archived to `results`.

GitHub: https://github.com/CHIMEFRB/workflow  
Docs: https://chimefrb.github.io/workflow-docs/  
PyPI: `workflow.core`

## System Connections

workflow (the library and its backends) is the asynchronous task bus connecting all
science-layer services. It does not process FRB events itself — it coordinates the
work that services do with those events.

```
Producers (deposit Work)          Consumers (withdraw Work)
─────────────────────────         ────────────────────────
L4_pipeline                   →   baseband-converter
baseband-converter            →   baseband-analysis (persistent_localization.py)
baseband-analysis             →   baseband-analysis (copy_to_canfar.py)
datatrail daemons             →   datatrail workers (replicators, deleters, state-updater)
L4_databases (sync_frb_master)→   intensity-ml pipeline workers

All via Buckets backend: http://frb-vsop.chime:8004
```

| Consumer / Producer | Workflow Pipeline Names | Role |
|---------------------|------------------------|------|
| **L4_pipeline** → **baseband-converter** | `baseband-converter` | Queues HDF5 conversion after Kotekan dump |
| **baseband-converter** → **baseband-analysis** | `baseband-localizer-outrigger-buffer` | Triggers localization after HDF5 ready |
| **baseband-analysis** → **copy workers** | `baseband-converter-copy-to-frb-baseband`, `baseband-converter-copy-to-canfar` | Queues data movement after localization |
| **datatrail** daemons | `datatrail-replicator-{site}-minoc`, `datatrail-deleter-{site}`, `datatrail-state-updater`, `datatrail-registration`, `datatrail-replica-heal`, `datatrail-deletion-notifications`, `policy-evaluator-file` | All datatrail file lifecycle operations |
| **L4_databases** | `intensity-ml` | Submits intensity ML analysis jobs |

**Backends in the Workflow System:**
- **workflow** (this repo) — the `Work` model, HTTP client, CLI (PyPI: `workflow.core`)
- **workflow-results** — Results backend (`:8005`), archives completed Work
- **workflow-pipelines** — Pipelines + Managers (`:8007`/`:8002`), orchestrates multi-step pipelines
- **workflow-web** — the operator UI for browsing Work, Results, and Pipelines

All four share the same MongoDB at `frb-vsop.chime:27018`. The Buckets backend (Work
queue) lives in `workflow-pipelines`' MongoDB namespace. All are deployed together via
**frb-devops** Swarm stacks.

## Architecture Overview

```
Pipeline code
  │  work.deposit()         ─→ Buckets backend (MongoDB, :8004)
  │
Worker process (CLI: workflow run)
  │  Work.withdraw()        ←─ Buckets backend
  │  execute.function() / execute.command()
  │  work.update()          ─→ Buckets backend (status update)
  │  archive                ─→ Results backend (MongoDB, :8005) + POSIX/S3
  │
Pipelines/Managers backend (:8007)
  │  pipeline definitions, scheduling, deployers
```

## The Work Object (`workflow.definitions.work.Work`)

The fundamental task unit. A Pydantic `BaseSettings` model — values sourced from
constructor args, then `WORKFLOW_*` env vars, then `/run/secrets/`.

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `pipeline` | str | Pipeline name (alphanumeric + hyphens only) |
| `site` | str | Site where work runs (`chime`, `kko`, `gbo`, `hco`, `aro`, `canfar`, `cedar`, `calcul-quebec`, `local`) |
| `user` | str | User who created the work |

### Optional payload fields

| Field | Type | Description |
|-------|------|-------------|
| `function` | str | Python dotted import path to call as `function(**parameters)` |
| `parameters` | Dict | Kwargs for `function`; ignored if `command` is set |
| `command` | List[str] | Shell command to run via `subprocess.run()` |
| `results` | Dict | Results stored by the worker after execution |
| `products` | List[str] | File paths of non-visual data products |
| `plots` | List[str] | File paths of visual data products |
| `tags` | List[str] | Searchable tags |
| `event` | List[int] | FRB event ID(s) the work is associated with |

### State machine fields (set by backend/worker)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | str | None | BSON ID assigned by MongoDB |
| `status` | Literal | `created` | `created` → `queued` → `running` → `success`/`failure` |
| `attempt` | int | 0 | Attempt count (incremented by backend) |
| `timeout` | int | 3600 | Seconds; range [1, 259200] |
| `retries` | int | 2 | Max retries before permanent failure |
| `priority` | int | 3 | 1–5, higher wins; 5 > 1 |
| `creation` | float | now() | Unix timestamp |
| `start` | float | None | Set by backend on withdraw |
| `stop` | float | None | Set by worker on completion |

### Config sub-object (`workflow.definitions.config.Config`)

`WORKFLOW_CONFIG_*` env prefix.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `archive.results` | bool | True | Archive results dict to Results backend |
| `archive.products` | str | `copy` | Strategy: `bypass`, `copy`, `move`, `delete` |
| `archive.plots` | str | `copy` | Strategy for plot files |
| `archive.logs` | str | `move` | Strategy for log files |
| `metrics` | bool | False | Push Prometheus metrics from lifecycle |
| `parent` | str | None | Parent pipeline ID (for chained pipelines) |
| `orgs` | List[str] | `["chimefrb"]` | GitHub orgs for access control |
| `teams` | List[str] | None | GitHub teams for access control |
| `strategy` | str | `strict` | `strict`: validates site against workspace; `relaxed`: skips |

### Notify sub-object (`workflow.definitions.notify.Notify`)

Slack notification config. `WORKFLOW_NOTIFY_SLACK_*` env prefix.

| Field | Description |
|-------|-------------|
| `channel_id` | Slack channel ID |
| `member_ids` | Slack user IDs to DM |
| `message` | Custom message text |
| `results` / `products` / `plots` | Whether to include each in the notification |
| `blocks` | Raw Slack block kit dict |
| `reply` | Written back by the lifecycle after sending |

### Key Work methods

```python
# Deposit (create) work in the queue
work = Work(pipeline="my-pipeline", site="chime", user="shinybrar")
work.deposit(return_ids=True)   # → List[str] of MongoDB IDs

# Withdraw (claim) work for execution
work = Work.withdraw(pipeline="my-pipeline", site="chime")

# Update status/results in-place
work.update()

# Delete from queue
work.delete()
```

`function` and `command` are mutually exclusive — setting both raises `ValueError`.

Results dict is capped at 4 MB — use `products` for large data.

## HTTP Backends

`HTTPContext` manages connections to all backend services. Endpoint URLs are read from
the active workspace YAML (`~/.config/workflow/workspace.yml` by default).

| Service | Internal URL | Public URL | Purpose |
|---------|-------------|------------|---------|
| **Buckets** | `http://frb-vsop.chime:8004` | `https://frb.chimenet.ca/workflow/buckets` | Work queue (deposit, withdraw, update, delete) |
| **Results** | `http://frb-vsop.chime:8005` | `https://frb.chimenet.ca/workflow/results` | Archived work results |
| **Pipelines/v2** | `http://frb-vsop.chime:8007/v2` | `https://frb.chimenet.ca/workflow/pipelines/v2` | Pipeline definitions, configs, schedules |

All backed by MongoDB at `frb-vsop.chime:27018` (the Workflow MongoDB, port 27018 —
distinct from frb-master's MongoDB at 27017).

## Workspace Configuration

`workflow/workspaces/chimefrb.yml` is the production workspace. It defines:
- **sites**: `local`, `chime`, `kko`, `gbo`, `hco`, `aro`, `canfar`, `cedar`, `calcul-quebec`
- **http.baseurls**: per-service endpoint lists (primary + fallback)
- **archive.posix**: per-site POSIX paths for products/plots
  - `chime`: `/data/chime/baseband/processed/workflow`
  - `canfar`: `/arc/projects/chime_frb/data/canfar/processed/workflow`
- **archive.s3**: per-site MinIO/S3 bucket config
- **deployers**: Docker daemon URL (`tcp://frb-vsop.chime:2375`) for pipeline deployers

Active workspace is selected by `WORKFLOW_WORKSPACE` env var or defaults to
`~/.config/workflow/workspace.yml`.

## Lifecycle (worker execution flow)

`workflow.lifecycle.attempt.work()` is the main worker loop entry point:

1. `Work.withdraw(pipeline=...)` — claim a queued work item
2. Optionally override `function` or `command` (CLI flags)
3. `execute.function(work)` — dynamically import `work.function` via dotted path,
   call `func(**work.parameters)` or `func.main(args=[...])` for Click commands
4. `execute.command(work)` — run `subprocess.run(work.command)`
5. Parse outcome: `(results, products, plots)` tuple or plain dict
6. `archive.*` — copy/move products and plots to POSIX or S3; push results to Results backend
7. `work.update()` — push final status (`success`/`failure`) to Buckets

Execution is timed; `work.stop` is set in the `finally` block.

## Daemons

Two background daemons run as Swarm services or standalone:

- **`audit`** (`workflow audit`): finds stale `running` work (stuck past timeout) and
  resets them to `queued` for retry.
- **`transfer`** (`workflow transfer`): moves work between backends (e.g., from one
  Buckets instance to another). Runs with configurable `--sleep`, `--limit`, `--cutoff`.

## CLI commands

```bash
workflow run          # Execute work: withdraw → execute → archive → update
workflow buckets      # Inspect / manage the Buckets backend
workflow results      # Query archived results
workflow pipelines    # Manage pipeline definitions
workflow configs      # Pipeline configuration management
workflow schedules    # Pipeline schedule management
workflow workspace    # Manage workspace configuration
workflow audit        # Run the audit daemon
workflow transfer     # Run the transfer daemon
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `WORKFLOW_PIPELINE` | Override pipeline name |
| `WORKFLOW_SITE` | Override site |
| `WORKFLOW_PRIORITY` | Override priority (1–5) |
| `WORKFLOW_TAGS` | Merge additional tags |
| `WORKFLOW_HTTP_TOKEN` / `WORKFLOW_TOKEN` / `GITHUB_TOKEN` / `GITHUB_PAT` | Auth token |
| `WORKFLOW_HTTP_TIMEOUT` | HTTP timeout (seconds) |
| `WORKFLOW_S3_ENDPOINT` / `WORKFLOW_S3_ACCESS_KEY` / `WORKFLOW_S3_SECRET_KEY` | MinIO/S3 |
| `WORKFLOW_CONFIG_ARCHIVE_RESULTS` | Override archive.results |

Secrets also read from `/run/secrets/` (Docker secrets).

## Deployment (Dev)

`docker-compose.yml` at the repo root spins up a local dev stack:
- `pipelines` container — pipelines + managers server (`:8001`)
- `managers` container — pipeline manager (`:8002`)
- `buckets` container — work queue server (`:8004`)
- `results` container — results archive server (`:8005`)
- `mongo` container — MongoDB (`:27017`)

Production deployment is via Docker Swarm stacks in `frb-devops/stacks/core/workflow/`.

## Documentation

| Document | Content |
|----------|---------|
| [README.md](README.md) | Install, dev setup, testing, contributing |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [workflow/definitions/jsonschema.md](workflow/definitions/jsonschema.md) | How to generate/use JSON Schema from Pydantic Work model |
| [Workflow Docs](https://chimefrb.github.io/workflow-docs/) | Full documentation site (external) |

## Notes

- `Work` is a `BaseSettings` — instantiation reads env vars automatically. Always check
  whether `WORKFLOW_*` env vars are set before debugging unexpected field values.
- `config.strategy = "strict"` (default) validates `site` against the workspace's `sites`
  list. New compute sites must be added to the workspace YAML before work can be submitted there.
- Products/plots use `products` URL prefix (`https://frb.chimenet.ca/frb-master/v1/events/query-file?filename=`)
  to build accessible links for the workflow web UI.
- Loki log aggregation: `WORKFLOW_HTTP_LOKI_URL` or workspace `logging.loki` points to
  `https://frb.chimenet.ca/loki/loki/api/v1/push`.
