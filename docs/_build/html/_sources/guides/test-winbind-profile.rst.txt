Winbind profile tests (``test_winbind.py``)
###########################################

Tests in ``src/tests/system/tests/test_winbind.py`` exercise the authselect
``winbind`` profile against a Samba AD domain.

Marker and fixtures
*******************

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.topology import Profile


    @pytest.mark.topology(Profile.Winbind)
    def test_winbind__example(client: Client, provider: GenericProvider):
        ...

* ``client`` — client configured for winbind (SSSD disabled by :class:`~authselect_test_framework.controllers.WinbindController`)
* ``provider`` — ``sssd.samba[0]`` (Samba AD, implements :class:`~authselect_test_framework.roles.generic.GenericProvider`)

Common pattern
**************

Winbind tests mirror the SSSD profile flow with these substitutions:

* ``client.authselect.select("winbind", [features])`` instead of ``"sssd"``
* ``client.winbind.start()`` instead of ``client.sssd.start()``
* Samba users are often created with explicit POSIX attributes:

.. code-block:: python

    provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")

with-mkhomedir
==============

``test_winbind__with_mkhomedir`` — same mkhomedir flow as SSSD, using winbind.

.. code-block:: python

    client.fs.backup("/home/user-1")

    provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")

    client.fs.rm("/home/user-1")
    client.authselect.select("winbind", ["with-mkhomedir"])
    client.oddjob.start()
    client.winbind.start()

    assert client.auth.ssh.password("user-1", "Secret123"), "user-1 should be able to log in!"
    assert client.fs.exists("/home/user-1"), "/home/user-1 should be created on first login!"

    client.fs.rm("/home/user-1")
    client.authselect.disable_feature(["with-mkhomedir"])

    assert client.auth.ssh.password("user-1", "Secret123"), "user-1 should be able to log in!"
    assert not client.fs.exists("/home/user-1"), "/home/user-1 should not exist without with-mkhomedir!"

with-faillock
=============

``test_all_profiles__with_faillock`` — PAM faillock with ``su``; no SSSD pam responder.

.. code-block:: python

    from authselect_test_framework.utils.pam import PAMFaillockUtils
    from pytest_mh import mh_utility

    provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")

    faillock = PAMFaillockUtils(client.host, client.fs)
    with mh_utility(faillock):
        faillock.config_set({"deny": "3", "unlock_time": "300"})

        client.authselect.select("winbind", ["with-faillock"])
        client.winbind.start()

        assert client.auth.su.password("user-1", "Secret123"), (
            "Initial su authentication failed for user-1 with with-faillock enabled!"
        )

        for i in range(3):
            client.auth.su.password("user-1", "BadSecret123")

        assert not client.auth.su.password("user-1", "Secret123"), (
            "user-1 should be locked out after 3 failed authentication attempts!"
        )
        client.tools.faillock(["--user", "user-1", "--reset"])
        assert client.auth.su.password("user-1", "Secret123"), (
            "su authentication failed for user-1 after faillock reset!"
        )

        client.authselect.disable_feature(["with-faillock"])

        for i in range(3):
            client.auth.su.password("user-1", "BadSecret123")
        assert client.auth.su.password("user-1", "Secret123"), (
            "user-1 should not be locked out after with-faillock was disabled!"
        )

with-pamaccess
==============

``test_winbind__with_pamaccess`` — SSH access control.

.. code-block:: python

    from authselect_test_framework.utils.pam import PAMAccessUtils
    from pytest_mh import mh_utility

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

        assert client.auth.ssh.password("user-1", "Secret123"), (
            "SSH authentication failed for permitted user-1 with with-pamaccess enabled!"
        )
        assert not client.auth.ssh.password("user-2", "Secret123"), (
            "SSH authentication should be denied for user-2 with with-pamaccess enabled!"
        )

with-silent-lastlog
===================

``test_winbind__with_silent_lastlog`` — same last-login check as SSSD, via winbind.

.. code-block:: python

    provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")
    client.authselect.select("winbind", ["with-silent-lastlog"])
    client.winbind.start()

    client.auth.su.password_with_output("user-1", password="Secret123")
    result = client.auth.su.password_with_output("user-1", password="Secret123")
    assert "Last login:" not in result[2], (
        "su output should not contain last login information with with-silent-lastlog enabled!"
    )

with-gssapi
===========

``test_winbind__with_gssapi`` — Kerberos sudo over SSH; no extra SSSD domain options.

.. code-block:: python

    provider.user("user-1").add(uid=10001, gid=10001, home="/home/user-1", shell="/bin/bash")
    provider.sudorule("test").add(user="user-1", host="ALL", command="/bin/ls")
    client.authselect.select("winbind", ["with-gssapi", "with-sudo"])
    client.winbind.start()

    with client.ssh("user-1", "Secret123") as ssh:
        assert ssh.run(f"kinit user-1@{provider.realm}", input="Secret123"), (
            f"kinit failed for user-1@{provider.realm} with with-gssapi enabled!"
        )
        assert "(root) /bin/ls" in ssh.run("sudo -l").stdout, (
            "sudo rule was not listed with with-gssapi enabled!"
        )
        assert ssh.run("sudo /bin/ls /root"), "sudo command failed with with-gssapi enabled!"

SSSD vs winbind differences
***************************

.. list-table::
   :header-rows: 1

   * - Step
     - SSSD profile
     - Winbind profile
   * - Profile marker
     - ``Profile.SSSD``
     - ``Profile.Winbind``
   * - authselect profile
     - ``"sssd"``
     - ``"winbind"``
   * - Identity service
     - ``client.sssd.start()``
     - ``client.winbind.start()``
   * - Provider fixture
     - FreeIPA (``provider`` → IPA)
     - Samba AD (``provider`` → Samba)
   * - Sudo / pamaccess extras
     - SSSD responders and domain options
     - winbind only; no ``client.sssd`` configuration

Skeleton tests
**************

The remaining ``test_winbind__*`` cases are ``@pytest.mark.skip`` placeholders for
features listed by ``authselect list-features winbind``. Use the implemented
tests above as templates when filling them in.