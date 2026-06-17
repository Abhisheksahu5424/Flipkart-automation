"""
BrowserFactory - Initializes WebDriver instances with proxy, anti-detection, and stable defaults.

Supported browsers: chrome, firefox, edge
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, Optional

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from ProxyManager import ProxyManager

logger = logging.getLogger(__name__)

SUPPORTED_BROWSERS = frozenset({"chrome", "firefox", "edge"})


class BrowserFactory:
    """Factory for creating WebDriver instances for Robot Framework tests."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    DEFAULT_FIREFOX_USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    )

    DEFAULT_EDGE_USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    )

    def __init__(self):
        self._proxy_manager = self._get_proxy_manager()
        self._last_options: Optional[Any] = None

    def _get_proxy_manager(self) -> ProxyManager:
        try:
            return BuiltIn().get_library_instance("ProxyManager")
        except Exception:
            return ProxyManager()

    def _resolve_user_agent(
        self, browser: str, user_agent: Optional[str] = None
    ) -> str:
        if user_agent:
            return user_agent
        env_agent = os.getenv("BROWSER_USER_AGENT", "").strip()
        if env_agent:
            return env_agent
        defaults = {
            "chrome": self.DEFAULT_USER_AGENT,
            "firefox": self.DEFAULT_FIREFOX_USER_AGENT,
            "edge": self.DEFAULT_EDGE_USER_AGENT,
        }
        return defaults.get(browser, self.DEFAULT_USER_AGENT)

    def _resolve_proxy_config(
        self, proxy_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return proxy_config or self._proxy_manager.get_active_proxy_config() or {}

    @keyword("Get Chrome Options")
    def get_chrome_options(
        self,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        proxy_config: Optional[Dict[str, Any]] = None,
    ) -> ChromeOptions:
        """Build ChromeOptions with proxy, stealth flags, and browser preferences."""
        options = ChromeOptions()
        resolved_proxy = self._resolve_proxy_config(proxy_config)

        if incognito:
            options.add_argument("--incognito")
            logger.info("Incognito mode enabled.")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        resolved_user_agent = self._resolve_user_agent("chrome", user_agent)
        options.add_argument(f"--user-agent={resolved_user_agent}")
        logger.info("Using user-agent: %s", resolved_user_agent)

        proxy_argument = self._proxy_manager.build_chrome_proxy_argument(resolved_proxy)
        if proxy_argument:
            options.add_argument(proxy_argument)

        if resolved_proxy and resolved_proxy.get("authenticated"):
            extension_path = self._proxy_manager.create_proxy_auth_extension(
                host=resolved_proxy["host"],
                port=resolved_proxy["port"],
                username=resolved_proxy["username"],
                password=resolved_proxy["password"],
                scheme=resolved_proxy.get("scheme", "http"),
            )
            options.add_extension(extension_path)
            logger.info("Authenticated proxy extension attached.")

        self._last_options = options
        return options

    @keyword("Get Firefox Options")
    def get_firefox_options(
        self,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        proxy_config: Optional[Dict[str, Any]] = None,
    ) -> FirefoxOptions:
        """Build Firefox Options with proxy and browser preferences."""
        options = FirefoxOptions()
        resolved_proxy = self._resolve_proxy_config(proxy_config)

        if incognito:
            options.set_preference("browser.privatebrowsing.autostart", True)
            logger.info("Firefox private browsing enabled.")

        resolved_user_agent = self._resolve_user_agent("firefox", user_agent)
        options.set_preference("general.useragent.override", resolved_user_agent)
        options.set_preference("dom.webnotifications.enabled", False)
        logger.info("Using user-agent: %s", resolved_user_agent)

        if resolved_proxy:
            host = resolved_proxy.get("host")
            port = int(resolved_proxy.get("port", 0))
            if host and port:
                options.set_preference("network.proxy.type", 1)
                options.set_preference("network.proxy.http", host)
                options.set_preference("network.proxy.http_port", port)
                options.set_preference("network.proxy.ssl", host)
                options.set_preference("network.proxy.ssl_port", port)
                logger.info("Firefox proxy configured: %s:%s", host, port)
            if resolved_proxy.get("authenticated"):
                logger.warning(
                    "Authenticated proxy is not fully supported on Firefox; "
                    "use a non-authenticated proxy or Chrome/Edge."
                )

        self._last_options = options
        return options

    @keyword("Get Edge Options")
    def get_edge_options(
        self,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        proxy_config: Optional[Dict[str, Any]] = None,
    ) -> EdgeOptions:
        """Build Edge Options with proxy, stealth flags, and browser preferences."""
        options = EdgeOptions()
        resolved_proxy = self._resolve_proxy_config(proxy_config)

        if incognito:
            options.add_argument("--inprivate")
            logger.info("Edge InPrivate mode enabled.")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        resolved_user_agent = self._resolve_user_agent("edge", user_agent)
        options.add_argument(f"--user-agent={resolved_user_agent}")
        logger.info("Using user-agent: %s", resolved_user_agent)

        proxy_argument = self._proxy_manager.build_chrome_proxy_argument(resolved_proxy)
        if proxy_argument:
            options.add_argument(proxy_argument)

        if resolved_proxy and resolved_proxy.get("authenticated"):
            extension_path = self._proxy_manager.create_proxy_auth_extension(
                host=resolved_proxy["host"],
                port=resolved_proxy["port"],
                username=resolved_proxy["username"],
                password=resolved_proxy["password"],
                scheme=resolved_proxy.get("scheme", "http"),
            )
            options.add_extension(extension_path)
            logger.info("Authenticated proxy extension attached.")

        self._last_options = options
        return options

    @keyword("Create Chrome Driver")
    def create_chrome_driver(
        self,
        url: str,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        proxy_config: Optional[Dict[str, Any]] = None,
    ):
        """Create and return a Chrome WebDriver pointed at the given URL."""
        options = self.get_chrome_options(
            user_agent=user_agent,
            incognito=incognito,
            proxy_config=proxy_config,
        )
        driver = webdriver.Chrome(service=ChromeService(), options=options)
        return self._finalize_driver(driver, url, apply_stealth=True)

    @keyword("Create Firefox Driver")
    def create_firefox_driver(
        self,
        url: str,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        proxy_config: Optional[Dict[str, Any]] = None,
    ):
        """Create and return a Firefox WebDriver pointed at the given URL."""
        options = self.get_firefox_options(
            user_agent=user_agent,
            incognito=incognito,
            proxy_config=proxy_config,
        )
        driver = webdriver.Firefox(service=FirefoxService(), options=options)
        return self._finalize_driver(driver, url, apply_stealth=False)

    @keyword("Create Edge Driver")
    def create_edge_driver(
        self,
        url: str,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        proxy_config: Optional[Dict[str, Any]] = None,
    ):
        """Create and return an Edge WebDriver pointed at the given URL."""
        options = self.get_edge_options(
            user_agent=user_agent,
            incognito=incognito,
            proxy_config=proxy_config,
        )
        driver = webdriver.Edge(service=EdgeService(), options=options)
        return self._finalize_driver(driver, url, apply_stealth=True)

    def _finalize_driver(self, driver, url: str, apply_stealth: bool):
        driver.maximize_window()
        if apply_stealth:
            self._apply_stealth_scripts(driver)
        logger.info("Navigating to URL: %s", url)
        driver.get(url)
        return driver

    @keyword("Register Driver With SeleniumLibrary")
    def register_driver_with_selenium_library(self, driver):
        """Attach a custom driver instance to the active SeleniumLibrary session."""
        selenium_library = BuiltIn().get_library_instance("SeleniumLibrary")
        selenium_library.register_driver(driver, "default")
        logger.info("Custom WebDriver registered with SeleniumLibrary.")

    @keyword("Open Browser With Proxy")
    def open_browser_with_proxy(
        self,
        url: str,
        browser: str = "chrome",
        user_agent: Optional[str] = None,
        incognito: bool = True,
        rotate_proxy: bool = False,
    ):
        """
        High-level keyword used by Common.robot.
        Creates the requested browser with proxy and registers it with SeleniumLibrary.
        """
        normalized_browser = browser.strip().lower()
        if normalized_browser not in SUPPORTED_BROWSERS:
            supported = ", ".join(sorted(SUPPORTED_BROWSERS))
            raise ValueError(
                f"Unsupported browser '{browser}'. Supported browsers: {supported}"
            )

        if rotate_proxy:
            self._proxy_manager.rotate_proxy()

        proxy_config = self._proxy_manager.get_active_proxy_config() or None
        creators: Dict[str, Callable[..., Any]] = {
            "chrome": self.create_chrome_driver,
            "firefox": self.create_firefox_driver,
            "edge": self.create_edge_driver,
        }

        logger.info("Launching browser: %s", normalized_browser)
        driver = creators[normalized_browser](
            url=url,
            user_agent=user_agent,
            incognito=incognito,
            proxy_config=proxy_config,
        )
        self.register_driver_with_selenium_library(driver)
        return driver

    @keyword("Open Chrome With Proxy")
    def open_chrome_with_proxy(
        self,
        url: str,
        user_agent: Optional[str] = None,
        incognito: bool = True,
        rotate_proxy: bool = False,
    ):
        """Backward-compatible wrapper for Chrome-only launches."""
        return self.open_browser_with_proxy(
            url=url,
            browser="chrome",
            user_agent=user_agent,
            incognito=incognito,
            rotate_proxy=rotate_proxy,
        )

    def _apply_stealth_scripts(self, driver) -> None:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            },
        )
        logger.info("Applied anti-automation stealth scripts.")
