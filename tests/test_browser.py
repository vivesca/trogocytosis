"""Tests for trogocytosis browser module."""

from unittest.mock import MagicMock, patch


def _mock_proc(stdout="", stderr="", returncode=0):
    """Create a mock Popen process that behaves like a successful run."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    proc.pid = 99999
    return proc


def test_import():
    """Package imports without error."""
    import trogocytosis

    assert trogocytosis.__version__ == "0.9.0"


def test_agent_browser_wrapper_navigate():
    """_agent_browser.run calls Popen with --session trogocytosis when CLI available."""
    from trogocytosis._agent_browser import run

    with (
        patch("trogocytosis._agent_browser._has_agent_browser", return_value=True),
        patch("subprocess.Popen") as mock_popen,
    ):
        mock_popen.return_value = _mock_proc(stdout="Page loaded")
        ok, output = run(["open", "https://example.com"])
        assert ok is True
        assert "Page loaded" in output
        cmd = mock_popen.call_args[0][0]
        assert cmd == [
            "agent-browser",
            "--session", "trogocytosis",
            "open", "https://example.com",
        ]


def test_agent_browser_wrapper_failure():
    """_agent_browser.run handles non-zero returncode."""
    from trogocytosis._agent_browser import run

    with (
        patch("trogocytosis._agent_browser._has_agent_browser", return_value=True),
        patch("subprocess.Popen") as mock_popen,
    ):
        mock_popen.return_value = _mock_proc(stderr="error", returncode=1)
        ok, output = run(["open", "https://example.com"])
        assert ok is False


def test_remote_host_uses_ssh_prefix(monkeypatch):
    """Uses SSH transport when TROGOCYTOSIS_HOST is set."""
    from trogocytosis._agent_browser import run

    monkeypatch.setenv("TROGOCYTOSIS_HOST", "mac")
    with (
        patch("trogocytosis._agent_browser._has_agent_browser", return_value=False),
        patch("subprocess.Popen") as mock_popen,
    ):
        mock_popen.return_value = _mock_proc(stdout="remote result")
        ok, output = run(["open", "https://example.com"])
        assert ok is True
        assert output == "remote result"
        assert mock_popen.call_args[0][0] == [
            "ssh", "mac",
            "agent-browser",
            "--session", "trogocytosis",
            "open", "https://example.com",
        ]


def test_no_backend_error(monkeypatch):
    """Returns helpful error when neither local nor remote CLI is available."""
    from trogocytosis._agent_browser import run

    monkeypatch.delenv("TROGOCYTOSIS_HOST", raising=False)
    with patch("trogocytosis._agent_browser._has_agent_browser", return_value=False):
        ok, output = run(["open", "https://example.com"])
        assert ok is False
        assert "agent-browser not found" in output
        assert "TROGOCYTOSIS_HOST" in output


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


def test_text_returns_body_dict():
    """browser.text returns dict with body text via get text body."""
    from trogocytosis.browser import text

    with patch("trogocytosis._agent_browser.run") as mock_run:
        mock_run.return_value = (True, "Hello World\nWelcome")
        result = text()
        assert result == {"text": "Hello World\nWelcome"}
        mock_run.assert_called_once_with(["get", "text", "body"])


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


def test_install_skills_to_custom_path(tmp_path):
    """install_skills copies SKILL.md files to the target directory."""
    from trogocytosis.install import install_skills

    installed = install_skills(tmp_path, force=True)
    assert len(installed) >= 4
    assert "auth-wall-recovery" in installed
    assert "browser-extraction" in installed
    assert "browser-stealth" in installed
    assert "browser-session" in installed

    # Verify files actually exist with proper frontmatter
    for name in installed:
        skill_file = tmp_path / name / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert content.startswith("---\n")
        assert f"name: {name}" in content
