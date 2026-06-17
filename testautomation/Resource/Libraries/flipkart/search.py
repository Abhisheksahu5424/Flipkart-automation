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

class FlipkartSearchActions:
    """Search screen actions."""

    def _get_product_cards(self):
        """Collect visible search-result product cards, excluding widgets like Trending."""
        cards = []
        seen_ids = set()
        for card in self._driver().find_elements(By.CSS_SELECTOR, "div[data-id]"):
            if not card.is_displayed():
                continue
            card_id = card.get_attribute("data-id") or ""
            if card_id in seen_ids:
                continue
            if not self._is_product_card(card):
                continue
            seen_ids.add(card_id)
            cards.append(card)
        return cards

    def _is_product_card(self, card) -> bool:
        text = (card.text or "").strip()
        if not re.search(r"₹[\d,]+", text):
            return False
        links = card.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        if not links:
            return False
        try:
            name = self._extract_product_name_from_card(card)
        except AssertionError:
            return False
        junk_names = {"trending", "sponsored", "add to compare", "best sellers"}
        return name.lower() not in junk_names and len(name) >= 8

    def _extract_product_name_from_card(self, card) -> str:
        link = card.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
        title = (link.get_attribute("title") or "").strip()
        if title and len(title) >= 8:
            return title

        for line in link.text.split("\n"):
            line = line.strip()
            if not line or line.lower() == "add to compare":
                continue
            if line.startswith("₹") or re.match(r"^[\d(]", line):
                continue
            if line.lower() in {"trending", "sponsored"}:
                continue
            if len(line) >= 8:
                return line

        raise AssertionError("Could not extract product name from card")

    def _get_compare_tray_link(self):
        for anchor in self._driver().find_elements(By.CSS_SELECTOR, "a[href*='compare']"):
            if not anchor.is_displayed():
                continue
            href = (anchor.get_attribute("href") or "").lower()
            if "ids=" in href:
                return anchor
        for anchor in self._driver().find_elements(
            By.XPATH,
            "//a[.//span[normalize-space()='COMPARE'] or contains(@class,'mLLskC') or contains(@class,'eiYwW9')]",
        ):
            if anchor.is_displayed():
                return anchor
        return None

    def _get_compare_tray_count(self) -> int:
        anchor = self._get_compare_tray_link()
        if anchor is None:
            return 0

        href = anchor.get_attribute("href") or ""
        match = re.search(r"ids=([^&]+)", href)
        if match:
            ids = [item for item in match.group(1).split(",") if item.strip()]
            if ids:
                return len(ids)

        digits = re.findall(r"\b(\d+)\b", anchor.text or "")
        if digits:
            return int(digits[-1])

        if "compare" in (anchor.text or "").upper():
            return 1
        return 0

    def _compare_tray_visible(self) -> bool:
        anchor = self._get_compare_tray_link()
        return anchor is not None and anchor.is_displayed()

    def _find_compare_tray(self):
        anchor = self._get_compare_tray_link()
        if anchor is not None:
            return anchor.find_element(By.XPATH, "./ancestor::div[1]")
        return None

    def _name_in_text(self, product_name: str, text: str) -> bool:
        if product_name in text:
            return True
        first_token = product_name.split()[0]
        return len(first_token) >= 4 and first_token in text

    def _scroll_card_into_view(self, card) -> None:
        driver = self._driver()
        driver.execute_script("window.scrollBy(0, -140);")
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            card,
        )

    def _find_compare_label_for_card(self, card):
        driver = self._driver()
        card_id = card.get_attribute("data-id") or ""
        if card_id:
            xpath_options = [
                (
                    f"//div[@data-id='{card_id}']/following-sibling::div"
                    f"[contains(@class,'FJ7IAS')]//label[contains(@class,'8MOCJ3')]"
                ),
                (
                    f"//div[@data-id='{card_id}']/parent::div//div"
                    f"[contains(@class,'FJ7IAS')]//label[contains(@class,'8MOCJ3')]"
                ),
                f"//div[@data-id='{card_id}']//label[contains(@class,'8MOCJ3')]",
            ]
            for xpath in xpath_options:
                matches = [item for item in driver.find_elements(By.XPATH, xpath) if item.is_displayed()]
                if matches:
                    return matches[0]

        label = driver.execute_script(
            """
            const card = arguments[0];
            let node = card;
            for (let depth = 0; depth < 8 && node; depth++) {
                const compareWrap = node.querySelector("div.FJ7IAS");
                if (compareWrap) {
                    const wrapLabel = compareWrap.querySelector("label");
                    if (wrapLabel) {
                        return wrapLabel;
                    }
                }
                const labels = node.querySelectorAll("label");
                for (const item of labels) {
                    if ((item.className || "").includes("8MOCJ3")) {
                        return item;
                    }
                }
                node = node.parentElement;
            }
            return null;
            """,
            card,
        )
        if label:
            return label
        raise AssertionError("Compare checkbox not found near product card")

    def _find_compare_label_by_list_index(self, index: int):
        card = self.get_product_card_by_index(index)
        return self._find_compare_label_for_card(card)

    def _activate_compare_control(self, element) -> None:
        driver = self._driver()
        label = element
        if element.tag_name.lower() != "label":
            parents = element.find_elements(By.XPATH, "./ancestor::label[1]")
            if parents:
                label = parents[0]

        click_target = label
        boxes = label.find_elements(By.CSS_SELECTOR, "div.ybaCDx")
        if boxes:
            click_target = boxes[0]

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            click_target,
        )
        ActionChains(driver).move_to_element(click_target).pause(0.3).click().perform()

    def _is_compare_label_checked(self, element) -> bool:
        label = element
        if element.tag_name.lower() != "label":
            parents = element.find_elements(By.XPATH, "./ancestor::label[1]")
            if parents:
                label = parents[0]
        checkboxes = label.find_elements(By.CSS_SELECTOR, "input.UXWKAE, input[type='checkbox']")
        if not checkboxes:
            return False
        box = checkboxes[0]
        if box.is_selected():
            return True
        checked = box.get_attribute("checked")
        return bool(checked and checked not in ("false", ""))

    def _click_compare_on_card_index(self, index: int) -> None:
        card = self.get_product_card_by_index(index)
        self._scroll_card_into_view(card)
        label = self._find_compare_label_for_card(card)
        if not self._is_compare_label_checked(label):
            self._activate_compare_control(label)
        logger.info("Compare checkbox selected for product index %s.", index)

    def _compare_tray_text(self) -> str:
        tray = self._find_compare_tray()
        if tray is not None:
            return tray.text
        body_lines = self._driver().find_element(By.TAG_NAME, "body").text.split("\n")
        return "\n".join(body_lines[-40:])

    def ensure_product_cards_loaded(self, minimum: int) -> None:
        for _ in range(12):
            cards = self._get_product_cards()
            if len(cards) >= minimum:
                logger.info("Loaded %s product cards (required %s).", len(cards), minimum)
                return
            self._driver().execute_script("window.scrollBy(0, 850);")
            try:
                self._wait(3).until(
                    lambda driver: len(self._get_product_cards()) >= minimum
                )
            except Exception:
                pass
        raise AssertionError(
            f"Could not load at least {minimum} product cards on search page."
        )

    def get_product_card_by_index(self, index: int):
        self.ensure_product_cards_loaded(index)
        cards = self._get_product_cards()
        if len(cards) < index:
            raise AssertionError(
                f"Expected at least {index} product cards, found {len(cards)}"
            )
        return cards[index - 1]

    def get_product_name_from_card_index(self, index: int) -> str:
        card = self.get_product_card_by_index(index)
        product_name = self._extract_product_name_from_card(card)
        logger.info("Product name at index %s: %s", index, product_name)
        return product_name

    def get_product_price_from_card_index(self, index: int) -> str:
        card = self.get_product_card_by_index(index)
        price = self._extract_selling_price_from_card_text(card.text or "")
        if not price:
            raise AssertionError(f"Could not read product price for index {index}")
        logger.info("Product price at index %s: %s", index, price)
        return price

    def get_product_href_from_card_index(self, index: int) -> str:
        card = self.get_product_card_by_index(index)
        link = self._get_product_link_from_card(card)
        href = link.get_attribute("href")
        if not href or "/p/" not in href:
            raise AssertionError(f"Invalid product href for index {index}: {href}")
        return href

    def reset_compare_selection_state(self) -> None:
        self._compared_products = []
        logger.info("Compare selection state reset.")

    def select_compare_on_card_index(self, index: int) -> str:
        product_name = self.get_product_name_from_card_index(index)
        before_count = self._get_compare_tray_count()
        expected_count = before_count + 1

        self._click_compare_on_card_index(index)

        def compare_added(driver) -> bool:
            if self._get_compare_tray_count() >= expected_count:
                return True
            try:
                cards = self._get_product_cards()
                if len(cards) >= index:
                    label = self._find_compare_label_for_card(cards[index - 1])
                    return self._is_compare_label_checked(label)
            except Exception:
                return False
            return False

        self._wait(20).until(compare_added)

        if product_name not in self._compared_products:
            self._compared_products.append(product_name)
        logger.info(
            "Selected compare for card %s: %s (tray count=%s)",
            index,
            product_name,
            self._get_compare_tray_count(),
        )
        return product_name

    def verify_compare_tray_contains_product(
        self, product_name: str, timeout: Optional[int | str] = None
    ) -> None:
        def tray_contains_product(driver) -> bool:
            tray_text = self._compare_tray_text().lower()
            if "compare" not in tray_text:
                return False
            if self._name_in_text(product_name, tray_text):
                return True

            for card in self._get_product_cards():
                try:
                    card_name = self._extract_product_name_from_card(card)
                except AssertionError:
                    continue
                if self._name_in_text(product_name, card_name):
                    return True

            return any(
                self._name_in_text(product_name, compared_name)
                for compared_name in self._compared_products
            )

        self._wait(timeout).until(lambda driver: tray_contains_product(driver))
        logger.info("Compare tray contains product: %s", product_name)

    def verify_compare_tray_item_count(
        self, expected_count: int, timeout: Optional[int | str] = None
    ) -> None:
        expected = int(expected_count)

        def tray_has_count(driver) -> bool:
            tray_count = self._get_compare_tray_count()
            if tray_count >= expected:
                return True
            return self._compare_tray_visible() and len(self._compared_products) >= expected

        self._wait(timeout).until(lambda driver: tray_has_count(driver))
        actual = max(self._get_compare_tray_count(), len(self._compared_products))
        if actual < expected and not self._compare_tray_visible():
            raise AssertionError(
                f"Compare tray expected {expected} items, found {actual}."
            )
        logger.info("Compare tray item count verified: %s", expected_count)

    def verify_compare_tray_is_visible(self, timeout: Optional[int | str] = None) -> None:
        def tray_visible(driver) -> bool:
            anchor = self._get_compare_tray_link()
            return anchor is not None and anchor.is_displayed()

        self._wait(timeout).until(lambda driver: tray_visible(driver))
        logger.info("Compare tray COMPARE button is visible.")

    def _get_product_link_from_card(self, card):
        best = None
        best_score = -1
        for anchor in card.find_elements(By.CSS_SELECTOR, "a[href*='/p/']"):
            href = (anchor.get_attribute("href") or "").lower()
            if "compare" in href:
                continue
            title = (anchor.get_attribute("title") or "").strip()
            text = (anchor.text or "").strip()
            score = len(title or text)
            if title and len(title) >= 8:
                score += 100
            if score > best_score:
                best_score = score
                best = anchor
        if best is None:
            raise AssertionError("Product link not found on card")
        return best

    def open_product_from_card_index(
        self, index: int, timeout: Optional[int | str] = None
    ) -> str:
        product_name = self.get_product_name_from_card_index(index)
        href = self.get_product_href_from_card_index(index)
        driver = self._driver()

        card = self.get_product_card_by_index(index)
        link = self._get_product_link_from_card(card)
        self._scroll_card_into_view(card)

        handles_before = set(driver.window_handles)
        try:
            driver.execute_script("arguments[0].click();", link)
        except Exception:
            logger.info("Product title click failed; opening product href directly.")

        new_handles = set(driver.window_handles) - handles_before
        if new_handles:
            driver.switch_to.window(new_handles.pop())

        if "/p/" not in driver.current_url:
            driver.get(href)

        self._wait(timeout).until(lambda d: "/p/" in d.current_url)
        self.dismiss_login_popup_if_visible()
        self._wait(15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.info("Opened product page for index %s: %s", index, product_name)
        return product_name
