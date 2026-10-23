# E2E測試報告 — TASK-20261011-line-baseline-recovery-02（recovery-02 IMPLEMENT）

**識別與執行配置（§1）**
- local task：`TASK-20261011-line-baseline-recovery-02`；stage：`IMPLEMENT`；run_id：`a8e86935-d398-4e9c-b860-03f52cba8fec`；日期：2026-10-11；task_class：`QUICK`（plan_review／handoff_review／independent_acceptance 均 false）。
- 執行配置：root 串行執行所有官方步驟與 gates（同一條 frozen 驗證集合，各一次性）；本輪經使用者明確授權（2026-10-11 implement turn：「最大的 subagent 平行處理、非唯讀、提升效率」）額外啟用平行起草/核對子代理於 tail deliverables：報告起草 `Hume`（report-drafter，單檔 RUNROOT-only）、ledger 起草 `Halley`（ledger-drafter，單檔 RUNROOT-only）、唯讀 hash census `Carver`（hash-verifier）、唯讀 preservation 稽核 `Darwin`（preservation-verifier）。四位 agent IDs 完整記於 `evidence/attempt-ledger-recovery-02.json` 的 `user_authorized_parallel_authoring.agent_ids`；root 逐項核對後定稿本報告。
- 本輪唯讀稽核已完成：hash census 0 mismatch；preservation 稽核全部獨立重算相符；稽核另修正本報告 6 處細部描述（已併入 §5、§7、§8、§13 註記）。
- native controller writer allocations/receipts：`NOT_RUN`。本環境無 Harness native controller、無 stage packet，因此不存在 controller-registered writer、worktree 或 allocation receipt；子代理是使用者授權的起草/核對者，不冒充 native writer。native Harness（admission/contract/result validators）一律 `NOT_RUN`。
- 本檔（`E2E測試報告.md`）為本輪唯一可寫交付之一；寫入後即定稿（除 root 明確要求修改）。本報告不自引用自身 hash。

**目標與授權範圍（§2）**
- 本地目標（plan §1）：修復 task-local 完整 filesystem baseline（型別感知、FIFO 僅 lstat）與固定 root guarded runner；在 G_RUNNER PASS 後對 unchanged adapter 各執行一次 Node syntax 與一次完整（existing + supplemental）suite；產出報告交 Planner。
- 範圍限 `RUNREL = harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02`（allowed_paths 僅此一項）。ROOT 外零寫入；RUNROOT 外既有 dirty/untracked/ignored 全部保留。
- 明確排除：無 LINE UI／前景操作、無 Save All／chooser／下載、無產品或 state／config／ledger／backups 寫入、無 commit／push、無網路（`network=OFF`、`browser=false`、`destinations=[]`）、未關閉 parent E2E。產品 attempt 額度不重置。
- 授權界線：使用者對子代理的授權只涵蓋 tail deliverables 的起草/核對，不擴張至產品編輯、狀態遷移、LINE、下載或 Git 發布。

**計畫版本（§3，凍結，全部經磁碟 shasum 核對）**

| 檔案（ROOT 相對） | bytes | sha256 | 核對 |
|---|---|---|---|
| `…/recovery-02/plan.md` | 21887 | `6604529c8e9bf06aa59eeb4a0c92358a0b0e7218335d6cd568e8cd4d96bb71bc` | 相符 |
| `…/recovery-02/handoff.md` | 18692 | `fa076f677c547abe690f6b0be5d1d996c85110bc89cd5634c4f023022a72c3c5` | 相符 |
| `…/recovery-02/plan-contract.json` | 2811 | `057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a` | 相符 |
| `…/recovery-02/handoff.json` | 2811 | `057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a` | 相符（與 plan-contract.json 逐 byte 相同） |
| `…/recovery-02/check-specs.json` | 11288 | `5bd52c11c232fecee06b6edb83b009ea49fcb1378459a5653f31310bb8b59d4c` | 相符 |
| `…/recovery-02/check-specs-freeze.json` | 2278 | `1010261ee03bf1d327410d125488b00fc8ae5678d1fe0516e12dcd95ba5a6a70` | 相符（created 2026-10-11T03:12:27Z；generator `tmp/write_freeze.py` `9916110e…`；`native_harness_validation=NOT_RUN`） |
| `…/recovery-02/evidence/planned-additions.json` | 13550 | `98b62f049ed1c9bdff64039b43cdfac6e688edfc4d7e7147e8a421201ed22d92` | 相符（finalized 2026-10-11T03:17:09Z；修訂史見 §6/§9） |

（`…/recovery-02/` 以下簡寫為 `R/`；絕對路徑＝`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/` ＋ 相對路徑。）

**環境（§4）**
- ROOT＝`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`；RUNREL＝`harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02`；RUNROOT＝ROOT/RUNREL。
- Git：branch `v43-ab/codex-rev28`；HEAD `6dbd45679ebf54a2c27faf1c8212b475c4b87f7a`；index `13fe8bd0c329367fbbc6a24439a0cf27635c4e30c6193c17b1b940980351cb83`（5,080,170 B）；staged 空。g-baseline check `git_two_observations_equal`＝true；唯讀 Git 使用 `GIT_OPTIONAL_LOCKS=0`。
- `status_z` 觀測為 `996042055ed817989b403c4fb9fa115886c5843cf314207f52410c97bcede759`／11,968,907 B，屬資訊性漂移（gate 不比對；歷史 `67f78557…`／11,943,372 B 保持不動）。
- 固定 runtimes（check-specs executables）：python 52640／`34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804`；node 50320／`1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040`。
- child 執行環境：cwd＝ROOT；timeout 60 s／check；stream limit 1 MiB；`automatic_retry=false`；`TMPDIR/TMP/TEMP=RUNROOT/tmp`；`PYTHONDONTWRITEBYTECODE=1`；Python 以 `-B` 啟動。
- FIFO 政策（lstat-only，永不 open/read/move/recreate）：allowlist 路徑 `evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo`；4 份 inventory 觀測一致：kind=FIFO、mode=420（0o644；含型別之完整 st_mode 為 0o10644）、dev=16777229、ino=124270681、nlink=1、size=0、uid=501、gid=20、mtime_ns=ctime_ns=1789559276839867533、content_read=false、content_hash=null。
- 政策：network OFF；browser false；destinations 空。

