Writing new tests
#################

Authselect system tests use `pytest`_, `pytest-mh`_ and
:mod:`authselect_test_framework`.

.. _pytest: https://docs.pytest.org
.. _pytest-mh: https://pytest-mh.readthedocs.io

Using profile markers
*********************

Each test that requires remote hosts must be marked with a topology marker.
Use predefined profiles from :class:`authselect_test_framework.profiles.Profile`:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.profiles import Profile


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
   * - :attr:`~authselect_test_framework.profiles.Profile.Local`
     - client
     - Local profile, presets, CLI tests, and local-only PAM tests
   * - :attr:`~authselect_test_framework.profiles.Profile.SSSD`
     - client + ipa
     - SSSD profile with FreeIPA provider
   * - :attr:`~authselect_test_framework.profiles.Profile.Winbind`
     - client + samba
     - Winbind profile against a Samba AD domain

Choosing the right test file
*****************************

Use this table to decide where a test belongs:

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Topology
     - File
     - When to use
   * - :attr:`~authselect_test_framework.profiles.ProfileGroup.AnyProfile`
     - ``test_profiles.py``
     - Feature behaves the same on local, SSSD, and Winbind
   * - :attr:`~authselect_test_framework.profiles.ProfileGroup.AnyProvider`
     - ``test_profiles.py``
     - Feature requires a remote directory provider (SSSD or Winbind) but not local
   * - :attr:`~authselect_test_framework.profiles.Profile.Local`
     - ``test_local.py``
     - PAM behaviour only testable on the local profile (e.g. when ``pam_sss.so`` would intercept before ``pam_unix.so`` on sssd/winbind)
   * - :attr:`~authselect_test_framework.profiles.Profile.SSSD`
     - ``test_sssd.py``
     - SSSD-specific feature (e.g. ``with-sudo``, ``with-smartcard``)
   * - :attr:`~authselect_test_framework.profiles.Profile.Winbind`
     - ``test_winbind.py``
     - Winbind-specific feature (e.g. ``with-krb5``)
   * - ``Profile.Local``
     - ``test_cli.py``
     - CLI command output and exit codes only — no functional behaviour

All profiles — AnyProfile
==========================

Tests in ``test_profiles.py`` marked with
:attr:`~authselect_test_framework.profiles.ProfileGroup.AnyProfile` run once per
profile (local, sssd, winbind). Use ``client.profile`` to get the current profile
and ``client.profile`` as the profile string argument to ``authselect.select()``.

From ``test_profiles__with_ecryptfs``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.profiles import ProfileGroup


    @pytest.mark.topology(ProfileGroup.AnyProfile)
    def test_profiles__with_ecryptfs(client: Client, provider: GenericProvider):
        client.authselect.select(client.profile, ["with-ecryptfs"])

        system_auth = client.fs.read("/etc/pam.d/system-auth")
        assert "pam_ecryptfs.so" in system_auth, "system-auth should include pam_ecryptfs!"

        client.authselect.disable_feature(["with-ecryptfs"])

        system_auth = client.fs.read("/etc/pam.d/system-auth")
        assert "pam_ecryptfs.so" not in system_auth, (
            "system-auth should not include pam_ecryptfs after feature is disabled!"
        )

Functional shared tests that need users or an identity service use a helper
``start_identity_service`` (defined at the top of ``test_profiles.py``) and
branch on ``client.profile`` only where the behaviour genuinely differs:

From ``test_profiles__with_faillock``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.profiles import Profile, ProfileGroup
    from authselect_test_framework.utils.pam import PAMFaillockUtils
    from pytest_mh import mh_utility


    @pytest.mark.topology(ProfileGroup.AnyProfile)
    def test_profiles__with_faillock(client: Client, provider: GenericProvider):
        provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")

        start_identity_service(client, provider)

        faillock = PAMFaillockUtils(client.host, client.fs)
        with mh_utility(faillock):
            faillock.config_set({"deny": "3", "unlock_time": "300"})

            client.authselect.select(client.profile, ["with-faillock"])
            faillock.reset_user("user-1")

            if client.profile is not Profile.Local:
                assert client.tools.id("user-1") is not None, "'user-1' was not found!"
            assert client.auth.su.password("user-1", password="Secret123"), (
                "initial su authentication should succeed!"
            )

            for _ in range(3):
                client.auth.su.password("user-1", password="BadSecret123")

            assert not client.auth.su.password("user-1", password="Secret123"), (
                "user should be locked out after failed attempts!"
            )

            client.authselect.disable_feature(["with-faillock"])

            assert client.auth.su.password("user-1", password="Secret123"), (
                "su authentication should succeed after 'with-faillock' was disabled!"
            )

Notes:

* ``client.profile`` — current :class:`~authselect_test_framework.profiles.Profile`
  member (``Profile.Local``, ``Profile.SSSD``, or ``Profile.Winbind``)
