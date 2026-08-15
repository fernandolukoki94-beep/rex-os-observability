from backend.core.services.access_control import Actor


def test_roles_have_expected_permissions():
    assert Actor("a", "ADMIN").can("manage")
    assert Actor("s", "SUPERVISOR").can("sync")
    assert Actor("o", "OPERATOR").can("write")
    assert not Actor("v", "VIEWER").can("write")
