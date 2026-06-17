*** Settings ***
Documentation     Shared reusable keywords for Flipkart automation framework
Library           SeleniumLibrary
Library           Collections
Library           OperatingSystem
Library           String
Library           ../Libraries/BrowserFactory.py
Library           ../Libraries/ProxyManager.py
Library           ../Libraries/WaitUtils.py
Library           ../Libraries/DataReader.py

*** Variables ***
${EXPLICIT_WAIT}      20s
${SHORT_WAIT}         10s
${SCREENSHOT_DIR}     Output/Screenshots

*** Keywords ***
Set Timestamp
    [Documentation]    Logs test start timestamp for traceability
    ${timestamp}=    Get Time    epoch
    Log    Test started at epoch: ${timestamp}    console=yes

Open Browser With Proxy
    [Documentation]    Opens the configured browser with proxy, stealth flags, and registers driver with SeleniumLibrary. Supported browsers: chrome, firefox, edge.
    [Arguments]    ${url}    ${rotate_proxy}=${FALSE}    ${browser}=chrome
    Log    Opening browser '${browser}' for URL: ${url}
    ProxyManager.Load Proxy Pool From Environment
    BrowserFactory.Open Browser With Proxy    ${url}    browser=${browser}    incognito=${TRUE}    rotate_proxy=${rotate_proxy}
    Set Selenium Implicit Wait    0 seconds
    Set Selenium Timeout    ${EXPLICIT_WAIT}

Wait For Element
    [Documentation]    Explicit wait wrapper for visible elements
    [Arguments]    ${locator}    ${timeout}=${EXPLICIT_WAIT}
    Wait For Element Visible    ${locator}    ${timeout}

Click Element Safely
    [Documentation]    Scrolls into view and clicks with retry-safe explicit waits
    [Arguments]    ${locator}    ${timeout}=${EXPLICIT_WAIT}
    Safe Click Element    ${locator}    ${timeout}

Input Text Safely
    [Documentation]    Clears and types text using explicit waits
    [Arguments]    ${locator}    ${text}    ${timeout}=${EXPLICIT_WAIT}
    Safe Input Text    ${locator}    ${text}    clear=${TRUE}    timeout=${timeout}

Scroll Into View
    [Documentation]    Scrolls target element to the center of the viewport
    [Arguments]    ${locator}    ${timeout}=${EXPLICIT_WAIT}
    Scroll Locator Into View    ${locator}    ${timeout}

Take Screenshot On Failure
    [Documentation]    Captures screenshot when a step fails; used in teardown hooks
    ${status}=    Run Keyword And Return Status    Capture Page Screenshot    ${SCREENSHOT_DIR}${/}failure_{index}.png
    Run Keyword If    not ${status}    Log    Screenshot capture failed    WARN

Close Browser Safely
    [Documentation]    Closes browser and logs teardown status
    ${status}=    Run Keyword And Return Status    Close Browser
    Run Keyword If    not ${status}    Log    Browser close skipped or already closed    WARN

Log Step
    [Documentation]    Standardized step logging
    [Arguments]    ${message}
    Log    *** STEP: ${message} ***    console=yes

Run Step With Error Handling
    [Documentation]    Executes a keyword with TRY/EXCEPT and screenshot on failure
    [Arguments]    ${keyword}    @{args}
    TRY
        Run Keyword    ${keyword}    @{args}
    EXCEPT    AS    ${error}
        Log    Step failed: ${error}    ERROR
        Take Screenshot On Failure
        Fail    ${error}
    END
