SSSD profile tests (``test_sssd.py``)
#####################################

Tests in ``src/tests/system/tests/test_sssd.py`` exercise the authselect
``sssd`` profile against a FreeIPA domain.

Marker and fixtures
*******************

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.roles.generic import GenericProvider
    from authselect_test_framework.profiles import Profile


    @pytest.mark.topology(Profile.SSSD)
    def test_sssd__example(client: Client, provider: GenericProvider):
        ...

* ``client`` — authselect client enrolled into IPA
* ``provider`` — ``sssd.ipa[0]`` (implements :class:`~authselect_test_framework.roles.generic.GenericProvider`)

Common pattern
**************

Functional tests follow the same flow:

1. Create users or rules on ``provider``
2. ``client.authselect.select("sssd", [features])``
3. Configure and start ``client.sssd``
4. Exercise the feature (authentication, sudo, getent, …)
5. ``client.authselect.disable_feature([...])`` and verify the feature is off

Use descriptive assertion messages ending with ``!``.

with-mkhomedir
==============

``test_sssd__with_mkhomedir`` — oddjob creates ``/home/user-1`` on first SSH login.

.. code-block:: python

    client.fs.backup("/home/user-1")

    provider.user("user-1").add(home="/home/user-1")

    client.fs.rm("/home/user-1")
    client.authselect.select("sssd", ["with-mkhomedir"])
    client.oddjob.start()
    client.sssd.start()

    assert client.auth.ssh.password("user-1", "Secret123"), "user-1 should be able to log in!"
    assert client.fs.exists("/home/user-1"), "/home/user-1 should be created on first login!"

    client.fs.rm("/home/user-1")
    client.authselect.disable_feature(["with-mkhomedir"])

    assert client.auth.ssh.password("user-1", "Secret123"), "user-1 should be able to log in!"
    assert not client.fs.exists("/home/user-1"), "/home/user-1 should not exist without with-mkhomedir!"

with-faillock
=============

``test_all_profiles__with_faillock`` — PAM faillock lockout via ``su``, reset with ``faillock``.

.. code-block:: python

    from authselect_test_framework.utils.pam import PAMFaillockUtils
    from pytest_mh import mh_utility

    provider.user("user-1").add()

    faillock = PAMFaillockUtils(client.host, client.fs)
    with mh_utility(faillock):
        faillock.config_set({"deny": "3", "unlock_time": "300"})

        client.authselect.select("sssd", ["with-faillock"])
        client.sssd.enable_responder("pam")
        client.sssd.start()

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

with-sudo
=========

``test_sssd__with_sudo`` — IPA sudo rules through the SSSD sudo responder.

.. code-block:: python

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

with-pamaccess
================

``test_sssd__with_pamaccess`` — ``/etc/security/access.conf`` rules with SSH auth.

.. code-block:: python

    from authselect_test_framework.utils.pam import PAMAccessUtils
    from pytest_mh import mh_utility

    provider.user("user-1").add()
    provider.user("user-2").add()

    access = PAMAccessUtils(client.host, client.fs)
    with mh_utility(access):
        access.config_set(
            [
                {"access": "+", "user": "user-1", "origin": "ALL"},
                {"access": "-", "user": "user-2", "origin": "ALL"},
            ]
        )

        client.authselect.select("sssd", ["with-pamaccess"])
        client.sssd.start()

        assert client.auth.ssh.password("user-1", "Secret123"), (
            "SSH authentication failed for permitted user-1 with with-pamaccess enabled!"
        )
        assert not client.auth.ssh.password("user-2", "Secret123"), (
            "SSH authentication should be denied for user-2 with with-pamaccess enabled!"
        )

with-silent-lastlog
===================

``test_sssd__with_silent_lastlog`` — ``su`` output with and without last-login banner.

.. code-block:: python

    provider.user("user-1").add()
    client.authselect.select("sssd", ["with-silent-lastlog"])
    client.sssd.start()

    client.auth.su.password_with_output("user-1", password="Secret123")
    result = client.auth.su.password_with_output("user-1", password="Secret123")
    assert "Last login:" not in result[2], (
        "su output should not contain last login information with with-silent-lastlog enabled!"
    )

with-gssapi
===========

``test_sssd__with_gssapi`` — Kerberos-backed passwordless sudo over SSH.

.. code-block:: python

    provider.user("user-1").add()
    provider.sudorule("test").add(user="user-1", host="ALL", command="/bin/ls")
    client.authselect.select("sssd", ["with-gssapi", "with-sudo"])
    client.sssd.enable_responder("sudo")
    client.sssd.domain["pam_gssapi_services"] = "sudo, sudo-i"
    client.sssd.domain["pam_gssapi_check_upn"] = "False"
    client.sssd.start()

    with client.ssh("user-1", "Secret123") as ssh:
        assert ssh.run(f"kinit user-1@{provider.realm}", input="Secret123"), (
            f"kinit failed for user-1@{provider.realm} with with-gssapi enabled!"
        )
        assert "(root) /bin/ls" in ssh.run("sudo -l").stdout, (
            "sudo rule was not listed with with-gssapi enabled!"
        )
        assert ssh.run("sudo /bin/ls /root"), "sudo command failed with with-gssapi enabled!"

with-group-merging
==================

``test_sssd__with_group_merging`` — merged group lookup via ``getent``.

.. code-block:: python

    client.local.group("group").add(gid=123456)
    provider.group("group").add(gid=123456).add_member(provider.user("user").add())
    client.authselect.select("sssd", ["with-group-merging"])
    client.sssd.start()

    group = client.tools.getent.group("group")
    assert group is not None, "merged group lookup should find 'group'!"
    assert "user" in group.members, "'user' is not a member of the merged group lookup!"

    files_group = client.tools.getent.group("group", service="files")
    assert files_group is not None, "files group lookup should find 'group'!"
    assert "user" not in files_group.members, (
        "'user' should not be a member of the files-only group lookup!"
    )

Skeleton tests
**************

The remaining ``test_sssd__*`` cases are ``@pytest.mark.skip`` placeholders for
features listed by ``authselect list-features sssd``. Implement them by
following the enable → verify → disable pattern above.