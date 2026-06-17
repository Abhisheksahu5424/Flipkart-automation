*** Settings ***
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
Suite Teardown    Close All Browsers
Test Setup        Set Timestamp
Test Teardown     Take Screenshot On Failure

*** Variables ***
# env setting for whole test suite, available options: dev, qa
${rbt_env}        qa
#
# Test User:
${rbt_usr}        Default
#
# browser setting, available options: Firefox, Chrome, IE
${browser}        Chrome

*** Test Cases ***
01 HomePage - Open Flipkart And Close Login Popup
    [Documentation]    HomePage: launch Flipkart and dismiss login modal
    [Tags]    flipkart    e2e    smoke    regression    homepage
    01HomePageTC.Step 1- Open Flipkart
    01HomePageTC.Step 2- Close login popup

02 SearchPage - Search Mobile And Verify Results
    [Documentation]    SearchPage: open search, search mobile, verify results summary
    [Tags]    flipkart    e2e    smoke    regression    searchpage
    02SearchPageTC.Step 3- Click global search module
    02SearchPageTC.Step 4- Search with keyword mobile
    02SearchPageTC.Step 5- Verify search results message

03 SearchPage ProductPage CartPage - Compare Add To Cart And Verify Cart
    [Documentation]    SearchPage compare, ProductPage add to cart, CartPage verify product and price
    [Tags]    flipkart    e2e    smoke    regression    searchpage    productpage    cartpage
    03SearchPageProductPageCartPageTC.Step 6- Compare 10th and 11th products
    03SearchPageProductPageCartPageTC.Step 7- Open 10th product details page
    03SearchPageProductPageCartPageTC.Step 8- Add product to cart and verify Go to Cart button
    03SearchPageProductPageCartPageTC.Step 9- Verify product added to cart
    03SearchPageProductPageCartPageTC.Step 10- Verify cart total amount matches listing price

04 CartPage - Increase Quantity Remove Product And Verify Empty Cart
    [Documentation]    CartPage: update quantity, remove product, confirm removal, verify empty cart
    [Tags]    flipkart    e2e    smoke    regression    cartpage
    04CartPageTC.Step 11- Increase quantity and verify toast message
    04CartPageTC.Step 12- Remove product and verify confirmation popup
    04CartPageTC.Step 13- Confirm remove and verify removal message
    04CartPageTC.Step 14- Verify empty cart message
