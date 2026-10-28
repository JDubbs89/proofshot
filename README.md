# Proofshot

## About

Proofshot is a Linux CLI screenshot organizer for penetration testers, students, and anyone who needs repeatable screenshot indexing. It captures through selectable providers, names images consistently, tracks project columns, lists related images, and packages them for export.

Current version: `0.3.0`

The 0.3.0 GUI is available as an optional PySide6 interface while the CLI remains the default lightweight installation.

## Features

- Configurable index labels (`Q1`, `Fig1`, etc.)
- Form, Proof, and custom project columns
- Direct indices, ranges, spans, and replacement captures
- Persistent project configuration and counters
- Content-based manifests that survive file renames
- Interactive ZIP packaging by column and range
- Flameshot, GNOME Screenshot, and native wlroots (Grim + Slurp) providers
- Legacy project upgrades

## Requirements

- Python 3.10+
- Flameshot 0.10+ with `flameshot gui --raw`, `gnome-screenshot`, or Grim + Slurp
- Optional: `zenity` and `notify-send`

## Installation

### Latest release

```bash
curl -fsSL https://raw.githubusercontent.com/JDubbs89/proofshot/main/release-install.sh | bash
```

The normal installer installs the default Flameshot dependencies. Set `PROOFSHOT_SKIP_DEPS=1` to skip dependency installation.

### From source

```bash
git clone https://github.com/JDubbs89/proofshot.git
cd proofshot
./install.sh
```

The installer supports `apt`, `dnf`, `pacman`, and `zypper`. Use `PROOFSHOT_BIN_DIR=/usr/local/bin` for a system-wide installation.

### Update and uninstall

```bash
proofshot --update
proofshot --uninstall
```

From a checkout, use `./uninstall.sh`. Saved project settings and counters are preserved by default.

## Quick start

```bash
proofshot --init AcmeWeb
proofshot -N                  # AcmeWebQ1.png
proofshot -P -N              # AcmeWebQ1Proof.png
proofshot -L                 # list indexed screenshots
proofshot -V 5               # open the image at index 5
proofshot -W                 # show the current project
```

`-D PATH` selects and persists a project directory.

## How to use

### Capture and index screenshots

```bash
proofshot -Q 5               # capture index 5
proofshot -Q 5-7             # capture a range
proofshot -N                 # advance by one
proofshot -N 2               # advance by two
proofshot -N 2 -S            # capture the complete next span
proofshot -N -I 3 --force    # replace the screenshot at index 3
proofshot -P -N              # capture in the Proof column
proofshot -I 4               # set the selected column's current index
```

Counters are committed only after a successful capture. Cancelling a provider leaves the counter unchanged.

### Columns

```bash
proofshot --add-column Evidence
proofshot -C Evidence -N
proofshot --rename-column Evidence Findings
proofshot --remove-column Findings
proofshot -C 0 -N
```

Columns are zero-based when selected numerically. Form and Proof cannot be removed, but they can be renamed.

### Index labels and naming

The default index label is `Q`. Change it per project:

```bash
proofshot --set-index-label Fig
proofshot -N                  # AcmeWebFig1.png
```

Configure global or per-column templates:

```bash
proofshot --set-prefix '{directory}{index_label}'
proofshot --set-suffix '-{category}'
proofshot --set-column-prefix Evidence 'Evidence-{project}-'
proofshot --set-column-suffix Evidence '-evidence'
proofshot --set-variable project AcmeWeb
```

Built-in variables are `{directory}`, `{category}`, `{number}`, and `{index_label}`. Add custom variables with `--set-variable NAME VALUE`.

### Listing screenshots

```bash
proofshot -L
```

The listing uses `.manifest.json` content hashes first, so renamed screenshots retain their index and category. Older screenshots use legacy filename discovery.

## Project configuration

```bash
proofshot --show-config
proofshot --show-columns
proofshot --upgrade-project
```

Settings are stored in `<project>/.proofshot.json`. New configurations include `proofshot_version`; files without one are treated as `0.2.5` or older and use legacy filename discovery until upgraded.

Successful captures are recorded in `<project>/.manifest.json` with a SHA-256 hash, index/range, category, and filename.

Each project stores its current column indices in `<project>/.proofshot-counts.json`. Opening a project restores the Form, Proof, and custom-column indices you last used in that project.

## Screenshot providers

Flameshot is the default provider. GNOME Screenshot and a native wlroots provider are also supported:

```bash
proofshot --list-providers
proofshot --provider gnome-screenshot --install
proofshot --provider flameshot
proofshot --provider grim-slurp --install
```

`grim-slurp` opens Slurp's region selector and captures the selection with Grim.
It is intended for Hyprland and other wlroots compositors, and does not use the
XDG desktop portal.

Provider changes verify dependencies before saving the new selection. `--install` must be explicitly provided to install a provider. The selection is stored in `~/.config/proofshot/provider`.

## Packaging screenshots

```bash
proofshot --package
```

Enter a column name or index, then a range such as `1-5`. Leave the range blank for all indices in that column. Repeat for more columns, then leave the column prompt blank to finish. The output is `proofshot-package.zip`; use `--force` to replace it.

## Storage and architecture

Global state is stored in `~/.config/proofshot/`:

- `last_dir` — current project directory
- `provider` — selected screenshot provider

Current column indices are stored in each project rather than global state.

The code is organized as:

- `proofshot.py` — screenshot workflow orchestration
- `lib/cli_service.py` — CLI argument definitions, operation registration, and combination validation
- `lib/config_service.py` — configuration, counters, manifests, and upgrades
- `lib/screenshot_service.py` — provider interface and implementations
- `lib/package_service.py` — ZIP packaging

Run `proofshot --help` for the complete command reference.

## Development

### Optional GUI

Install PySide6 in the environment used by Proofshot, then launch with:

```bash
proofshot --gui
proofshot-gui
```

The GUI stores ordered discovery paths in `~/.config/proofshot/workspace.json`. It discovers immediate child directories as projects and uses each project's existing `.proofshot.json` and `.manifest.json` files as the source of truth.

The release workflow reads `__version__` from `proofshot.py`, creates a matching `v<version>` tag, and packages the source with `lib/`.
