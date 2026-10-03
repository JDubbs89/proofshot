"""Read-only project image records shared by CLI and GUI."""
from pathlib import Path
from .config_service import image_hash, load_manifest

def project_images(project_dir: Path) -> list[dict]:
    manifest = load_manifest(project_dir).get("images", {})
    records = []
    for path in sorted(project_dir.glob("*.png"), key=lambda item: item.name.lower()):
        entries = manifest.get(image_hash(path), []); entry = entries[0] if entries else {}
        records.append({"path": path, "filename": path.name, "category": entry.get("category", ""), "index": entry.get("index"), "index_end": entry.get("index_end", entry.get("index")), "manifested": bool(entries), "size": path.stat().st_size})
    return records
