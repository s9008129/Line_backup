# AGENT-RESUME-P0-20261022：M0 與 M1 階段驗證報告

- 日期：2026-10-22（Asia/Taipei）
- Plan revision：v2.1（Plan SHA-256 `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502`）
- Owner 決策：`EXTERNAL_PLAN_REVIEW=OWNER_WAIVED`；本次免審不代表產品、Code Review 或獨立 E2E PASS。
- 本輪範圍：M0 零 LINE 接線能力，以及 M1 的離線 store／manifest／history／intent／verification／wrapper 薄切片。M1 尚未完成；M2、真實 LINE、Save All、Chooser、下載、真實照片 ImageIO、CI、External Code Review、獨立 DeepSeek E2E 均未執行。
- 產品來源 base：master `64515eb56b04accc40ade9e2db2fe0ad18c1ced3`。
- 文件來源 commit：`0491393b45090897d925f95ca4e6d8c40cd925bc`（PR30，Plan／Handoff bytes 與本地副本逐 bytes 相同）。

## 1. 結論

M0 在本機 macOS 通過一組有界能力檢查：既有 Node runtime 實際以 `node:child_process.spawn` 啟動本地 Python 長活 session，只用 stdin/stdout 的單一 JSON-lines 連線；controller 持有固定 runtime root 的全域非阻塞 `flock`，hello 綁定 controller／GUI host／boot 身分，target Mac 的 file fsync、`F_FULLFSYNC`、directory fsync 與 readback 均成功；controller 遺失後 wrapper 永久關閉，舊 host 仍活時拒絕接管。

M1 薄切片已可在合成資料與 fake app 上演練：固定 100 本 ordered manifest、單一 checkpoint／generation／checksum、跨 task 的 VERIFIED／日期歧義屏障、239／109／329／65 唯讀 history barrier、durable Save All／Chooser intent、同一 inventory／SHA-256／原樣 ImageIO verifier、單次 `app.click` 與 controller 遺失後永久停止。這些是離線實作證據，不是 LINE 或完整 M1 PASS。

沒有取得 LINE app、截圖、AX、OCR 畫面、選單、相簿或照片；本輪離線程序證據中的 `gui_observations=0`、`gui_dispatches=0`，wrapper 測試只呼叫 fake app，沒有正式 GUI 派送。

## 2. 實際執行與結果

### 2.1 文件／來源對帳

| 檢查 | 實際結果 |
|---|---|
| Plan SHA-256 | `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502`，與 handoff 兩處綁定相同 |
| Handoff SHA-256 | `d95c73fca8abcb631a2af56f1c376bbe4d899556eb521f425570038010326d9b` |
| PRD | `0d69c560490504f1b2af5466db680768e27924c4416c879d8c0545f1224a75d5`；實際檔案存在並已讀 |
| ImageIO source | `scripts/agent_resume/image_decode.swift`，SHA-256 `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b`，與指定來源逐 bytes 相同 |
| OCR source | `scripts/agent_resume/modern_ocr.swift`，SHA-256 `19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861`，與指定來源逐 bytes 相同 |
| 原 dirty repo | 未 reset／clean／stash／切換其 branch；本輪從 master 的 external clean worktree 建立 feature branch |

### 2.2 M0 Python 核心測試

命令：

```text
python3 -B -m unittest discover -s tests -p 'test_agent_resume.py' -v
```

實際結果：exit `0`，`Ran 11 tests`，`OK`。涵蓋：

- strict JSON duplicate key／NaN／NUL／size 拒絕。
- 真實 controller process start identity、boot identity 與不存在 PID。
- 固定 root 的 real file fsync／`F_FULLFSYNC`／directory fsync／readback，且 probe 清理後無殘留。
- 全域 writer lock；第二 writer 得到 `WRITER_BUSY`。
- active owner 的舊 host 仍活時拒絕接管；host 結束後可接管。
- `pending_input=true` 在 host 已死時仍拒絕接管。
- canonical lock record 損壞或 duplicate key 時 fail closed。
- hello 後 stdin EOF 以 exit `3` 停止，留下 active barrier；舊 host 未退出時不接管。
- 兩份 Swift 工具來源 hash 與 Plan 指定值一致。

### 2.3 M0 Node／Python 真程序接線

命令：

```text
node --test tests/test_agent_resume_cua.mjs
```

實際結果：exit `0`，`tests 5`、`pass 5`、`fail 0`。使用真 Node child process、真 Python process 與 fake GUI host；沒有 LINE。

- Node 以 `spawn` 啟動 Python `session --task ...`，`shell=false`，單一 stdin/stdout JSON-lines 連線成功。
- hello 回傳的 controller PID/start、host PID/start、boot identity、fixed-root SHA-256、generation 與 writer lock 均通過 wrapper 重驗。
- file fsync、fullfsync、directory fsync、readback 四項皆為 `true`。
- ping 與 clean close 成功；clean record 的 state 為 `closed`，root mode `0700`、lock mode `0600`。
- stale host start identity 在 GUI 能力前被拒絕。
- 強制終止 controller 後，wrapper 進入永久 closed；後續 ping 不再送出。
- 舊 host 仍活時，新 controller 得到 `OLD_HOST_ALIVE`；舊 host 結束後 takeover 成功。
- 第一個 controller 持鎖時，第二個 controller 得到 `WRITER_BUSY`。

