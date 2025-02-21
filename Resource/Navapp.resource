***Settings***
Library     SeleniumLibrary
Resource    Resources.resource
 
*** Variables ***
${browser}    firefox

*** Keywords ***

Create Firefox Options
    ${options}=    Evaluate    sys.modules['selenium.webdriver.firefox.options'].Options()    sys, selenium.webdriver.firefox.options
    Call Method    ${options}   add_argument    --disable-gpu
    Call Method    ${options}   add_argument    --disable-notifications
    Call Method    ${options}   add_argument    --no-proxy-server
    Call Method    ${options}   add_argument    --ignore-certificate-errors
    Call Method    ${options}   add_argument    --disable-extensions
    Call Method    ${options}   add_argument    --disable-extensions-file-access-check
    Call Method    ${options}   add_argument    --disable-extensions-http-throttling
    Call Method    ${options}   add_argument    --window-size\=1920,1080
    Call Method    ${options}   add_argument    --incognito
    Call Method    ${options}   add_argument    --headless
    [Return]    ${options}


Open Firefox Browser
    [Arguments]    ${url}
    ${options}=    Create Firefox Options
    Open Browser    ${url}    firefox    options=${options}
    Maximize Browser Window
    
Get Versione Periferica From XPath
    ${full_text}=    Get Text    xpath=/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr[2]/td/center/textarea
    [Return]    ${full_text}

Get Versione Axis From XPath
    ${full_text}=    Get Text    xpath=/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr[2]/td/center/textarea
    [Return]    ${full_text}