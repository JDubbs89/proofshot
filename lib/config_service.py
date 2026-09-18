"""Project configuration, counters, and persisted-directory services."""

import json
import hashlib
import re
import sys
from pathlib import Path

PROJECT_CONFIG_NAME = ".proofshot.json"
MANIFEST_NAME = ".manifest.json"
STATE_DIR = Path.home() / ".config" / "proofshot"
STATE_FILE = STATE_DIR / "last_dir"
COUNTS_FILE = STATE_DIR / "counts.json"
PROVIDER_FILE = STATE_DIR / "provider"
DEFAULT_CONFIG_FILE = Path(__file__).resolve().parent.parent / "default_config.json"
DEFAULT_CONFIG = {"form_category": "Form", "proof_category": "Proof", "index_label": "Q", "filename_prefix": "{directory}{index_label}", "filename_suffix": "{category}", "categories": {"Form": {"suffix": ""}, "Proof": {"suffix": "{category}"}}}
CURRENT_PROJECT_VERSION = "0.2.6"
DEFAULT_CONFIG["proofshot_version"] = CURRENT_PROJECT_VERSION

def expand_template(template: str, config: dict, **values) -> str:
    """Expand built-in and user-defined naming variables."""
    variables = dict(config.get("variables", {}))
    variables.update(values)
    return re.sub(r"\{([A-Za-z0-9_-]+)\}", lambda match: str(variables.get(match.group(1), match.group(0))), template)

def ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def create_project_config(project_dir: Path):
    config_file = project_dir / PROJECT_CONFIG_NAME
    if not config_file.exists():
        source = DEFAULT_CONFIG_FILE.read_text() if DEFAULT_CONFIG_FILE.exists() else json.dumps(DEFAULT_CONFIG, indent=2)
        config_file.write_text(source if source.endswith("\n") else source + "\n")

def load_config(project_dir: Path | None = None) -> dict:
    config = DEFAULT_CONFIG.copy(); config_file = project_dir / PROJECT_CONFIG_NAME if project_dir else None
    if config_file and config_file.exists():
        try:
            data = json.loads(config_file.read_text())
            if isinstance(data, dict):
                for key in config:
                    if key == "categories" and isinstance(data.get(key), dict): config[key] = data[key]
                    elif isinstance(data.get(key), str) and data[key]: config[key] = data[key]
        except json.JSONDecodeError:
            print(f"Warning: ignoring invalid config file: {config_file}", file=sys.stderr)
    return config

def project_version(config: dict) -> str:
    """Return a project's declared version, defaulting legacy files safely."""
    return config.get("proofshot_version", "0.2.5")

def save_config(project_dir: Path, config: dict):
    (project_dir / PROJECT_CONFIG_NAME).write_text(json.dumps(config, indent=2) + "\n")

def normalise_category(value: str) -> str:
    category = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    if not category: raise ValueError("column name must contain at least one letter or number")
    return category

def naming_for_category(config: dict, category: str) -> tuple[str, str]:
    category_config = config.get("categories", {}).get(category, {})
    return category_config.get("prefix", config["filename_prefix"]), category_config.get("suffix", config["filename_suffix"])

def load_counts() -> dict:
    ensure_state_dir()
    if not COUNTS_FILE.exists(): return {"Form": 0, "Proof": 0}
    try:
        data = json.loads(COUNTS_FILE.read_text())
        if not isinstance(data, dict): return {"Form": 0, "Proof": 0}
        counts = {str(k): int(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, int) and v >= 0}
        counts.setdefault("Form", 0); counts.setdefault("Proof", 0); return counts
    except (json.JSONDecodeError, KeyError): return {"Form": 0, "Proof": 0}

def save_counts(counts: dict):
    ensure_state_dir(); COUNTS_FILE.write_text(json.dumps(counts, indent=2))

def update_count_for_type(shot_type: str, counts: dict, steps: int) -> int:
    counts.setdefault(shot_type, 0); counts[shot_type] += steps; save_counts(counts); return counts[shot_type]

def set_index_for_type(shot_type: str, index: int):
    counts = load_counts(); counts[shot_type] = index; save_counts(counts)

def reset_indices(config: dict | None = None):
    config = config or DEFAULT_CONFIG; categories = config.get("categories", {})
    save_counts({str(name): 0 for name in categories} or {config["form_category"]: 0, config["proof_category"]: 0})

def resolve_category(value: str | None, counts: dict, config: dict) -> str:
    if not value: return config["proof_category"] if counts.get("__proof_flag__") else config["form_category"]
    if value.isdigit():
        categories = list(config.get("categories", {})) or [config["form_category"], config["proof_category"]]
        index = int(value)
        if index >= len(categories): raise ValueError(f"category column {index} is out of range (0-{len(categories) - 1})")
        return categories[index]
    return normalise_category(value)

def save_state(target_dir: Path):
    STATE_DIR.mkdir(parents=True, exist_ok=True); STATE_FILE.write_text(str(target_dir))

def load_state() -> Path:
    if not STATE_FILE.exists(): sys.exit("No directory set yet. Run `proofshot -D <path>` first, or pass -D directly with -Q/-N.")
    saved = Path(STATE_FILE.read_text().strip())
    if not saved.is_dir(): sys.exit(f"Saved directory no longer exists: {saved}\nRun `proofshot -D <path>` to set a new one.")
    return saved

