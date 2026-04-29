from pathlib import Path
from typing import Optional


class AssetLoader:
    """Simple additive asset loader placeholder for E-7.

    This loader is intentionally minimal: it resolves asset paths under a
    package-level `assets/` folder and exposes helpers for tests and later
    GUI code to call. It performs no I/O beyond path resolution.
    """

    def __init__(self, assets_root: Optional[Path] = None):
        if assets_root is None:
            # default to repository-level assets directory near the GUI package
            self.assets_root = Path(__file__).parent.parent.parent / "assets"
        else:
            self.assets_root = Path(assets_root)

    def logo_path(self) -> Path:
        return self.assets_root / "logo.png"

    def icon_path(self, name: str) -> Path:
        return self.assets_root / name

    def exists(self, name: str) -> bool:
        return (self.assets_root / name).exists()

    def load_logo(self) -> str:
        """Return the filesystem path for the logo; actual pixmap loading
        is done elsewhere in GUI code (E-7 will wire that in)."""
        return str(self.logo_path())
