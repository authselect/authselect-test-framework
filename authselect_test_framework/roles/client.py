"""Client multihost role."""

from __future__ import annotations

from pytest_mh.conn import ProcessResult

from ..config import AuthselectTopologyMark
from ..hosts.client import ClientHost
from ..utils.gdm import GDM
from ..utils.local_users import (
    LocalGroup,
    LocalNetgroup,
    LocalSudoAlias,
    LocalSudoAliasKind,
    LocalSudoRule,
    LocalUser,
    LocalUsersUtils,
)
from ..utils.oddjobd import OddjobUtils
from ..utils.smartcard import SmartCardUtils
from ..utils.sssctl import SSSCTLUtils
from ..utils.sssd import SSSDUtils
from ..utils.vfido import Vfido
from ..utils.winbind import WinbindUtils
from .base import BaseLinuxRole
from .generic import (
    GenericCertificateAuthority,
    GenericPasswordPolicy,
    GenericProvider,
)

__all__ = [
    "Client",
]


class Client(BaseLinuxRole[ClientHost], GenericProvider):
    """
    Authselect client role.

    Provides unified Python API for managing authselect, SSSD, winbind and
    related client-side test utilities.

    .. code-block:: python
        :caption: Starting SSSD

        @pytest.mark.topology(Profile.Local)
        def test_example(client: Client):
            client.sssd.start()

    .. note::

        The role object is instantiated automatically as a dynamic pytest
        fixture by the multihost plugin. You should not create the object
        manually.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.sssd: SSSDUtils = SSSDUtils(
            self.host,
            self.fs,
            self.svc,
            self.authselect,
            load_config=False,
        )
        """
        Managing and configuring SSSD.
        """

        self.sssctl: SSSCTLUtils = SSSCTLUtils(self.host, self.fs)
        """
        Call commands from sssctl.
        """

        self.winbind: WinbindUtils = WinbindUtils(self.host, self.svc)
        """
        Managing winbind.
        """

        self.oddjob: OddjobUtils = OddjobUtils(self.host, self.svc)
        """
        Managing oddjobd.
        """

        self.smartcard: SmartCardUtils = SmartCardUtils(self.host, self.fs, self.svc)
        """
        Utility class for managing smart card operations using SoftHSM and PKCS#11.
        """

        self.gdm: GDM = GDM(self.host)
        """
        Managing GDM interface from SCAutolib
        """

        self.vfido: Vfido = Vfido(self.host)
        """
        Managing virtual passkey device and service
        """

        self.local: LocalUsersUtils = LocalUsersUtils(self.host, self.fs, client=self)
        """
        Managing local users and groups.
        """

        self.domain: str = "local"
        """Local provider domain name."""

        self.realm: str = "LOCAL"
        """Local provider Kerberos realm."""

        self.name: str = "local"
        """Provider role identifier (``local``)."""

        self.hostname: str = self.host.hostname
        """Provider hostname."""

    @property
    def naming_context(self) -> str:
        """
        Naming context (not available on the local provider).
        """
        raise NotImplementedError("Naming context is not available on the local provider")

    @property
    def password_policy(self) -> GenericPasswordPolicy:
        """
        Domain password policy management (not available on the local provider).
        """
        raise NotImplementedError("Password policy is not available on the local provider")

    @property
    def ca(self) -> GenericCertificateAuthority:
        """
        Certificate Authority management (not available on the local provider).
        """
        raise NotImplementedError("Certificate authority is not available on the local provider")

    def fqn(self, name: str) -> str:
        """
        Return fully qualified name (local users are not domain-qualified).
        """
        return name

    def setup(self) -> None:
        """
        Called before execution of each test.

        Setup client host:

        #. stop identity services
        #. on SSSD topologies, clear sssd cache, logs and configuration
        #. on SSSD topologies, import implicit domains from topology marker
        """
        super().setup()
        self.host.stop_identity_services()

        mark = self.mh.data.topology_mark
        if mark is None:
            return

        if not isinstance(mark, AuthselectTopologyMark):
            raise ValueError("Multihost data does not have AuthselectTopologyMark")

        if not mark.domains:
            return

        self.sssd.clear(db=True, memcache=True, logs=True, config=True)

        for domain, path in mark.domains.items():
            role = self.mh._lookup(path)
            if isinstance(role, list):
                raise ValueError("List is not expected")

            self.sssd.import_domain(domain, role)

            if self.fs.exists("/etc/krb5.keytab"):
                dom = self.sssd.dom(domain)
                for key in ("krb5_keytab", "ldap_krb5_keytab"):
                    ktpath = dom.get(key)
                    if ktpath and ktpath.startswith("/var/enrollment/"):
                        self.fs.copy("/etc/krb5.keytab", ktpath)

    def sss_ssh_knownhosts(self, *args: str) -> ProcessResult:
        """
        Execute sss_ssh_knownhosts.

        :param `*args`: Command arguments.
        :type `*args`: str
        :return: Command result.
        :rtype: ProcessResult
        """
        return self.host.conn.exec(["sss_ssh_knownhosts", *args])

    def sss_ssh_authorizedkeys(self, *args: str) -> ProcessResult:
        """
        Execute sss_ssh_authorizedkeys.

        :param `*args`: Command arguments.
        :type `*args`: str
        :return: Command result.
        :rtype: ProcessResult
        """
        return self.host.conn.exec(["sss_ssh_authorizedkeys", *args], raise_on_error=False)

    def user(self, name: str) -> LocalUser:
        """
        Get user object.

        :param name: User name.
        :type name: str
        :return: New user object.
        :rtype: LocalUser
        """

        return LocalUser(self.local, name)

    def group(self, name: str) -> LocalGroup:
        """
        Get group object.
        :param name: Group name.
        :type name: str
        :return: New group object.
        :rtype: LocalGroup
        """

        return LocalGroup(self.local, name)

    def sudoalias(self, name: str, kind: LocalSudoAliasKind) -> LocalSudoAlias:
        """
        Get sudo alias object.
        :param name: Sudo alias name.
        :type name: str
        :param kind: Alias kind.
        :type kind: LocalSudoAliasKind
        :return: New sudo alias object.
        :rtype: LocalSudoAlias
        """

        return self.local.sudoalias(name, kind)

    def netgroup(self, name: str) -> LocalNetgroup:
        """
        Get netgroup object.
        :param name: Netgroup name.
        :type name: str
        :return: New netgroup object.
        :rtype: LocalNetgroup
        """

        return self.local.netgroup(name)

    def sudorule(self, name: str) -> LocalSudoRule:
        """
        Get sudo rule object.
        :param name: Sudo rule name.
        :type name: str
        :return: New sudo rule object.
        :rtype: LocalSudoRule
        """

        return self.local.sudorule(name)
