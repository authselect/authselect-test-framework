"""Generic roles used with topology parametrization."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..profiles import Profile
from .base import BaseObject

__all__ = [
    "GenericProvider",
    "GenericOrganizationalUnit",
    "GenericPasswordPolicy",
    "GenericUser",
    "GenericGroup",
    "GenericComputer",
    "GenericSite",
    "GenericNetgroup",
    "GenericNetgroupMember",
    "GenericSudoRule",
    "SudoRuleUserField",
    "SudoRuleHostField",
    "SudoRuleCommandField",
    "SudoRuleRunAsUserField",
    "SudoRuleRunAsGroupField",
    "GenericCertificateAuthority",
    "GroupMemberField",
]


class GenericProvider(ABC):
    """
    Generic provider interface. IPA, Samba and Client roles implement this interface.

    .. note::

        This class provides a generic interface for the ``provider`` fixture. It is
        used for type hinting in profile tests that run on multiple topologies.
    """

    domain: str
    """Domain name."""

    realm: str
    """Kerberos realm."""

    name: str
    """Provider role identifier (for example ``ipa`` or ``ad``)."""

    hostname: str
    """Provider hostname."""

    @property
    @abstractmethod
    def profile(self) -> Profile:
        """
        Active authselect profile for the current topology.
        """
        pass

    @property
    @abstractmethod
    def naming_context(self) -> str:
        """
        Naming context.
        """
        pass

    @property
    @abstractmethod
    def password_policy(self) -> GenericPasswordPolicy:
        """
        Domain password policy management.

        .. code-block:: python
            :caption: Example usage

            @pytest.mark.topology(Profile.SSSD)
            @pytest.mark.topology(Profile.Winbind)
            def test_example(client: Client, provider: GenericProvider):
                # Enable password complexity
                provider.password_policy.complexity(enable=True)

                # Set 3 login attempts and 30 lockout duration
                provider.password_policy.lockout(attempts=3, duration=30)
        """
        pass

    @abstractmethod
    def fqn(self, name: str) -> str:
        """
        Return fully qualified name.
        """
        pass

    @abstractmethod
    def user(self, name: str) -> GenericUser:
        """
        Get user object.

        .. code-block:: python
            :caption: Example usage

            @pytest.mark.topology(Profile.SSSD)
            @pytest.mark.topology(Profile.Winbind)
            def test_example(client: Client, provider: GenericProvider):
                # Create user
                provider.user('user-1').add()

                # Start SSSD
                client.sssd.start()

                # Call `id user-1` and assert the result
                result = client.tools.id('user-1')
                assert result is not None
                assert result.user.name == 'user-1'

        :param name: Username.
        :type name: str
        :return: New user object.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def group(self, name: str) -> GenericGroup:
        """
        Get group object.

        .. code-block:: python
            :caption: Example usage

            @pytest.mark.topology(Profile.SSSD)
            @pytest.mark.topology(Profile.Winbind)
            def test_example(client: Client, provider: GenericProvider):
                # Create user
                user = provider.user('user-1').add()

                # Create secondary group and add user as a member
                provider.group('group-1').add().add_member(user)

                # Start SSSD
                client.sssd.start()

                # Call `id user-1` and assert the result
                result = client.tools.id('user-1')
                assert result is not None
                assert result.user.name == 'user-1'
                assert result.memberof('group-1')

        :param name: Group name.
        :type name: str
        :return: New group object.
        :rtype: GenericGroup
        """
        pass

    @abstractmethod
    def netgroup(self, name: str) -> GenericNetgroup:
        """
        Get netgroup object.

        .. code-block:: python
            :caption: Example usage

            @pytest.mark.topology(Profile.SSSD)
            @pytest.mark.topology(Profile.Winbind)
            def test_example_netgroup(client: Client, provider: GenericProvider):
                # Create user
                user = provider.user("user-1").add()

                # Create two netgroups
                ng1 = provider.netgroup("ng-1").add()
                ng2 = provider.netgroup("ng-2").add()

                # Add user and ng2 as members to ng1
                ng1.add_member(user=user)
                ng1.add_member(ng=ng2)

                # Add host as member to ng2
                ng2.add_member(host="client")

                # Start SSSD
                client.sssd.start()

                # Call `getent netgroup ng-1` and assert the results
                result = client.tools.getent.netgroup("ng-1")
                assert result is not None
                assert result.name == "ng-1"
                assert len(result.members) == 2
                assert "(-,user-1,)" in result.members
                assert "(client,-,)" in result.members

        :param name: Netgroup name.
        :type name: str
        :return: New netgroup object.
        :rtype: GenericNetgroup
        """
        pass

    @abstractmethod
    def sudorule(self, name: str) -> GenericSudoRule:
        """
        Get sudo rule object.

        .. code-block:: python
            :caption: Example usage

            @pytest.mark.topology(Profile.SSSD)
            @pytest.mark.topology(Profile.Winbind)
            def test_example(client: Client, provider: GenericProvider):
                user = provider.user('user-1').add()
                provider.sudorule('testrule').add(user=user, host='ALL', command='/bin/ls')

                client.sssd.common.sudo()
                client.sssd.start()

                # Test that user can run /bin/ls
                assert client.auth.sudo.run('user-1', command='/bin/ls')

        :param name: Sudo rule name.
        :type name: str
        :return: New sudo rule object.
        :rtype: GenericSudoRule
        """
        pass

    @property
    @abstractmethod
    def ca(self) -> GenericCertificateAuthority:
        """
        Certificate Authority management.

        Provides certificate operations across different provider roles.

        .. code-block:: python
            :caption: Example usage

            @pytest.mark.topology(Profile.SSSD)
            @pytest.mark.topology(Profile.Winbind)
            def test_certificate_operations(client: Client, provider: GenericProvider):
                # Request certificate
                cert, key, csr = provider.ca.request(...)

                # Revoke certificate
                provider.ca.revoke(cert, reason="key_compromise")

                # Place certificate on hold
                provider.ca.revoke_hold(cert)

                # Remove hold
                provider.ca.revoke_hold_remove(cert)

                # Get certificate details
                cert_details = provider.ca.get(cert)
        """
        pass


