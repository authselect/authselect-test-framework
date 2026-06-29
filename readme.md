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
