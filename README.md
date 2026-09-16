# Proofshot

Proofshot is a Linux CLI screenshot organizer for students, penetration testers, and anyone who needs fast screenshot enumeration, tracking, categorization, and naming. It wraps [Flameshot](https://flameshot.org/) and supports numbered captures, ranges, persistent modules, custom categories, and table listings.

Current version: `0.1.7`

## Install

### Install from the latest GitHub release

Recommended one-liner for all supported distributions:

```bash
curl -fsSL https://raw.githubusercontent.com/JDubbs89/proofshot/main/release-install.sh | bash
```

The installer queries GitHub’s `releases/latest` endpoint, downloads that release’s packaged archive, installs dependencies, and updates the local command. Use `PROOFSHOT_SKIP_DEPS=1` before `bash` to skip dependency installation.

### Install from source

Clone the repository directly:

```bash
git clone https://github.com/JDubbs89/proofshot.git && cd proofshot && ./install.sh
```

Or use a distro-specific one-liner:

Debian / Ubuntu:
```bash
sudo apt-get update && sudo apt-get install -y git && git clone https://github.com/JDubbs89/proofshot.git && cd proofshot && ./install.sh
```

Fedora / RHEL:
```bash
sudo dnf install -y git && git clone https://github.com/JDubbs89/proofshot.git && cd proofshot && ./install.sh
```

Arch Linux:
```bash
sudo pacman -Sy --needed --noconfirm git && git clone https://github.com/JDubbs89/proofshot.git && cd proofshot && ./install.sh
```

openSUSE:
```bash
sudo zypper --non-interactive install git && git clone https://github.com/JDubbs89/proofshot.git && cd proofshot && ./install.sh
```

### Dependencies and updates

The installer gathers `flameshot`, `zenity`, and `libnotify` using `apt`, `dnf`, `pacman`, or `zypper`. It may ask for `sudo`. Set `PROOFSHOT_SKIP_DEPS=1` to skip dependency installation. Running `install.sh` again from the checkout pulls fast-forward updates and reinstalls the command. Set `PROOFSHOT_BIN_DIR=/usr/local/bin` for a system-wide install (with appropriate permissions).

Once installed, update Proofshot directly:

```bash
proofshot --update
```

This downloads and installs the latest published GitHub release.

Maintainers publish a release by updating `__version__` in `proofshot.py` and pushing to `main`. GitHub Actions uses that Python version, creates a `v<version>` tag, and packages the archive automatically. The workflow does not modify or push repository files. If that release already exists, the workflow does nothing.

### Uninstall

From a cloned checkout:

```bash
./uninstall.sh
```

This removes the executable and keeps saved settings. To also remove the persisted directory and category counters:

```bash
./uninstall.sh --purge
```

For a release installation without cloning the repository:

```bash
curl -fsSL https://raw.githubusercontent.com/JDubbs89/proofshot/main/uninstall.sh | bash
```

If the installed command is available, it can uninstall itself:

```bash
proofshot --uninstall
```

This removes the executable but preserves saved settings and counters. Use `./uninstall.sh --purge` from a checkout to remove those as well.

## Basic usage

```bash
proofshot --init ModuleName
proofshot -N
proofshot -P -N
proofshot -C Finding -N
proofshot -Q 5-7 -C Evidence
proofshot -L
```

`-D PATH` sets and persists the destination, `-W` displays it, and `-I NUMBER` sets the selected category's current index. `-N STEP` advances a category counter; add `-S` to capture the complete range from the previous index.

### Categories and naming

`Form` and `Proof` remain available for compatibility. `proofshot -N` uses category column `0` by default (the first category column after `Question`, which is `Form`). Use `-C NAME` to create or select categories such as `Evidence` or `Finding`; each gets its own counter. Use `-C 0`, `-C 1`, and so on to select zero-based category columns shown by `-L`. Use `--name PREFIX` to customize the filename prefix:

```bash
proofshot --name LoginPageQ -C Evidence -N
# LoginPageQ1Evidence.png
```

## Usage examples

Capture normal and proof screenshots for a module:

```bash
proofshot --init AcmeWeb
proofshot -N                  # AcmeWebQ1.png, Form column 0
proofshot -P -N               # AcmeWebQ1Proof.png
proofshot -P -I 4             # set Proof's current index to 4
proofshot -P -N               # AcmeWebQ5Proof.png
```

Capture ranges and move through indices:

```bash
proofshot -Q 10 -f            # AcmeWebQ10.png
proofshot -N 3 -f             # advance Form by 3
proofshot -N 2 -S -f          # capture the next two-question span
```

Custom column names have independent counters and become filename suffixes:

```bash
proofshot -C Finding -N       # AcmeWebQ1Finding.png
proofshot -C Evidence -N      # AcmeWebQ1Evidence.png
proofshot -C Finding -I 7     # Finding's next index will be Q8
proofshot -C Finding -N       # AcmeWebQ8Finding.png
```

Run `proofshot -L` to see category columns. Numeric categories are zero-based: `-C 0` selects the first category column after `Question`, `-C 1` the second, and so on. Names such as `-C Evidence` can always be used directly.

### Configuration

Counters are stored in `~/.config/proofshot/counts.json`; the selected directory is stored in `~/.config/proofshot/last_dir`.

`proofshot --init NAME` creates a project-local `.proofshot.json` from the repository’s `default_config.json` template. Existing config files are never overwritten. Naming and category settings are stored per project in `<project-directory>/.proofshot.json`:

```json
{
  "form_category": "Form",
  "proof_category": "Proof",
  "filename_prefix": "{directory}Q",
  "filename_suffix": "{category}"
}
```

`{directory}` is replaced with the destination folder name and `{category}` with the selected category. The prefix controls everything before the number, including the `Q` marker. The default prefix is `{directory}Q`, preserving names such as `AcmeWebQ1.png`; Proof and custom categories retain their category suffix. Put this file inside each project directory to customize that project independently. For example, this configuration renames the default columns and adds a fixed prefix:

```json
{
  "form_category": "Question",
  "proof_category": "Verified",
  "filename_prefix": "Lab-{directory}Q",
  "filename_suffix": "-{category}"
}
```

## Requirements

- Python 3.10+
- Flameshot 0.10 or newer, with `flameshot gui --raw`
- Optional: `zenity` and `notify-send`

Run `proofshot --help` for the complete CLI reference.

Check the installed version with:

```bash
proofshot --version
```
