# Authoring note — corrected user-fact record v1.1 (Rev19 §19.1)

Scope: provenance and grounding for `source-identity-user-fact.confirmed.v1.1.json`.
This note stays outside the record body: the record gained and lost no keys, and its only
difference from v1 is one string leaf (single changed line; see §4).

## 1. Owner authorization (verbatim) and session reference

- Owner reply (verbatim, 2026-09-17): `1.可以` — authorization to re-author the corrected
  record from the same preserved one-shot gate answer (the original record is not touched;
  a corrected versioned file is added).
- Session: `01a0a9f9-d915-7d10-89f4-1b6772c681a2`; transcript
  `/Users/hsiaojohnny/.codex/sessions/2026/09/16/rollout-2026-09-16T19-28-38-01a0a9f9-d915-7d10-89f4-1b6772c681a2.jsonl`,
  answer message at line 5091 (2026-09-17T06:59:40.847Z), which reads `1.可以` and
  `2.要，授權給你` (answer 1 = this re-authoring; answer 2 = the §19.2 second one-shot ⋮
  authorization, recorded in `evidence/20260916-route/attempt-04/gate-2-authorization.json`).
- The question actually asked (assistant message, transcript line 5084, 2026-09-17T06:21:53.852Z):
  「決定 1：可不可以讓我用你上次那個「是」的答案，重做一份格式正確的確認紀錄？（你原本那份紀錄我不會動，會另外做一份修正版。）」
- The auxiliary third question of the same message ("選單有彈出來嗎？") was left UNANSWERED;
  it is recorded UNANSWERED in the gate-2 authorization artifact and is never assumed.

## 2. Deterministic construction (fail-closed)

- Script: `evidence/20260916-user-fact/build-user-fact-v1.1.py` (5,336 bytes, SHA-256
  `669240f7891a224713f5c5007fca21c4ca0c028757d4d420ae1589733ceb44cc`), frozen byte-identical
  from the pre-verified Stage-04 build script (`/tmp/s4/build_v1_1.py`, same SHA-256).
- Commands run from the repository root (dry-run first, then the real write):
  - `/usr/bin/python3 evidence/20260916-user-fact/build-user-fact-v1.1.py --dry-run`
  - `/usr/bin/python3 evidence/20260916-user-fact/build-user-fact-v1.1.py`
- The script asserts the candidate's exact byte length (1,741) and SHA-256
  (`a8c1055137d14026f7ecbc15b4f06ee540b56114af3276b081a0be72d195c263`) before writing; it
  refuses to overwrite an existing target (`os.path.exists` guard); and it fails closed on:
  leaf-count != 1, key-set drift (top level and under `answer`/`part_2`), `record_version`
  drift, any other-leaf drift, evidence re-hash mismatch, gate-artifact bytes/SHA mismatch,
  and changed-line count != 1.
- Stage-05 re-verification recipe (does not touch the frozen record):
  `/usr/bin/python3 evidence/20260916-user-fact/build-user-fact-v1.1.py --out /tmp/v11-recheck.json`
  then require `/tmp/v11-recheck.json` to be byte-identical (`cmp`) to the frozen v1.1 record.
- Post-write re-read of the frozen file re-hashed to the asserted bytes/SHA-256; v1 and the
  gate artifact re-hashed unchanged after the write.

## 3. Files and hashes

| file | bytes | SHA-256 |
|---|---|---|
| v1 (unchanged history; keeps its recorded defect) | 1,746 | `2cd7eccdb99da5dc15324f3cb89160d5c283651d8bda550e34cbd5cec44b1d5d` |
| v1.1 (this construction) | 1,741 | `a8c1055137d14026f7ecbc15b4f06ee540b56114af3276b081a0be72d195c263` |
| gate artifact `human-gate-answer-20260917.json` (unchanged) | 1,438 | `03ffff57d50a5f97e596749dfa6bbde50b5ab50253c1f34469cc896e89ef57f7` |

## 4. Single-line diff (v1 → v1.1)

```
30c30
<       "confirmed_album": "2024/05/13～2024/05/17",
---
>       "confirmed_album": "2024/05/13～05/17",
```

The changed leaf is `answer.part_2.confirmed_album`; U+FF5E `～` is preserved. All other
values — including `question.text`, `answer.part_2.text`, `answer.raw`,
`part_2.confirmed_group_string`, `part_2.confirmed_expected_images`, `fingerprint.*`,
`supplied_by`, `recorded_at_local`, and the single `evidence[]` entry — are byte-identical
to v1; the evidence entry re-hashes at its recorded absolute path.

