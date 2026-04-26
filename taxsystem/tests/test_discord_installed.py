# Standard Library
from types import SimpleNamespace
from unittest.mock import patch

# Django
from django.test import TestCase, modify_settings

# AA TaxSystem
from taxsystem.helpers import discord as discord_helper
from taxsystem.helpers.discord import (
    _discordbot_send_direct_message,
    _discordproxy_send_direct_message,
    allianceauth_discordbot_installed,
    discordnotify_installed,
    discordproxy_installed,
    send_user_notification,
)


class TestModulesInstalled(TestCase):
    @modify_settings(INSTALLED_APPS={"remove": "aadiscordbot"})
    def test_allianceauth_discordbot_installed_should_return_false(self):
        self.assertFalse(allianceauth_discordbot_installed())

    @modify_settings(INSTALLED_APPS={"append": "aadiscordbot"})
    def test_allianceauth_discordbot_installed_should_return_true(self):
        self.assertTrue(allianceauth_discordbot_installed())

    @modify_settings(INSTALLED_APPS={"remove": "discordnotify"})
    def test_aa_discordnotify_installed_should_return_false(self):
        self.assertFalse(discordnotify_installed())

    @modify_settings(INSTALLED_APPS={"append": "discordnotify"})
    def test_aa_discordnotify_installed_should_return_true(self):
        self.assertTrue(discordnotify_installed())

    @modify_settings(INSTALLED_APPS={"append": "discordproxy"})
    def test_discordproxy_installed_should_return_true(self):
        self.assertTrue(discordproxy_installed())

    def test_discordproxy_installed_should_return_false_on_modulenotfounderror(self):
        # Standard Library
        import builtins

        original_import = builtins.__import__

        def import_side_effect(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "discordproxy.client":
                raise ModuleNotFoundError("No module named 'discordproxy'")

            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=import_side_effect):
            self.assertFalse(discordproxy_installed())


class TestSendDiscordMessage(TestCase):
    @patch("aadiscordbot.tasks.send_message")
    def test_send_direct_message_with_embed_should_call_send_message_with_embed(
        self, mock_send_message
    ):
        _discordbot_send_direct_message(
            user_id=123456789,
            title="Test Message",
            message="This is a test message.",
            embed_message=True,
            level="info",
        )

        mock_send_message.assert_called_once()
        call_kwargs = mock_send_message.call_args.kwargs

        self.assertEqual(call_kwargs["user_id"], 123456789)
        self.assertIn("embed", call_kwargs)
        self.assertEqual(str(call_kwargs["embed"].title), "Test Message")
        self.assertEqual(call_kwargs["embed"].description, "This is a test message.")

    @patch("aadiscordbot.tasks.send_message")
    def test_send_direct_message_without_embed_should_call_send_message_with_text(
        self, mock_send_message
    ):
        _discordbot_send_direct_message(
            user_id=123456789,
            title="Test Message",
            message="This is a test message.",
            embed_message=False,
            level="info",
        )

        mock_send_message.assert_called_once_with(
            user_id=123456789,
            message="**Test Message**\n\nThis is a test message.",
        )

    @patch("discordproxy.client.DiscordClient.create_direct_message")
    def test_discordproxy_send_direct_message_should_call_create_direct_message(
        self, mock_create_direct_message
    ):
        _discordproxy_send_direct_message(
            user_id=123456789,
            title="Test Message",
            message="This is a test message.",
            embed_message=True,
            level="info",
        )

        mock_create_direct_message.assert_called_once()
        call_kwargs = mock_create_direct_message.call_args.kwargs

        self.assertEqual(call_kwargs["user_id"], 123456789)
        self.assertIn("embed", call_kwargs)
        self.assertEqual(call_kwargs["embed"].title, "Test Message")
        self.assertEqual(call_kwargs["embed"].description, "This is a test message.")

    @patch("discordproxy.client.DiscordClient.create_direct_message")
    def test_discordproxy_send_direct_message_without_embed_should_send_plain_text(
        self, mock_create_direct_message
    ):
        _discordproxy_send_direct_message(
            user_id=123456789,
            title="Test Message",
            message="This is a test message.",
            embed_message=False,
            level="info",
        )

        mock_create_direct_message.assert_called_once_with(
            user_id=123456789,
            content="**Test Message**\n\nThis is a test message.",
        )