class GenericOrganizationalUnit(ABC, BaseObject):
    """
    Generic ou management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        OU name.
        """
        pass

    @abstractmethod
    def add(self, name: str) -> GenericOrganizationalUnit:
        """
        Create a new OU.
        :param name:
        :type name: str
        :return: self
        :rtype: GenericOrganizationalUnit
        """
        pass


class GenericUser(ABC, BaseObject):
    """
    Generic user management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        User name.
        """
        pass

    @abstractmethod
    def add(
        self,
        *,
        uid: int | None = None,
        gid: int | None = None,
        password: str = "Secret123",
        home: str | None = None,
        gecos: str | None = None,
        shell: str | None = None,
        email: str | None = None,
    ) -> GenericUser:
        """
        Create a new user.

        Parameters that are not set are ignored.

        :param uid: POSIX ``uidNumber`` attribute (``uid-number``), defaults to None
        :type uid: int | None, optional
        :param gid: POSIX ``gidNumber`` attribute (``gid-number``), defaults to None
        :type gid: int | None, optional
        :param password: User password, defaults to 'Secret123'
        :type password: str, optional
        :param home: Home directory, defaults to None
        :type home: str | None, optional
        :param gecos: GECOS, defaults to None
        :type gecos: str | None, optional
        :param shell: Login shell, defaults to None
        :type shell: str | None, optional
        :param email: email attribute, defaults to None
        :type email: str | None, optional
        :return: Self.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def modify(
        self,
        *,
        uid: int | None = None,
        gid: int | None = None,
        password: str | None = None,
        home: str | None = None,
        gecos: str | None = None,
        shell: str | None = None,
        email: str | None = None,
    ) -> GenericUser:
        """
        Modify existing user.

        Parameters that are not set are ignored.

        :param uid: POSIX ``uidNumber`` attribute (``uid-number``), defaults to None
        :type uid: int | None, optional
        :param gid: POSIX ``gidNumber`` attribute (``gid-number``), defaults to None
        :type gid: int | None, optional
        :param password: Password, defaults to None
        :type password: str, optional
        :param home: Home directory, defaults to None
        :type home: str | None, optional
        :param gecos: GECOS, defaults to None
        :type gecos: str | None, optional
        :param shell: Login shell, defaults to None
        :type shell: str | None, optional
        :param email: email attribute, defaults to None
        :type email: str | None, optional
        :return: Self.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def reset(self, password: str | None = "Secret123") -> GenericUser:
        """
        Reset user password.

        :param password: Password, defaults to 'Secret123'
        :type password: str, optional
        :return: Self.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def expire(self, expiration: str | None = "19700101000000") -> GenericUser:
        """
        Set user password expiration date and time.

        :param expiration: Date and time for user password expiration, defaults to 19700101000000
        :type expiration: str, optional
        :return: Self.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def password_change_at_logon(self, **kwargs) -> GenericUser:
        """
        Force user to change password next logon.

        LDAP server implementations need to administratively reset the user password to trigger the
        password change. The ``password`` keyword is required for LDAP but ignored by other roles.

        :return: Self.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Delete the user.

        :raises SSHProcessError: If the user does not exist or deletion fails.
        """
        pass

    @abstractmethod
    def discard(self) -> None:
        """
        Delete the user if they exist.

        Does not raise when the user is already absent. Use :meth:`delete` when removal must succeed.
        """
        pass

    @abstractmethod
    def get(self, attrs: list[str] | None = None, *, opattrs: bool = False) -> dict[str, list[str]] | None:
        """
        Get user attributes.

        :param attrs: If set, only requested attributes are returned, defaults to None
        :type attrs: list[str] | None, optional
        :param opattrs: If True, include operational attributes (LDAP only), defaults to False
        :type opattrs: bool, optional
        :return: Dictionary with attribute name as a key, or None if not found.
        :rtype: dict[str, list[str]] | None
        """
        pass

    @abstractmethod
    def passkey_add(self, passkey_mapping: str) -> GenericUser:
        """
        Add passkey mapping to the user.

        :param passkey_mapping: Passkey mapping generated by ``sssctl passkey-register``
        :type passkey_mapping: str
        :return: Self.
        :rtype: GenericUser
        """
        pass

    @abstractmethod
    def passkey_remove(self, passkey_mapping: str) -> GenericUser:
        """
        Remove passkey mapping from the user.

        :param passkey_mapping: Passkey mapping generated by ``sssctl passkey-register``
        :type passkey_mapping: str
        :return: Self.
        :rtype: GenericUser.
        """
        pass


