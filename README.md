# Proofshot

Proofshot is a Linux CLI screenshot organizer for students, penetration testers, and anyone who needs fast screenshot enumeration, tracking, categorization, and naming. It wraps [Flameshot](https://flameshot.org/) and supports numbered captures, ranges, persistent modules, custom categories, and table listings.

## Install

```bash
git clone https://github.com/REPLACE_ME/proofshot.git
cd proofshot
./install.sh
```

Running `install.sh` again from the checkout pulls fast-forward updates and reinstalls the command. Set `PROOFSHOT_BIN_DIR=/usr/local/bin` for a system-wide install (with appropriate permissions). Install `flameshot`; `zenity` is needed for overwrite prompts, and `libnotify` is optional for notifications.

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

Counters are stored in `~/.config/proofshot/counts.json`; the selected directory is stored in `~/.config/proofshot/last_dir`.

## Requirements

- Python 3.10+
- Flameshot 0.10 or newer, with `flameshot gui --raw`
- Optional: `zenity` and `notify-send`

Run `proofshot --help` for the complete CLI reference.
