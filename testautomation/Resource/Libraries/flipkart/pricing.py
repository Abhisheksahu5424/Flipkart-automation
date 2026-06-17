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

class FlipkartPricingActions:
    """Pricing screen actions."""

    def _extract_non_emi_prices(self, text: str) -> list[str]:
        prices: list[str] = []
        for match in re.finditer(r"₹\s*([\d,]+)", text or ""):
            start, end = match.span()
            window = text[max(0, start - 12) : min(len(text), end + 18)].lower()
            if any(token in window for token in ("month", "/mo", "emi", "per mo")):
                continue
            prices.append(f"₹{match.group(1)}")
        return prices

    def _get_selling_price_from_prices(self, prices: list[str]) -> str:
        if not prices:
            raise AssertionError("No product prices were found.")
        if len(prices) == 1:
            return prices[0]
        values = [int(self.normalize_price_value(price)) for price in prices[:4]]
        return f"₹{min(values)}"

    def _extract_selling_price_from_card_text(self, text: str) -> Optional[str]:
        for line in (text or "").split("\n"):
            line = line.strip()
            if not line or re.search(r"exchange|off with|bank offer", line, re.I):
                continue
            prices = self._extract_non_emi_prices(line)
            if prices:
                return self._get_selling_price_from_prices(prices)
        prices = self._extract_non_emi_prices(text or "")
        if prices:
            return self._get_selling_price_from_prices(prices)
        return None

    def _extract_selling_price_from_page_text(self, text: str) -> Optional[str]:
        amounts: list[int] = []
        for line in (text or "").split("\n"):
            line = line.strip()
            if not line or re.search(
                r"exchange|off with|bank offer|emi|/mo|protect|fee",
                line,
                re.I,
            ):
                continue
            for price in self._extract_non_emi_prices(line):
                amount = int(self.normalize_price_value(price))
                if amount >= 200:
                    amounts.append(amount)
        if not amounts:
            return None
        selling = min(amounts)
        return f"₹{selling:,}"

    def get_product_page_selling_price(self) -> str:
        self._ensure_product_page_window()
        self.dismiss_login_popup_if_visible()
        self._scroll_product_page_for_cta()
        text = self._get_visible_page_text()
        price = self._extract_selling_price_from_page_text(text[:4000])
        if not price:
            raise AssertionError("Product page selling price was not found.")
        self.store_selected_listing_price(price)
        logger.info("Product page selling price: %s", price)
        return price

    def normalize_price_value(self, price: str) -> str:
        return re.sub(r"[^\d]", "", price or "")

    def prices_should_be_equal(self, expected_price: str, actual_price: str) -> None:
        expected = self.normalize_price_value(expected_price)
        actual = self.normalize_price_value(actual_price)
        if expected != actual:
            raise AssertionError(
                f"Prices do not match. Expected '{expected_price}', got '{actual_price}'"
            )

    def _get_price_details_section_text(self) -> str:
        text = self._get_visible_page_text()
        match = re.search(r"price\s+details", text, re.I)
        if match:
            return text[match.start() :]
        return text

    def _get_cart_line_price(self, prices: list[str]) -> str:
        values = [
            (int(self.normalize_price_value(price)), price)
            for price in prices
            if int(self.normalize_price_value(price)) >= 100
        ]
        if not values:
            raise AssertionError("Cart item price was not found on cart page.")
        return min(values, key=lambda item: item[0])[1]

    def get_cart_item_price_text(self, product_name: str = "") -> str:
        price = self._driver().execute_script(
            """
            const productToken = (arguments[0] || '').split(/\s+/)[0].toLowerCase();

            const parseAmount = (value) => {
                const digits = String(value || '').replace(/[^\d]/g, '');
                return digits ? parseInt(digits, 10) : 0;
            };

            const isFeeLine = (line) => /protect|promise fee|delivery fee|handling/i.test(line);

            const collectPrices = (root) => {
                const amounts = [];
                const text = (root && root.innerText) || '';
                for (const line of text.split('\\n')) {
                    const trimmed = line.trim();
                    if (!trimmed || isFeeLine(trimmed)) {
                        continue;
                    }
                    const match = trimmed.match(/₹\\s*([\\d,]+)/);
                    if (!match || trimmed.length > 50) {
                        continue;
                    }
                    const amount = parseAmount(match[1]);
                    if (amount >= 200) {
                        amounts.push(amount);
                    }
                }
                return amounts;
            };

            let rowContainer = null;
            for (const anchor of document.querySelectorAll('a[href*="/p/"]')) {
                const anchorText = (anchor.textContent || '').toLowerCase();
                if (productToken && !anchorText.includes(productToken)) {
                    continue;
                }
                let current = anchor;
                for (let depth = 0; depth < 10 && current; depth += 1) {
                    const blockText = (current.innerText || '').toLowerCase();
                    if (blockText.includes('qty:') && blockText.includes('₹')) {
                        rowContainer = current;
                        break;
                    }
                    current = current.parentElement;
                }
                if (rowContainer) {
                    break;
                }
            }

            let amounts = collectPrices(rowContainer);
            if (!amounts.length) {
                const pageText = (document.body.innerText || '').split('Price Details')[0];
                for (const line of pageText.split('\\n')) {
                    const trimmed = line.trim();
                    if (!trimmed || isFeeLine(trimmed)) {
                        continue;
                    }
                    const match = trimmed.match(/₹\\s*([\\d,]+)/);
                    if (!match || trimmed.length > 50) {
                        continue;
                    }
                    const amount = parseAmount(match[1]);
                    if (amount >= 200) {
                        amounts.push(amount);
                    }
                }
            }

            if (!amounts.length) {
                return null;
            }

            const selling = Math.min(...amounts);
            return `₹${selling.toLocaleString('en-IN')}`;
            """,
            product_name,
        )
        if not price:
            raise AssertionError("Cart item price was not found on cart page.")
        logger.info("Cart item price: %s", price)
        return price

    def get_cart_total_amount_text(self) -> str:
        section = self._get_price_details_section_text()
        total = self._driver().execute_script(
            """
            const section = arguments[0] || '';
            const matches = [
                ...section.matchAll(/Total\\s+Amount[\\s\\S]{0,80}?₹\\s*([\\d,]+)/gi),
            ];
            if (matches.length) {
                return matches[matches.length - 1][1];
            }

            const lines = section.split('\\n');
            for (let index = 0; index < lines.length; index += 1) {
                if (!/total\\s+amount/i.test(lines[index])) {
                    continue;
                }
                for (
                    let offset = 0;
                    offset < 4 && index + offset < lines.length;
                    offset += 1
                ) {
                    const match = lines[index + offset].match(/₹\\s*([\\d,]+)/);
                    if (match) {
                        return match[1];
                    }
                }
            }
            return null;
            """,
            section,
        )
        if total:
            amount = f"₹{total}"
            logger.info("Cart Total Amount: %s", amount)
            return amount

        match = re.search(
            r"Total\s+Amount[\s\S]{0,80}?₹\s*([\d,]+)", section, re.I
        )
        if match:
            amount = f"₹{match.group(1)}"
            logger.info("Cart Total Amount: %s", amount)
            return amount

        raise AssertionError("Total Amount was not found on cart page")

    def store_selected_listing_price(self, price: str) -> str:
        self._selected_listing_price = price
        logger.info("Stored listing price: %s", price)
        return price

    def get_stored_listing_price(self) -> str:
        if not self._selected_listing_price:
            raise AssertionError("Listing price has not been stored yet.")
        return self._selected_listing_price