**工具與程式（§5；關鍵片段自磁碟實讀，未自創）**
- `R/tools/inventory.py` 22374／`7c4a749c2eeed6b67c9b5c4deda3b4710ddf57cd421bae645b03891a2b7b8e5e`：型別感知完整掃描；FIFO 分支在任何 open 之前；未完成掃描（exception／timeout／unreadable）保留 partial，delta 判 BLOCKED，不中途回空清單。
```
FIFO_REL = (
    "evidence/20260916-auto-verification/attempt-01/archive-phase1/"
    "private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo"
)
FIFO_ABS = ROOT / FIFO_REL
```
```
def _record_fifo(state: ScanState, rel: str, st) -> None:
    state.fifo_found = True
    if not stat.S_ISFIFO(st.st_mode):
        state.error("FIFO_TYPE_CHANGED", rel, f"allowlisted FIFO path is now {stat.filemode(st.st_mode)}")
        state.violation("FIFO_TYPE_CHANGED", rel, "known FIFO path changed type; never opened")
        …
    record = _base_record(rel, st)
    record.update({"kind": "FIFO", "content_read": False, "content_hash": None})
    state.add(record)
    state.fifo_observation = {k: record[k] for k in ("path", "mode", "dev", "ino", "nlink", "size", "mtime_ns", "ctime_ns")}
```
  `complete = not state.errors and not state.timeout`；`policy_ok = not state.policy_violations and state.fifo_found and state.fifo_observation is not None`（L540）；`ScanState.complete`／`ScanState.policy` 以 property 實作（L229、L233），修正 pre-freeze blocker（§8）。
- `R/checks/test_inventory.py` 17168／`9518e419d08cd41170731e4852c4dde5948140ef7f48e5cd88b441e125a087a0`：9 cases（含 `fifo_lstat_only`）；最終官方 selftest 9/9 PASS。
- `R/checks/compare_inventories.py` 19215／`cbee9e07d7467ef66eeda55266f0162ad437b145bb91038fd8a7916990707f9e`：本檔 `SELF_OUTPUTS` 為檔案常數（L55–60；不是 compare JSON 的鍵）：
```
SELF_OUTPUTS = {
    f"{RUNREL}/evidence/inventory-baseline-01.json",
    f"{RUNREL}/evidence/inventory-baseline-02.json",
    f"{RUNREL}/evidence/inventory-preservation-01.json",
    f"{RUNREL}/evidence/inventory-preservation-02.json",
}
```
  L365（p1→p2 consistency）與 L366（b1→p2 delta）皆以 `allowed_additions=… | set(SELF_OUTPUTS)` 計；參數/`WRONG_CWD` 拒絕在副作用前 `return 2`（L393–397，Pasteur blocker 之修正已落地）。
- `R/checks/test_run_command.py` 14764／`157a37c1f3415b50af0e42fa8ada8175c69fb23c967c880fa60835a0620e1d98`：12 cases（錯置/ancestor symlink/argv 未凍結/ID collision/重放/timeout process-group/stream limit/caller cwd）。
- `R/checks/run_command.py` 19829／`7a99176f828aeb098f0f68a16f470e6685782677386d2a9237b6908a10521cf3`：讀 `check-specs-freeze.json` 綁定，缺失或錯配即拒絕（exit 2，副作用前）：
```
    freeze = load_json(FREEZE)
    resolved = freeze.get("resolved_source_hashes") or {}
    …
    if resolved != expected:
        …
        problems.append(f"FREEZE_BINDINGS_MISMATCH:missing={missing}:extra={extra}:mismatched={mismatched}")
```
```
    if check_id not in allowed_ids:
        refusal.append(f"CHECK_ID_NOT_ALLOWED:{check_id}")
    …
        if frozen_argv != [str(item) for item in argv]:
            refusal.append(f"ARGV_NOT_FROZEN:{check_id}")
    …
        if os.path.lexists(path):
            refusal.append(f"ID_COLLISION:{path}")
    if refusal:
        return 2, {"status": "REFUSED", "check_id": check_id, "errors": refusal}
```
- `R/checks/test_capture_regression.mjs` 10808／`dc45d7e79a96e86fee4f942981304e1e0748872d705afeda3a1f54c020d4d639`：補充 Node capture/chooser/SCK/quota 回歸（fake I/O）。
- `R/tools/gate_receipts.py` 28836／`18fafe68fcfff2b34b694e3e9020256111c33c0b22cf1517ddf16223c88154fd`：產生 4 份 gate receipt；backups 檢查以 kind-aware 過濾（`kind == "REGULAR"`，L249；修正 Leibniz blocker，§8），最終 `backups_hashed_in_inventory`＝239 REGULAR 全部 `read_verified`。

**執行步驟與順序（§6；時間為 UTC，`Z`／`+00:00` 並記；expected vs actual 逐項）**

