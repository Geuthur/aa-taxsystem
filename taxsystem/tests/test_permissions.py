"""Tests that all permission strings used in the code match General.Meta.permissions."""

# Standard Library
import re
from pathlib import Path

# Django
from django.test import TestCase

# AA TaxSystem
from taxsystem import __app_name__
from taxsystem.models.general import General

PACKAGE_DIR = Path(__file__).resolve().parent.parent
PY_PATTERN = re.compile(
    r"""(?:permission_required|has_perm)\(\s*["'](\w+)\.(\w+)["']"""
)
TEMPLATE_PATTERN = re.compile(r"""perms\.(\w+)\.(\w+)""")


def _used_permissions():
    """Return (file, app_label, codename) for every permission string in the code."""
    found = []
    for path in PACKAGE_DIR.rglob("*"):
        if "tests" in path.parts or "migrations" in path.parts:
            continue
        if path.suffix == ".py":
            pattern = PY_PATTERN
        elif path.suffix == ".html":
            pattern = TEMPLATE_PATTERN
        else:
            continue
        for label, codename in pattern.findall(path.read_text(encoding="utf-8")):
            found.append((path.name, label, codename))
    return found


class TestPermissionStrings(TestCase):
    """Permission strings in views, hooks, API, managers and templates must match General."""

    def test_used_permissions_match_general(self):
        codenames = {codename for codename, __ in General._meta.permissions}
        used = _used_permissions()
        self.assertTrue(used)
        for filename, label, codename in used:
            with self.subTest(file=filename, permission=f"{label}.{codename}"):
                self.assertEqual(label, __app_name__)
                self.assertIn(codename, codenames)
