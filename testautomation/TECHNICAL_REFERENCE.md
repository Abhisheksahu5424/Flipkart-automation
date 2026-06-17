# Flipkart Test Automation — Technical Reference (Deep Dive)

> **Companion to:** [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)  
> **Last updated:** June 2026

---

## Table of Contents

1. [Robot Framework Bootstrap Sequence](#1-robot-framework-bootstrap-sequence)
2. [Complete Keyword API Reference](#2-complete-keyword-api-reference)
3. [Step Call Stack (All 14 Steps)](#3-step-call-stack-all-14-steps)
4. [Session & State Management](#4-session--state-management)
5. [Window & Tab Management](#5-window--tab-management)
6. [Locator Strategy Catalog](#6-locator-strategy-catalog)
7. [Wait & Synchronization Matrix](#7-wait--synchronization-matrix)
8. [BrowserFactory — Chrome Configuration](#8-browserfactory--chrome-configuration)
9. [ProxyManager — Implementation & Known Issues](#9-proxymanager--implementation--known-issues)
10. [FlipkartActions Mixin Architecture](#10-flipkartactions-mixin-architecture)
11. [Search Page — Product Card Heuristics](#11-search-page--product-card-heuristics)
12. [Product Page — CTA Discovery Algorithm](#12-product-page--cta-discovery-algorithm)
13. [Pricing Engine](#13-pricing-engine)
14. [Cart Operations — Quantity & Remove Flow](#14-cart-operations--quantity--remove-flow)
15. [Retry & Fallback Matrix](#15-retry--fallback-matrix)
16. [Suite Variants & Tag Filtering](#16-suite-variants--tag-filtering)
17. [Failure Diagnostics](#17-failure-diagnostics)
18. [Extension Points for Developers](#18-extension-points-for-developers)

---

## 1. Robot Framework Bootstrap Sequence

When `./run_flipkart_tests.sh` executes, the following initialization chain runs:

```
robot CLI
  ├── Creates output dir: Testsuite/
  ├── Injects variables: rbt_env=qa, rbt_usr=Default
  ├── Loads FlipkartTestSuite.robot
  │     ├── RunDefaults.robot          → ${rbt_env}, ${rbt_usr} defaults
  │     ├── TestEnv_qa.robot           → URL, indexes, waits
  │     ├── TestUser_Default.robot     → guest user profile
  │     ├── Common.robot               → SeleniumLibrary + Python libs
  │     ├── Screen/*.robot (×4)        → Page objects
  │     └── TestCases/Flipkart/*.robot → Step keywords
  │
  ├── Python sys.path includes Resource/Libraries/ (implicit via imports)
  ├── GLOBAL-scoped libraries instantiated once per suite:
  │     SeleniumLibrary, BrowserFactory, ProxyManager, WaitUtils,
  │     DataReader, FlipkartActions
  │
  └── Test Case 01 starts
        Test Setup: Set Timestamp
        Steps execute...
        Test Teardown: Take Screenshot On Failure
  ...
  Suite Teardown: Close All Browsers
```

### Resource dependency graph

```mermaid
graph TD
    Suite[FlipkartTestSuite.robot]
    Suite --> RunDefaults
    Suite --> TestEnv[TestEnv_qa.robot]
    Suite --> TestUser[TestUser_Default.robot]
    Suite --> Common
    Suite --> HomePage
    Suite --> SearchPage
    Suite --> ProductPage
    Suite --> CartPage
    Suite --> TC01[01HomePageTC.robot]
    Suite --> TC02[02SearchPageTC.robot]
    Suite --> TC03[03SearchPageProductPageCartPageTC.robot]
    Suite --> TC04[04CartPageTC.robot]

    Common --> BrowserFactory
    Common --> ProxyManager
    Common --> WaitUtils
    Common --> DataReader
    Common --> SeleniumLibrary

    HomePage --> Common
    HomePage --> WaitUtils
    HomePage --> FlipkartActions

    TC01 --> HomePage
    TC02 --> HomePage
    TC02 --> SearchPage
    TC03 --> SearchPage
    TC03 --> ProductPage
    TC03 --> CartPage
    TC04 --> CartPage
```

### Library scope

All custom Python libraries declare:

```python
ROBOT_LIBRARY_SCOPE = "GLOBAL"
```

This means **one instance per test suite** — state on `FlipkartActions` (e.g., `_selected_listing_price`) persists across all 4 test cases within a run.

---

## 2. Complete Keyword API Reference

### 2.1 Common.robot (Infrastructure)

| Keyword | Arguments | Returns | Description |
|---------|-----------|---------|-------------|
| `Set Timestamp` | — | — | Logs epoch timestamp at test start |
| `Open Browser With Proxy` | `${url}`, `${rotate_proxy}=${FALSE}` | — | Loads proxy pool, opens Chrome, registers driver |
| `Wait For Element` | `${locator}`, `${timeout}=${EXPLICIT_WAIT}` | — | Wrapper for `Wait For Element Visible` |
| `Click Element Safely` | `${locator}`, `${timeout}` | — | Scroll + click with retry |
| `Input Text Safely` | `${locator}`, `${text}`, `${timeout}` | — | Clear + type with wait |
| `Scroll Into View` | `${locator}`, `${timeout}` | — | Scroll element to viewport center |
| `Take Screenshot On Failure` | — | — | Saves `Output/Screenshots/failure_{index}.png` |
| `Close Browser Safely` | — | — | Graceful browser close |
| `Log Step` | `${message}` | — | Standardized `*** STEP: ... ***` console log |
| `Run Step With Error Handling` | `${keyword}`, `@{args}` | — | TRY/EXCEPT wrapper with screenshot |

### 2.2 BrowserFactory.py

| Robot Keyword | Python Method | Parameters |
|---------------|---------------|------------|
| `Get Chrome Options` | `get_chrome_options()` | `user_agent`, `incognito=True`, `proxy_config` |
| `Create Chrome Driver` | `create_chrome_driver()` | `url`, `user_agent`, `incognito`, `proxy_config` |
| `Register Driver With SeleniumLibrary` | `register_driver_with_selenium_library()` | `driver` |
| `Open Chrome With Proxy` | `open_chrome_with_proxy()` | `url`, `user_agent`, `incognito`, `rotate_proxy` |

### 2.3 ProxyManager.py

| Robot Keyword | Python Method | Parameters | Returns |
|---------------|---------------|------------|---------|
| `Load Proxy Pool From Environment` | `load_proxy_pool_from_environment()` | — | Pool count (int) |
| `Get Active Proxy Config` | `get_active_proxy_config()` | — | Dict with host/port/scheme/credentials |
| `Rotate Proxy` | `rotate_proxy()` | — | Next proxy config dict |
| `Build Chrome Proxy Argument` | `build_chrome_proxy_argument()` | `proxy_config` | `--proxy-server=...` string |
| `Create Proxy Auth Extension` | `create_proxy_auth_extension()` | host, port, username, password, scheme | Path to `.zip` extension |

### 2.4 WaitUtils.py

| Robot Keyword | Selenium EC Used | Notes |
|---------------|------------------|-------|
| `Wait For Element Visible` | `visibility_of_element_located` | Primary wait for interactions |
| `Wait For Element Clickable` | `element_to_be_clickable` | Pre-click validation |
| `Wait For Element Present` | `presence_of_element_located` | DOM exists, may not be visible |
| `Wait For Text In Element` | `text_to_be_present_in_element` | Element text assertion wait |
| `Wait For Page To Contain` | XPath `//*[contains(., text)]` | Body-level text search |
| `Safe Click Element` | clickable + 3 retries + JS fallback | Handles stale/intercepted clicks |
| `Safe Input Text` | visible + scroll + clear + send_keys | Form input helper |
| `Scroll Locator Into View` | presence + JS scrollIntoView | Viewport positioning |

**Locator prefix parsing:**

| Prefix | Maps to |
|--------|---------|
| `xpath=` | `By.XPATH` |
| `css:` / `css=` | `By.CSS_SELECTOR` |
| `id=` | `By.ID` |
| `//` or `(//` | `By.XPATH` (implicit) |
| *(none)* | `By.CSS_SELECTOR` (default) |

### 2.5 FlipkartActions — Public Methods (via Screen layer)

Robot converts Python `snake_case` methods to `Title Case With Spaces` keywords automatically.

#### Home (`flipkart/home.py`)

| Method | Called From | Behavior |
|--------|-------------|----------|
| `dismiss_login_popup_if_visible()` | HomePage, base helpers | Finds `span[role='button']` close icon; JS click fallback |

#### Search (`flipkart/search.py`)

| Method | Screen Keyword | Returns |
|--------|----------------|---------|
| `ensure_product_cards_loaded(minimum)` | Direct in TC02 | — |
| `get_product_card_by_index(index)` | Internal | WebElement |
| `get_product_name_from_card_index(index)` | Internal | Product name string |
| `get_product_price_from_card_index(index)` | `Get Product Price` | Price string e.g. `₹12,999` |
| `reset_compare_selection_state()` | Step 6 | Clears `_compared_products` list |
| `select_compare_on_card_index(index)` | `Select Product For Compare` | Product name |
| `verify_compare_tray_is_visible(timeout)` | `Verify Compare Tray` | — |
| `verify_compare_tray_item_count(expected, timeout)` | `Verify Compare Tray` | — |
| `open_product_from_card_index(index, timeout)` | `Open Product Details` | Product name |

#### Product (`flipkart/product.py`)

| Method | Screen Keyword | Returns |
|--------|----------------|---------|
| `wait_for_product_page_title(timeout)` | `Verify Product Page Loaded` | — |
| `wait_for_add_to_cart_button(timeout)` | `Add Product To Cart` | — |
| `click_add_to_cart_on_product_page()` | `Add Product To Cart` | — |
| `verify_go_to_cart_button_visible(timeout)` | `Verify Go To Cart Button` | Button text |
| `navigate_to_cart_from_product_page()` | `Navigate To Cart` | — |
| `set_delivery_pincode_if_prompted(pincode)` | Commented out in Screen | bool |

#### Pricing (`flipkart/pricing.py`)

| Method | Screen Keyword | Returns |
|--------|----------------|---------|
| `store_selected_listing_price(price)` | `Get Product Price` | Stored price |
| `get_stored_listing_price()` | `Verify Cart Amount` | Previously stored price |
| `get_cart_total_amount_text()` | `Verify Cart Amount` | Cart total e.g. `₹12,999` |
| `prices_should_be_equal(expected, actual)` | `Verify Cart Amount` | Raises AssertionError on mismatch |
| `normalize_price_value(price)` | Internal | Digits-only string |

#### Cart (`flipkart/cart.py`)

| Method | Screen Keyword | Returns |
|--------|----------------|---------|
| `wait_for_cart_page_loaded(timeout)` | Multiple cart keywords | — |
| `verify_product_in_cart(name, timeout)` | `Verify Product Added To Cart` | — |
| `increase_cart_product_quantity(increase_by)` | `Increase Product Quantity` | New quantity (int) |
| `verify_quantity_change_message(name, qty, timeout)` | `Verify Quantity Update Toast` | — |
| `click_cart_remove_button()` | `Remove Product` | — |
| `verify_remove_confirmation_popup(timeout)` | `Verify Remove Popup` | — |
| `confirm_cart_remove()` | `Confirm Remove Product` | — |
| `verify_product_removed_message(name, timeout)` | `Verify Removed Product Success Message` | — |
| `verify_empty_cart_message(timeout)` | `Verify Empty Cart Message` | — |

### 2.6 DataReader.py (Available but unused in current flow)

| Keyword | Purpose |
|---------|---------|
| `Read Json File` | Load JSON test data |
| `Read Csv File` | Load CSV as list of dicts |
| `Get Environment Variable Or Default` | Env var with fallback |
| `Get Value From Dictionary` | Dict key lookup |

---

## 3. Step Call Stack (All 14 Steps)

### Step 1 — Open Flipkart

```
01HomePageTC.Step 1- Open Flipkart
  └─ HomePage.Open Flipkart Website(${URL})
       └─ Common.Open Browser With Proxy(${URL})
            ├─ ProxyManager.Load Proxy Pool From Environment
            └─ BrowserFactory.Open Chrome With Proxy(${URL}, incognito=True)
                 ├─ ProxyManager.get_active_proxy_config()
                 ├─ get_chrome_options() → Chrome flags + proxy + stealth
                 ├─ webdriver.Chrome(service=Service(), options=...)
                 ├─ _apply_stealth_scripts() → navigator.webdriver = undefined
                 ├─ driver.get(url)
                 └─ register_driver_with_selenium_library(driver)
       └─ WaitUtils.Wait For Element Visible(${LOC_SEARCH_INPUT})
```

### Step 2 — Close Login Popup

```
01HomePageTC.Step 2- Close login popup
  └─ HomePage.Close Login Popup
       ├─ Wait For Element Present(${LOC_LOGIN_MODAL}, 10s)  [optional path]
       ├─ Click Element Safely(${LOC_LOGIN_CLOSE_BTN})
       │    └─ WaitUtils.Safe Click Element (3 retries + JS fallback)
       ├─ FlipkartActions.dismiss_login_popup_if_visible()  [fallback]
       └─ Wait Until Element Is Not Visible(${LOC_LOGIN_MODAL})
```

### Step 3 — Click Search Box

```
02SearchPageTC.Step 3- Click global search module
  └─ HomePage.Click Search Box
       ├─ Wait Until Element Is Not Visible(${LOC_LOGIN_MODAL})  [ignore error]
       └─ Click Element Safely(${LOC_SEARCH_INPUT})
```

### Step 4 — Search with Keyword

```
02SearchPageTC.Step 4- Search with keyword mobile
  ├─ WaitUtils.Safe Input Text(${LOC_SEARCH_INPUT}, ${SEARCH_KEYWORD})
  ├─ Press Keys RETURN
  └─ Wait For Element Present(css:div[data-id])
```

### Step 5 — Verify Search Results

```
02SearchPageTC.Step 5- Verify search results message
  ├─ SearchPage.Verify Search Result Message("Showing 1 – 24 of", "mobile")
  │    ├─ Wait For Page To Contain(pagination_text)
  │    ├─ Wait For Page To Contain(keyword)
  │    └─ Should Contain assertions on body text
  └─ FlipkartActions.ensure_product_cards_loaded(${COMPARE_PRODUCT_INDEX_2})
       └─ Scroll + wait loop until ≥11 cards found (max 12 iterations)
```

### Step 6 — Compare Products 10 & 11

```
03TC.Step 6- Compare 10th and 11th products
  ├─ reset_compare_selection_state()
  ├─ SearchPage.Select Product For Compare(10)
  │    └─ select_compare_on_card_index(10)
  │         ├─ get_product_name_from_card_index(10)
  │         ├─ _click_compare_on_card_index(10)
  │         │    ├─ _scroll_card_into_view(card)
  │         │    ├─ _find_compare_label_for_card(card)  [XPath + JS]
  │         │    └─ _activate_compare_control(label)  [ActionChains click]
  │         └─ WebDriverWait until tray count ≥ expected
  ├─ Verify Compare Tray(product_10, 1)
  ├─ Select Product For Compare(11)
  ├─ Verify Compare Tray(product_11, 2)
  └─ Set Suite Variable ${PRODUCT_NAME} = product_10
```

### Step 7 — Open Product PDP

```
03TC.Step 7- Open 10th product details page
  ├─ Get Product Price(10) → store listing price in ${LISTING_PRICE}
  ├─ Open Product Details(10)
  │    └─ open_product_from_card_index(10)
  │         ├─ JS click on product link OR driver.get(href)
  │         ├─ Switch to new window if opened
  │         └─ Wait until URL contains /p/
  └─ Verify Product Page Loaded(${PRODUCT_NAME})
       └─ Wait Until Location Contains /p/
```

### Step 8 — Add to Cart

```
03TC.Step 8- Add product to cart
  ├─ Add Product To Cart
  │    ├─ wait_for_add_to_cart_button()
  │    └─ click_add_to_cart_on_product_page()
  │         ├─ _scroll_product_page_for_cta()
  │         ├─ _find_add_to_cart_button()  [icon → text → XPath cascade]
  │         ├─ _click_product_page_button(button)
  │         └─ Wait until _is_product_added_or_go_to_cart()
  └─ Verify Go To Cart Button
       └─ verify_go_to_cart_button_visible() → regex match on text
```

### Step 9 — Verify Product in Cart

```
03TC.Step 9- Verify product added to cart
  ├─ Navigate To Cart
  │    └─ navigate_to_cart_from_product_page()
  │         └─ _open_cart_from_product_page()
  │              Strategy order: snackbar → header → PDP CTA → direct URL
  └─ Verify Product Added To Cart(${PRODUCT_NAME})
       └─ verify_product_in_cart() → body text contains product name token
```

### Step 10 — Verify Cart Price

```
03TC.Step 10- Verify cart total amount
  └─ Verify Cart Amount(${LISTING_PRICE})
       ├─ get_cart_total_amount_text()  [parse "Total Amount" section]
       └─ prices_should_be_equal(listing, total)
            └─ normalize_price_value() → strip non-digits, compare
```

### Step 11 — Increase Quantity

```
04TC.Step 11- Increase quantity
  ├─ Increase Product Quantity(${QTY_INCREASE_BY})
  │    └─ increase_cart_product_quantity(2)
  │         ├─ _stabilize_cart_page()
  │         └─ _set_cart_quantity_to(current + 2)  [up to 3 retry attempts]
  │              Strategy: dropdown option → + button → keyboard ARROW_DOWN
  └─ Verify Quantity Update Toast(${PRODUCT_NAME}, ${new_quantity})
```

### Step 12 — Remove Product (Open Popup)

```
04TC.Step 12- Remove product
  ├─ Remove Product → click_cart_remove_button()
  └─ Verify Remove Popup → verify_remove_confirmation_popup()
```

### Step 13 — Confirm Removal

```
04TC.Step 13- Confirm remove
  ├─ Confirm Remove Product → confirm_cart_remove()
  └─ Verify Removed Product Success Message(${PRODUCT_NAME})
```

### Step 14 — Verify Empty Cart (Pass Criteria)

```
04TC.Step 14- Verify empty cart
  └─ CartPage.Verify Empty Cart Message
       └─ verify_empty_cart_message()
            └─ Assert body contains "missing cart items"
                 *** SUITE PASS CRITERION ***
```

---

## 4. Session & State Management

### Browser session lifecycle

```
Test Case 01 ──┐
Test Case 02 ──┤  ONE Chrome WebDriver instance (registered as "default")
Test Case 03 ──┤  Cookies, cart state, open tabs persist between tests
Test Case 04 ──┘
       │
       ▼
Suite Teardown: Close All Browsers
```

### Suite-scoped Robot variables

| Variable | Set In | Used In | Purpose |
|----------|--------|---------|---------|
| `${PRODUCT_NAME}` | Step 6 | Steps 9, 11, 13 | Product added to cart |
| `${LISTING_PRICE}` | Step 7 | Step 10 | Price captured from search listing |

### Python instance state (`FlipkartActions`)

| Attribute | Type | Set By | Used By |
|-------------|------|--------|---------|
| `_selected_listing_price` | `Optional[str]` | `store_selected_listing_price()` | `get_stored_listing_price()`, cart price check |
| `_compared_products` | `list[str]` | `select_compare_on_card_index()` | `verify_compare_tray_contains_product()` fallback |
| `default_timeout` | `int` | `__init__(20)` | All `_wait()` calls |

### Test user profile (guest mode)

```robot
${TEST_USER_NAME}    Default Guest User
${TEST_USER_ROLE}    guest
${USE_LOGIN}         ${FALSE}
```

No authenticated login flow exists. Login popup is **dismissed**, not completed.

---

## 5. Window & Tab Management

Flipkart opens PDP and cart in **new tabs**. The framework handles multi-window state explicitly.

### Product page window selection

```python
# flipkart/base.py → _ensure_product_page_window()
for handle in driver.window_handles:
    driver.switch_to.window(handle)
    if "/p/" in driver.current_url:
        return  # Found PDP tab
```

### Cart page window selection

```python
# flipkart/base.py → _ensure_cart_page_window()
for handle in driver.window_handles:
    if "viewcart" in url or "/cart" in url:
        return  # Found cart tab

# Fallback: construct cart URL from current domain
driver.get(f"{base_url}/viewcart?otracker=Cart_Icon_ViewCart")
```

### Open product flow (Step 7)

```
Search tab (original)
    │
    ├─ JS click product link
    │
    ▼
New tab opens with /p/ URL
    │
    ├─ driver.switch_to.window(new_handle)
    │
    ▼
PDP tab active for Steps 7–8
    │
    ├─ Navigate to cart (Step 9)
    │
    ▼
Cart tab (may be new tab or same tab)
```

### Cart navigation strategy priority (Step 9)

| Priority | Strategy | Detection |
|----------|----------|-----------|
| 1 | Snackbar "Go to cart" link | Text match, not in buy bar |
| 2 | Header cart icon | `a[href*="viewcart"]`, cart count > 0 |
| 3 | PDP "Go to cart" CTA | Icon or text button on product page |
| 4 | Direct URL | `{domain}/viewcart?otracker=Cart_Icon_ViewCart` |

---

## 6. Locator Strategy Catalog

### HomePage.robot

| Variable | Locator | Element |
|----------|---------|---------|
| `${LOC_LOGIN_MODAL}` | `xpath=//div[contains(@class,'RFBkxv')]` | Login overlay container |
| `${LOC_LOGIN_CLOSE_BTN}` | Multi-XPath union | Close button (role=button) |
| `${LOC_SEARCH_INPUT}` | `xpath=//input[@name='q' ...]` | Global search input |
| `${LOC_SEARCH_SUBMIT}` | Button with class/aria-label | Search submit (unused; Enter key used) |

### SearchPage.robot

| Variable | Locator | Element |
|----------|---------|---------|
| `${LOC_SEARCH_RESULTS_TEXT}` | XPath with `results for` + keyword | Search summary line |

**Dynamic card locators (Python):**

| Selector | Purpose |
|----------|---------|
| `div[data-id]` | Product card root |
| `a[href*='/p/']` | Product detail link |
| `label.8MOCJ3` / `div.FJ7IAS` | Compare checkbox wrapper |
| `a[href*='compare']` with `ids=` | Compare tray link |

### ProductPage.robot

| Variable | Locator | Element |
|----------|---------|---------|
| `${LOC_PRODUCT_TITLE}` | Multi-XPath: `B_NuCI`, `yhB1nd`, `VU-ZEz` | Product title |
| `${LOC_ADD_TO_CART_BTN}` | Normalized text XPath | Text-based Add to Cart |
| `${LOC_GO_TO_CART_BTN}` | Normalized text XPath | Go/Going to cart |
| `${LOC_PRODUCT_PRICE}` | First `₹` element | Fallback price |

**Primary PDP CTA discovery uses JavaScript**, not these XPath locators, due to Flipkart's icon-based buy bar.

### CartPage.robot

| Variable | Locator | Element |
|----------|---------|---------|
| `${LOC_CART_QTY_SELECTOR}` | `contains(normalize-space(.),'Qty:')` | Quantity dropdown |
| `${LOC_CART_PLUS_BTN}` | `button[normalize-space(.)='+']` | Increment button |
| `${LOC_CART_REMOVE_LINK}` | `div[normalize-space(.)='Remove']` | Remove link |
| `${LOC_EMPTY_CART_TITLE}` | Contains `missing cart items` | Empty cart heading |

---

## 7. Wait & Synchronization Matrix

### Global wait configuration

| Setting | Value | Location |
|---------|-------|----------|
| Implicit wait | `0 seconds` | Set in `Common.Open Browser With Proxy` |
| SeleniumLibrary timeout | `${EXPLICIT_WAIT}` (20s) | Common.robot |
| Python default timeout | `20` seconds | FlipkartBase, WaitUtils |

### Wait types by layer

| Layer | Mechanism | Example |
|-------|-----------|---------|
| Robot | `Wait Until ...` keywords | `Wait Until Location Contains /p/` |
| WaitUtils | Selenium EC + WebDriverWait | `visibility_of_element_located` |
| FlipkartActions | Custom lambda conditions | `cart_ready()`, `tray_visible()` |
| Hard sleep | `time.sleep()` / `Sleep` | `_pause(0.4)` after scroll/click |

### Critical custom wait conditions

| Condition Function | Waits For | Timeout |
|-------------------|-----------|---------|
| `ensure_product_cards_loaded(n)` | ≥ n product cards in DOM | 3s per scroll × 12 iterations |
| `compare_added()` | Compare tray count incremented OR checkbox checked | 20s |
| `add_to_cart_visible()` | Add to cart button found via JS/XPath | 30s |
| `_is_product_added_or_go_to_cart()` | Header cart count++, "Going to cart" text, or GoToCart clipPath | 30s |
| `cart_loaded()` | URL has viewcart + price/qty markers | 20–30s |
| `quantity_reached(expected)` | Qty selector shows target number | 12–20s |
| `empty_cart_visible()` | "Missing Cart items?" in body | 20s |

---

## 8. BrowserFactory — Chrome Configuration

### Full Chrome argument list

| Argument / Option | Purpose |
|-------------------|---------|
| `--incognito` | Clean session, no persisted cookies |
| `--start-maximized` | Full viewport |
| `--disable-notifications` | Block notification prompts |
| `--disable-popup-blocking` | Allow popups (cart snackbar) |
| `--disable-infobars` | Hide info bars |
| `--no-sandbox` | Required for some Linux/CI environments |
| `--disable-dev-shm-usage` | Prevent /dev/shm exhaustion in containers |
| `--disable-blink-features=AutomationControlled` | Reduce automation fingerprint |
| `--user-agent={UA}` | Custom or default Chrome 122 UA |
| `--proxy-server={url}` | Optional proxy (when configured) |
| `excludeSwitches: ["enable-automation"]` | Remove automation switch |
| `useAutomationExtension: False` | Disable automation extension |

### CDP stealth injection

Executed on every new document via `Page.addScriptToEvaluateOnNewDocument`:

```javascript
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
```

### Driver registration pattern

SeleniumLibrary normally creates its own driver via `Open Browser`. This project **bypasses that** by:

1. Creating a custom `webdriver.Chrome()` in `BrowserFactory`
2. Injecting it: `selenium_library.register_driver(driver, "default")`
3. All subsequent SeleniumLibrary and FlipkartActions calls use this driver

---

## 9. ProxyManager — Implementation & Known Issues

### Environment variable resolution order

```
_resolve_proxy_config()
  1. self._proxy_pool[rotation_index]   ← if pool loaded
  2. PROXY_URL env var                  ← e.g. http://host:8080
  3. PROXY_HOST + PROXY_PORT env vars
  4. None → no proxy
```

### Supported env vars

| Variable | Format | Example |
|----------|--------|---------|
| `PROXY_HOST` | hostname | `proxy.example.com` |
| `PROXY_PORT` | port number | `8080` |
| `PROXY_SCHEME` | protocol | `http` (default) |
| `PROXY_USERNAME` | auth user | `myuser` |
| `PROXY_PASSWORD` | auth pass | `mypass` |
| `PROXY_URL` | full URL | `http://user:pass@host:8080` |
| `PROXY_POOL` | comma-separated | `host1:8080,user:pass@host2:8080` |

### Authenticated proxy extension

Chrome cannot pass proxy credentials via CLI. For authenticated proxies, a **Manifest V2** ZIP extension is generated at runtime:

```
flipkart_proxy_ext_XXXXX/
  └── proxy_auth_extension.zip
        ├── manifest.json    (permissions: proxy, webRequest, webRequestBlocking)
        └── background.js    (chrome.proxy.settings + onAuthRequired listener)
```

### Known issue: dual ProxyManager instances

```
Common.robot
  └─ ProxyManager (Robot library instance A)
       └─ Load Proxy Pool From Environment  ← pool loaded HERE

BrowserFactory
  └─ self._proxy_manager = ProxyManager()  ← separate instance B
       └─ get_active_proxy_config()        ← used for Chrome startup
```

**Impact:**

| Config Method | Works? |
|---------------|--------|
| `PROXY_HOST` + `PROXY_PORT` | Yes (both read os.environ) |
| `PROXY_URL` | Yes |
| `PROXY_POOL` | **No** (pool loaded on A, Chrome uses B) |
| `Rotate Proxy` | **No** (unless fixed) |

**Fix:** Replace `self._proxy_manager = ProxyManager()` with `BuiltIn().get_library_instance("ProxyManager")` in `BrowserFactory.__init__`.

---

## 10. FlipkartActions Mixin Architecture

### Class composition (C3 MRO)

```python
FlipkartActions(
    FlipkartBase,           # MRO priority: first match wins
    FlipkartHomeActions,
    FlipkartSearchActions,
    FlipkartPricingActions,
    FlipkartProductActions,
    FlipkartCartActions,
)
```

```mermaid
classDiagram
    class FlipkartActions {
        +ROBOT_LIBRARY_SCOPE = GLOBAL
    }
    class FlipkartBase {
        -_selected_listing_price
        -_compared_products
        +_driver()
        +_wait()
        +_ensure_product_page_window()
        +_ensure_cart_page_window()
        +_stabilize_cart_page()
    }
    class FlipkartHomeActions {
        +dismiss_login_popup_if_visible()
    }
    class FlipkartSearchActions {
        +ensure_product_cards_loaded()
        +select_compare_on_card_index()
        +open_product_from_card_index()
    }
    class FlipkartPricingActions {
        +store_selected_listing_price()
        +get_cart_total_amount_text()
        +prices_should_be_equal()
    }
    class FlipkartProductActions {
        +click_add_to_cart_on_product_page()
        +navigate_to_cart_from_product_page()
    }
    class FlipkartCartActions {
        +increase_cart_product_quantity()
        +confirm_cart_remove()
        +verify_empty_cart_message()
    }

    FlipkartActions --|> FlipkartBase
    FlipkartActions --|> FlipkartHomeActions
    FlipkartActions --|> FlipkartSearchActions
    FlipkartActions --|> FlipkartPricingActions
    FlipkartActions --|> FlipkartProductActions
    FlipkartActions --|> FlipkartCartActions
    FlipkartHomeActions --|> FlipkartBase : implicit via MRO
    FlipkartSearchActions --|> FlipkartBase : uses _driver, _wait
```

### Driver access pattern

All mixins access the WebDriver through SeleniumLibrary — never store a driver reference:

```python
def _driver(self):
    return BuiltIn().get_library_instance("SeleniumLibrary").driver
```

This ensures a single driver instance regardless of which mixin method is called.

---

## 11. Search Page — Product Card Heuristics

### Card collection algorithm

```python
# _get_product_cards()
for card in driver.find_elements(By.CSS_SELECTOR, "div[data-id]"):
    if card.is_displayed()
    and card_id not in seen_ids
    and _is_product_card(card):
        cards.append(card)
```

### Product card validation (`_is_product_card`)

A `div[data-id]` element qualifies as a product card if **all** conditions pass:

| Check | Rule |
|-------|------|
| Price present | Text matches `₹[\d,]+` |
| Product link | Has `a[href*='/p/']` |
| Name extractable | `_extract_product_name_from_card()` succeeds |
| Name length | ≥ 8 characters |
| Not junk | Name not in `{trending, sponsored, add to compare, best sellers}` |

### Product name extraction priority

1. `link.get_attribute("title")` if length ≥ 8
2. First text line from link that isn't price, "Add to compare", or junk label
3. Raise `AssertionError` if none found

### Compare checkbox location strategy

For card at index N:

1. XPath by `data-id` sibling/parent traversal for `label.8MOCJ3`
2. JavaScript DOM walk up to 8 parent levels searching `div.FJ7IAS`
3. Raise if not found

### Lazy loading handler

```python
# ensure_product_cards_loaded(minimum)
for _ in range(12):
    if len(cards) >= minimum: return
    scrollBy(0, 850)
    wait up to 3s
raise AssertionError
```

Default requires **11 cards** loaded (for compare index 11).

---

## 12. Product Page — CTA Discovery Algorithm

Flipkart PDP uses **SVG icon buttons** in a bottom buy action bar instead of stable text buttons.

### Add to Cart discovery cascade

```
_find_add_to_cart_button()
  │
  ├─ 1. _scroll_product_page_for_cta()
  │
  ├─ 2. _find_pdp_icon_cart_button("add")
  │      └─ JS: find clipPath[id*="AddToCart"] → SVG → buy bar icon
  │
  ├─ 3. _find_pdp_text_cta("add")
  │      └─ JS: text matches /^add\s*to\s*cart$/i
  │
  └─ 4. XPath fallbacks (5 patterns)
         └─ div/button with normalized "add to cart" text
```

### Icon button validation rules (JavaScript)

| Rule | Purpose |
|------|---------|
| Has SVG child | Icon-based button |
| Visible (width > 10, height > 10) | Not hidden |
| Not wishlist (aria-label, clipPath id, position) | Avoid heart icon |
| In buy action bar (contains "buy now" row, bottom > 72% viewport) | Correct button row |
| Width 24–140px, height < 110px | Size constraints |
| Own text doesn't contain buy/emi/₹/wish | Not a text CTA |

### Add-to-cart success detection

```python
_is_product_added_or_go_to_cart(cart_count_before):
  - Page text matches "go(ing) to cart" or "added to cart/bag"
  - Header cart count > cart_count_before
  - clipPath[id*="GoToCart"] exists in DOM
  - Go-to-cart icon button found with matching aria-label
```

---

## 13. Pricing Engine

### Price extraction pipeline

```
Raw page/card text
  │
  ├─ _extract_non_emi_prices()
  │    └─ Find ₹[\d,]+ but EXCLUDE if nearby text has: month, /mo, emi, per mo
  │
  ├─ Filter lines containing: exchange, bank offer, protect, fee
  │
  ├─ Filter amounts < ₹200 (for page-level extraction)
  │
  └─ _get_selling_price_from_prices()
       └─ Return MIN price (selling price = lowest non-EMI price)
```

### Price comparison (Step 10)

```python
def prices_should_be_equal(expected, actual):
    expected_digits = re.sub(r"[^\d]", "", expected)  # "12999"
    actual_digits   = re.sub(r"[^\d]", "", actual)    # "12999"
    assert expected_digits == actual_digits
```

**Note:** Compares **listing page price** (search card) vs **cart Total Amount**, not per-unit × quantity. After quantity increase (Step 11), total will differ — Step 10 runs before qty change.

### Cart total extraction

1. Find "Price Details" section in body text
2. Regex: `Total\s+Amount[\s\S]{0,80}?₹\s*([\d,]+)`
3. JavaScript fallback scans line-by-line after "Total Amount" label
4. Returns last matched total (handles multiple ₹ values in section)

---

## 14. Cart Operations — Quantity & Remove Flow

### Quantity increase algorithm

```
increase_cart_product_quantity(increase_by=2)
  │
  ├─ _stabilize_cart_page()
  ├─ current = _get_cart_item_quantity()    ← parse "Qty: N" text
  ├─ target = current + increase_by
  │
  └─ _set_cart_quantity_to(target)  [up to 3 outer retries]
       │
       ├─ Strategy A: Open dropdown → select exact quantity option
       ├─ Strategy B: Click '+' button repeatedly until target
       ├─ Strategy C: Keyboard ARROW_DOWN + ENTER on dropdown
       │
       └─ _wait_for_cart_quantity(target)
```

### Remove flow state machine

```mermaid
stateDiagram-v2
    [*] --> CartWithItem
    CartWithItem --> RemoveClicked: click_cart_remove_button()
    RemoveClicked --> ConfirmPopup: verify_remove_confirmation_popup()
    RemoveClicked --> AlreadyEmpty: cart emptied instantly
    ConfirmPopup --> ConfirmClicked: confirm_cart_remove()
    ConfirmClicked --> EmptyCart: verify_empty_cart_message()
    AlreadyEmpty --> EmptyCart
    EmptyCart --> [*]: PASS
```

### Empty cart detection

Primary: case-insensitive `"missing cart items"` in `document.body.innerText`

Secondary JS scan: elements with text matching `/missing cart items?/i` and length ≤ 40

---

## 15. Retry & Fallback Matrix

| Operation | Retries | Fallback Strategy |
|-----------|---------|-------------------|
| Safe click (WaitUtils) | 3 | JavaScript `element.click()` |
| Login close (HomePage) | 1 | `dismiss_login_popup_if_visible()` Python fallback |
| Product card loading | 12 scrolls | 850px scroll + 3s wait each |
| Compare checkbox click | 1 | ActionChains → implicit in `_activate_compare_control` |
| Open product link | 1 | `driver.get(href)` direct navigation |
| Add to cart click | 1 | ActionChains → JS click via `_click_product_page_button` |
| Cart navigation | 4 strategies | snackbar → header → PDP → direct URL |
| Quantity set | 3 outer attempts | dropdown → + button → keyboard |
| Quantity increase (cart) | 3 attempts | Full re-stabilize between attempts |
| Cart remove click | 1 | ActionChains → JS click |

---

## 16. Suite Variants & Tag Filtering

### Suite comparison

| Property | FlipkartTestSuite | FlipkartSmokeTestSuite | FlipkartRegressionTestSuite |
|----------|-------------------|------------------------|----------------------------|
| Force Tags | — | `smoke` | `regression` |
| Test case tags | smoke + regression + e2e | homepage, searchpage, etc. | e2e + screen tags |
| Output files | log.html, report.html | smoke_log.html, smoke_report.html | regression_log.html, regression_report.html |
| `--include` filter | None (runs all) | `--include smoke` | `--include regression` |
| Test logic | Identical 14 steps | Identical 14 steps | Identical 14 steps |

### Tag hierarchy

```
flipkart (all tests)
  ├── e2e
  ├── smoke        ← used by smoke runner
  ├── regression   ← used by regression runner
  ├── homepage
  ├── searchpage
  ├── productpage
  └── cartpage
```

### Reusable flow keyword

`FlipkartFlow.robot` exposes `Execute Flipkart Mobile Purchase Flow` — runs all 14 steps as a single keyword (not used by current suites but available for custom tests).

---

## 17. Failure Diagnostics

### Automatic artifacts

| Trigger | Output |
|---------|--------|
| Any test failure | `Output/Screenshots/failure_{index}.png` |
| Robot run | `Testsuite/log.html` (step-level trace) |
| Robot run | `Testsuite/report.html` (summary) |
| Robot run | `Testsuite/output.xml` (CI/JUnit integration) |

### Common failure points

| Symptom | Likely Cause | Check |
|---------|--------------|-------|
| Step 5 fails | Search results layout changed | Pagination text "Showing 1 – 24 of" |
| Step 6 fails | < 11 products loaded | Increase scroll in `ensure_product_cards_loaded` |
| Step 6 fails | Compare checkbox moved | Update `FJ7IAS` / `8MOCJ3` class selectors |
| Step 7 fails | Product index out of range | Adjust `${CART_PRODUCT_INDEX}` in TestEnv |
| Step 8 fails | Icon cart layout changed | Update `_find_pdp_icon_cart_button` JS |
| Step 10 fails | Price mismatch | Listing price vs cart total (fees, offers) |
| Step 11 fails | Qty dropdown changed | Update `_find_cart_quantity_selector` JS |
| Step 14 fails | Empty cart message changed | Update `_is_empty_cart_visible` text check |
| Login/captcha | Bot detection | Stealth flags, proxy, slower execution |

### Log messages to search for

```
*** STEP: ... ***                          ← Step boundaries
Incognito mode enabled.                    ← Browser mode
Applied anti-automation stealth scripts.   ← Stealth active
Loaded N product cards (required M).       ← Search page ready
Compare checkbox selected for product index N.
Clicked Add to cart icon/button on product page.
Navigated to cart from product page via snackbar/header/pdp/direct.
Increased cart quantity from X to Y.
Empty cart message verified: Missing Cart items?
```

---

## 18. Extension Points for Developers

### Add a new test step

1. Add keyword to appropriate `Resource/TestCases/Flipkart/XXTC.robot`
2. If new page interaction needed, add method to relevant `flipkart/*.py` mixin
3. Expose via `Resource/Screen/XPage.robot` keyword
4. Wire into `Testsuite/FlipkartTestSuite.robot`

### Add a new page object

```
Resource/Screen/WishlistPage.robot     ← locators + page keywords
Resource/Libraries/flipkart/wishlist.py ← FlipkartWishlistActions mixin
Resource/Libraries/flipkart/actions.py    ← add to inheritance list
```

### Add data-driven tests

`DataReader.py` is already imported in `Common.robot`:

```robot
${data}=    Read Json File    Resource/TestData/products.json
${keyword}=    Get Value From Dictionary    ${data}    search_keyword
```

### Enable headless CI

In `BrowserFactory.get_chrome_options()`:

```python
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
```

### Fix proxy pool support

In `BrowserFactory.__init__`:

```python
from robot.libraries.BuiltIn import BuiltIn

def __init__(self):
    try:
        self._proxy_manager = BuiltIn().get_library_instance("ProxyManager")
    except Exception:
        self._proxy_manager = ProxyManager()
```

---

## Appendix A — Environment Variable Reference

| Variable | Used By | Default |
|----------|---------|---------|
| `PROXY_HOST` | ProxyManager | — |
| `PROXY_PORT` | ProxyManager | — |
| `PROXY_SCHEME` | ProxyManager | `http` |
| `PROXY_USERNAME` | ProxyManager | — |
| `PROXY_PASSWORD` | ProxyManager | — |
| `PROXY_URL` | ProxyManager | — |
| `PROXY_POOL` | ProxyManager | — |
| `BROWSER_USER_AGENT` | BrowserFactory | Chrome 122 Linux UA |

## Appendix B — TestEnv_qa.robot Variable Reference

| Variable | Default | Consumed By |
|----------|---------|-------------|
| `${URL}` | `https://www.flipkart.com` | Step 1 |
| `${SEARCH_KEYWORD}` | `mobile` | Steps 4, 5 |
| `${DELIVERY_PINCODE}` | `560103` | Commented out in Screen files |
| `${COMPARE_PRODUCT_INDEX_1}` | `10` | Step 6 |
| `${COMPARE_PRODUCT_INDEX_2}` | `11` | Step 6 |
| `${CART_PRODUCT_INDEX}` | `10` | Steps 7, 8 |
| `${QTY_INCREASE_BY}` | `2` | Step 11 |
| `${EXPLICIT_WAIT}` | `20s` | All wait keywords |
| `${SHORT_WAIT}` | `10s` | Available, rarely used |

## Appendix C — File Inventory

| File | Lines (approx) | Role |
|------|----------------|------|
| `flipkart/search.py` | 418 | Largest module — card/compare logic |
| `flipkart/product.py` | 618 | PDP CTA discovery (most complex JS) |
| `flipkart/cart.py` | 700 | Cart qty/remove/empty state |
| `flipkart/pricing.py` | 254 | Price parsing engine |
| `flipkart/base.py` | 168 | Shared browser/window helpers |
| `flipkart/home.py` | 35 | Login popup only |
| `BrowserFactory.py` | 149 | Chrome bootstrap |
| `ProxyManager.py` | 268 | Proxy config + auth extension |
| `WaitUtils.py` | 208 | Explicit wait wrappers |

---

*For overview and presentation script, see [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).*