1. **Host anchors（bootstrap）**：任何新契約/工具寫入前，host 兩次 fresh namespace/metadata 觀察須一致。證據：`R/evidence/bootstrap-prewrite-runroot.json` 41,083,592／`bc3be825bde02a2032e5baefcfed907f9e94810e2f39cc77f12eed10c1a4ba5f`；`R/evidence/bootstrap-prewrite-runroot-v2.json` 26694／`4e067bac795173164d11361029c09d4f4a17890d07f3c90cbfbc2428c45f96ce`（後者為 compare-bootstrap-delta 的 prewrite 輸入）。expected：一致；actual：一致，後續 bootstrap delta 的 51 additions 與 planned `pre_baseline_additions` 51 完全對應（removed 0、changed 0、directory_explained 1、failures 0、status PASS）。
2. **Contract materialization**：exclusive 建立 `R/plan-contract.json`、逐 byte 複製 `R/handoff.json`（2811／`057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a`，兩者相同）與 `R/check-specs.json`（11288／`5bd52c11…`）。expected：與 plan/handoff 內嵌契約 block 相同；actual：相符（本地 equality/readback；非 native schema validation，native NOT_RUN）。
3. **Tools + host selftest**：`baseline-selftest-02`＝`…/python3.13 -B R/checks/test_inventory.py`（cwd=ROOT；TMPDIR=RUNROOT/tmp）。03:10:42Z→03:10:49.077Z，exit 0／PASS；stdout 11702／`a1ad63ff46b507df6abdc5c389f2d220ca8a6f4e25025baa29a44773ed673cd2`（9/9 cases；`removed.attempted=true`，paths 68）；stderr 0／`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；receipt 2797／`bd4e5c0cb84449d63dc4ec424058b7cf1518616112a372a086599a6298c87e09`；invocation 2523／`16eb47ec61ccf7242740d53e84480cea9f35b722c1d5248424068fccf1e2ff62`（`readback_verified=true`）。
4. **Freeze**：`R/tmp/write_freeze.py`（sha `9916110e…`）於 03:12:27Z 產生 `R/check-specs-freeze.json`（2278／`1010261e…`）；`resolved_source_hashes` 覆蓋 check-specs、compare_inventories.py、run_command.py、test_capture_regression.mjs、test_inventory.py、test_run_command.py、tools/inventory.py、adapter `bf83dd93…`、tests `0bb0d996…`；self_reference 排除自身。實測次序＝G_BASELINE PASS 後、host preflight 前（與 `source_binding.written_when` 一致）。
5. **Baseline b1/b2**：`tools/inventory.py baseline 01|02`（deadline 1200 s；輸出 evidence/inventory-baseline-0{1,2}.json）。b1：128671（REGULAR 98496、DIRECTORY 30138、SYMLINK 36、FIFO 1），ended 03:11:13.736Z，75024668／`36e825ee70ea24892a96be5ed0e44e8724db8171c4bd788cc22309783946e69e`；b2：128672（REGULAR 98497），ended 03:11:33.944Z，75025245／`3cfa66cab97c1afa14b967d67cfd9000ce90d13b4b426c661e1ee6f8eb94c7d2`；b1→b2 唯一 delta＝b1 自身完成檔（allowed）。errors 0。
6. **Compares（三份，`checks/compare_inventories.py`）**：
   - `baseline-consistency` PASS 1884／`088aa45f3667d63066577276ecb51389c99ab80cf356c8a3c9a0f1118bdf7827`（added 1＝b1 inventory 自身；removed/changed 0）。
   - `bootstrap-delta` PASS 9311／`f38a3ff58c9b083216dbe2602340649ad5a511b36dc1a46753b6a834ef300d33`（added 51＝pre_baseline_additions；removed/changed 0）。
   - `historical` PASS 6132／`89aa047f6083ba5b7b9d730e25deb42639911e49b0e0c8568af418ffbb497954`（historic 98,513；missing 0；changed 0；directory_entry_extensions 0；coverage_gap_counts＝DIRECTORY 29,960／FIFO 1／REGULAR 94；runroot coverage gap false）。
7. **G_BASELINE PASS**：`R/evidence/g-baseline-recovery-02.json` 24360／`879e4aec93999278f32b175b7850ac1ff87527eafe86829a46c0c708fc772279`（37/37 checks；含 selftest pass、b1/b2 usable、三 compares、`git_two_observations_equal`、adapter/test/state/config/ledger/python/node hash、check 36 `backups_hashed_in_inventory`＝239 all regular verified、check 37 `contract_matches_frozen_contract`）。
8. **Runner preflight**：`…/python3.13 -B R/checks/run_command.py --preflight`；03:12:31Z→03:13:19.804Z，exit 0／PASS；receipt 2799／`02a5f555ad44643e423572447fe271dc5561bd7f14fc1207d7396cc059104639`；invocation 2544／`29479fc5f73fb2309bc18e4775e864b4e27981f4f58b3dd8aa658c6b444301e0`；stdout 3703／`22f4bb2263df6f874a6072765a5836edc64132a142a7f5ba6e3a75d3c0c73b8e`；stderr 0／`e3b0…`；`preflight_before_node_launch=true`。
9. **Runner selftest**：`…/python3.13 -B R/checks/test_run_command.py`；03:13:22Z→03:13:41.744Z，exit 0／PASS；receipt 2882／`fbb9245c1ebb03d96f7fe88c96effa722fd240edcb16b39184710cabe7f277be`；invocation 2517／`db2d5ccb0460e9c388252f031b59a13f133971811225c1d20d2e4fb87d41cc05`；stdout 3285／`8fc299ba1a62c8a4e21fae43f314cfbd2ac067792f4547678e4c4d08036ce449`（12/12 cases；removed 1＝fixture 根 `fixtures/selftest-runner-20261011T031322Z-6099`）；stderr 0／`e3b0…`。
10. **G_RUNNER PASS**：`R/evidence/g-runner.json` 7361／`072bf7c508a2631315b2e23f7c47f47c82c8ed408340e45cf86b43acfeaf202b`（11/11 checks）。
11. **Node syntax `node-adapter-syntax-02`**（runner RUN_COMMAND；無 invocation.json，設計如此）：argv `node --check scripts/line_backup_cua_adapter.mjs`（cwd=ROOT）；03:14:19.529959Z→.566Z，exit 0／PASS；receipt 3362／`f483031a49a67ec0757d63d0dac1633f037ec3b43753e5540dfdf8e6b68336e6`；stdout 0／`e3b0…`；stderr 0／`e3b0…`。此 launch 同時消耗產品候選集合第三次（最後一次）：LIVE_CLASSIFIER_CHOOSER 3/3（§11）。
12. **Node tests `node-adapter-tests-01`**：argv `node --test tests/test_cua_adapter.mjs R/checks/test_capture_regression.mjs`；03:14:22.878522Z→.968503Z，exit 0／PASS；receipt 3743／`f5d51efaede49cff45d9760ace29a00aed3feb7da599b4c1ed6be3e3c4a193c6`；stdout 2660／`541d58cb4af4a8168279119a02ce476e6f9591f086188356813a24ebf4b2b23b`（tests 31／pass 31／fail 0／cancelled 0／skipped 0／todo 0；duration_ms 54.3765）；stderr 0／`e3b0…`。
13. **G_ADAPTER_OFFLINE PASS**：`R/evidence/g-adapter-offline.json` 8948／`ad59db8d590adf580f48c34b103f0989b0abe0a3cc8266bba5a95f2f699257b1`（15/15 checks；檔內 `gate_id="g-adapter"`，檔名為 g-adapter-offline.json——唯讀稽核點 3）。
14. **Preservation p1/p2**：`tools/inventory.py preservation 01|02`。p1：128703（REGULAR 98528、errors 0、policy_ok true、elapsed 16.554 s），75043000／`c4b1a330cccca80d1dfc5312dd3be4f96b79c77edcf42602f97fca5a1c4df905`；p2：128706（REGULAR 98531、errors 0、elapsed 6.811 s），75044728／`f4b864e0be855f237360f9553380f6a508c45bbd655ff4c865bbb83922a5af54`；FIFO/DIRECTORY/SYMLINK 不變。tmp host-capture：stdout 725／`39d1010df0a413d2d8e711029377dc5c1462741dee34fdadfdd317c2c867b73a`、724／`b0823611b77c2aeec60c477ff53485785417952171e575c7a91a981e55ee9fc9`；stderr 皆 0／`e3b0…`。
15. **compare-preservation**：`checks/compare_inventories.py preservation`，03:17:13.828Z FAIL；21100／`3ee56302567089d4a0739e301a52c70e18e243a477cb159904a5f8f263d675bd`；inputs＝inventory-baseline-01、inventory-preservation-01、inventory-preservation-02、planned-additions（唯讀稽核點 1）；failures 7（§7）；tmp capture stdout 516／`830ae7592f1a339c0c4a1917352a20683a0b1fedf8fbd98a64e0180ea8186ef7`（`{"blocked_reasons":0,"failures":7,…,"status":"FAIL"}`）、stderr 0／`e3b0…`。
16. **G_PRESERVE FAIL**：`R/evidence/preservation-recovery-02.json` 18870／`c8d9d2ba15250bc595944c2abbcae4261ddb723a7d616020720e506e7f6ae9d7`（23 checks；22 ok；唯一 not-ok＝`compare_preservation`；gate failures＝["compare_preservation"]）。
17. **Tail**：planned-additions finalize 03:17:09Z（13550／`98b62f04…`）；attempt-ledger-recovery-02.json（35079／`827c5241…`，updated_at 03:30Z）、progress.md（4267／`3f626c55…`）、本報告依序落地；`R/evidence/report-manifest.json` 與 `R/evidence/implementation-result.json` 於本報告定稿時尚未建立（root tail 待完成）。
18. **收據結構（唯讀稽核點 4）**：5 個官方 stem（baseline-selftest-02、runner-preflight-01、runner-selftest-01、node-adapter-syntax-02、node-adapter-tests-01）各恰一份 receipt；其中 3 個 host receipt 另有 invocation.json；2 個 Node receipt 為 RUN_COMMAND schema（無 invocation.json、無 `readback_verified` 鍵，設計如此，非缺漏）；5 份對應 stderr 全部 bytes=0／`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

