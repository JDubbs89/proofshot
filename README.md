# Proofshot

Proofshot is a Linux CLI screenshot organizer for students, penetration testers, and anyone who needs fast screenshot enumeration, tracking, categorization, and naming. It wraps [Flameshot](https://flameshot.org/) and supports numbered captures, ranges, persistent modules, custom categories, and table listings.

## Install

```bash
git clone https://github.com/JDubbs89/proofshot.git
cd proofshot
./install.sh
```

The installer gathers `flameshot`, `zenity`, and `libnotify` using `apt`, `dnf`, `pacman`, or `zypper`. It may ask for `sudo`. Set `PROOFSHOT_SKIP_DEPS=1` to skip dependency installation. Running `install.sh` again from the checkout pulls fast-forward updates and reinstalls the command. Set `PROOFSHOT_BIN_DIR=/usr/local/bin` for a system-wide install (with appropriate permissions).

## Quick start

```bash
proofshot --init ModuleName
proofshot -N
proofshot -P -N
proofshot -C Finding -N
proofshot -Q 5-7 -C Evidence
proofshot -L
```

`-D PATH` sets and persists the destination, `-W` displays it, and `-I NUMBER` sets the selected category's current index. `-N STEP` advances a category counter; add `-S` to capture the complete range from the previous index.

`Form` and `Proof` remain available for compatibility. `proofshot -N` uses category column `0` by default (the first category column after `Question`, which is `Form`). Use `-C NAME` to create or select categories such as `Evidence` or `Finding`; each gets its own counter. Use `-C 0`, `-C 1`, and so on to select zero-based category columns shown by `-L`. Use `--name PREFIX` to customize the filename prefix:

```bash
proofshot --name LoginPage -C Evidence -N
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

Counters are stored in `~/.config/proofshot/counts.json`; the selected directory is stored in `~/.config/proofshot/last_dir`.

## Requirements

- Python 3.10+
- Flameshot 0.10 or newer, with `flameshot gui --raw`
- Optional: `zenity` and `notify-send`

Run `proofshot --help` for the complete CLI reference.
