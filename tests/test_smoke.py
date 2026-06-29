"""Framework smoke tests that do not require remote hosts."""

from __future__ import annotations

from authselect_test_framework.profiles import Profile, ProfileGroup


def test_profiles_are_defined() -> None:
    assert Profile.Local.value.name == "local"
    assert Profile.SSSD.value.name == "sssd"
    assert Profile.Winbind.value.name == "winbind"
    assert ProfileGroup.AnyProfile.value == [Profile.Local, Profile.SSSD, Profile.Winbind]
