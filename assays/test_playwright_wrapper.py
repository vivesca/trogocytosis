"""Tests for _playwright module."""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from trogocytosis._playwright import (
    _dispatch,
    _ensure_browser,
    _format_tree,
    run,
)


def _inject_mock_playwright(mock_sync_playwright: MagicMock) -> None:
    """Inject a fake 'playwright.sync_api' into sys.modules so that
    ``from playwright.sync_api import sync_playwright`` resolves to *mock_sync_playwright*.
    """
    fake_pw = types.ModuleType("playwright")
    fake_pw.__path__ = []  # make it look like a package
    fake_sync_api = types.ModuleType("playwright.sync_api")
    fake_sync_api.sync_playwright = mock_sync_playwright
    sys.modules["playwright"] = fake_pw
    sys.modules["playwright.sync_api"] = fake_sync_api


def _remove_mock_playwright() -> None:
    """Remove injected fake playwright modules from sys.modules."""
    sys.modules.pop("playwright", None)
    sys.modules.pop("playwright.sync_api", None)


class TestEnsureBrowser(unittest.TestCase):
    """Tests for _ensure_browser (lazy launch)."""

    def setUp(self):
        """Reset module-level globals before each test."""
        import trogocytosis._playwright as mod

        mod._browser = None
        mod._context = None
        mod._page = None
        if hasattr(mod, "sync_playwright"):
            delattr(mod, "sync_playwright")

    def tearDown(self):
        _remove_mock_playwright()

    @patch.dict(
        "os.environ",
        {"TROGOCYTOSIS_PROFILE": "/tmp/trogo-test-profile"},
    )
    def test_launches_browser_and_returns_page(self):
        mock_pw_cls = MagicMock()
        mock_pw = MagicMock()
        mock_pw_cls.return_value = mock_pw
        mock_pw.start.return_value = mock_pw

        mock_ctx = MagicMock()
        mock_pw.chromium.launch_persistent_context.return_value = mock_ctx
        mock_page = MagicMock()
        mock_ctx.pages = [mock_page]

        _inject_mock_playwright(mock_pw_cls)
        page = _ensure_browser()
        self.assertIs(page, mock_page)
        mock_pw.chromium.launch_persistent_context.assert_called_once_with(
            "/tmp/trogo-test-profile",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

    def test_returns_existing_page_without_relaunching(self):
        mock_page = MagicMock()
        import trogocytosis._playwright as mod

        mod._page = mock_page

        page = _ensure_browser()
        self.assertIs(page, mock_page)

    def test_creates_new_page_when_pages_empty(self):
        mock_pw_cls = MagicMock()
        mock_pw = MagicMock()
        mock_pw_cls.return_value = mock_pw
        mock_pw.start.return_value = mock_pw

        mock_ctx = MagicMock()
        mock_pw.chromium.launch_persistent_context.return_value = mock_ctx
        mock_ctx.pages = []
        mock_new_page = MagicMock()
        mock_ctx.new_page.return_value = mock_new_page

        _inject_mock_playwright(mock_pw_cls)
        page = _ensure_browser()
        self.assertIs(page, mock_new_page)
        mock_ctx.new_page.assert_called_once()


class TestRun(unittest.TestCase):
    """Tests for the run entry point."""

    @patch("trogocytosis._playwright._dispatch", return_value=(True, "ok"))
    @patch("trogocytosis._playwright._ensure_browser")
    def test_success_returns_dispatch_result(self, mock_ensure, mock_dispatch):
        ok, out = run(["open", "https://example.com"])
        self.assertTrue(ok)
        self.assertEqual(out, "ok")

    @patch("trogocytosis._playwright._ensure_browser", side_effect=RuntimeError("boom"))
    def test_exception_returns_false_and_message(self, mock_ensure):
        ok, out = run(["open", "https://example.com"])
        self.assertFalse(ok)
        self.assertIn("boom", out)


class TestDispatch(unittest.TestCase):
    """Tests for _dispatch command routing."""

    def tearDown(self):
        _remove_mock_playwright()

    # --- open (navigate) ---
    def test_open_navigates_and_returns_true(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["open", "https://example.com"])
        self.assertTrue(ok)
        self.assertEqual(out, "")
        page.goto.assert_called_once_with(
            "https://example.com", wait_until="domcontentloaded", timeout=30000
        )

    # --- get ---
    def test_get_title(self):
        page = MagicMock()
        page.title.return_value = "My Page"
        ok, out = _dispatch(page, ["get", "title"])
        self.assertTrue(ok)
        self.assertEqual(out, "My Page")

    def test_get_url(self):
        page = MagicMock()
        page.url = "https://example.com"
        ok, out = _dispatch(page, ["get", "url"])
        self.assertTrue(ok)
        self.assertEqual(out, "https://example.com")

    def test_get_unknown_property(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["get", "foo"])
        self.assertFalse(ok)
        self.assertIn("Unknown property", out)

    # --- snapshot ---
    def test_snapshot_returns_formatted_tree(self):
        page = MagicMock()
        page.accessibility.snapshot.return_value = {
            "role": "root",
            "name": "",
            "children": [{"role": "button", "name": "Submit", "children": []}],
        }
        ok, out = _dispatch(page, ["snapshot"])
        self.assertTrue(ok)
        self.assertIn("root", out)
        self.assertIn("button", out)
        self.assertIn("Submit", out)

    def test_snapshot_returns_empty_when_none(self):
        page = MagicMock()
        page.accessibility.snapshot.return_value = None
        ok, out = _dispatch(page, ["snapshot"])
        self.assertTrue(ok)
        self.assertEqual(out, "")

    # --- screenshot ---
    def test_screenshot(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["screenshot", "/tmp/shot.png"])
        self.assertTrue(ok)
        self.assertEqual(out, "")
        page.screenshot.assert_called_once_with(path="/tmp/shot.png")

    # --- click ---
    def test_click(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["click", "#btn"])
        self.assertTrue(ok)
        self.assertEqual(out, "clicked")
        page.click.assert_called_once_with("#btn")

    # --- fill ---
    def test_fill(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["fill", "#input", "hello"])
        self.assertTrue(ok)
        self.assertEqual(out, "")
        page.fill.assert_called_once_with("#input", "hello")

    # --- eval ---
    def test_eval_returns_stringified_result(self):
        page = MagicMock()
        page.evaluate.return_value = 42
        ok, out = _dispatch(page, ["eval", "1+1"])
        self.assertTrue(ok)
        self.assertEqual(out, "42")
        page.evaluate.assert_called_once_with("1+1")

    def test_eval_returns_empty_for_none(self):
        page = MagicMock()
        page.evaluate.return_value = None
        ok, out = _dispatch(page, ["eval", "void(0)"])
        self.assertTrue(ok)
        self.assertEqual(out, "")

    # --- cookies set ---
    def test_cookies_set_basic(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["cookies", "set", "sid", "abc123"])
        self.assertTrue(ok)
        self.assertEqual(out, "")
        page.context.add_cookies.assert_called_once_with(
            [{"name": "sid", "value": "abc123"}]
        )

    def test_cookies_set_with_flags(self):
        page = MagicMock()
        ok, out = _dispatch(
            page,
            [
                "cookies",
                "set",
                "sid",
                "abc",
                "--domain",
                ".example.com",
                "--path",
                "/",
                "--httpOnly",
                "--secure",
            ],
        )
        self.assertTrue(ok)
        page.context.add_cookies.assert_called_once_with(
            [
                {
                    "name": "sid",
                    "value": "abc",
                    "domain": ".example.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                }
            ]
        )

    def test_cookies_set_with_url_flag(self):
        page = MagicMock()
        ok, out = _dispatch(
            page, ["cookies", "set", "tok", "x", "--url", "https://example.com"]
        )
        self.assertTrue(ok)
        page.context.add_cookies.assert_called_once_with(
            [{"name": "tok", "value": "x", "url": "https://example.com"}]
        )

    # --- set ---
    def test_set_viewport(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["set", "viewport", "1280", "720"])
        self.assertTrue(ok)
        self.assertEqual(out, "")
        page.set_viewport_size.assert_called_once_with({"width": 1280, "height": 720})

    def test_set_device_known(self):
        page = MagicMock()
        mock_pw_cls = MagicMock()
        mock_pw = MagicMock()
        mock_pw_cls.return_value = mock_pw
        mock_pw.start.return_value = mock_pw
        mock_pw.devices = {"iPhone 12": {"viewport": {"width": 390, "height": 844}}}

        _inject_mock_playwright(mock_pw_cls)
        ok, out = _dispatch(page, ["set", "device", "iPhone 12"])
        self.assertTrue(ok)
        self.assertEqual(out, "")
        page.set_viewport_size.assert_called_once_with({"width": 390, "height": 844})

    def test_set_device_unknown_still_succeeds(self):
        page = MagicMock()
        mock_pw_cls = MagicMock()
        mock_pw = MagicMock()
        mock_pw_cls.return_value = mock_pw
        mock_pw.start.return_value = mock_pw
        mock_pw.devices = {}

        _inject_mock_playwright(mock_pw_cls)
        ok, out = _dispatch(page, ["set", "device", "FakePhone"])
        self.assertTrue(ok)
        page.set_viewport_size.assert_not_called()

    def test_set_unknown_subcommand(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["set", "unknown"])
        self.assertFalse(ok)
        self.assertIn("Unknown set command", out)

    # --- error / unknown ---
    def test_no_args_returns_error(self):
        page = MagicMock()
        ok, out = _dispatch(page, [])
        self.assertFalse(ok)
        self.assertIn("No command specified", out)

    def test_unknown_command(self):
        page = MagicMock()
        ok, out = _dispatch(page, ["fly"])
        self.assertFalse(ok)
        self.assertIn("Unknown command", out)


class TestFormatTree(unittest.TestCase):
    """Tests for _format_tree helper."""

    def test_formats_nested_tree(self):
        tree = {
            "role": "root",
            "name": "",
            "children": [
                {
                    "role": "heading",
                    "name": "Welcome",
                    "children": [],
                },
                {
                    "role": "link",
                    "name": "Click",
                    "children": [],
                },
            ],
        }
        result = _format_tree(tree)
        self.assertIn('- root', result)
        self.assertIn('  - heading "Welcome"', result)
        self.assertIn('  - link "Click"', result)

    def test_none_returns_empty(self):
        self.assertEqual(_format_tree(None), "")

    def test_empty_dict(self):
        # {} is falsy, so _format_tree treats it like None
        self.assertEqual(_format_tree({}), "")


if __name__ == "__main__":
    unittest.main()
