"""Selecting authselect profiles."""

from __future__ import annotations

from typing import List

from pytest_mh import MultihostHost, MultihostUtility
from pytest_mh.conn import ProcessResult

from ..hosts.client import ClientHost

__all__ = [
    "AuthselectUtils",
]


class AuthselectUtils(MultihostUtility[MultihostHost]):
    """
    Use authselect to configure nsswitch and PAM.

    .. code-block:: python
        :caption: Example usage

        @pytest.mark.topology(Profile.SSSD)
        @pytest.mark.topology(Profile.Winbind)
        def test_example(client: Client, provider: GenericProvider):
            client.authselect.select('sssd', ['with-mkhomedir'])

    .. note::

        Authselect changes are restored in :meth:`ClientHost.teardown`.
    """

    __backup_name = "multihost.backup"

    def _backup_args(self) -> List[str]:
        if isinstance(self.host, ClientHost):
            if self.host.authselect_backup is None:
                self.host.authselect_track_backup(self.__backup_name)
                return [f"--backup={self.__backup_name}"]

            return []

        return [f"--backup={self.__backup_name}"]

    def select(self, profile: str, features: List[str] = []) -> None:
        """
        Select an authselect profile.

        :param profile: Authselect profile name.
        :type profile: str
        :param features: Authselect features to enable, defaults to []
        :type features: list[str], optional
        """
        self.host.conn.exec(["authselect", "select", profile, *features, "--force", *self._backup_args()])
        self.assert_selected(profile, features)

    def assert_selected(self, profile: str, features: List[str] | None = None) -> None:
        """
        Verify that authselect profile and features were applied.

        :param profile: Authselect profile or preset name passed to :meth:`select`.
        :type profile: str
        :param features: Authselect features expected to be enabled, defaults to None
        :type features: list[str] | None, optional
        """
        if features is None:
            features = []

        current = self.current(raw=True).strip()

        if profile.startswith("@"):
            assert current, f"authselect should apply configuration after selecting preset {profile}!"
            if features:
                assert self.is_feature_enabled(
                    features
                ), f"authselect features {features!r} should be enabled after selecting {profile}!"
            return

        expected = " ".join([profile, *features]) if features else profile
        assert current == expected, f"authselect current should be '{expected}' after select, got '{current}'!"

        if features:
            assert self.is_feature_enabled(
                features
            ), f"authselect features {features!r} should be enabled after selecting {profile}!"

    def list(self) -> ProcessResult:
        """
        Run ``authselect list``.

        :return: Command result.
        :rtype: ProcessResult
        """
        return self.host.conn.run("authselect list", raise_on_error=False)

    def current(self, raw: bool = False) -> str:
        """
        Return current Authselect configuration.

        :param raw: If True, run ``authselect current --raw``, defaults to False
        :type raw: bool, optional
        :return: Authselect configuration
        :rtype: str
        """
        args = ["authselect", "current"]
        if raw:
            args.append("--raw")

        return self.host.conn.exec(args).stdout

    def disable_feature(self, features: List[str]) -> None:
        """
        Disable Authselect feature.
        :param features: Authselect features to disable
        :type: list[str], required
        """
        self.host.conn.exec(["authselect", "disable-feature", *features, *self._backup_args()])

    def enable_feature(self, features: List[str]) -> None:
        """
        Enable Authselect feature.
        :param features:  Authselect features to enable
        :type: list[str], required
        """
        self.host.conn.exec(["authselect", "enable-feature", *features, *self._backup_args()])

    def is_feature_enabled(self, feature: str | List[str]) -> bool:
        """
        Check whether authselect features are enabled.

        Runs ``authselect is-feature-enabled`` for each given feature. When multiple
        features are passed, returns ``True`` only if every feature is enabled.

        :param feature: Feature name or list of feature names.
        :type feature: str | list[str]
        :return: ``True`` if the feature (or every feature in the list) is enabled.
        :rtype: bool
        """
        features = [feature] if isinstance(feature, str) else feature

        for name in features:
            result = self.host.conn.exec(["authselect", "is-feature-enabled", name], raise_on_error=False)
            if result.rc != 0:
                return False

        return True
