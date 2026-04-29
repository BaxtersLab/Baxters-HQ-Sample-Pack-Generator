from typing import Callable, Dict, Optional


class HRTConnector:
    """Minimal HRT connector interface placeholder.

    This stub provides a small callback registry and no networking.
    Real networking will be added in later module blocks.
    """

    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self.connected = False

    def set_callback(self, name: str, cb: Callable) -> None:
        self._callbacks[name] = cb

    def connect(self) -> None:
        # best-effort: mark connected and call on_connect if present
        self.connected = True
        cb = self._callbacks.get('on_connect')
        if cb:
            try:
                cb()
            except Exception:
                pass

    def disconnect(self) -> None:
        self.connected = False
        cb = self._callbacks.get('on_disconnect')
        if cb:
            try:
                cb()
            except Exception:
                pass

    def is_connected(self) -> bool:
        return bool(self.connected)
