[![Continuous Integration](https://github.com/CHIMEFRB/workflow/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/CHIMEFRB/workflow/actions/workflows/ci.yml) [![Continuous Deployment](https://github.com/CHIMEFRB/workflow/actions/workflows/cd.yml/badge.svg)](https://github.com/CHIMEFRB/workflow/actions/workflows/cd.yml) [![Coverage Status](https://coveralls.io/repos/github/CHIMEFRB/workflow/badge.svg?branch=main&t=WaYxol)](https://coveralls.io/github/CHIMEFRB/workflow?branch=main)

# Workflow

Workflow is a Python-based system designed to manage and automate any task in a structured manner. It provides a framework for defining (work), scheduling (buckets), sequencing (pipelines), executing (managers) and archiving (results) the output of any task. The system is designed to be modular with a low threshold of entry for new users, while also providing advanced features for power users.

For more information, please refer to the [Workflow documentation](https://chimefrb.github.io/workflow-docs/).

## Getting Started

To get started with the Workflow, you need to have Python 3.8.1 or later installed. You can then install the project's dependencies using Poetry:

### Install from PyPI

```bash
pip install workflow.core
```

### Install from Source

```bash
pip install git+https://github.com/chimefrb/workflow.git
```

Alternatively, you can add the Workflow project as a dependency to your own project using Poetry:

```bash
poetry add git+https://github.chime/chimefrb/workflow.git
```

## Contributing

Contributions to the Workflow project are welcome. Please ensure that any changes you make pass the project's tests and adhere to the project's coding standards.

### Setting Up Your Development Environment

```bash
git clone https://github.com/chimefrb/workflow.git
cd workflow
poetry install
pre-commit install
```

### Writing Your First Commit

```bash
git add file/you/changed.py
poetry run commitizen commit
```

### Running Tests

You can run the project's tests using Docker & Poetry:

```bash
docker compose up -d
poetry run pytest
```

## License

Workflow is licensed under the MIT license.

Copyright (c) 2024 CHIME/FRB Collaboration

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---
<p align="center">
  <a href="Some Love">
    <img src="https://forthebadge.com/images/badges/built-with-love.svg">
  </a>
</p>