class GenericGroup(ABC, BaseObject):
    """
    Generic group management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Group name.
        """
        pass

    @abstractmethod
    def add(
        self,
        *,
        gid: int | None = None,
        description: str | None = None,
    ) -> GenericGroup:
        """
        Create a new group.

        Parameters that are not set are ignored.

        :param gid: Group id, defaults to None
        :type gid: int | None, optional
        :param description: Description, defaults to None
        :type description: str | None, optional
        :return: Self.
        :rtype: GenericGroup
        """
        pass

    @abstractmethod
    def modify(
        self,
        *,
        gid: int | None = None,
        description: str | None = None,
    ) -> GenericGroup:
        """
        Modify existing group.

        Parameters that are not set are ignored.

        :param gid: Group id, defaults to None
        :type gid: int | None, optional
        :param description: Description, defaults to None
        :type description: str | None, optional
        :return: Self.
        :rtype: GenericGroup
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Delete the group.

        :raises SSHProcessError: If the group does not exist or deletion fails.
        """
        pass

    @abstractmethod
    def discard(self) -> None:
        """
        Delete the group if it exists.

        Does not raise when the group is already absent. Use :meth:`delete` when removal must succeed.
        """
        pass

    @abstractmethod
    def get(self, attrs: list[str] | None = None, *, opattrs: bool = False) -> dict[str, list[str]] | None:
        """
        Get group attributes.

        :param attrs: If set, only requested attributes are returned, defaults to None
        :type attrs: list[str] | None, optional
        :param opattrs: If True, include operational attributes (LDAP only), defaults to False
        :type opattrs: bool, optional
        :return: Dictionary with attribute name as a key, or None if not found.
        :rtype: dict[str, list[str]] | None
        """
        pass

    @abstractmethod
    def add_member(self, member: GroupMemberField) -> GenericGroup:
        """
        Add group member.

        :param member: User, group, or member name / external principal string.
        :type member: GroupMemberField
        :return: Self.
        :rtype: GenericGroup
        """
        pass

    @abstractmethod
    def add_members(self, members: list[GroupMemberField]) -> GenericGroup:
        """
        Add multiple group members.

        :param members: List of users, groups, or member name strings.
        :type members: list[GroupMemberField]
        :return: Self.
        :rtype: GenericGroup
        """
        pass

    @abstractmethod
    def remove_member(self, member: GroupMemberField) -> GenericGroup:
        """
        Remove group member.

        :param member: User, group, or member name / external principal string.
        :type member: GroupMemberField
        :return: Self.
        :rtype: GenericGroup
        """
        pass

    @abstractmethod
    def remove_members(self, members: list[GroupMemberField]) -> GenericGroup:
        """
        Remove multiple group members.

        :param members: List of users, groups, or member name strings.
        :type members: list[GroupMemberField]
        :return: Self.
        :rtype: GenericGroup
        """
        pass


