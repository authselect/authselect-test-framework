Writing new tests
#################

Authselect system tests use `pytest`_, `pytest-mh`_ and
:mod:`authselect_test_framework`.

.. _pytest: https://docs.pytest.org
.. _pytest-mh: https://pytest-mh.readthedocs.io

Using profile markers
*********************

Each test that requires remote hosts must be marked with a topology marker.
Use predefined profiles from :class:`authselect_test_framework.topology.Profile`:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.topology import Profile


    @pytest.mark.topology(Profile.Local)
    def test_example(client: Client):
        client.authselect.select("local")
        assert True

Available profiles
==================

.. list-table::
   :header-rows: 1

   * - Profile
     - Hosts
     - Use case
   * - :attr:`~authselect_test_framework.topology.Profile.Local`
     - client
     - Local profile, presets, CLI tests
   * - :attr:`~authselect_test_framework.topology.Profile.SSSD`
     - client + ipa
     - SSSD profile with FreeIPA provider
   * - :attr:`~authselect_test_framework.topology.Profile.Winbind`
     - client + samba
     - Winbind profile against a Samba AD domain

All profiles — :attr:`~authselect_test_framework.topology.ProfileGroup.AnyProfile`
==================================================================================

Some authselect features behave the same on every profile. Put those tests in
``test_all_profiles.py`` and mark them with
:class:`~authselect_test_framework.topology.ProfileGroup`. pytest-mh then
parametrizes the test and runs it once per profile (local, sssd, winbind).

From ``test_all_profiles__with_ecryptfs``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.topology import Profile, ProfileGroup


    @pytest.mark.topology(ProfileGroup.AnyProfile)
    def test_all_profiles__with_ecryptfs(client: Client, profile: Profile):
        client.authselect.select(profile.value.name, ["with-ecryptfs"])
        client.authselect.assert_selected(profile.value.name, ["with-ecryptfs"])

        assert client.authselect.is_feature_enabled("with-ecryptfs"), (
            "with-ecryptfs should be enabled!"
        )
        system_auth = client.fs.read("/etc/pam.d/system-auth")
        assert "pam_ecryptfs.so" in system_auth, "system-auth should include pam_ecryptfs!"

        client.authselect.disable_feature(["with-ecryptfs"])

        assert not client.authselect.is_feature_enabled("with-ecryptfs"), (
            "with-ecryptfs should be disabled!"
        )

Functional shared tests need users or identity services that differ per profile.
Use the ``profile`` fixture and branch on :class:`~authselect_test_framework.topology.Profile`
members instead of inspecting host roles or ``mh_topology_mark``:

.. code-block:: python

    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.topology import Profile, ProfileGroup


    @pytest.mark.topology(ProfileGroup.AnyProfile)
    def test_all_profiles__with_faillock(
        client: Client,
        provider: GenericProvider,
        profile: Profile,
    ):
        provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")

        client.authselect.select(profile.value.name, ["with-faillock"])
        start_client_service(client, profile, users=["user-1"])

        if profile is not Profile.Local:
            assert client.tools.id("user-1") is not None, (
                f"user should be resolvable via {profile.value.name}!"
            )

        assert client.auth.su.password("user-1", "Secret123"), (
            "initial su authentication should succeed!"
        )

Notes:

* ``profile`` — :func:`~authselect_test_framework.fixtures.profile` fixture;
  ``Profile.Local``, ``Profile.SSSD``, or ``Profile.Winbind`` for the current run
* ``profile.value.name`` — authselect profile string (``"local"``, ``"sssd"``,
  ``"winbind"``)
* ``provider`` must appear in the test signature when the test uses it (do not
  call ``request.getfixturevalue("provider")``)
* ``provider.user(...).add()`` creates users on the active provider (local client,
  IPA, or Samba); ``start_client_service()`` in ``test_all_profiles.py`` starts
  profile-specific identity services

Provider fixture tests
======================

Authselect tests are grouped by profile (``test_sssd.py``, ``test_winbind.py``).
The ``provider`` fixture points to ``sssd.ipa[0]`` on the SSSD profile and
``sssd.samba[0]`` on the Winbind profile.

SSSD — with-sudo
================

From ``test_sssd__with_sudo``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.topology import Profile


    @pytest.mark.topology(Profile.SSSD)
    def test_sssd__with_sudo(client: Client, provider: GenericProvider):
        provider.user("user-1").add()
        provider.sudorule("test").add(user="user-1", host="ALL", command="/bin/ls")

        client.authselect.select("sssd", ["with-sudo"])
        client.sssd.enable_responder("sudo")
        client.sssd.start()

        assert client.auth.sudo.list(
            "user-1", "Secret123", expected=["(root) /bin/ls"]
        ), "sudo rule was not listed for user-1 with with-sudo enabled!"
        assert client.auth.sudo.run(
            "user-1", "Secret123", command="/bin/ls /root"
        ), "sudo command failed for user-1 with with-sudo enabled!"

        client.authselect.disable_feature(["with-sudo"])

        assert not client.auth.sudo.list(
            "user-1", "Secret123", expected=["(root) /bin/ls"]
        ), "sudo rule should not be listed for user-1 after with-sudo was disabled!"

Winbind — with-pamaccess
========================

From ``test_winbind__with_pamaccess``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.topology import Profile
    from authselect_test_framework.utils.pam import PAMAccessUtils
    from pytest_mh import mh_utility


    @pytest.mark.topology(Profile.Winbind)
    def test_winbind__with_pamaccess(client: Client, provider: GenericProvider):
        provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")
        provider.user("user-2").add(uid=10002, gid=10002, home="/home/user-2", shell="/bin/bash")

        access = PAMAccessUtils(client.host, client.fs)
        with mh_utility(access):
            access.config_set(
                [
                    {"access": "+", "user": "user-1", "origin": "ALL"},
                    {"access": "-", "user": "user-2", "origin": "ALL"},
                ]
            )

            client.authselect.select("winbind", ["with-pamaccess"])
            client.winbind.start()

            assert client.auth.ssh.password(
                "user-1", "Secret123"
            ), "SSH authentication failed for permitted user-1 with with-pamaccess enabled!"
            assert not client.auth.ssh.password(
                "user-2", "Secret123"
            ), "SSH authentication should be denied for user-2 with with-pamaccess enabled!"

            client.authselect.disable_feature(["with-pamaccess"])

            assert client.auth.ssh.password(
                "user-1", "Secret123"
            ), "SSH authentication failed for user-1 after with-pamaccess was disabled!"
            assert client.auth.ssh.password(
                "user-2", "Secret123"
            ), "SSH authentication failed for user-2 after with-pamaccess was disabled!"

conftest.py
===========

Authselect tests load the framework through ``conftest.py``:

.. code-block:: python

    from pytest_mh import MultihostPlugin
    from authselect_test_framework.config import AuthselectMultihostConfig

    pytest_plugins = (
        "pytest_importance",
        "pytest_mh",
        "pytest_ticket",
        "pytest_tier",
        "authselect_test_framework.fixtures",
        "authselect_test_framework.markers",
    )

    def pytest_plugin_registered(plugin) -> None:
        if isinstance(plugin, MultihostPlugin):
            plugin.config_class = AuthselectMultihostConfig

.. seealso::

    ``src/tests/system/tests/test_all_profiles.py`` for shared feature tests across
    all profiles.
    :doc:`guides/test-sssd-profile` for SSSD-only examples from ``test_sssd.py``.
    :doc:`guides/test-winbind-profile` for Winbind-only examples from ``test_winbind.py``.
    :doc:`api` for the full API reference.
