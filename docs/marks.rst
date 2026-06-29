Additional markers and metadata
###############################

Additional test metadata
************************

Each test should include the following metadata in its docstring:

.. code-block:: python

    def test_example():
        """
        :title: Human readable test title
        :setup:
            1. Setup step
        :steps:
            1. Test step
        :expectedresults:
            1. Expected result
        :customerscenario: False|True
        """

@pytest.mark.ticket
===================

Associate a test with GitHub issues, Bugzilla or JIRA tickets.

.. code-block:: python

    @pytest.mark.ticket(bz=2077893)
    @pytest.mark.ticket(jira="SSSD-7706")
    def test_example():
        pass

Run tests for a specific ticket:

.. code-block:: text

    pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --ticket=bz#2077893

@pytest.mark.importance
=======================

Associate a test with a level of importance: ``critical``, ``high``, ``medium`` or
``low``.

.. code-block:: python

    @pytest.mark.importance("critical")
    def test_example():
        pass

@pytest.mark.builtwith
======================

Skip tests when a host does not support a required SSSD feature:

.. code-block:: python

    import pytest

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.profiles import Profile

    @pytest.mark.topology(Profile.Local)
    @pytest.mark.builtwith("files-provider")
    def test_example(client: Client):
        pass

``@pytest.mark.builtwith`` is converted to ``@pytest.mark.require`` from
pytest-mh. See `runtime requirements
<https://pytest-mh.readthedocs.io/en/latest/runtime-requirements.html>`_.

@pytest.mark.topology
=====================

Required for tests that use multihost fixtures. Use
:class:`~authselect_test_framework.profiles.Profile` values:

.. code-block:: python

    import pytest

    from authselect_test_framework.profiles import Profile

    @pytest.mark.topology(Profile.Local)
    @pytest.mark.topology(Profile.SSSD)
    @pytest.mark.topology(Profile.Winbind)
