# YAML Reference

Pipeline configuration files use YAML syntax, in a `.yml` or `.yaml` file extension.

## `version`

---

Version number to be used by the parser, currently only version 1 available.

## `name`

---

Name for identifying the pipeline configuration.

## `defaults`

---

Use `defaults` to create a `map` of default settings that will apply to all `Work` objects in the configuration.

```yaml title="defaults_example.yaml"
version: 1
name: "defaults_example"
defaults: # (1)
  user: "chimefrb"
  event: ["123456"]
```

1. All Work objects created on this configuration will have `user="chimefrb"` and `event=["123456"]` as default values.

## `schedule`

---

A map that specifies the schedule for the job. If this is not defined, the pipeline configuration will run only once.

## `schedule.cronspec`

---

A string that specifies the cron expression for when the job should run.

#### Example: Creating a pipeline with cronspec

```yaml title="cronspec_example.yaml"
version: 1
name: "cronspec_example"
schedule:
  cronspec: "30 4 * * 0" # (1)
pipeline: ...
```

1. This pipeline configuration will run at 04:30 every Sunday.

## `schedule.count`

---

An integer that specifies how many times the job should be triggered by the cronspec. Default is 0 (will execute every time the cronspec triggers).

#### Example: Creating a pipeline with cronspec and count

```yaml title="cronspec_count_example.yaml"
version: 1
name: "cronspec_count_example"
schedule:
  cronspec: "30 4 * * 0"
  count: 2 # (1)
pipeline: ...
```

1. Same as the previous example, this will execute at 04:30 every Sunday but only 2 times. Once this limit has been reached, the `Schedule` status will be `expired`.

## `matrix`

---

Just like in `defaults`, you can use `matrix` on the top level of the configuration to set several default settings for all the `Work` objects with the plus that this will generate several configurations from one file.

#### Example: Creating a top level matrix

```yaml title="matrix_example.yaml"
version: 1
name: "matrix_example"
matrix:
  event: ["123456", "456123"] # (1)
pipeline: ...
```

1. This matrix will generate 2 pipeline configurations, one for each event listed.

## `pipeline`

---

The main focus on a workflow pipeline configuration is the `pipeline` which contains all the steps to be executed, these steps can be separated on stages, all the steps inside a stage will execute concurrently.

## `pipeline.<step_name>`

---

Use this syntax to give your step a unique identifier on the pipeline. This name will work as a key, which value is a map of the step configuration. The `<step_name>` must start with a letter and contain only alphanumeric characters or `_`.

#### Example: Creating steps on a pipeline

```yaml
version: 1
name: "pipeline_test"
pipeline:
  task_1: # (1)
    stage: 1
    work:
      ...
  task_2:
    stage: 1
    work:
      ...
  task_2_1:
    stage: 2
    ...

```

1. Here `task_1` is the name of the step and its value is the map containing the keys `stage` and `work`.

## `pipeline.<step_name>.stage`

This represents the order of execution on the pipeline configuration. e.g. In the example `Creating steps on a pipeline` there are 2 steps on the stage 1 and one step on the stages 2; a `Work` object will be created for all of the steps on stage 1 and the stage2 will only be executed if stage1 has completed succesfully.

## `pipeline.<step_name>.work`

---

All the keys under `<step_name>.work` will represent the parameters for a `Work` object. For example:

```yaml
  baseband-localization: # (1)
    stage: 2
    work: # (2)
      parameters: # Work.parameters
      path: # Work.path
      event: # Work.event
      tags: # Work.tags
      function: # Work.function
      ...
```

1. Step name.
2. Fill this as if you were creating a `Work` object on console.

## `pipeline.<step_name>.matrix`

Just like in the top level `matrix` you can define a set of values that will be used for the step to generate `Work` objects depending on all the combinations of these values.

#### Example: Creating a matrix for a step

```yaml title="inner_matrix_example.yaml"
stage_1_a:
  stage: 1
  matrix: # (1)
    event: [123456, 645123]
    site: ["aro", "canfar"]
  work: # (2)
    site: ${{ matrix.site }}
    command: ["ls", "${{ matrix.event }}"]
```

1. This `matrix` will generate 4 `Work` objects, one per each combination: `[123456, "aro"], [123456, "canfar"], [645123, "aro"], [645123, "canfar"]`
2. The values will be replaced where the `matrix.<key_name>` are specified on the `Work` object.

Note: You cannot use the same key on a top level `matrix` and on a inner `matrix`. This will raise an error on your pipeline configuration.

## `pipeline.<step_name>.if`

Use `<step_name>.if` when you need to specify conditions for a step to execute. Workflow pipelines keeps a context for all configurations that can be referenced to access several values of the pipeline configuration.

#### Example: Running a step depending on results of previous steps

```yaml title="conditionals_example.yaml"
version: 1
name: "conditionals_tests"
pipeline:
  stage_1_step_1:
    stage: 1
    work:
      ...
  stage_1_step_2:
    stage: 1
    work:
      ...
  stage_2_step_1: # (1)
    stage: 2
    if: ${{ pipeline.stage_1_step_1.status == 'success' }}
    ...
```

1. This step will only be executed if `stage_1_step_1` executed successfully.

#### Example: Running a step using internal functions

```yaml title="internals_example.yaml"
version: 1
name: "internals_tests"
pipeline:
  stage_1_step_1:
    stage: 1
    work: ...
  stage_2_step_1:
    stage: 2
    work: ...
  stage_success:
    if: success # (1)
    work: ...
  stage_failure:
    if: failure # (2)
    work: ...
  stage_always:
    if: always # (3)
    work: ...
```

1. `success` will be true only if the whole pipeline has the status `success`.
2. `failure` will be true only if the whole pipeline has the status `failure`.
3. `always` will always be `True`.
