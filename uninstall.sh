#!/usr/bin/env bash
set -euo pipefail

bin_dir="${PROOFSHOT_BIN_DIR:-${HOME}/.local/bin}"
target="$bin_dir/proofshot"

remove_installed_file() {
  local path="$1"
  if [[ -e "$path" || -L "$path" ]]; then
    rm -f "$path"
    printf 'Removed %s\n' "$path"
  fi
}

if [[ -e "$target" || -L "$target" ]]; then
  rm -f "$target"
  printf 'Removed %s\n' "$target"
else
  printf 'proofshot is not installed at %s\n' "$target"
fi

remove_installed_file "$bin_dir/proofshot-gui"
remove_installed_file "$bin_dir/default_config.json"
if [[ -f "$bin_dir/lib/config_service.py" ]]; then
  rm -rf "$bin_dir/lib"
  printf 'Removed %s\n' "$bin_dir/lib"
fi
if [[ -f "$bin_dir/ui/main_window.ui" ]]; then
  remove_installed_file "$bin_dir/ui/main_window.ui"
  rmdir "$bin_dir/ui" 2>/dev/null || true
fi
remove_installed_file "${XDG_DATA_HOME:-${HOME}/.local/share}/applications/proofshot.desktop"
if [[ -n "${PROOFSHOT_DESKTOP_DIR:-}" ]]; then
  desktop_dir="$PROOFSHOT_DESKTOP_DIR"
elif command -v xdg-user-dir >/dev/null 2>&1; then
  desktop_dir="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
  desktop_dir="${desktop_dir:-${HOME}/Desktop}"
else
  desktop_dir="${HOME}/Desktop"
fi
remove_installed_file "$desktop_dir/proofshot.desktop"

if [[ "${1:-}" == "--purge" ]]; then
  state_dir="${HOME}/.config/proofshot"
  if [[ -d "$state_dir" ]]; then
    rm -rf "$state_dir"
    printf 'Removed saved configuration: %s\n' "$state_dir"
  fi
else
  printf 'Saved configuration was kept. Use --purge to remove it.\n'
fi
