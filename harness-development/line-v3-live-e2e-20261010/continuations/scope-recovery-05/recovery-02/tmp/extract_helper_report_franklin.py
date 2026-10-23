#!/usr/bin/env python3
"""Save Franklin's verbatim final report (AUDITOR_C_BOOTSTRAP_DELTA_SIM).

Reads only the parent-session JSONL wait records (read-only input); writes the
RECOVERY_02_HELPER_REPORT_V1 wrapper exactly once (O_EXCL) so a pre-existing
file can never be clobbered. Supports --dry-run for inspection.
"""
import hashlib
import json
import os
import sys

RUNROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION = (
    "/Users/hsiaojohnny/.codex/sessions/2026/10/11/"
    "rollout-2026-10-11T10-12-39-01a128bb-d159-78a0-b562-475f02e58526.jsonl"
)
AGENT_ID = "01a128e7-59d8-7362-9f31-7ad7de131244"
OUT = os.path.join(RUNROOT, "evidence", "helper-reports", "agent-%s.json" % AGENT_ID)

ROLE = (
    "read-only audit helper (AUDITOR_C_BOOTSTRAP_DELTA_SIM): simulate prewrite->current "
    "bootstrap delta, verify no missing/changed prewrite records, predict planned additions "
    "and directory explanation; no writes"
)


def collect():
    texts = []
    with open(SESSION, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if AGENT_ID not in line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            try:
                state = obj["payload"]["item"]["agents_states"].get(AGENT_ID)
            except Exception:
                state = None
            if isinstance(state, dict) and isinstance(state.get("completed"), str):
                texts.append((lineno, state["completed"]))
    return texts


def main():
    dry = "--dry-run" in sys.argv[1:]
    texts = collect()
    uniq = {}
    for lineno, text in texts:
        uniq.setdefault(text, []).append(lineno)
    if len(uniq) != 1:
        raise SystemExit("unexpected unique completed texts: %d" % len(uniq))
    text = next(iter(uniq))
    if "AUDITOR_C_BOOTSTRAP_DELTA_SIM" not in text:
        raise SystemExit("marker missing in extracted text")
    fence_open = text.find("```json")
    fence_close = text.rfind("```")
    if not (0 <= fence_open < fence_close):
        raise SystemExit("fenced json block not found")
    block = text[fence_open + 7 : fence_close].strip()
    parsed = json.loads(block, strict=False)
    if parsed.get("added_count") != 42 or len(parsed.get("added_paths", [])) != 42:
        raise SystemExit("added_paths validation failed")
    strict_ok = True
    try:
        json.loads(block)
    except Exception:
        strict_ok = False
    payload = {
        "agent_id": AGENT_ID,
        "extracted_from": SESSION,
        "format": "RECOVERY_02_HELPER_REPORT_V1",
        "kind": "HELPER_REPORT_VERBATIM",
        "nickname": "Franklin",
        "role_in_this_round": ROLE,
        "source": "subagent_notification",
        "task_id": "TASK-20261011-line-baseline-recovery-02",
        "text": text,
        "text_json_parses": False,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_utf8_bytes": len(text.encode("utf-8")),
        "extraction_note": (
            "Verbatim completed-message text of parent-session wait record(s) %s (byte-identical). "
            "Message is prose plus a fenced JSON report block (added_count=42); the whole text is not "
            "itself JSON (text_json_parses=false). The fenced block parses with json.loads(strict=False) "
            "only: strict=True fails on a raw control character inside one string of the block."
            % ", ".join(str(n) for n in sorted(uniq[text]))
        ),
    }
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if dry:
        preview = dict(payload)
        preview["text"] = text[:90] + "... [%d chars total]" % len(text)
        preview["text_sha256"] = payload["text_sha256"]
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        print("dry-run ok | strict_fence_parse:", strict_ok, "| candidates:", sorted(uniq[text]), "| text_chars:", len(text))
        return
    fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(data)
    back = open(OUT, encoding="utf-8").read()
    if back != data:
        raise SystemExit("readback mismatch")
    print("wrote", OUT)
    print("bytes", len(data.encode("utf-8")), "sha256", hashlib.sha256(data.encode("utf-8")).hexdigest())
    print("text_sha256", payload["text_sha256"], "text_utf8_bytes", payload["text_utf8_bytes"])


if __name__ == "__main__":
    main()
