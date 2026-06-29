# Authselect Test Framework

Minimal test framework for [authselect system tests](https://github.com/authselect/authselect/tree/master/src/tests/system).

It is derived from [sssd-test-framework](https://github.com/SSSD/sssd-test-framework) and includes only the components required by authselect tests:

* Client, IPA and Samba roles
* Profiles: `Profile.Local`, `Profile.SSSD`, `Profile.Winbind`
* Authselect, PAM, authentication, SSSD, winbind and oddjob utilities used by the system tests

## Installation

```bash
pip install git+https://github.com/authselect/authselect-test-framework
```

Or install from a local checkout:

```bash
pip install /path/to/authselect-test-framework
```

## Running tests

### Installing requirements

Authselect system tests are written in Python using [pytest](https://pytest.org)
and additional plugins. Install the dependencies inside a virtual environment:

```bash
# Install python-ldap and pylibssh dependencies
sudo dnf install -y gcc python3-devel openldap-devel libssh libssh-devel

# Install test dependencies
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

#### Important pytest plugins

* [pytest-mh](https://pytest-mh.readthedocs.io): multihost testing support
* [pytest-ticket](https://github.com/next-actions/pytest-ticket): `@pytest.mark.ticket(...)` and `--ticket` option
* [pytest-tier](https://github.com/next-actions/pytest-tier): `@pytest.mark.tier(...)` and `--tier` option
* [pytest-importance](https://github.com/next-actions/pytest-importance): `@pytest.mark.importance(...)` and `--importance` option

### Setting up multihost environment

Tests run commands on remote machines rather than the local host, to keep the
setup flexible and avoid changing anything on your machine. authselect has no
container images of its own, so it reuses
[sssd-ci-containers](https://github.com/SSSD/sssd-ci-containers) — it already
ships ready-to-use client, IPA and Samba hosts with authselect and SSSD/
winbind installed, avoiding the need to build and maintain a separate set of
images just for this smaller test matrix.

#### Starting the containers

```bash
git clone https://github.com/SSSD/sssd-ci-containers.git
cd sssd-ci-containers

sudo dnf install -y podman podman-docker docker-compose
sudo systemctl enable --now podman.socket
sudo setsebool -P container_manage_cgroup true

cp env.example .env
sudo make trust-ca
sudo make setup-dns
sudo make up
```

Only the client, IPA and Samba containers are required for authselect tests.

#### Multihost configuration

The authselect repository ships `src/tests/system/mhc.yaml`, configured for
the three supported profiles: `local`, `sssd` and `winbind`. See
[Multihost configuration](docs/config.rst) for the full schema.

### Running tests

From the authselect source tree:

```bash
cd src/tests/system
pytest --mh-config=mhc.yaml --mh-lazy-ssh -v
```

Filter by profile name:

```bash
pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --mh-topology=sssd
pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --mh-topology=winbind
pytest --mh-config=mhc.yaml --mh-lazy-ssh -v --mh-topology=local
```

> **See also**
> [pytest-mh documentation](https://pytest-mh.readthedocs.io) for additional
> options such as `--mh-log-path` and `--mh-topology`.

## Documentation

Full documentation, including [Writing tests](docs/writing-tests.rst),
[Core concepts](docs/concepts.rst), and the [API reference](docs/api.rst), is
built with Sphinx from the [docs/](docs) directory and modeled after the
[SSSD system test documentation](https://tests.sssd.io/en/latest/index.html).
