#!/usr/bin/env python3
"""Minimal stdio MCP server shim for Continue (offline, no network).

Reads JSON lines from stdin, responds with simple JSON-RPC responses, and logs requests to a local file.
This is intentionally minimal to satisfy Continue's expectation of an MCP server process without external deps.
"""
import sys
import json
from pathlib import Path

LOG = Path(__file__).parent.parent.joinpath("onboarding-reports", "mempalace_minimal.log")
LOG.parent.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main():
    log("mempalace_minimal_mcp started")
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except Exception as e:
            # ignore malformed input
            continue
        log(f"REQ: {json.dumps(obj)}")
        # respond with a simple ok result for requests with id
        resp = None
        if isinstance(obj, dict) and "id" in obj:
            resp = {"jsonrpc": "2.0", "id": obj.get("id"), "result": {"ok": True}}
        else:
            # If it's a notification, optionally echo
            resp = {"jsonrpc": "2.0", "id": None, "result": {"received": True}}
        out = json.dumps(resp, separators=(",", ":"))
        print(out, flush=True)
        log(f"RES: {out}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        raise
