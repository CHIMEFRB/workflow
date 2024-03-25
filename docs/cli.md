# Workflow CLI


## Runners

```bash
workflow run [PIPELINE]
```

!!! Note
    If the `work.function` is a Click CLI command, then `workflow run` will inherit the CLI default arguments and then merge them with the `work.parameters` specified in the work object. This allows for a single CLI to be used for both interactive and non-interactive workflows.

# Pipelines CLI

## Overview

This CLI tool provides a command-line interface for interacting with the Pipelines server, enabling users to manage workflow pipelines efficiently. It supports various operations, such as deploying, listing, counting, and managing the lifecycle of pipeline configurations and schedules.

## Usage

The CLI tool offers the following commands for interacting with the workflow pipelines:

### Get server info

Get the current version of the pipelines server and info about configuration.

#### Command: `workflow pipelines version`

Example output:

```json
{
    'client': {
        'baseurl': 'http://localhost:8001',
        'timeout': 15.0,
        'token': None
    },
    'server': {
        'version': '2.6.1'
    }
}
```

### List pipelines

List all pipelines or scheduled pipelines.

#### Command: `workflow pipelines ls [OPTIONS]`
#### Options:
* `--schedule: For interacting with the Schedule API.`

Example output:

```shell
                   Workflow Pipelines
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ ID                       ┃ Name    ┃ Status  ┃ Stage ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ 65fc4dae5ffde0e8dbeebc61 │ example │ created │ 1     │
│ 65fc4eda5ffde0e8dbeebc65 │ example │ created │ 1     │
│ 65fc50065ffde0e8dbeebc69 │ example │ created │ 1     │
└──────────────────────────┴─────────┴─────────┴───────┘
```

### Count pipelines

Count pipelines configurations per collection.

#### Command: `workflow pipelines count [OPTIONS]`
#### Options:
* `--schedule: For interacting with the Schedule API.`

Example output:

```shell
                Workflow Pipelines
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Name                      ┃ Count              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ example                   │ 3                  │
├───────────────────────────┼────────────────────┤
│ Total                     │ 3                  │
└───────────────────────────┴────────────────────┘
```

### Deploy pipeline configurations

Deploy a workflow pipeline or schedule from a YAML file.

#### Command: `workflow pipelines deploy <FILENAME> [OPTIONS]`
#### Options:
* `--schedule: For interacting with the Schedule API.`

Example output:

```shell
                Workflow Pipelines
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ IDs                                            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 65fc7450157ed72595b91a2c                       │
└────────────────────────────────────────────────┘
```

### Pipeline details

Get the whole payload for a pipeline configuration or schedule.

#### Command: `workflow pipelines ps <PIPELINE> <ID> [OPTIONS]`
#### Options:
* `--schedule: For interacting with the Schedule API.`

Example output:

```shell
                 Workflow Pipelines
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pipeline: example                                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ {                                                 │
│   "id": "65fc69cf5ffde0e8dbeebcc1",               │
│   "name": "example",                              │
│   "current_stage": 1,                             │
│   "status": "created",                            │
│   "version": "1",                                 │
│   "creation": 1711040975.1336632,                 │
│   "start": null,                                  │
│   "stop": null,                                   │
│   "pipeline": {                                   │
│     "runs_on": null,                              │
│     "services": [],                               │
│     "steps": [                                    │
│       {                                           │
│         "name": "daily_monitoring_task",          │
│         "work_id": null,                          │
│         "runs_on": null,                          │
│         "services": [],                           │
│         "replicate_deployments": false,           │
│         "work": {                                 │
│           "user": "test",                         │
│           "site": "local",                        │
│           "function": "guidelines.example.alpha", │
│           "parameters": {                         │
│             "mu0": "${{ matrix.mu0 }}",           │
│             "alpha": "${{ matrix.alpha }}",       │
│             "sigma0": 22.0                        │
│           },                                      │
│           "pipeline": "daily-monitoring-task"     │
│         },                                        │
│         "status": "created",                      │
│         "stage": 1,                               │
│         "if_condition": "",                       │
│         "reason": null,                           │
│         "matrix": null,                           │
│         "evaluate_on_runtime": false,             │
│         "success_threshold": 1.0                  │
│       }                                           │
│     ]                                             │
│   },                                              │
│   "deployments": null,                            │
│   "user": "test"                                  │
│ }                                                 │
└───────────────────────────────────────────────────┘
```

### Stop a pipeline management

Kill a running pipeline.

#### Command: `workflow pipelines stop <PIPELINE> <ID> [OPTIONS]`
#### Options:
* `--schedule: For interacting with the Schedule API.`

Example output:

```shell
                Workflow Pipelines
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Stopped IDs                                    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 65fc69cf5ffde0e8dbeebcc1                       │
└────────────────────────────────────────────────┘
```

### Remove pipeline

Removes a pipeline, you can only use this command on pipelines with `status="cancelled"`

#### Command: `workflow pipelines rm <PIPELINE> <ID> [OPTIONS]`
#### Options:
* `--schedule: For interacting with the Schedule API.`

Example output:
