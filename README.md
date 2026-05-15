# ns8-teaspeak

TeaSpeak server module for NethServer 8.

This repository packages a rootless TeaSpeak deployment for NS8 with these MVP decisions:

- TeaSpeak version pinned to 1.5.6
- TeaWeb client pinned to release 59737567
- self-built service image from the official upstream tarball
- self-built TeaWeb image from the official upstream web release
- SQLite as the default backend
- fixed public ports 9987/udp, 9987/tcp, 10101/tcp and 30303/tcp
- TeaWeb is published through Traefik with a hostname-based route
- one instance per node

## Install

Instantiate the module with:

    add-module ghcr.io/nethserver/teaspeak:latest 1

The output contains the created instance name. Example:

    {"module_id": "teaspeak1", "image_name": "teaspeak", "image_url": "ghcr.io/nethserver/teaspeak:latest"}

## Configure

Assuming the instance is named `teaspeak1`, configure it with:

    api-cli run module/teaspeak1/configure-module --data '{"timezone":"UTC","query_ssl_mode":2,"web_enabled":true,"web_host":"teaspeak.example.org","web_lets_encrypt":true,"music_enabled":false,"vpn_check_enabled":false,"license_key":""}'

The action will:

- persist the selected settings in the module environment
- generate `config.yml` for TeaSpeak
- open the required public firewall ports
- enable and start `teaspeak.service`
- optionally enable and start `teaspeak-web.service` when `web_enabled` is true
- create, update or remove the TeaWeb Traefik route based on `web_host`

## Public ports

- 9987/udp: voice traffic
- 9987/tcp: client compatibility path exposed by the upstream container
- 10101/tcp: ServerQuery
- 30303/tcp: file transfer

## Web and music support

When `web_enabled` is true, the module starts a bundled TeaWeb sidecar on an internal loopback HTTP port reserved from NS8.

Set `web_host` to publish TeaWeb through Traefik. If `web_lets_encrypt` is true, the module asks Traefik to obtain a Let's Encrypt certificate for that hostname.
If `web_host` is left empty, TeaWeb remains enabled internally but no public Traefik route is created.

When `music_enabled` is true, the module enables TeaSpeak's built-in music bot system in the server configuration.
There is no separate TeaMusic runtime image integrated yet because the upstream TeaMusic repository does not currently provide a stable, documented release artifact for direct deployment.

## Initial credentials

TeaSpeak prints the initial server admin privilege key and the ServerQuery password on first boot.
The module captures these startup credentials into a dedicated runtime state file and exposes them through the status UI and the `get-initial-credentials` action.
They are intentionally not stored in the normal module environment file.
If an instance was initialized before credential capture support was added, the original values may still only be available in the module system logs.

## Build

The build produces three images:

- `teaspeak`: the NS8 module package image
- `teaspeak-service`: the TeaSpeak runtime image used by the module
- `teaspeak-web`: the TeaWeb runtime image used when `web_enabled` is true

The module also requests one internal TCP port from NS8 for the TeaWeb loopback backend behind Traefik.

Build locally with:

    bash build-images.sh

You can override the upstream binary version with:

    TEASPEAK_VERSION=1.5.6 bash build-images.sh

You can override the TeaWeb client release with:

    TEAWEB_VERSION=59737567 bash build-images.sh

## Uninstall

To remove the instance:

    remove-module --no-preserve teaspeak1

## Running tests locally

This module uses the NS8 standard testing infrastructure. For instructions on how to run the test suite locally, refer to the [Running tests locally](https://github.com/NethServer/ns8-github-actions/blob/v1/README.md#running-tests-locally) section of the ns8-github-actions README.

The default Robot suite now includes a node-local HTTPS smoke test for the TeaWeb Traefik route. It verifies that Traefik serves TeaWeb correctly when the configured hostname is sent as the `Host` header to `https://127.0.0.1/` on the NS8 node.

If you want to validate real Let's Encrypt issuance as well, export `TEASPEAK_PUBLIC_FQDN` before running the suite and point that public DNS name at the NS8 node. The optional Robot test will reconfigure TeaWeb with `web_lets_encrypt=true`, wait for the route to answer over Traefik and then verify that the served certificate issuer contains `Let's Encrypt`.
