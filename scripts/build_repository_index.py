#!/usr/bin/env python3

import argparse
import copy
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_REPOSITORY_DIR = Path("repository")
DEFAULT_VERSION_FILE = Path("VERSION")
DEFAULT_BOOTSTRAP_SOURCE_TAG = "latest"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


class RegistryError(RuntimeError):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a static NS8 software repository index from local metadata and GHCR tags."
    )
    parser.add_argument(
        "--repository-dir",
        default=str(DEFAULT_REPOSITORY_DIR),
        help="Directory that contains module metadata folders and the generated repodata.json.",
    )
    parser.add_argument(
        "--version-file",
        default=str(DEFAULT_VERSION_FILE),
        help="File that contains the bootstrap semantic version for the first stable release.",
    )
    parser.add_argument(
        "--bootstrap-source-tag",
        default=DEFAULT_BOOTSTRAP_SOURCE_TAG,
        help="Registry tag used as a template before the first semantic version exists.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the checked-in repodata.json instead of overwriting it.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def is_semver(tag: str) -> bool:
    return SEMVER_RE.match(tag) is not None


def semver_sort_key(tag: str):
    match = SEMVER_RE.match(tag)
    if not match:
        return (-1, -1, -1, -1, ())

    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    prerelease = match.group(4)
    if prerelease is None:
        prerelease_weight = 1
        prerelease_key = ()
    else:
        prerelease_weight = 0
        prerelease_key = tuple(_parse_prerelease_part(part) for part in prerelease.split("."))
    return (major, minor, patch, prerelease_weight, prerelease_key)


def _parse_prerelease_part(part: str):
    if part.isdigit():
        return (0, int(part))
    return (1, part)


def is_testing(tag: str) -> bool:
    match = SEMVER_RE.match(tag)
    return bool(match and match.group(4))


def ghcr_get_json(image_path: str, endpoint: str, accept: str | None = None):
    token_url = (
        "https://ghcr.io/token?service=ghcr.io&scope="
        + urllib.parse.quote(f"repository:{image_path}:pull", safe=":")
    )
    with urllib.request.urlopen(token_url) as response:
        token_payload = json.load(response)
    token = token_payload["token"]

    request = urllib.request.Request(
        f"https://ghcr.io/v2/{image_path}/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if accept:
        request.add_header("Accept", accept)

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as ex:
        details = ex.read().decode("utf-8", errors="replace")
        raise RegistryError(f"GHCR request failed for {image_path}/{endpoint}: {details}") from ex


def fetch_tags(image_path: str) -> list[str]:
    payload = ghcr_get_json(image_path, "tags/list")
    return payload.get("tags", []) or []


def fetch_labels(image_path: str, tag: str) -> dict:
    accept = ", ".join(
        [
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.v2+json",
        ]
    )
    manifest = ghcr_get_json(image_path, f"manifests/{tag}", accept=accept)
    config_digest = manifest.get("config", {}).get("digest")
    if not config_digest:
        raise RegistryError(f"Image {image_path}:{tag} has no config digest")

    blob = ghcr_get_json(image_path, f"blobs/{config_digest}")
    return blob.get("config", {}).get("Labels", {}) or {}


def rewrite_embedded_image_tags(labels: dict, target_tag: str) -> dict:
    rewritten = copy.deepcopy(labels)
    images = rewritten.get("org.nethserver.images")
    if not images:
        return rewritten

    image_refs = []
    for image_ref in images.split():
        if ":" not in image_ref:
            image_refs.append(image_ref)
            continue
        image_name, _tag = image_ref.rsplit(":", 1)
        image_refs.append(f"{image_name}:{target_tag}")
    rewritten["org.nethserver.images"] = " ".join(image_refs)
    return rewritten


def collect_versions(metadata: dict, bootstrap_version: str, bootstrap_source_tag: str) -> list[dict]:
    source = metadata["source"]
    if not source.startswith("ghcr.io/"):
        raise RegistryError(f"Unsupported source registry for {source}")

    image_path = source.removeprefix("ghcr.io/")
    tags = fetch_tags(image_path)
    semver_tags = sorted((tag for tag in tags if is_semver(tag)), key=semver_sort_key, reverse=True)

    versions = []
    for tag in semver_tags:
        versions.append(
            {
                "tag": tag,
                "testing": is_testing(tag),
                "labels": fetch_labels(image_path, tag),
            }
        )

    if bootstrap_version and bootstrap_version not in {version["tag"] for version in versions}:
        bootstrap_labels = rewrite_embedded_image_tags(
            fetch_labels(image_path, bootstrap_source_tag), bootstrap_version
        )
        versions.insert(
            0,
            {
                "tag": bootstrap_version,
                "testing": False,
                "labels": bootstrap_labels,
            },
        )

    return versions


def load_metadata(module_dir: Path) -> dict:
    metadata_path = module_dir / "metadata.json"
    metadata = json.loads(read_text(metadata_path))
    metadata["id"] = module_dir.name
    metadata["logo"] = "logo.png" if (module_dir / "logo.png").is_file() else None
    screenshots_dir = module_dir / "screenshots"
    metadata["screenshots"] = []
    if screenshots_dir.is_dir():
        metadata["screenshots"] = [
            f"screenshots/{path.name}"
            for path in sorted(screenshots_dir.iterdir())
            if path.is_file() and path.suffix.lower() == ".png"
        ]
    return metadata


def build_index(repository_dir: Path, version_file: Path, bootstrap_source_tag: str) -> list[dict]:
    bootstrap_version = read_text(version_file)
    index = []
    for module_dir in sorted(path for path in repository_dir.iterdir() if path.is_dir()):
        metadata = load_metadata(module_dir)
        metadata["versions"] = collect_versions(metadata, bootstrap_version, bootstrap_source_tag)
        if not metadata["versions"]:
            raise RegistryError(f"No semantic versions available for {metadata['source']}")
        index.append(metadata)
    return index


def main():
    args = parse_args()
    repository_dir = Path(args.repository_dir)
    version_file = Path(args.version_file)
    output_path = repository_dir / "repodata.json"

    index = build_index(repository_dir, version_file, args.bootstrap_source_tag)
    rendered = json.dumps(index, indent=2, ensure_ascii=True) + "\n"

    if args.check:
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            print(f"{output_path} is out of date", file=sys.stderr)
            return 1
        return 0

    output_path.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())