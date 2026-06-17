"""
ProxyManager - Chrome proxy configuration utility for Robot Framework automation.

Supports:
  - HTTP / HTTPS proxy
  - Authenticated proxy (via Chrome extension)
  - Rotating proxy pool
"""

from __future__ import annotations

import logging
import os
import tempfile
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from robot.api.deco import keyword

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Normalized proxy configuration."""

    host: str
    port: int
    scheme: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None

    @property
    def server_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def is_authenticated(self) -> bool:
        return bool(self.username and self.password)


class ProxyManager:
    """Builds Chrome-compatible proxy settings from environment or explicit config."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self):
        self._proxy_pool: List[ProxyConfig] = []
        self._rotation_index: int = 0
        self._extension_path: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Robot Framework keywords
    # ------------------------------------------------------------------ #

    @keyword("Load Proxy Pool From Environment")
    def load_proxy_pool_from_environment(self) -> int:
        """
        Load rotating proxy pool from environment variables.

        Expected format for PROXY_POOL:
            host1:port1,host2:port2,user:pass@host3:port3
        """
        raw_pool = os.getenv("PROXY_POOL", "").strip()
        if not raw_pool:
            logger.info("PROXY_POOL is empty; proxy rotation disabled.")
            self._proxy_pool = []
            return 0

        entries = [item.strip() for item in raw_pool.split(",") if item.strip()]
        self._proxy_pool = [self._parse_proxy_entry(entry) for entry in entries]
        self._rotation_index = 0
        logger.info("Loaded %s proxies into rotation pool.", len(self._proxy_pool))
        return len(self._proxy_pool)

    @keyword("Get Active Proxy Config")
    def get_active_proxy_config(self) -> Dict[str, Any]:
        """Return active proxy as a dictionary for BrowserFactory consumption."""
        config = self._resolve_proxy_config()
        if not config:
            return {}

        payload = {
            "host": config.host,
            "port": config.port,
            "scheme": config.scheme,
            "server_url": config.server_url,
            "username": config.username or "",
            "password": config.password or "",
            "authenticated": config.is_authenticated,
        }
        logger.info("Active proxy resolved: %s", config.server_url)
        return payload

    @keyword("Rotate Proxy")
    def rotate_proxy(self) -> Dict[str, Any]:
        """Advance rotating proxy index and return next proxy config."""
        if not self._proxy_pool:
            self.load_proxy_pool_from_environment()
        if not self._proxy_pool:
            logger.warning("Proxy pool is empty; rotation skipped.")
            return {}

        self._rotation_index = (self._rotation_index + 1) % len(self._proxy_pool)
        logger.info("Rotated proxy to index %s.", self._rotation_index)
        return self.get_active_proxy_config()

    @keyword("Build Chrome Proxy Argument")
    def build_chrome_proxy_argument(self, proxy_config: Optional[Dict[str, Any]] = None) -> str:
        """Return --proxy-server argument for ChromeOptions."""
        config = self._dict_to_config(proxy_config) if proxy_config else self._resolve_proxy_config()
        if not config:
            return ""
        argument = f"--proxy-server={config.server_url}"
        logger.info("Chrome proxy argument: %s", argument)
        return argument

    @keyword("Create Proxy Auth Extension")
    def create_proxy_auth_extension(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        scheme: str = "http",
    ) -> str:
        """
        Create a temporary Chrome extension that supplies proxy credentials.
        Chrome does not support authenticated proxies via CLI flags alone.
        """
        config = ProxyConfig(
            host=host,
            port=int(port),
            scheme=scheme,
            username=username,
            password=password,
        )
        extension_path = self._build_auth_extension(config)
        self._extension_path = extension_path
        logger.info("Proxy auth extension created at %s", extension_path)
        return extension_path

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _resolve_proxy_config(self) -> Optional[ProxyConfig]:
        if self._proxy_pool:
            return self._proxy_pool[self._rotation_index]

        explicit = os.getenv("PROXY_URL", "").strip()
        if explicit:
            return self._parse_proxy_entry(explicit)

        host = os.getenv("PROXY_HOST", "").strip()
        port = os.getenv("PROXY_PORT", "").strip()
        if host and port:
            return ProxyConfig(
                host=host,
                port=int(port),
                scheme=os.getenv("PROXY_SCHEME", "http").strip() or "http",
                username=os.getenv("PROXY_USERNAME", "").strip() or None,
                password=os.getenv("PROXY_PASSWORD", "").strip() or None,
            )
        return None

    def _parse_proxy_entry(self, entry: str) -> ProxyConfig:
        scheme = "http"
        if "://" in entry:
            scheme, entry = entry.split("://", 1)

        username = None
        password = None
        if "@" in entry:
            creds, endpoint = entry.rsplit("@", 1)
            if ":" in creds:
                username, password = creds.split(":", 1)
            host, port = endpoint.split(":", 1)
        else:
            host, port = entry.split(":", 1)

        return ProxyConfig(
            host=host.strip(),
            port=int(port.strip()),
            scheme=scheme.strip() or "http",
            username=username.strip() if username else None,
            password=password.strip() if password else None,
        )

    def _dict_to_config(self, payload: Dict[str, Any]) -> Optional[ProxyConfig]:
        if not payload:
            return None
        host = payload.get("host")
        port = payload.get("port")
        if not host or not port:
            return None
        return ProxyConfig(
            host=str(host),
            port=int(port),
            scheme=str(payload.get("scheme", "http")),
            username=payload.get("username") or None,
            password=payload.get("password") or None,
        )

    def _build_auth_extension(self, config: ProxyConfig) -> str:
        if not config.is_authenticated:
            raise ValueError("Proxy auth extension requires username and password.")

        manifest = """
{
  "version": "1.0.0",
  "manifest_version": 2,
  "name": "Chrome Proxy Auth",
  "permissions": [
    "proxy",
    "tabs",
    "unlimitedStorage",
    "storage",
    "<all_urls>",
    "webRequest",
    "webRequestBlocking"
  ],
  "background": {
    "scripts": ["background.js"]
  },
  "minimum_chrome_version": "22.0.0"
}
""".strip()

        background = f"""
var config = {{
  mode: "fixed_servers",
  rules: {{
    singleProxy: {{
      scheme: "{config.scheme}",
      host: "{config.host}",
      port: parseInt({config.port})
    }},
    bypassList: ["localhost", "127.0.0.1"]
  }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
  return {{
    authCredentials: {{
      username: "{config.username}",
      password: "{config.password}"
    }}
  }};
}}

chrome.webRequest.onAuthRequired.addListener(
  callbackFn,
  {{urls: ["<all_urls>"]}},
  ["blocking"]
);
""".strip()

        temp_dir = tempfile.mkdtemp(prefix="flipkart_proxy_ext_")
        extension_file = os.path.join(temp_dir, "proxy_auth_extension.zip")
        with zipfile.ZipFile(extension_file, "w") as archive:
            archive.writestr("manifest.json", manifest)
            archive.writestr("background.js", background)
        return extension_file
