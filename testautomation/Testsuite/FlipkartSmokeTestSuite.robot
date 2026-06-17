*** Settings ***
Documentation     Flipkart smoke suite - quick validation for HomePage, SearchPage, ProductPage and CartPage flows
Library           OperatingSystem
Resource          ../Resource/TestEnv/RunDefaults.robot
Resource          ../Resource/TestEnv/TestEnv_${rbt_env}.robot
Resource          ../Resource/TestUser/TestUser_${rbt_usr}.robot
Resource          ../Resource/Keywords/Common.robot
Resource          ../Resource/Screen/HomePage.robot
Resource          ../Resource/Screen/SearchPage.robot
Resource          ../Resource/Screen/ProductPage.robot
Resource          ../Resource/Screen/CartPage.robot
Resource          ../Resource/TestCases/Flipkart/01HomePageTC.robot
Resource          ../Resource/TestCases/Flipkart/02SearchPageTC.robot
Resource          ../Resource/TestCases/Flipkart/03SearchPageProductPageCartPageTC.robot
Resource          ../Resource/TestCases/Flipkart/04CartPageTC.robot
Force Tags        smoke
Suite Teardown    Close All Browsers
Test Setup        Set Timestamp
Test Teardown     Take Screenshot On Failure

*** Variables ***
${rbt_env}        qa
${rbt_usr}        Default
${browser}        Chrome

*** Test Cases ***
Smoke 01 HomePage - Open Flipkart And Close Login Popup
    [Documentation]    Smoke: HomePage launch and login popup dismissal
    [Tags]    flipkart    homepage
    01HomePageTC.Step 1- Open Flipkart
    01HomePageTC.Step 2- Close login popup

Smoke 02 SearchPage - Search Mobile And Verify Results
    [Documentation]    Smoke: SearchPage search and results validation
    [Tags]    flipkart    searchpage
    02SearchPageTC.Step 3- Click global search module
    02SearchPageTC.Step 4- Search with keyword mobile
    02SearchPageTC.Step 5- Verify search results message

Smoke 03 SearchPage ProductPage CartPage - Compare Add To Cart And Verify Cart
    [Documentation]    Smoke: compare, add to cart, and cart verification
    [Tags]    flipkart    searchpage    productpage    cartpage
    03SearchPageProductPageCartPageTC.Step 6- Compare 10th and 11th products
    03SearchPageProductPageCartPageTC.Step 7- Open 10th product details page
    03SearchPageProductPageCartPageTC.Step 8- Add product to cart and verify Go to Cart button
    03SearchPageProductPageCartPageTC.Step 9- Verify product added to cart
    03SearchPageProductPageCartPageTC.Step 10- Verify cart total amount matches listing price

Smoke 04 CartPage - Increase Quantity Remove Product And Verify Empty Cart
    [Documentation]    Smoke: cart quantity update, remove product, and empty cart check
    [Tags]    flipkart    cartpage
    04CartPageTC.Step 11- Increase quantity and verify toast message
    04CartPageTC.Step 12- Remove product and verify confirmation popup
    04CartPageTC.Step 13- Confirm remove and verify removal message
    04CartPageTC.Step 14- Verify empty cart message
