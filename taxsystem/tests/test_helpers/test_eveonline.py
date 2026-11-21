"""Tests for the eveonline helpers."""

# AA TaxSystem
from taxsystem.helpers.eveonline import (
    get_alliance_logo_url,
    get_character_portrait_url,
    get_corporation_logo_url,
    get_icon_render_url,
    get_type_render_url,
)
from taxsystem.tests import NoSocketsTestCase

IMAGE_SERVER = "https://images.evetech.net"


class TestGetCharacterPortraitUrl(NoSocketsTestCase):
    def test_should_return_url(self):
        result = get_character_portrait_url(1001, size=64)

        self.assertEqual(result, f"{IMAGE_SERVER}/characters/1001/portrait?size=64")

    def test_should_return_empty_string_for_invalid_size(self):
        result = get_character_portrait_url(1001, size=13)

        self.assertEqual(result, "")

    def test_should_return_html(self):
        result = get_character_portrait_url(
            1001, character_name="Bruce Wayne", as_html=True
        )

        self.assertHTMLEqual(
            result,
            '<img class="character-portrait rounded-circle" '
            f'src="{IMAGE_SERVER}/characters/1001/portrait?size=32" alt="Bruce Wayne">',
        )

    def test_should_return_html_with_display_name(self):
        result = get_character_portrait_url(
            1001, character_name="Bruce Wayne", as_html=True, display_name=True
        )

        self.assertHTMLEqual(
            result,
            '<div class="d-flex align-items-center">'
            '<img class="character-portrait rounded-circle me-2" '
            f'src="{IMAGE_SERVER}/characters/1001/portrait?size=32" alt="Bruce Wayne">'
            "<span>Bruce Wayne</span>"
            "</div>",
        )

    def test_should_ignore_display_name_without_html(self):
        result = get_character_portrait_url(
            1001, character_name="Bruce Wayne", display_name=True
        )

        self.assertEqual(result, f"{IMAGE_SERVER}/characters/1001/portrait?size=32")

    def test_should_escape_name(self):
        result = get_character_portrait_url(
            1001, character_name="<b>Bruce</b>", as_html=True, display_name=True
        )

        self.assertNotIn("<b>", result)
        self.assertIn("&lt;b&gt;Bruce&lt;/b&gt;", result)


class TestGetCorporationLogoUrl(NoSocketsTestCase):
    def test_should_return_url(self):
        result = get_corporation_logo_url(2001, size=64)

        self.assertEqual(result, f"{IMAGE_SERVER}/corporations/2001/logo?size=64")

    def test_should_return_html(self):
        result = get_corporation_logo_url(
            2001, corporation_name="Wayne Technologies", as_html=True
        )

        self.assertHTMLEqual(
            result,
            '<img class="corporation-logo rounded-circle" '
            f'src="{IMAGE_SERVER}/corporations/2001/logo?size=32" alt="Wayne Technologies">',
        )

    def test_should_return_html_with_display_name(self):
        result = get_corporation_logo_url(
            2001, corporation_name="Wayne Technologies", as_html=True, display_name=True
        )

        self.assertHTMLEqual(
            result,
            '<div class="d-flex align-items-center">'
            '<img class="corporation-logo rounded-circle me-2" '
            f'src="{IMAGE_SERVER}/corporations/2001/logo?size=32" alt="Wayne Technologies">'
            "<span>Wayne Technologies</span>"
            "</div>",
        )


class TestGetAllianceLogoUrl(NoSocketsTestCase):
    def test_should_return_url(self):
        result = get_alliance_logo_url(3001, size=64)

        self.assertEqual(result, f"{IMAGE_SERVER}/alliances/3001/logo?size=64")

    def test_should_return_html(self):
        result = get_alliance_logo_url(
            3001, alliance_name="Wayne Enterprises", as_html=True
        )

        self.assertHTMLEqual(
            result,
            '<img class="alliance-logo rounded-circle" '
            f'src="{IMAGE_SERVER}/alliances/3001/logo?size=32" alt="Wayne Enterprises">',
        )

    def test_should_return_html_with_display_name(self):
        result = get_alliance_logo_url(
            3001, alliance_name="Wayne Enterprises", as_html=True, display_name=True
        )

        self.assertHTMLEqual(
            result,
            '<div class="d-flex align-items-center">'
            '<img class="alliance-logo rounded-circle me-2" '
            f'src="{IMAGE_SERVER}/alliances/3001/logo?size=32" alt="Wayne Enterprises">'
            "<span>Wayne Enterprises</span>"
            "</div>",
        )


class TestGetTypeRenderUrl(NoSocketsTestCase):
    def test_should_return_url(self):
        result = get_type_render_url(603, size=64)

        self.assertEqual(result, f"{IMAGE_SERVER}/types/603/render?size=64")

    def test_should_return_html(self):
        result = get_type_render_url(603, type_name="Merlin", as_html=True)

        self.assertHTMLEqual(
            result,
            '<img class="type-render rounded-circle" '
            f'src="{IMAGE_SERVER}/types/603/render?size=32" alt="Merlin">',
        )

    def test_should_return_html_with_display_name(self):
        result = get_type_render_url(
            603, type_name="Merlin", as_html=True, display_name=True
        )

        self.assertHTMLEqual(
            result,
            '<div class="d-flex align-items-center">'
            '<img class="type-render rounded-circle me-2" '
            f'src="{IMAGE_SERVER}/types/603/render?size=32" alt="Merlin">'
            "<span>Merlin</span>"
            "</div>",
        )


class TestGetIconRenderUrl(NoSocketsTestCase):
    def test_should_return_url(self):
        result = get_icon_render_url(603, size=64)

        self.assertEqual(result, f"{IMAGE_SERVER}/types/603/icon?size=64")

    def test_should_return_html(self):
        result = get_icon_render_url(603, type_name="Merlin", as_html=True)

        self.assertHTMLEqual(
            result,
            '<img class="type-render rounded-circle" data-bs-tooltip="aa-taxsystem" '
            f'src="{IMAGE_SERVER}/types/603/icon?size=32" title="Merlin">',
        )

    def test_should_return_html_with_display_name(self):
        result = get_icon_render_url(
            603, type_name="Merlin", as_html=True, display_name=True
        )

        self.assertHTMLEqual(
            result,
            '<div class="d-flex align-items-center">'
            '<img class="type-render rounded-circle me-2" data-bs-tooltip="aa-taxsystem" '
            f'src="{IMAGE_SERVER}/types/603/icon?size=32" title="Merlin">'
            "<span>Merlin</span>"
            "</div>",
        )
