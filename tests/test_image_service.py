from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from lib.image_service import project_images


class ProjectImagesTests(TestCase):
    def test_orders_manifested_figures_by_index(self):
        """Gallery consumers receive figures in numeric, not filename, order."""
        with TemporaryDirectory() as directory:
            project_dir = Path(directory)
            for filename in ("Figure10.png", "Figure2.png", "Figure1.png", "legacy.png"):
                (project_dir / filename).write_bytes(b"image")

            manifest = {
                "images": {
                    "hash-figure10": [{"index": 10, "index_end": 10, "category": "Proof"}],
                    "hash-figure2": [{"index": 2, "index_end": 2, "category": "Proof"}],
                    "hash-figure1": [{"index": 1, "index_end": 1, "category": "Proof"}],
                }
            }
            hashes = {
                "Figure10.png": "hash-figure10",
                "Figure2.png": "hash-figure2",
                "Figure1.png": "hash-figure1",
                "legacy.png": "hash-legacy",
            }

            with patch("lib.image_service.load_manifest", return_value=manifest), patch(
                "lib.image_service.image_hash", side_effect=lambda path: hashes[path.name]
            ):
                images = project_images(project_dir)

            self.assertEqual([image["filename"] for image in images], [
                "Figure1.png",
                "Figure2.png",
                "Figure10.png",
                "legacy.png",
            ])