def load_provider() -> str:
    ensure_state_dir()
    if not PROVIDER_FILE.exists():
        return "flameshot"
    provider = PROVIDER_FILE.read_text().strip().lower()
    return provider or "flameshot"

def save_provider(provider: str):
    ensure_state_dir()
    PROVIDER_FILE.write_text(provider.lower() + "\n")

def image_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as image:
        for chunk in iter(lambda: image.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def load_manifest(project_dir: Path) -> dict:
    manifest_file = project_dir / MANIFEST_NAME
    if not manifest_file.exists():
        return {"version": 1, "images": {}}
    try:
        data = json.loads(manifest_file.read_text())
        if isinstance(data, dict) and isinstance(data.get("images"), dict):
            return data
    except json.JSONDecodeError:
        pass
    return {"version": 1, "images": {}}

def save_manifest(project_dir: Path, manifest: dict):
    (project_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")

def record_screenshot(project_dir: Path, screenshot: Path, index: int, category: str, index_end: int | None = None):
    manifest = load_manifest(project_dir)
    images = manifest.setdefault("images", {})
    filename = screenshot.name
    for records in images.values():
        if isinstance(records, list):
            records[:] = [record for record in records if record.get("filename") != filename]
    digest = image_hash(screenshot)
    images.setdefault(digest, []).append({
        "filename": filename, "index": index, "index_end": index_end or index, "category": category,
    })
    save_manifest(project_dir, manifest)

class ConfigEditor:
    """Mutates and displays project-local configuration."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config = load_config(project_dir)

    def save(self):
        save_config(self.project_dir, self.config)

    def show(self):
        print(json.dumps(self.config, indent=2, sort_keys=False))

    def show_columns(self):
        for index, name in enumerate(self.config.get("categories", {})):
            settings = self.config["categories"][name]
            prefix = settings.get("prefix", self.config["filename_prefix"])
            suffix = settings.get("suffix", self.config["filename_suffix"])
            print(f"{index}: {name} (prefix={prefix!r}, suffix={suffix!r})")

    def add_column(self, name: str):
        name = normalise_category(name)
        categories = self.config.setdefault("categories", {})
        if name in categories: raise ValueError(f"column already exists: {name}")
        categories[name] = {"suffix": "{category}"}
        counts = load_counts(); counts.setdefault(name, 0); save_counts(counts); self.save()

    def rename_column(self, old: str, new: str):
        old, new = normalise_category(old), normalise_category(new)
        categories = self.config.setdefault("categories", {})
        if old not in categories: raise ValueError(f"column does not exist: {old}")
        if new in categories and old != new: raise ValueError(f"column already exists: {new}")
        categories[new] = categories.pop(old)
        for key in ("form_category", "proof_category"):
            if self.config.get(key) == old: self.config[key] = new
        counts = load_counts()
        if old in counts: counts[new] = counts.pop(old); save_counts(counts)
        self.save()

    def remove_column(self, name: str):
        name = normalise_category(name); categories = self.config.setdefault("categories", {})
        if name not in categories: raise ValueError(f"column does not exist: {name}")
        if name in (self.config.get("form_category"), self.config.get("proof_category")):
            raise ValueError("cannot remove the Form or Proof column; rename it instead")
        categories.pop(name); counts = load_counts(); counts.pop(name, None); save_counts(counts); self.save()

    def set_template(self, template: str, value: str, column: str | None = None):
        if column:
            column = normalise_category(column)
            if column not in self.config.get("categories", {}): raise ValueError(f"column does not exist: {column}")
            self.config["categories"][column][template] = value
        else:
            self.config["filename_" + template] = value
        self.save()

    def set_variable(self, name: str, value: str):
        name = normalise_category(name)
        if name in ("directory", "category", "number"): raise ValueError(f"reserved variable name: {name}")
        self.config.setdefault("variables", {})[name] = value
        self.save()

    def set_index_label(self, label: str):
        label = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_")
        if not label: raise ValueError("index label must contain at least one letter or number")
        self.config["index_label"] = label
        if self.config.get("filename_prefix") in ("{directory}Q", "{directory}{index_label}"):
            self.config["filename_prefix"] = "{directory}{index_label}"
        self.save()

def config_operation(args, project_dir: Path) -> bool:
    editor = ConfigEditor(project_dir)
    if args.show_config: editor.show(); return True
    if args.show_columns: editor.show_columns(); return True
    if args.add_column: editor.add_column(args.add_column); print(f"Added column {normalise_category(args.add_column)}"); return True
    if args.rename_column: editor.rename_column(*args.rename_column); print(f"Renamed column {args.rename_column[0]} to {args.rename_column[1]}"); return True
    if args.remove_column: editor.remove_column(args.remove_column); print(f"Removed column {normalise_category(args.remove_column)}"); return True
    if args.set_prefix: editor.set_template("prefix", args.set_prefix); print("Updated filename prefix"); return True
    if args.set_suffix: editor.set_template("suffix", args.set_suffix); print("Updated filename suffix"); return True
    if args.set_column_prefix: editor.set_template("prefix", args.set_column_prefix[1], args.set_column_prefix[0]); return True
    if args.set_column_suffix: editor.set_template("suffix", args.set_column_suffix[1], args.set_column_suffix[0]); return True
    if args.set_variable: editor.set_variable(*args.set_variable); print(f"Set variable {args.set_variable[0]}"); return True
    if args.set_index_label: editor.set_index_label(args.set_index_label); print(f"Set index label to {args.set_index_label}"); return True
    return False
