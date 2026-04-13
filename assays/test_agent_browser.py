"""Tests for _agent_browser module."""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from trogocytosis._agent_browser import _has_agent_browser, _has_playwright, _run_cli, run


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


class TestHasPlaywright(unittest.TestCase):
    """Tests for _has_playwright."""

    @patch("trogocytosis._agent_browser.importlib.util.find_spec")
    def test_returns_true_when_found(self, mock_find):
        mock_find.return_value = MagicMock()
        self.assertTrue(_has_playwright())
        mock_find.assert_called_once_with("playwright")

    @patch("trogocytosis._agent_browser.importlib.util.find_spec")
    def test_returns_false_when_not_found(self, mock_find):
        mock_find.return_value = None
        self.assertFalse(_has_playwright())
        mock_find.assert_called_once_with("playwright")


class TestRunCli(unittest.TestCase):
    """Tests for _run_cli."""

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
        # stderr is None, so it falls back to str(exc)
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

    @patch("trogocytosis._agent_browser._has_agent_browser", return_value=False)
    @patch("trogocytosis._agent_browser._has_playwright", return_value=True)
    @patch("trogocytosis._playwright.run", return_value=(True, "pw-result"))
    def test_falls_back_to_playwright(self, mock_pw_run, mock_has_pw, mock_has_ab):
        ok, out = run(["goto", "https://x.com"])
        self.assertTrue(ok)
        self.assertEqual(out, "pw-result")
        mock_pw_run.assert_called_once_with(["goto", "https://x.com"])

    @patch("trogocytosis._agent_browser._has_agent_browser", return_value=False)
    @patch("trogocytosis._agent_browser._has_playwright", return_value=False)
    def test_returns_error_when_no_backend(self, mock_has_pw, mock_has_ab):
        ok, out = run(["anything"])
        self.assertFalse(ok)
        self.assertIn("No browser backend found", out)
        self.assertIn("agent-browser", out)
        self.assertIn("playwright", out)


if __name__ == "__main__":
    unittest.main()
