"""Command-line interface for HQSPG (scaffold)

This CLI is a lightweight scaffold to run the HQSPG pipeline. It does
not run heavy processing yet — the commands are placeholders that
invoke the pipeline stages implemented later.
"""
import os
import sys
import argparse
import json
import logging

try:
    import yaml
except Exception:
    yaml = None

from . import __version__
from .loader import HQLoader
from .separator import HQSeparator
from .repair import HQRepair
from .extractor import extract_samples

LOG = logging.getLogger('hqspg')
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


def load_config(path: str):
    if not path:
        return {}
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if yaml is not None and (path.endswith('.yaml') or path.endswith('.yml')):
        return yaml.safe_load(text)
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def _default_config_path():
    cand = os.path.join(os.path.dirname(__file__), '..', 'config', 'hqspg_default.yaml')
    # resolve relative to package root
    cand = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir, 'config', 'hqspg_default.yaml'))
    if os.path.isfile(cand):
        return cand
    # fallback to workspace-relative path
    alt = os.path.join(os.getcwd(), 'config', 'hqspg_default.yaml')
    return alt if os.path.isfile(alt) else None


def _ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def run_pipeline_for_file(src: str, cfg: dict, out_base: str):
    result = {'input': src, 'separated': {}, 'repaired': {}, 'slices': []}
    LOG.info('Processing %s', src)

    sep_cfg = cfg.get('separator', {}) if isinstance(cfg, dict) else {}
    rep_cfg = cfg.get('repair', {}) if isinstance(cfg, dict) else {}

    separator = HQSeparator(model=sep_cfg.get('model', 'htdemucs_6s'), config=sep_cfg, logger_obj=LOG)
    repairer = HQRepair(mode=rep_cfg.get('mode', 'balanced'), config=rep_cfg, logger_obj=LOG)

    try:
        out_dir = os.path.join(out_base, os.path.splitext(os.path.basename(src))[0])
        os.makedirs(out_dir, exist_ok=True)

        stems = separator.separate(src, out_dir=out_dir)
        result['separated'] = stems

        # Repair all stems (repairer.repair expects a dict of stems -> paths)
        try:
            repaired_map = repairer.repair(stems, output_base=out_dir, track_name=os.path.splitext(os.path.basename(src))[0])
            result['repaired'] = repaired_map
        except Exception as e:
            LOG.exception('Error during repair step: %s', e)
            result['repaired'] = {'error': str(e)}

        # Prepare mapping of repaired stem files for extractor
        repaired_paths = {s: v.get('repaired_path') for s, v in result['repaired'].items() if isinstance(v, dict) and v.get('repaired_path')}
        if repaired_paths:
            try:
                slices = extract_samples(repaired_paths, output_base=out_dir, track_name=os.path.splitext(os.path.basename(src))[0], config=cfg.get('extractor', {}))
                result['slices'] = slices
            except Exception as e:
                LOG.exception('Extractor failed: %s', e)
                result['slices'] = {'error': str(e)}

    except FileNotFoundError as e:
        LOG.error('File not found: %s', e)
        result['error'] = str(e)
    except Exception as e:
        LOG.exception('Unexpected error processing %s: %s', src, e)
        result['error'] = str(e)

    return result


def cmd_run(args):
    cfg_path = args.config or _default_config_path()
    cfg = {}
    if cfg_path:
        try:
            cfg = load_config(cfg_path) or {}
            LOG.info('Using config: %s', cfg_path)
        except Exception as e:
            LOG.error('Failed to load config %s: %s', cfg_path, e)
            return 2
    else:
        LOG.info('No config provided; using empty defaults')

    inputs = cfg.get('inputs', []) if isinstance(cfg, dict) else []
    loader_mode = cfg.get('loader', {}).get('mode') if isinstance(cfg, dict) else None
    if not inputs and not loader_mode:
        LOG.warning('No input files found in config (inputs) and no loader mode configured. Nothing to do.')
        print(json.dumps({'results': []}, indent=2))
        return 0

    loader = HQLoader(config=cfg.get('loader', {}), logger_obj=LOG)
    # normalize inputs via loader if config provides mode/file list; otherwise assume explicit list
    normalized = []
    # if config contains loader.mode, use loader
    loader_mode = cfg.get('loader', {}).get('mode')
    if loader_mode:
        normalized = loader.load(mode=loader_mode, file=cfg.get('loader', {}).get('file'), folder=cfg.get('loader', {}).get('folder'), files=cfg.get('loader', {}).get('files'))
    else:
        normalized = _ensure_list(inputs)

    if not normalized:
        LOG.warning('No files were resolved for processing after loader step.')
        print(json.dumps({'results': []}, indent=2))
        return 0

    out_base = cfg.get('output', {}).get('base_dir', 'HQSPG_output')
    os.makedirs(out_base, exist_ok=True)

    results = []
    for src in normalized:
        if not os.path.isfile(src):
            LOG.warning('Skipping missing input: %s', src)
            continue
        res = run_pipeline_for_file(src, cfg, out_base)
        results.append(res)

    print(json.dumps({'results': results}, indent=2))
    return 0


