#!/usr/bin/env python3
"""Write the evidence-backed partial Implementer handoff for live-grounding-03."""
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


ROOT = Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
CON = "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03"
TASK_ROOT = "harness-development/line-v3-live-e2e-20261010"
TASK = "TASK-20261010-line-v3-live-e2e"
CONTRACT_SHA = "d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219"
RELEASE_ROOT = Path("/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source")
RELEASE_PYTHON = "/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3"
SDK = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk"
EVIDENCE = Path(CON) / "evidence"
CHECK_IDS = [
    "node-check-adapter", "node-check-classifier", "node-check-locators",
    "node-check-runner", "node-check-classifier-test", "node-check-test",
    "adapter-suite-04", "classifier-suite-04", "runner-suite-03",
    "batch-python-06", "binding-python-04", "transaction-python-02",
    "swift-full-suite-01", "swift-full-suite-02", "swift-full-suite-03",
    "auth-suite-01", "auth-suite-02", "grant-validation-02", "grant-validation-03",
    "producer-cli-preflight-01",
]
FINAL_PASS_IDS = [
    "node-check-adapter", "node-check-classifier", "node-check-locators",
    "runner-syntax-04", "adapter-syntax-03", "chooser-syntax-01", "classifier-syntax-01",
    "node-check-classifier-test", "node-check-test",
    "adapter-suite-04", "classifier-suite-04", "runner-suite-03",
    "batch-python-06", "binding-python-04", "transaction-python-02",
    "swift-full-suite-03", "auth-suite-02", "grant-validation-03",
    "producer-cli-preflight-01",
]
FAILURE_SUMMARIES = {
    "node-check-runner": "Initial syntax check failed before a later --check pass; the later runner-syntax-04 receipt is the final check.",
    "classifier-suite-01": "Boundary ordering assertion failed; the classifier was corrected and classifier-suite-04 passed.",
    "runner-suite-01": "The baseline timestamp equality case failed; the adapter/runner evidence was corrected and runner-suite-03 passed.",
    "batch-python-01": "Test setup omitted required fixture environment.",
    "batch-python-02": "Test setup omitted the task-root environment.",
    "batch-python-03": "Fixture artifact-root binding did not match; subsequent run used the fixed task/fixture roots.",
    "batch-python-05": "A new test fixture lacked a Path import; fixed before batch-python-06.",
    "binding-python-01": "Test setup omitted required fixture environment.",
    "binding-python-02": "Test setup omitted the task-root environment.",
    "swift-full-suite-01": "Compilation failed in rev28ctl/main.swift: Any? grant comparisons, throwing resourceValues calls, and missing manifestReference argument; no tests executed.",
    "swift-full-suite-02": "329 tests executed, 17 failed: 16 lacked LINE_BACKUP_INSPECTION_FIXTURES; one clipping fixture only touched the frame boundary. Corrected environment and fixture before the final run.",
    "auth-suite-01": "Test setup omitted LINE_BACKUP_BATCH_TASK; auth-suite-02 passed with the frozen task/fixture roots.",
    "grant-validation-02": "Runtime binding verification first exposed a missing artifact import and then NotADirectoryError while enumerating Swift files; both were fixed before refreshed bindings passed.",
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_ref(path):
    raw = (ROOT / path).read_bytes()
    return {"path": path, "absolute_path": str(ROOT / path), "bytes": len(raw), "sha256": sha(raw)}


def receipt(check_id):
    path = f"{CON}/evidence/{check_id}.receipt.json"
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def invocation(check_id):
    path = ROOT / CON / "evidence" / f"{check_id}.invocation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def receipt_ref(check_id):
    return file_ref(f"{CON}/evidence/{check_id}.receipt.json")


def test_summary(check_id):
    d = receipt(check_id)
    return {"check_id": check_id, "status": d["status"], "exit_code": d["exit_code"],
            "started_at": d["started_at"], "ended_at": d["ended_at"],
            "receipt": receipt_ref(check_id),
            "stdout": file_ref(d["stdout"]["path"]), "stderr": file_ref(d["stderr"]["path"]),
            "invocation": invocation(check_id)}


def main():
    sys.path.insert(0, str(ROOT / "src"))
    from line_backup_batch.store import Store

    con = ROOT / CON
    progress_path = con / "progress.md"
    old_progress = progress_path.read_bytes() if progress_path.is_file() else None
    if old_progress is not None:
        archived = EVIDENCE / "progress-before-implementer.md"
        if not archived.exists():
            archived.parent.mkdir(parents=True, exist_ok=True)
            archived.write_bytes(old_progress)

    snapshot = Store(str(ROOT)).snapshot()
    state = snapshot["state"]
    state_summary = {
        "schema_version": state["schema_version"],
        "revision": state["revision"],
        "runs": len(state["runs"]),
        "verified_albums": len(state["verified_albums"]),
        "active_batch": state["active_batch"],
        "active_writer_id": state["active_writer_id"],
        "context_lock": state["context_lock"],
    }
    state_continuity = {
        "kind": "READ_ONLY_STATE_CONTINUITY",
        "observed_at": now(),
        "project_root": str(ROOT),
        "verdict": "PASS",
        "validation": "Store.snapshot completed, including schema-3 history validation; state/config/source hashes recorded below.",
        "receipt": snapshot["receipt"],
        "state_summary": state_summary,
        "config": {"schema_version": snapshot["config"]["schema_version"],
                   "group_key": snapshot["config"]["group_key"],
                   "group_name": snapshot["config"]["group_name"],
                   "max_albums_per_run": snapshot["config"]["max_albums_per_run"]},
    }
    write_json(f"{CON}/evidence/state-continuity.json", state_continuity)

    baseline_path = f"{CON}/baseline-implementer.json"
    baseline = json.loads((ROOT / baseline_path).read_text(encoding="utf-8"))
    baseline_untracked_path = ROOT / CON / "baseline-untracked.txt.gz"
    baseline_untracked = set(gzip.decompress(baseline_untracked_path.read_bytes()).decode("utf-8").splitlines())
    current_untracked_raw = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"],
                                           cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
    current_untracked = {item.decode("utf-8") for item in current_untracked_raw.split(b"\0") if item}
    allowed_untracked = lambda path: (path.startswith(CON + "/")
        or path == f"{TASK_ROOT}/gui-ledger.json"
        or path == "rev28/Tests/Rev28CoreTests/FrameSupportTests.swift")
    added_untracked = sorted(current_untracked - baseline_untracked)
    out_of_scope = []
    for path in added_untracked:
        if allowed_untracked(path):
            continue
        raw = (ROOT / path).read_bytes()
        stat = (ROOT / path).stat()
        out_of_scope.append({"path": path, "absolute_path": str(ROOT / path), "bytes": len(raw),
                             "sha256": sha(raw), "mtime_ns": stat.st_mtime_ns})

    config_ref = file_ref("config/line_backup_config.json")
    state_ref = file_ref("state/backup_state.json")
    lock_ref = file_ref("state/.line-backup-state.lock")
    gui_path = f"{TASK_ROOT}/gui-ledger.json"
    gui_ledger = json.loads((ROOT / gui_path).read_text(encoding="utf-8"))
    current_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                  stdout=subprocess.PIPE, text=True).stdout.strip()
    current_branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, check=True,
                                    stdout=subprocess.PIPE, text=True).stdout.strip()
    current_index = sha(subprocess.run(["git", "ls-files", "--stage", "-z"], cwd=ROOT,
                                       check=True, stdout=subprocess.PIPE).stdout)
    preservation = {
        "kind": "IMPLEMENTER_PRESERVATION_OBSERVATION",
        "observed_at": now(),
        "baseline": file_ref(baseline_path),
        "branch": {"before": baseline["branch"], "after": current_branch,
                   "unchanged": baseline["branch"] == current_branch},
        "head": {"before": baseline["head"], "after": current_head,
                 "unchanged": baseline["head"] == current_head},
        "index_entries_sha256": {"before": baseline["index_entries_sha256"], "after": current_index,
                                 "unchanged": baseline["index_entries_sha256"] == current_index},
        "config": {**config_ref, "matches_plan_baseline": config_ref["sha256"] == "5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362"},
        "state": {**state_ref, "matches_plan_baseline": state_ref["sha256"] == "455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6",
                  "revision": state["revision"], "active_batch": state["active_batch"],
                  "active_writer_id": state["active_writer_id"], "context_lock": state["context_lock"]},
        "lock_file": lock_ref,
        "gui_ledger": {**file_ref(gui_path), "entries": len(gui_ledger["entries"]),
                       "cap": gui_ledger["cap"], "baseline_reported_absent_as_zero": True},
        "backup_writes": {"count": 0, "basis": "No LINE/CUA action, Save All, download, or backup-path write command was executed in this continuation."},
        "outside_scope_untracked_additions": out_of_scope,
        "outside_scope_note": "These paths were absent from the frozen untracked baseline. Eight task-root evidence files appeared during/after Python test runs and six Python bytecode cache files appeared after a Store snapshot call; this attribution is an inference from their content/path and timestamps. They were left untouched. No cleanup or commit was performed.",
        "verdict": "PARTIAL" if out_of_scope else "PASS",
    }
    write_json(f"{CON}/evidence/preservation.json", preservation)

    grant_validation = test_summary("grant-validation-03")
    producer_preflight = test_summary("producer-cli-preflight-01")
    auth = {
        "gate_id": "G_AUTH",
        "verdict": "PASS",
        "observed_at": now(),
        "source_sha256": snapshot["receipt"]["source_sha256"],
        "config_sha256": snapshot["receipt"]["config_sha256"],
        "contract_sha256": CONTRACT_SHA,
        "runtime_binding": file_ref(f"{CON}/runtime-binding.json"),
        "authorization": file_ref(f"{CON}/authorization.json"),
        "grants": [file_ref(f"{CON}/live-grant-1.json"), file_ref(f"{CON}/live-grant-2.json")],
        "producer_binary": file_ref(f"{CON}/bin/rev28ctl"),
        "native_decoder": file_ref(f"{TASK_ROOT}/bin/image_decode"),
        "authorization_validation": grant_validation,
        "producer_cli_preflight": producer_preflight,
        "scope": {"owners": ["live-grounding-03-g1", "live-grounding-03-g2"],
                  "album_quota": 2, "lifecycle_limit": 1, "save_all_limit": 2,
                  "chooser_limit": 2, "reversible_gui_limit": 1000,
                  "independent_acceptance_required": True,
                  "acceptance_evidence": None},
        "limits": "This proves local grant/runtime/hash/scope validation and executable startup only. It does not prove native stage admission, actual CUA process bridge, live capture, or album acceptance.",
    }
    write_json(f"{CON}/evidence/g-auth.json", auth)

    all_checks = [test_summary(check_id) for check_id in CHECK_IDS]
    failed = [{"check_id": check_id, "summary": FAILURE_SUMMARIES[check_id],
               "receipt": receipt_ref(check_id)}
              for check_id in FAILURE_SUMMARIES if (ROOT / CON / "evidence" / f"{check_id}.receipt.json").is_file()]
    offline = {
        "gate_id": "G_OFFLINE",
        "verdict": "PASS",
        "observed_at": now(),
        "final_passes": [test_summary(check_id) for check_id in FINAL_PASS_IDS],
        "test_counts": {"adapter_node": 18, "classifier_node": 3, "runner_node": 4,
                        "batch_python": 70, "project_binding_python": 31,
                        "transaction_core_python": 5, "post_fix_authority_python": 24,
                        "swift": 329},
        "python_environment": {
            "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1",
            "LINE_BACKUP_BATCH_TASK": f"{TASK_ROOT}",
            "LINE_BACKUP_INSPECTION_TEST_ROOT": f"{TASK_ROOT}/fixtures",
            "interpreter": "/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3",
        },
        "swift_environment": {
            "SWIFT_MODULE_CACHE_PATH": f"{ROOT}/{CON}/swift-module-cache-26.5",
            "CLANG_MODULE_CACHE_PATH": f"{ROOT}/{CON}/clang-module-cache-26.5",
            "TMPDIR": f"{ROOT}/{CON}/tmp-swift-26.5",
            "LINE_BACKUP_INSPECTION_FIXTURES": f"{ROOT}/{TASK_ROOT}/fixtures/swift-inspection",
            "sdk": "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk",
        },
        "failed_attempts_retained": failed,
        "scope_limit": "All listed PASS results are local offline tests or local source/grant checks. No LINE foreground screenshot, live album, chooser, Save All, download, scroll, or independent Acceptance was run.",
    }
    write_json(f"{CON}/evidence/g-offline.json", offline)

    run_id = str(uuid.uuid4())
    run_identity = {"kind": "LOCAL_IMPLEMENTER_RESULT_ID", "run_id": run_id,
                    "native_harness_run_id": None,
                    "note": "This UUID identifies the locally authored role result only; no native controller run, invitation, or stage receipt was allocated."}
    write_json(f"{CON}/evidence/implementer-local-run.json", run_identity)

    report = f"""# E2E 測試報告 — live-grounding-03

更新時間：{now()}（UTC）  
Task：`{TASK}`  
Plan：`{CON}/plan.md`，SHA-256 `{file_ref(f'{CON}/plan.md')['sha256']}`  
Handoff：`{CON}/handoff.md`，SHA-256 `{file_ref(f'{CON}/handoff.md')['sha256']}`  
Contract：`{CON}/plan-contract.json`，SHA-256 `{CONTRACT_SHA}`  
Project root：`{ROOT}`

## 本輪結果

離線實作與驗證已取得部分進展：Swift 全套 329/0、Python 與 Node 必要 suites 通過；新 runtime binding、兩份 v2 grants 及 producer binary 的雜湊／membership／quota 驗證也通過。完整兩本 LINE 相簿 E2E **未執行**。目前沒有使用者明確交還 LINE 前景的紀錄，且 native CUA frame／AX analyzer 尚未以當下真實畫面完成 grounding；因此沒有點擊、滾動、Save All、chooser confirmation、下載或 state mutation。`G_CATALOG`、`G_MENU`、`G_FIRST`、`G_SCROLL`、`G_SECOND` 均未通過；獨立 Acceptance 尚未執行。

本報告引用的機器證據均在 workspace 內，並列 relative path、absolute path、bytes 與 SHA-256。完整測試收據索引見 `{CON}/evidence/g-offline.json`；授權綁定見 `{CON}/evidence/g-auth.json`；state／preservation 觀察見 `{CON}/evidence/state-continuity.json`、`{CON}/evidence/preservation.json`。

## 變更與邊界

本輪在核准路徑內新增／更新 non-menu frame support、native capture timing、grounded classifier、chooser locator、session runner、下載開始觀察、v2 grant source/runtime binding，以及 GUI ledger 類型。主要來源包括：

- `rev28/Sources/Rev28Core/Perception/OcrEngine.swift`：non-menu surface geometry、frame bounds、intersection、uncertainty 與 safe-margin fail-closed checks。
- `rev28/Sources/Rev28Core/Sensor/FrameCapture.swift`、`rev28/Sources/rev28ctl/main.swift`：full-display capture timing、native frame-support 命令與 sidecar/manifest 產出；producer 不建立 GUI input。
- `{CON}/live_classifier.mjs`、`chooser_locators.mjs`、`live_runner.mjs`：同一 capture 綁定、嚴格 17-key frame、typed chooser phase、下載 evidence 與 bounded scroll checks。
- `src/line_backup_batch/observations.py`、`service.py`、`store.py`、`cli.py` 與 `scripts/line_backup_cua_adapter.mjs`：live v2 phase/evidence validation、fresh empty baseline、shared quota 與 runtime source closure。
- `rev28/Tests/Rev28CoreTests/FrameSupportTests.swift`：把 clipping fixture 寬度由剛好 100 改為 101，以確實超出 100px frame；這是測試資料修正，不是降低檢查。

授權綁定在最終來源碼完成後重建。`Store.snapshot()` 觀察到 source SHA `{snapshot['receipt']['source_sha256']}`、config SHA `{snapshot['receipt']['config_sha256']}`、state revision `{state['revision']}`。兩個 grants 分別綁定 owner `live-grounding-03-g1`、`live-grounding-03-g2`，各自保留雙 lifecycle 共用 quota；`acceptance_evidence` 為 `null`，因 Acceptance 尚未發生。驗證只證明本地 bytes／契約／權限 shape，沒有建立 native Harness admission。

授權程式修正的關鍵片段：

```python
def validate_runtime_binding(reader, grant):
    from .observations import artifact
    from .store import SOURCE_PATHS
```

且 Swift membership 遞迴將 `NotADirectoryError` 視為 leaf file，才可建立完整 Swift source list。這兩項錯誤由 `grant-validation-02` 暴露，修正後 `grant-validation-03` 通過。

## 實際執行順序與離線驗證

所有 test stdout、stderr、exit code、bytes 與 SHA-256 留在 `{CON}/evidence`。`run_command.py` 的 invocation 記錄 argv；下表補列實際環境：

| 檢查 | 命令／環境 | 結果與證據 |
|---|---|---|
| Node syntax | `/opt/homebrew/bin/node --check` adapter、classifier、locators、runner 和 tests | PASS；最新 receipts：`node-check-adapter`、`node-check-classifier`、`node-check-locators`、`runner-syntax-04`、`classifier-syntax-01`、`node-check-test`。 |
| Node suites | `/opt/homebrew/bin/node --test tests/test_cua_adapter.mjs`；`--test {CON}/checks/test_live_classifier.mjs`；`--test {CON}/checks/test_live_runner.mjs` | PASS：18 + 3 + 4 tests。Receipts：`adapter-suite-04` stdout SHA `deb797edf09e3047df6ddf62ff4852037e70135d51e67986041df3ed15f6db58`；`classifier-suite-04` stdout SHA `eb4aa6b4171eed6e750947a4648c051b0868002601303ca61082bf5af08cf81b`；`runner-suite-03` stdout SHA `843c6b5b3ae6a097739d6c14d6927778373ddc6bc904cc371ce41913b9a352f9`。 |
| Python batch | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 LINE_BACKUP_BATCH_TASK={TASK_ROOT} LINE_BACKUP_INSPECTION_TEST_ROOT={TASK_ROOT}/fixtures {RELEASE_PYTHON} -B -m unittest discover -s tests -p 'test_batch_*.py' -v` | PASS：70 tests；receipt `batch-python-06`，stderr SHA `0d0ceb1ad142485d043005d256069791beaa61906c6e55b78d8136960d2c1533`。 |
| Python binding | 同環境，`-p test_project_binding.py` | PASS：31 tests；receipt `binding-python-04`，stderr SHA `4b304b2b1b987821f9ec2f2faf6037d072ec04464e65767f3c2db02d0535bad7`。 |
| Python transaction | 同環境，`-p test_transaction_core.py` | PASS：5 tests；receipt `transaction-python-02`，stderr SHA `55f760c20d3525ae53c2a120e64e3a39d3fe649e75c3640f06d1ed72201badbe`。 |
| Authority regression | 同 interpreter；`LINE_BACKUP_BATCH_TASK={TASK_ROOT}`、fixture root `{TASK_ROOT}/fixtures`；`-p test_batch_authority.py` | PASS：24 tests after final CLI fixes；receipt `auth-suite-02`，stderr SHA `a930116d5626303c2c8decff8ca54afa1a7988084af4b4b294a7030e3dba745a`。 |
| Swift full suite | `/usr/bin/swift test --package-path rev28 --sdk {SDK} --scratch-path {ROOT}/{CON}/swift-build-26.5`; module cache、clang cache、TMPDIR 均在 `{CON}`，fixture env `{ROOT}/{TASK_ROOT}/fixtures/swift-inspection` | 最終 PASS：329 tests / 0 failures；receipt `swift-full-suite-03`，stdout SHA `d1aaa94f715d456c1908cd481315a0f46397a76e4b7a2b47cdca8227cba4dda6`，stderr SHA `3b955a3a547eaac6435e0581b09d275b3eeca934e51b0edbed773117b17c596e`。 |
| V2 grants | fixed Python runtime；呼叫 `authorize(root, grant, fixture=False, operation='begin')`，對兩個 owner 各驗一次 | PASS：contract/source/config/runtime membership、producer bytes、authorization／waiver／user decision、quota 與 sensor scope；receipt `grant-validation-03` stdout SHA `d68adc625135c1fc547d9bbd9d08609439a4ae5d9b30e0b8f51babaad364679b`。 |
| Producer startup | 啟動 `{CON}/bin/rev28ctl` 無參數，檢查預期 usage 輸出與 exit 64 | PASS（process-start diagnostic only）；receipt `producer-cli-preflight-01` stderr SHA `7663b1a47cc0efab613a6b8ef5857db07e81619251aa367926bbb53dcb7ade07`。這不等於 live capture/preflight PASS。 |

`{RELEASE_PYTHON}` 是 `/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3`；`{SDK}` 是 `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk`。完整 invocation/environment receipts見 `{CON}/evidence/g-offline.json`。

## 失敗嘗試與新資訊

失敗原始輸出都保留，沒有覆寫：

| 嘗試 | 實際結果／得到的新資訊 | 後續 |
|---|---|---|
| `swift-full-suite-01` | 編譯錯：grant `Any?` 比較型別、throwing `resourceValues`、menu receipt 缺 `manifestReference`；測試未執行。stderr 87,240 B，SHA `9d823d2abaa039af878e847d309bc020dedd4557e5e23ed7dc807f7390eb0e65`。 | 修正 Swift 型別／錯誤處理並補 menu manifest reference。 |
| `swift-full-suite-02` | 編譯成功，329 tests 中 17 failed。16 項因漏傳 `LINE_BACKUP_INSPECTION_FIXTURES`；1 項測試座標 `[0,0,100,40]` 實際剛好落在 frame 內，並未裁切。stderr SHA `281ca32744e89aa6cb5f168cd4bac9813a70a40de9713f219963fd5634dad149`。 | 綁定 fixture 環境，並將 clipping test width 調為 101；第三次 full suite 全通過。 |
| `auth-suite-01` | 測試啟動缺 `LINE_BACKUP_BATCH_TASK`；無產品斷言失敗。 | 補齊核准 task／fixture env，`auth-suite-02` 24/0。 |
| `grant-validation-02` | v2 grant 實際預檢暴露未匯入 `artifact()`；修正後再揭露 Swift membership traversal 未攔截 `NotADirectoryError`。 | 兩處修正、source digest／binary／runtime-binding／auth/grants 重新凍結，`grant-validation-03` PASS。 |
| 早期 Node/Python receipts | `classifier-suite-01` boundary ordering、`runner-suite-01` timestamp equality、Python fixture env/root 與一個 fixture `Path` import 問題；每項新結果後都有修正。 | 最新 suites 為 Node adapter/classifier/runner 18/3/4 PASS、Python 70/31/5 PASS；舊失敗收據仍保留。 |

`attempt-ledger.json` 記錄三次 Swift full-suite reservation：兩次失敗均消耗額度，第三次通過；沒有再啟動 Swift build/test。`grant-validation-03`、`auth-suite-02` 是後續針對新 runtime source binding 的有界回歸檢查。

## Preservation、副作用與差異

- state SHA `{state_ref['sha256']}`、revision `{state['revision']}`，與凍結 Plan baseline 相同；config SHA `{config_ref['sha256']}`，與 Plan baseline 相同。Schema-3 snapshot/history validation PASS；2 runs、2 verified albums、active batch/writer/context lock 均 null。
- Branch `{current_branch}`、HEAD `{current_head}`、Git index SHA `{current_index}` 均未改；沒有 stage、commit、push。原有大量 dirty/untracked 工作沒有 reset/checkout。
- `{gui_path}` 在 frozen baseline 不存在，舊報告已記錄 0 GUI reservations。現在按 Plan 建立正式 ledger，`entries=[]`、`cap=1000`，目前 GUI input 仍為 0。
- 本輪沒有任何 CUA/LINE input、Save All、chooser、下載、scroll 或備份路徑寫入命令；因此 backup files 未由本輪操作改寫。內容逐檔 inventory 未執行，不能宣稱內容解碼／整體備份驗收。
- Preservation 檢查發現 14 個 baseline 之外的 untracked files 落在 allowed paths 外：task-root `evidence/` 8 個檔案、`src/.../__pycache__/` 6 個 `.pyc`。它們出現在測試／Store snapshot 之後；歸因於 batch tests 和一次未帶 `-B` 的 snapshot 是有時間與路徑支持的推論。檔案未刪、未移、未再改；逐檔 bytes/hash 見 `{CON}/evidence/preservation.json`。因此 `G_PRESERVE=PARTIAL`，不掩蓋範圍偏差。

這是本輪的實際副作用與 scope issue。後續不得再執行會往 task-root `evidence/` 寫入的 Python suites，除非先由 Planner 凍結一個在允許路徑內的 test artifact root；不得自行清除上述文件。

## Gate 狀態與未執行項目

| Gate | 本輪狀態 | 證據／原因 |
|---|---|---|
| `G_PLAN_REVIEW_WAIVER` | PASS（waiver） | `plan-review-waiver.json` 綁 contract；Plan Review 本身仍是 `WAIVED_NOT_RUN`，不是 reviewer PASS。 |
| `G_AUTH` | PASS（local） | `evidence/g-auth.json`；native Harness admission 未執行。 |
| `G_OFFLINE` | PASS | `evidence/g-offline.json`；只適用離線檢查。 |
| `G_MIGRATION` | PASS（continuity） | `evidence/state-continuity.json`；未再次 migrate，原 state bytes/history 不變。 |
| `G_CATALOG` | BLOCKED | 缺當下 LINE full-display/AX capture；沒有候選卡證據。 |
| `G_MENU` | BLOCKED | 未觀察真實 menu row／SCK popup pair／latency。 |
| `G_FIRST` | BLOCKED | Save All、chooser、download、content verification、VERIFIED/readback 全部未執行。 |
| `G_SCROLL` | NOT_RUN | first owner 未完成釋放；沒有真實 scroll before/action/after。 |
| `G_SECOND` | BLOCKED | first transaction/scroll 未完成；第二本全流程未執行。 |
| `G_PRESERVE` | PARTIAL | state/config/index 保持不變，但有 14 個 allowed paths 外新 untracked files，見 preservation evidence。 |
| `G_REPORT` | PASS | 本報告、`progress.md`、ledger 與 evidence index 已落檔。 |
| `G_ACCEPTANCE` | NOT_RUN | 仍需未參與本候選實作的 Acceptance Reviewer；helpers 不算。 |
| `G_DELIVERY` | PARTIAL | 離線程式與資料已保存；完整 E2E、required gates 與 Acceptance 未完成。 |

另有 native admission/stage publication/CONTRACT/RESULT validation 均 `NOT_RUN`；本地 schema check 只驗結構，不等同 controller PASS。Planner handoff 尚未完成，因本環境沒有 controller-backed Planner stage。

## 阻塞與下一步

1. 需要使用者把 LINE app 切到前景，開啟「旻謙允禎成長日記」相簿列表並明確回覆「前景已交還」。拿到交接後，第一個動作只會是一次新鮮唯讀截圖＋AX 擷取，用來驗證實際 capture shape；不會在該步點擊、滾動或下載。後續每個 GUI 動作仍會先公告精確動作並取得當次前景交接。
2. 目前分類器仍需要用真實 CUA capture 確認 analyzer/frame references 的實際結構；沒有該觀察就不能接上真實 UI 或宣稱 live grounding。
3. 14 個範圍外 untracked outputs 維持原位；下一輪 Planner 必須決定只調整測試輸出 root 至 `$CON`，以及如何處理已存在 outputs。不得由 Implementer自行刪除或移動。
4. 真機資料補齊後，才可執行 first transaction → release → downward bounded scroll → second transaction。最後再交給獨立 Acceptance；其審查不是本輪額外獨立 Plan Review。

### 證據索引

| 證據 | Relative path | Absolute path | Bytes | SHA-256 |
|---|---|---|---:|---|
"""

    primary_evidence = [
        f"{CON}/evidence/g-auth.json", f"{CON}/evidence/g-offline.json",
        f"{CON}/evidence/state-continuity.json", f"{CON}/evidence/preservation.json",
        f"{CON}/evidence/swift-full-suite-03.receipt.json", f"{CON}/evidence/swift-full-suite-03.stdout",
        f"{CON}/evidence/swift-full-suite-03.stderr", f"{CON}/evidence/batch-python-06.receipt.json",
        f"{CON}/evidence/batch-python-06.stderr", f"{CON}/evidence/adapter-suite-04.receipt.json",
        f"{CON}/evidence/classifier-suite-04.receipt.json", f"{CON}/evidence/runner-suite-03.receipt.json",
        f"{CON}/evidence/auth-suite-02.receipt.json", f"{CON}/evidence/grant-validation-03.receipt.json",
        f"{CON}/evidence/producer-cli-preflight-01.receipt.json",
    ]
    for path in primary_evidence:
        ref = file_ref(path)
        report += f"| {Path(path).name} | `{path}` | `{ref['absolute_path']}` | {ref['bytes']} | `{ref['sha256']}` |\n"
    report += f"| state source | `state/backup_state.json` | `{ROOT}/state/backup_state.json` | {state_ref['bytes']} | `{state_ref['sha256']}` |\n"
    report += f"| config source | `config/line_backup_config.json` | `{ROOT}/config/line_backup_config.json` | {config_ref['bytes']} | `{config_ref['sha256']}` |\n"
    (con / "E2E測試報告.md").write_text(report, encoding="utf-8")

    progress = f"""# live-grounding-03 進度

我們要完成兩本不同 LINE 相簿的真實備份與第二本 scroll 驗收。離線程式、固定來源綁定和 grants 已完成到可驗證的程度：Swift 329/0、Python batch 70/0、project binding 31/0、transaction 5/0、Node adapter/classifier/runner 18/3/4 全通過。grant 預檢也已通過；state revision {state['revision']} 和 config 未變。

目前卡在真實 CUA capture grounding 與 LINE 前景交接。尚未做 LINE 截圖、點擊、滾動、Save All、chooser、下載或 state write，所以兩本 E2E 與獨立 Acceptance 都未完成。需要先取得 LINE 前景交接；第一步只做 fresh 唯讀截圖／AX。若 raw capture shape 與 runner 介面不同，保留 evidence 後回到 Planner，不猜格式。

Swift full suite 三次 reservation 均已消耗：第一次編譯失敗；第二次 17 項失敗（16 項缺 fixture env，1 項錯誤 clipping fixture）；第三次修正環境和 fixture 後 329/0 PASS。grant 驗證又揭露 `artifact()` 匯入和 Swift file traversal 的兩個接線問題，已修正並由 24 項 authority suite 與雙 grant 驗證通過。最近一次明確增加資訊的嘗試讓我們更接近離線完成，但沒有縮短缺少的真機證據。

本輪檢查後發現 14 個 baseline 之外的新 untracked files 落在核准路徑外，可能由 Python test artifacts 和未禁用 bytecode 的 snapshot 命令產生；完整路徑/hash 已列於 `evidence/preservation.json`。我沒有刪除或搬移它們，也不會再跑可能往 `$TP/evidence` 寫入的 suites。下一輪 Planner 需先把 test output root 鎖在 `$CON` 並決定現有檔案處置。若繼續前景工作未獲交接，或 capture shape 無法明確對應，停止在唯讀觀察，不送任何 LINE input。

報告：`E2E測試報告.md`。目前還沒有真實 Planner stage，故正式 Planner handoff 尚未完成。
"""
    (con / "progress.md").write_text(progress, encoding="utf-8")

    blocker = f"""# Blocker packet — live-grounding-03

Task: `{TASK}`  
Plan SHA-256: `{file_ref(f'{CON}/plan.md')['sha256']}`  
Contract SHA-256: `{CONTRACT_SHA}`

## 已證實

- 本機 offline suites 通過：Swift 329/0、Python 70/0 + 31/0 + 5/0，Node adapter/classifier/runner 18/0 + 3/0 + 4/0。
- 新 grant/runtime binding 驗證通過；兩個 owner/quota slots 和 decoder/producer/source hashes 綁定本輪 contract。
- State remains schema 3, revision {state['revision']}, SHA `{state_ref['sha256']}`；config SHA `{config_ref['sha256']}`；兩者都與 Plan baseline 相同。
- GUI ledger 初始 0 reservations；沒有任何 LINE/CUA input 或備份寫入。
- 14 個 baseline 之外的 untracked files 在核准 allowed paths 外，逐檔列於 `{CON}/evidence/preservation.json`。沒有清除或搬動。

## 未知／阻塞

- 沒有當下 LINE CUA full-display bytes/AX tree；真實 capture support、surface/window/PID mapping、catalog card geometry、chooser controls 和 latency 都 UNKNOWN。
- `live_runner` 的 capture/analyzer/locators 尚未以真實 CUA object/data 完成 production binding。Fake tests 不能補這個缺口。
- 當前沒有明確前景交接。不得存取 LINE 前景或輸入。
- 本地測試副作用落到 `$TP/evidence` 和 Python `__pycache__`；在 Planner 凍結安全輸出位置前，不再跑相同可能寫出這些路徑的 Python suites。

## 精確下一步

1. 請使用者將 LINE macOS 切到前景，停在「旻謙允禎成長日記」相簿列表，明確回覆「前景已交還」。
2. 交接後只做一次 fresh read-only screenshot + AX capture，保存原始 bytes/tree 於本輪 evidence，無點擊、滾動、下載。根據 raw structure 對應 runner analyzer；若無法安全映射則停止並附最小原始證據。
3. 先由 Planner 收到本報告與 scope-drift 清單，決定測試輸出 root 與 14 個範圍外檔案後續處置；不要自行刪除／搬移或重跑會產生同類輸出的 Python suites。
4. 即使 grounding 成功，後續每次 LINE UI input 仍需公告目標/精確動作並取得當次前景交接。兩本交易與獨立 Acceptance 仍未執行。

前景交接只讓下一步唯讀 capture 成為可能，不是對 Save All、chooser confirmation、下載或 state mutation 的額外授權。
"""
    (con / "blocker-packet.md").write_text(blocker, encoding="utf-8")

    # Update the live ledger without consuming or re-labeling root issue attempts.
    ledger_path = con / "attempt-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["updated_at"] = now()
    ledger["updated_note"] = "Three Swift full-suite reservations are consumed (01 compile failure, 02 test/setup failures, 03 PASS). Runtime binding/grants were regenerated after two authorization preflight defects; auth-suite-02, grant-validation-03 and producer startup passed. Live GUI remains unrun; 14 outside-scope untracked artifacts were detected and left untouched."
    ledger["implementation_observations"] = [
        {"root_issue_id": "NON_MENU_SCK_SUPPORT", "status": "OFFLINE_PASS_LIVE_NOT_RUN",
         "evidence": ["swift-full-suite-01", "swift-full-suite-02", "swift-full-suite-03"],
         "note": "The native suite passed 329 tests; live CUA frame support still awaits foreground handoff."},
        {"root_issue_id": "LIVE_CLASSIFIER_CHOOSER", "status": "OFFLINE_PARTIAL_LIVE_NOT_RUN",
         "evidence": ["classifier-suite-04", "runner-suite-03"],
         "note": "Offline frame/chooser/scroll/download checks passed; actual CUA analyzer binding remains unknown."},
        {"root_issue_id": "LIVE_RUNTIME_BINDING_ORCHESTRATION", "status": "LOCAL_BINDING_PASS_LIVE_NOT_RUN",
         "evidence": ["auth-suite-02", "grant-validation-03", "producer-cli-preflight-01"],
         "note": "Both current v2 grants validate against exact runtime membership and quotas; live process bridge/lifecycle remains unrun."},
    ]
    write_json(f"{CON}/attempt-ledger.json", ledger)

    # Refresh report refs now that the main report/ledger have been written.
    manifest_paths = primary_evidence + [
        f"{CON}/evidence/g-auth.json", f"{CON}/evidence/g-offline.json",
        f"{CON}/evidence/state-continuity.json", f"{CON}/evidence/preservation.json",
        f"{CON}/E2E測試報告.md", f"{CON}/progress.md", f"{CON}/blocker-packet.md",
        f"{CON}/attempt-ledger.json", f"{CON}/runtime-binding.json",
        f"{CON}/authorization.json", f"{CON}/live-grant-1.json", f"{CON}/live-grant-2.json",
        f"{CON}/plan-review-waiver.json", f"{CON}/plan.md", f"{CON}/handoff.md",
    ]
    evidence_manifest = {
        "kind": "IMPLEMENTER_EVIDENCE_MANIFEST",
        "task_id": TASK,
        "run_id": run_id,
        "stage": "IMPLEMENT",
        "role": "IMPLEMENTER",
        "source_sha256": snapshot["receipt"]["source_sha256"],
        "contract_sha256": CONTRACT_SHA,
        "entries": [file_ref(path) for path in dict.fromkeys(manifest_paths)],
    }
    write_json(f"{CON}/evidence/evidence-manifest.json", evidence_manifest)

    report_ref = file_ref(f"{CON}/E2E測試報告.md")
    auth_ref = file_ref(f"{CON}/evidence/g-auth.json")
    offline_ref = file_ref(f"{CON}/evidence/g-offline.json")
    state_ref_record = file_ref(f"{CON}/evidence/state-continuity.json")
    preserve_ref = file_ref(f"{CON}/evidence/preservation.json")
    blocker_ref = file_ref(f"{CON}/blocker-packet.md")
    manifest_ref = file_ref(f"{CON}/evidence/evidence-manifest.json")
    gate_results = [
        ("G_PLAN_REVIEW_WAIVER", "PASS", file_ref(f"{CON}/plan-review-waiver.json")["path"]),
        ("G_AUTH", "PASS", auth_ref["path"]),
        ("G_OFFLINE", "PASS", offline_ref["path"]),
        ("G_MIGRATION", "PASS", state_ref_record["path"]),
        ("G_CATALOG", "BLOCKED", blocker_ref["path"]),
        ("G_MENU", "BLOCKED", blocker_ref["path"]),
        ("G_FIRST", "BLOCKED", blocker_ref["path"]),
        ("G_SCROLL", "NOT_RUN", blocker_ref["path"]),
        ("G_SECOND", "BLOCKED", blocker_ref["path"]),
        ("G_PRESERVE", "PARTIAL", preserve_ref["path"]),
        ("G_REPORT", "PASS", report_ref["path"]),
        ("G_ACCEPTANCE", "NOT_RUN", None),
        ("G_DELIVERY", "PARTIAL", manifest_ref["path"]),
    ]
    manifests = []
    for evidence_id, path in [
        ("E_BASELINE", baseline_path), ("E_AUTH", f"{CON}/evidence/g-auth.json"),
        ("E_OFFLINE", f"{CON}/evidence/g-offline.json"),
        ("E_MIGRATION", f"{CON}/evidence/state-continuity.json"),
        ("E_PRESERVATION", f"{CON}/evidence/preservation.json"),
        ("E_REPORT", f"{CON}/E2E測試報告.md"), ("E_PLAN_REVIEW_WAIVER", f"{CON}/plan-review-waiver.json"),
        ("E_FRAME_SUPPORT", f"{CON}/evidence/swift-full-suite-03.receipt.json"),
        ("E_CLASSIFIER", f"{CON}/evidence/classifier-suite-04.receipt.json"),
        ("E_CHOOSER", f"{CON}/evidence/adapter-suite-04.receipt.json"),
        ("E_RUNTIME_BINDING", f"{CON}/evidence/g-auth.json"),
        ("E_SESSION_LIFECYCLE", f"{CON}/evidence/runner-suite-03.receipt.json"),
        ("E_BLOCKER", f"{CON}/blocker-packet.md"),
    ]:
        ref = file_ref(path)
        manifests.append({"task_id": TASK, "run_id": run_id, "stage": "IMPLEMENT", "role": "IMPLEMENTER",
                          "source_sha256": snapshot["receipt"]["source_sha256"], "evidence_id": evidence_id,
                          "path": path, "bytes": ref["bytes"], "sha256": ref["sha256"],
                          "contract_sha256": CONTRACT_SHA,
                          "observation": f"Local artifact only: {ref['absolute_path']}"})

    result = {
        "result_format_version": "3",
        "task_id": TASK,
        "run_id": run_id,
        "role": "IMPLEMENTER",
        "candidate_fact": "PARTIAL",
        "validation_fact": "VALID",
        "routing_fact": "EXTERNAL_BLOCKER",
        "statuses": {
            "PRIMARY_OUTCOME_STATUS": "NOT_ACHIEVED",
            "IMPLEMENTATION_STATUS": "BLOCKED",
            "CORE_ACCEPTANCE_STATUS": "BLOCKED",
            "REQUIRED_VERIFICATION_STATUS": "INCOMPLETE",
            "INDEPENDENT_ACCEPTANCE_STATUS": "PENDING",
            "TASK_CLOSURE_STATUS": "IMPLEMENTATION_BLOCKED",
        },
        "gate_results": [{"gate_id": gate, "verdict": verdict, "evidence_manifest": path}
                         for gate, verdict, path in gate_results],
        "evidence_ids": ["E_BASELINE", "E_AUTH", "E_OFFLINE", "E_MIGRATION", "E_PRESERVATION",
                         "E_REPORT", "E_PLAN_REVIEW_WAIVER", "E_FRAME_SUPPORT", "E_CLASSIFIER",
                         "E_CHOOSER", "E_RUNTIME_BINDING", "E_SESSION_LIFECYCLE", "E_BLOCKER"],
        "blocker_fingerprint": "LINE_FOREGROUND_HANDOFF_AND_OUT_OF_SCOPE_TEST_ARTIFACTS",
        "information_gain": True,
        "stage": "IMPLEMENT",
        "plan_sha256": file_ref(f"{CON}/plan.md")["sha256"],
        "handoff_sha256": file_ref(f"{CON}/handoff.md")["sha256"],
        "source_sha256": snapshot["receipt"]["source_sha256"],
        "evidence_manifests": manifests,
        "plan_contract_sha256": CONTRACT_SHA,
        "analysis": {
            "facts": [
                "The final reserved Swift full suite passed 329 tests with 0 failures.",
                "Python batch/binding/transaction suites passed 70/31/5 tests; post-fix authority tests passed 24.",
                "Node adapter/classifier/runner suites passed 18/3/4 tests.",
                "Both current v2 grants pass local runtime membership, producer, contract, waiver, decision and quota validation.",
                "State remains revision 35 with the frozen hash; config hash is unchanged; GUI ledger has 0 entries.",
                "No LINE/CUA UI action, Save All, chooser, download, scroll, or backup-path write occurred.",
                "Fourteen post-baseline untracked files were observed outside Plan allowed paths and left untouched.",
            ],
            "inferences": [
                "The eight task-root evidence files likely came from Python test artifact generation; six bytecode files likely came from a snapshot command run without -B. Attribution is based on paths/timestamps, not a per-file writer trace.",
                "Fresh CUA capture is the next practical evidence source for binding live analyzer/frame references.",
            ],
            "unknowns": [
                "Actual current LINE AX tree, screenshot bytes, display/window/PID mapping, real album geometry and scroll effect.",
                "Chooser control identities, live download-start evidence, full content verification, state commit/readback, and two-album transaction results.",
                "Native Harness admission/stage validation and independent Acceptance.",
                "Whether the untracked scope-drift files require a new Plan or authorized cleanup.",
            ],
            "evidence": [f"{CON}/evidence/evidence-manifest.json", f"{CON}/E2E測試報告.md",
                         f"{CON}/blocker-packet.md", f"{CON}/attempt-ledger.json"],
            "confidence": "High for listed local test/hash/state facts; live LINE and full E2E remain unobserved.",
            "dependencies": {"offline_suites": "PREREQUISITE_SATISFIED", "grant_binding": "PREREQUISITE_SATISFIED",
                             "foreground_handoff": "PREREQUISITE_BLOCKED", "live_acceptance": "PREREQUISITE_BLOCKED",
                             "independent_acceptance": "PREREQUISITE_BLOCKED"},
        },
        "handoff_summary": "離線 native/Python/Node 驗證與兩份 v2 grant 綁定已通過，state/config 未變。完整 LINE 相簿 E2E 未執行：尚無前景交接或真實 CUA capture，且發現 14 個核准路徑外新 untracked artifacts，均未清除。等待使用者交還 LINE 前景做一次唯讀 grounding；後續測試輸出範圍須先交 Planner 決定。Plan Review 為 USER_WAIVED_NOT_RUN；獨立 Acceptance 仍待實作完成後執行。",
        "needs_human": True,
        "human_decisions": [{"id": "LINE_FOREGROUND_HANDOFF",
                             "question": "請將 Mac LINE 切到前景，停在「旻謙允禎成長日記」的相簿列表，並明確回覆「前景已交還」。我接著只做一次 fresh 唯讀截圖與 AX 擷取，不點擊、滾動或下載。",
                             "options": ["前景已交還", "暫不交還，先停在離線結果"],
                             "recommendation": "交還前景後先做唯讀 grounding；任何後續 LINE input 仍逐動作公告並取得當次交接。"}],
        "convergence": {"meaningful_attempts": 3, "consecutive_no_progress": 0,
                        "last_attempt": "Swift full suite passed 329/0; v2 grant preflight uncovered and then verified fixes for two CLI binding errors. Live UI remains unrun.",
                        "information_gain": True, "stuck": False},
    }
    write_json(f"{CON}/results/implementer.result.json", result)

    # The evidence manifest intentionally excludes the result itself to avoid a hash cycle;
    # the result carries the manifest's exact bytes/hash as its last evidence entry.
    result["evidence_manifests"].append({
        "task_id": TASK, "run_id": run_id, "stage": "IMPLEMENT", "role": "IMPLEMENTER",
        "source_sha256": snapshot["receipt"]["source_sha256"], "evidence_id": "E_EVIDENCE_MANIFEST",
        "path": f"{CON}/evidence/evidence-manifest.json",
        "bytes": file_ref(f"{CON}/evidence/evidence-manifest.json")["bytes"],
        "sha256": file_ref(f"{CON}/evidence/evidence-manifest.json")["sha256"],
        "contract_sha256": CONTRACT_SHA,
        "observation": f"Local evidence index: {ROOT}/{CON}/evidence/evidence-manifest.json",
    })
    result["evidence_ids"].append("E_EVIDENCE_MANIFEST")
    write_json(f"{CON}/results/implementer.result.json", result)
    print(json.dumps({"run_id": run_id, "source_sha256": snapshot["receipt"]["source_sha256"],
                      "result": file_ref(f"{CON}/results/implementer.result.json"),
                      "report": file_ref(f"{CON}/E2E測試報告.md"),
                      "progress": file_ref(f"{CON}/progress.md"),
                      "blocker": file_ref(f"{CON}/blocker-packet.md"),
                      "preservation": file_ref(f"{CON}/evidence/preservation.json"),
                      "outside_scope_count": len(out_of_scope)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