class TestSendUserNotification(TestCase):
    @patch("taxsystem.helpers.discord.notify")
    @patch("taxsystem.helpers.discord.logger.warning")
    @patch("taxsystem.helpers.discord.User.objects.get")
    def test_send_user_notification_should_return_if_user_not_exists(
        self, mock_get_user, mock_logger_warning, mock_notify
    ):
        mock_get_user.side_effect = discord_helper.User.DoesNotExist

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_logger_warning.assert_called_once_with(
            "User with ID %s does not exist. Notification not sent.", 123
        )
        mock_notify.info.assert_not_called()

    @patch("taxsystem.helpers.discord._discordproxy_send_direct_message")
    @patch("taxsystem.helpers.discord._discordbot_send_direct_message")
    @patch("taxsystem.helpers.discord.notify")
    @patch("taxsystem.helpers.discord.User.objects.get")
    def test_send_user_notification_should_only_notify_if_user_has_no_discord(
        self,
        mock_get_user,
        mock_notify,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(username="tester")
        mock_get_user.return_value = user

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()

    @patch("taxsystem.helpers.discord._discordproxy_send_direct_message")
    @patch("taxsystem.helpers.discord._discordbot_send_direct_message")
    @patch("taxsystem.helpers.discord.allianceauth_discordbot_installed")
    @patch("taxsystem.helpers.discord.notify")
    @patch("taxsystem.helpers.discord.User.objects.get")
    def test_send_user_notification_should_use_discordbot_if_installed(
        self,
        mock_get_user,
        mock_notify,
        mock_discordbot_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user
        mock_discordbot_installed.return_value = True

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=False,
            level="warning",
        )

        mock_notify.warning.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_called_once_with(
            user_id=123456789,
            title="Test Title",
            message="Test Message",
            embed_message=False,
            level="warning",
        )
        mock_send_discordproxy.assert_not_called()

    @patch("taxsystem.helpers.discord._discordproxy_send_direct_message")
    @patch("taxsystem.helpers.discord._discordbot_send_direct_message")
    @patch("taxsystem.helpers.discord.discordproxy_installed")
    @patch("taxsystem.helpers.discord.discordnotify_installed")
    @patch("taxsystem.helpers.discord.allianceauth_discordbot_installed")
    @patch("taxsystem.helpers.discord.notify")
    @patch("taxsystem.helpers.discord.User.objects.get")
    def test_send_user_notification_should_use_discordproxy_if_available(
        self,
        mock_get_user,
        mock_notify,
        mock_discordbot_installed,
        mock_discordnotify_installed,
        mock_discordproxy_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user
        mock_discordbot_installed.return_value = False
        mock_discordnotify_installed.return_value = False
        mock_discordproxy_installed.return_value = True

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordproxy.assert_called_once_with(
            user_id=123456789,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )
        mock_send_discordbot.assert_not_called()

    @patch("taxsystem.helpers.discord._discordproxy_send_direct_message")
    @patch("taxsystem.helpers.discord._discordbot_send_direct_message")
    @patch("taxsystem.helpers.discord.discordproxy_installed")
    @patch("taxsystem.helpers.discord.discordnotify_installed")
    @patch("taxsystem.helpers.discord.allianceauth_discordbot_installed")
    @patch("taxsystem.helpers.discord.notify")
    @patch("taxsystem.helpers.discord.User.objects.get")
    def test_send_user_notification_should_not_send_discord_message_when_discordproxy_unavailable(
        self,
        mock_get_user,
        mock_notify,
        mock_discordbot_installed,
        mock_discordnotify_installed,
        mock_discordproxy_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user
        mock_discordbot_installed.return_value = False
        mock_discordnotify_installed.return_value = False
        mock_discordproxy_installed.return_value = False

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()

    @patch("taxsystem.helpers.discord._discordproxy_send_direct_message")
    @patch("taxsystem.helpers.discord._discordbot_send_direct_message")
    @patch("taxsystem.helpers.discord.discordnotify_installed")
    @patch("taxsystem.helpers.discord.allianceauth_discordbot_installed")
    @patch("taxsystem.helpers.discord.notify")
    @patch("taxsystem.helpers.discord.User.objects.get")
    def test_send_user_notification_should_not_send_direct_message_if_no_sender_available(
        self,
        mock_get_user,
        mock_notify,
        mock_discordbot_installed,
        mock_discordnotify_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user
        mock_discordbot_installed.return_value = False
        mock_discordnotify_installed.return_value = True

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()