GroupMemberField = GenericUser | GenericGroup | str
"""Group member: user, nested group, or string (name / external member / RDN fragment)."""


class GenericComputer(ABC, BaseObject):
    """
    Generic computer management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Computer name.
        """
        pass

    @abstractmethod
    def move(self, target: str) -> GenericComputer:
        """
        Move  a computer object.
        :param target: Target path.
        :type target: str
        :return: Self.
        :rtype: GenericComputer
        """
        pass


class GenericSite(ABC, BaseObject):
    """
    Generic site management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Site name.
        """
        pass

    @abstractmethod
    def add(self) -> GenericSite:
        """
        Create new site.

        :return: Self.
        :type: GenericSite
        """
        pass


class GenericNetgroup(ABC, BaseObject):
    """
    Generic netgroup management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Netgroup name.
        """
        pass

    @abstractmethod
    def add(self) -> GenericNetgroup:
        """
        Create a new netgroup.

        :return: Self.
        :rtype: GenericNetgroup
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Delete the netgroup.
        """
        pass

    @abstractmethod
    def get(self, attrs: list[str] | None = None, *, opattrs: bool = False) -> dict[str, list[str]] | None:
        """
        Get netgroup attributes.

        :param attrs: If set, only requested attributes are returned, defaults to None
        :type attrs: list[str] | None, optional
        :param opattrs: If True, include operational attributes (LDAP only), defaults to False
        :type opattrs: bool, optional
        :return: Dictionary with attribute name as a key, or None if not found.
        :rtype: dict[str, list[str]] | None
        """
        pass

    @abstractmethod
    def add_member(
        self,
        *,
        host: str | None = None,
        user: GenericUser | str | None = None,
        ng: GenericNetgroup | str | None = None,
    ) -> GenericNetgroup:
        """
        Add netgroup member.

        :param host: Host, defaults to None
        :type host: str | None, optional
        :param user: User, defaults to None
        :type user: GenericUser | str | None, optional
        :param ng: Netgroup, defaults to None
        :type ng: GenericNetgroup | str | None, optional
        :return: Self.
        :rtype: GenericNetgroup
        """
        pass

    @abstractmethod
    def add_members(self, members: list[GenericNetgroupMember]) -> GenericNetgroup:
        """
        Add multiple netgroup members at once.

        :param members: List of netgroup members to add.
        :type members: list[GenericNetgroupMember]
        :return: Self.
        :rtype: GenericNetgroup
        """
        pass

    @abstractmethod
    def remove_member(
        self,
        *,
        host: str | None = None,
        user: GenericUser | str | None = None,
        ng: GenericNetgroup | str | None = None,
    ) -> GenericNetgroup:
        """
        Remove netgroup member.

        :param host: Host, defaults to None
        :type host: str | None, optional
        :param user: User, defaults to None
        :type user: GenericUser | str | None, optional
        :param ng: Netgroup, defaults to None
        :type ng: GenericNetgroup | str | None, optional
        :return: Self.
        :rtype: GenericNetgroup
        """
        pass

    @abstractmethod
    def remove_members(self, members: list[GenericNetgroupMember]) -> GenericNetgroup:
        """
        Remove multiple netgroup members.

        :param members: List of netgroup members to remove.
        :type members: list[GenericNetgroupMember]
        :return: Self.
        :rtype: GenericNetgroup
        """
        pass


