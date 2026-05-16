*** Settings ***
Library    SSHLibrary
Library    Browser

*** Variables ***
${ADMIN_USER}    admin
${ADMIN_PASSWORD}    Nethesis,1234
${module_id}    ${EMPTY}
${TEST_WEB_HOST}    teaspeak.test.local

*** Keywords ***
Login to cluster-admin
    New Page    https://${NODE_ADDR}/cluster-admin/
    Fill Text    text="Username"    ${ADMIN_USER}
    Click    button >> text="Continue"
    Fill Text    text="Password"    ${ADMIN_PASSWORD}
    Click    button >> text="Log in"
    Wait For Elements State    css=#main-content    visible    timeout=10s

Configure TeaSpeak Module
    [Arguments]    ${web_host}=${TEST_WEB_HOST}    ${web_lets_encrypt}=false    ${music_enabled}=false
    ${payload} =    Catenate    SEPARATOR=
    ...    {"timezone":"UTC","query_ssl_mode":2,"web_enabled":true,
    ...    "web_host":"${web_host}","web_lets_encrypt":${web_lets_encrypt},
    ...    "music_enabled":${music_enabled},"vpn_check_enabled":false,"license_key":""}
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '${payload}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

Read TeaSpeak Runtime Info
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-runtime-info
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    [Return]    ${output}

TeaSpeak database should exist on persisted volume
    ${output}  ${rc} =    Execute Command    runagent -m ${module_id} podman exec teaspeak.service test -s /ts/database/TeaData.sqlite
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0

TeaWeb route is reachable for host
    [Arguments]    ${host}
    ${output}  ${error}  ${rc} =    Execute Command    curl -s -S -L -k -H "Host: ${host}" https://127.0.0.1/
    ...    return_rc=True  return_stdout=True  return_stderr=True
    Should Be Equal As Integers    ${rc}  0
    Should Not Be Empty    ${output}

TeaWeb landing page contains NS8 auto-connect bootstrap
    [Arguments]    ${host}
    ${output}  ${error}  ${rc} =    Execute Command    curl -s -S -k -H "Host: ${host}" https://127.0.0.1/
    ...    return_rc=True  return_stdout=True  return_stderr=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    ns8TeaSpeakAutoConnect

TeaWeb certificate should be issued by Let's Encrypt
    [Arguments]    ${host}
    ${output}  ${error}  ${rc} =    Execute Command    openssl s_client -connect 127.0.0.1:443 -servername ${host} </dev/null 2>/dev/null | openssl x509 -noout -issuer
    ...    return_rc=True  return_stdout=True  return_stderr=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    Let's Encrypt

*** Test Cases ***
Check if teaspeak is installed correctly
    ${output}  ${rc} =    Execute Command    add-module ${IMAGE_URL} 1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    &{output} =    Evaluate    ${output}
    Set Global Variable    ${module_id}    ${output.module_id}

Take screenshots
    [Tags]    ui
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
    Go To    https://${NODE_ADDR}/cluster-admin/#/apps/${module_id}?page=about
    Wait For Elements State    iframe >>> h2 >> text="About"    visible    timeout=10s
    Sleep    5s
    Take Screenshot    filename=${OUTPUT DIR}/browser/screenshot/3._About.png
    Close Browser

Check if teaspeak can be configured
    Configure TeaSpeak Module

Check if teaspeak service is active
    ${output}  ${rc} =    Execute Command    runagent -m ${module_id} systemctl --user is-active teaspeak.service
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    active

Check if teaspeak runtime info is available
    ${output} =    Read TeaSpeak Runtime Info
    Should Contain    ${output}    "server_version"
    Should Contain    ${output}    "credentials_available"
    Should Contain    ${output}    "tls_certificate_available"
    Should Contain    ${output}    "tls_certificate_host"
    Should Contain    ${output}    "web_enabled"
    Should Contain    ${output}    "web_route_host"
    Should Contain    ${output}    "web_route_configured"
    Should Contain    ${output}    "music_enabled"

Check if teaspeak runtime info reflects TeaWeb route state
    ${output} =    Read TeaSpeak Runtime Info
    ${runtime} =    Evaluate    json.loads(r'''${output}''')    modules=json
    Should Be Equal    ${runtime}[web_enabled]    ${True}
    Should Be Equal    ${runtime}[web_route_host]    ${TEST_WEB_HOST}
    Should Be Equal    ${runtime}[web_route_configured]    ${True}
    Should Be Equal    ${runtime}[web_route_lets_encrypt]    ${False}
    Should Be Equal    ${runtime}[web_public_url]    https://${TEST_WEB_HOST}

Check if teaspeak initial credentials action is available
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-initial-credentials
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    "available"
    Should Contain    ${output}    "captured_at"

Check if teaspeak web service is active
    ${output}  ${rc} =    Execute Command    runagent -m ${module_id} systemctl --user is-active teaspeak-web.service
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    active

Check if TeaWeb Traefik route is reachable with configured host header
    Wait Until Keyword Succeeds    20 times    3 seconds    TeaWeb route is reachable for host    ${TEST_WEB_HOST}

Check if TeaWeb landing page injects the NS8 auto-connect bootstrap
    Wait Until Keyword Succeeds    20 times    3 seconds    TeaWeb landing page contains NS8 auto-connect bootstrap    ${TEST_WEB_HOST}

Check if TeaSpeak database survives a service restart
    Wait Until Keyword Succeeds    20 times    3 seconds    TeaSpeak database should exist on persisted volume
    ${rc} =    Execute Command    runagent -m ${module_id} systemctl --user restart teaspeak.service
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    Wait Until Keyword Succeeds    20 times    3 seconds    TeaSpeak database should exist on persisted volume

Check optional Let's Encrypt issuance for TeaWeb
    ${public_fqdn} =    Evaluate    os.getenv("TEASPEAK_PUBLIC_FQDN", "").strip().lower()    modules=os
    IF    '${public_fqdn}' == ''
        Skip    Set TEASPEAK_PUBLIC_FQDN to run the live Let's Encrypt smoke test.
    END
    Configure TeaSpeak Module    ${public_fqdn}    true
    ${output} =    Read TeaSpeak Runtime Info
    ${runtime} =    Evaluate    json.loads(r'''${output}''')    modules=json
    Should Be Equal    ${runtime}[web_route_host]    ${public_fqdn}
    Should Be Equal    ${runtime}[web_route_configured]    ${True}
    Should Be Equal    ${runtime}[web_route_lets_encrypt]    ${True}
    Should Be Equal    ${runtime}[web_public_url]    https://${public_fqdn}
    Wait Until Keyword Succeeds    20 times    15 seconds    TeaWeb route is reachable for host    ${public_fqdn}
    Wait Until Keyword Succeeds    20 times    15 seconds    TeaWeb certificate should be issued by Let's Encrypt    ${public_fqdn}

Check if teaspeak is removed correctly
    ${rc} =    Execute Command    remove-module --no-preserve ${module_id}
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0