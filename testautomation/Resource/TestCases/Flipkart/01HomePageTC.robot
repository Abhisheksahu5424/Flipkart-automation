*** Settings ***
Documentation     HomePage test case steps - launch Flipkart and dismiss login
Resource          ../../TestEnv/RunDefaults.robot
Resource          ../../Keywords/Common.robot
Resource          ../../Screen/HomePage.robot
Resource          ../../TestEnv/TestEnv_${rbt_env}.robot
Resource          ../../TestUser/TestUser_${rbt_usr}.robot

*** Keywords ***
Step 1- Open Flipkart
    [Documentation]    Launch browser and open Flipkart home page
    Open Flipkart Website    ${URL}

Step 2- Close login popup
    [Documentation]    Close login module by clicking cross icon on top right of pop-up
    Close Login Popup