class GenericNetgroupMember(object):
    """
    Generic netgroup member.

    .. note::

        This is a essentially a NIS Netgroup Triple, but we have to omit the
        domain part as it is not supported by FreeIPA. In addition to the
        triple, it can also hold a netgroup as a member.

    """

    def __init__(
        self,
        *,
        host: str | None = None,
        user: GenericUser | str | None = None,
        ng: GenericNetgroup | str | None = None,
    ) -> None:
        """
        :param host: Host, defaults to None
        :type host: str | None, optional
        :param user: User, defaults to None
        :type user: GenericUser | str | None, optional
        :param ng: Netgroup, defaults to None
        :type ng: GenericNetgroup | str | None, optional
        """
        self.host: str | None = host
        """Member host."""

        self.user: str | None = self._get_name(user)
        """Member user."""

        self.netgroup: str | None = self._get_name(ng)
        """Member netgroup."""

    def _get_name(
        self,
        item: GenericUser | GenericNetgroup | GenericGroup | str | None = None,
    ) -> str | None:
        if item is None:
            return None

        if hasattr(item, "name"):
            return item.name

        return item

    def triple(self) -> str | None:
        """
        NIS netgroup triple string ``(host,user,)``.

        :class:`LDAPNetgroupMember` overrides this when a ``domain`` field is set.
        :class:`LocalNetgroupMember` uses :meth:`LocalNetgroupMember.to_member_string` instead.

        :return: Triple string, or None if the member is only a nested netgroup.
        :rtype: str | None
        """
        if self.host is None and self.user is None:
            return None

        host = self.host if self.host is not None else "-"
        user = self.user if self.user is not None else "-"
        return f"({host},{user},)"


SudoRuleUserField = str | GenericUser | GenericGroup | list[str | GenericUser | GenericGroup] | None
SudoRuleHostField = str | list[str] | None
SudoRuleCommandField = str | list[str] | None
SudoRuleRunAsUserField = str | GenericUser | GenericGroup | list[str | GenericUser | GenericGroup] | None
SudoRuleRunAsGroupField = str | GenericGroup | list[str | GenericGroup] | None


