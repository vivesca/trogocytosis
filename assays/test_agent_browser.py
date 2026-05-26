"""Tests for _agent_browser module."""

import os
import signal
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from trogocytosis._agent_browser import (
    _DEFAULT_SESSION,
    _DEFAULT_TIMEOUT,
    _has_agent_browser,
    _parse_timeout,
    _run_cli,
    _session_name,
    _ssh_prefix,
    run,
)


def _mock_proc(stdout="", stderr="", returncode=0):
    """Create a mock Popen process that behaves like a successful run."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    proc.pid = 99999
    return proc


class TestSshPrefix(unittest.TestCase):
    """Tests for SSH transport selection."""

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_empty_without_host(self):
        self.assertEqual(_ssh_prefix(), [])

    @patch.dict(os.environ, {"TROGOCYTOSIS_HOST": "mac"})
    def test_returns_ssh_prefix_with_host(self):
        self.assertEqual(_ssh_prefix(), ["ssh", "mac"])


class TestHasAgentBrowser(unittest.TestCase):
    """Tests for _has_agent_browser."""

    @patch("trogocytosis._agent_browser.shutil.which")
    def test_returns_true_when_found(self, mock_which):
        mock_which.return_value = "/usr/local/bin/agent-browser"
        self.assertTrue(_has_agent_browser())
        mock_which.assert_called_once_with("agent-browser")

    @patch("trogocytosis._agent_browser.shutil.which")
    def test_returns_false_when_not_found(self, mock_which):
        mock_which.return_value = None
        self.assertFalse(_has_agent_browser())
        mock_which.assert_called_once_with("agent-browser")


class TestParseTimeout(unittest.TestCase):
    """Tests for _parse_timeout."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_when_unset(self):
        self.assertEqual(_parse_timeout(), _DEFAULT_TIMEOUT)

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": "120"})
    def test_valid_override(self):
        self.assertEqual(_parse_timeout(), 120)

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": "0"})
    def test_zero_falls_back(self):
        self.assertEqual(_parse_timeout(), _DEFAULT_TIMEOUT)

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": "-5"})
    def test_negative_falls_back(self):
        self.assertEqual(_parse_timeout(), _DEFAULT_TIMEOUT)

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": "abc"})
    def test_non_numeric_falls_back(self):
        self.assertEqual(_parse_timeout(), _DEFAULT_TIMEOUT)

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": ""})
    def test_empty_falls_back(self):
        self.assertEqual(_parse_timeout(), _DEFAULT_TIMEOUT)

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": "  "})
    def test_whitespace_falls_back(self):
        self.assertEqual(_parse_timeout(), _DEFAULT_TIMEOUT)


