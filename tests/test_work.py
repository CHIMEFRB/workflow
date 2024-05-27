"""Test the work object."""

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from workflow.cli.workspace import set, unset
from workflow.definitions.work import Work


def test_good_instantiation():
    """Test that the work object can be instantiated with the correct parameters."""
    work = Work(pipeline="test", site="local", user="test")
    assert work.pipeline == "test"


def test_bad_instantiation():
    """Test that the work object can't be instantiated without a pipeline."""
    with pytest.raises(ValidationError):
        Work()


def test_bad_pipeline():
    """Test that the work object can't be instantiated with empty pipeline."""
    with pytest.raises(ValidationError):
        Work(pipeline="", site="local", user="test")


def test_worskpace_unset():
    """Test that the work object can't be instantiated without a setted workspace."""
    runner = CliRunner()
    runner.invoke(unset)
    with pytest.raises(ValidationError):
        Work(pipeline="", site="local", user="test")
    runner.invoke(set, ["development"])


def test_pipeline_reformat():
    """Test that the work object can't be instantiated with empty pipeline."""
    with pytest.raises(ValidationError):
        Work(pipeline="sample test", site="local", user="test")


def test_bad_pipeline_char():
    """Test that the work object can't be instantiated with a pipeline containing
    invalid characters.
    """
    with pytest.raises(ValidationError):
        Work(pipeline="sample-test!", site="local", user="test")


@pytest.mark.parametrize("test_input", ["params", 123, [123, "123", {}], (32, "456")])
def test_bad_parameters_datatype(test_input):
    """Test parameters field not being a dict() object."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", parameters=test_input)


@pytest.mark.parametrize("test_input", ["params", 123, [123, "123", {}], (32, "456")])
def test_bad_results_datatype(test_input):
    """Test results field not being a dict() object."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", results=test_input)


def test_post_init_set():
    """Test post init assignment."""
    work = Work(pipeline="test", site="local", user="test")
    work.parameters = {}


def test_work_lifecycle():
    """Test that the work cannot be mutated between deposit and fetch stages."""
    work = Work(pipeline="test", site="local", user="test")
    work_again = Work(**work.payload)
    assert work.payload == work_again.payload


def test_json_serialization():
    """Test that the work can be serialized to JSON."""
    work = Work(pipeline="test", site="local", user="test")
    assert work.model_dump_json() is not None
    assert isinstance(work.model_dump_json(), str)


def test_check_work_payload():
    """Test that the work payload is correct."""
    work = Work(pipeline="test", site="local", user="test", parameters={"hi": "low"})
    assert work.payload["pipeline"] == "test"
    assert work.payload["parameters"] == {"hi": "low"}


def test_make_work_from_dict():
    """Test that the work object can be instantiated from a dictionary."""
    work = Work(pipeline="test", site="local", user="test", parameters={"hi": "low"})
    work_from_dict = Work.from_dict(work.payload)
    work_from_json = Work.from_json(work.model_dump_json())
    assert work == work_from_dict == work_from_json


def test_validation_after_instantiation():
    """Check if work validation works after instantiation."""
    work = Work(pipeline="test", site="local", user="test")
    with pytest.raises(ValidationError):
        work.pipeline = 2
    with pytest.raises(ValidationError):
        work.parameters = 2


def test_timeout_exceeds_maximum():
    """Checks if validation works when timeout field is greater than 86400."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", timeout=86401)


def test_retries_exceeds_maximum():
    """Checks if validation works when retries field is greater than 5."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", retries=6)


@pytest.mark.parametrize("test_input", [0, 7, -5, 6.5, "11"])
def test_bad_priorities(test_input):
    """Checks validation for priority fields when out of range value is given."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", priority=test_input)


@pytest.mark.parametrize("test_input", [{}, 2, "123456", [1, 2, 3]])
def test_products_bad_datatype(test_input):
    """Checks validation for products field."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", products=test_input)


@pytest.mark.parametrize("test_input", [{}, 2, "123456", [1, 2, 3]])
def test_status_bad_datatype(test_input):
    """Checks validation for status field datatype."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", status=test_input)


@pytest.mark.parametrize("test_input", ["waiting", "cancelled"])
def test_status_bad_value(test_input):
    """Checks validation for status field value."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", site="local", user="test", status=test_input)


@pytest.mark.parametrize("test_input", ["here", "there"])
def test_site_bad_value(test_input):
    """Checks validation for site field value."""
    with pytest.raises(ValidationError):
        Work(pipeline="test", user="test", site=test_input)


def test_command_and_function():
    """Checks if command and function fields are mutually exclusive."""
    with pytest.raises(ValidationError):
        Work(
            pipeline="test",
            user="test",
            site="local",
            command=["test"],
            function="test",
        )


def test_bad_slack_notify():
    """Checks if slack_notify field is of type bool."""
    with pytest.raises(ValidationError):
        Work(
            pipeline="test",
            user="test",
            site="local",
            notify={"slack": {"channel": "test"}},
        )


def test_good_slack_notify():
    """Checks if slack_notify field is of type bool."""
    work = Work(
        pipeline="test",
        user="test",
        site="local",
        notify={"slack": {"channel_id": "test"}},
    )
    assert work.notify.slack.channel_id == "test"
