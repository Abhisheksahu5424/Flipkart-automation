*** Settings ***
Documentation     Flipkart Product details page object
Resource          ../Keywords/Common.robot
Library           ../Libraries/WaitUtils.py
Library           ../Libraries/FlipkartActions.py

*** Variables ***
${LOC_PRODUCT_TITLE}          xpath=//span[contains(@class,'B_NuCI')] | //h1[contains(@class,'yhB1nd')] | //span[contains(@class,'VU-ZEz')]
${LOC_ADD_TO_CART_BTN}        xpath=(//div[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='add to cart'])[1]
${LOC_GO_TO_CART_BTN}         xpath=(//div[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='going to cart' or normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='go to cart'])[1]
${LOC_PRODUCT_PRICE}          xpath=(//*[contains(text(),'₹')])[1]

*** Keywords ***
Verify Product Page Loaded
    [Documentation]    Verifies product detail page is loaded
    [Arguments]    ${product_name}=${EMPTY}
    Common.Log Step    Verify product detail page loaded
    Wait Until Location Contains    /p/    timeout=${EXPLICIT_WAIT}
    # Set Delivery Pincode If Prompted    ${DELIVERY_PINCODE}
    IF    '${product_name}' != '${EMPTY}'
        ${name_token}=    Evaluate    '''${product_name}'''.split()[0]
        Wait For Page To Contain    ${name_token}    ${EXPLICIT_WAIT}
    ELSE
        Wait For Product Page Title    ${EXPLICIT_WAIT}
    END
    Log    Product page loaded successfully

Add Product To Cart
    [Documentation]    Clicks Add to Cart on product page
    Common.Log Step    Add product to cart
    Wait For Add To Cart Button    ${EXPLICIT_WAIT}
    Click Add To Cart On Product Page

Verify Go To Cart Button
    [Documentation]    Verifies CTA changed to Go to Cart / Going to cart
    Common.Log Step    Verify Go to Cart button is visible
    ${button_text}=    Verify Go To Cart Button Visible    ${EXPLICIT_WAIT}
    Should Match Regexp    ${button_text}    (?i).*(go to cart|going to cart).*
    Log    Go to Cart button verified: ${button_text}

Navigate To Cart
    [Documentation]    Navigates to cart from product page
    Common.Log Step    Navigate to cart page
    Navigate To Cart From Product Page
    Wait For Cart Page Loaded    ${EXPLICIT_WAIT}
