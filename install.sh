#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="${PROOFSHOT_BIN_DIR:-${HOME}/.local/bin}"

desktop_directory() {
  local directory
  if [[ -n "${PROOFSHOT_DESKTOP_DIR:-}" ]]; then
    printf '%s\n' "$PROOFSHOT_DESKTOP_DIR"
  elif command -v xdg-user-dir >/dev/null 2>&1; then
    directory="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
    printf '%s\n' "${directory:-${HOME}/Desktop}"
  else
    printf '%s\n' "${HOME}/Desktop"
  fi
}

write_desktop_entry() {
  local target="$1"
  local mode="$2"
  mkdir -p "$(dirname "$target")"
  cat > "$target" <<EOF
[Desktop Entry]
Type=Application
Name=Proofshot
Comment=Browse and manage Proofshot projects
Exec="$bin_dir/proofshot-gui"
Terminal=false
Icon=camera-photo
Categories=Graphics;Utility;
StartupNotify=true
EOF
  chmod "$mode" "$target"
}

desktop_shortcut_choice() {
  local choice="${PROOFSHOT_DESKTOP_SHORTCUT:-}"
  if [[ -z "$choice" ]]; then
    if [[ -t 0 ]]; then
      printf 'Do you want to create a desktop shortcut? [y/N] ' >&2
      IFS= read -r choice || choice="n"
    elif [[ -r /dev/tty && -w /dev/tty ]]; then
      printf 'Do you want to create a desktop shortcut? [y/N] ' > /dev/tty 2>/dev/null || true
      IFS= read -r choice < /dev/tty 2>/dev/null || choice="n"
    else
      choice="n"
    fi
  fi
  case "$choice" in
    y|Y|yes|YES|Yes|1|true|TRUE|True) return 0 ;;
    n|N|no|NO|No|0|false|FALSE|False|"") return 1 ;;
    *) printf 'Expected y or n for the desktop shortcut choice, got: %s\n' "$choice" >&2; return 2 ;;
  esac
}

install_dependencies() {
  [[ "${PROOFSHOT_SKIP_DEPS:-0}" == "1" ]] && return
  if command -v flameshot >/dev/null 2>&1 && command -v zenity >/dev/null 2>&1; then
    printf 'Runtime dependencies already installed.\n'
    return
  fi
  local runner=()
  if [[ "$(id -u)" -ne 0 ]]; then
    command -v sudo >/dev/null 2>&1 || { printf 'sudo is required; set PROOFSHOT_SKIP_DEPS=1 to skip.\n' >&2; return 1; }
    runner=(sudo)
  fi
  if command -v apt-get >/dev/null 2>&1; then
    "${runner[@]}" apt-get update
    "${runner[@]}" apt-get install -y flameshot zenity libnotify-bin
  elif command -v dnf >/dev/null 2>&1; then
    "${runner[@]}" dnf install -y flameshot zenity libnotify
  elif command -v pacman >/dev/null 2>&1; then
    "${runner[@]}" pacman -Sy --needed --noconfirm flameshot zenity libnotify
  elif command -v zypper >/dev/null 2>&1; then
    "${runner[@]}" zypper --non-interactive install flameshot zenity libnotify
  else
    printf 'No supported package manager found; install flameshot and zenity manually.\n' >&2
  fi
}

install_dependencies

mkdir -p "$bin_dir"
if git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$repo_dir" pull --ff-only
fi
install -m 0755 "$repo_dir/proofshot.py" "$bin_dir/proofshot"
cat > "$bin_dir/proofshot-gui" <<EOF
#!/usr/bin/env bash
exec "$bin_dir/proofshot" --gui "\$@"
EOF
chmod 0755 "$bin_dir/proofshot-gui"
rm -rf "$bin_dir/lib"
cp -R "$repo_dir/lib" "$bin_dir/lib"
install -m 0644 "$repo_dir/default_config.json" "$bin_dir/default_config.json"
mkdir -p "$bin_dir/ui"
install -m 0644 "$repo_dir/ui/main_window.ui" "$bin_dir/ui/main_window.ui"
desktop_dir="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
write_desktop_entry "$desktop_dir/proofshot.desktop" 0644

desktop_shortcut="$(desktop_directory)/proofshot.desktop"
if [[ -e "$desktop_shortcut" || -L "$desktop_shortcut" ]]; then
  printf 'Desktop shortcut already exists at %s; skipping prompt.\n' "$desktop_shortcut"
elif desktop_shortcut_choice; then
  write_desktop_entry "$desktop_shortcut" 0755
  printf 'Created desktop shortcut at %s\n' "$desktop_shortcut"
else
  choice_status=$?
  [[ "$choice_status" -ne 2 ]] || exit "$choice_status"
fi
printf 'Installed proofshot to %s/proofshot\n' "$bin_dir"
printf 'Installed GUI launcher to %s/proofshot-gui\n' "$bin_dir"
printf 'Ensure %s is on PATH.\n' "$bin_dir"
