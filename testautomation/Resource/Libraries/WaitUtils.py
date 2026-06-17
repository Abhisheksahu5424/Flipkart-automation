"""
WaitUtils - Explicit wait helpers for Selenium interactions.
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Tuple, Union

from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class WaitUtils:
    """Explicit wait utilities exposed as Robot Framework keywords."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, default_timeout: int = 20):
        self.default_timeout = int(default_timeout)

    def _parse_timeout(self, timeout: Optional[Union[int, str]] = None) -> int:
        if timeout is None:
            return self.default_timeout
        if isinstance(timeout, str):
            digits = re.sub(r"[^\d]", "", timeout)
            return int(digits or self.default_timeout)
        return int(timeout)

    def _get_driver(self):
        selenium_library = BuiltIn().get_library_instance("SeleniumLibrary")
        return selenium_library.driver

    def _parse_locator(self, locator: str) -> Tuple[str, str]:
        if locator.startswith("xpath="):
            return By.XPATH, locator[len("xpath=") :]
        if locator.startswith("css:") or locator.startswith("css="):
            prefix_len = 4 if locator.startswith("css:") else 4
            return By.CSS_SELECTOR, locator[prefix_len:]
        if locator.startswith("id="):
            return By.ID, locator[3:]
        if locator.startswith("//") or locator.startswith("(//"):
            return By.XPATH, locator
        return By.CSS_SELECTOR, locator

    @keyword("Wait For Element Visible")
    def wait_for_element_visible(
        self, locator: str, timeout: Optional[Union[int, str]] = None
    ) -> str:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        logger.info("Waiting for visible element: %s (timeout=%ss)", locator, timeout)
        WebDriverWait(self._get_driver(), timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        return locator

    @keyword("Wait For Element Clickable")
    def wait_for_element_clickable(
        self, locator: str, timeout: Optional[Union[int, str]] = None
    ) -> str:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        logger.info("Waiting for clickable element: %s (timeout=%ss)", locator, timeout)
        WebDriverWait(self._get_driver(), timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        return locator

    @keyword("Wait For Element Present")
    def wait_for_element_present(
        self, locator: str, timeout: Optional[Union[int, str]] = None
    ) -> str:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        logger.info("Waiting for element presence: %s (timeout=%ss)", locator, timeout)
        WebDriverWait(self._get_driver(), timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return locator

    @keyword("Wait For Text In Element")
    def wait_for_text_in_element(
        self,
        locator: str,
        expected_text: str,
        timeout: Optional[Union[int, str]] = None,
    ) -> str:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        logger.info(
            "Waiting for text '%s' in element %s (timeout=%ss)",
            expected_text,
            locator,
            timeout,
        )
        WebDriverWait(self._get_driver(), timeout).until(
            EC.text_to_be_present_in_element((by, value), expected_text)
        )
        return expected_text

    @keyword("Wait For Page To Contain")
    def wait_for_page_to_contain(
        self, text: str, timeout: Optional[Union[int, str]] = None
    ) -> str:
        timeout = self._parse_timeout(timeout)
        logger.info("Waiting for page to contain text '%s' (timeout=%ss)", text, timeout)
        WebDriverWait(self._get_driver(), timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(., '{text}')]"))
        )
        return text

    @keyword("Safe Click Element")
    def safe_click_element(
        self, locator: str, timeout: Optional[Union[int, str]] = None
    ) -> None:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        driver = self._get_driver()
        last_error = None

        element = None
        for attempt in range(1, 4):
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                    element,
                )
                element.click()
                logger.info("Clicked element safely: %s", locator)
                return
            except (
                StaleElementReferenceException,
                ElementClickInterceptedException,
                ElementNotInteractableException,
            ) as exc:
                last_error = exc
                logger.warning(
                    "Click attempt %s failed for %s: %s",
                    attempt,
                    locator,
                    exc,
                )

        if element is not None:
            try:
                driver.execute_script("arguments[0].click();", element)
                logger.info("Clicked element via JavaScript fallback: %s", locator)
                return
            except Exception as exc:
                last_error = exc

        raise TimeoutException(f"Unable to click element '{locator}': {last_error}")

    @keyword("Safe Input Text")
    def safe_input_text(
        self,
        locator: str,
        text: str,
        clear: bool = True,
        timeout: Optional[Union[int, str]] = None,
    ) -> None:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        driver = self._get_driver()
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )
        if clear:
            element.clear()
        element.send_keys(text)
        logger.info("Entered text into %s", locator)

    @keyword("Scroll Locator Into View")
    def scroll_locator_into_view(
        self, locator: str, timeout: Optional[Union[int, str]] = None
    ) -> None:
        timeout = self._parse_timeout(timeout)
        by, value = self._parse_locator(locator)
        driver = self._get_driver()
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )
        logger.info("Scrolled element into view: %s", locator)
