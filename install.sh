#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="${PROOFSHOT_BIN_DIR:-${HOME}/.local/bin}"

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
desktop_dir="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
mkdir -p "$desktop_dir"
cat > "$desktop_dir/proofshot.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Proofshot
Comment=Browse and manage Proofshot projects
Exec=$bin_dir/proofshot-gui
Terminal=false
Categories=Graphics;Utility;
EOF
printf 'Installed proofshot to %s/proofshot\n' "$bin_dir"
printf 'Installed GUI launcher to %s/proofshot-gui\n' "$bin_dir"
printf 'Ensure %s is on PATH.\n' "$bin_dir"