* Pass ``client.profile`` directly to ``authselect.select()`` — it is accepted
  as the profile string argument
* ``provider.user(...).add()`` creates users on the active provider (local client,
  IPA, or Samba)
* ``start_identity_service(client, provider)`` starts SSSD or Winbind as needed;
  call it **before** ``authselect.select()`` so service start is a setup step
* ``select()`` calls ``assert_selected()`` internally — never call
  ``assert_selected()`` again after ``select()``, and never use
  ``is_feature_enabled()`` as a standalone assertion

Provider-backed profiles — AnyProvider
=======================================

:attr:`~authselect_test_framework.profiles.ProfileGroup.AnyProvider` covers SSSD
and Winbind only. Use it when the test requires a central directory (users in IPA
or Samba AD) but the feature is otherwise profile-agnostic.

From ``test_profiles__with_group_merging``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.profiles import ProfileGroup


    @pytest.mark.topology(ProfileGroup.AnyProvider)
    def test_profiles__with_group_merging(client: Client, provider: GenericProvider):
        client.local.group("group").add(gid=123456)
        provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")
        provider.group("group").add(gid=123456).add_member(provider.user("user-1"))

        start_identity_service(client, provider)

        client.authselect.select(client.profile, ["with-group-merging"])

        group = client.tools.getent.group("group")
        assert group is not None, "merged group lookup should find group!"
        assert "user-1" in group.members, "user should be a member of the merged group lookup!"

        files_group = client.tools.getent.group("group", service="files")
        assert "user-1" not in files_group.members, (
            "user should not be a member of the files-only group lookup!"
        )

        client.authselect.disable_feature(["with-group-merging"])

        nsswitch = client.fs.read("/etc/nsswitch.conf")
        group_line = next(line for line in nsswitch.splitlines() if line.startswith("group:"))
        assert "[SUCCESS=merge]" not in group_line, (
            "group nsswitch entry should not use 'SUCCESS=merge' when feature is disabled!"
        )

Local profile only — test_local.py
====================================

Some features can only be tested meaningfully on the local profile. For example,
``without-nullok`` removes ``nullok`` from ``pam_unix.so``, but on the sssd and
winbind profiles ``pam_sss.so`` short-circuits authentication with
``default=bad`` before ``pam_unix.so`` is ever reached for local users. Put such
tests in ``test_local.py``:

From ``test_local__without_nullok``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.profiles import Profile


    @pytest.mark.topology(Profile.Local)
    def test_local__without_nullok(client: Client):
        client.user("user-3").add(uid=10003, gid=10003, home="/home/user-3", shell="/bin/bash", password="")
        client.host.conn.run("passwd -d user-3")

        client.authselect.select("local", ["without-nullok"])

        assert not client.auth.su.password("user-3", password=""), (
            "login with empty password should be denied with 'without-nullok' enabled!"
        )

        client.authselect.disable_feature(["without-nullok"])

        system_auth = client.fs.read("/etc/pam.d/system-auth")
        assert "nullok" in system_auth, (
            "'pam_unix.so' should have 'nullok' after disabling 'without-nullok'!"
        )

SSSD — with-sudo
================

From ``test_sssd__with_sudo``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.profiles import Profile


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

Winbind — with-krb5
====================

From ``test_winbind__with_krb5``:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.samba import Samba
    from authselect_test_framework.profiles import Profile


    @pytest.mark.topology(Profile.Winbind)
    def test_winbind__with_krb5(client: Client, provider: Samba):
        provider.user("user-1").add(uid=10002, gid=10002, home="/home/user-1", shell="/bin/bash")

        client.authselect.select("winbind", ["with-krb5"])
        client.winbind.start()

        result = client.host.conn.run(
            f'su - "user-1" -c "kinit user-1@{provider.realm} && klist"',
            input="Secret123",
            raise_on_error=False,
        )
        assert result.rc == 0, "kinit should succeed with 'with-krb5' enabled!"
        assert f"krbtgt/{provider.realm}@{provider.realm}" in result.stdout, (
            "klist should show a TGT!"
        )

        client.authselect.disable_feature(["with-krb5"])

        result = client.host.conn.run(
            f'su - "user-1" -c "kinit user-1@{provider.realm} && klist"',
            input="Secret123",
            raise_on_error=False,
        )
        assert result.rc == 0, "kinit should still succeed after 'with-krb5' was disabled!"
        assert client.auth.ssh.password("user-1", password="Secret123"), (
            "domain user password login should succeed after 'with-krb5' was disabled!"
        )

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

    ``src/tests/system/tests/test_profiles.py`` for shared feature tests across
    all profiles and provider-backed topologies.
    ``src/tests/system/tests/test_local.py`` for local-only PAM feature tests.
    :doc:`guides/test-sssd-profile` for SSSD-only examples from ``test_sssd.py``.
    :doc:`guides/test-winbind-profile` for Winbind-only examples from ``test_winbind.py``.
    :doc:`api` for the full API reference.
