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

Currently active repository URL:

    https://raw.githubusercontent.com/GeneraBlack/NS8TeaSpeak/main/repository

Optional browser-friendly URL after enabling GitHub Pages in the repository settings:

    https://generablack.github.io/NS8TeaSpeak/

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
The repository currently advertises GUI release `0.1.24`.

Note: the raw repository base URL returns `404` in a browser because GitHub Raw does not expose directory listings. NS8 still works with it because it requests `repodata.json` explicitly. For a manual browser check, open `https://raw.githubusercontent.com/GeneraBlack/NS8TeaSpeak/main/repository/repodata.json` directly.

If you want a browser-friendly repository homepage, enable `Settings -> Pages -> Build and deployment -> Source: GitHub Actions` in the GitHub repository and then rerun the `Deploy software repository to Pages` workflow.

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

The TeaWeb landing page now auto-adds `connect_default=1`, `connect_address=<requested host>:443`, and `connect_no_dnsproxy=true` when the public URL is opened without query parameters.
It also normalizes older NS8 self-connect URLs like `?connect_default=1&connect_address=<requested host>` so cached browser URLs do not keep using direct `9987` WebSocket TLS.
In practice this means opening `https://<web_host>/` immediately starts a TeaWeb connection attempt through the public Traefik HTTPS route instead of asking the browser to connect directly to TeaSpeak's `9987` WebSocket endpoint.
The TeaWeb sidecar proxies WebSocket upgrade requests from Traefik to TeaSpeak's internal `9987` listener, so the browser only validates the normal `web_host` certificate on port `443`.

TeaWeb release `59737567` also has an upstream formatting bug where the browser certificate fallback renders as `<unknwon object>` instead of a clickable link.
The `ns8teaspeak-web` image patches that release during build so the certificate acceptance link is clickable again.

The module mirrors the active Traefik certificate for `web_host` into TeaSpeak's own TLS files during service start and on `certificate-changed` events.
Before TeaSpeak starts, the service entrypoint validates that the staged certificate still matches the current `web_host` and is inside its validity window; stale certificates from previous hosts are removed before the server boots.
For existing installations it also refreshes TeaSpeak's persisted web certificate database entries (`webcert-cert`, `webcert-key`, `webcert-revision`) so an older stored web certificate cannot linger in the database.
TeaSpeak 1.5.6 still manages the WebSocket certificate on `9987` internally and does not reliably use the staged Traefik certificate for that listener.
For browser clients, the module therefore keeps `9987` behind the TeaWeb sidecar and lets Traefik terminate the public TLS connection on `443`.
Module updates restart TeaSpeak after refreshing the staged Traefik certificate so old containers cannot keep running after the new module image is installed.

When `music_enabled` is true, the module enables TeaSpeak's built-in music bot system in the server configuration.
The service image now also ships the upstream runtime prerequisites for the built-in music providers: `ffmpeg`, `python3`, a `python` compatibility symlink and a `youtube-dl` compatibility command backed by a freshly downloaded upstream `yt-dlp` binary.
It also pre-creates the TeaSpeak provider config files, mirrors the packaged tools into `/ts/providers/bin`, and the service entrypoint now reasserts those files plus a provider-first `PATH` at container startup so NS8 runtime differences cannot drop the music helper resolution back to a bare `youtube-dl` lookup.
There is no separate TeaMusic runtime image integrated yet because the upstream TeaMusic repository does not currently provide a stable, documented release artifact for direct deployment.

TeaSpeak now also stores its SQLite database on the persisted `/ts/database` volume via `sqlite:///ts/database/TeaData.sqlite`.
The service entrypoint also passes TeaSpeak explicit `-Pgeneral.database.url=...` and keeps `/ts/TeaData.sqlite` as a compatibility symlink to the persisted database file so older/default TeaSpeak paths cannot fall back to ephemeral container storage.
During module updates the updater stages any legacy in-container `TeaData.sqlite` file into module state, and the next container start imports it into the persisted database volume before the server boots.

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
If `VERSION` points to a semantic release tag that is not yet present in GHCR, the generator bootstraps that version from the published `latest` image until the real tag exists.

To publish a new GUI-installable stable release:

1. Update `VERSION` if needed.
2. Run `python scripts/build_repository_index.py`.
3. Commit and push the repository changes.
4. Create and push the matching Git tag, for example `0.1.13`.

The existing `publish-images.yml` workflow will publish that semantic image tag automatically, and the GUI repository will then resolve to the stable image instead of the bootstrap fallback.

## Uninstall

To remove the instance:

    remove-module --no-preserve ns8teaspeak1

## Running tests locally

This module uses the NS8 standard testing infrastructure. For instructions on how to run the test suite locally, refer to the [Running tests locally](https://github.com/NethServer/ns8-github-actions/blob/v1/README.md#running-tests-locally) section of the ns8-github-actions README.

The default Robot suite now includes a node-local HTTPS smoke test for the TeaWeb Traefik route. It verifies that Traefik serves TeaWeb correctly when the configured hostname is sent as the `Host` header to `https://127.0.0.1/` on the NS8 node.

The suite also verifies that TeaSpeak writes its SQLite database to `/ts/database/TeaData.sqlite` and that the file still exists after a service restart, protecting against full-state resets on restart.

If you want to validate real Let's Encrypt issuance as well, export `TEASPEAK_PUBLIC_FQDN` before running the suite and point that public DNS name at the NS8 node. The optional Robot test will reconfigure TeaWeb with `web_lets_encrypt=true`, wait for the route to answer over Traefik and then verify that the served certificate issuer contains `Let's Encrypt`.
