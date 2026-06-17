*** Settings ***
Documentation     SearchPage, ProductPage and CartPage steps - compare, add to cart, verify cart
Resource          ../../TestEnv/RunDefaults.robot
Resource          ../../Keywords/Common.robot
Resource          ../../Screen/SearchPage.robot
Resource          ../../Screen/ProductPage.robot
Resource          ../../Screen/CartPage.robot
Resource          ../../TestEnv/TestEnv_${rbt_env}.robot
Resource          ../../TestUser/TestUser_${rbt_usr}.robot
Library           ../../Libraries/FlipkartActions.py

*** Variables ***
${PRODUCT_NAME}       ${EMPTY}
${LISTING_PRICE}      ${EMPTY}

*** Keywords ***
Step 6- Compare 10th and 11th products
    [Documentation]    Select compare checkbox for 10th and 11th phone and verify compare tray
    Reset Compare Selection State
    ${product_10}=    Select Product For Compare    ${COMPARE_PRODUCT_INDEX_1}
    Verify Compare Tray    ${product_10}    1
    ${product_11}=    Select Product For Compare    ${COMPARE_PRODUCT_INDEX_2}
    Verify Compare Tray    ${product_11}    2
    Set Suite Variable    ${PRODUCT_NAME}    ${product_10}

Step 7- Open 10th product details page
    [Documentation]    Click 10th phone name and open product description page
    ${listing_price}=    Get Product Price    ${CART_PRODUCT_INDEX}
    Open Product Details    ${CART_PRODUCT_INDEX}
    Set Suite Variable    ${LISTING_PRICE}    ${listing_price}
    Verify Product Page Loaded    ${PRODUCT_NAME}

Step 8- Add product to cart and verify Go to Cart button
    [Documentation]    Click Add to cart and verify button name changed to Going to cart
    Add Product To Cart
    Verify Go To Cart Button

Step 9- Verify product added to cart
    [Documentation]    Navigate to cart and verify selected product is present
    Navigate To Cart
    Verify Product Added To Cart    ${PRODUCT_NAME}

Step 10- Verify cart total amount matches listing price
    [Documentation]    Verify Total Amount on cart page matches price from products list page
    Verify Cart Amount    ${LISTING_PRICE}
