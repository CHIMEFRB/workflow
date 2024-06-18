# JSON Schema

## Overview

JSON schema is the standard for defining the structure of JSON data. It is used to validate the structure of JSON data or by extension any system that accepts JSON Schema. For our usecase, we use JSON Schema derived from Pydantic Models in Python to generate a JSON Schema file. This, schema is then used by IDE's to provide autocompletion and validation for YAML files that are used to define the workflow workspaces and pipelines.

## Translate Pydanitc Models to JSON Schema

```python
from workflow.definitions.work import Work

schema = Work.model_json_schema(mode="serialization")
```

## Translate JSON Schema to Python Dataclasses

- Go to [JSON Schema Store](https://www.schemastore.org/json/) and download a JSON schema file, using

    ```bash
    curl -O https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json
    ```

- Follow the Code Generation instructions in the Pydantic documentation to create Python Code from the JSON schema file.

    ```bash
    pip install datamodel-code-generator
    datamodel-codegen  --input compose-spec.json --input-file-type jsonschema --output compose.py
    ```
