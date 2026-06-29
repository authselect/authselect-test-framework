Core concepts
#############

The authselect test framework is a minimal fork of `sssd-test-framework
<https://github.com/SSSD/sssd-test-framework>`_ used by `authselect system tests
<https://github.com/authselect/authselect/tree/master/src/tests/system>`_.

It provides:

* **Profiles** — predefined multihost topologies for authselect profiles
  (:class:`~authselect_test_framework.topology.Profile`)
* **Roles** — client, IPA and Samba hosts with a Python API for test setup
* **Utilities** — authselect, SSSD, winbind, oddjob, PAM, authentication and
  local user helpers

Tests are written with `pytest`_, the `pytest-mh`_ plugin and this framework.
Each test that needs remote hosts is marked with ``@pytest.mark.topology`` using
one of the predefined profiles.

.. _pytest: https://docs.pytest.org
.. _pytest-mh: https://pytest-mh.readthedocs.io
