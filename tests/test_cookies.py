"""Tests for cookie extraction and injection."""

from unittest.mock import MagicMock, patch
import json


def test_extract_cookies_bridge_first():
    """Remote bridge is tried before local pycookiecheat."""
    from trogocytosis.cookies import _extract_cookies

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"SID": "abc123"}).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
        result = _extract_cookies("github.com")

    assert result == {"SID": "abc123"}
    mock_url.assert_called_once()
    assert "mac:7743" in mock_url.call_args[0][0]


def test_extract_cookies_falls_back_to_pycookiecheat():
    """Falls back to pycookiecheat when bridge is unreachable."""
    from trogocytosis.cookies import _extract_cookies

    with patch("urllib.request.urlopen", side_effect=ConnectionError("unreachable")):
        with patch("pycookiecheat.chrome_cookies", return_value={"NID": "xyz"}) as mock_cc:
            result = _extract_cookies("github.com")

    assert result == {"NID": "xyz"}
    mock_cc.assert_called_once_with("https://github.com/")


def test_extract_cookies_returns_empty_when_both_fail():
    """Returns empty dict when both bridge and pycookiecheat fail."""
    from trogocytosis.cookies import _extract_cookies

    with patch("urllib.request.urlopen", side_effect=ConnectionError):
        with patch.dict("sys.modules", {"pycookiecheat": None}):
            result = _extract_cookies("example.com")

    assert result == {}


def test_inject_host_cookie_no_domain_flag():
    """__Host- cookies are injected without --domain flag."""
    from trogocytosis.cookies import inject

    cookies = {"__Host-session": "abc", "SID": "xyz"}

    with patch("trogocytosis.cookies._extract_cookies", return_value=cookies):
        with patch("trogocytosis._agent_browser.run", return_value=(True, "")) as mock_run:
            result = inject("github.com")

    assert result["success"] is True
    assert result["count"] == 2

    # Check that __Host- cookie was set WITHOUT --domain
    calls = mock_run.call_args_list
    host_call = [c for c in calls if "__Host-session" in c[0][0]]
    assert len(host_call) == 1
    assert "--domain" not in host_call[0][0][0]

    # Check that regular cookie was set WITH --domain
    sid_call = [c for c in calls if "SID" in c[0][0]]
    assert len(sid_call) == 1
    assert "--domain" in sid_call[0][0][0]


def test_inject_returns_failure_on_empty_cookies():
    """inject() returns failure when no cookies found."""
    from trogocytosis.cookies import inject

    with patch("trogocytosis.cookies._extract_cookies", return_value={}):
        result = inject("example.com")

    assert result["success"] is False
    assert result["count"] == 0


def test_inject_strips_protocol():
    """inject() normalises URLs with protocol prefix."""
    from trogocytosis.cookies import inject

    with patch("trogocytosis.cookies._extract_cookies", return_value={"a": "b"}) as mock_extract:
        with patch("trogocytosis._agent_browser.run", return_value=(True, "")):
            inject("https://github.com/")

    mock_extract.assert_called_once_with("github.com", "mac:7743")


def test_inject_tracks_failures():
    """inject() tracks which cookies failed to inject."""
    from trogocytosis.cookies import inject

    cookies = {"good": "1", "bad": "2"}

    def mock_run(args):
        if "bad" in args:
            return False, "error"
        return True, ""

    with patch("trogocytosis.cookies._extract_cookies", return_value=cookies):
        with patch("trogocytosis._agent_browser.run", side_effect=mock_run):
            result = inject("example.com")

    assert result["count"] == 1
    assert "bad" in result["failures"]


def test_inject_custom_bridge_host():
    """inject() passes custom bridge_host to _extract_cookies."""
    from trogocytosis.cookies import inject

    with patch("trogocytosis.cookies._extract_cookies", return_value={}) as mock_extract:
        inject("github.com", bridge_host="myhost:8080")

    mock_extract.assert_called_once_with("github.com", "myhost:8080")
