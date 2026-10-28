"""Read-only project image records shared by CLI and GUI."""
from pathlib import Path
from .config_service import image_hash, load_manifest

def project_images(project_dir: Path) -> list[dict]:
    manifest = load_manifest(project_dir).get("images", {})
    records = []
    for path in sorted(project_dir.glob("*.png"), key=lambda item: item.name.lower()):
        entries = manifest.get(image_hash(path), []); entry = entries[0] if entries else {}
        records.append({"path": path, "filename": path.name, "category": entry.get("category", ""), "index": entry.get("index"), "index_end": entry.get("index_end", entry.get("index")), "manifested": bool(entries), "size": path.stat().st_size})
    # Filenames are user-editable and lexical sorting puts, for example,
    # Figure10 before Figure2.  The manifest index is the project's source of
    # truth for figure order, so use it to control the gallery insertion order.
    # Unindexed (usually legacy) images remain available after indexed figures.
    return sorted(
        records,
        key=lambda record: (
            record["index"] is None,
            record["index"] if record["index"] is not None else float("inf"),
            record["index_end"] if record["index_end"] is not None else float("inf"),
            record["category"].casefold(),
            record["filename"].casefold(),
        ),
    )
