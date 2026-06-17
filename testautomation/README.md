# Flipkart Test Automation

Robot Framework end-to-end tests for [Flipkart](https://www.flipkart.com): search, compare, add to cart, cart updates, and remove flow.

## Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | Architecture overview and 10-minute project walkthrough |
| [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) | Deep dive: call stacks, keyword API, algorithms, troubleshooting |

---

## Quick start

```bash
# 1. Clone or copy the project
cd testautomation

# 2. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install a browser (Chrome recommended — see Prerequisites below)

# 5. Run tests
chmod +x run_flipkart_tests.sh
./run_flipkart_tests.sh
```

Reports are written under `Testsuite/` (`log.html`, `report.html`).

---

## Will `pip install -r requirements.txt` be enough?

**No — not by itself.** `requirements.txt` only installs Python packages. You also need:

| Requirement | Required? | Notes |
|-------------|-----------|--------|
| **Python 3.9+** | Yes | Tested with Robot Framework 7 |
| **Browser** | Yes | Chrome (default), Firefox, or Edge — see [Browser selection](#browser-selection) |
| **WebDriver** | Usually automatic | Selenium 4 downloads a matching driver via Selenium Manager on first run |
| **Internet access** | Yes | Tests hit `https://www.flipkart.com` live |
| **Display / desktop session** | Yes* | Browser runs **headed** (visible window). On Linux servers use a display (`DISPLAY`) or adapt for headless |
| **Proxy** | No | Optional; see [Optional proxy](#optional-proxy) |

There is **no `.env` file or database** to configure for the default flow. Test data (search keyword, product indexes, pincode) lives in `Resource/TestEnv/TestEnv_qa.robot`.

\* For CI/headless servers you may need extra browser flags or code changes; the default setup expects a normal desktop environment.

---

## Prerequisites

### Linux (Ubuntu/Debian example)

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv wget

# Google Chrome (recommended — default browser)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Optional: Firefox or Edge
sudo apt install -y firefox
# Edge: install from Microsoft package repository for your distro
```

### macOS

```bash
brew install python@3.11
brew install --cask google-chrome
# Optional:
brew install --cask firefox
brew install --cask microsoft-edge
```

### Windows

- Install [Python 3](https://www.python.org/downloads/)
- Install [Google Chrome](https://www.google.com/chrome/) (or Firefox / Edge)

---

## Running tests

| Script | Suite | Purpose |
|--------|--------|---------|
| `./run_flipkart_tests.sh` | `FlipkartTestSuite.robot` | Full E2E (4 tests, sequential browser session) |
| `./run_flipkart_smoke_tests.sh` | `FlipkartSmokeTestSuite.robot` | Smoke-tagged run |
| `./run_flipkart_regression_tests.sh` | `FlipkartRegressionTestSuite.robot` | Regression-tagged run |

Manual run with custom environment:

```bash
robot --outputdir Testsuite \
  --variable rbt_env:qa \
  --variable rbt_usr:Default \
  --variable browser:chrome \
  Testsuite/FlipkartTestSuite.robot
```

### Test flow (4 test cases)

1. **HomePage** — open Flipkart, close login popup  
2. **SearchPage** — search `mobile`, verify results  
3. **SearchPage + ProductPage + CartPage** — compare products, add to cart, verify cart & price  
4. **CartPage** — increase qty by 2, remove item, verify empty cart  

Tests **share one browser session** across the four cases (browser closes at suite teardown).

---

## Browser selection

The framework supports **Chrome**, **Firefox**, and **Edge** via `BrowserFactory.py`. **Chrome is the default** and is the browser used for Flipkart test development.

| Browser | Variable value | Private mode | Stealth (CDP) | Notes |
|---------|----------------|--------------|---------------|-------|
| Chrome | `chrome` | Incognito | Yes | Recommended |
| Firefox | `firefox` | Private browsing | No | Cross-browser checks |
| Edge | `edge` | InPrivate | Yes | Chromium-based |

### Run with a specific browser

**CLI override:**

```bash
robot --variable browser:firefox Testsuite/FlipkartTestSuite.robot
robot --variable browser:edge Testsuite/FlipkartTestSuite.robot
```

**Suite variable** (in `Testsuite/FlipkartTestSuite.robot` or `Resource/TestEnv/RunDefaults.robot`):

```robot
${browser}    chrome    # or firefox, edge
```

### BrowserFactory keywords

| Keyword | Purpose |
|---------|---------|
| `Open Browser With Proxy` | Launch any supported browser (dispatcher) |
| `Open Chrome With Proxy` | Chrome-only (backward compatible) |
| `Create Chrome Driver` / `Create Firefox Driver` / `Create Edge Driver` | Low-level driver creation |

Flipkart DOM logic was built and tested on Chrome. Firefox and Edge may behave differently (cart icons, tabs, bot detection) — re-validate flows when switching browsers.

---

## Project structure

```
testautomation/
├── README.md
├── PROJECT_DOCUMENTATION.md      # Architecture & presentation guide
├── TECHNICAL_REFERENCE.md        # Deep technical reference
├── requirements.txt
├── run_flipkart_tests.sh
├── run_flipkart_smoke_tests.sh
├── run_flipkart_regression_tests.sh
├── Testsuite/                    # Robot suites & HTML reports
├── Resource/
│   ├── TestEnv/                  # URL, waits, product indexes, browser default
│   ├── TestUser/                 # User profile variables
│   ├── TestCases/Flipkart/       # Step keywords per screen group
│   │   ├── 01HomePageTC.robot
│   │   ├── 02SearchPageTC.robot
│   │   ├── 03SearchPageProductPageCartPageTC.robot
│   │   └── 04CartPageTC.robot
│   ├── Screen/                   # Page objects (Home, Search, Product, Cart)
│   ├── Keywords/                 # Common helpers, FlipkartFlow
│   └── Libraries/
│       ├── FlipkartActions.py    # Robot entry point
│       ├── BrowserFactory.py     # Multi-browser + stealth + proxy
│       ├── ProxyManager.py       # Optional proxy
│       ├── WaitUtils.py
│       └── flipkart/             # Screen-split Python logic
│           ├── base.py           # Shared browser helpers
│           ├── home.py           # HomePage actions
│           ├── search.py         # SearchPage actions
│           ├── product.py        # ProductPage actions
│           ├── cart.py           # CartPage actions
│           ├── pricing.py        # Price parsing
│           └── actions.py        # Combines all mixins
└── Output/Screenshots/           # Failure screenshots
```

### Layering

```
Test Suite  →  TestCases (steps)  →  Screen (.robot)  →  FlipkartActions (Python)
                      ↑
              BrowserFactory (WebDriver bootstrap)
```

---

## Configuration

### Environment (`rbt_env`)

| Value | File | Default URL |
|-------|------|-------------|
| `qa` | `Resource/TestEnv/TestEnv_qa.robot` | `https://www.flipkart.com` |
| `dev` | `Resource/TestEnv/TestEnv_dev.robot` | (override as needed) |

Key variables in `TestEnv_qa.robot`:

- `SEARCH_KEYWORD` — default `mobile`
- `COMPARE_PRODUCT_INDEX_1` / `_2` — compare 10th & 11th products
- `CART_PRODUCT_INDEX` — product added to cart (default `10`)
- `QTY_INCREASE_BY` — cart quantity increase (default `2`)
- `EXPLICIT_WAIT` — default `20s`

Defaults in `Resource/TestEnv/RunDefaults.robot`:

- `rbt_env` — `qa`
- `rbt_usr` — `Default`
- `browser` — `chrome`

Change suite variables:

```bash
robot --variable rbt_env:qa \
      --variable rbt_usr:Default \
      --variable browser:chrome \
      Testsuite/FlipkartTestSuite.robot
```

### Optional proxy

Proxy is **off** unless you set environment variables before running:

```bash
# Single proxy
export PROXY_HOST=proxy.example.com
export PROXY_PORT=8080

# Optional auth
export PROXY_USERNAME=user
export PROXY_PASSWORD=pass

# Or full URL
export PROXY_URL=http://user:pass@proxy.example.com:8080

# Or rotating pool: host:port,user:pass@host:port,...
export PROXY_POOL="host1:8080,host2:8080"

./run_flipkart_tests.sh
```

| Proxy type | Chrome | Edge | Firefox |
|------------|--------|------|---------|
| Simple (host/port) | Yes | Yes | Yes |
| Authenticated | Chrome extension | Chrome extension | Limited — warning logged |

Optional custom user-agent:

```bash
export BROWSER_USER_AGENT="Mozilla/5.0 ..."
```

### Anti-detection defaults

On **Chrome** and **Edge**, the framework applies:

- Incognito / InPrivate mode
- `--disable-blink-features=AutomationControlled`
- `navigator.webdriver` hidden via CDP script
- Custom user-agent

Incognito provides a **clean session** (no stale cookies); stealth flags reduce basic automation detection. They do not guarantee bypass of Flipkart captcha or bot blocking.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `SessionNotCreatedException` / driver error | Update browser; delete cached driver; re-run (Selenium Manager fetches driver) |
| `WebDriverException: chrome not reachable` | Browser not installed or no GUI/display on Linux |
| `Unsupported browser` | Use `chrome`, `firefox`, or `edge` (lowercase) |
| Login / captcha / blocked | Flipkart UI or bot detection; stealth flags, network, or proxy |
| Product index failures | Search results change; adjust indexes in `TestEnv_qa.robot` |
| `flipkart` import errors | Run `robot` from project root; libraries load from `Resource/Libraries/` |
| Firefox/Edge cart or PDP failures | Flipkart UI logic optimized for Chrome; try Chrome first |

Failure screenshots: `Output/Screenshots/failure_*.png`

---

## Dependencies (`requirements.txt`)

```
robotframework==7.0
robotframework-seleniumlibrary==6.3.0
selenium>=4.15.0
```

---

## License

Internal / project use. Flipkart is a trademark of its respective owner; this project is for test automation learning and QA only.
