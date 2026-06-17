*** Settings ***
Documentation     Flipkart Cart page object
Resource          ../Keywords/Common.robot
Library           ../Libraries/WaitUtils.py
Library           ../Libraries/FlipkartActions.py

*** Variables ***
${LOC_CART_PRODUCT_NAME}      xpath=//a[contains(@class,'_2Kn22P')] | //div[contains(@class,'_2-uG6-')]//a
${LOC_CART_QTY_SELECTOR}      xpath=(//div[contains(normalize-space(.),'Qty:')])[1]
${LOC_CART_PLUS_BTN}          xpath=(//button[normalize-space(.)='+'])[last()]
${LOC_CART_REMOVE_LINK}       xpath=(//div[normalize-space(.)='Remove'])[1]
${LOC_REMOVE_CONFIRM_BTN}     xpath=//div[contains(@class,'_3auQ3N')]//button[normalize-space(.)='Remove'] | //button[normalize-space(.)='Remove' and not(contains(@class,'_2KpZ6l'))]
${LOC_REMOVE_CANCEL_BTN}      xpath=//button[normalize-space(.)='Cancel'] | //div[normalize-space(.)='Cancel']
${LOC_EMPTY_CART_TITLE}       xpath=//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'missing cart items')]
${LOC_EMPTY_CART_SUBTEXT}     xpath=//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'login to see the items you added previously')]

*** Keywords ***
Verify Product Added To Cart
    [Documentation]    Verifies selected product is present in cart
    [Arguments]    ${product_name}
    Common.Log Step    Verify product added to cart: ${product_name}
    Wait For Cart Page Loaded    ${EXPLICIT_WAIT}
    Verify Product In Cart    ${product_name}    ${EXPLICIT_WAIT}

Verify Cart Amount
    [Documentation]    Verifies cart total matches stored listing price
    [Arguments]    ${expected_price}=${EMPTY}
    Common.Log Step    Verify cart amount matches listing price
    Wait For Cart Page Loaded    ${EXPLICIT_WAIT}
    IF    '${expected_price}' == '${EMPTY}'
        ${listing_price}=    Get Stored Listing Price
    ELSE
        ${listing_price}=    Set Variable    ${expected_price}
    END
    ${cart_total}=    Get Cart Total Amount Text
    Prices Should Be Equal    ${listing_price}    ${cart_total}
    Log    Cart amount verified. Listing=${listing_price}, Total=${cart_total}

Increase Product Quantity
    [Documentation]    Increases cart quantity by given amount from current Qty dropdown value
    [Arguments]    ${increase_by}=2
    Common.Log Step    Increase product quantity
    Wait For Cart Page Loaded    ${EXPLICIT_WAIT}
    ${new_quantity}=    Increase Cart Product Quantity    ${increase_by}
    Sleep    0.5s
    RETURN    ${new_quantity}

Verify Quantity Update Toast
    [Documentation]    Verifies quantity update toast with dynamic product name and quantity
    [Arguments]    ${product_name}    ${quantity}=2
    Common.Log Step    Verify quantity update toast for ${product_name}
    Verify Quantity Change Message    ${product_name}    ${quantity}    ${EXPLICIT_WAIT}

Remove Product
    [Documentation]    Clicks Remove on cart item
    Common.Log Step    Click remove product
    Wait For Cart Page Loaded    ${EXPLICIT_WAIT}
    Click Cart Remove Button

Verify Remove Popup
    [Documentation]    Verifies remove confirmation popup contains Cancel and Remove
    Common.Log Step    Verify remove confirmation popup
    Verify Remove Confirmation Popup    ${EXPLICIT_WAIT}

Confirm Remove Product
    [Documentation]    Confirms product removal from cart
    Common.Log Step    Confirm remove product
    Confirm Cart Remove

Verify Empty Cart Message
    [Documentation]    Final pass check — empty cart shows Missing Cart items? after removal
    Common.Log Step    Verify empty cart message: Missing Cart items?
    FlipkartActions.Verify Empty Cart Message    ${EXPLICIT_WAIT}
    Log    Flipkart E2E flow completed successfully    console=yes

Verify Removed Product Success Message
    [Documentation]    Verifies product removed success toast/message
    [Arguments]    ${product_name}
    Common.Log Step    Verify product removed message for ${product_name}
    FlipkartActions.Verify Product Removed Message    ${product_name}    ${EXPLICIT_WAIT}
