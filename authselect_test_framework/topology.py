"""Authselect predefined well-known topologies."""

from __future__ import annotations

from enum import unique
from typing import TYPE_CHECKING, final

from pytest_mh import KnownTopologyBase, KnownTopologyGroupBase, Topology, TopologyDomain

from .config import AuthselectTopologyMark

if TYPE_CHECKING:
    from pytest_mh import TopologyMark
from .controllers import (
    LocalController,
    SSSDController,
    WinbindController,
)

__all__ = [
    "Profile",
    "ProfileGroup",
    "profile_from_topology_mark",
]


def profile_from_topology_mark(mark: TopologyMark) -> Profile:
    """
    Resolve :class:`Profile` enum member from a topology mark.
    """
    if not isinstance(mark, AuthselectTopologyMark):
        raise ValueError(f"Expected AuthselectTopologyMark, got {type(mark)}")

    for item in Profile:
        if mark is item.value:
            return item

    raise ValueError(f"Unknown topology mark: {mark.name}")


@final
@unique
class Profile(KnownTopologyBase):
    Local = AuthselectTopologyMark(
        name="local",
        topology=Topology(TopologyDomain("sssd", client=1)),
        controller=LocalController(),
        fixtures=dict(client="sssd.client[0]", provider="sssd.client[0]"),
    )

    SSSD = AuthselectTopologyMark(
        name="sssd",
        topology=Topology(TopologyDomain("sssd", client=1, ipa=1)),
        controller=SSSDController(),
        domains=dict(test="sssd.ipa[0]"),
        fixtures=dict(client="sssd.client[0]", ipa="sssd.ipa[0]", provider="sssd.ipa[0]"),
    )

    Winbind = AuthselectTopologyMark(
        name="winbind",
        topology=Topology(TopologyDomain("sssd", client=1, samba=1)),
        controller=WinbindController(),
        fixtures=dict(client="sssd.client[0]", samba="sssd.samba[0]", provider="sssd.samba[0]"),
    )


class ProfileGroup(KnownTopologyGroupBase):
    """
    Groups of authselect profiles for tests that run on every profile.

    The test is parametrized and runs once per profile in the group.

    .. code-block:: python
        :caption: Example usage

        @pytest.mark.topology(ProfileGroup.AnyProfile)
        def test_example(client: Client, mh_topology_mark: AuthselectTopologyMark):
            assert True
    """

    AnyProfile = [Profile.Local, Profile.SSSD, Profile.Winbind]
    """
    .. topology-mark:: ProfileGroup.AnyProfile
    """