### 2.4 M0 原樣 Mac 工具

編譯命令（OCR 依來源所需的 Swift 模組模式加上 `-parse-as-library`，未修改來源）：

```text
xcrun swiftc -O scripts/agent_resume/image_decode.swift -o /tmp/agent-resume-m0.XQRUfX/image_decode
xcrun swiftc -parse-as-library -O scripts/agent_resume/modern_ocr.swift -o /tmp/agent-resume-m0.XQRUfX/modern_ocr
```

| 案例 | 實際結果 |
|---|---|
| 1×1 synthetic PNG，完整 RGB draw | decoder exit `0`、`verdict=PASS`、`decoded=true` |
| 同檔截斷至 20 bytes | decoder exit `1`、`verdict=FAIL`、`decoded=false` |
| OCR source 編譯與 1×1 synthetic PNG | OCR exit `0`；`screenCapture=false`、`uiInputsSent=0`、`items=[]` |

這是 synthetic ImageIO／Vision capability check，不是真實照片或 LINE 畫面驗證。decoder binary SHA-256 為 `11ea74725a0b8f97b2957cfb9bb5e2a24e5376eba5c2c03cea63d031a513ff1e`；OCR binary SHA-256 為 `8677dc6b24105c5dc5c671b09f0e0d90a69fae1a2c9434e5a66780610cf7ee03`。

### 2.5 M1 核心與 wrapper 測試

命令：

```text
python3 -B -m unittest discover -s tests -p 'test_agent_resume.py' -v
node --test tests/test_agent_resume_cua.mjs
python3 -m py_compile scripts/line_backup_agent_resume.py
node --check scripts/line_backup_agent_resume_cua.mjs
git diff --check
```

實際結果：五個命令均 exit `0`；Python `Ran 24 tests`／`OK`，Node `tests 9`、`pass 9`、`fail 0`。M1 新增覆蓋：

- 100 本 ordered manifest 跨新 store 讀取恢復；重複 `inspect`／淺層 `reconcile` 不改 checkpoint、不派送 GUI。
- #50 的 32/80 partial 保留 32 個既有檔案與 hash，整個 task 進 `BLOCKED_AND_PRESERVE_WHOLE_TASK`，#50～100 無派送資格。
- #50 完整後驗證進 VERIFIED，下一次只允許 #51；其後可完成 #51～100，已有 VERIFIED 再次驗證為 idempotent。
- Save All intent 在 click 前已持久化；重啟後為 `UNKNOWN`，零重試。Chooser 前、缺 chooser 證據及 wrapper click 失敗同樣保留 UNKNOWN 屏障。
- 空白目的地等待延遲內容；非空／缺失／額外／zero-byte／partial／symlink 目的地不重建、不覆寫。空目的地超時回 `DESTINATION_EMPTY`。
- 239／109／329／65 history barrier、跨 task VERIFIED skip、跨 task 未解 intent 阻擋，以及同日期不同張數的 `CROSS_TASK_DATE_AMBIGUOUS` 精確傳遞。
- 壞 JSON／duplicate key／未知 schema／checksum／manifest binding／symlink／orphan temp／traversal／generation stale／foreign scope 均 fail closed。
- Node wrapper 對 Save All 與 Chooser 各只呼叫 fake app 一次；重複 request 不再 click。非正 timeout、stale host、controller 死亡、舊 host 存活、`pending_input` 與第二 writer 均有負例。

私有原始證據位於固定 runtime root 的 task evidence，公開路徑遮蔽為：

```text
<HOME>/Library/Application Support/LineBackup/agent-resume/tasks/AGENT-RESUME-P0-20261022/evidence/m1-final-20261022/
```

| 私有證據 | bytes／SHA-256 |
|---|---|
| `python-unittest.stderr` | `2473`／`988d4d1a86a18d6fdd739f777d79edb988e4f662e3e67ebd7c452c0a7d4d575a` |
| `node-test.stdout` | `970`／`74d9050c7fc8ca28375232605060d10ad85a76385aa4960a5343fcd3dd6e9f5c` |
| `sha256.txt` | `3828`／`bfe6202ecb634689bd924b0d59e1082efd07e9d622987e4c3445fa8b980e2662` |

證據目錄 mode `0700`、檔案 mode `0600`。`python-unittest.stdout`、`diff-check.stdout`、`diff-check.stderr` 等空檔 SHA-256 為 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；四個 exit-code 檔內容 `0\n`，SHA-256 為 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`。此目錄不含 LINE 畫面、相簿、下載照片或正式 state。

## 3. 狀態與證據

```text
PRIMARY_OUTCOME_STATUS=IN_PROGRESS
IMPLEMENTATION_STATUS=M0_IMPLEMENTED_M1_IN_PROGRESS_M2_NOT_RUN
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=M0_LOCAL_PASS_M1_PARTIAL_LOCAL_PASS
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
ZERO_GUI_PREFLIGHT=M0_CAPABILITY_PASS_NOT_FULL
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