def cmd_full_pipeline(args):
    # for now behave same as run but expose config path and verbose flag
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
    return cmd_run(args)


def cmd_separate(args):
    cfg = {}
    cfg_path = args.config or _default_config_path()
    if cfg_path:
        try:
            cfg = load_config(cfg_path) or {}
        except Exception as e:
            LOG.error('Failed to load config: %s', e)
            return 2

    separator = HQSeparator(model=cfg.get('separator', {}).get('model', 'htdemucs_6s'), config=cfg.get('separator', {}), logger_obj=LOG)
    if not os.path.isfile(args.input):
        LOG.error('Input file missing: %s', args.input)
        return 2
    out_dir = args.out_dir or cfg.get('output', {}).get('base_dir', 'HQSPG_output')
    os.makedirs(out_dir, exist_ok=True)
    mapping = separator.separate(args.input, out_dir=out_dir)
    print(json.dumps(mapping, indent=2))
    return 0


def cmd_repair(args):
    cfg = {}
    cfg_path = args.config or _default_config_path()
    if cfg_path:
        try:
            cfg = load_config(cfg_path) or {}
        except Exception as e:
            LOG.error('Failed to load config: %s', e)
            return 2

    repairer = HQRepair(mode=cfg.get('repair', {}).get('mode', 'balanced'), config=cfg.get('repair', {}), logger_obj=LOG)
    if not os.path.isfile(args.input):
        LOG.error('Stem file missing: %s', args.input)
        return 2
    out_path = args.out_path
    result = repairer.repair(args.input, out_path=out_path)
    print(json.dumps(result, indent=2))
    return 0


def cmd_extract(args):
    cfg = {}
    cfg_path = args.config or _default_config_path()
    if cfg_path:
        try:
            cfg = load_config(cfg_path) or {}
        except Exception as e:
            LOG.error('Failed to load config: %s', e)
            return 2

    folder = args.folder
    if not os.path.isdir(folder):
        LOG.error('Repaired folder missing: %s', folder)
        return 2

    # collect wav files in folder (shallow)
    stems = {}
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith('.wav'):
            continue
        path = os.path.abspath(os.path.join(folder, fname))
        # derive stem name
        base = os.path.splitext(fname)[0]
        # strip suffixes like _repaired
        if base.endswith('_repaired'):
            stem = base[:-9]
        else:
            stem = base
        stems[stem] = path

    if not stems:
        LOG.warning('No WAV files found in repaired folder: %s', folder)
        print(json.dumps({'slices': []}, indent=2))
        return 0

    out_base = args.output_base or cfg.get('output', {}).get('base_dir', 'HQSPG_output')
    track_name = args.track_name or os.path.basename(os.path.normpath(folder))
    try:
        slices = extract_samples(stems, output_base=out_base, track_name=track_name, config=cfg.get('extractor', {}))
        print(json.dumps({'slices': slices, 'count': len(slices)}, indent=2))
        return 0
    except Exception as e:
        LOG.exception('Extractor failed: %s', e)
        print(json.dumps({'error': str(e)}))
        return 2


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(prog="hqspg", description="HQSPG — HQ Sample Pack Generator (scaffold)")
    parser.add_argument('--version', action='store_true', help='print version')
    parser.add_argument('--config', '-c', help='path to config (yaml or json)')

    sub = parser.add_subparsers(dest='command')

    p_run = sub.add_parser('run', help='Run the pipeline using config inputs')
    p_run.set_defaults(func=cmd_run)

    p_full = sub.add_parser('full-pipeline', help='Run full pipeline with extra options')
    p_full.add_argument('--verbose', action='store_true', help='enable verbose logging')
    p_full.set_defaults(func=cmd_full_pipeline)

    p_sep = sub.add_parser('separate', help='Run separator on a single file')
    p_sep.add_argument('input', help='input audio file')
    p_sep.add_argument('--out-dir', help='output directory for stems')
    p_sep.set_defaults(func=cmd_separate)

    p_rep = sub.add_parser('repair', help='Repair a single stem file')
    p_rep.add_argument('input', help='input stem file')
    p_rep.add_argument('--out-path', help='repaired output path')
    p_rep.set_defaults(func=cmd_repair)

    p_ext = sub.add_parser('extract', help='Run extractor on a repaired stems folder')
    p_ext.add_argument('folder', help='folder containing repaired stem WAVs')
    p_ext.add_argument('--output-base', help='base output directory for samples')
    p_ext.add_argument('--track-name', help='track name to use for samples folder')
    p_ext.set_defaults(func=cmd_extract)

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except Exception as e:
        LOG.exception('Unhandled CLI error: %s', e)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
