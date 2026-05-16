#!/usr/bin/env python3

import json
import os
from pathlib import Path
import re
import signal
import ssl
import subprocess
import sys
import textwrap
from datetime import datetime, timezone


STATE_DIR = Path(os.environ.get("TEASPEAK_STATE_DIR", "/ts/module_state"))
TEASPEAK_ROOT = Path("/ts")
DATABASE_FILENAME = "TeaData.sqlite"
DATABASE_DIR = TEASPEAK_ROOT / "database"
PERSISTENT_DATABASE_FILE = DATABASE_DIR / DATABASE_FILENAME
LEGACY_CONTAINER_DATABASE_FILE = TEASPEAK_ROOT / DATABASE_FILENAME
LEGACY_DATABASE_STAGE_DIR = STATE_DIR / "legacy-database"
LEGACY_STAGED_DATABASE_FILE = LEGACY_DATABASE_STAGE_DIR / DATABASE_FILENAME
DATABASE_FILE_SUFFIXES = ("", "-wal", "-shm", "-journal")
CERTS_DIR = TEASPEAK_ROOT / "certs"
STAGED_TLS_DIR = STATE_DIR / "tls"
DEFAULT_CERTIFICATE_FILENAME = "default_certificate.pem"
DEFAULT_CERTIFICATE_CRT_FILENAME = "default_certificate.crt"
DEFAULT_PRIVATEKEY_FILENAME = "default_privatekey.pem"
STAGED_CERTIFICATE_FILE = STAGED_TLS_DIR / DEFAULT_CERTIFICATE_FILENAME
STAGED_PRIVATEKEY_FILE = STAGED_TLS_DIR / DEFAULT_PRIVATEKEY_FILENAME
TLS_SYNC_TARGETS = (
    (STAGED_CERTIFICATE_FILE, CERTS_DIR / DEFAULT_CERTIFICATE_FILENAME, 0o644),
    (STAGED_CERTIFICATE_FILE, CERTS_DIR / DEFAULT_CERTIFICATE_CRT_FILENAME, 0o644),
    (STAGED_PRIVATEKEY_FILE, CERTS_DIR / DEFAULT_PRIVATEKEY_FILENAME, 0o600),
    (STAGED_CERTIFICATE_FILE, CERTS_DIR / "query_certificate.pem", 0o644),
    (STAGED_PRIVATEKEY_FILE, CERTS_DIR / "query_privatekey.pem", 0o600),
)
DEFAULT_CERTIFICATE_FILE = CERTS_DIR / DEFAULT_CERTIFICATE_FILENAME
DEFAULT_PRIVATEKEY_FILE = CERTS_DIR / DEFAULT_PRIVATEKEY_FILENAME
RUNTIME_STATE_FILE = STATE_DIR / "runtime-info.json"
CAPTURED_LINES_FILE = STATE_DIR / "bootstrap-lines.log"
PROVIDERS_DIR = TEASPEAK_ROOT / "providers"
PROVIDERS_BIN_DIR = PROVIDERS_DIR / "bin"
FFMPEG_CONFIG_FILE = PROVIDERS_DIR / "config_ffmpeg.ini"
YOUTUBE_CONFIG_FILE = PROVIDERS_DIR / "config_youtube.ini"
FFMPEG_WRAPPER_PATH = PROVIDERS_BIN_DIR / "ffmpeg"
YOUTUBE_WRAPPER_PATH = PROVIDERS_BIN_DIR / "youtube-dl"
YOUTUBE_WRAPPER = '#!/bin/sh\nexec /usr/local/bin/yt-dlp "$@"\n'
FFMPEG_CONFIG = "[general]\nffmpeg_command=/ts/providers/bin/ffmpeg\n"
YOUTUBE_CONFIG = "[general]\nyoutubedl_command=/ts/providers/bin/youtube-dl\n"
CERTIFICATE_TIME_FORMAT = "%b %d %H:%M:%S %Y %Z"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state():
    state = {
        "server_version": os.environ.get("SERVER_VERSION", ""),
        "credentials_available": False,
        "server_admin_privilege_key": "",
        "server_query_password": "",
        "server_admin_privilege_key_line": "",
        "server_query_password_line": "",
        "captured_at": "",
        "updated_at": utc_now(),
        "source": "startup-log",
        "tls_certificate_available": False,
        "tls_certificate_host": "",
        "tls_certificate_synced_at": "",
        "database_migrated_at": "",
        "database_migration_source": "",
    }

    if RUNTIME_STATE_FILE.exists():
        try:
            with RUNTIME_STATE_FILE.open("r", encoding="utf-8") as stream:
                saved_state = json.load(stream)
            if isinstance(saved_state, dict):
                state.update(saved_state)
        except (OSError, json.JSONDecodeError):
            pass

    state["server_version"] = state.get("server_version") or os.environ.get(
        "SERVER_VERSION", ""
    )
    state["updated_at"] = utc_now()
    return state


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = RUNTIME_STATE_FILE.with_suffix(".tmp")
    payload = json.dumps(state, ensure_ascii=True, sort_keys=True)
    with temp_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
        stream.write("\n")
    os.replace(temp_path, RUNTIME_STATE_FILE)


