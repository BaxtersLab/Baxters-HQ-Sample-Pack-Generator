from pathlib import Path


def sanitize_path(p: str) -> str:
    # minimal sanitizer: expand user and resolve where possible
    try:
        pth = Path(p).expanduser().resolve()
        return str(pth)
    except Exception:
        return p
