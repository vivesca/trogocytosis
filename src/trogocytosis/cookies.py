"""Cookie extraction from host browser and injection into agent-browser."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

from trogocytosis import _agent_browser

DEFAULT_BRIDGE_HOST = os.environ.get("TROGOCYTOSIS_BRIDGE_HOST", "mac:7743")


def _normalize_domain(value: str) -> str:
    raw = value.strip()
    parsed = urlparse(raw)
    if parsed.scheme:
        host = parsed.netloc
    else:
        host = raw.split("/", 1)[0]
    return host.split("@")[-1].split(":", 1)[0]


def _bridge_url(bridge_host: str) -> str:
    legacy = os.environ.get("COOKIE_BRIDGE_URL", "").strip()
    if legacy:
        return legacy.rstrip("/")
    if bridge_host.startswith(("http://", "https://")):
        return bridge_host.rstrip("/")
    return f"http://{bridge_host.rstrip('/')}"


def _remote_host() -> str:
    return os.environ.get("TROGOCYTOSIS_HOST", "").strip()


def _host_command(*args: str) -> list[str]:
    host = _remote_host()
    return ["ssh", host, *args] if host else list(args)


def _command_available(command: str) -> bool:
    host = _remote_host()
    if not host:
        return shutil.which(command) is not None
    try:
        result = subprocess.run(
            ["ssh", host, "command", "-v", command],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _extract_via_bridge(domain: str, bridge_host: str) -> dict[str, str]:
    """Extract cookies via cookie-bridge HTTP service."""
    url = f"{_bridge_url(bridge_host)}/cookies?{urlencode({'domain': domain})}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        cookies = json.loads(resp.read())
        if not cookies:
            raise ValueError(f"Cookie bridge returned empty for {domain}")
        return cookies


def _extract_via_porta(domain: str, browser: str = "chrome") -> dict[str, str]:
    """Extract cookies via porta CLI."""
    if not shutil.which("porta"):
        raise FileNotFoundError("porta not installed")
    result = subprocess.run(
        ["porta", "inject", "--domain", domain, "--json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"porta failed: {result.stderr.strip()}")
    cookies = json.loads(result.stdout)
    if not cookies:
        raise ValueError(f"porta returned empty for {domain}")
    return cookies


def _extract_via_pycookiecheat(domain: str, browser: str = "chrome") -> dict[str, str]:
    """Extract cookies from host browser using pycookiecheat."""
    from pycookiecheat import BrowserType, chrome_cookies

    url = f"https://{domain}/"
    cookies = chrome_cookies(url, browser=BrowserType(browser))
    if not cookies:
        raise ValueError(f"pycookiecheat returned empty for {domain}")
    return cookies


def _macos_safe_storage_key(service: str, account: str) -> str | None:
    """Read a macOS Keychain generic password quietly via the security CLI.

    Returns the stripped password on success, or None on any failure.
    Output is captured, never printed.
    """
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-w",
                "-s",
                service,
                "-a",
                account,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _extract_via_comet(domain: str) -> dict[str, str]:
    """Extract cookies from the Comet browser on macOS (Chromium-based)."""
    from cryptography.hazmat.primitives.hashes import SHA1
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from pycookiecheat.chrome import chrome_decrypt
    from pycookiecheat.common import generate_host_keys

    cookie_file = Path.home() / "Library/Application Support/Comet/Default/Cookies"
    if not cookie_file.exists():
        raise FileNotFoundError(f"Comet cookie file not found: {cookie_file}")

    key_material = _macos_safe_storage_key("Comet Safe Storage", "Comet")
    if not key_material:
        raise ValueError("Comet Safe Storage key unavailable")

    kdf = PBKDF2HMAC(
        algorithm=SHA1(),
        iterations=1003,
        length=16,
        salt=b"saltysalt",
    )
    enc_key = kdf.derive(key_material.encode("utf8"))
    init_vector = b" " * 16

    cookies: dict[str, str] = {}
    conn = sqlite3.connect(f"file:{cookie_file}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        conn.text_factory = bytes
        version_row = conn.execute(
            "select value from meta where key = 'version';"
        ).fetchone()
        db_version = int(version_row[0]) if version_row else 0
        for host_key in generate_host_keys(domain):
            for row in conn.execute(
                "select name, value, encrypted_value from cookies where host_key like ?",
                (host_key,),
            ):
                name = row["name"]
                value = row["value"]
                encrypted = row["encrypted_value"]
                if not value and encrypted[:3] in (b"v10", b"v11"):
                    value = chrome_decrypt(
                        encrypted,
                        key=enc_key,
                        init_vector=init_vector,
                        cookie_database_version=db_version,
                    )
                if isinstance(name, bytes):
                    name = name.decode("utf8")
                if isinstance(value, bytes):
                    value = value.decode("utf8")
                cookies[name] = value
    finally:
        conn.close()

    if not cookies:
        raise ValueError(f"Comet returned empty for {domain}")
    return cookies


def _extract_cookies(
    domain: str,
    bridge_host: str = DEFAULT_BRIDGE_HOST,
    browser: str = "chrome",
) -> dict[str, str]:
    """Extract cookies by escalating through bridge, porta, then pycookiecheat."""
    browser = browser.lower()
    extractors: list[Any] = [
        lambda: _extract_via_bridge(domain, bridge_host),
    ]
    if browser == "comet":
        extractors.append(lambda: _extract_via_comet(domain))
    extractors.extend(
        [
            lambda: _extract_via_porta(domain, browser),
            lambda: _extract_via_pycookiecheat(domain, browser),
        ]
    )
    for extractor in extractors:
        try:
            return extractor()
        except Exception:
            continue
    return {}


def _inject_into_browser(domain: str, extracted: dict[str, str]) -> tuple[int, list[str]]:
    """Inject extracted cookies into agent-browser."""
    url = f"https://{domain}/"
    _agent_browser.run(["open", url])
    count = 0
    failures: list[str] = []
    for cookie_name, value in extracted.items():
        args = [
            "cookies",
            "set",
            cookie_name,
            value,
            "--url",
            url,
            "--path",
            "/",
            "--httpOnly",
            "--secure",
        ]
        if not cookie_name.startswith("__Host-"):
            args.extend(["--domain", f".{domain}"])

        ok, _ = _agent_browser.run(args)
        if ok:
            count += 1
        else:
            failures.append(cookie_name)
    return count, failures


def inject(
    domain: str,
    browser: str = "chrome",
    *,
    bridge_host: str = DEFAULT_BRIDGE_HOST,
) -> dict[str, Any]:
    """Extract cookies and inject them into agent-browser."""
    clean_domain = _normalize_domain(domain)
    extracted = _extract_cookies(clean_domain, bridge_host, browser)
    if not extracted:
        return {"success": False, "count": 0, "domain": clean_domain, "failures": []}
    count, failures = _inject_into_browser(clean_domain, extracted)
    return {
        "success": count > 0 and not failures,
        "count": count,
        "domain": clean_domain,
        "failures": failures,
    }


def login_headed(domain: str, login_url: str | None = None) -> dict[str, Any]:
    """Open headed browser for manual login, then persist session."""
    if login_url is None:
        login_url = f"https://{domain}/login"

    _agent_browser.run(["close"])
    time.sleep(1)

    creds = _op_lookup(domain)

    ok, _ = _agent_browser.run(["--headed", "open", login_url])
    if not ok:
        return {"success": False, "error": "Failed to open headed browser"}

    if creds:
        time.sleep(2)
        _agent_browser.run([
            "fill",
            "#username, [name=username], [name=email], [type=email]",
            creds["username"],
        ])
        _agent_browser.run([
            "fill",
            "#password, [name=password], [type=password]",
            creds["password"],
        ])
        _agent_browser.run(["click", "[type=submit], button[data-litms]"])
        time.sleep(3)

    _, url = _agent_browser.run(["get", "url"])
    authenticated = "login" not in url.lower() and "auth" not in url.lower()
    return {"success": authenticated, "url": url, "auto_filled": creds is not None}


def _op_lookup(domain: str) -> dict[str, str] | None:
    """Look up credentials from 1Password Agents vault by domain.

    Matches items whose URL contains the domain. When multiple items match,
    picks the closest match by shortest matching URL. When TROGOCYTOSIS_HOST
    is set, the lookup runs on that host so login auto-fill follows the
    remote browser session.
    """
    if not _command_available("op"):
        return None
    try:
        result = subprocess.run(
            _host_command("op", "item", "list", "--vault", "Agents", "--format=json"),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        items = json.loads(result.stdout)
        best_match: tuple[int, str] | None = None
        for item in items:
            for url_entry in item.get("urls", []):
                href = url_entry.get("href", "")
                if domain in href:
                    url_len = len(href)
                    if best_match is None or url_len < best_match[0]:
                        best_match = (url_len, item["id"])

        if best_match is None:
            return None

        item_id = best_match[1]
        username = subprocess.run(
            _host_command(
                "op",
                "item",
                "get",
                item_id,
                "--vault",
                "Agents",
                "--fields",
                "username",
                "--reveal",
            ),
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        password = subprocess.run(
            _host_command(
                "op",
                "item",
                "get",
                item_id,
                "--vault",
                "Agents",
                "--fields",
                "password",
                "--reveal",
            ),
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if username and password:
            return {"username": username, "password": password}
    except Exception:
        pass
    return None
