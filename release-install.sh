#!/usr/bin/env bash
set -euo pipefail

repo="JDubbs89/proofshot"
api_url="https://api.github.com/repos/${repo}/releases/latest"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

archive_url="$(curl -fsSL "$api_url" | sed -n 's/.*"browser_download_url": "\([^"]*\.tar\.gz\)".*/\1/p' | head -n 1)"
[[ -n "$archive_url" ]] || { echo "No packaged GitHub release found." >&2; exit 1; }

curl -fsSL "$archive_url" -o "$tmp_dir/proofshot.tar.gz"
tar -xzf "$tmp_dir/proofshot.tar.gz" -C "$tmp_dir"
release_dir="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
[[ -n "$release_dir" ]] || { echo "Release archive is invalid." >&2; exit 1; }

PROOFSHOT_SKIP_DEPS="${PROOFSHOT_SKIP_DEPS:-0}" "$release_dir/install.sh"
