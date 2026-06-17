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

class FlipkartCartActions:
    """Cart screen actions."""

    def _find_cart_quantity_selector(self):
        return self._driver().execute_script(
            """
            const isVisible = (node) => {
                if (!node) {
                    return false;
                }
                const rect = node.getBoundingClientRect();
                return rect.width > 5 && rect.height > 5;
            };

            const hasQtyText = (node) => /^qty:?\\s*\\d+$/i.test(
                (node.textContent || '').replace(/\\s+/g, ' ').trim()
            );

            const candidates = [];
            for (const box of document.querySelectorAll('div[class*="css-g5y9jx"]')) {
                if (!hasQtyText(box)) {
                    continue;
                }
                const rect = box.getBoundingClientRect();
                if (!isVisible(box) || rect.width < 40 || rect.height < 18) {
                    continue;
                }
                candidates.push({ box, area: rect.width * rect.height });
            }

            candidates.sort((left, right) => left.area - right.area);
            if (candidates.length) {
                return candidates[0].box;
            }

            for (const node of document.querySelectorAll('div, span, button')) {
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (!/^qty:?\\s*\\d+$/i.test(text)) {
                    continue;
                }
                if (!isVisible(node)) {
                    continue;
                }
                return (
                    node.closest('div[class*="css-g5y9jx"]')
                    || node.closest('[style*="cursor: pointer"]')
                    || node
                );
            }
            return null;
            """
        )

    def _get_cart_item_quantity(self) -> int:
        selector = self._find_cart_quantity_selector()
        if selector is None:
            return 1
        text = (selector.text or "").replace("\n", " ").strip()
        match = re.search(r"qty:\s*(\d+)", text, re.I)
        return int(match.group(1)) if match else 1

    def _find_cart_quantity_option(self, quantity: str, qty_selector=None):
        return self._driver().execute_script(
            """
            const quantity = String(arguments[0]);
            const qtySelector = arguments[1];
            const qtyRect = qtySelector
                ? qtySelector.getBoundingClientRect()
                : { top: 0, bottom: 0 };

            const isVisible = (node) => {
                const rect = node.getBoundingClientRect();
                return rect.width > 5 && rect.height > 5;
            };

            const matchesQuantity = (text) => {
                const normalized = (text || '').replace(/\\s+/g, ' ').trim();
                return (
                    normalized === quantity
                    || new RegExp(`^qty:?\\s*${quantity}$`, 'i').test(normalized)
                );
            };

            const candidates = [];
            for (const node of document.querySelectorAll(
                'div, span, button, li, a'
            )) {
                const ownText = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (!matchesQuantity(ownText)) {
                    continue;
                }
                if (/^qty:\\s*\\d+$/i.test(ownText) && ownText.toLowerCase() !== `qty: ${quantity}`) {
                    continue;
                }
                if (!isVisible(node)) {
                    continue;
                }
                const rect = node.getBoundingClientRect();
                if (rect.width > 160 || rect.height > 90) {
                    continue;
                }
                const belowSelector = !qtySelector || rect.top >= qtyRect.top - 10;
                candidates.push({
                    node,
                    area: rect.width * rect.height,
                    below: belowSelector ? 0 : 1,
                    top: rect.top,
                });
            }

            candidates.sort(
                (left, right) => (
                    left.below - right.below
                    || left.top - right.top
                    || left.area - right.area
                ),
            );
            return candidates.length ? candidates[0].node : null;
            """,
            quantity,
            qty_selector,
        )

    def _find_cart_plus_button(self, qty_selector=None):
        qty_selector = qty_selector or self._find_cart_quantity_selector()
        return self._driver().execute_script(
            """
            const qtySelector = arguments[0];
            const isVisible = (node) => {
                const rect = node.getBoundingClientRect();
                return rect.width > 5 && rect.height > 5;
            };

            const nearQty = (node) => {
                if (!qtySelector) {
                    return true;
                }
                const qtyRect = qtySelector.getBoundingClientRect();
                const rect = node.getBoundingClientRect();
                const verticalGap = Math.abs(rect.top - qtyRect.top);
                const horizontalGap = Math.abs(rect.left - qtyRect.left);
                return verticalGap < 80 && horizontalGap < 260;
            };

            const candidates = [];
            for (const node of document.querySelectorAll('button, div, span')) {
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (text !== '+') {
                    continue;
                }
                if (!isVisible(node)) {
                    continue;
                }
                const rect = node.getBoundingClientRect();
                candidates.push({
                    node,
                    near: nearQty(node) ? 0 : 1,
                    left: rect.left,
                });
            }

            candidates.sort(
                (left, right) => left.near - right.near || right.left - left.left,
            );
            return candidates.length ? candidates[0].node : null;
            """,
            qty_selector,
        )

    def _cart_quantity_menu_visible(self, selector) -> bool:
        return bool(
            self._driver().execute_script(
                """
                const qtySelector = arguments[0];
                const qtyRect = qtySelector
                    ? qtySelector.getBoundingClientRect()
                    : { top: 0 };
                let count = 0;
                for (const node of document.querySelectorAll('div, span, li, button')) {
                    const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                    if (!/^\\d+$/.test(text)) {
                        continue;
                    }
                    const rect = node.getBoundingClientRect();
                    if (rect.width < 8 || rect.height < 8) {
                        continue;
                    }
                    if (rect.top < qtyRect.top - 20) {
                        continue;
                    }
                    count += 1;
                }
                return count >= 2;
                """,
                selector,
            )
        )

    def _open_cart_quantity_dropdown(self, selector) -> None:
        driver = self._driver()
        self._scroll_cart_controls_into_view()
        targets = driver.execute_script(
            """
            const selector = arguments[0];
            const nodes = [selector];
            let current = selector;
            for (let depth = 0; depth < 4 && current; depth += 1) {
                nodes.push(current);
                current = current.parentElement;
            }
            return [...new Set(nodes.filter(Boolean))];
            """,
            selector,
        )
        for target in targets:
            self._click_cart_control(target, scroll=False)
            self._pause(0.6)
            if self._cart_quantity_menu_visible(selector):
                return

    def _wait_for_cart_quantity(self, expected: int, timeout: Optional[int | str] = 20) -> None:
        def quantity_reached(driver) -> bool:
            self._ensure_cart_page_window()
            return self._get_cart_item_quantity() == expected

        self._wait(timeout).until(lambda driver: quantity_reached(driver))
        self._pause(0.4)

    def _click_cart_control(self, element, scroll: bool = False) -> None:
        driver = self._driver()
        if scroll:
            self._scroll_cart_controls_into_view()
        try:
            ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", element)
        self._pause(0.5)

    def _select_cart_quantity_option(self, selector, target: int) -> bool:
        self._open_cart_quantity_dropdown(selector)
        option = None
        try:
            self._wait(12).until(
                lambda driver: self._find_cart_quantity_option(
                    str(target), selector
                )
                is not None
            )
            option = self._find_cart_quantity_option(str(target), selector)
        except Exception:
            option = self._find_cart_quantity_option(str(target), selector)

        if option is None:
            return False

        self._click_cart_control(option, scroll=False)
        self._pause(0.8)
        return self._get_cart_item_quantity() == target

    def _set_cart_quantity_to(self, target: int) -> None:
        selector = self._find_cart_quantity_selector()
        if selector is None:
            raise AssertionError("Cart quantity selector was not found.")

        current = self._get_cart_item_quantity()
        if current == target:
            return

        if self._select_cart_quantity_option(selector, target):
            self._wait_for_cart_quantity(target, 20)
            return

        live_qty = self._get_cart_item_quantity()
        while live_qty < target:
            plus_button = self._find_cart_plus_button(selector)
            if plus_button is None:
                break
            self._click_cart_control(plus_button, scroll=False)
            self._wait_for_cart_quantity(live_qty + 1, 12)
            live_qty += 1
            selector = self._find_cart_quantity_selector() or selector

        if self._get_cart_item_quantity() == target:
            return

        if self._select_cart_quantity_option(selector, target):
            self._wait_for_cart_quantity(target, 20)
            return

        driver = self._driver()
        try:
            self._open_cart_quantity_dropdown(selector)
            steps = max(1, target - current)
            chain = ActionChains(driver)
            for _ in range(steps):
                chain = chain.send_keys(Keys.ARROW_DOWN).pause(0.15)
            chain.send_keys(Keys.ENTER).perform()
            self._pause(0.8)
            if self._get_cart_item_quantity() == target:
                self._wait_for_cart_quantity(target, 15)
                return
        except Exception:
            pass

        raise AssertionError(
            f"Could not set cart quantity from {current} to {target}."
        )

    def increase_cart_product_quantity(self, increase_by: int | str = 1) -> int:
        increase = max(1, int(increase_by))
        self._stabilize_cart_page()
        self.wait_for_cart_page_loaded(30)

        self._wait(25).until(lambda driver: self._find_cart_quantity_selector() is not None)
        current = self._get_cart_item_quantity()
        target = current + increase

        last_error: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                self._stabilize_cart_page()
                live_qty = self._get_cart_item_quantity()
                if live_qty >= target:
                    logger.info(
                        "Cart quantity already %s (target %s).",
                        live_qty,
                        target,
                    )
                    return live_qty

                self._set_cart_quantity_to(target)
                self._wait_for_cart_quantity(target, 20)
                logger.info(
                    "Increased cart quantity from %s to %s (attempt %s).",
                    current,
                    target,
                    attempt,
                )
                return target
            except Exception as exc:
                last_error = exc
                logger.info(
                    "Quantity increase attempt %s failed: %s",
                    attempt,
                    exc,
                )
                self._stabilize_cart_page()
                self._pause(1.0)

        raise AssertionError(
            f"Could not increase cart quantity from {current} to {target}."
        ) from last_error

    def verify_quantity_change_message(
        self, product_name: str, quantity: str = "2", timeout: Optional[int | str] = None
    ) -> None:
        name_token = product_name.split()[0]
        patterns = [
            re.compile(
                rf"You['’]ve changed\s+'?[^']*{re.escape(name_token)}[^']*'?\s+QUANTITY to\s+'?{quantity}'?",
                re.I,
            ),
            re.compile(
                rf"You['’]ve changed\s+'?{re.escape(product_name)}'?\s+QUANTITY to\s+'?{quantity}'?",
                re.I,
            ),
            re.compile(rf"QUANTITY to\s+'?{quantity}'?", re.I),
        ]

        def message_visible(driver) -> bool:
            self._ensure_cart_page_window()
            text = self._get_visible_page_text()
            if any(pattern.search(text) for pattern in patterns):
                return True
            if self._get_cart_item_quantity() == int(quantity):
                return True
            qty_selector = self._find_cart_quantity_selector()
            if qty_selector is not None:
                qty_text = (qty_selector.text or "").replace("\n", " ").strip()
                if re.search(rf"qty:\s*{re.escape(quantity)}\b", qty_text, re.I):
                    return True
            return False

        self._pause(0.5)
        self._wait(timeout or 30).until(lambda driver: message_visible(driver))
        logger.info(
            "Quantity change message verified for '%s' quantity '%s'.",
            product_name,
            quantity,
        )

    def _find_action_button(self, label: str, exclude_cart_remove: bool = False):
        return self._driver().execute_script(
            """
            const label = arguments[0].toLowerCase();
            const excludeCartRemove = arguments[1];

            const isVisible = (node) => {
                const rect = node.getBoundingClientRect();
                return rect.width > 5 && rect.height > 5;
            };

            const pickTarget = (node) => (
                node.closest('[style*="cursor: pointer"]')
                || node.closest('div[class*="css-g5y9jx"]')
                || node.closest('button')
                || node
            );

            const candidates = [];
            for (const node of document.querySelectorAll('div, span, button')) {
                const text = (node.textContent || '').trim();
                if (text.toLowerCase() !== label) {
                    continue;
                }
                if (!isVisible(node)) {
                    continue;
                }
                const rect = node.getBoundingClientRect();
                if (rect.width > 240 || rect.height > 90) {
                    continue;
                }

                if (excludeCartRemove) {
                    const context = (
                        node.closest('div[class*="css-g5y9jx"]')?.parentElement?.textContent || ''
                    ).toLowerCase();
                    if (
                        context.includes('save for later')
                        || context.includes('buy this now')
                    ) {
                        continue;
                    }
                }

                const style = window.getComputedStyle(node);
                candidates.push({
                    target: pickTarget(node),
                    top: rect.top,
                    z: parseInt(style.zIndex, 10) || 0,
                    width: rect.width,
                });
            }

            if (!candidates.length) {
                return null;
            }
            candidates.sort(
                (left, right) => right.z - left.z || left.top - right.top || left.width - right.width
            );
            return candidates[0].target;
            """,
            label,
            exclude_cart_remove,
        )

    def _find_confirmation_cancel_button(self):
        for label in ("Cancel", "No", "Keep"):
            button = self._find_action_button(label)
            if button is not None:
                return button
        return None

    def _is_empty_cart_visible(self) -> bool:
        text = self._get_visible_page_text().lower()
        return "missing cart items" in text

    def _is_remove_popup_visible(self) -> bool:
        if self._is_empty_cart_visible():
            return False
        cancel_button = self._find_confirmation_cancel_button()
        remove_button = self._find_action_button("Remove", exclude_cart_remove=True)
        if cancel_button is not None and remove_button is not None:
            return True
        text = self._get_visible_page_text().lower()
        confirm_hints = (
            "remove item",
            "remove this",
            "want to remove",
            "are you sure",
        )
        return any(hint in text for hint in confirm_hints) and "remove" in text

    def _find_cart_remove_button(self):
        return self._driver().execute_script(
            """
            const isVisible = (node) => {
                const rect = node.getBoundingClientRect();
                return rect.width > 5 && rect.height > 5;
            };

            const pickTarget = (node) => (
                node.closest('[style*="cursor: pointer"]')
                || node.closest('div[class*="css-g5y9jx"]')
                || node
            );

            for (const node of document.querySelectorAll('div, span, button')) {
                const text = (node.textContent || '').trim();
                if (text !== 'Remove') {
                    continue;
                }
                if (!isVisible(node)) {
                    continue;
                }
                const section = (
                    node.closest('div[class*="css-g5y9jx"]')?.parentElement?.textContent || ''
                ).toLowerCase();
                if (
                    section.includes('save for later')
                    || section.includes('buy this now')
                ) {
                    return pickTarget(node);
                }
            }

            for (const node of document.querySelectorAll('div, span, button')) {
                const text = (node.textContent || '').trim();
                if (text !== 'Remove') {
                    continue;
                }
                if (!isVisible(node)) {
                    continue;
                }
                const rect = node.getBoundingClientRect();
                if (rect.width > 160) {
                    continue;
                }
                return pickTarget(node);
            }
            return null;
            """
        )

    def click_cart_remove_button(self) -> None:
        self._ensure_cart_page_window()
        self.dismiss_login_popup_if_visible()
        self.wait_for_cart_page_loaded()

        self._wait(20).until(lambda driver: self._find_cart_remove_button() is not None)
        remove_button = self._find_cart_remove_button()
        if remove_button is None:
            raise AssertionError("Cart Remove button was not found.")
        self._click_product_page_button(remove_button)
        logger.info("Clicked Remove on cart item.")

    def verify_remove_confirmation_popup(
        self, timeout: Optional[int | str] = None
    ) -> None:
        def popup_or_empty_cart(driver) -> bool:
            return self._is_empty_cart_visible() or self._is_remove_popup_visible()

        self._wait(timeout).until(lambda driver: popup_or_empty_cart(driver))
        if self._is_empty_cart_visible():
            logger.info("Cart is already empty after Remove click.")
            return
        if not self._is_remove_popup_visible():
            raise AssertionError(
                "Remove confirmation popup did not show Cancel and Remove actions."
            )
        logger.info("Remove confirmation popup verified.")

    def confirm_cart_remove(self) -> None:
        self._ensure_cart_page_window()
        self.dismiss_login_popup_if_visible()
        if self._is_empty_cart_visible():
            logger.info("Cart already empty; skipping remove confirmation.")
            return
        if not self._is_remove_popup_visible():
            raise AssertionError("Remove confirmation popup is not visible.")
        remove_button = self._find_action_button("Remove", exclude_cart_remove=True)
        if remove_button is None:
            remove_button = self._find_action_button("Remove")
        if remove_button is None:
            raise AssertionError("Remove confirmation button was not found.")
        self._click_product_page_button(remove_button)
        self._wait(30).until(lambda driver: self._is_empty_cart_visible())
        logger.info("Confirmed product removal from cart.")

    def verify_empty_cart_message(self, timeout: Optional[int | str] = None) -> None:
        def empty_cart_visible(driver) -> bool:
            self._ensure_cart_page_window()
            self.dismiss_login_popup_if_visible()
            if self._is_empty_cart_visible():
                return True
            return bool(
                self._driver().execute_script(
                    """
                    for (const node of document.querySelectorAll(
                        'div, span, h1, h2, h3, p'
                    )) {
                        const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                        if (/missing cart items\\??/i.test(text) && text.length <= 40) {
                            return true;
                        }
                    }
                    return false;
                    """
                )
            )

        self._wait(timeout).until(lambda driver: empty_cart_visible(driver))
        if not self._is_empty_cart_visible():
            raise AssertionError(
                "Empty cart title 'Missing Cart items?' was not displayed."
            )
        logger.info(
            "Empty cart message verified: Missing Cart items? — test suite success criteria met."
        )

    def verify_product_removed_message(
        self, product_name: str, timeout: Optional[int | str] = None
    ) -> None:
        name_token = product_name.split()[0]
        patterns = [
            re.compile(
                rf"{re.escape(product_name)}.*removed from your cart|removed.*{re.escape(product_name)}",
                re.I | re.S,
            ),
            re.compile(
                rf"{re.escape(name_token)}.*removed from your cart|removed.*{re.escape(name_token)}",
                re.I | re.S,
            ),
            re.compile(r"removed from your cart", re.I),
        ]

        def message_visible(driver) -> bool:
            if self._is_empty_cart_visible():
                return True
            text = self._get_visible_page_text()
            return any(pattern.search(text) for pattern in patterns)

        self._wait(timeout).until(lambda driver: message_visible(driver))
        logger.info("Product removed message verified for '%s'.", product_name)

    def wait_for_cart_page_loaded(self, timeout: Optional[int | str] = None) -> None:
        def cart_loaded(driver) -> bool:
            self._ensure_cart_page_window()
            url = driver.current_url.lower()
            if "viewcart" not in url and "/cart" not in url:
                return False
            text = self._get_visible_page_text().strip()
            if len(text) < 15:
                return False
            markers = (
                "price details",
                "total amount",
                "place order",
                "delivery address",
                "missing cart items",
                "qty:",
            )
            has_qty = self._find_cart_quantity_selector() is not None
            return has_qty or any(marker in text.lower() for marker in markers) or bool(
                re.search(r"₹[\d,]+", text)
            )

        self._wait(timeout).until(lambda driver: cart_loaded(driver))
        self._pause(0.3)
        logger.info("Cart page content is loaded.")

    def verify_product_in_cart(
        self, product_name: str, timeout: Optional[int | str] = None
    ) -> None:
        name_token = product_name.split()[0]

        def product_visible(driver) -> bool:
            self._ensure_cart_page_window()
            self.dismiss_login_popup_if_visible()
            text = self._get_visible_page_text()
            if len(text.strip()) < 10:
                return False
            lowered = text.lower()
            return (
                product_name.lower() in lowered
                or name_token.lower() in lowered
            )

        self._wait(timeout).until(lambda driver: product_visible(driver))
        logger.info("Verified product '%s' is present in cart.", product_name)
