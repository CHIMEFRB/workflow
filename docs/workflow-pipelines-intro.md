# `workflow-pipelines`

A lightweight Python backend using Sanic that allows the creation and monitoring of pipelines configurations by parsing YAML files.

## Example

```yaml
version: "1"
name: "test-configuration"
schedule:
  cronspec: "*/2 * * * *"
  count: 4
defaults:
  user: "chimefrb"
  site: "canfar"
pipeline:
  test_stage_1:
    stage: 1
    work:
      command: ["ls", "-la"]
      tags: ["tag1", "tag2"]
  test_stage_2:
    stage: 2
    work:
      command: ["ls", "-la"]
      tags: ["tag1", "tag2"]
```