## 5. §16.4 per-condition check (frozen product matcher) — all True

Exact command, run from the repository root (self-contained; paste as-is):

```bash
PYTHONPATH=src /usr/bin/python3 - <<'PY'
import copy, hashlib, json, sys
from line_backup_acceptance.common import user_fact_v1_matches, _rehash_evidence_entries

APP = "jp.naver.line.mac"
GROUP = "旻謙允禎成長日記"
FP = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}
V1 = "evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.json"
V11 = "evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.1.json"

v1_text = open(V1, encoding="utf-8").read()
rec_text = open(V11, encoding="utf-8").read()
v1 = json.loads(v1_text)
rec = json.loads(rec_text)
group_key = "line:" + APP + ":" + GROUP
album_label = FP["start_date"].replace("-", "/") + "～" + FP["end_date"][5:].replace("-", "/")
part2 = rec["answer"]["part_2"]

conditions = {
    "answer_raw_nonempty": bool(str(rec["answer"].get("raw", "")).strip()),
    "app_identifier": rec.get("app_identifier") == APP,
    "evidence_rehash": _rehash_evidence_entries(rec.get("evidence")),
    "fingerprint_equal": rec.get("fingerprint") == FP,
    "kind": rec.get("kind") == "source_identity_user_fact",
    "merge_prohibited_true": rec.get("merge_prohibited") is True,
    "part2_confirmed_album_equal": part2.get("confirmed_album") == album_label,
    "part2_confirmed_expected_images_equal": part2.get("confirmed_expected_images") == FP["expected_images"],
    "part2_confirmed_group_string_equal": part2.get("confirmed_group_string") == GROUP,
    "part2_confirms_same_source_true": part2.get("confirms_same_source") is True,
    "question_text_nonempty": bool(str(rec["question"].get("text", "")).strip()),
    "raw_requested_group_join": "line:" + APP + ":" + str(rec.get("raw_requested_group")) == group_key,
    "record_version_is_1.0": rec.get("record_version") == "1.0",
    "source_correspondence_result_CONFIRMED": rec.get("source_correspondence_result") == "CONFIRMED",
    "status_CONFIRMED": rec.get("status") == "CONFIRMED",
}
diff_lines = [(i + 1, a, b) for i, (a, b) in enumerate(zip(v1_text.splitlines(), rec_text.splitlines())) if a != b]
report = {
  "matcher": "line_backup_acceptance.common.user_fact_v1_matches @ src/line_backup_acceptance/common.py:533",
  "group_key": group_key,
  "album_label_expected_by_contract": album_label,
  "record_confirmed_album": part2.get("confirmed_album"),
  "conditions": conditions,
  "conditions_all_true": all(conditions.values()),
  "conditions_true_count": sum(1 for v in conditions.values() if v),
  "conditions_total": len(conditions),
  "matcher_result": user_fact_v1_matches(rec, app_identifier=APP, group_key=group_key, fp=FP),
  "v1_matcher_result_for_reference": user_fact_v1_matches(v1, app_identifier=APP, group_key=group_key, fp=FP),
  "keyset_top_equal_to_v1": set(rec) == set(v1),
  "keyset_answer_part2_equal_to_v1": set(rec["answer"]) == set(v1["answer"]) and set(rec["answer"]["part_2"]) == set(v1["answer"]["part_2"]),
  "record_version": rec.get("record_version"),
  "single_changed_line_one_based": diff_lines[0][0] if len(diff_lines) == 1 else None,
  "single_changed_line_count": len(diff_lines),
  "other_leaf_drift": [k for k in set(v1) | set(rec) if k not in ("answer",) and v1.get(k) != rec.get(k)],
}
ok = (report["conditions_all_true"] and report["matcher_result"] and report["keyset_top_equal_to_v1"]
      and report["keyset_answer_part2_equal_to_v1"] and report["single_changed_line_count"] == 1
      and report["record_version"] == "1.0")
print(json.dumps(report, ensure_ascii=False, indent=1))
print("CHECK_RESULT:", "ALL_TRUE" if ok else "FAILED")
sys.exit(0 if ok else 2)
PY
```