def append_matching_line(line):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with CAPTURED_LINES_FILE.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(line.rstrip("\n") + "\n")


def ensure_text_file(path, content, mode=None):
    current = None

    try:
        if path.exists() or path.is_symlink():
            current = path.read_text(encoding="utf-8")
    except OSError:
        current = None

    if current != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    if mode is not None:
        try:
            path.chmod(mode)
        except OSError:
            pass


def write_bytes_file(path, content, mode=None):
    current = None

    try:
        if path.exists() or path.is_symlink():
            current = path.read_bytes()
    except OSError:
        current = None

    if current != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = Path(str(path) + ".tmp")
        temp_path.write_bytes(content)
        os.replace(temp_path, path)

    if mode is not None:
        try:
            path.chmod(mode)
        except OSError:
            pass


def sync_file(source, destination, mode=None, delete_source=False):
    try:
        content = source.read_bytes()
    except OSError:
        return False

    write_bytes_file(destination, content, mode=mode)

    if delete_source:
        try:
            source.unlink()
        except OSError:
            pass

    return True


def remove_file(path):
    try:
        if path.exists() or path.is_symlink():
            path.unlink()
            return True
    except OSError:
        pass

    return False


def clear_tls_targets():
    removed = False

    for _, destination, _ in TLS_SYNC_TARGETS:
        removed = remove_file(destination) or removed

    return removed


def clear_staged_certificates():
    return remove_file(STAGED_CERTIFICATE_FILE) or remove_file(STAGED_PRIVATEKEY_FILE)