class TestSessionName(unittest.TestCase):
    """Tests for _session_name."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_when_unset(self):
        self.assertEqual(_session_name(), _DEFAULT_SESSION)

    @patch.dict(os.environ, {"TROGOCYTOSIS_SESSION": "custom-session"})
    def test_override(self):
        self.assertEqual(_session_name(), "custom-session")

    @patch.dict(os.environ, {"TROGOCYTOSIS_SESSION": ""})
    def test_empty_falls_back(self):
        self.assertEqual(_session_name(), _DEFAULT_SESSION)

    @patch.dict(os.environ, {"TROGOCYTOSIS_SESSION": "   "})
    def test_whitespace_falls_back(self):
        self.assertEqual(_session_name(), _DEFAULT_SESSION)


class TestRunCli(unittest.TestCase):
    """Tests for _run_cli."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen")
    def test_success_returns_true_and_stdout(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="  ok result  \n")
        ok, out = _run_cli(["navigate", "https://example.com"])
        self.assertTrue(ok)
        self.assertEqual(out, "ok result")
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            cmd,
            [
                "agent-browser",
                "--session",
                _DEFAULT_SESSION,
                "--headed",
                "false",
                "navigate",
                "https://example.com",
            ],
        )
        env = mock_popen.call_args[1]["env"]
        self.assertNotIn("AGENT_BROWSER_HEADED", env)

    @patch.dict(os.environ, {"TROGOCYTOSIS_HOST": "mac"})
    @patch("subprocess.Popen")
    def test_ssh_host_prefixes_command_with_session(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="remote ok")
        ok, out = _run_cli(["snapshot"])
        self.assertTrue(ok)
        self.assertEqual(out, "remote ok")
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            cmd,
            [
                "ssh",
                "mac",
                "agent-browser",
                "--session",
                _DEFAULT_SESSION,
                "--headed",
                "false",
                "snapshot",
            ],
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen")
    def test_nonzero_returncode_returns_false_and_stderr(self, mock_popen):
        mock_popen.return_value = _mock_proc(stderr="  bad stuff  \n", returncode=1)
        ok, out = _run_cli(["bad-arg"])
        self.assertFalse(ok)
        self.assertEqual(out, "bad stuff")

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen")
    def test_nonzero_returncode_no_stderr_returns_exit_code(self, mock_popen):
        mock_popen.return_value = _mock_proc(stderr="", returncode=2)
        ok, out = _run_cli(["oops"])
        self.assertFalse(ok)
        self.assertIn("exit code 2", out)

    @patch.dict(
        os.environ,
        {
            "AGENT_BROWSER_HEADED": "1",
            "AGENT_BROWSER_PROFILE": "/tmp/profile",
            "AGENT_BROWSER_EXTENSIONS": "/tmp/ext",
        },
        clear=True,
    )
    @patch("subprocess.Popen")
    def test_ambient_browser_env_stripped_for_normal_commands(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="ok")
        _run_cli(["snapshot"])
        env = mock_popen.call_args[1]["env"]
        self.assertNotIn("AGENT_BROWSER_HEADED", env)
        self.assertNotIn("AGENT_BROWSER_PROFILE", env)
        self.assertNotIn("AGENT_BROWSER_EXTENSIONS", env)
        cmd = mock_popen.call_args[0][0]
        self.assertIn("--headed", cmd)
        self.assertEqual(cmd[cmd.index("--headed") + 1], "false")

    @patch.dict(
        os.environ,
        {
            "AGENT_BROWSER_HEADED": "1",
            "AGENT_BROWSER_PROFILE": "/tmp/profile",
            "AGENT_BROWSER_EXTENSIONS": "/tmp/ext",
        },
        clear=True,
    )
    @patch("subprocess.Popen")
    def test_ambient_browser_env_preserved_for_headed_commands(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="ok")
        _run_cli(["open", "https://example.com", "--headed"])
        env = mock_popen.call_args[1]["env"]
        self.assertEqual(env["AGENT_BROWSER_HEADED"], "1")
        self.assertEqual(env["AGENT_BROWSER_PROFILE"], "/tmp/profile")
        self.assertEqual(env["AGENT_BROWSER_EXTENSIONS"], "/tmp/ext")
        cmd = mock_popen.call_args[0][0]
        self.assertNotIn("false", cmd[: cmd.index("open")])

    @patch.dict(os.environ, {"AGENT_BROWSER_HEADED": "1"}, clear=True)
    @patch("subprocess.Popen")
    def test_headed_equals_option_is_explicit(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="ok")
        _run_cli(["open", "https://example.com", "--headed=false"])
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            cmd,
            [
                "agent-browser",
                "--session",
                _DEFAULT_SESSION,
                "open",
                "https://example.com",
                "--headed=false",
            ],
        )

    @patch.dict(os.environ, {"TROGOCYTOSIS_SESSION": "my-session"}, clear=True)
    @patch("subprocess.Popen")
    def test_session_override(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="ok")
        _run_cli(["snapshot"])
        cmd = mock_popen.call_args[0][0]
        self.assertIn("--session", cmd)
        session_idx = cmd.index("--session")
        self.assertEqual(cmd[session_idx + 1], "my-session")

    @patch.dict(os.environ, {"TROGOCYTOSIS_TIMEOUT": "10"}, clear=True)
    @patch("subprocess.Popen")
    def test_timeout_override(self, mock_popen):
        mock_proc = _mock_proc(stdout="ok")
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
            cmd=[], timeout=10
        )
        mock_popen.return_value = mock_proc
        with patch("os.killpg"), patch("subprocess.run"):
            ok, out = _run_cli(["snapshot"])
        self.assertFalse(ok)
        self.assertIn("timed out after 10s", out)

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen")
    def test_timeout_kills_process_group(self, mock_popen):
        mock_proc = _mock_proc()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
            cmd=[], timeout=_DEFAULT_TIMEOUT
        )
        mock_popen.return_value = mock_proc
        with patch("os.killpg") as mock_killpg, patch("subprocess.run") as mock_run:
            ok, out = _run_cli(["snapshot"])
        self.assertFalse(ok)
        self.assertIn(f"timed out after {_DEFAULT_TIMEOUT}s", out)
        mock_killpg.assert_any_call(mock_proc.pid, signal.SIGTERM)
        # Close only the private session — never --all
        close_cmd = mock_run.call_args[0][0]
        self.assertEqual(
            close_cmd,
            ["agent-browser", "--session", _DEFAULT_SESSION, "close"],
        )
        self.assertNotIn("--all", close_cmd)

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen")
    def test_timeout_returns_clear_failure(self, mock_popen):
        mock_proc = _mock_proc()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
            cmd=[], timeout=_DEFAULT_TIMEOUT
        )
        mock_popen.return_value = mock_proc
        with patch("os.killpg"), patch("subprocess.run"):
            ok, out = _run_cli(["snapshot"])
        self.assertFalse(ok)
        self.assertEqual(out, f"agent-browser timed out after {_DEFAULT_TIMEOUT}s")

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen")
    def test_uses_start_new_session(self, mock_popen):
        mock_popen.return_value = _mock_proc(stdout="ok")
        _run_cli(["snapshot"])
        self.assertTrue(mock_popen.call_args[1]["start_new_session"])

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.Popen", side_effect=OSError("not found"))
    def test_oserror_returns_false(self, mock_popen):
        ok, out = _run_cli(["snapshot"])
        self.assertFalse(ok)
        self.assertEqual(out, "not found")


