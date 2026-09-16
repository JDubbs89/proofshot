#!/usr/bin/env python3
"""
proofshot — capture a screenshot and save it with Qx/QxProof naming.

Two-step workflow:
    proofshot -D path/to/folder/          # sets the working directory (persisted)
    proofshot -Q 5-8 --proof              # captures into that directory
    proofshot -Q 6 -f                     # another capture, same directory
    proofshot -N                          # auto-increment from last question (1 step)
    proofshot -N 2                        # auto-increment from last question (2 steps)
    proofshot -N 2 -S                     # span from last+1 to last+2 (e.g., Q3-4)
    proofshot -P                          # shortcut for --proof
    proofshot -P -N -S                    # auto-increment proof counter with span
    proofshot -I 4                        # set index to 4 (next -N gives Q5) [FORM DEFAULT]
    proofshot -P -I 4                     # set proof index to 4
    proofshot -L                          # list all question indices in table
    proofshot --init ModuleName           # create new folder, reset indices, persist

-D can also be combined with -Q/-N in one call:
    proofshot -D ~/Documents/HTB/Module -Q 5 -f
    proofshot -D ~/Documents/HTB/Module -N -P

Requires: flameshot (>=0.10, needs `gui --raw`), zenity (only needed when
-p/-f/-s are omitted or on filename collision), notify-send (optional).

Quick Reference:
    -Q NUM       Specify question number directly (e.g., -Q 5 or -Q 5-7)
    -N [STEP]    Auto-increment from last question (default: 1)
    -S           Include all questions in the span when used with -N
    -I NUMBER    Manually set the current index [DEFAULTS TO FORM]
    --init NAME  Create new folder, reset indices to 0, persist directory
    -D PATH      Set/persist the working directory
    -P           Trigger Proof mode (appends "Proof" to filename/index)
    -f           Explicitly specify Form mode (no "Proof" suffix)
    -L           List all indexed questions with filenames (always uses persisted dir)
    -W           Show current directory
    --force      Skip overwrite confirmation
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

__version__ = "0.1.7"

STATE_DIR = Path.home() / ".config" / "proofshot"
STATE_FILE = STATE_DIR / "last_dir"
COUNTS_FILE = STATE_DIR / "counts.json"
PROJECT_CONFIG_NAME = ".proofshot.json"
DEFAULT_CONFIG_FILE = Path(__file__).resolve().parent / "default_config.json"
DEFAULT_CONFIG = {
    "form_category": "Form",
    "proof_category": "Proof",
    "filename_prefix": "{directory}Q",
    "filename_suffix": "{category}",
}

def ensure_state_dir():
    """Create state directory if it doesn't exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def create_project_config(project_dir: Path):
    """Create a project config from the repository default without overwriting one."""
    config_file = project_dir / PROJECT_CONFIG_NAME
    if config_file.exists():
        return
    if DEFAULT_CONFIG_FILE.exists():
        config_file.write_text(DEFAULT_CONFIG_FILE.read_text())
    else:
        config_file.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")

def load_config(project_dir: Path | None = None) -> dict:
    """Load project-local naming and category settings."""
    config = DEFAULT_CONFIG.copy()
    config_file = project_dir / PROJECT_CONFIG_NAME if project_dir else None
    if config_file and config_file.exists():
        try:
            data = json.loads(config_file.read_text())
            if isinstance(data, dict):
                for key in config:
                    if isinstance(data.get(key), str) and data[key]:
                        config[key] = data[key]
        except json.JSONDecodeError:
            print(f"Warning: ignoring invalid config file: {config_file}", file=sys.stderr)
    return config

def load_counts() -> dict:
    """Load last question numbers for every category."""
    ensure_state_dir()
    if not COUNTS_FILE.exists():
        return {"Form": 0, "Proof": 0}
    try:
        data = json.loads(COUNTS_FILE.read_text())
        if not isinstance(data, dict):
            return {"Form": 0, "Proof": 0}
        counts = {str(key): int(value) for key, value in data.items()
                  if isinstance(key, str) and isinstance(value, int) and value >= 0}
        counts.setdefault("Form", 0)
        counts.setdefault("Proof", 0)
        return counts
    except (json.JSONDecodeError, KeyError):
        return {"Form": 0, "Proof": 0}

def save_counts(counts: dict):
    """Save last question numbers for each type."""
    ensure_state_dir()
    COUNTS_FILE.write_text(json.dumps(counts, indent=2))

