"""Flipkart screen-wise action modules."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

class FlipkartBase:
    """Shared browser helpers and session state."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, default_timeout: int = 20):
        self.default_timeout = int(default_timeout)
        self._selected_listing_price: Optional[str] = None
        self._compared_products: list[str] = []

    def _driver(self):
        return BuiltIn().get_library_instance("SeleniumLibrary").driver

    def _parse_timeout(self, timeout: Optional[int | str] = None) -> int:
        if timeout is None:
            return self.default_timeout
        if isinstance(timeout, str):
            digits = re.sub(r"[^\d]", "", timeout)
            return int(digits or self.default_timeout)
        return int(timeout)

    def _wait(self, timeout: Optional[int | str] = None):
        return WebDriverWait(self._driver(), self._parse_timeout(timeout))

    def wait_for_body_text_pattern(
        self, pattern: str, timeout: Optional[int | str] = None
    ) -> None:
        compiled = re.compile(pattern, re.I | re.S)
        self._wait(timeout).until(
            lambda driver: bool(compiled.search(driver.find_element(By.TAG_NAME, "body").text))
        )
        logger.info("Body text matched pattern: %s", pattern)

    def _find_element_by_js(self, script: str):
        element = self._driver().execute_script(script)
        return element

    def _pause(self, seconds: float = 0.4) -> None:
        time.sleep(seconds)

    def _scroll_product_page_for_cta(self) -> None:
        self._driver().execute_script(
            """
            const max = Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            );
            window.scrollTo({
                top: Math.max(0, max - window.innerHeight + 140),
                behavior: 'instant',
            });
            """
        )

    def _scroll_cart_controls_into_view(self) -> None:
        selector = self._find_cart_quantity_selector()
        if selector is not None:
            self._driver().execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                selector,
            )
            self._pause(0.3)
            return
        self._driver().execute_script("window.scrollTo({top: 0, behavior: 'instant'});")
        self._pause(0.2)

    def _ensure_product_page_window(self) -> None:
        driver = self._driver()
        handles = driver.window_handles
        if len(handles) <= 1:
            return
        for handle in handles:
            driver.switch_to.window(handle)
            try:
                if "/p/" in driver.current_url:
                    return
            except Exception:
                continue
        driver.switch_to.window(handles[0])

    def _get_visible_page_text(self) -> str:
        return self._driver().execute_script(
            "return (document.body && document.body.innerText) || '';"
        )

    def _ensure_cart_page_window(self) -> None:
        driver = self._driver()
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            try:
                url = driver.current_url.lower()
                if "viewcart" in url or "/cart" in url:
                    return
            except Exception:
                continue
        current_url = driver.current_url.lower()
        if "viewcart" in current_url or "/cart" in current_url:
            return
        base_url = (
            driver.current_url.split("/p/")[0]
            if "/p/" in driver.current_url
            else "https://www.flipkart.com"
        )
        if base_url.startswith("http"):
            driver.get(f"{base_url}/viewcart?otracker=Cart_Icon_ViewCart")
            self._wait_for_cart_url(20)

    def _stabilize_cart_page(self) -> None:
        self._ensure_cart_page_window()
        self.dismiss_login_popup_if_visible()
        self._scroll_cart_controls_into_view()

        def cart_ready(driver) -> bool:
            text = self._get_visible_page_text().lower()
            if not text or len(text) < 15:
                return False
            has_qty = self._find_cart_quantity_selector() is not None
            has_markers = any(
                marker in text
                for marker in (
                    "price details",
                    "total amount",
                    "place order",
                    "qty:",
                )
            )
            return has_qty or has_markers

        self._wait(25).until(lambda driver: cart_ready(driver))
        self._pause(0.5)

    def _click_product_page_button(self, element) -> None:
        driver = self._driver()
        target = self._pick_clickable_icon_target(element) or element
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            target,
        )
        try:
            ActionChains(driver).move_to_element(target).pause(0.3).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", target)

    def _wait_for_cart_url(self, timeout: int = 20) -> None:
        self._wait(timeout).until(
            lambda d: "viewcart" in d.current_url.lower()
            or "/cart" in d.current_url.lower()
        )
