"""Topology controllers for authselect system test profiles."""

from __future__ import annotations

import re

from pytest_mh import BackupTopologyController

from .config import AuthselectMultihostConfig
from .hosts.client import ClientHost
from .hosts.ipa import IPAHost
from .hosts.samba import SambaHost

__all__ = [
    "LocalController",
    "SambaController",
    "SSSDController",
    "WinbindController",
]


class ProvisionedBackupController(BackupTopologyController[AuthselectMultihostConfig]):
    """
    Provide basic restore functionality for topologies.

    Skips provisioning when a topology is listed in
    ``provisioned_topologies`` in the multihost configuration.
    """

    def __init__(self) -> None:
        """
        Initialize controller state.
        """
        super().__init__()

        self.provisioned: bool = False

    def init(self, *args, **kwargs):
        """
        Detect whether this topology is already provisioned in CI.
        """
        super().init(*args, **kwargs)
        self.provisioned = self.name in self.multihost.provisioned_topologies

    def topology_setup(self, *args, **kwargs) -> None:
        """
        Take topology backups when provisioning is required.
        """
        if self.provisioned:
            self.logger.info(f"Topology '{self.name}' is already provisioned")
            return

        super().topology_setup(*args, **kwargs)

    def topology_teardown(self, *args, **kwargs) -> None:
        """
        Restore hosts to their pre-topology state when provisioning ran.
        """
        if self.provisioned:
            return

        super().topology_teardown(*args, **kwargs)

    def teardown(self, *args, **kwargs) -> None:
        """
        Restore topology backup after each test, or vanilla state for provisioned topologies.
        """
        if self.provisioned:
            self.restore_vanilla()
            return

        super().teardown(*args, **kwargs)


class LocalController(ProvisionedBackupController):
    """
    Local profile controller.
    """

    pass


class SSSDController(ProvisionedBackupController):
    """
    SSSD profile controller.
    """

    @BackupTopologyController.restore_vanilla_on_error
    def topology_setup(self, client: ClientHost, ipa: IPAHost) -> None:
        """
        Prepare the client for SSSD tests against an IPA domain.

        Sets the client hostname, enrolls the host into IPA, and takes a
        topology backup for per-test restore.
        """
        short_hostname = client.conn.run("hostname").stdout.split(".")[0].strip()
        hostname = f"{short_hostname}.{ipa.domain}"
        client.fs.backup("/etc/hostname")
        client.fs.backup("/etc/hosts")
        client.conn.run(f"echo {hostname} > /etc/hostname")
        client.fs.write("/etc/hosts", client.fs.read("/etc/hosts").replace("client.test", hostname))

        self.logger.info(f"Changing hostname to {hostname}")
        client.conn.run(f"hostname {hostname}")

        client.fs.backup("/etc/resolv.conf")

        if self.provisioned:
            self.logger.info(f"Topology '{self.name}' is already provisioned")
            return

        self.logger.info(f"Enrolling {client.hostname} into {ipa.domain}")

        client.fs.rm("/etc/krb5.conf")
        client.fs.rm("/etc/krb5.keytab")

        result = client.conn.exec(["realm", "list"])
        self.logger.info(f"REALM_LIST STDOUT: \n{result.stdout}")
        self.logger.info(f"REALM_LIST STDERR: \n{result.stderr}")
        pattern = rf"^{re.escape(ipa.domain)}$"
        if re.search(pattern, result.stdout, re.MULTILINE):
            self.logger.info(f"Found {ipa.domain} in realm list.  Leaving.")
            client.conn.exec(["realm", "leave", ipa.domain], input=ipa.adminpw, raise_on_error=False)

        client.fs.backup("/etc/ipa")
        client.fs.backup("/var/lib/ipa-client")

        result = client.conn.exec(["realm", "join", ipa.domain], input=ipa.adminpw, raise_on_error=False)
        if result.rc != 0:
            self.logger.info(f"Running realm join failed with:\n{result.stdout}\n{result.stderr}")
            self.logger.info("Trying uninstall and join again.")
            client.conn.exec(["ipa-client-install", "--uninstall", "-U"])
            client.conn.exec(["realm", "join", ipa.domain], input=ipa.adminpw)

        client.svc.stop("winbind.service")
        client.svc.stop("sssd.service")

        super().topology_setup()


class SambaController(ProvisionedBackupController):
    """
    Samba profile controller.

    Handles Samba domain controller setup shared by winbind tests.
    """

    @BackupTopologyController.restore_vanilla_on_error
    def topology_setup(self, provider: SambaHost) -> None:
        """
        Start the Samba domain controller.
        """
        provider.start()


