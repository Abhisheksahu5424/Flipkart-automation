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

class FlipkartProductActions:
    """Product screen actions."""

    def _find_pdp_text_cta(self, action: str):
        button = self._driver().execute_script(
            """
            const action = arguments[0];
            const patterns = action === 'add'
                ? [/^add\\s*to\\s*cart$/i]
                : [/^go(?:ing)?\\s*to\\s*cart$/i];

            const candidates = [];
            for (const node of document.querySelectorAll('div, button, span')) {
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (!text || text.length > 20) {
                    continue;
                }
                if (!patterns.some((pattern) => pattern.test(text))) {
                    continue;
                }

                const target = (
                    node.closest('div[class*="css-q5y9jx"]')
                    || node.closest('div[class*="css-g5y9jx"]')
                    || node.closest('button')
                    || node
                );
                const rect = target.getBoundingClientRect();
                if (rect.width < 20 || rect.height < 10) {
                    continue;
                }
                candidates.push({
                    target,
                    area: rect.width * rect.height,
                    text,
                });
            }

            candidates.sort((left, right) => left.area - right.area);
            return candidates.length ? candidates[0].target : null;
            """,
            action,
        )
        return button

    def _pick_clickable_icon_target(self, node):
        if node is None:
            return None
        return self._driver().execute_script(
            """
            let current = arguments[0];
            while (current) {
                const style = (current.getAttribute('style') || '').toLowerCase();
                const computed = window.getComputedStyle(current);
                if (
                    (style.includes('cursor') && style.includes('pointer'))
                    || computed.cursor === 'pointer'
                ) {
                    return current;
                }
                current = current.parentElement;
            }
            return (
                arguments[0].closest('div[class*="css-g5y9jx"]')
                || arguments[0].closest('div[class*="css-q5y9jx"]')
                || arguments[0].closest('button')
                || arguments[0]
            );
            """,
            node,
        )

    def _find_pdp_icon_cart_button(self, action: str):
        return self._driver().execute_script(
            """
            const action = arguments[0];
            const actionKey = action === 'add' ? 'AddToCart' : 'GoToCart';

            const isVisible = (node) => {
                if (!node) {
                    return false;
                }
                const rect = node.getBoundingClientRect();
                return rect.width > 10 && rect.height > 10;
            };

            const pickTarget = (node) => {
                let current = node;
                while (current) {
                    const style = (current.getAttribute('style') || '').toLowerCase();
                    const computed = window.getComputedStyle(current);
                    if (
                        (style.includes('cursor') && style.includes('pointer'))
                        || computed.cursor === 'pointer'
                    ) {
                        return current;
                    }
                    current = current.parentElement;
                }
                return (
                    node?.closest('div[class*="css-g5y9jx"]')
                    || node?.closest('div[class*="css-q5y9jx"]')
                    || node?.closest('button')
                    || node
                );
            };

            const isWishlistButton = (btn) => {
                const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                if (/wish|heart|favourite|favorite/.test(`${aria} ${title}`)) {
                    return true;
                }
                for (const clip of btn.querySelectorAll('clipPath')) {
                    const id = (clip.id || '').toLowerCase();
                    if (/wish|heart|fav/i.test(id)) {
                        return true;
                    }
                }
                const rect = btn.getBoundingClientRect();
                return rect.bottom < window.innerHeight * 0.65;
            };

            const isInBuyActionBar = (btn) => {
                const btnRect = btn.getBoundingClientRect();
                if (btnRect.bottom < window.innerHeight * 0.72) {
                    return false;
                }
                let current = btn.parentElement;
                for (let depth = 0; depth < 8 && current; depth += 1) {
                    const rowText = (current.textContent || '').toLowerCase();
                    const rowRect = current.getBoundingClientRect();
                    if (
                        rowText.includes('buy now')
                        && rowRect.height < 180
                        && rowRect.width > 180
                        && rowRect.bottom > window.innerHeight * 0.7
                    ) {
                        return true;
                    }
                    current = current.parentElement;
                }
                return false;
            };

            const isCartIconButton = (btn) => {
                if (!btn?.querySelector('svg')) {
                    return false;
                }
                if (!isVisible(btn)) {
                    return false;
                }
                if (isWishlistButton(btn)) {
                    return false;
                }
                const ownText = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
                if (ownText && /buy|emi|now|₹|wish/i.test(ownText)) {
                    return false;
                }
                const rect = btn.getBoundingClientRect();
                if (rect.width > 140 || rect.height > 110 || rect.width < 24) {
                    return false;
                }
                return isInBuyActionBar(btn);
            };

            const acceptTarget = (node) => {
                const target = pickTarget(node);
                if (!target || !isVisible(target) || isWishlistButton(target)) {
                    return null;
                }
                if (!isInBuyActionBar(target)) {
                    return null;
                }
                return target;
            };

            for (const clip of document.querySelectorAll('clipPath')) {
                const clipId = clip.id || '';
                if (!clipId.toLowerCase().includes(actionKey.toLowerCase())) {
                    continue;
                }
                if (/wish|heart|fav/i.test(clipId)) {
                    continue;
                }
                const svg = document.querySelector(`svg[clip-path="url(#${clipId})"]`);
                const target = acceptTarget(svg);
                if (target) {
                    return target;
                }
            }

            for (const svg of document.querySelectorAll('svg')) {
                const clipPath = svg.getAttribute('clip-path') || '';
                if (!clipPath.toLowerCase().includes(actionKey.toLowerCase())) {
                    continue;
                }
                if (/wish|heart|fav/i.test(clipPath)) {
                    continue;
                }
                const target = acceptTarget(svg);
                if (target) {
                    return target;
                }
            }

            const buyBarIcons = [];
            for (const btn of document.querySelectorAll(
                'div[class*="css-g5y9jx"], div[class*="css-q5y9jx"]'
            )) {
                if (!isCartIconButton(btn)) {
                    continue;
                }
                const rect = btn.getBoundingClientRect();
                buyBarIcons.push({ btn, bottom: rect.bottom, left: rect.left });
            }

            buyBarIcons.sort((left, right) => (
                right.bottom - left.bottom || left.left - right.left
            ));

            if (!buyBarIcons.length) {
                return null;
            }

            if (action === 'add') {
                return buyBarIcons[0].btn;
            }

            const aria = (buyBarIcons[0].btn.getAttribute('aria-label') || '').toLowerCase();
            if (/go(?:ing)?\\s*to\\s*cart/.test(aria)) {
                return buyBarIcons[0].btn;
            }

            for (const path of document.querySelectorAll('svg path')) {
                const d = path.getAttribute('d') || '';
                if (!d.includes('17 18.375') && !d.includes('M17 18')) {
                    continue;
                }
                const target = acceptTarget(path.closest('svg'));
                if (target) {
                    return target;
                }
            }

            return null;
            """,
            action,
        )

    def _get_header_cart_count(self) -> int:
        count = self._driver().execute_script(
            """
            for (const anchor of document.querySelectorAll(
                'a[href*="viewcart"], a[title*="Cart"], a[title*="cart"]'
            )) {
                const text = (anchor.textContent || '').replace(/\\s+/g, ' ').trim();
                const match = text.match(/\\b(\\d+)\\b/);
                if (match) {
                    return parseInt(match[1], 10);
                }
                for (const child of anchor.querySelectorAll('span, div')) {
                    const value = (child.textContent || '').trim();
                    if (/^\\d+$/.test(value)) {
                        return parseInt(value, 10);
                    }
                }
            }
            return 0;
            """
        )
        return int(count or 0)

    def _find_header_cart_link(self):
        return self._driver().execute_script(
            """
            const candidates = [];
            for (const anchor of document.querySelectorAll(
                'a[href*="viewcart"], a[href*="/cart"]'
            )) {
                const rect = anchor.getBoundingClientRect();
                if (rect.width < 8 || rect.height < 8 || rect.top > 180) {
                    continue;
                }
                candidates.push({ anchor, top: rect.top, left: rect.left });
            }
            candidates.sort((left, right) => left.top - right.top || right.left - left.left);
            return candidates.length ? candidates[0].anchor : null;
            """
        )

    def _find_go_to_cart_snackbar_link(self):
        return self._driver().execute_script(
            """
            const isInBuyActionBar = (node) => {
                let current = node;
                for (let depth = 0; depth < 8 && current; depth += 1) {
                    const rowText = (current.textContent || '').toLowerCase();
                    const rowRect = current.getBoundingClientRect();
                    if (
                        rowText.includes('buy now')
                        && rowRect.height < 180
                        && rowRect.width > 180
                        && rowRect.bottom > window.innerHeight * 0.7
                    ) {
                        return true;
                    }
                    current = current.parentElement;
                }
                return false;
            };

            const candidates = [];
            for (const node of document.querySelectorAll('a, button, div, span')) {
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (!/^go\\s*to\\s*cart$/i.test(text)) {
                    continue;
                }
                if (isInBuyActionBar(node)) {
                    continue;
                }
                const rect = node.getBoundingClientRect();
                if (rect.width < 20 || rect.height < 8) {
                    continue;
                }
                const target = node.closest('a, button') || node;
                candidates.push({
                    target,
                    area: rect.width * rect.height,
                    bottom: rect.bottom,
                });
            }

            candidates.sort((left, right) => right.bottom - left.bottom || left.area - right.area);
            return candidates.length ? candidates[0].target : null;
            """
        )

    def _uses_icon_cart_layout(self) -> bool:
        return self._find_pdp_icon_cart_button("add") is not None

    def _is_product_added_or_go_to_cart(self, cart_count_before: int = 0) -> bool:
        visible_text = self._get_visible_page_text()
        if re.search(r"go(?:ing)? to cart", visible_text, re.I):
            return True
        if re.search(r"added to (?:cart|bag)", visible_text, re.I):
            return True
        if self._get_header_cart_count() > cart_count_before:
            return True
        if self._driver().execute_script(
            'return !!document.querySelector(\'clipPath[id*="GoToCart"]\');'
        ):
            return True
        go_icon = self._find_pdp_icon_cart_button("go")
        if go_icon is not None:
            aria = (go_icon.get_attribute("aria-label") or "").lower()
            if re.search(r"go(?:ing)? to cart", aria, re.I):
                return True
        return False

    def _has_go_to_cart_icon_state(self) -> bool:
        return self._is_product_added_or_go_to_cart(0) and (
            self._get_header_cart_count() > 0 or self._uses_icon_cart_layout()
        )

    def _find_add_to_cart_button(self):
        self._scroll_product_page_for_cta()
        button = self._find_pdp_icon_cart_button("add")
        if button is not None:
            return button

        button = self._find_pdp_text_cta("add")
        if button is not None:
            return button

        xpaths = [
            "//div[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='add to cart']",
            "//button[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='add to cart']",
            "//div[contains(@class, '_2KpZ6l') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
            "//div[contains(@class, 'css-g5y9jx')][.//clipPath[contains(@id, 'AddToCart')]]",
            "//svg[contains(@clip-path, 'AddToCart')]/ancestor::div[contains(@class, 'css-g5y9jx')][1]",
        ]
        for xpath in xpaths:
            for element in self._driver().find_elements(By.XPATH, xpath):
                if element.is_displayed():
                    return element
        return None

    def _find_go_to_cart_button(self):
        self._scroll_product_page_for_cta()
        button = self._find_pdp_text_cta("go")
        if button is not None:
            return button

        button = self._find_pdp_icon_cart_button("go")
        if button is not None:
            return button

        xpaths = [
            "//div[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='going to cart']",
            "//div[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='go to cart']",
            "//button[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='going to cart']",
            "//button[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='go to cart']",
            "//div[contains(@class, 'css-g5y9jx')][.//clipPath[contains(@id, 'GoToCart')]]",
            "//svg[contains(@clip-path, 'GoToCart')]/ancestor::div[contains(@class, 'css-g5y9jx')][1]",
        ]
        for xpath in xpaths:
            for element in self._driver().find_elements(By.XPATH, xpath):
                if element.is_displayed():
                    return element
        return None

    def _get_go_to_cart_text(self) -> str:
        button = self._find_go_to_cart_button()
        if button is not None:
            text = (button.text or "").strip()
            if re.search(r"go(?:ing)? to cart", text, re.I):
                return text
            aria = (button.get_attribute("aria-label") or "").strip()
            if re.search(r"go(?:ing)? to cart", aria, re.I):
                return aria

        if self._has_go_to_cart_icon_state():
            return "Going to cart"

        visible_text = self._get_visible_page_text()
        match = re.search(r"(go(?:ing)? to cart)", visible_text, re.I)
        if match:
            return match.group(1)
        return ""

    def wait_for_product_page_title(self, timeout: Optional[int | str] = None) -> None:
        def title_visible(driver) -> bool:
            self.dismiss_login_popup_if_visible()
            for xpath in (
                "//h1",
                "//span[contains(@class, 'B_NuCI')]",
                "//h1[contains(@class, 'yhB1nd')]",
                "//span[contains(@class, 'VU-ZEz')]",
            ):
                for element in driver.find_elements(By.XPATH, xpath):
                    if element.is_displayed() and len(element.text.strip()) >= 5:
                        return True
            body = driver.find_element(By.TAG_NAME, "body").text
            return bool(re.search(r"₹[\d,]+", body))

        self._wait(timeout).until(lambda driver: title_visible(driver))
        logger.info("Product page title/content is visible.")

    def wait_for_add_to_cart_button(self, timeout: Optional[int | str] = None) -> None:
        self._ensure_product_page_window()
        self.dismiss_login_popup_if_visible()
        self._scroll_product_page_for_cta()
        self._pause(0.3)

        def add_to_cart_visible(driver) -> bool:
            return self._find_add_to_cart_button() is not None

        self._wait(timeout or 30).until(lambda driver: add_to_cart_visible(driver))
        logger.info("Add to cart button is visible on product page.")

    def click_add_to_cart_on_product_page(self) -> None:
        self._ensure_product_page_window()
        self.dismiss_login_popup_if_visible()
        self._scroll_product_page_for_cta()
        self._pause(0.4)
        self._wait(30).until(lambda d: self._find_add_to_cart_button() is not None)
        button = self._find_add_to_cart_button()
        if button is None:
            raise AssertionError("Add to cart button was not found on product page.")
        used_icon = self._driver().execute_script(
            """
            const node = arguments[0];
            const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
            return node.querySelector('svg') !== null && !/add\\s*to\\s*cart/i.test(text);
            """,
            button,
        )
        cart_before = self._get_header_cart_count()
        self._click_product_page_button(button)
        self._ensure_product_page_window()
        self._pause(0.6)
        self._wait(30).until(
            lambda driver: self._is_product_added_or_go_to_cart(cart_before)
        )
        self._pause(0.4)
        logger.info(
            "Clicked Add to cart %s on product page.",
            "icon" if used_icon else "button",
        )

    def verify_go_to_cart_button_visible(self, timeout: Optional[int | str] = None) -> str:
        self._ensure_product_page_window()
        self._pause(0.4)

        def go_to_cart_visible(driver) -> bool:
            self._ensure_product_page_window()
            text = self._get_go_to_cart_text()
            if re.search(r"go(?:ing)? to cart", text, re.I):
                return True
            if self._find_go_to_cart_button() is not None:
                return True
            if self._get_header_cart_count() > 0 and self._uses_icon_cart_layout():
                return True
            return self._is_product_added_or_go_to_cart(0)

        self._wait(timeout).until(lambda driver: go_to_cart_visible(driver))
        text = self._get_go_to_cart_text()
        if not text:
            if self._get_header_cart_count() > 0 and self._uses_icon_cart_layout():
                text = "Going to cart"
            elif self._find_go_to_cart_button() or self._has_go_to_cart_icon_state():
                text = "Going to cart"
        if not re.search(r"go(?:ing)? to cart", text, re.I):
            if self._get_header_cart_count() > 0 and self._uses_icon_cart_layout():
                text = "Going to cart"
            else:
                raise AssertionError(
                    "Go to cart / Going to cart button was not found after adding item."
                )
        logger.info("Go to cart button verified: %s", text)
        return text

    def _open_cart_from_product_page(self) -> str:
        """Try snackbar, header cart, then PDP CTA. Returns strategy used."""
        self._ensure_product_page_window()
        self.dismiss_login_popup_if_visible()
        driver = self._driver()
        handles_before = set(driver.window_handles)

        strategies = []
        snackbar = self._find_go_to_cart_snackbar_link()
        if snackbar is not None:
            strategies.append(("snackbar", snackbar))

        header = self._find_header_cart_link()
        if header is not None and self._get_header_cart_count() > 0:
            strategies.append(("header", header))

        if self._uses_icon_cart_layout() and header is not None:
            strategies = [("header", header)] + [
                item for item in strategies if item[0] != "header"
            ]

        button = self._find_go_to_cart_button()
        if button is not None:
            strategies.append(("pdp", button))

        if not strategies:
            raise AssertionError("Go to cart entry point was not found on product page.")

        for name, target in strategies:
            self._ensure_product_page_window()
            self._click_product_page_button(target)
            self._pause(0.6)
            new_handles = set(driver.window_handles) - handles_before
            if new_handles:
                driver.switch_to.window(new_handles.pop())
            try:
                self._wait_for_cart_url(10)
                return name
            except Exception:
                self._pause(0.4)
                continue

        base_url = driver.current_url.split("/p/")[0] or "https://www.flipkart.com"
        driver.get(f"{base_url}/viewcart?otracker=Cart_Icon_ViewCart")
        self._wait_for_cart_url(20)
        return "direct"

    def navigate_to_cart_from_product_page(self) -> None:
        strategy = self._open_cart_from_product_page()
        self._stabilize_cart_page()
        self.wait_for_cart_page_loaded(30)
        logger.info("Navigated to cart from product page via %s.", strategy)

    def set_delivery_pincode_if_prompted(self, pincode: str) -> bool:
        inputs = self._driver().find_elements(
            By.XPATH,
            "//input[@placeholder='Enter Delivery Pincode' or @name='pincode' or contains(@placeholder,'pincode')]",
        )
        for input_el in inputs:
            if input_el.is_displayed():
                input_el.clear()
                input_el.send_keys(pincode)
                buttons = self._driver().find_elements(
                    By.XPATH,
                    "//button[normalize-space()='Check' or normalize-space()='Submit']",
                )
                for button in buttons:
                    if button.is_displayed():
                        button.click()
                        self._wait(10).until(
                            EC.invisibility_of_element(input_el)
                        )
                        logger.info("Delivery pincode %s submitted.", pincode)
                        return True
        return False