**G_PRESERVE FAIL 專節（§7）**

`compare-preservation.json` 之 7 筆失敗原文（節錄 code/field/path）：
```
{"code": "ADDED_NOT_ALLOWED", "path": "…/recovery-02/tmp/inventory-preservation-02.stderr"}
{"code": "ADDED_NOT_ALLOWED", "path": "…/recovery-02/tmp/inventory-preservation-02.stdout"}
{"code": "FIELD_MISMATCH", "field": "bytes",    "path": "…/recovery-02/tmp/inventory-preservation-01.stdout"}
{"code": "FIELD_MISMATCH", "field": "ctime_ns", "path": "…/recovery-02/tmp/inventory-preservation-01.stdout"}
{"code": "FIELD_MISMATCH", "field": "mtime_ns", "path": "…/recovery-02/tmp/inventory-preservation-01.stdout"}
{"code": "FIELD_MISMATCH", "field": "sha256",   "path": "…/recovery-02/tmp/inventory-preservation-01.stdout"}
{"code": "FIELD_MISMATCH", "field": "size",     "path": "…/recovery-02/tmp/inventory-preservation-01.stdout"}
```
（p1→p2 consistency 另含：added 3＝p1 自身完成之 inventory JSON（allowed self output）＋p2 之 stdout/stderr；changed 1＝inventory-preservation-01.stdout，0 B→725 B。）

機制：p1 掃描期間其 host redirect stdout 尚未完成（0 B），p1 如實記為 0 B；p2 掃描時該檔已完成（725 B）→ `bytes`／`ctime_ns`／`mtime_ns`／`sha256`／`size` 5 欄位不一致（FIELD_MISMATCH×5）。p2 掃描期間才出現 `inventory-preservation-02.stdout/stderr`，p1 未見 → ADDED_NOT_ALLOWED×2。`SELF_OUTPUTS`（compare_inventories.py L55–60）只宣告 `evidence/` 四份 inventory JSON 為 allowed self output，未宣告 `tmp/` host-capture 檔，亦無「捕獲檔可能延遲完成」規則 → deterministic host-capture/policy 互動。依規則不降 gate、不重跑（一次性額度已用盡）、不以更新 baseline 方式讓其通過；**verdict 維持 FAIL**，修正需求交 Planner（§12）。不得宣稱 preservation PASS。

底層 delta 乾淨事實（區分 policy FAIL 與實際漂移）：
- b1→p2 delta：added 35、removed 0、changed 0、directory_explained 3、failures 0、status PASS；35 筆與 `post_baseline_additions_expected` 完全相等且全在 RUNREL。
- RUNROOT 外 0 變動：compare-historical missing 0／changed 0；ledger `outside_runroot_changes: 0`。
- FIFO：4 份 inventory 之 lstat 觀測完全相同（§4；`content_read=false`、`content_hash=null`）。
- backups：4 份 inventory 各 243 records（239 REGULAR＋4 DIRECTORY），239 REGULAR 全部 `read_verified=true`（與 g-baseline check 36 一致）。
- adapter／existing test／state／config／ledger：b1↔p2 hash 相同（adapter `bf83dd93…`、tests `0bb0d996…`、state `455050110…`、config `5e4f769d…`、ledger `92bab0cf…`）。
- 10 筆 host receipt source-hash 重算相符（唯讀 hash census 0 mismatch）。

**嘗試歷史與新資訊（§8）**

Smoke 序列（`R/tmp/`，非官方）：
- `smoke-baseline-selftest-02`（10:49 本機）FAIL：case `fifo_lstat_only` → `AttributeError:'ScanState' object has no attribute 'policy'`；fixture `fixtures/selftest-20261011T024918Z-98375`；`removed.attempted=false`（失敗保留）。stdout 1635／`c0b67a58cea05b058961702f2ced8792a72825d6309915b23d2c5256258f4809`。
- `smoke-baseline-selftest-03` FAIL：同 case → `AssertionError:`；fixture `fixtures/selftest-20261011T025117Z-99017`；`removed.attempted=false`。stdout 1591／`b9c2f7cb76a028dd8b466ea8a53023e5dae1937abc2ac5bb92d022bec967d72b`。
- `smoke-baseline-selftest-04` PASS 9/9：`removed.attempted=true`，paths 68（fixture `fixtures/selftest-20261011T025134Z-99160`）。stdout 11771／`de8539634b0ca469f69128dc56e2e104fedec0625a014f53fda2fcbf0cb9f1af`。
- `smoke-runner-selftest-02` PASS 12/12；`removed` 1（fixture `fixtures/selftest-runner-20261011T025607Z-1731`）。stdout 3285／`81f5de003ddbe48a3bd80971826222d68e8d4722bf452fb66eb40b5a9b12bf68`（與官方 runner-selftest-01 內容一致，同 12/12）。
- `smoke-fixture-listing.json` 34979／`4ca777d7ddbd933009bc36663ba511e27bf33e12b3712a8992976e5ce1809485`：134 entries＝67×2（兩棵 failed-smoke tree 刪除前 listing）。
- 每次嘗試的新資訊：policy property 缺失（02）→ FIFO case AssertionError（03）→ 完整 PASS（04）；官方 selftest 最終 9/9、runner selftest 12/12。
- 刪除證據（唯讀稽核點 6）：`evidence/baseline-selftest-02.stdout` `removed.attempted=true`、`removed.paths` 恰 68 筆；`evidence/runner-selftest-01.stdout` removed 1（fixture 根）。**不一致回報**：attempt-ledger 將「runner selftest cleanup deletions」記為 UNKNOWN 並稱 68-path set 未留 durable record，但磁碟上 68 筆清單即在 baseline-selftest-02.stdout（smoke-04.stdout 亦 68）；以磁碟為準，並將此 ledger/稽核差異交 root 覆核。兩棵 failed-smoke tree 之刪除僅有 note＋目錄現況之間接佐證、無獨立 deletion receipt（此點與稽核一致）。