class GenericSudoRule(ABC, BaseObject):
    """
    Generic sudo rule management.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Sudo rule name.
        """
        pass

    @abstractmethod
    def add(
        self,
        *,
        user: SudoRuleUserField = None,
        host: SudoRuleHostField = None,
        command: SudoRuleCommandField = None,
        option: str | list[str] | None = None,
        runasuser: SudoRuleRunAsUserField = None,
        runasgroup: SudoRuleRunAsGroupField = None,
        order: int | None = None,
        nopasswd: bool | None = None,
    ) -> GenericSudoRule:
        """
        Create new sudo rule.

        :param user: sudoUser attribute, defaults to None
        :type user: SudoRuleUserField, optional
        :param host: sudoHost attribute, defaults to None
        :type host: SudoRuleHostField, optional
        :param command: sudoCommand attribute, defaults to None
        :type command: SudoRuleCommandField, optional
        :param option: sudoOption attribute, defaults to None
        :type option: str | list[str] | None, optional
        :param runasuser: sudoRunAsUser attribute, defaults to None
        :type runasuser: SudoRuleRunAsUserField, optional
        :param runasgroup: sudoRunAsGroup attribute, defaults to None
        :type runasgroup: SudoRuleRunAsGroupField, optional
        :param order: sudoOrder attribute, defaults to None
        :type order: int | None, optional
        :param nopasswd: If true, no authentication is required (NOPASSWD), defaults to None (no change)
        :type nopasswd: bool | None, optional
        :return: Self.
        :rtype: GenericSudoRule
        """
        pass

    @abstractmethod
    def modify(
        self,
        *,
        user: SudoRuleUserField = None,
        host: SudoRuleHostField = None,
        command: SudoRuleCommandField = None,
        option: str | list[str] | None = None,
        runasuser: SudoRuleRunAsUserField = None,
        runasgroup: SudoRuleRunAsGroupField = None,
        order: int | None = None,
        nopasswd: bool | None = None,
    ) -> GenericSudoRule:
        """
        Modify existing sudo rule.

        :param user: sudoUser attribute, defaults to None
        :type user: SudoRuleUserField, optional
        :param host: sudoHost attribute, defaults to None
        :type host: SudoRuleHostField, optional
        :param command: sudoCommand attribute, defaults to None
        :type command: SudoRuleCommandField, optional
        :param option: sudoOption attribute, defaults to None
        :type option: str | list[str] | None, optional
        :param runasuser: sudoRunAsUser attribute, defaults to None
        :type runasuser: SudoRuleRunAsUserField, optional
        :param runasgroup: sudoRunAsGroup attribute, defaults to None
        :type runasgroup: SudoRuleRunAsGroupField, optional
        :param order: sudoOrder attribute, defaults to None
        :type order: int | None, optional
        :param nopasswd: If true, no authentication is required (NOPASSWD), defaults to None (no change)
        :type nopasswd: bool | None, optional
        :return: Self.
        :rtype: GenericSudoRule
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Delete the sudo rule.
        """
        pass

    @abstractmethod
    def get(self, attrs: list[str] | None = None, *, opattrs: bool = False) -> dict[str, list[str]] | None:
        """
        Get sudo rule attributes.

        :param attrs: If set, only requested attributes are returned, defaults to None
        :type attrs: list[str] | None, optional
        :param opattrs: If True, include operational attributes (LDAP only), defaults to False
        :type opattrs: bool, optional
        :return: Dictionary with attribute name as a key, or None if not found.
        :rtype: dict[str, list[str]] | None
        """
        pass


class GenericPasswordPolicy(ABC, BaseObject):
    """
    Password policy management.
    """

    @abstractmethod
    def complexity(self, enable: bool) -> GenericPasswordPolicy:
        """
        Enable or disable password complexity.

        :param enable: Enable or disable password complexity.
        :type enable: bool
        :return: GenericPasswordPolicy object.
        :rtype: GenericPasswordPolicy
        """
        pass

    @abstractmethod
    def lockout(self, duration: int, attempts: int) -> GenericPasswordPolicy:
        """
        Set lockout duration and login attempts.

        :param duration: Duration of lockout in seconds.
        :type duration: int
        :param attempts: Number of login attempts.
        :type attempts: int
        :return: GenericPasswordPolicy object.
        :rtype: GenericPasswordPolicy
        """
        pass


class GenericCertificateAuthority(ABC):
    @abstractmethod
    def request(self, *args, **kwargs) -> tuple[str, str, str]:
        """
        :returns: A tuple of (certificate_path, key_path, csr_path).
        :rtype: tuple[str, str, str]
        """
        pass

    @abstractmethod
    def revoke(self, cert_path: str, reason: str = "unspecified") -> None:
        """
        Revoke a certificate.

        :param cert_path: Path to the certificate file.
        :type cert_path: str
        :param reason: Reason for revocation.
        :type reason: str
        """
        pass

    @abstractmethod
    def revoke_hold(self, cert_path: str) -> None:
        """
        Place a certificate on hold.

        :param cert_path: Path to the certificate file.
        :type cert_path: str
        """
        pass

    @abstractmethod
    def revoke_hold_remove(self, cert_path: str) -> None:
        """
        Remove hold from a certificate.

        :param cert_path: Path to the certificate file.
        :type cert_path: str
        """
        pass

    @abstractmethod
    def get(self, cert_path: str) -> dict[str, list[str]]:
        """
        Retrieve certificate details.

        :param cert_path: Path to the certificate file.
        :type cert_path: str
        :returns: A dictionary of certificate attributes.
        :rtype: dict[str, list[str]]
        """
        pass
