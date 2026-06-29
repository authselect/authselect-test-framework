Running tests
#############

Installing requirements
***********************

Authselect system tests are written in Python using `pytest`_ and additional
plugins. Install dependencies inside a virtual environment:

.. code-block:: text

    sudo dnf install -y gcc python3-devel openldap-devel libssh libssh-devel

    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install -r requirements.txt

Important pytest plugins
========================

* `pytest-mh`_: multihost testing support
* `pytest-ticket`_: ``@pytest.mark.ticket(...)`` and ``--ticket`` option
* `pytest-tier`_: ``@pytest.mark.tier(...)`` and ``--tier`` option
* `pytest-importance`_: ``@pytest.mark.importance(...)`` and ``--importance`` option

Setting up multihost environment
********************************

Tests run commands on remote machines. Use `sssd-ci-containers`_ to provide
client, IPA and Samba hosts.

.. _sssd-ci-containers: https://github.com/SSSD/sssd-ci-containers

Starting containers
===================

.. code-block:: bash

    git clone https://github.com/SSSD/sssd-ci-containers.git
    cd sssd-ci-containers

    sudo dnf install -y podman podman-docker docker-compose
    sudo systemctl enable --now podman.socket
    sudo setsebool -P container_manage_cgroup true

    cp env.example .env
    sudo make trust-ca
    sudo make setup-dns
    sudo make up

Only client, IPA and Samba containers are required for authselect tests.

Multihost configuration
=========================

See :doc:`config` for details. The authselect repository ships
``src/tests/system/mhc.yaml`` configured for the three supported profiles:
``local``, ``sssd`` and ``winbind``.

Running tests
*************

From the authselect source tree:

.. code-block:: text

    cd src/tests/system
    pytest --mh-config=mhc.yaml --mh-lazy-ssh -v

Filter by profile name:

.. code-block:: text

    pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --mh-topology=sssd
    pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --mh-topology=winbind
    pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --mh-topology=local

.. seealso::

  `pytest-mh documentation <https://pytest-mh.readthedocs.io>`_ for additional
  options such as ``--mh-log-path`` and ``--mh-topology``.

.. _pytest: https://pytest.org
.. _pytest-mh: https://pytest-mh.readthedocs.io
.. _pytest-ticket: https://github.com/next-actions/pytest-ticket
.. _pytest-tier: https://github.com/next-actions/pytest-tier
.. _pytest-importance: https://github.com/next-actions/pytest-importance
