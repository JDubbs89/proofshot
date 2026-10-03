"""User-level workspace discovery configuration."""
import json
from pathlib import Path

WORKSPACE_FILE = "workspace.json"
WORKSPACE_VERSION = 1

def workspace_path(state_dir: Path) -> Path:
    return state_dir / WORKSPACE_FILE

def load_workspace(state_dir: Path) -> dict:
    path = workspace_path(state_dir)
    if not path.exists(): return {"version": WORKSPACE_VERSION, "discovery_paths": []}
    try: value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError): value = {}
    paths = value.get("discovery_paths", []) if isinstance(value, dict) else []
    return {"version": WORKSPACE_VERSION, "discovery_paths": [str(p) for p in paths if isinstance(p, str)]}

def save_workspace(state_dir: Path, workspace: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    workspace_path(state_dir).write_text(json.dumps({"version": WORKSPACE_VERSION, "discovery_paths": workspace.get("discovery_paths", [])}, indent=2) + "\n")

def normalize_paths(paths: list[str]) -> list[str]:
    result, seen = [], set()
    for raw in paths:
        path = str(Path(raw).expanduser().resolve())
        if path not in seen: seen.add(path); result.append(path)
    return result

def discover_projects(workspace: dict) -> list[dict]:
    projects = {}
    for raw in normalize_paths(workspace.get("discovery_paths", [])):
        root = Path(raw)
        if not root.is_dir(): continue
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if child.is_dir(): projects[str(child)] = {"name": child.name, "path": str(child), "available": True}
    return list(sorted(projects.values(), key=lambda item: item["name"].lower()))
