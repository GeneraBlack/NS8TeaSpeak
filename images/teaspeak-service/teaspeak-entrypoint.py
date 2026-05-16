#!/usr/bin/env python3

import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
from datetime import datetime, timezone


STATE_DIR = Path(os.environ.get("TEASPEAK_STATE_DIR", "/ts/module_state"))
RUNTIME_STATE_FILE = STATE_DIR / "runtime-info.json"
CAPTURED_LINES_FILE = STATE_DIR / "bootstrap-lines.log"
PROVIDERS_DIR = Path("/ts/providers")
PROVIDERS_BIN_DIR = PROVIDERS_DIR / "bin"
FFMPEG_CONFIG_FILE = PROVIDERS_DIR / "config_ffmpeg.ini"
YOUTUBE_CONFIG_FILE = PROVIDERS_DIR / "config_youtube.ini"
FFMPEG_WRAPPER_PATH = PROVIDERS_BIN_DIR / "ffmpeg"
YOUTUBE_WRAPPER_PATH = PROVIDERS_BIN_DIR / "youtube-dl"
YOUTUBE_WRAPPER = '#!/bin/sh\nexec /usr/bin/python3 /usr/bin/yt-dlp "$@"\n'
FFMPEG_CONFIG = "[general]\nffmpeg_command=/ts/providers/bin/ffmpeg\n"
YOUTUBE_CONFIG = "[general]\nyoutubedl_command=/ts/providers/bin/youtube-dl\n"


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
    save_state(state)
    process_env = os.environ.copy()
    process_env["PATH"] = build_runtime_path()

    process = subprocess.Popen(
        ["./TeaSpeakServer"],
        cwd="/ts",
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