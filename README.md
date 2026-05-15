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

    add-module ghcr.io/generablack/ns8teaspeak:latest 1

The output contains the created instance name. Example:

    {"module_id": "ns8teaspeak1", "image_name": "ns8teaspeak", "image_url": "ghcr.io/generablack/ns8teaspeak:latest"}

## Install from GUI

This repository now ships an NS8 software repository index under `repository/`.

To add it from the NS8 web interface:

1. Open `Software center`.
2. Open the three-dots menu in the top-right corner.
3. Choose `Software repositories`.
4. Click `Add repository`.
5. Enter these values:

    Name: z-generablack
    URL: https://raw.githubusercontent.com/GeneraBlack/NS8TeaSpeak/main/repository
    Status: enabled

6. Click `Reload repositories`.

TeaSpeak will then appear in the Software center as soon as a matching semantic-version image tag is published.
The repository bootstrap version for the first GUI-installable release is `0.1.0`.

## Configure

Assuming the instance is named `ns8teaspeak1`, configure it with:

    api-cli run module/ns8teaspeak1/configure-module --data '{"timezone":"UTC","query_ssl_mode":2,"web_enabled":true,"web_host":"teaspeak.example.org","web_lets_encrypt":true,"music_enabled":false,"vpn_check_enabled":false,"license_key":""}'

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

- `ns8teaspeak`: the NS8 module package image
- `ns8teaspeak-service`: the TeaSpeak runtime image used by the module
- `ns8teaspeak-web`: the TeaWeb runtime image used when `web_enabled` is true

The module also requests one internal TCP port from NS8 for the TeaWeb loopback backend behind Traefik.

Build locally with:

    bash build-images.sh

You can override the upstream binary version with:

    TEASPEAK_VERSION=1.5.6 bash build-images.sh

You can override the TeaWeb client release with:

    TEAWEB_VERSION=59737567 bash build-images.sh

## Build the NS8 software repository index

The static NS8 repository index for GUI installation is stored in `repository/`.
Rebuild it with:

    python scripts/build_repository_index.py

The generator reads the module metadata from `repository/ns8teaspeak/metadata.json`, copies the logo from the repository tree and resolves image labels from GHCR.
For the first stable GUI release it bootstraps version `0.1.0` from the published `latest` image until the real `0.1.0` image tag exists.

To publish a new GUI-installable stable release:

1. Update `VERSION` if needed.
2. Run `python scripts/build_repository_index.py`.
3. Commit and push the repository changes.
4. Create and push the matching Git tag, for example `0.1.0`.

The existing `publish-images.yml` workflow will publish that semantic image tag automatically, and the GUI repository will then resolve to the stable image instead of the bootstrap fallback.

## Uninstall

To remove the instance:

    remove-module --no-preserve ns8teaspeak1

## Running tests locally

This module uses the NS8 standard testing infrastructure. For instructions on how to run the test suite locally, refer to the [Running tests locally](https://github.com/NethServer/ns8-github-actions/blob/v1/README.md#running-tests-locally) section of the ns8-github-actions README.

The default Robot suite now includes a node-local HTTPS smoke test for the TeaWeb Traefik route. It verifies that Traefik serves TeaWeb correctly when the configured hostname is sent as the `Host` header to `https://127.0.0.1/` on the NS8 node.

If you want to validate real Let's Encrypt issuance as well, export `TEASPEAK_PUBLIC_FQDN` before running the suite and point that public DNS name at the NS8 node. The optional Robot test will reconfigure TeaWeb with `web_lets_encrypt=true`, wait for the route to answer over Traefik and then verify that the served certificate issuer contains `Let's Encrypt`.