def parse_certificate_time(value):
    if not value:
        return None

    try:
        return datetime.strptime(value, CERTIFICATE_TIME_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def read_certificate_metadata(path):
    try:
        return ssl._ssl._test_decode_cert(str(path))
    except (OSError, ValueError):
        return None


def certificate_time_is_valid(metadata):
    now = datetime.now(timezone.utc)
    not_before = parse_certificate_time(metadata.get("notBefore", ""))
    not_after = parse_certificate_time(metadata.get("notAfter", ""))

    if not_before and now < not_before:
        return False
    if not_after and now > not_after:
        return False

    return True


def normalize_hostname(value):
    try:
        return value.strip().rstrip(".").lower().encode("idna").decode("ascii")
    except UnicodeError:
        return value.strip().rstrip(".").lower()


def certificate_dns_names(metadata):
    subject_alt_names = [
        value
        for key, value in metadata.get("subjectAltName", ())
        if key.lower() == "dns"
    ]

    if subject_alt_names:
        return subject_alt_names

    common_names = []
    for relative_distinguished_name in metadata.get("subject", ()):
        for key, value in relative_distinguished_name:
            if key == "commonName":
                common_names.append(value)

    return common_names


def hostname_pattern_matches(pattern, certificate_host):
    normalized_pattern = normalize_hostname(pattern)
    normalized_host = normalize_hostname(certificate_host)

    if normalized_pattern.startswith("*."):
        suffix = normalized_pattern[1:]
        return (
            normalized_host.endswith(suffix)
            and normalized_host != suffix.lstrip(".")
            and normalized_host.count(".") == normalized_pattern.count(".")
        )

    return normalized_pattern == normalized_host


def certificate_hostname_matches(metadata, certificate_host):
    for dns_name in certificate_dns_names(metadata):
        if hostname_pattern_matches(dns_name, certificate_host):
            return True

    return False


def certificate_pair_is_usable(certificate_file, privatekey_file, certificate_host):
    if not certificate_host:
        return False, "missing certificate host"

    if not certificate_file.exists() or not privatekey_file.exists():
        return False, "certificate or private key missing"

    try:
        if certificate_file.stat().st_size == 0 or privatekey_file.stat().st_size == 0:
            return False, "certificate or private key empty"
    except OSError:
        return False, "certificate or private key inaccessible"

    metadata = read_certificate_metadata(certificate_file)
    if not metadata:
        return False, "certificate cannot be decoded"

    if not certificate_time_is_valid(metadata):
        return False, "certificate is not currently valid"

    if not certificate_hostname_matches(metadata, certificate_host):
        subject = metadata.get("subject", ())
        return False, f"certificate does not match {certificate_host}: {subject}"

    return True, ""


def run_python_without_teaspeak_libs(code, *args):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ""

    return subprocess.run(
        [sys.executable, "-c", code, *map(str, args)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def sync_web_certificate_database(certificate_host):
    usable, reason = certificate_pair_is_usable(
        DEFAULT_CERTIFICATE_FILE,
        DEFAULT_PRIVATEKEY_FILE,
        certificate_host,
    )
    if not usable:
        return False, reason

    if not PERSISTENT_DATABASE_FILE.exists():
        return True, "database not initialized yet"

    code = textwrap.dedent(
        """
        import sqlite3
        import sys
        import time
        from pathlib import Path

        db_path = Path(sys.argv[1])
        cert_path = Path(sys.argv[2])
        key_path = Path(sys.argv[3])

        cert_pem = cert_path.read_text(encoding="ascii")
        key_pem = key_path.read_text(encoding="ascii")
        revision = str(int(time.time()))

        conn = sqlite3.connect(str(db_path))
        try:
            table_exists = conn.execute(
                "select 1 from sqlite_master where type='table' and name='general'"
            ).fetchone()
            if not table_exists:
                print("general table does not exist")
                sys.exit(3)

            existing = dict(
                conn.execute(
                    "select key, value from general where key in "
                    "('webcert-cert', 'webcert-key')"
                ).fetchall()
            )
            if (
                existing.get("webcert-cert") == cert_pem
                and existing.get("webcert-key") == key_pem
            ):
                print("web certificate database already current")
                sys.exit(0)

            conn.execute(
                "delete from general where key in "
                "('webcert-revision', 'webcert-cert', 'webcert-key')"
            )
            conn.executemany(
                "insert into general (key, value) values (?, ?)",
                [
                    ("webcert-revision", revision),
                    ("webcert-cert", cert_pem),
                    ("webcert-key", key_pem),
                ],
            )
            conn.commit()
            print("web certificate database updated")
        finally:
            conn.close()
        """
    )
    result = run_python_without_teaspeak_libs(
        code,
        PERSISTENT_DATABASE_FILE,
        DEFAULT_CERTIFICATE_FILE,
        DEFAULT_PRIVATEKEY_FILE,
    )

    if result.stdout:
        print(result.stdout.rstrip(), flush=True)

    return result.returncode in (0, 3), result.stdout.strip()


def clear_web_certificate_database():
    if not PERSISTENT_DATABASE_FILE.exists():
        return True, "database not initialized yet"

    code = textwrap.dedent(
        """
        import sqlite3
        import sys
        from pathlib import Path

        db_path = Path(sys.argv[1])

        conn = sqlite3.connect(str(db_path))
        try:
            table_exists = conn.execute(
                "select 1 from sqlite_master where type='table' and name='general'"
            ).fetchone()
            if not table_exists:
                print("general table does not exist")
                sys.exit(3)

            conn.execute(
                "delete from general where key in "
                "('webcert-revision', 'webcert-cert', 'webcert-key')"
            )
            conn.commit()
            print("web certificate database cleared")
        finally:
            conn.close()
        """
    )
    result = run_python_without_teaspeak_libs(code, PERSISTENT_DATABASE_FILE)

    if result.stdout:
        print(result.stdout.rstrip(), flush=True)

    return result.returncode in (0, 3), result.stdout.strip()


def ensure_symlink(path, target):
    try:
        if path.is_symlink() and os.readlink(path) == target:
            return
        if path.exists() or path.is_symlink():
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
    except OSError:
        pass


def ensure_music_runtime():
    ensure_symlink(FFMPEG_WRAPPER_PATH, "/usr/bin/ffmpeg")
    ensure_text_file(YOUTUBE_WRAPPER_PATH, YOUTUBE_WRAPPER, mode=0o755)
    ensure_text_file(FFMPEG_CONFIG_FILE, FFMPEG_CONFIG)
    ensure_text_file(YOUTUBE_CONFIG_FILE, YOUTUBE_CONFIG)


def migrate_database_from(source_base):
    migrated = False

    for suffix in DATABASE_FILE_SUFFIXES:
        source = Path(str(source_base) + suffix)
        if not source.exists():
            continue

        destination = Path(str(PERSISTENT_DATABASE_FILE) + suffix)
        migrated = sync_file(source, destination, delete_source=True) or migrated

    return migrated


def ensure_persistent_database(state):
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    if PERSISTENT_DATABASE_FILE.exists():
        return False

    migration_source = ""
    migrated = False

    if LEGACY_STAGED_DATABASE_FILE.exists():
        migrated = migrate_database_from(LEGACY_STAGED_DATABASE_FILE)
        if migrated:
            migration_source = "module-state"

    if not migrated and LEGACY_CONTAINER_DATABASE_FILE.exists():
        migrated = migrate_database_from(LEGACY_CONTAINER_DATABASE_FILE)
        if migrated:
            migration_source = "container-root"

    if migrated:
        state["database_migrated_at"] = utc_now()
        state["database_migration_source"] = migration_source
        state["updated_at"] = utc_now()

    return migrated


def ensure_legacy_database_link():
    if LEGACY_CONTAINER_DATABASE_FILE.is_symlink():
        try:
            if LEGACY_CONTAINER_DATABASE_FILE.resolve() == PERSISTENT_DATABASE_FILE:
                return False
        except OSError:
            pass
        LEGACY_CONTAINER_DATABASE_FILE.unlink()

    if LEGACY_CONTAINER_DATABASE_FILE.exists():
        if not PERSISTENT_DATABASE_FILE.exists():
            migrate_database_from(LEGACY_CONTAINER_DATABASE_FILE)
        elif LEGACY_CONTAINER_DATABASE_FILE.is_file():
            LEGACY_CONTAINER_DATABASE_FILE.unlink()

    if not LEGACY_CONTAINER_DATABASE_FILE.exists() and not LEGACY_CONTAINER_DATABASE_FILE.is_symlink():
        LEGACY_CONTAINER_DATABASE_FILE.symlink_to(PERSISTENT_DATABASE_FILE)
        return True

    return False


def update_tls_metadata(state, certificate_host, available, synced):
    changed = False

    if state.get("tls_certificate_available") != available:
        state["tls_certificate_available"] = available
        changed = True

    if state.get("tls_certificate_host") != certificate_host:
        state["tls_certificate_host"] = certificate_host
        changed = True

    if available and (synced or changed or not state.get("tls_certificate_synced_at")):
        state["tls_certificate_synced_at"] = utc_now()
        changed = True

    if changed:
        state["updated_at"] = utc_now()

    return changed


def sync_staged_certificates(state):
    certificate_host = (os.environ.get("TRAEFIK_HOST") or "").strip().lower()

    if not certificate_host:
        cleared = clear_staged_certificates() or clear_tls_targets()
        metadata_changed = update_tls_metadata(
            state,
            certificate_host,
            available=False,
            synced=cleared,
        )
        return cleared or metadata_changed

    staged_valid, staged_reason = certificate_pair_is_usable(
        STAGED_CERTIFICATE_FILE,
        STAGED_PRIVATEKEY_FILE,
        certificate_host,
    )

    if not staged_valid:
        current_valid, current_reason = certificate_pair_is_usable(
            DEFAULT_CERTIFICATE_FILE,
            DEFAULT_PRIVATEKEY_FILE,
            certificate_host,
        )

        clear_staged_certificates()

        if current_valid:
            return update_tls_metadata(
                state,
                certificate_host,
                available=True,
                synced=False,
            )

        cleared = clear_tls_targets()
        print(
            "[ns8teaspeak] TLS certificate unavailable for "
            f"{certificate_host}: staged {staged_reason}; current {current_reason}",
            flush=True,
        )
        metadata_changed = update_tls_metadata(
            state,
            certificate_host,
            available=False,
            synced=cleared,
        )
        return cleared or metadata_changed

    synced = False
    for source, destination, mode in TLS_SYNC_TARGETS:
        synced = sync_file(source, destination, mode=mode) or synced

    metadata_changed = update_tls_metadata(
        state,
        certificate_host,
        available=True,
        synced=synced,
    )
    return synced or metadata_changed


def ensure_valid_web_certificate_ready(state):
    certificate_host = (os.environ.get("TRAEFIK_HOST") or "").strip().lower()
    if not certificate_host:
        return True

    usable, reason = certificate_pair_is_usable(
        DEFAULT_CERTIFICATE_FILE,
        DEFAULT_PRIVATEKEY_FILE,
        certificate_host,
    )
    if not usable:
        state["tls_certificate_available"] = False
        state["tls_certificate_host"] = certificate_host
        state["updated_at"] = utc_now()
        save_state(state)
        print(
            "[ns8teaspeak] Web TLS certificate is not valid for "
            f"{certificate_host}: {reason}",
            flush=True,
        )
        clear_web_certificate_database()
        return False

    synced, sync_message = sync_web_certificate_database(certificate_host)
    if not synced:
        print(
            "[ns8teaspeak] Web certificate database could not be updated: "
            f"{sync_message}",
            flush=True,
        )
        return False

    return True


def build_runtime_path():
    preferred_entries = [
        "/ts/providers/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]
    configured_entries = [
        entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry
    ]
    ordered_entries = []

    for entry in preferred_entries + configured_entries:
        if entry not in ordered_entries:
            ordered_entries.append(entry)

    return os.pathsep.join(ordered_entries)


def extract_credential_value(line, credential_type):
    patterns = []
    if credential_type == "privilege_key":
        patterns = [
            r"(?i)privilege\s+key[^:=]*[:=]\s*['\"]?([^'\"\s]+)['\"]?",
            r"(?i)key[^:=]*[:=]\s*['\"]?([^'\"\s]+)['\"]?",
            r"(?i)token\s*[:=]\s*['\"]?([^'\"\s]+)['\"]?",
        ]
    elif credential_type == "server_query_password":
        patterns = [
            r"(?i)serverquery[^:=]*password[^:=]*[:=]\s*['\"]?([^'\"\s]+)['\"]?",
            r"(?i)password[^:=]*[:=]\s*['\"]?([^'\"\s]+)['\"]?",
        ]

    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1).strip()

    delimiter_match = re.search(r"[:=]\s*['\"]?(.+?)['\"]?\s*$", line)
    if delimiter_match:
        candidate = delimiter_match.group(1).strip().strip("'\"")
        if candidate:
            return candidate

    tokens = re.findall(r"[A-Za-z0-9+/=_-]{8,}", line)
    if tokens:
        return tokens[-1]

    return ""


def update_credential_from_line(state, normalized, value_key, line_key, credential_type):
    updated = False
    value = extract_credential_value(normalized, credential_type)

    if value and not state.get(value_key):
        state[value_key] = value
        state[line_key] = normalized
        updated = True
    elif not state.get(line_key):
        state[line_key] = normalized
        updated = True

    append_matching_line(normalized)
    return updated


def update_capture_status(state):
    updated = False
    credentials_available = bool(
        state.get("server_admin_privilege_key") and state.get("server_query_password")
    )

    if credentials_available and not state.get("captured_at"):
        state["captured_at"] = utc_now()
        updated = True
    if state.get("credentials_available") != credentials_available:
        state["credentials_available"] = credentials_available
        updated = True

    return updated


def capture_credentials(line, state):
    normalized = line.strip()
    lowered = normalized.lower()
    updated = False

    if "serverquery" in lowered and "password" in lowered:
        updated = (
            update_credential_from_line(
                state,
                normalized,
                "server_query_password",
                "server_query_password_line",
                "server_query_password",
            )
            or updated
        )

    if "privilege" in lowered and "key" in lowered:
        updated = (
            update_credential_from_line(
                state,
                normalized,
                "server_admin_privilege_key",
                "server_admin_privilege_key_line",
                "privilege_key",
            )
            or updated
        )

    updated = update_capture_status(state) or updated

    if updated:
        state["updated_at"] = utc_now()

    return updated


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ensure_music_runtime()
    state = load_state()
    state_changed = False
    state_changed = ensure_persistent_database(state) or state_changed
    state_changed = ensure_legacy_database_link() or state_changed
    state_changed = sync_staged_certificates(state) or state_changed
    if state_changed:
        save_state(state)
    save_state(state)
    if not ensure_valid_web_certificate_ready(state):
        sys.exit(1)
    process_env = os.environ.copy()
    process_env["PATH"] = build_runtime_path()

    process = subprocess.Popen(
        [
            "./TeaSpeakServer",
            "-Pgeneral.database.url=sqlite:///ts/database/TeaData.sqlite",
            "-Pquery.ssl.certificate=/ts/certs/query_certificate.pem",
            "-Pquery.ssl.privatekey=/ts/certs/query_privatekey.pem",
            "-Pweb.ssl.certificate=/ts/certs/default_certificate.pem",
            "-Pweb.ssl.certificate.default=/ts/certs/default_certificate.pem",
            "-Pweb.ssl.privatekey=/ts/certs/default_privatekey.pem",
        ],
        cwd=str(TEASPEAK_ROOT),
        env=process_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def forward_signal(signum, _frame):
        if process.poll() is None:
            process.send_signal(signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, forward_signal)

    assert process.stdout is not None

    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        if capture_credentials(line, state):
            save_state(state)

    return_code = process.wait()
    state["updated_at"] = utc_now()
    save_state(state)
    sys.exit(return_code)


if __name__ == "__main__":
    main()