Pre-freeze helper blocker 與修正（自 `R/evidence/helper-reports/` 重建；無法證實者標 UNKNOWN）：
- `Hilbert`（`agent-01a128ca-8541…`）：FIFO/型別稽核；BLOCKER＝selftest 斷言不存在的 `ScanState.complete`（test_inventory.py:212,232,259,272 vs inventory.py:186-226,525），R14 永遠無法 exit 0。修正：`ScanState` 增 property `complete`／`policy`（L229、L233）；官方 selftest 9/9 PASS。
- `Pasteur`（`agent-01a128ca-8589…`，唯讀、工具未執行）：C1 BLOCKER＝錯誤 args 以 `SystemExit("string")` 離場（exit 1）而非副作用前 exit 2（CWD 拒絕正確）；發生於舊 compare revision `b4afd4a6…`。修正：最終 compare_inventories.py L393–397 `return 2`（sha `cbee9e07…`）。
- `Leibniz`（`agent-01a128d6-690d…`，唯讀 review；含 `/tmp` scratch）：BLOCKER＝backups 檢查 kind-blind（239 regular＋4 directories＝243 records 全要求 regular → 永遠 FAIL）。修正：gate_receipts.py L249 `kind == "REGULAR"`；check 36＝239 all regular verified。
- 其餘 14 份 helper-reports 主題（唯讀稽核點 8）：James=adapter API/behavior report；Lorentz=generic read-only verification；Planck=scope-recovery-05/.local 歷史基線 manifest；Maxwell=scope and method；Bernoulli=hash audit；Ramanujan=one-shot 未消耗稽核；Plato=read-only evidence audit；Bohr=static review PASS（node --check）；Lovelace=Recovery 02 static audit；Huygens=audit result；Kepler=read-only audit（未開 FIFO）；Pascal=AUDITOR_A_FINAL_CODE_FIXES PASS；Euclid=AUDITOR_B_FREEZE_AND_ORDER PASS；Franklin=AUDITOR_C_BOOTSTRAP_DELTA_SIM。
- UNKNOWN：這些 helper 為 pre-freeze 歷史報告，部分 finding 描述的中間修訂已不可回復；磁碟無法證實的中間狀態不列入結論。舊 ledger 未收錄 attempts 保持 UNKNOWN（不當 0）。

**副作用與狀態差異（§9）**

- **35 post-baseline additions**（`R/evidence/planned-additions.json` `post_baseline_additions`；全部 RUNROOT 內，與 delta 完全相等）：`R/check-specs-freeze.json`；`R/evidence/{compare-baseline-consistency,compare-bootstrap-delta,compare-historical,g-adapter-offline,g-baseline-recovery-02,g-runner}.json`；`R/evidence/{inventory-baseline-01,inventory-baseline-02,inventory-preservation-01}.json`；`R/evidence/node-adapter-{syntax-02,tests-01}.{receipt.json,stderr,stdout}`；`R/evidence/planned-additions.json`；`R/evidence/runner-{preflight-01,selftest-01}.{invocation.json,receipt.json,stderr,stdout}`；`R/tmp/{inventory-preservation-01,inventory-preservation-02}.{stdout,stderr}`；`R/tmp/{make_planned_additions.py,write_freeze.py}`；`R/tmp/runner-node-adapter-{syntax-02,tests-01}.summary.{json,stderr}`。
- **Declared tail 7**：`R/evidence/compare-preservation.json`、`R/evidence/preservation-recovery-02.json`、`R/E2E測試報告.md`（本檔）、`R/progress.md`、`R/evidence/attempt-ledger-recovery-02.json`、`R/evidence/report-manifest.json`、`R/evidence/implementation-result.json`（後兩者 PENDING）。
- **額外 host-capture（超出 declared tail、不在 35 內）**：`R/tmp/compare-preservation.stdout` 516／`830ae759…`；`R/tmp/compare-preservation.stderr` 0／`e3b0…`（ledger `extra_host_capture_files` 已如實記錄）。
- **修訂史**：compare-bootstrap-delta 執行時（03:12:05Z）planned-additions 為 r1（8861／`8bbbe820…`，記於該 JSON inputs）；03:17:09Z finalize 為 r2（13550／`98b62f04…`）並作為 compare-preservation 輸入；兩 compare 各自內部一致，無 gate 影響。
- **刪除**：官方 stem 記錄 68（baseline selftest fixtures）＋1（runner fixture 根）；failed-smoke 兩棵樹以 smoke-fixture-listing 134 entries＋note 佐證（無獨立 deletion receipt）；現 `R/fixtures/` 為空目錄。
- **RUNROOT 外零寫入**；Git 前後相同（§4）；產品 adapter／tests／state／config／ledger 本輪未改（hash 前後相同，§7）。
- **Tail 狀態**：progress.md、attempt-ledger-recovery-02.json、本報告已落地；report-manifest.json 與 implementation-result.json 尚未建立（PENDING，root tail）。

**六狀態（§10）**

本地（recovery-02 IMPLEMENT，2026-10-11 定稿）：

| 字段 | 狀態 | 依據 |
|---|---|---|
| PRIMARY_OUTCOME_STATUS | `NOT_ACHIEVED` | 本地五 gate 之 G_PRESERVE FAIL（policy 互動），本地目標未全達成；已證實之 G_BASELINE／G_RUNNER／G_ADAPTER_OFFLINE PASS 與 delta 乾淨事實全數保留。 |
| IMPLEMENTATION_STATUS | `COMPLETE` | 盤點器、fixed-root runner、freeze、五 gates 收據、離線 adapter 驗證與 tail 起草均實際完成；不因 G_PRESERVE FAIL 抹除。 |
| CORE_ACCEPTANCE_STATUS | `FAIL` | G_PRESERVE FAIL（compare-preservation 7 failures；gate 23 checks 中 22 ok）。 |
| REQUIRED_VERIFICATION_STATUS | `INCOMPLETE` | native Harness NOT_RUN；無 stage packet；schema／admission／publication 未驗。 |
| INDEPENDENT_ACCEPTANCE_STATUS | `NOT_REQUIRED` | QUICK；plan-contract／handoff 明定 independent_acceptance_required=false。 |
| TASK_CLOSURE_STATUS | `REPLAN_REQUIRED` | 需新計畫修正 capture/compare policy 後以 fresh lineage 重驗 preservation（不得降 gate）。 |

