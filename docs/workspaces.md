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

In order to run workflow, pre-configured from container images, it is recommended to set the `workflow set workspace` command during the container build process. For example, in a Dockerfile:

    ```dockerfile
    FROM python:3.8-slim-buster

    RUN set -ex \
        pip install workflow && \
        workflow workspace set development
    ```

## Workspace YAML format

### `workspace`

This key states the name of the workspace.

    ```yaml
    workspace: "test-workspace"
    ```

### `sites`

Under the 'sites' key is where a list of strings naming the sites that
are allowed when running Workflow. Eg:

    ```yaml
    sites:
      - local
    ```

### `archive`

The 'archive' key describes the storage sites that are available. Valid
keys are:

- `mounts`, which should contain a key for every valid site listed under
  `sites` giving its root mount point.

      ```yaml
      archive:
      mounts:
        local: "./"
      ```

### `http`

The `http` key contains the configuration for requests that utilise http.
It is here that we set the base URLs for Workflow's dependant services.

- `baseurls`, this should contain a URL for each of the six services that
  Workflow is able to use. These comprise:

  - Buckets database
  - Results database
  - Pipelines API
  - Products API
  - Loki logs
  - MinIO object storage

  An example of this section of the YAML file:

      ```yaml
      http:
        baseurls:
          buckets: http://localhost:8001
          results: http://localhost:8002
          pipelines: http://localhost:8003
          products: http://localhost:8004
          minio: http://localhost:8005
          loki: http://localhost:8005/loki/api/v1/push
      ```

### `config`

- `archive`

  - `results`, this key enables or disables the functionality to copy Work
    entries across to the Results database upon their completion. Valid values
    are either:

        ```yaml
        # To enable
        results: true
        # To disable
        results: false

        ```

  - `plots`, this sets the archiving methods and storage type for plots produced
    when using Workflow. It has the following keys:

    - `methods`, this is a list that sets the methods enabled by the workspace admin
      these can be a including any of the following: `bypass`, `move`, `copy`, `delete`.
    - `storage`, this tells Workflow what storage type it will use to archive
      the plots, which can be either: `s3`, `posix`, or `http` (currently only
      has place-holding code).

            ```yaml
            plots:
              methods: ["move", "delete"]
              storage: "s3"
            ```

  - `products`, this sets the archiving methods and storage type for the products
    produced. It has the same keys as `plots`, above, and those have the same options.

    - `methods`, same as above.
    - `storage`, same as above.

          ```yaml
          products:
            methods: ["bypass", "copy"]
            storage: "posix"
          ```

  - `permissions`, this is used by the archiver to determine how to set the permissions
    for each storage type. Although, 's3' is included here, MinIO handles permissions
    internally.

    - `s3`
      - `user`
      - `group`
    - `posix`

      - `command`, this is an f-string template that defines the command that you wish
        to use to set the directory permissions.
      - `user`, the user to use in the permissions command.
      - `group`, the group to use in the permissions command.

            ```yaml
            posix:
              group: "chime-frb-rw"
              command: "setfacl -R m g:{group}:rw {path}"
            ```

Below is an example of the `config` section of the workspace YAML.

    ```yaml
    config:
      archive:
        results: true
        plots:
          methods: ["move", "delete"]
          storage: "s3"
        products:
          methods: ["bypass", "copy"]
          storage: "posix"
        permissions:
          s3:
            user: "user1"
            group: "group1"
          posix:
            group: "group1"
            command: "setfacl -R -m g:{group}:r {path}"
    ```

- `slack`, WIP; to be implemented.
