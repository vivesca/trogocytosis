"""Tests for _agent_browser module."""

import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from trogocytosis._agent_browser import _has_agent_browser, _run_cli, _ssh_prefix, run


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


class TestRunCli(unittest.TestCase):
    """Tests for _run_cli."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.run")
    def test_success_returns_true_and_stdout(self, mock_run):
        mock_run.return_value = MagicMock(stdout="  ok result  \n")
        ok, out = _run_cli(["navigate", "https://example.com"])
        self.assertTrue(ok)
        self.assertEqual(out, "ok result")
        mock_run.assert_called_once_with(
            ["agent-browser", "navigate", "https://example.com"],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )

    @patch.dict(os.environ, {"TROGOCYTOSIS_HOST": "mac"})
    @patch("subprocess.run")
    def test_ssh_host_prefixes_command(self, mock_run):
        mock_run.return_value = MagicMock(stdout="remote ok")
        ok, out = _run_cli(["snapshot"])
        self.assertTrue(ok)
        self.assertEqual(out, "remote ok")
        self.assertEqual(mock_run.call_args.args[0], ["ssh", "mac", "agent-browser", "snapshot"])

    @patch("subprocess.run")
    def test_called_process_error_returns_false_and_stderr(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["agent-browser"], stderr="  bad stuff  \n"
        )
        ok, out = _run_cli(["bad-arg"])
        self.assertFalse(ok)
        self.assertEqual(out, "bad stuff")

    @patch("subprocess.run")
    def test_called_process_error_no_stderr_returns_str_of_exc(self, mock_run):
        exc = subprocess.CalledProcessError(returncode=2, cmd=["agent-browser"])
        mock_run.side_effect = exc
        ok, out = _run_cli(["oops"])
        self.assertFalse(ok)
        self.assertIn("returned non-zero exit status 2", out)


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
