#!/usr/bin/env python3
"""Vens orchestrator: lease manager, atomic message writes, archiving, and simple CLI.

Usage examples:
  python orchestrator.py --workdir . --action send_message --from COPILOT --to ANTIGRAVITY --message "Hello"
  python orchestrator.py --workdir . --action acquire_lease --agent COPILOT --ttl 60
"""
import argparse
import datetime
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path


ISO = "%Y-%m-%dT%H:%M:%SZ"


def now_iso():
    return datetime.datetime.utcnow().strftime(ISO)


def ensure_dirs(base: Path):
    (base / "messages" / "incoming").mkdir(parents=True, exist_ok=True)
    (base / "messages" / "archive").mkdir(parents=True, exist_ok=True)
    (base / "messages" / "structured" / "incoming").mkdir(parents=True, exist_ok=True)
    (base / "messages" / "structured" / "archive").mkdir(parents=True, exist_ok=True)
    (base / "state").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)
    (base / "tasks").mkdir(parents=True, exist_ok=True)


def lease_path(base: Path):
    return base / "state" / "active_agent.txt"


def read_lease(base: Path):
    p = lease_path(base)
    if not p.exists():
        return None, None
    txt = p.read_text(encoding="utf-8").strip().splitlines()
    if len(txt) < 2:
        return None, None
    return txt[0].strip(), txt[1].strip()


def acquire_lease(base: Path, agent: str, ttl: int = 60):
    p = lease_path(base)
    now = datetime.datetime.utcnow()
    owner, expires = read_lease(base)
    if owner and expires:
        try:
            exp = datetime.datetime.strptime(expires, ISO)
            if exp > now:
                return False, f"Lease held by {owner} until {expires}"
        except Exception:
            # malformed lease -> allow takeover
            pass
    new_exp = (now + datetime.timedelta(seconds=ttl)).strftime(ISO)
    tmp = p.with_name(f".{p.name}.tmp.{uuid.uuid4().hex}")
    tmp.write_text(f"{agent}\n{new_exp}\n", encoding="utf-8")
    os.replace(tmp, p)
    return True, new_exp


def release_lease(base: Path, agent: str):
    p = lease_path(base)
    owner, _ = read_lease(base)
    if owner != agent:
        return False, f"Lease owned by {owner}, not {agent}"
    # remove lease file to relinquish
    try:
        p.unlink()
        return True, "released"
    except Exception as e:
        return False, str(e)


def atomic_write_message(base: Path, payload: dict):
    incoming = base / "messages" / "structured" / "incoming"
    uid = uuid.uuid4().hex
    final = incoming / f"{uid}.json"
    fd, tmppath = tempfile.mkstemp(prefix=f".{uid}.", dir=str(incoming))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmppath, final)
        return True, final
    except Exception as e:
        try:
            os.remove(tmppath)
        except Exception:
            pass
        return False, str(e)


def archive_message(path: Path, base: Path):
    archive = base / "messages" / "structured" / "archive"
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = archive / f"{ts}-{path.name}"
    shutil.move(str(path), str(dest))
    return dest


def append_log(base: Path, entry: dict):
    p = base / "logs" / (datetime.datetime.utcnow().strftime("%Y%m%d") + ".log")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default=".")
    parser.add_argument("--action", choices=["send_message", "acquire_lease", "release_lease", "show_lease"], required=True)
    parser.add_argument("--from")
    parser.add_argument("--to")
    parser.add_argument("--message")
    parser.add_argument("--agent")
    parser.add_argument("--ttl", type=int, default=60)
    args = parser.parse_args()

    base = Path(args.workdir).resolve()
    ensure_dirs(base)

    if args.action == "acquire_lease":
        agent = args.agent
        ok, info = acquire_lease(base, agent, args.ttl)
        print(ok, info)
        sys.exit(0 if ok else 2)

    if args.action == "release_lease":
        agent = args.agent
        ok, info = release_lease(base, agent)
        print(ok, info)
        sys.exit(0 if ok else 2)

    if args.action == "show_lease":
        owner, exp = read_lease(base)
        print(owner, exp)
        sys.exit(0)

    if args.action == "send_message":
        frm = args.__dict__.get("from")
        to = args.to
        msg = args.message
        if not frm or not to or not msg:
            print("--from, --to and --message are required for send_message")
            sys.exit(2)
        # acquire temporary lease for sender to perform write
        ok, info = acquire_lease(base, frm, args.ttl)
        if not ok:
            print("Failed to acquire lease:", info)
            sys.exit(2)
        payload = {
            "id": uuid.uuid4().hex,
            "from": frm,
            "to": to,
            "type": "request",
            "task": "ad-hoc",
            "content": {"text": msg},
            "meta": {"timestamp": now_iso()}
        }
        ok2, result = atomic_write_message(base, payload)
        append_log(base, {"event": "send_message", "ok": ok2, "path": str(result)})
        # release lease immediately
        release_lease(base, frm)
        if ok2:
            print("WROTE", result)
            sys.exit(0)
        else:
            print("ERROR", result)
            sys.exit(2)


if __name__ == "__main__":
    main()
