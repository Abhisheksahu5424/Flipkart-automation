*** Settings ***
Documentation     SearchPage test case steps - search mobile and verify results
Resource          ../../TestEnv/RunDefaults.robot
Resource          ../../Keywords/Common.robot
Resource          ../../Screen/HomePage.robot
Resource          ../../Screen/SearchPage.robot
Resource          ../../TestEnv/TestEnv_${rbt_env}.robot
Resource          ../../TestUser/TestUser_${rbt_usr}.robot

*** Keywords ***
Step 3- Click global search module
    [Documentation]    Click on the global search input on home page
    Click Search Box

Step 4- Search with keyword mobile
    [Documentation]    Search products using the configured keyword
    Input Text Safely    ${LOC_SEARCH_INPUT}    ${SEARCH_KEYWORD}
    Press Keys    ${LOC_SEARCH_INPUT}    RETURN
    Wait For Element Present    css:div[data-id]    ${EXPLICIT_WAIT}

Step 5- Verify search results message
    [Documentation]    Verify search summary shows pagination and keyword in results message
    Verify Search Result Message    Showing 1 – 24 of    ${SEARCH_KEYWORD}
    Ensure Product Cards Loaded    ${COMPARE_PRODUCT_INDEX_2}