既有 M0 commit `4d95f186faa5953d1f3478fcfe1d7965b33b8131` 的來源／測試 SHA-256：

```text
465d69ae5367563eb3da8a4756c61be539848708a01875a944e671ad825973af  scripts/line_backup_agent_resume.py
6d8d1db859148669a8604b69a947b19fa1734fdb89e58d1fd21c17afa2eca6eb  scripts/line_backup_agent_resume_cua.mjs
4b6bc740f832aa63e5da2e9b98453358a3db9053117c217a76ade9df0231a9ac  tests/test_agent_resume.py
0b320f96569017e972235511d55fe1a41b8cda353437c01cd96b6ef9738c4008  tests/test_agent_resume_cua.mjs
```

目前工作樹的 M1 薄切片來源／測試 SHA-256（尚未包含在既有 M0 commit）：

```text
95b6ccfe93064f94359da21b7baedaba66f1a83389ef6d694140fc94290d227b  scripts/line_backup_agent_resume.py
94faa5e8092d602c0fab058e4fd9715a83547792d8e26e9d6844487daf7f851c  scripts/line_backup_agent_resume_cua.mjs
984cf25ac73478415a7ac67052e95cc95c2c2a2970f2ef1c14d3db83e8d76f85  tests/test_agent_resume.py
659b288628270e8ab4c0439207bcd0ba917917f0294a6c927b3748ed286bbd2d  tests/test_agent_resume_cua.mjs
```

私有原始證據保留於固定 runtime root 的 task evidence，公開路徑遮蔽為：

```text
<HOME>/Library/Application Support/LineBackup/agent-resume/tasks/AGENT-RESUME-P0-20261022/evidence/m0-final/
```

| 私有證據 | bytes／SHA-256 |
|---|---|
| `python-unittest.stderr` | `c8da5f9ff459325930a3e1d2d44b5da2af5c96620b309a4f481a9cb3beaa10dc` |
| `node-test.stdout` | `d88868c99a615ee3b1f81c3e8856bc718f0653026c2e53fe1308914dce69b0a3` |
| `image-decode.json` | `280e195db9ddf7f684ca83a9e5029cfeddc1f5aea39ab080f4cc516967578e54` |
| `truncated-decode.json` | `dfbc183936e431847a2514fe810b3ed1456931b587da83f82ddf5ec10b3739e9` |
| `ocr.json` | `0d9c06e2ad3a9a0eb7b1cc3a2fec9f74111f77e5fb3213016fdedb22f3053163` |

臨時 synthetic 工具輸出另留存於 `/tmp/agent-resume-m0.XQRUfX/`；其 JSON 與 binary hashes 已記錄於本節與 §2.4。該路徑不是正式 authority。最終 test 證據目錄另含 `python-unittest.stdout`、`node-test.stderr`、`tracked-diff-check.stdout/stderr`，四個空檔 SHA-256 均為 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；`git diff --check` exit `0`。

## 4. 未執行／限制

- `M1` 完整矩陣：`IN_PROGRESS`。現有測試尚未逐項涵蓋 TC01～20 的所有 fault point；尤其 atomic write 的每個 hook 前後故障、ENOSPC、decoder timeout、malformed protocol／oversize、完整 wrapper close／record failure 負例、protected baseline 全流程不變與跨新程序 100 本故障注入仍需補齊。
- `TC01～20` 完整矩陣：`NOT_RUN`；本輪只有上列薄切片與聚焦負例，不能把個別案例外推成矩陣 PASS。
- LINE app 取得、唯讀觀察、截圖、AX、真實 menu OCR、scroll：`NOT_RUN`。
- 真實相簿 Save All、Chooser、下載、逐檔 SHA-256、真實原圖 ImageIO：`NOT_RUN`。
- feature CI／legacy CI、External Code Review、獨立 DeepSeek `deepseek-v4.1-flash:1017` E2E：`NOT_RUN`；目前 repo 尚無 feature workflow，不能宣稱遠端綠燈。
- 本輪未證明實體掉電耐久性，也未證明 OS sandbox／網路隔離。`kill -9`／強制終止只代表程序故障注入。

## 5. 下一個安全動作

在同一 feature worktree 補完 M1 的 TC01～20 故障注入與 wrapper 失敗路徑，新增只在乾淨 checkout 執行 Python／Node／原樣 Mac ImageIO 的 feature CI，重新以精確 HEAD 執行並記錄結果。M1 完整前不取得 LINE GUI、不派送正式 Save All、不宣稱 AC01～10 或獨立驗收 PASS；M2 交付後仍須 External Code Review，才可由 Owner 啟動獨立 DeepSeek E2E。
