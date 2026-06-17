*** Settings ***
Documentation     Flipkart Search results page object
Resource          ../Keywords/Common.robot
Library           ../Libraries/WaitUtils.py
Library           ../Libraries/FlipkartActions.py

*** Variables ***
${LOC_SEARCH_RESULTS_TEXT}    xpath=//*[contains(normalize-space(.),'results for') and contains(translate(.,'MOBILE','mobile'),'mobile')]

*** Keywords ***
Verify Search Result Message
    [Documentation]    Verifies search summary contains expected pagination and keyword text
    [Arguments]    ${pagination_text}=Showing 1 – 24 of    ${keyword}=mobile
    Common.Log Step    Verify search result summary message
    Wait For Page To Contain    ${pagination_text}    ${EXPLICIT_WAIT}
    Wait For Page To Contain    ${keyword}    ${EXPLICIT_WAIT}
    ${body}=    Get Text    tag:body
    Should Contain    ${body}    ${pagination_text}
    Should Contain    ${body}    ${keyword}
    Log    Search summary validated successfully

Select Product For Compare
    [Documentation]    Selects compare checkbox on the product card at given index (1-based)
    [Arguments]    ${index}
    Common.Log Step    Select compare checkbox for product index ${index}
    ${product_name}=    Select Compare On Card Index    ${index}
    RETURN    ${product_name}

Verify Compare Tray
    [Documentation]    Verifies floating COMPARE tray is visible with expected item count
    [Arguments]    ${product_name}    ${expected_count}=1
    Common.Log Step    Verify compare tray contains ${product_name}
    Verify Compare Tray Is Visible    ${EXPLICIT_WAIT}
    Verify Compare Tray Item Count    ${expected_count}    ${EXPLICIT_WAIT}
    Log    Compare tray validated for product: ${product_name} with count ${expected_count}

Open Product Details
    [Documentation]    Opens product details page for the given index and returns product name
    [Arguments]    ${index}
    Common.Log Step    Open product details for index ${index}
    ${product_name}=    Open Product From Card Index    ${index}    ${EXPLICIT_WAIT}
    # Set Delivery Pincode If Prompted    ${DELIVERY_PINCODE}
    RETURN    ${product_name}

Get Product Price
    [Documentation]    Reads listing price for product card index
    [Arguments]    ${index}
    ${price}=    Get Product Price From Card Index    ${index}
    Store Selected Listing Price    ${price}
    RETURN    ${price}
