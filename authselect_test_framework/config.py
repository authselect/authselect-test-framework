from __future__ import annotations

from typing import Any, Mapping, Self, Tuple, Type

import pytest
from pytest_mh import (
    MultihostConfig,
    MultihostDomain,
    MultihostHost,
    MultihostRole,
    Topology,
    TopologyController,
    TopologyMark,
)

__all__ = [
    "AuthselectMultihostConfig",
    "AuthselectMultihostDomain",
    "AuthselectTopologyMark",
]


class AuthselectTopologyMark(TopologyMark):
    """
    Topology mark used by authselect system tests.

    In addition to the standard topology mark fields, it defines **domains**
    that are automatically configured on the client host.
    """

    def __init__(
        self,
        name: str,
        topology: Topology,
        *,
        controller: TopologyController | None = None,
        fixtures: dict[str, str] | None = None,
        domains: dict[str, str] | None = None,
    ) -> None:
        super().__init__(name, topology, controller=controller, fixtures=fixtures)

        self.domains: dict[str, str] = domains if domains is not None else {}
        """Map hosts to SSSD domains."""

    def export(self) -> dict:
        d = super().export()
        d["domains"] = self.domains

        return d

    @classmethod
    def CreateFromArgs(cls, item: pytest.Function, args: Tuple, kwargs: Mapping[str, Any]) -> Self:
        if len(args) != 2 and len(args) != 3:
            nodeid = item.parent.nodeid if item.parent is not None else ""
            error = f"{nodeid}::{item.originalname}: invalid arguments for @pytest.mark.topology"
            raise ValueError(error)

        name = args[0]
        topology = args[1]
        domains = args[2] if len(args) == 3 else {}
        controller = kwargs.get("controller", None)
        fixtures = {k: str(v) for k, v in kwargs.get("fixtures", {}).items()}

        return cls(name, topology, controller=controller, fixtures=fixtures, domains=domains)


class AuthselectMultihostConfig(MultihostConfig):
    @property
    def provisioned_topologies(self) -> list[str]:
        out = self.confdict.get("provisioned_topologies", [])
        return out if out is not None else []

    @property
    def TopologyMarkClass(self) -> Type[TopologyMark]:
        return AuthselectTopologyMark

    @property
    def id_to_domain_class(self) -> dict[str, Type[MultihostDomain]]:
        return {"*": AuthselectMultihostDomain}


class AuthselectMultihostDomain(MultihostDomain[AuthselectMultihostConfig]):
    def __init__(self, config: AuthselectMultihostConfig, confdict: dict[str, Any]) -> None:
        super().__init__(config, confdict)

    @property
    def role_to_host_class(self) -> dict[str, Type[MultihostHost]]:
        from .hosts.client import ClientHost
        from .hosts.ipa import IPAHost
        from .hosts.samba import SambaHost

        return {
            "client": ClientHost,
            "ipa": IPAHost,
            "samba": SambaHost,
        }

    @property
    def role_to_role_class(self) -> dict[str, Type[MultihostRole]]:
        from .roles.client import Client
        from .roles.ipa import IPA
        from .roles.samba import Samba

        return {
            "client": Client,
            "ipa": IPA,
            "samba": Samba,
        }
