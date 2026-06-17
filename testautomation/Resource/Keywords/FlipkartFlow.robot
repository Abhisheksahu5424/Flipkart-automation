*** Settings ***
Documentation     Flipkart end-to-end flow keywords
Resource          Common.robot
Resource          ../TestCases/Flipkart/01HomePageTC.robot
Resource          ../TestCases/Flipkart/02SearchPageTC.robot
Resource          ../TestCases/Flipkart/03SearchPageProductPageCartPageTC.robot
Resource          ../TestCases/Flipkart/04CartPageTC.robot

*** Keywords ***
Execute Flipkart Mobile Purchase Flow
    [Documentation]    Reusable E2E flow executed by calling all Flipkart step keywords in sequence
    01HomePageTC.Step 1- Open Flipkart
    01HomePageTC.Step 2- Close login popup
    02SearchPageTC.Step 3- Click global search module
    02SearchPageTC.Step 4- Search with keyword mobile
    02SearchPageTC.Step 5- Verify search results message
    03SearchPageProductPageCartPageTC.Step 6- Compare 10th and 11th products
    03SearchPageProductPageCartPageTC.Step 7- Open 10th product details page
    03SearchPageProductPageCartPageTC.Step 8- Add product to cart and verify Go to Cart button
    03SearchPageProductPageCartPageTC.Step 9- Verify product added to cart
    03SearchPageProductPageCartPageTC.Step 10- Verify cart total amount matches listing price
    04CartPageTC.Step 11- Increase quantity and verify toast message
    04CartPageTC.Step 12- Remove product and verify confirmation popup
    04CartPageTC.Step 13- Confirm remove and verify removal message
    04CartPageTC.Step 14- Verify empty cart message
