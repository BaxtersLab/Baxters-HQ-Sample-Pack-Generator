from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PathsConfig:
    input_files: List[str] = field(default_factory=list)
    output_folder: Optional[str] = None
    last_used_input: Optional[str] = None
    last_used_output: Optional[str] = None


@dataclass
class SettingsConfig:
    backsplash_enabled: bool = True
    hoverlogic_enabled: bool = True
    theme: str = 'dark'
    debug_enabled: bool = False


@dataclass
class ChopConfig:
    silence_threshold: float = 0.01
    transient_sensitivity: float = 1.5
    pre_ms: int = 20
    post_ms: int = 80
    min_slice_ms: int = 50
    max_slice_ms: int = 10000


@dataclass
class FlowchartConfig:
    cb1: bool = True
    cb2: bool = True
    cb3: bool = True
    cb4: bool = True
    cb5: bool = True
    cb6: bool = True
    cb7: bool = True
    cb8: bool = True


@dataclass
class HRTConfig:
    auto_connect: bool = False
    manual_override: bool = False
    connected: bool = False
    host: str = '127.0.0.1'
    port: int = 8090
    autolink_enabled: bool = True


@dataclass
class AppConfig:
    paths: PathsConfig = field(default_factory=PathsConfig)
    settings: SettingsConfig = field(default_factory=SettingsConfig)
    flowchart: FlowchartConfig = field(default_factory=FlowchartConfig)
    chop: ChopConfig = field(default_factory=ChopConfig)
    hrt: HRTConfig = field(default_factory=HRTConfig)
    terms_accepted: bool = False

    # Persistence helpers (add-only, minimal)
    def save(self, path: str = 'hqspg_config.json'):
        try:
            import json
            from dataclasses import asdict
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2)
            return True
        except Exception:
            return False

    def load(self, path: str = 'hqspg_config.json'):
        try:
            import json
            from dataclasses import is_dataclass
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Simple merge: set attributes if present
            if not isinstance(data, dict):
                return False

            # paths
            p = data.get('paths', {})
            try:
                if p and hasattr(self, 'paths'):
                    for k, v in p.items():
                        if hasattr(self.paths, k):
                            setattr(self.paths, k, v)
            except Exception:
                pass

            # settings
            s = data.get('settings', {})
            try:
                if s and hasattr(self, 'settings'):
                    for k, v in s.items():
                        if hasattr(self.settings, k):
                            setattr(self.settings, k, v)
            except Exception:
                pass

            # flowchart
            fcfg = data.get('flowchart', {})
            try:
                if fcfg and hasattr(self, 'flowchart'):
                    for k, v in fcfg.items():
                        if hasattr(self.flowchart, k):
                            setattr(self.flowchart, k, v)
            except Exception:
                pass

            # hrt
            h = data.get('hrt', {})
            try:
                if h and hasattr(self, 'hrt'):
                    for k, v in h.items():
                        if hasattr(self.hrt, k):
                            setattr(self.hrt, k, v)
            except Exception:
                pass

            # terms flag
            try:
                if 'terms_accepted' in data:
                    self.terms_accepted = bool(data.get('terms_accepted'))
            except Exception:
                pass

            return True
        except Exception:
            return False

