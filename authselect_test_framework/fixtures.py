"""Pytest fixtures."""

from __future__ import annotations

import os

import pytest
from pytest_mh import TopologyMark

from .config import AuthselectTopologyMark
from .profiles import Profile, profile_from_topology_mark


@pytest.fixture(scope="session")
def datadir(request: pytest.FixtureRequest) -> str:
    """
    Data directory shared for all tests.

    :return: Path to the data directory ``(root-pytest-dir)/data``.
    :rtype: str
    """
    return os.path.join(request.node.path, "data")


@pytest.fixture(scope="module")
def moduledatadir(datadir: str, request: pytest.FixtureRequest) -> str:
    """
    Data directory shared for all tests within a single module.

    :return: Path to the data directory ``(root-pytest-dir)/data/$module_name``.
    :rtype: str
    """
    name = request.module.__name__
    return os.path.join(datadir, name)


@pytest.fixture(scope="function")
def testdatadir(moduledatadir: str, request: pytest.FixtureRequest) -> str:
    """
    Data directory for current test.

    :return: Path to the data directory ``(root-pytest-dir)/data/$module_name/$test_name``.
    :rtype: str
    """
    if not isinstance(request.node, pytest.Function):
        raise TypeError(f"Excepted pytest.Function, got {type(request.node)}")

    name = request.node.originalname
    return os.path.join(moduledatadir, name)


@pytest.fixture(scope="function")
def profile(mh_topology_mark: TopologyMark) -> Profile:
    """
    Current authselect profile for parametrized topology tests.

    :return: Profile enum member (``Profile.Local``, ``Profile.SSSD``, or ``Profile.Winbind``).
    :rtype: Profile
    """
    if not isinstance(mh_topology_mark, AuthselectTopologyMark):
        raise ValueError(f"Expected AuthselectTopologyMark, got {type(mh_topology_mark)}")

    return profile_from_topology_mark(mh_topology_mark)
