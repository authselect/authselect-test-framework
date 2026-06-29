Testing PAM Modules
###################

PAM utilities are used with ``mh_utility`` from pytest-mh:

.. code-block:: python

    from pytest_mh._private.multihost import mh_utility

    from authselect_test_framework.utils.pam import PAMAccessUtils, PAMFaillockUtils

pam_access
==========

.. code-block:: python

    with mh_utility(PAMAccessUtils(client.host, client.fs)) as access:
        access.config_set(
            [{"access": "+", "user": "user-1", "origin": "ALL"},
             {"access": "-", "user": "user-2", "origin": "ALL"}]
        )
        client.authselect.select("sssd", ["with-pamaccess"])
        client.sssd.start()

pam_faillock
============

.. code-block:: python

    with mh_utility(PAMFaillockUtils(client.host, client.fs)) as faillock:
        faillock.config_set({"deny": "3", "unlock_time": "300"})
        client.sssd.common.pam(["with-faillock"])
        client.sssd.start()

        client.tools.faillock(["--user", "user-1", "--reset"])

.. seealso::

    :class:`~authselect_test_framework.utils.pam.PAMAccessUtils`
    :class:`~authselect_test_framework.utils.pam.PAMFaillockUtils`