Parent（不變）：`NOT_ACHIEVED`／`BLOCKED`／`BLOCKED`／`INCOMPLETE`／`PENDING`／`REPLAN_REQUIRED`。

**未執行／未知／限制／停止原因（§11）**

- native Harness：admission／contract／result validators 皆 `NOT_RUN`；無 stage packet；未以任何 JSON parse／equality／readback 冒充 native schema PASS。OS sandbox／network denial 無平台證明，如實記 capability 事實。
- **Planner 交接未完成（無通道）**：本環境沒有可用的 Planner 通道；本報告保留於 RUNROOT 並記「尚未交接」，不聲稱已提交。
- **LINE 未碰**：無前景操作、無 UI／menu 校準、無單本交易、無 Save All／chooser／下載、無 state mutation。parent 之實際 bounded scroll **`SCROLL_TEST_NOT_RUN`**；**兩本交易未執行**；第二本 grounding／整體 batch／state 驗收與 parent 獨立 Acceptance 未執行；不得宣稱父 E2E 或任一交易成功。
- 產品額度：`LIVE_CLASSIFIER_CHOOSER` 已 3/3 用盡（第三次於 `node-adapter-syntax-02` launch 03:14:19.529959Z 消耗）；任何進一步產品檢查需明確決策。工具 fixture／盤點集合與產品集合分開記，未挪用。
- UNKNOWN：舊 ledger 未收錄 attempts（不當 0）；pre-freeze helper 描述的中間修訂不可回復；attempt-ledger 的 68-path deletion UNKNOWN 條目與磁碟 stdout 證據不一致（已於 §8 回報）；native controller／worktree／allocation receipts 不存在（NOT_RUN，不虛構）。
- 限制：官方 check／gate／compare 一次性用盡、永不重跑；G_PRESERVE FAIL 後停止依賴步驟、保存現場、不修改 baseline 或 gate、不另換 writer。
- 停止原因：deterministic host-capture×policy 互動導致 compare-preservation FAIL（§7）；依停止條件交回 Planner。

**下一步決策需求（§12）**

- **選項 A（建議）**：修正 capture/compare policy：把 `tmp/*.stdout`／`*.stderr` host-capture 檔明確宣告為 allowed self outputs（或 declared tail），或改為「不落地捕捉」（capture 只進記憶體，最終只寫 compare JSON）；再以 fresh lineage（新 evidence ID、不覆寫現有 FAIL 收據）重驗 preservation。**不得降低 gate**。
- 選項 B：維持現行 policy，僅以「delta 乾淨」事實請求替代判定（需要明確 waiver 且 gate 為 CORE/MUST_NOT_BREAK，不建議）。
- 選項 C：由 Planner 重新凍結 check 集合與 policy（含是否重配產品 attempt 額度與 native stage packet）。
- 另需決策：`report-manifest.json`／`implementation-result.json` tail 完成方式；是否於新 run 重新綁定 native validators。

**證據索引（§13）**

說明：`R/`＝`harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/`；`ROOT_ABS`＝`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/`；表內相對路徑之絕對路徑＝`ROOT_ABS`＋相對路徑（例：`R/plan.md` → `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/plan.md`）。全部引用檔案以批次 `shasum -a 256`（唯讀）核對；本報告自身不自引用。

**A. Gates／compares／host receipts／ledger**

| 主張 | 證據（相對路徑） | bytes | sha256 | 工具或命令 |
|---|---|---|---|---|
| G_BASELINE PASS（37/37；check 36＝239 backups all regular verified） | `R/evidence/g-baseline-recovery-02.json` | 24360 | `879e4aec93999278f32b175b7850ac1ff87527eafe86829a46c0c708fc772279` | `tools/gate_receipts.py`（`18fafe68…`） |
| G_RUNNER PASS（11/11；preflight＋selftest 12/12） | `R/evidence/g-runner.json` | 7361 | `072bf7c508a2631315b2e23f7c47f47c82c8ed408340e45cf86b43acfeaf202b` | 同上 |
| G_ADAPTER_OFFLINE PASS（15/15；檔內 gate_id=`g-adapter`） | `R/evidence/g-adapter-offline.json` | 8948 | `ad59db8d590adf580f48c34b103f0989b0abe0a3cc8266bba5a95f2f699257b1` | 同上 |
| G_PRESERVE FAIL（23 checks；compare_preservation not ok） | `R/evidence/preservation-recovery-02.json` | 18870 | `c8d9d2ba15250bc595944c2abbcae4261ddb723a7d616020720e506e7f6ae9d7` | 同上 |
| baseline-consistency PASS（added 1） | `R/evidence/compare-baseline-consistency.json` | 1884 | `088aa45f3667d63066577276ecb51389c99ab80cf356c8a3c9a0f1118bdf7827` | `checks/compare_inventories.py`（`cbee9e07…`） |
| bootstrap-delta PASS（added 51＝pre_baseline） | `R/evidence/compare-bootstrap-delta.json` | 9311 | `f38a3ff58c9b083216dbe2602340649ad5a511b36dc1a46753b6a834ef300d33` | 同上 |
| historical PASS（missing/changed 0） | `R/evidence/compare-historical.json` | 6132 | `89aa047f6083ba5b7b9d730e25deb42639911e49b0e0c8568af418ffbb497954` | 同上 |
| compare-preservation FAIL（7 failures；inputs 3 inventories＋planned-additions） | `R/evidence/compare-preservation.json` | 21100 | `3ee56302567089d4a0739e301a52c70e18e243a477cb159904a5f8f263d675bd` | 同上 |
| planned additions（35／7／51；p2 sha） | `R/evidence/planned-additions.json` | 13550 | `98b62f049ed1c9bdff64039b43cdfac6e688edfc4d7e7147e8a421201ed22d92` | `tmp/make_planned_additions.py`（`b52a521b…`） |
| host anchor（bootstrap 前觀測） | `R/evidence/bootstrap-prewrite-runroot.json` | 41083592 | `bc3be825bde02a2032e5baefcfed907f9e94810e2f39cc77f12eed10c1a4ba5f` | host observation |
| host anchor v2（delta 用） | `R/evidence/bootstrap-prewrite-runroot-v2.json` | 26694 | `4e067bac795173164d11361029c09d4f4a17890d07f3c90cbfbc2428c45f96ce` | host observation |
| attempt ledger（含 4 subagent IDs 與 side effects） | `R/evidence/attempt-ledger-recovery-02.json` | 35079 | `827c52410a8f52ba88041dc5d0efb860262737dc1b071c5f2e3b415a37676485` | 起草/root 核對 |
| baseline selftest receipt／invocation／stdout／stderr | 4 檔（見 §6.3） | 2797／2523／11702／0 | `bd4e5c0c…`／`16eb47ec…`／`a1ad63ff…`／`e3b0c442…` | host receipt（固定 Python） |
| runner preflight 4 檔 | （見 §6.8） | 2799／2544／3703／0 | `02a5f555…`／`29479fc5…`／`22f4bb22…`／`e3b0c442…` | host receipt |
| runner selftest 4 檔 | （見 §6.9） | 2882／2517／3285／0 | `fbb9245c…`／`db2d5ccb…`／`8fc299ba…`／`e3b0c442…` | host receipt |
| Node syntax receipt／stdout／stderr | `R/evidence/node-adapter-syntax-02.*` | 3362／0／0 | `f483031a…`／`e3b0c442…`／`e3b0c442…` | RUN_COMMAND receipt（無 invocation） |
| Node tests receipt／stdout／stderr | `R/evidence/node-adapter-tests-01.*` | 3743／2660／0 | `f5d51efa…`／`541d58cb…`／`e3b0c442…` | RUN_COMMAND receipt（無 invocation） |
| 4 份 preservation／baseline inventory | `R/evidence/inventory-{baseline-01,baseline-02,preservation-01,preservation-02}.json` | 75024668／75025245／75043000／75044728 | `36e825ee…`／`3cfa66ca…`／`c4b1a330…`／`f4b864e0…` | `tools/inventory.py`（`7c4a749c…`） |