def update_count_for_type(shot_type: str, counts: dict, steps: int) -> int:
    """Increment and return the new question number for this type."""
    counts.setdefault(shot_type, 0)
    counts[shot_type] += steps
    save_counts(counts)
    return counts[shot_type]

def set_index_for_type(shot_type: str, index: int):
    """Set the index for a specific type (Form or Proof)."""
    counts = load_counts()
    counts[shot_type] = index
    save_counts(counts)

def reset_indices():
    """Reset the default indices to 0."""
    save_counts({"Form": 0, "Proof": 0})

def resolve_category(value: str | None, counts: dict, config: dict) -> str:
    """Resolve a category name or zero-based category column number."""
    if not value:
        return config["proof_category"] if counts.get("__proof_flag__") else config["form_category"]
    if value.isdigit():
        index = int(value)
        categories = [key for key in counts if not key.startswith("__")]
        if index < 0 or index >= len(categories):
            raise ValueError(f"category column {index} is out of range (0-{len(categories) - 1})")
        return categories[index]
    category = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    if not category:
        raise ValueError("category must contain at least one letter or number")
    return category

def zenity_choice_form_or_proof() -> str:
    """Present zenity dialog to choose Form or Proof type."""
    try:
        result = subprocess.run(
            [
                "zenity", "--list", "--title=proofshot", "--text=Screenshot type:",
                "--radiolist", "--column=Pick", "--column=Type",
                "TRUE", "Form", "FALSE", "Proof",
                "--width=300", "--height=200",
            ],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        sys.exit("zenity not found (install it, or pass -p/-f/-s to skip the prompt)")
    if result.returncode != 0:
        sys.exit("Cancelled.")
    return result.stdout.strip()

def zenity_confirm_overwrite(name: str, target_dir: Path) -> bool:
    """Confirm file overwrite via zenity dialog."""
    try:
        result = subprocess.run(
            [
                "zenity", "--question", "--title=File exists",
                f"--text={name}.png already exists in {target_dir}. Overwrite?",
            ]
        )
    except FileNotFoundError:
        sys.exit(f"{name}.png already exists and zenity isn't available to confirm "
                  f"overwrite. Pass --force or remove the file.")
    return result.returncode == 0

def zenity_confirm_init(dir_path: Path) -> bool:
    """Confirm directory initialization via zenity dialog if exists."""
    if dir_path.exists():
        try:
            result = subprocess.run(
                [
                    "zenity", "--question", "--title=Directory exists",
                    f"--text={dir_path} already exists. Reinitialize?",
                ]
            )
        except FileNotFoundError:
            sys.exit(f"{dir_path} already exists and zenity isn't available. "
                    f"Remove directory manually or use different name.")
        if result.returncode != 0:
            sys.exit("Aborted.")
    return True

def save_state(target_dir: Path):
    """Persist the target directory for future sessions."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(target_dir))

def load_state() -> Path:
    """Load the persisted target directory."""
    if not STATE_FILE.exists():
        sys.exit(
            "No directory set yet. Run `proofshot -D <path>` first, "
            "or pass -D directly with -Q/-N."
        )
    saved = Path(STATE_FILE.read_text().strip())
    if not saved.is_dir():
        sys.exit(f"Saved directory no longer exists: {saved}\n"
                  f"Run `proofshot -D <path>` to set a new one.")
    return saved

def display_path(path: Path) -> str:
    """Collapse the home dir to ~ for display, matching the box's convention."""
    home = Path.home()
    try:
        return f"~/{path.relative_to(home)}"
    except ValueError:
        return str(path)

def print_box(title: str, lines: list[str]):
    """Print a nicely formatted text box."""
    content = [title] + lines
    width = max(len(l) for l in content) + 4
    border = "+" + "-" * (width - 2) + "+"
    print(border)
    for line in content:
        print("|  " + line.ljust(width - 4) + " |")
    print(border)

def parse_question_arg(q_str: str) -> tuple[int, int]:
    """Parse question argument like '5', '5-7', '8' into (start, end)."""
    if '-' in q_str:
        parts = q_str.split('-')
        return int(parts[0]), int(parts[1])
    return int(q_str), int(q_str)

def build_question_string(start: int, end: int) -> str:
    """Build question string like '5' or '5-7'."""
    if start == end:
        return str(start)
    return f"{start}-{end}"

def extract_question_files(target_dir: Path, config: dict | None = None) -> dict:
    """Scan directory for proofshot files and return mapping of question numbers to filenames.
    
    Returns: {question_number: {category: [filenames]}}
    """
    mapping = {}
    config = config or load_config(target_dir)
    
    # Pattern: ModuleQ1.png, ModuleQ1-5.png, ModuleQ1Proof.png, ModuleQ1-5Proof.png
    pattern = re.compile(r'^.*?Q(\d+)(?:-(\d+))?(.*)\.png$', re.IGNORECASE)
    
    for file in target_dir.glob('*.png'):
        match = pattern.match(file.name)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else start
            
            suffix = match.group(3)
            category = suffix if suffix else config["form_category"]
            
            # Map each question number in the range
            for q_num in range(start, end + 1):
                if q_num not in mapping:
                    mapping[q_num] = {}
                
                filename_display = file.name
                mapping[q_num].setdefault(category, []).append(filename_display)
    
    return mapping

def print_index_table(target_dir: Path):
    """Print a table of all question indices with their associated files."""
    mapping = extract_question_files(target_dir, load_config(target_dir))
    
    if not mapping:
        print_box("INDEX LISTING", [
            f"No screenshots found in: {display_path(target_dir)}",
            "Make sure you've captured files in this directory first."
        ])
        return
    
    # Get all sorted question numbers
    questions = sorted(mapping.keys())
    
    # Calculate column widths
    q_width = max(len(str(max(questions))), 4)
    categories = sorted({category for row in mapping.values() for category in row})
    widths = {category: max(5, max(len(', '.join(mapping[q].get(category, [])))
                             if mapping[q].get(category) else 5 for q in questions))
              for category in categories}
    
    # Print header
    print()
    border_top = "+" + "-" * (q_width + 2) + "+" + "+".join("-" * (widths[c] + 2) for c in categories) + "+"
    separator = "+" + "-" * (q_width + 2) + "+" + "+".join("-" * (widths[c] + 2) for c in categories) + "+"
    
    print(border_top)
    print("| " + f"{'Question':^{q_width}} | " + " | ".join(f"{c:^{widths[c]}}" for c in categories) + " |")
    print(separator)
    
    # Print each row
    for q_num in questions:
        cells = []
        for category in categories:
            files = ', '.join(sorted(mapping[q_num].get(category, []))) or '(none)'
            cells.append(f"{files:^{widths[category]}}")
        print("| " + f"{q_num:^{q_width}} | " + " | ".join(cells) + " |")
    
    print(border_top)
    
    # Print current indices
    counts = load_counts()
    print("\nCurrent Index: " + ", ".join(f"{k}={v}" for k, v in counts.items()))

def check_dependencies():
    """Verify required dependencies are installed."""
    missing = []
    if subprocess.run(["which", "flameshot"], capture_output=True).returncode != 0:
        missing.append("flameshot")
    
    if not missing:
        return True
    
    sys.exit(f"Missing dependencies: {', '.join(missing)}. Install them to use proofshot.")

def capture_screenshot(target: Path):
    """Capture a screenshot using flameshot and save to target path."""
    with open(target, "wb") as f:
        # Suppress QPainter warnings by redirecting stderr
        result = subprocess.run(
            ["flameshot", "gui", "--raw"],
            stdout=f,
            stderr=subprocess.DEVNULL
        )
    
    return result.returncode == 0 and target.stat().st_size >= 100

def send_notification(target: Path):
    """Send desktop notification if notify-send is available."""
    if subprocess.run(["which", "notify-send"], capture_output=True).returncode == 0:
        subprocess.run(["notify-send", "Screenshot Saved", str(target)],
                       stderr=subprocess.DEVNULL)

def uninstall_command():
    """Remove the installed executable without deleting saved settings."""
    executable = Path(sys.argv[0]).resolve()
    source_file = Path(__file__).resolve()
    if executable == source_file or executable.suffix == ".py":
        sys.exit("Refusing to remove the source file. Run the installed `proofshot --uninstall` command.")
    if executable.exists():
        executable.unlink()
        print(f"Removed {executable}")
    else:
        print("proofshot is not installed at the requested path.")
    print(f"Saved configuration was kept in {STATE_DIR}")

def update_command():
    """Install the latest published GitHub release."""
    installer_url = "https://raw.githubusercontent.com/JDubbs89/proofshot/main/release-install.sh"
    try:
        with urllib.request.urlopen(installer_url, timeout=30) as response:
            installer = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(f"Unable to download the update installer: {exc}")

    with tempfile.NamedTemporaryFile(mode="wb", suffix="-proofshot-update.sh") as script:
        script.write(installer)
        script.flush()
        result = subprocess.run(["bash", script.name])
    if result.returncode != 0:
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(
        prog="proofshot",
        description="Capture screenshots with automatic question numbering and proof tracking.",
        epilog="""Examples:
  proofshot -D ~/HTB/module         Set working directory
  proofshot -Q 5                    Capture question 5 (FORM default)
  proofshot -Q 5-7 --proof          Capture questions 5-7 as proof
  proofshot -P                      Shortcut for --proof
  proofshot -N                      Auto-increment by 1 (FORM: e.g., last=5 → Q6)
  proofshot -N 2                    Auto-increment by 2 (FORM: e.g., last=5 → Q7)
  proofshot -N 2 -S                 Span increment (FORM: e.g., last=5 → Q6-7)
  proofshot -P -N                   Auto-increment PROOF (requires -P)
  proofshot -I 4                    Set FORM index to 4 [DEFAULT TYPE]
  proofshot -P -I 4                 Set PROOF index to 4
  proofshot --init ModuleName       Create folder, reset indices, persist
  proofshot -L                      List all indexed questions
  proofshot -W                      Show current directory""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove the installed proofshot command (keeps saved settings)")
    parser.add_argument("--update", action="store_true",
                        help="Download and install the latest GitHub release")

    group_questions = parser.add_argument_group('Question Parameters')
    group_questions.add_argument("-Q", "--question", metavar="NUM",
                                 help="Specify question number directly (e.g., '5' or '5-7')")
    group_questions.add_argument("-N", "--next", nargs="?", const=1, type=int, metavar="STEP",
                                 help="Auto-increment from last question (default: 1 step) [FORM unless -P]")
    group_questions.add_argument("-S", "--span", action="store_true",
                                 help="Include all questions in span when used with -N (e.g., -N 2 -S → Q3-4)")
    group_questions.add_argument("-I", "--index", type=int, metavar="NUMBER",
                                 help="Manually set the current index for the selected category")
    group_questions.add_argument("-C", "--category", metavar="NAME_OR_COLUMN",
                                 help="Category name (or zero-based listing column; column 0 is the default)")
    group_questions.add_argument("--name", metavar="PREFIX",
                                 help="Custom filename prefix instead of the destination folder name")
    group_questions.add_argument("--init", metavar="NAME",
                                 help="Create new folder with this name, reset indices to 0, and persist")

    group_directory = parser.add_argument_group('Directory Parameters')
    group_directory.add_argument("-D", "--dir", metavar="PATH",
                                 help="Set the working directory (persists across sessions)")
    group_directory.add_argument("-W", "--where", action="store_true",
                                 help="Show the current persisted directory")
    group_directory.add_argument("-L", "--list", action="store_true",
                                 help="List all indexed questions with filenames in table format")

    group_type = parser.add_mutually_exclusive_group()
    group_type.add_argument("-p", "--proof", action="store_true",
                            help="Enable Proof mode (adds 'Proof' suffix to filename)")
    group_type.add_argument("-P", action="store_true", dest="proof_shortcut",
                            help="Short form of --proof (-P instead of --proof)")
    group_type.add_argument("-f", "--form", action="store_true",
                            help="Explicit Form mode (default behavior)")

    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing file without confirmation")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress the final confirmation box")

    args = parser.parse_args()

    if args.uninstall:
        uninstall_command()
    if args.update:
        update_command()

    # Resolve -P shortcut into --proof flag
    if args.proof_shortcut:
        args.proof = True

    # Handle --init flag first (highest priority)
    if args.init:
        module_name = args.init
        target_dir = Path.cwd() / module_name
        
        # Validate directory name
        if '/' in module_name or '\\' in module_name:
            sys.exit(f"Invalid directory name: {module_name}. Use a simple name without paths.")
        
        # Check if directory exists
        zenity_confirm_init(target_dir)
        
        # Create directory
        try:
            target_dir.mkdir(parents=False, exist_ok=True)
        except FileExistsError:
            sys.exit(f"Directory {target_dir} already exists. Remove it manually or choose different name.")
        except PermissionError:
            sys.exit(f"Permission denied creating {target_dir}")

        create_project_config(target_dir)
        
        # Reset indices to 0
        reset_indices()
        
        # Persist the new directory
        save_state(target_dir)
        
        print_box("PROOFSHOT: Module Initialized", [
            f"Folder: {display_path(target_dir)}",
            f"Config: {PROJECT_CONFIG_NAME}",
            "Form Index: 0",
            "Proof Index: 0",
            "Next -N will create: Q1.png",
            "Next -P -N will create: Q1Proof.png"
        ])
        return

    if args.dir is None and args.question is None and args.next is None and \
       args.index is None and not args.where and not args.list:
        parser.error("pass -D to set a directory, -Q/-N/-I/--init for question/index/init, -W to check, -L to list, or -h for help")

    # Load or set target directory
    if args.dir is not None:
        target_dir = Path(args.dir).expanduser().resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        save_state(target_dir)
    else:
        target_dir = None  # loaded lazily below if needed

    # Handle -W (where) flag
    if args.where:
        shown_dir = target_dir if target_dir is not None else load_state()
        print_box("PROOFSHOT: Current Directory",
                  [f"Destination: {display_path(shown_dir)}"])
        return

    # Handle -L (list) flag - ALWAYS uses persisted directory
    if args.list:
        shown_dir = target_dir if target_dir is not None else load_state()
        print_index_table(shown_dir)
        return

    if target_dir is None:
        target_dir = load_state()
    config = load_config(target_dir)

    # Resolve category for index/capture operations. -P remains a Proof alias.
    counts = load_counts()
    counts["__proof_flag__"] = args.proof
    try:
        shot_type = resolve_category(args.category, counts, config)
    except ValueError as exc:
        parser.error(str(exc))
    counts.pop("__proof_flag__", None)
    counts.setdefault(shot_type, 0)

    # Handle -I (index) flag
    if args.index is not None:
        set_index_for_type(shot_type, args.index)
        print_box("PROOFSHOT: Index Set",
                  [f"Index for {shot_type}: Q{args.index}",
                   f"Next -N will produce: Q{args.index + 1}"])
        return

    if args.question is None and args.next is None:
        # Only showing directory info
        if target_dir is None:
            target_dir = load_state()
        print_box("PROOFSHOT: Directory Set",
                  [f"Destination: {display_path(target_dir)}"])
        return

    # Check dependencies early
    check_dependencies()

    # Default to Form, only use Proof with explicit -P/-p
    # Category was resolved above; explicit -f keeps the traditional Form name.

    # Handle question number resolution
    question_start = None
    question_end = None

    if args.question:
        question_start, question_end = parse_question_arg(args.question)
    elif args.next is not None:
        # Auto-increment mode
        counts = load_counts()
        last_q = counts[shot_type]
        step = args.next  # default 1 if passed as -N, or custom if -N 2

        if args.span:
            # Span mode: include all questions from last+1 to last+step
            question_start = last_q + 1
            question_end = last_q + step
        else:
            # Single question mode: jump to last+step
            question_start = last_q + step
            question_end = question_start

    if question_start is None:
        sys.exit("Could not determine question number. Pass -Q or -N.")

    # Build the question string for the filename
    question_str = build_question_string(question_start, question_end)

    # Update the count AFTER determining what we're capturing
    if args.span and args.next:
        steps = question_end - question_start + 1
    else:
        steps = args.next if args.next else 1
    update_count_for_type(shot_type, load_counts(), steps)

    # Filename construction
    prefix = args.name or config["filename_prefix"]
    prefix = prefix.replace("{directory}", target_dir.name).replace("{category}", shot_type)
    suffix = config["filename_suffix"]
    if shot_type == config["form_category"] and suffix == DEFAULT_CONFIG["filename_suffix"]:
        suffix = ""
    suffix = suffix.replace("{directory}", target_dir.name).replace("{category}", shot_type)
    base_name = f"{prefix}{question_str}{suffix}"
    target = target_dir / f"{base_name}.png"

    if target.exists() and not args.force:
        if not zenity_confirm_overwrite(base_name, target_dir):
            sys.exit("Aborted.")

    # Capture screenshot
    print(f"\nLaunching Flameshot. Select the region to capture...\n")
    success = capture_screenshot(target)

    if not success:
        target.unlink(missing_ok=True)
        sys.exit("Capture cancelled or empty — nothing saved.")

    send_notification(target)

    if not args.quiet:
        print_box("PROOFSHOT: New Screenshot Catalogued", [
            f"Question: Q{question_str}",
            f"Type: {shot_type}",
            f"Filename: {base_name}.png",
            f"Destination: {display_path(target_dir)}"
        ])

if __name__ == "__main__":
    main()
