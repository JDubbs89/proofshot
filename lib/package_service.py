"""Packaging service for exporting mapped project screenshots."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

def package_images(project_dir: Path, files: list[str], output: Path, force: bool = False) -> Path:
    """Create a ZIP containing the selected project screenshots."""
    if output.exists() and not force:
        raise ValueError(f"package already exists: {output} (use --force to replace it)")
    unique_files = list(dict.fromkeys(files))
    if not unique_files:
        raise ValueError("no screenshots matched the selected columns and indices")
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for filename in unique_files:
            source = project_dir / filename
            if source.is_file() and source.suffix.lower() == ".png":
                archive.write(source, arcname=source.name)
    return output