**B. tmp／checks／tools（本輪產物與 smoke）**

| 證據 | bytes | sha256 |
|---|---|---|
| `R/tmp/inventory-preservation-01.stdout`／`.stderr` | 725／0 | `39d1010df0a413d2d8e711029377dc5c1462741dee34fdadfdd317c2c867b73a`／`e3b0c442…` |
| `R/tmp/inventory-preservation-02.stdout`／`.stderr` | 724／0 | `b0823611b77c2aeec60c477ff53485785417952171e575c7a91a981e55ee9fc9`／`e3b0c442…` |
| `R/tmp/compare-preservation.stdout`／`.stderr` | 516／0 | `830ae7592f1a339c0c4a1917352a20683a0b1fedf8fbd98a64e0180ea8186ef7`／`e3b0c442…` |
| `R/tmp/smoke-baseline-selftest-02.stdout`／`-03.stdout`／`-04.stdout` | 1635／1591／11771 | `c0b67a58…`／`b9c2f7cb…`／`de853963…` |
| `R/tmp/smoke-runner-selftest-02.stdout` | 3285 | `81f5de003ddbe48a3bd80971826222d68e8d4722bf452fb66eb40b5a9b12bf68` |
| `R/tmp/smoke-fixture-listing.json`（134 entries） | 34979 | `4ca777d7ddbd933009bc36663ba511e27bf33e12b3712a8992976e5ce1809485` |
| `R/tmp/runner-node-adapter-syntax-02.summary.json`／`runner-node-adapter-tests-01.summary.json` | 1540／1536 | `d0480f1f…`／`19bd4a56…` |
| `R/tmp/make_host_receipt.py`／`make_planned_additions.py`／`write_freeze.py`／`extract_helper_report_franklin.py` | 6148／4988／2826／4522 | `d753dbcc…`／`b52a521b…`／`9916110e…`／`e70cbd60…` |
| `R/checks/compare_inventories.py`／`run_command.py`／`test_capture_regression.mjs`／`test_inventory.py`／`test_run_command.py` | 19215／19829／10808／17168／14764 | `cbee9e07…`／`7a99176f…`／`dc45d7e7…`／`9518e419…`／`157a37c1…` |
| `R/tools/gate_receipts.py`／`inventory.py` | 28836／22374 | `18fafe68…`／`7c4a749c…` |

**C. helper-reports（17 份；pre-freeze 唯讀稽核）**

