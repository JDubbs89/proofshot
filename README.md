# Proofshot

Proofshot is a Linux CLI screenshot organizer for students, penetration testers, and anyone who needs fast screenshot enumeration, tracking, categorization, and naming. It wraps [Flameshot](https://flameshot.org/) and supports numbered captures, ranges, persistent modules, custom categories, and table listings.

The implementation is split into a CLI interpreter (`proofshot.py`), a project configuration service (`lib/config_service.py`), and a screenshot provider service (`lib/screenshot_service.py`). Flameshot is the default screenshot provider, allowing additional capture backends to be added independently.

Screenshot providers can be swapped persistently:

```bash
proofshot --list-providers
proofshot --provider gnome-screenshot --install
proofshot --provider flameshot
```

Supported providers are `flameshot` and `gnome-screenshot`. Flameshot opens its normal region selector; GNOME Screenshot uses its interactive area selector. The selected provider is stored in `~/.config/proofshot/provider` and is used for subsequent captures. Provider changes verify that the provider is installed; if it is missing, the change fails and leaves the current provider unchanged. Append `--install` to explicitly install the selected provider through the system package manager:

```bash
proofshot --provider gnome-screenshot --install
proofshot --provider flameshot --install
```

The normal Proofshot installer installs only the default Flameshot dependencies. It does not install `gnome-screenshot` unless you explicitly request it with the provider command.

Project configuration can be inspected and edited from the CLI:

```bash
proofshot -D ./AcmeWeb --show-config
proofshot --show-columns
proofshot --set-prefix 'Lab-{directory}-{project}Q'
proofshot --set-suffix '-{category}-{environment}'
proofshot --set-variable project AcmeWeb
proofshot --set-variable environment prod
proofshot --set-index-label Fig
proofshot --set-column-suffix Evidence '-evidence'
```

Built-in naming variables are `{directory}`, `{category}`, and `{number}`. Additional variables set with `--set-variable NAME VALUE` can be used in global or column-specific prefix and suffix templates.

Current version: `0.2.6`

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

To capture a replacement at an exact index, combine `-N` with `-I`:

```bash
proofshot -N -I 3       # capture/replace the selected category's Q3 screenshot
proofshot -P -N -I 3    # capture/replace Proof Q3
```

The index is committed only after Flameshot successfully saves the image. Cancelling a capture leaves the counter and existing screenshot unchanged. Use `--force` to replace an existing screenshot without the overwrite prompt.

### Project management

Project settings and screenshots can be changed from the command line. These commands use the persisted directory, or the directory supplied with `-D`:

```bash
proofshot --add-column Finding
proofshot --rename-column Form Question
proofshot --remove-column Finding
proofshot --add-screenshot ~/Pictures/extra.png
proofshot --remove-screenshot AcmeWebQ3.png
```

Column changes update `.proofshot.json` and preserve or remove the matching counter. The built-in Form and Proof columns cannot be removed; rename them if needed. Screenshot management accepts PNG files only, and `--force` allows an added screenshot to replace an existing file with the same name.

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

### Configuration and naming editor

Counters are stored in `~/.config/proofshot/counts.json`; the selected directory is stored in `~/.config/proofshot/last_dir`; the selected screenshot provider is stored in `~/.config/proofshot/provider`.

Configuration commands operate on the persisted directory, or on a directory selected with `-D`:

```bash
proofshot --show-config
proofshot --show-columns
proofshot --set-prefix 'Lab-{directory}-{project}Q'
proofshot --set-suffix '-{category}-{environment}'
proofshot --set-column-prefix Evidence 'Evidence-{project}-Q'
proofshot --set-column-suffix Evidence '-evidence'
proofshot --set-variable project AcmeWeb
proofshot --set-variable environment prod
```

`--show-config` prints the complete JSON configuration. `--show-columns` prints the configured column order and effective templates. The index label defaults to `Q`, producing names such as `Q1` and `Q2`; `--set-index-label Fig` changes this to `Fig1`, `Fig2`, and so on. The `-L` table uses the configured label in its index column and current-index summary. Prefix and suffix settings are saved per project and can contain `{directory}`, `{category}`, `{number}`, and `{index_label}`. Variables created with `--set-variable NAME VALUE` can also be used in templates. Unknown variables are left unchanged in generated names.

Each successfully captured screenshot is recorded in the project-root `.manifest.json`. The manifest stores a SHA-256 hash of the image content, its index or range, category, and filename. `-L` uses this content mapping first, so renaming a screenshot does not lose its index/category association; older screenshots without manifest entries continue to use filename matching.

### Upgrading projects

Project configs now record the Proofshot compatibility version. Projects without `proofshot_version` are treated as version `0.2.5` or older and continue using the legacy filename convention for discovery. Upgrade a project with:

```bash
proofshot --upgrade-project
```

This adds the current version to `.proofshot.json` and migrates legacy filename-based screenshot mappings into `.manifest.json`. Existing screenshots are not renamed or modified.

### Packaging screenshots

Use `--package` to interactively create `proofshot-package.zip` in the current project:

```bash
proofshot --package
```

Enter a column name or zero-based column index, then enter an index range such as `1-5`. Leave the range blank to include every mapped index in that column. Repeat for additional columns, then leave the column prompt blank to finish. Use `--force` to replace an existing package. Packaging uses the manifest mapping, so renamed screenshots are included under their current filenames.

`proofshot --init NAME` creates a project-local `.proofshot.json` from the repository’s `default_config.json` template. Existing config files are never overwritten. Naming and category settings are stored per project in `<project-directory>/.proofshot.json`:

```json
{
  "form_category": "Form",
  "proof_category": "Proof",
  "filename_prefix": "{directory}Q",
  "filename_suffix": "{category}",
  "variables": {
    "project": "AcmeWeb",
    "environment": "prod"
  },
  "categories": {
    "Form": {
      "suffix": ""
    },
    "Proof": {
      "suffix": "{category}"
    }
  }
}
```

`filename_prefix` and `filename_suffix` are global defaults. Entries under `categories` override them for individual categories. `{directory}` is replaced with the destination folder name and `{category}` with the selected category. The prefix controls everything before the number, including the `Q` marker. The default prefix is `{directory}Q`, preserving names such as `AcmeWebQ1.png`; Proof and custom categories retain their category suffix. Put this file inside each project directory to customize that project independently. For example:

```json
{
  "form_category": "Question",
  "proof_category": "Verified",
  "filename_prefix": "Lab-{directory}Q",
  "filename_suffix": "-{category}",
  "categories": {
    "Finding": {
      "prefix": "Finding-",
      "suffix": "-{category}"
    },
    "Evidence": {
      "prefix": "Evidence-Q",
      "suffix": ""
    }
  }
}
```

Custom columns are created from the command line or declared in the project config. For example, adding `Finding` and `Evidence` to `categories` makes them available for that project:

```bash
proofshot -C Finding -N
proofshot -C Evidence -N
```

Declared category columns can also be selected by zero-based number with `-C 2`, `-C 3`, and so on. The built-in categories occupy the earlier columns according to the project configuration and saved counters.

## Requirements

- Python 3.10+
- Flameshot 0.10 or newer, with `flameshot gui --raw`, or `gnome-screenshot`
- Optional: `zenity` and `notify-send`; `gnome-screenshot` is installed separately with `proofshot --provider gnome-screenshot --install`

Run `proofshot --help` for the complete CLI reference.

Check the installed version with:

```bash
proofshot --version
```
