"""Tests for trogocytosis browser module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest


def test_import():
    """Package imports without error."""
    import trogocytosis
    assert trogocytosis.__version__ == "0.1.0"


def test_agent_browser_wrapper_navigate():
    """_agent_browser.run calls subprocess with correct args."""
    from trogocytosis._agent_browser import run

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Page loaded", stderr="", returncode=0
        )
        ok, output = run(["open", "https://example.com"])
        assert ok is True
        assert "Page loaded" in output
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "agent-browser" in args[0]
        assert args[1:] == ["open", "https://example.com"]


def test_agent_browser_wrapper_failure():
    """_agent_browser.run handles subprocess failure."""
    from trogocytosis._agent_browser import run

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "agent-browser")
        ok, output = run(["open", "https://example.com"])
        assert ok is False


def test_navigate_returns_title_and_url():
    """browser.navigate returns structured result."""
    from trogocytosis.browser import navigate

    with patch("trogocytosis._agent_browser.run") as mock_run:
        mock_run.side_effect = [
            (True, ""),  # open
            (True, "Example Domain"),  # get title
            (True, "https://example.com/"),  # get url
        ]
        result = navigate("https://example.com")
        assert result["title"] == "Example Domain"
        assert result["url"] == "https://example.com/"


def test_snapshot_returns_aria_tree():
    """browser.snapshot returns accessibility tree text."""
    from trogocytosis.browser import snapshot

    aria = '- link "Hello" [ref=e1]'
    with patch("trogocytosis._agent_browser.run") as mock_run:
        mock_run.return_value = (True, aria)
        result = snapshot()
        assert result["snapshot"] == aria


def test_click_calls_agent_browser():
    """browser.click dispatches correct CLI command."""
    from trogocytosis.browser import click

    with patch("trogocytosis._agent_browser.run") as mock_run:
        mock_run.return_value = (True, "clicked")
        result = click("#submit")
        assert result["success"] is True
        mock_run.assert_called_once_with(["click", "#submit"])


def test_fill_clears_then_types():
    """browser.fill clears field then types value."""
    from trogocytosis.browser import fill

    with patch("trogocytosis._agent_browser.run") as mock_run:
        mock_run.return_value = (True, "")
        result = fill("#email", "test@example.com")
        assert result["success"] is True
        calls = mock_run.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == ["fill", "#email", ""]  # clear
        assert calls[1][0][0] == ["fill", "#email", "test@example.com"]  # type


def test_eval_returns_result():
    """browser.evaluate returns JS evaluation result."""
    from trogocytosis.browser import evaluate

    with patch("trogocytosis._agent_browser.run") as mock_run:
        mock_run.return_value = (True, "42")
        result = evaluate("1 + 41")
        assert result["result"] == "42"


def test_inject_cookies_extracts_and_injects():
    """cookies.inject extracts from Chrome and injects into agent-browser."""
    from trogocytosis.cookies import inject

    mock_cookies = {"session_id": "abc123", "csrf": "xyz"}

    with (
        patch("trogocytosis.cookies._extract_cookies") as mock_extract,
        patch("trogocytosis._agent_browser.run") as mock_run,
    ):
        mock_extract.return_value = mock_cookies
        mock_run.return_value = (True, "")
        result = inject("example.com")
        assert result["count"] == 2
        assert result["domain"] == "example.com"
        assert mock_run.call_count == 3  # navigate + 2 cookie sets


def test_stealth_patches_generate_valid_js():
    """stealth.patches returns executable JavaScript strings."""
    from trogocytosis.stealth import patches

    js_list = patches()
    assert isinstance(js_list, list)
    assert len(js_list) > 0
    for js in js_list:
        assert isinstance(js, str)
        assert len(js) > 10


def test_stealth_random_ua():
    """stealth.random_ua returns a Chrome user-agent string."""
    from trogocytosis.stealth import random_ua

    ua = random_ua()
    assert "Chrome" in ua
    assert "Mozilla" in ua