| nickname（主題） | 檔案（`R/evidence/helper-reports/…`） | bytes | sha256 |
|---|---|---|---|
| James（adapter API/behavior） | `agent-01a128be-96b8-7520-b8aa-7a7c8ae36477.json` | 28812 | `022a827935b17ad8633cb7f30f1afaac52f82cb621a1aa7add0f7f8e2a915f8f` |
| Lorentz（generic read-only verification） | `agent-01a128c3-e6ab-72f2-b8a8-6da489d256a1.json` | 21371 | `f205928bae69b5e2c51c74a5082b993c081ba40e9e917607b8f672826556c46b` |
| Planck（CON/.local 歷史基線 manifest） | `agent-01a128c3-e6ef-7250-b9de-a0be056889ed.json` | 20954 | `52e548e20cd9321427207db372e2421027e886a2c81b2875b932ab7bd100c6f9` |
| Maxwell（scope and method） | `agent-01a128c3-e73b-7911-8623-ce522bdbe28e.json` | 13696 | `07bcc4bf69350b055c58e93905a5182bded2de9a50569dfc05ee0af827c8c878` |
| Bernoulli（hash audit） | `agent-01a128c3-e771-71b0-b2ae-44b5602844de.json` | 7461 | `c76ba1ce4911b2d2600d9f7ec01ca9dc42dafba67b21214e80e37115fb267997` |
| Hilbert（FIFO 稽核；ScanState.complete BLOCKER） | `agent-01a128ca-8541-7af1-b258-3264a9c869b2.json` | 11278 | `b8b0d09003054eacb16d1d13d9726ef00c31c394e954b8749fadb976bb93b9e7` |
| Pasteur（read-only audit；C1 BLOCKER；工具未執行） | `agent-01a128ca-8589-7752-9713-09ffc7a03bb3.json` | 12074 | `2c5b2359a4784d70c52d1a64b00ae1e252e7730b0e5e0c2ac381fc373aed037e` |
| Ramanujan（one-shot 未消耗稽核） | `agent-01a128ca-85db-7db1-a5d2-8488859cb14c.json` | 4875 | `bd8b883398143e771aca9dc2f9ede00ce43a02b5fdadd4c208b5311ee99f9ccb` |
| Plato（read-only evidence audit） | `agent-01a128ca-8614-7c81-a9d0-3a0cb166ccd1.json` | 17964 | `84914a20cf57f6da081d63ed27f47c3864410237e53be5ab76ddc31f5b7ee848` |
| Bohr（static review PASS；node --check） | `agent-01a128d6-68c7-7973-90bf-d101c881f191.json` | 3679 | `816f45699e984ee20c6688bfa3e366e6a36dd357477040506029ca106534af94` |
| Leibniz（read-only review；kind-blind BLOCKER） | `agent-01a128d6-690d-7d02-bd23-44628a71f9c0.json` | 7244 | `3dc355e2b22ec362edf46860ee04c2234b2a5335b535f723772dcd2bc8676162` |
| Lovelace（Recovery 02 static audit） | `agent-01a128df-e926-7710-91aa-bd58f0bcbc0b.json` | 4949 | `ca069759d6c6e09665d5656c089c8b4c205e876dc085ea45e277ecfda0f56b85` |
| Huygens（audit result） | `agent-01a128df-e95e-7c33-a293-c3847916eb69.json` | 12415 | `329dfd36cc214dbd60a240cade48ef7252b98d0240c49003ad6b09e6b8ea4dde` |
| Kepler（read-only audit；未開 FIFO） | `agent-01a128df-e999-7361-9997-c78163f2f96a.json` | 10500 | `72d4d3cbc5c4472be155147bdf6c8ad3f5feb2955e711572f643ed861f8bd8ec` |
| Pascal（AUDITOR_A_FINAL_CODE_FIXES PASS） | `agent-01a128e7-5938-7a01-8f94-7265b0432633.json` | 12539 | `e6fd649d5bbdf5cd153792d96463d3657134688ea16757339ff05c80e64b9b60` |
| Euclid（AUDITOR_B_FREEZE_AND_ORDER PASS） | `agent-01a128e7-5991-7950-a5f4-a1de3dac0390.json` | 14665 | `907304d1542b996bbb750a0d3c4638780ff0afdaa66841f0ec7324848f66301a` |
| Franklin（AUDITOR_C_BOOTSTRAP_DELTA_SIM） | `agent-01a128e7-59d8-7362-9f31-7ad7de131244.json` | 12209 | `4d140b4b75da65044d2fe9ca8aa2b8030539ff680daa5216c2cf8e3360c38b03` |

**D. 外部參照（產品／狀態／runtime／parent）**

| 證據 | bytes | sha256 |
|---|---|---|
| `scripts/line_backup_cua_adapter.mjs`（unchanged） | 39953 | `bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2` |
| `tests/test_cua_adapter.mjs` | 18529 | `0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd` |
| `state/backup_state.json` | 252115 | `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6` |
| `config/line_backup_config.json` | 384 | `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362` |
| `harness-development/line-v3-live-e2e-20261010/gui-ledger.json` | 123 | `92bab0cf122871b42f3db62af956289b62fbf4e279219766a8850b61f20e135f` |
| python runtime `/opt/homebrew/Cellar/python@3.13/3.13.3/…/bin/python3.13` | 52640 | `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804` |
| node runtime `/opt/homebrew/Cellar/node/26.7.0/bin/node` | 50320 | `1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040` |
| CON 參考報告 `…/scope-recovery-05/E2E測試報告.md` | 21815 | `168dc950512ab10872447840ca7fbe3ab267f34965e52bd5a6f2639794d0bb5d` |
| CON incident `…/scope-recovery-05/evidence/g-baseline.json` | 142531 | `b8837c5dc8aadccf46e24c25d768ed57fa4dde7e7644e5938448b90e67ef464d` |
| CON incident `…/scope-recovery-05/evidence/g-baseline-failure-detail.json`（FIFO lstat 處置） | 1680 | `c0ce0019b68df53f72e2b0e6ab2c0e0ac151df2c3dd8e6619c7289ed38a6a005` |
| CON result `…/scope-recovery-05/evidence/implementation-result.json` | 10490 | `ce74d1deacb972ef835aa41e1e6b1db43bbfb4280af444261c956ee58731f7ef` |
| 歷史 manifest `…/scope-recovery-05/.local/preexisting-files.json` | 27949525 | `b115df6ea55e3a985e98651018e742769b02e6f7854989e68f8d7214680832f2` |
| 歷史 status `…/scope-recovery-05/.local/preexisting-status.z` | 11943372 | `67f7855774654f9f32f635fba5dbc80262b1e72fc950d32df00360a39fa40f04` |
| 前次 baseline attempt stderr／invocation／stdout | 1049／1595／0 | `327d40c8…`／`2bba45fe…`／`e3b0c442…` |
| 事故收據 `…/continuations/evidence/node-adapter-syntax-01.{invocation,receipt,stdout,stderr}`（位於 scope-recovery-05 上一層，唯讀稽核點 5） | 303／678／0／318 | `e6af5795…`／`e1d16b37…`／`e3b0c442…`／`8948d951…` |
| parent ledger `…/continuations/live-grounding-03/attempt-ledger.json` | 10014 | `205461d838d4d1b4d596c5637e03ea087373d229837c3b4aec57fe5a4cdeba1a` |
| parent incident `…/continuations/live-grounding-04/scope-incident-001.json` | 5976 | `0fa1e0d11325bdbc15290b98d178cd808e89ae9aaf3c773bf106ee3f8c56418f` |

**稽核修正採納清單（6 處；唯讀稽核 2026-10-11）**

1. compare-preservation inputs＝3 份 inventory（baseline-01、preservation-01、preservation-02）＋planned-additions（非 4 份 inventory）。
2. `SELF_OUTPUTS` 是 `checks/compare_inventories.py` 常數（L55–60），不是 compare JSON 的鍵；內容＝`evidence/` 四份 inventory JSON。
3. `g-adapter-offline.json` 內 `gate_id`＝`"g-adapter"`（檔名才是 g-adapter-offline.json）。
4. 兩份 Node 收據為 RUN_COMMAND schema：無 `readback_verified` 鍵、無 invocation.json（設計如此，非缺漏）。
5. `node-adapter-syntax-01.*` 4 檔位於 `harness-development/line-v3-live-e2e-20261010/continuations/evidence/`（scope-recovery-05 上一層），不在 recovery-02 evidence 內。
6. 刪除證據：`evidence/baseline-selftest-02.stdout` removed.attempted=true、paths 恰 68（smoke-04.stdout 亦 68）；runner-selftest-01 removed=1（fixture 根）；failed-smoke 兩樹僅有 note＋現況之間接佐證（無獨立 deletion receipt）。

（本報告至此定稿。）
