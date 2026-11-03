"""Tests for writing the active workspace."""

import threading
from pathlib import Path

import pytest
import yaml

from workflow.utils import write

WORKSPACE = {"workspace": "test", "sites": ["local"], "http": {"baseurls": {}}}


def test_writes_a_dictionary(tmp_path: Path):
    destination = tmp_path / "workspace.yml"
    write.workspace(WORKSPACE, destination)
    assert yaml.safe_load(destination.read_text()) == WORKSPACE


def test_copies_a_file_and_keeps_it(tmp_path: Path):
    source = tmp_path / "mine.yml"
    source.write_text(yaml.dump(WORKSPACE))
    destination = tmp_path / "active" / "workspace.yml"
    write.workspace(source, destination)
    assert yaml.safe_load(destination.read_text()) == WORKSPACE
    assert source.exists()


def test_same_workspace_leaves_no_backup(tmp_path: Path):
    destination = tmp_path / "workspace.yml"
    write.workspace(WORKSPACE, destination)
    write.workspace(WORKSPACE, destination)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["workspace.yml"]


def test_changed_workspace_backs_up_the_previous_one(tmp_path: Path):
    destination = tmp_path / "workspace.yml"
    write.workspace(WORKSPACE, destination)
    write.workspace({**WORKSPACE, "workspace": "other"}, destination)
    backups = list(tmp_path.glob("workspace.*.bak"))
    assert len(backups) == 1
    assert yaml.safe_load(backups[0].read_text()) == WORKSPACE
    assert yaml.safe_load(destination.read_text())["workspace"] == "other"


def test_rejects_other_sources(tmp_path: Path):
    with pytest.raises(ValueError):
        write.workspace("not a path", tmp_path / "workspace.yml")  # type: ignore


def test_readers_never_see_it_missing_or_empty(tmp_path: Path):
    """Runners sharing a home write the workspace while others read it."""
    destination = tmp_path / "workspace.yml"
    write.workspace(WORKSPACE, destination)
    stop = threading.Event()
    seen = []

    def writer(n: int):
        for i in range(200):
            write.workspace({**WORKSPACE, "workspace": f"w{n}-{i % 2}"}, destination)

    def reader():
        while not stop.is_set():
            try:
                seen.append(yaml.safe_load(destination.read_text()))
            except FileNotFoundError:
                seen.append("missing")

    readers = [threading.Thread(target=reader) for _ in range(4)]
    writers = [threading.Thread(target=writer, args=(n,)) for n in range(4)]
    for thread in readers + writers:
        thread.start()
    for thread in writers:
        thread.join()
    stop.set()
    for thread in readers:
        thread.join()
    assert seen
    assert all(isinstance(s, dict) and s.get("workspace") for s in seen)
    assert not list(tmp_path.glob(".workspace.yml.*.tmp"))
