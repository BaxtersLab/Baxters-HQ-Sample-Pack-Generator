#!/usr/bin/env python3
"""Generate a conservative Continue profile for Qwen3.5 using Nemotron as template.

Writes:
- tools/generated_profiles/qwen3.5-conservative.yaml
- vens/onboarding-reports/qwen3.5-conservative.json

No changes are made to C:\\Users\\Baxter\\.continue\\config.yaml.
"""
from __future__ import annotations
import os
import re
import json
from datetime import datetime
from pathlib import Path

ROOTS = [
    Path(r"C:\Users\Baxter\Desktop\Vens Constitution"),
    Path(r"C:\Users\Baxter\Desktop\gguf chatbox"),
]

OUT_YAML = Path("tools/generated_profiles/qwen3.5-conservative.yaml")
OUT_JSON = Path("vens/onboarding-reports/qwen3.5-conservative.json")


def find_exec_params(roots):
    ctx = None
    gpu_layers = None
    threads = None
    pattern_ctx = re.compile(r"--ctx[- ]size\s+(\d+)")
    pattern_gpu = re.compile(r"--n-gpu-layers\s+(\d+)")
    pattern_threads = re.compile(r"--threads\s+(\d+)")

    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.lower().endswith((".rs", ".txt", ".log", ".md", ".py", ".toml", ".json")):
                    continue
                fpath = Path(dirpath) / fn
                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if ctx is None:
                    m = pattern_ctx.search(text)
                    if m:
                        ctx = int(m.group(1))
                if gpu_layers is None:
                    m = pattern_gpu.search(text)
                    if m:
                        gpu_layers = int(m.group(1))
                if threads is None:
                    m = pattern_threads.search(text)
                    if m:
                        threads = int(m.group(1))
                if ctx is not None and gpu_layers is not None and threads is not None:
                    return ctx, gpu_layers, threads
    return ctx, gpu_layers, threads


def conservative_from(src_ctx, src_gpu, src_threads):
    # Defaults if nothing found
    if src_ctx is None:
        src_ctx = 131072
    if src_gpu is None:
        src_gpu = 33
    if src_threads is None:
        src_threads = 4

    # Conservative scaling
    n_gpu_layers = max(1, int(src_gpu * 0.75))
    ctx_size = min(src_ctx, 65536)
    threads = max(1, int(src_threads))
    return {
        "source_ctx": src_ctx,
        "source_n_gpu_layers": src_gpu,
        "computed_ctx_size": ctx_size,
        "computed_n_gpu_layers": n_gpu_layers,
        "computed_threads": threads,
    }


def dict_to_simple_yaml(d, indent=0):
    lines = []
    pad = "  " * indent
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.extend(dict_to_simple_yaml(v, indent + 1))
            else:
                if v is None:
                    val = ""
                elif isinstance(v, bool):
                    val = "true" if v else "false"
                else:
                    val = str(v)
                lines.append(f"{pad}{k}: {val}")
    elif isinstance(d, list):
        for item in d:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(dict_to_simple_yaml(item, indent + 1))
            else:
                lines.append(f"{pad}- {item}")
    else:
        lines.append(f"{pad}{d}")
    return lines


def main():
    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    src_ctx, src_gpu, src_threads = find_exec_params(ROOTS)
    computed = conservative_from(src_ctx, src_gpu, src_threads)

    profile = {
        "name": "Qwen3.5-9B (conservative)",
        "provider": "openai",
        "apiBase": "http://127.0.0.1:8080/v1",
        "apiKey": "local",
        "model": "Qwen3.5-9B-GLM5.1-Distill-v1-BF16",
        "capabilities": ["chat"],
        "defaultCompletionOptions": {
            "contextLength": computed["computed_ctx_size"],
            "temperature": 0.2,
            "maxTokens": 1024,
        },
        "requestOptions": {
            "timeout": 120000,
            "headers": {"Authorization": "Bearer local"},
        },
        "notes": "Generated conservatively from detected Nemotron params; do not apply automatically.",
    }

    # Write YAML
    yaml_lines = dict_to_simple_yaml(profile)
    OUT_YAML.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_search_roots": [str(p) for p in ROOTS],
        "source_ctx_detected": computed["source_ctx"],
        "source_n_gpu_layers_detected": computed["source_n_gpu_layers"],
        "computed": {
            "ctx_size": computed["computed_ctx_size"],
            "n_gpu_layers": computed["computed_n_gpu_layers"],
            "threads": computed["computed_threads"],
        },
        "output_yaml": str(OUT_YAML),
        "notes": "No changes made to C:\\Users\\Baxter\\.continue\\config.yaml. Review before applying.",
        "suggested_tests": [
            "Invoke GET http://127.0.0.1:8080/v1/models with Authorization: Bearer local",
            "POST /v1/chat/completions with model set to this profile's model and small message",
        ],
    }

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Wrote:")
    print(" -", OUT_YAML)
    print(" -", OUT_JSON)


if __name__ == "__main__":
    main()
