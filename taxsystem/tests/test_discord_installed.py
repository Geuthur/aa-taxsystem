# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase, modify_settings

# AA TaxSystem
from taxsystem.helpers.discord import (
    _discordbot_send_direct_message,
    _discordproxy_send_direct_message,
    allianceauth_discordbot_installed,
    discordnotify_installed,
    discordproxy_installed,
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

    @patch("aadiscordbot.tasks.send_message")
    @patch("discordproxy.client.DiscordClient.create_direct_message")
    def test_send_direct_message_with_both_modules_installed_should_use_discordproxy(
        self, mock_create_direct_message, mock_send_message
    ):
        with patch(
            "taxsystem.helpers.discord.discordproxy_installed", return_value=True
        ):
            _discordproxy_send_direct_message(
                user_id=123456789,
                title="Test Message",
                message="This is a test message.",
                embed_message=True,
                level="info",
            )

        mock_create_direct_message.assert_called_once()
        mock_send_message.assert_not_called()

    @patch("aadiscordbot.tasks.send_message")
    @patch("discordproxy.client.DiscordClient.create_direct_message")
    def test_send_direct_message_with_only_aadiscordbot_installed_should_use_aadiscordbot(
        self, mock_create_direct_message, mock_send_message
    ):
        with patch(
            "taxsystem.helpers.discord.discordproxy_installed", return_value=False
        ):
            _discordbot_send_direct_message(
                user_id=123456789,
                title="Test Message",
                message="This is a test message.",
                embed_message=True,
                level="info",
            )

        mock_send_message.assert_called_once()
        mock_create_direct_message.assert_not_called()
