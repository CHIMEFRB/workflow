# Workflow CLI


## Runners

```bash
workflow run [PIPELINE]
```

!!! Note
    If the `work.function` is a Click CLI command, then `workflow run` will inherit the CLI default arguments and then merge them with the `work.parameters` specified in the work object. This allows for a single CLI to be used for both interactive and non-interactive workflows.
