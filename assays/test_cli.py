"""Tests for trogocytosis CLI."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from trogocytosis.cli import app, main


@pytest.fixture
def mock_browser():
    """Mock the browser module."""
    with patch("trogocytosis.cli.browser") as mock:
        yield mock


@pytest.fixture
def mock_cookies():
    """Mock the cookies module."""
    with patch("trogocytosis.cli.cookies") as mock:
        yield mock


@pytest.fixture
def mock_stealth():
    """Mock the stealth module."""
    with patch("trogocytosis.cli.stealth") as mock:
        yield mock


def test_navigate_command(capsys, mock_browser):
    """Test navigate command."""
    mock_browser.navigate.return_value = {"title": "Test Page", "url": "https://example.com"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["navigate", "https://example.com"])
    
    assert exc_info.value.code == 0
    mock_browser.navigate.assert_called_once_with("https://example.com")
    captured = capsys.readouterr()
    assert "Test Page" in captured.out
    assert "https://example.com" in captured.out


def test_navigate_json_output(capsys, mock_browser):
    """Test navigate command with json output."""
    expected = {"title": "Test Page", "url": "https://example.com"}
    mock_browser.navigate.return_value = expected
    
    with pytest.raises(SystemExit) as exc_info:
        app(["navigate", "https://example.com", "--json-output"])
    
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out.strip()) == expected


def test_snapshot_command(capsys, mock_browser):
    """Test snapshot command."""
    mock_browser.snapshot.return_value = {"snapshot": "test snapshot content"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["snapshot"])
    
    assert exc_info.value.code == 0
    mock_browser.snapshot.assert_called_once()
    captured = capsys.readouterr()
    assert "test snapshot content" in captured.out


def test_screenshot_command(capsys, mock_browser):
    """Test screenshot command."""
    mock_browser.screenshot.return_value = {"size_bytes": 12345, "path": "/tmp/screenshot.png"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["screenshot"])
    
    assert exc_info.value.code == 0
    mock_browser.screenshot.assert_called_once_with("/tmp/screenshot.png", "")
    captured = capsys.readouterr()
    assert "12345 bytes" in captured.out
    assert "/tmp/screenshot.png" in captured.out


def test_click_command_success(capsys, mock_browser):
    """Test click command with successful result."""
    mock_browser.click.return_value = {"success": True}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["click", "#submit"])
    
    assert exc_info.value.code == 0
    mock_browser.click.assert_called_once_with("#submit")


def test_click_command_failure(mock_browser):
    """Test click command with failed result exits with code 1."""
    mock_browser.click.return_value = {"success": False}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["click", "#submit"])
    
    assert exc_info.value.code == 1


def test_fill_command_success(capsys, mock_browser):
    """Test fill command with successful result."""
    mock_browser.fill.return_value = {"success": True}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["fill", "#username", "testuser"])
    
    assert exc_info.value.code == 0
    mock_browser.fill.assert_called_once_with("#username", "testuser")


def test_fill_command_failure(mock_browser):
    """Test fill command with failed result exits with code 1."""
    mock_browser.fill.return_value = {"success": False}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["fill", "#username", "testuser"])
    
    assert exc_info.value.code == 1


def test_eval_command(capsys, mock_browser):
    """Test eval command."""
    mock_browser.evaluate.return_value = {"result": "42"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["eval", "document.title"])
    
    assert exc_info.value.code == 0
    mock_browser.evaluate.assert_called_once_with("document.title")
    captured = capsys.readouterr()
    assert captured.out.strip() == "42"


def test_inject_cookies_command(capsys, mock_cookies):
    """Test inject-cookies command."""
    mock_cookies.inject.return_value = {"count": 5, "domain": "example.com"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["inject-cookies", "example.com", "--browser-name", "firefox"])
    
    assert exc_info.value.code == 0
    mock_cookies.inject.assert_called_once_with("example.com", "firefox")
    captured = capsys.readouterr()
    assert "Injected 5 cookies for example.com" in captured.out


def test_check_auth_command_authenticated(capsys, mock_browser):
    """Test check-auth command when authenticated."""
    mock_browser.check_auth.return_value = {"authenticated": True, "url": "https://example.com"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["check-auth"])
    
    assert exc_info.value.code == 0
    mock_browser.check_auth.assert_called_once()
    captured = capsys.readouterr()
    assert "authenticated: https://example.com" in captured.out


def test_check_auth_command_required(capsys, mock_browser):
    """Test check-auth command when auth is required."""
    mock_browser.check_auth.return_value = {"authenticated": False, "url": "https://example.com/login"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["check-auth"])
    
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "auth required: https://example.com/login" in captured.out


def test_login_command_success(capsys, mock_cookies):
    """Test login command with successful result."""
    mock_cookies.login_headed.return_value = {
        "success": True, 
        "auto_filled": True, 
        "url": "https://example.com/dashboard"
    }
    
    with pytest.raises(SystemExit) as exc_info:
        app(["login", "example.com"])
    
    assert exc_info.value.code == 0
    mock_cookies.login_headed.assert_called_once_with("example.com", None)
    captured = capsys.readouterr()
    assert "Logged in to example.com" in captured.out
    assert "(auto-filled from 1Password)" in captured.out
    assert "https://example.com/dashboard" in captured.out


def test_login_command_failure(mock_cookies):
    """Test login command with failed result exits with code 1."""
    mock_cookies.login_headed.return_value = {"success": False, "error": "user canceled"}
    
    with pytest.raises(SystemExit) as exc_info:
        app(["login", "example.com"])
    
    assert exc_info.value.code == 1


def test_apply_stealth_command(capsys, mock_browser, mock_stealth):
    """Test stealth command."""
    mock_stealth.patches.return_value = ["patch1.js", "patch2.js"]
    mock_stealth.random_ua.return_value = "Mozilla/5.0 Test UA"
    
    with pytest.raises(SystemExit) as exc_info:
        app(["stealth"])
    
    assert exc_info.value.code == 0
    assert mock_browser.evaluate.call_count == 2
    captured = capsys.readouterr()
    assert "Applied 2 patches" in captured.out
    assert "UA: Mozilla/5.0 Test UA" in captured.out


def test_serve_command():
    """Test serve command imports and runs mcp app."""
    # Use create=True because mcp_app only exists after import inside the function
    """Test main() calls app()."""
    with patch("trogocytosis.cli.app") as mock_app:
        main()
        mock_app.assert_called_once()
def test_serve_command():
    """Test serve command imports and runs mcp app."""
    # Patch the server module before it's imported by serve
    mock_app = MagicMock()
    with patch("trogocytosis.server.app", mock_app):
        with pytest.raises(SystemExit) as exc_info:
            app(["serve"])
        assert exc_info.value.code == 0
        mock_app.run.assert_called_once_with(transport="stdio")


def test_main_calls_app():
    """Test main() calls app()."""
    with patch("trogocytosis.cli.app") as mock_app:
        main()
        mock_app.assert_called_once()
