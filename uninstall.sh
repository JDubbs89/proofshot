#!/usr/bin/env bash
set -euo pipefail

bin_dir="${PROOFSHOT_BIN_DIR:-${HOME}/.local/bin}"
target="$bin_dir/proofshot"

if [[ -e "$target" || -L "$target" ]]; then
  rm -f "$target"
  printf 'Removed %s\n' "$target"
else
  printf 'proofshot is not installed at %s\n' "$target"
fi

if [[ "${1:-}" == "--purge" ]]; then
  state_dir="${HOME}/.config/proofshot"
  if [[ -d "$state_dir" ]]; then
    rm -rf "$state_dir"
    printf 'Removed saved configuration: %s\n' "$state_dir"
  fi
else
  printf 'Saved configuration was kept. Use --purge to remove it.\n'
fi
