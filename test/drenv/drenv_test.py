# SPDX-FileCopyrightText: The RamenDR authors
# SPDX-License-Identifier: Apache-2.0

import os

import yaml
import pytest

from drenv import cluster
from drenv import commands

EXAMPLE_ENV = os.path.join("envs", "example.yaml")
EXTERNAL_ENV = os.path.join("envs", "external.yaml")


def test_start_unknown():
    # Cluster does not exists, so it should fail.
    with pytest.raises(commands.Error):
        commands.run("drenv", "start", "--name-prefix", "unknown-", EXTERNAL_ENV)


def test_start(tmpenv):
    commands.run("drenv", "start", "--name-prefix", tmpenv.prefix, EXTERNAL_ENV)
    assert cluster.status(tmpenv.prefix + "cluster") == cluster.READY


def test_dump_without_prefix():
    out = commands.run("drenv", "dump", EXAMPLE_ENV)
    dump = yaml.safe_load(out)
    assert dump["profiles"][0]["name"] == "ex1"
    assert dump["profiles"][1]["name"] == "ex2"


def test_dump_with_prefix():
    out = commands.run("drenv", "dump", "--name-prefix", "test-", EXAMPLE_ENV)
    dump = yaml.safe_load(out)
    assert dump["profiles"][0]["name"] == "test-ex1"
    assert dump["profiles"][1]["name"] == "test-ex2"


def test_stop_unknown():
    # Does nothing, so should succeed.
    commands.run("drenv", "stop", "--name-prefix", "unknown-", EXTERNAL_ENV)


def test_stop(tmpenv):
    # Stop does nothing, so cluster must be ready.
    commands.run("drenv", "stop", "--name-prefix", tmpenv.prefix, EXTERNAL_ENV)
    assert cluster.status(tmpenv.prefix + "cluster") == cluster.READY


def test_delete_unknown():
    # Does nothing, so should succeed.
    commands.run("drenv", "delete", "--name-prefix", "unknown-", EXTERNAL_ENV)


def test_delete(tmpenv):
    # Delete does nothing, so cluster must be ready.
    commands.run("drenv", "delete", "--name-prefix", tmpenv.prefix, EXTERNAL_ENV)
    assert cluster.status(tmpenv.prefix + "cluster") == cluster.READY


def test_missing_addon(tmpdir):
    content = """
name: missing-test
profiles:
  - name: cluster
    external: true
    workers:
      - addons:
          - name: no-such-addon
"""
    path = tmpdir.join("missing-addon.yaml")
    path.write(content)
    with pytest.raises(commands.Error):
        commands.run("drenv", "start", str(path))
