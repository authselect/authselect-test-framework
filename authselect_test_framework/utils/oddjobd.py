"""Manage oddjobd on the client."""

from __future__ import annotations

from pytest_mh import MultihostHost, MultihostUtility
from pytest_mh.conn import ProcessResult
from pytest_mh.utils.services import SystemdServices

__all__ = [
    "OddjobUtils",
]


class OddjobUtils(MultihostUtility):
    """
    Management of oddjobd on the client host.

    .. code-block:: python
        :caption: Example usage

        @pytest.mark.topology(Profile.SSSD)
        def test_example(client: Client):
            client.authselect.select("sssd", ["with-mkhomedir"])
            client.oddjob.start()
    """

    def __init__(self, host: MultihostHost, svc: SystemdServices) -> None:
        """
        :param host: Multihost object.
        :type host: MultihostHost
        :param svc: Systemd utils.
        :type svc: SystemdServices
        """
        super().__init__(host)

        self.svc: SystemdServices = svc

    def start(self, *, enable: bool = True) -> ProcessResult:
        """
        Start oddjobd.

        :param enable: Enable the unit before starting, defaults to True
        :type enable: bool, optional
        :return: SSH process result.
        :rtype: ProcessResult
        """
        if enable:
            self.enable()

        return self.svc.start("oddjobd.service")

    def stop(self) -> ProcessResult:
        """
        Stop oddjobd.

        :return: SSH process result.
        :rtype: ProcessResult
        """
        return self.svc.stop("oddjobd.service")

    def enable(self, *, now: bool = False) -> ProcessResult:
        """
        Enable oddjobd.

        :param now: Enable and start the unit immediately, defaults to False
        :type now: bool, optional
        :return: SSH process result.
        :rtype: ProcessResult
        """
        args = ["systemctl", "enable"]
        if now:
            args.append("--now")
        args.append("oddjobd.service")
        return self.host.conn.exec(args)

    def disable(self, *, now: bool = False) -> ProcessResult:
        """
        Disable oddjobd.

        :param now: Disable and stop the unit immediately, defaults to False
        :type now: bool, optional
        :return: SSH process result.
        :rtype: ProcessResult
        """
        args = ["systemctl", "disable"]
        if now:
            args.append("--now")
        args.append("oddjobd.service")
        return self.host.conn.exec(args)