Observed output (recorded 2026-09-17, Stage-04 W1; exit 0):

```json
{
 "matcher": "line_backup_acceptance.common.user_fact_v1_matches @ src/line_backup_acceptance/common.py:533",
 "group_key": "line:jp.naver.line.mac:旻謙允禎成長日記",
 "album_label_expected_by_contract": "2024/05/13～05/17",
 "record_confirmed_album": "2024/05/13～05/17",
 "conditions": {
  "answer_raw_nonempty": true,
  "app_identifier": true,
  "evidence_rehash": true,
  "fingerprint_equal": true,
  "kind": true,
  "merge_prohibited_true": true,
  "part2_confirmed_album_equal": true,
  "part2_confirmed_expected_images_equal": true,
  "part2_confirmed_group_string_equal": true,
  "part2_confirms_same_source_true": true,
  "question_text_nonempty": true,
  "raw_requested_group_join": true,
  "record_version_is_1.0": true,
  "source_correspondence_result_CONFIRMED": true,
  "status_CONFIRMED": true
 },
 "conditions_all_true": true,
 "conditions_true_count": 15,
 "conditions_total": 15,
 "matcher_result": true,
 "v1_matcher_result_for_reference": false,
 "keyset_top_equal_to_v1": true,
 "keyset_answer_part2_equal_to_v1": true,
 "record_version": "1.0",
 "single_changed_line_one_based": 30,
 "single_changed_line_count": 1,
 "other_leaf_drift": []
}
CHECK_RESULT: ALL_TRUE
```

Summary: 15/15 per-condition booleans True and the frozen matcher itself returns True over
v1.1 (16 of 16 overall boolean assertions, counting `matcher_result`); the same matcher
returns False over v1, proving the one-leaf correction is load-bearing rather than cosmetic.
The matcher code is unchanged: `src/line_backup_acceptance/common.py` SHA-256
`df9fe0bc6333a8afec6f0bc87b336cf905e3683a209cbc8155190d4e5a0c60c0` (working tree clean for
`src/`; no product, test, config, state or photo change in this wave).

## 6. Grounding of the corrected value

- Transcript line 2826 (assistant question, 2026-09-17T00:46:44.592Z) asked, verbatim:
  「`Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` 那 57 張，是不是就是
  `旻謙允禎成長日記` 這個群組、2024/05/13～05/17 的備份？」— i.e. the canonical short label
  `2024/05/13～05/17`, exactly the label the §16.4 contract derives
  (`start_date` + `～` + short end) and exactly what v1.1 now records.
- No rule was changed, relaxed, or normalized: §16.4's matching rules are the frozen ones;
  only the authoritative record instance is added, by owner authorization, from the same
  preserved one-shot answer.

## 7. Recorded, not repaired — documentation anomalies

- ANOM-01 (gate artifact stale record back-reference): the frozen gate artifact
  `human-gate-answer-20260917.json` declares `record_path` → `…confirmed.v1.json` with
  `record_bytes` 1,585 and `record_sha256` `603ab720acf474d8350504827e6ebe3f9c281dd3a04bb627332322becf01bd1d`,
  while the actual v1 file on disk is 1,746 bytes with SHA-256 `2cd7eccd…` (declared ≠ actual).
  Recorded; NOT repaired. The gate artifact stays byte-identical (`03ffff57…`), and v1 keeps
  its recorded defect as history.
- ANOM-02 (long-form rendering of the question): the transcript at line 2826 asked the short
  form `2024/05/13～05/17`, while the frozen gate artifact's
  `question_verbatim_questions_only` and the record's `question.text` / `answer.part_2.text`
  render the long form `2024/05/13～2024/05/17`. Those non-matching text fields stay
  byte-identical in v1.1; the authoritative text is the transcript line 2826. Recorded;
  NOT repaired.

## 8. Consequences (as planned in §19.1)

- The §16.4 contract check over v1.1 passes → task-level `SOURCE_CORRESPONDENCE=CONFIRMED`
  for this task (plan.md:1594), subject to independent re-verification at Stage 05 attempt-06.
- This does not claim that the product CLI prints Source=CONFIRMED for the real destination:
  the product-level Source axis stays UNRESOLVED as a disclosed consequence of the read-only
  legacy formal state (plan.md:1162, 1311–1318); no state is written.
- v1, the gate artifact, all prior attempts and the formal project remain untouched.