class TestRun(unittest.TestCase):
    """Tests for the run router."""

    @patch("trogocytosis._agent_browser._run_cli", return_value=(True, "ok"))
    @patch("trogocytosis._agent_browser._has_agent_browser", return_value=True)
    def test_prefers_agent_browser(self, mock_has, mock_cli):
        ok, out = run(["navigate", "https://x.com"])
        self.assertTrue(ok)
        self.assertEqual(out, "ok")
        mock_cli.assert_called_once_with(["navigate", "https://x.com"])

    @patch.dict(os.environ, {"TROGOCYTOSIS_HOST": "mac"})
    @patch("trogocytosis._agent_browser._run_cli", return_value=(True, "remote"))
    @patch("trogocytosis._agent_browser._has_agent_browser", return_value=False)
    def test_uses_remote_host_without_local_cli(self, mock_has, mock_cli):
        ok, out = run(["snapshot"])
        self.assertTrue(ok)
        self.assertEqual(out, "remote")
        mock_cli.assert_called_once_with(["snapshot"])

    @patch.dict(os.environ, {}, clear=True)
    @patch("trogocytosis._agent_browser._has_agent_browser", return_value=False)
    def test_returns_error_when_no_backend(self, mock_has):
        ok, out = run(["anything"])
        self.assertFalse(ok)
        self.assertIn("agent-browser not found", out)
        self.assertIn("TROGOCYTOSIS_HOST", out)


if __name__ == "__main__":
    unittest.main()
