*** Settings ***
Resource    ../Resource/Resources.resource
Resource    ../Resource/Navapp.resource
Library    func.py
Library    Process

*** Variables ***
${GECKODRIVER_LOG}    NUL  # Inserisci il percorso completo se vuoi salvare in un log unico

#link for axis
#http://root:1TS_S0LUT10N@10.1.64.138/camera/index.html#/maintenance

${URL}    Default
${is_periferica}    True



*** Test Cases ***
GetVersioneFromXPath
        
    Open Firefox Browser    ${URL}    
    Log    Apro il seguente link: ${URL}
    IF    ${is_periferica} == True
        Log    parliamo di peri
        ${full_text}    Get Versione Periferica From XPath
        ${versione}=    getVersioneAnprFromText    ${full_text}
        Log To Console    THIS IS THE OUTPUT: ${versione}
    ELSE
        #TO DO recupera versione axis
        Log    non parliamo di peri
    END
        
    Close Browser
