#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="${PROOFSHOT_BIN_DIR:-${HOME}/.local/bin}"
mkdir -p "$bin_dir"
if git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$repo_dir" pull --ff-only
fi
install -m 0755 "$repo_dir/proofshot.py" "$bin_dir/proofshot"
printf 'Installed proofshot to %s/proofshot\n' "$bin_dir"
printf 'Ensure %s is on PATH.\n' "$bin_dir"
