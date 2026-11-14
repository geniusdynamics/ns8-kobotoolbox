*** Settings ***
Library    SSHLibrary
Library    String

*** Variables ***
${HOST}    kobotoolbox.example.org
${ADMIN_USER}    admin
${ADMIN_PASSWORD}    Nethesis,1234
${module_id}    ${EMPTY}

*** Keywords ***
Login to cluster-admin
    New Page    https://${NODE_ADDR}/cluster-admin/
    Fill Text    text="Username"    ${ADMIN_USER}
    Click    button >> text="Continue"
    Fill Text    text="Password"    ${ADMIN_PASSWORD}
    Click    button >> text="Log in"
    Wait For Elements State    css=#main-content    visible    timeout=10s

KoboToolbox login page answers through Traefik
    # The login page answers 200 only once the migrations are done and uWSGI
    # runs. 000: no answer, 404: Traefik has no route, 502: nginx is not
    # listening yet, 504: uWSGI is not listening yet.
    ${status} =    Execute Command    curl -k -s -o /dev/null --max-time 10 -w '\%{http_code}' --resolve ${HOST}:443:127.0.0.1 https://${HOST}/accounts/login/
    ${status} =    Strip String    ${status}
    Should Be Equal    ${status}    200    https://${HOST}/accounts/login/ answered HTTP ${status}

KoboToolbox services are healthy
    # KPI checks Mongo, both PostgreSQL databases, Redis, Celery and Enketo
    ${output}    ${rc} =    Execute Command    curl -k -s --max-time 30 -w '\nHTTP \%{http_code}' --resolve ${HOST}:443:127.0.0.1 https://${HOST}/service_health/
    ...    return_rc=True
    Should Contain    ${output}    HTTP 200    service_health failed: ${output}
    Should Contain    ${output}    OK KPI

*** Test Cases ***
Check if kobotoolbox is installed correctly
    ${output}  ${rc} =    Execute Command    add-module ${IMAGE_URL} 1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0    add-module failed: ${output}
    &{output} =    Evaluate    ${output}
    Set Global Variable    ${module_id}    ${output.module_id}

Take screenshots
    [Tags]    ui
    Import Library    Browser
    New Browser    chromium    headless=True
    New Context    ignoreHTTPSErrors=True
    Login to cluster-admin
    Go To    https://${NODE_ADDR}/cluster-admin/#/apps/${module_id}
    Wait For Elements State    iframe >>> h2 >> text="Status"    visible    timeout=10s
    Sleep    5s
    Take Screenshot    filename=${OUTPUT DIR}/browser/screenshot/1._Status.png
    Go To    https://${NODE_ADDR}/cluster-admin/#/apps/${module_id}?page=settings
    Wait For Elements State    iframe >>> h2 >> text="Settings"    visible    timeout=10s
    Sleep    5s
    Take Screenshot    filename=${OUTPUT DIR}/browser/screenshot/2._Settings.png
    Close Browser

Check if kobotoolbox can be configured
    # Valid against configure-module/validate-input.json
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"host":"${HOST}","http2https":true,"lets_encrypt":false}'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0    configure-module failed: ${output}

Check if kobotoolbox configuration reads back
    ${output}    ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}    0    get-configuration failed: ${output}
    &{config} =    Evaluate    json.loads(r'''${output}''')    modules=json
    Should Be Equal    ${config.host}    ${HOST}
    # Every module with the reader role can read it
    Should Not Contain    ${output}    PASSWORD
    Should Not Contain    ${output}    SECRET

Check if kobotoolbox works as expected
    Wait Until Keyword Succeeds    15 min    10 sec    KoboToolbox login page answers through Traefik

Check if kobotoolbox services are healthy
    Wait Until Keyword Succeeds    5 min    10 sec    KoboToolbox services are healthy

Check if kobotoolbox is removed correctly
    ${rc} =    Execute Command    remove-module --no-preserve ${module_id}
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
