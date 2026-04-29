from typing import Dict, Any, Optional
import os
from .loader import load_input
from .separator import separate
from .repair import repair_stems
from .extract import extract


def full_pipeline(input_path: str, config: Optional[Dict] = None, output_base: Optional[str] = None) -> Dict[str, Any]:
    """Run full pipeline for a single input file and return structured results."""
    cfg = config or {}
    out_base = output_base or cfg.get('output', {}).get('base_dir') or os.getcwd()
    results: Dict[str, Any] = {'input': input_path, 'separated': {}, 'repaired': {}, 'slices': []}

    # run separator
    stems = separate(input_path, out_dir=out_base, model=cfg.get('separator', {}).get('model'), config=cfg.get('separator', {}))
    results['separated'] = stems

    # repair
    repaired = repair_stems(stems, output_base=out_base, track_name=os.path.splitext(os.path.basename(input_path))[0], config=cfg.get('repair', {}))
    results['repaired'] = repaired

    # gather repaired paths
    repaired_paths = {s: v.get('repaired_path') for s, v in repaired.items() if isinstance(v, dict) and v.get('repaired_path')}
    if repaired_paths:
        slices = extract(repaired_paths, output_base=out_base, track_name=os.path.splitext(os.path.basename(input_path))[0], config=cfg.get('extractor', {}))
        results['slices'] = slices

    return results
