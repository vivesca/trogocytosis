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
    from pycookiecheat import BrowserType

    from trogocytosis.cookies import _extract_cookies

    with patch("urllib.request.urlopen", side_effect=ConnectionError("unreachable")):
        with patch("pycookiecheat.chrome_cookies", return_value={"NID": "xyz"}) as mock_cc:
            result = _extract_cookies("github.com")

    assert result == {"NID": "xyz"}
    mock_cc.assert_called_once_with("https://github.com/", browser=BrowserType.CHROME)


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

    mock_extract.assert_called_once_with("github.com", "mac:7743", "chrome")


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

    mock_extract.assert_called_once_with("github.com", "myhost:8080", "chrome")


def test_op_lookup_uses_remote_host(monkeypatch):
    """1Password lookup runs on TROGOCYTOSIS_HOST when set."""
    from trogocytosis.cookies import _op_lookup

    monkeypatch.setenv("TROGOCYTOSIS_HOST", "mac")
    items = [{"id": "item-1", "urls": [{"href": "https://linkedin.com/login"}]}]

    def mock_run(args, **kwargs):
        if args == ["ssh", "mac", "command", "-v", "op"]:
            return MagicMock(returncode=0, stdout="/usr/bin/op\n", stderr="")
        if args == ["ssh", "mac", "op", "item", "list", "--vault", "Agents", "--format=json"]:
            return MagicMock(returncode=0, stdout=json.dumps(items), stderr="")
        if "--fields" in args:
            field = args[args.index("--fields") + 1]
            value = "terry@example.com" if field == "username" else "secret"
            return MagicMock(returncode=0, stdout=value, stderr="")
        raise AssertionError(args)

    with patch("subprocess.run", side_effect=mock_run) as run:
        result = _op_lookup("linkedin.com")

    assert result == {"username": "terry@example.com", "password": "secret"}
    assert all(call.args[0][:2] == ["ssh", "mac"] for call in run.call_args_list)


def test_inject_passes_browser_into_extract_cookies():
    """inject(..., browser='comet') threads the selection into _extract_cookies."""
    from trogocytosis.cookies import inject

    with patch("trogocytosis.cookies._extract_cookies", return_value={}) as mock_extract:
        inject("github.com", browser="comet")

    mock_extract.assert_called_once_with("github.com", "mac:7743", "comet")


def test_extract_cookies_default_browser_is_chrome():
    """Default browser selection is chrome and flows to pycookiecheat."""
    from pycookiecheat import BrowserType

    from trogocytosis.cookies import _extract_cookies

    with patch("urllib.request.urlopen", side_effect=ConnectionError):
        with patch("pycookiecheat.chrome_cookies", return_value={"NID": "x"}) as mock_cc:
            result = _extract_cookies("github.com")

    assert result == {"NID": "x"}
    mock_cc.assert_called_once_with("https://github.com/", browser=BrowserType.CHROME)


def test_extract_cookies_normalizes_browser_and_tries_comet_first():
    """An uppercase 'Comet' is normalized and the Comet extractor wins over fallbacks."""
    from trogocytosis import cookies

    with patch.object(cookies, "_extract_via_bridge", side_effect=ConnectionError):
        with patch.object(cookies, "_extract_via_comet", return_value={"k": "v"}) as mock_comet:
            with patch.object(cookies, "_extract_via_porta") as mock_porta:
                with patch.object(cookies, "_extract_via_pycookiecheat") as mock_pcc:
                    result = cookies._extract_cookies("github.com", "mac:7743", "Comet")

    assert result == {"k": "v"}
    mock_comet.assert_called_once_with("github.com")
    mock_porta.assert_not_called()
    mock_pcc.assert_not_called()


def test_macos_safe_storage_key_calls_expected_security_command():
    """The helper invokes the expected `security` command and strips stdout."""
    from trogocytosis.cookies import _macos_safe_storage_key

    mock_result = MagicMock(returncode=0, stdout="  secretkey\n", stderr="")
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        key = _macos_safe_storage_key("Comet Safe Storage", "Comet")

    assert key == "secretkey"
    mock_run.assert_called_once()
    call = mock_run.call_args
    assert call.args[0] == [
        "security",
        "find-generic-password",
        "-w",
        "-s",
        "Comet Safe Storage",
        "-a",
        "Comet",
    ]
    assert call.kwargs["capture_output"] is True
    assert call.kwargs["timeout"] == 5


def test_macos_safe_storage_key_failure_returns_none_without_leaking():
    """On failure the helper returns None and captures all output."""
    from trogocytosis.cookies import _macos_safe_storage_key

    mock_result = MagicMock(returncode=1, stdout="should-not-leak\n", stderr="noisy-err\n")
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        key = _macos_safe_storage_key("Comet Safe Storage", "Comet")

    assert key is None
    assert mock_run.call_args.kwargs["capture_output"] is True