class WinbindController(SambaController):
    """
    Winbind profile controller.

    Joins the client to a Samba domain with winbind and prepares services
    for authselect winbind feature tests.
    """

    @BackupTopologyController.restore_vanilla_on_error
    def topology_setup(self, client: ClientHost, provider: SambaHost) -> None:
        """
        Prepare the client for winbind tests against a Samba domain.

        Starts the Samba provider, sets the client hostname, joins the domain
        with winbind, applies Samba configuration, and takes a topology backup.
        """
        SambaController.topology_setup(self, provider)

        short_hostname = client.conn.run("hostname").stdout.split(".")[0].strip()
        hostname = f"{short_hostname}.{provider.domain}"
        client.fs.backup("/etc/hostname")
        client.fs.backup("/etc/hosts")
        client.conn.run(f"echo {hostname} > /etc/hostname")
        client.fs.write("/etc/hosts", client.fs.read("/etc/hosts").replace("client.test", hostname))

        self.logger.info(f"Changing hostname to {hostname}")
        client.conn.run(f"hostname {hostname}")

        self.logger.info(f"Setting up winbind on {client.hostname} for {provider.domain}")

        client.svc.stop("sssd.service", raise_on_error=False)

        result = client.conn.run("realm list", raise_on_error=False)
        pattern = rf"^{re.escape(provider.domain)}$"
        if re.search(pattern, result.stdout, re.MULTILINE):
            self.logger.info(f"Found {provider.domain} in realm list. Leaving before winbind join.")
            client.conn.exec(["realm", "leave", provider.domain], input=provider.adminpw, raise_on_error=False)

        self.logger.info(f"Joining {client.hostname} into {provider.domain} with winbind")

        client.fs.backup("/etc/krb5.conf")
        client.fs.backup("/etc/krb5.keytab")
        client.fs.backup("/etc/samba/smb.conf")
        client.fs.rm("/etc/krb5.keytab")

        join_args = [
            "realm",
            "join",
            provider.domain,
            "--client-software=winbind",
            "--membership-software=samba",
            "-U",
            provider.adminuser,
        ]
        result = client.conn.exec(join_args, input=provider.adminpw, raise_on_error=False)
        if result.rc != 0:
            output = f"{result.stdout}\n{result.stderr}"
            self.logger.info(f"realm join failed:\n{output}")
            if "Already joined" in output:
                client.conn.exec(
                    ["net", "ads", "leave", "-U", provider.adminuser],
                    input=provider.adminpw,
                    raise_on_error=False,
                )
                client.conn.exec(
                    ["realm", "leave", provider.domain],
                    input=provider.adminpw,
                    raise_on_error=False,
                )
                client.conn.exec(join_args, input=provider.adminpw)
            else:
                result.throw()

        workgroup = provider.domain.split(".", maxsplit=1)[0].upper()
        include_path = "/etc/samba/conf.d/authselect-test-framework.conf"
        client.conn.run("mkdir -p /etc/samba/conf.d", raise_on_error=False)
        client.fs.write(
            include_path,
            "\n".join(
                [
                    "[global]",
                    "winbind use default domain = yes",
                    "winbind normalize names = yes",
                    "winbind nss info = rfc2307",
                    "idmap config * : backend = tdb",
                    "idmap config * : range = 3000-7999",
                    f"idmap config {workgroup} : backend = rid",
                    f"idmap config {workgroup} : range = 1000-999999",
                    "",
                ]
            ),
        )
        result = client.conn.run(f"grep -F '{include_path}' /etc/samba/smb.conf", raise_on_error=False)
        if result.rc != 0:
            client.conn.run(f"echo 'include = {include_path}' >> /etc/samba/smb.conf")
        client.conn.run(
            r"sed -i 's/^winbind use default domain = .*/winbind use default domain = yes/' /etc/samba/smb.conf",
            raise_on_error=False,
        )

        client.conn.run('systemctl disable "sssd.service"', raise_on_error=False)
        client.conn.run('systemctl enable "winbind.service"', raise_on_error=False)
        client.svc.restart("winbind.service", raise_on_error=False)
        client.conn.run("wbinfo -t")
        client.svc.stop("winbind.service")

        # Always take topology backups, even for provisioned environments.
        super(ProvisionedBackupController, self).topology_setup()

    def teardown(self, *args, **kwargs) -> None:
        """
        Restore the winbind-joined topology backup after each test.

        Provisioned topologies normally revert to the container's vanilla state
        (sssd-joined). Winbind tests require the winbind join from
        :meth:`topology_setup` to persist across tests.
        """
        super(ProvisionedBackupController, self).teardown(*args, **kwargs)

    def topology_teardown(self, *args, **kwargs) -> None:
        """
        Leave the Samba domain when the winbind topology session ends.

        Domain leave runs only for non-provisioned topologies. Provisioned CI
        environments keep their preconfigured enrollment.
        """
        if self.provisioned:
            return

        provider: SambaHost = kwargs["provider"]
        client: ClientHost = kwargs["client"]

        self.logger.info(f"Leaving {provider.domain} during winbind topology teardown")
        client.conn.exec(["realm", "leave", provider.domain], input=provider.adminpw, raise_on_error=False)

        super().topology_teardown(*args, **kwargs)
