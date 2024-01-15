# Workspaces

A workspace is `yaml` configuration which defines the behavior of your workflow system. Nominally, a workspace defines any stateful aspects of your workflow system outside the scope of a `Work` Object, e.g. the `baseurls` for connecting to backend services.

A workspace is,

    - Project-Specific: Each project can have their own workspace, while sharing the same installation.
    - YAML-Based: Workspaces are defined in YAML files, which can be version controlled.
    - Stored in the client/user's home directory under the path `~/.workflow/workspaces/`

## How do I activate a workspace?

Workflow ships with a few workspaces. A `development` workspace that is used for testing and development, and a `chimefrb` workspace that is used by the CHIME/FRB Collaboration. You can list the available workspace by running:

    ```bash
    workflow workspace ls
    ```

Your project administrator should provide you with a workspace configuration file. This file can be hosted as a remote url, a local file or be pushed upstream to be packaged into workflow itself.

To activate a workspace,

    ```bash
    workflow workspace set development
    workflow workspace set https://raw.githubusercontent.com/your/repo/development.yaml
    workflow workspace set /path/to/development.yaml
    ```

To remove an active workspace,

    ```bash
    workflow workspace rm
    ```
This will only remove the active workspace, i.e. `~/.workflow/workspaces/active.yml`.

!!! Important
    Running workflow without a workspace set will result in an runtime error.

In order to purge all workspaces, from `~/.workflow/workspaces/` run:

    ```bash
    workflow workspace purge
    ```

### Configuration for container images

In order to run workflow, pre-configured from container images, it is recommended to set the  `workflow set workspace` command during the container build process. For example, in a Dockerfile:

    ```dockerfile
    FROM python:3.8-slim-buster

    RUN set -ex \
        pip install workflow && \
        workflow workspace set development
    ```
