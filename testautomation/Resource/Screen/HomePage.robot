*** Settings ***
Documentation     Flipkart Home page object
Resource          ../Keywords/Common.robot
Library           ../Libraries/WaitUtils.py
Library           ../Libraries/FlipkartActions.py

*** Variables ***
${LOC_LOGIN_MODAL}            xpath=//div[contains(@class,'RFBkxv')]
${LOC_LOGIN_CLOSE_BTN}        xpath=//span[@role='button' and contains(@class,'_b3wTlE')] | //div[contains(@class,'RFBkxv')]//span[@role='button'] | //button[contains(@class,'_2doB4z')] | //span[contains(@class,'_30XB9F')]
${LOC_SEARCH_INPUT}           xpath=//input[@name='q' or contains(@title,'Search for Products')]
${LOC_SEARCH_SUBMIT}          xpath=//button[contains(@class,'L0Z3Pu')] | //button[contains(@aria-label,'Search')]

*** Keywords ***
Open Flipkart Website
    [Documentation]    Launches the configured browser and navigates to Flipkart base URL
    [Arguments]    ${url}=${URL}
    Common.Log Step    Open Flipkart website
    Open Browser With Proxy    ${url}    browser=${browser}
    Wait For Element    ${LOC_SEARCH_INPUT}

Close Login Popup
    [Documentation]    Closes login modal using top-right close icon when visible
    Common.Log Step    Close login popup if displayed
    ${modal_visible}=    Run Keyword And Return Status    Wait For Element Present    ${LOC_LOGIN_MODAL}    10s
    IF    not ${modal_visible}
        Dismiss Login Popup If Visible
        Log    Login popup not displayed; continuing
        RETURN
    END
    Wait For Element    ${LOC_LOGIN_CLOSE_BTN}    10s
    ${clicked}=    Run Keyword And Return Status    Click Element Safely    ${LOC_LOGIN_CLOSE_BTN}
    IF    not ${clicked}
        ${close_btn}=    Get WebElement    ${LOC_LOGIN_CLOSE_BTN}
        Execute Javascript    arguments[0].click();    ARGUMENTS    ${close_btn}
        Log    Login close clicked via JavaScript fallback
    END
    Wait Until Element Is Not Visible    ${LOC_LOGIN_MODAL}    10s
    Log    Login popup closed successfully

Click Search Box
    [Documentation]    Focuses the global search input
    Common.Log Step    Click search box
    Run Keyword And Ignore Error    Wait Until Element Is Not Visible    ${LOC_LOGIN_MODAL}    5s
    Wait For Element    ${LOC_SEARCH_INPUT}
    Click Element Safely    ${LOC_SEARCH_INPUT}

Search Product
    [Documentation]    Searches for a product keyword from the home page
    [Arguments]    ${keyword}
    Common.Log Step    Search product: ${keyword}
    Click Search Box
    Input Text Safely    ${LOC_SEARCH_INPUT}    ${keyword}
    Press Keys    ${LOC_SEARCH_INPUT}    RETURN
    Wait For Element Present    css:div[data-id]    ${EXPLICIT_WAIT}
