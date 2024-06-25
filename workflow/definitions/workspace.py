"""Definition of Workflow Workspace Configuration."""

from typing import Any, Dict, List, Literal, Optional, Union

from docker.types import DriverConfig, Mount
from pydantic import BaseModel, Field, model_validator


class DockerDeployerNetwork(BaseModel):
    """Definition of Workflow Docker Deployer Network Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        attachable (Optional[bool]):
            Whether the network is attachable by external containers.
        driver (Literal["host", "bridge", "overlay"]):
            The driver to use for the network.
    """

    attachable: Optional[bool] = Field(
        title="attachable",
        description="Whether the overlay network is attachable by external containers.",
        examples=[True, False],
        default=None,
    )
    driver: Literal["host", "bridge", "overlay"] = Field(
        ...,
        title="driver",
        description="The driver to use for the network.",
        examples=["host", "bridge", "overlay"],
    )

    class Config:
        """Pydantic configuration for the DockerDeployerNetwork model."""

        allow_population_by_field_name = True
        # Allow extra fields in the model.
        extra = "allow"


class WorkspaceDockerDeployer(BaseModel):
    """Definition of Workflow Workspace Docker Deployer Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        client_url (str):
            The URL pointing to the client's exposed Docker daemon.
        volumes (Optional[Dict[str, Mount]]):
            The volumes to be created (if non-existing)
            and mounted to each Docker Service.
        networks (Optional[Dict[str, DockerDeployerNetwork]]):
            The networks to be created (if non-existing)
            and mounted to each Docker Service.
        labels (Optional[Dict[str, str]]):
            The custom key-value labels to be mounted to each Docker Service.
        constraints (Optional[List[str]]):
            The Docker constraints to constrain the scheduling of each Docker Service.
        log_driver (Optional[DriverConfig]):
            The log driver to determine where logs are sent to for each Docker Service.
    """

    client_url: str = Field(
        ...,
        title="client_url",
        description="The URL pointing to the client's exposed Docker daemon.",
        examples=[
            "http://localhost:2375",
            "tcp://localhost:4444",
            "unix://var/run/docker.sock",
        ],
    )
    volumes: Optional[Dict[str, Mount]] = Field(
        title="volumes",
        description=(
            "The volumes to be created (if non-existing) "
            "and mounted to each Docker Service."
        ),
        examples=[
            {
                "volume-mount": {
                    "type": "volume",
                    "target": "/test/",
                    "driver_config": {
                        "driver": "local",
                        "driver_opts": {
                            "type": "nfs",
                            "o": ("nfsvers=4.0,noatime,nodiratime,soft,addr=nfs,rw"),
                            "device": ":/",
                        },
                    },
                },
                "bind-mount": {"type": "bind", "target": "/data/", "source": "/data/"},
                "tmpfs-mount": {
                    "type": "tmpfs",
                    "target": "/dev/shm",  # nosec
                    "tmpfs_size": 10000000,
                },
            }
        ],
        default=None,
    )
    networks: Optional[Dict[str, DockerDeployerNetwork]] = Field(
        title="networks",
        description=(
            "The networks to be created (if non-existing) "
            "and mounted to each Docker Service."
        ),
        examples=[
            {
                "swarm-network": {"attachable": True, "driver": "overlay"},
                "local-network": {"driver": "bridge"},
            }
        ],
        default=None,
    )
    labels: Optional[Dict[str, str]] = Field(
        title="labels",
        description=(
            "The custom key-value labels to be attached to each Docker Service"
        ),
        examples=[{"label1": "value1", "label2": "value2"}],
        default=None,
    )
    constraints: Optional[List[str]] = Field(
        title="constraints",
        description=(
            "The Docker constraints to constrain "
            "the scheduling of each Docker Service"
        ),
        examples=[["node.role == worker", "node.labels.type == compute"]],
        default=None,
    )
    log_driver: Optional[DriverConfig] = Field(
        title="log_driver",
        description=(
            "The log driver to determine where logs "
            "are sent to for each Docker Service"
        ),
        examples=[
            {
                "name": "json-file",
                "options": {
                    "max-size": "200k",
                    "max-file": "10",
                    "labels": "production_status",
                },
            },
            {
                "name": "loki",
                "options": {
                    "loki-url": "http://loki:3100/loki/api/v1/push",
                    "loki-batch-size": "400",
                    "loki-batch-wait": "1s",
                    "loki-min-level": "info",
                    "loki-retries": "5",
                },
            },
        ],
        default=None,
    )

    class Config:
        """Pydantic configuration for the WorkspaceDockerDeployer model."""

        populate_by_name = True
        # Allow extra fields in the model.
        extra = "allow"


class Workspace(BaseModel):
    """Definition of Workflow Workspace Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        workspace (str): Name of the workflow workspace.
        sites (List[str]): Valid sites for workflow.
        http (Dict): Workflow HTTP URLs.
        deployers (Dict[str, Dict[Literal["docker"], WorkspaceDockerDeployer]]):
            Workflow Deployers.
    """

    workspace: str = Field(
        ...,
        title="Name of the workflow workspace.",
        description="Name describing the purpose/usecase of the workspace.",
        examples=["chimefrb", "champss"],
    )
    sites: List[str] = Field(
        ...,
        title="Valid sites for workflow.",
        description="""
        List of valid sites where work belonging to a workspace can be performed.
        """,
        examples=[["chime", "hco", "frb"]],
    )
    http: Dict[
        Literal["baseurls"],
        Dict[
            Literal[
                "buckets",
                "results",
                "schedules",
                "pipelines",
                "configs",
                "loki",
                "products",
            ],
            Union[str, List[str]],
        ],
    ] = Field(
        ...,
        title="Workflow HTTP URLs",
        description="Baseurls define, the backend services for the workflow system.",
    )
    deployers: Dict[str, Dict[Literal["docker"], WorkspaceDockerDeployer]] = Field(
        ...,
        title="Workflow Deployers",
        description="Deployer driver configs per site to deploy Workflow Deployments.",
    )

    @model_validator(mode="before")
    def pre_validation(cls, data: Any) -> Any:
        """Validate the Workspace model before creating the object.

        Args:
            data (Any): Workspace data to validate.

        Raises:
            ValueError: If a site in 'deployers' is not in 'sites'.

        Returns:
            Any: Validated Workspace data.
        """
        for site in data.get("deployers", {}):
            if site not in data.get("sites", []):
                raise ValueError(
                    f"Site '{site}' in deployers mapping is not in provided sites list."
                )
        return data

    class Config:
        """Pydantic configuration for the Workspace model."""

        populate_by_name = True
        # Allow extra fields in the model.
        extra = "allow"
