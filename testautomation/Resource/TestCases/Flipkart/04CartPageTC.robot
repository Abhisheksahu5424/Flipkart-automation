*** Settings ***
Documentation     CartPage test case steps - quantity update, remove product, verify empty cart
Resource          ../../TestEnv/RunDefaults.robot
Resource          ../../Keywords/Common.robot
Resource          ../../Screen/CartPage.robot
Resource          ../../TestEnv/TestEnv_${rbt_env}.robot
Resource          ../../TestUser/TestUser_${rbt_usr}.robot
Library           ../../Libraries/FlipkartActions.py

*** Variables ***
${PRODUCT_NAME}       ${EMPTY}
${LISTING_PRICE}      ${EMPTY}

*** Keywords ***
Step 11- Increase quantity and verify toast message
    [Documentation]    Increase product qty by ${QTY_INCREASE_BY} and verify quantity update pop-up message
    ${new_quantity}=    Increase Product Quantity    ${QTY_INCREASE_BY}
    Verify Quantity Update Toast    ${PRODUCT_NAME}    ${new_quantity}

Step 12- Remove product and verify confirmation popup
    [Documentation]    Click remove and verify pop-up with Cancel and Remove buttons
    Remove Product
    Verify Remove Popup

Step 13- Confirm remove and verify removal message
    [Documentation]    Click Remove on confirmation pop-up and verify product removed message
    Confirm Remove Product
    Verify Removed Product Success Message    ${PRODUCT_NAME}

Step 14- Verify empty cart message
    [Documentation]    Final step — suite passes when Missing Cart items? screen is displayed
    CartPage.Verify Empty Cart Message
