# Standard Library
import socket

# Django
from django.test import RequestFactory, TestCase

# AA TaxSystem
# AA Skillfarm
from taxsystem.tests.testdata.integrations.allianceauth import load_allianceauth
from taxsystem.tests.testdata.integrations.eveuniverse import load_eveuniverse
from taxsystem.tests.testdata.utils import create_user_from_evecharacter


class SocketAccessError(Exception):
    """Error raised when a test script accesses the network"""


class NoSocketsTestCase(TestCase):
    """Variation of Django's TestCase class that prevents any network use.

    Example:

        .. code-block:: python

            class TestMyStuff(BaseTestCase):
                def test_should_do_what_i_need(self): ...

    """

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


class TaxSystemTestCase(NoSocketsTestCase):
    """
    Preloaded Testcase class for TaxSystem tests without Network access.

    Pre-Load:
        * Alliance Auth Characters, Corporation, Alliance Data
        * Eve Universe Data

    Available Request Factory:
        `self.factory`

    Available test users:
        * `user` User with standard Skillfarm access.
            * 'skillfarm.basic_access' Permission
            * Character ID 1001
            * Corporation ID 2001
        * `user_2` Second user with standard Skillfarm access.
            * 'skillfarm.basic_access' Permission
            * Character ID 1004
            * Corporation ID 2001
        * `manage_own_user` User with manage own corporation access.
            * 'skillfarm.basic_access' Permission
            * 'skillfarm.manage_own_corp' Permission
            * Character ID 1005
            * Corporation ID 2001
        * `manage_user` User with manage corporations access.
            * 'skillfarm.basic_access' Permission
            * 'skillfarm.manage_corps' Permission
            * Character ID 1006
            * Corporation ID 2001
        * `no_permission_user` User without any Skillfarm permissions.
            * No Permissions
            * Character ID 1002
        * `superuser` Superuser.
            * Access to whole Application
            * Character ID 1003

    Example:
        .. code-block:: python

            class TestMyTaxSystemStuff(TaxSystemTestCase):
                def test_should_do_what_i_need(self):
                    user = self.user
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Initialize Alliance Auth test data
        load_allianceauth()
        load_eveuniverse()

        # Request Factory
        cls.factory = RequestFactory()

        # User with Standard Access - Corporation 2001
        cls.user, cls.user_character = create_user_from_evecharacter(
            character_id=1001,
            permissions=["taxsystem.basic_access"],
        )
        # User with Standard Access - Corporation 2001
        cls.user_2, cls.user_2_character = create_user_from_evecharacter(
            character_id=1004,
            permissions=["taxsystem.basic_access"],
        )
        # User with Manage Own Corporation Access - Corporation 2001
        cls.manage_own_user, cls.manage_own_character = create_user_from_evecharacter(
            character_id=1005,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_own_corp",
            ],
        )
        # User with Manage Corporations Access - Corporation 2001
        cls.manage_user, cls.manage_character = create_user_from_evecharacter(
            character_id=1006,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
            ],
        )
        # User without Access to TaxSystem - Corporation 2002
        cls.no_permission_user, cls.no_perm_character = create_user_from_evecharacter(
            character_id=1002,
            permissions=[],
        )

        # User with Superuser Access - Corporation 2003
        cls.superuser, cls.superuser_character = create_user_from_evecharacter(
            character_id=1003,
            permissions=[],
        )
        cls.superuser.is_superuser = True
        cls.superuser.save()
