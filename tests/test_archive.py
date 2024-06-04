"""Test the archive module."""

import logging
import os
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from workflow.definitions.work import Work
from workflow.lifecycle.archive import http, posix, run, s3
from workflow.utils import read

workspace_path = (
    Path(__file__).parent.parent / "workflow" / "workspaces" / "sample-test.yaml"
)
WORKSPACE = read.workspace(workspace_path)


@pytest.fixture(scope="module")
def directory():
    """Create a temporary directory.

    Yields:
        directory (Path): Path to temporary directory.
    """
    directory = Path("tmp_test")
    directory.mkdir(exist_ok=True)
    yield directory
    shutil.rmtree(directory)


@pytest.fixture
def work():
    """Return a Work instance."""
    test_plot = Path("test_plot.txt")
    test_product = Path("test_product.txt")
    test_plot.touch()
    test_product.touch()
    yield Work(
        user="tester",
        site="local",
        pipeline="test-pipeline",
        id="pytest",
        plots=[test_plot.as_posix()],
        products=[test_product.as_posix()],
    )
    test_plot.unlink(missing_ok=True)
    test_product.unlink(missing_ok=True)


def test_s3_env_vars_set():
    """Test the environment for S3 vars."""
    assert os.getenv("WORKFLOW_S3_ENDPOINT") == "play.min.io"
    assert os.getenv("WORKFLOW_S3_ACCESS_KEY") == "Q3AM3UQ867SPQQA43P2F"
    assert (
        os.getenv("WORKFLOW_S3_SECRET_KEY")
        == "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
    )


def test_successful_run_archive(work):
    """Test the run function."""
    run(work, WORKSPACE)


def test_bad_method_run_archive(caplog, work, workspace=WORKSPACE):
    """Test the run function."""
    with pytest.raises(ValidationError):
        work.config.archive.products = "bad_method"
        work.config.archive.plots = "bad_method"
        run(work, workspace)


def test_excluded_method_run_archive(caplog, work, workspace=WORKSPACE):
    """Test the run function."""
    work.config.archive.products = "bypass"
    work.config.archive.plots = "bypass"
    workspace["config"]["archive"]["products"]["methods"] = ["copy"]
    workspace["config"]["archive"]["plots"]["methods"] = ["copy"]
    with caplog.at_level(logging.WARNING):
        run(work, workspace)
    assert (
        f"Archive method {work.config.archive.products} not allowed for products by workspace."  # noqa: E501
        in caplog.text
    )
    assert (
        f"Archive method {work.config.archive.plots} not allowed for plots by workspace."  # noqa: E501
        in caplog.text
    )


def test_storage_unset_run_archive(caplog, work, workspace=WORKSPACE):
    """Test the run function."""
    workspace["config"]["archive"]["products"]["storage"] = None
    workspace["config"]["archive"]["plots"]["storage"] = None
    with caplog.at_level(logging.WARNING):
        run(work, workspace)
    assert "storage has not been set for products in workspace." in caplog.text
    assert "storage has not been set for plots in workspace." in caplog.text


class TestS3:
    """Test S3 archive methods."""

    def test_s3_bypass(self):
        """Test the bypass method."""
        assert s3.bypass(Path("none"), []) is True

    def test_s3_copy(self, work):
        """Test the copy method."""
        file = work.plots[0]
        path = Path("workflow/testing/s3/method/copy")
        result = s3.copy(path, [file])
        assert result is True

    def test_s3_delete(self):
        """Test the delete method."""
        with pytest.raises(NotImplementedError):
            s3.delete(Path("none"), [])

    def test_s3_move(self, work):
        """Test the move method."""
        file = work.plots[0]
        path = Path("workflow/testing/s3/method/move")
        result = s3.move(path, [file])
        assert result is True

    def test_s3_permissions(self):
        """Test the permissions method."""
        with pytest.raises(NotImplementedError):
            s3.permissions(Path("none"), [])


class TestPosix:
    """Test POSIX archive methods."""

    def test_posix_bypass(self):
        """Test the bypass method."""
        assert posix.bypass(Path("none"), []) is True

    def test_posix_copy(self, work, directory):
        """Test the copy method."""
        file = work.plots[0]
        path = directory / "workflow/20240501" / "posix" / "method" / "copy"
        result = posix.copy(path, [file])
        assert result is True
        assert (path / file).exists()

    def test_posix_delete(self, work, directory):
        """Test the delete method."""
        file = work.plots[0]
        path = directory / "workflow/20240501" / "posix" / "method" / "delete"
        result = posix.delete(path, work.plots)
        assert result is True
        assert not Path(file).exists()
        assert len(work.plots) == 0

    def test_posix_move(self, work, directory):
        """Test the move method."""
        file = work.plots[0]
        path = directory / "workflow/20240501" / "posix" / "method" / "move"
        result = posix.move(path, [file])
        assert result is True
        assert (path / file).exists()
        assert not Path(file).exists()

    def test_posix_permissions(self):
        """Test the permissions method."""
        pass


class TestHttp:
    """Test HTTP archive methods."""

    def test_http_bypass(self):
        """Test the bypass method."""
        assert http.bypass(Path("none"), []) is True

    def test_http_copy(self):
        """Test the copy method."""
        with pytest.raises(NotImplementedError):
            http.copy(Path("none"), [])

    def test_http_delete(self):
        """Test the delete method."""
        with pytest.raises(NotImplementedError):
            http.delete(Path("none"), [])

    def test_http_move(self):
        """Test the move method."""
        with pytest.raises(NotImplementedError):
            http.move(Path("none"), [])

    def test_http_permissions(self):
        """Test the permissions method."""
        with pytest.raises(NotImplementedError):
            http.permissions(Path("none"), [])
