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

class FlipkartHomeActions:
    """Home screen actions."""

    def dismiss_login_popup_if_visible(self) -> bool:
        for element in self._driver().find_elements(
            By.XPATH, "//span[@role='button' and contains(@class, '_b3wTlE')]"
        ):
            if element.is_displayed():
                try:
                    element.click()
                except Exception:
                    self._driver().execute_script("arguments[0].click();", element)
                logger.info("Dismissed login popup on current page.")
                return True
        return False
