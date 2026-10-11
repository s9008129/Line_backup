# ML07 Amendment 05：e02 父目錄拒絕後的最後一次有界修復

日期：2026-10-11。決策 owner：root Planner。實際作者：`context_history`。本文件記錄已核准的 e03 最後一次 recovery；不改寫原 plan、handoff、machine contract、e01/e02 artifacts、必要 gates、`USER_WAIVED_NOT_RUN` 或獨立 Acceptance 要求。

## e02 的實際結果

Frozen e02 runner 曾收到唯一一次 `E01-evidence-policy` 呼叫，命令為 `epochs/e02/checks/run_command.py E01-evidence-policy`。實際結果是 exit 2、`REFUSED`，錯誤為 `FileNotFoundError: [Errno 2] No such file or directory: 'checks'`。缺少的是 `epochs/e02/evidence/checks` 父目錄。runner 在保存 claim 前發布失敗，因此 claim、invocation、stdout、stderr、receipt 五個輸出都不存在，child 未 launch，正式 check ID 沒有因 durable claim 而消耗。這不是 gate PASS，也不是正式 FAIL receipt。e02 frozen files 和該次拒絕保持原樣；不建立缺漏目錄、不重試 e02，也不搬移 e01 的結果。

唯讀檢視 frozen e02 policy 與實際工具後，發現同類父目錄缺口：`epochs/e02/evidence/inventory`（baseline/preservation scan、compare、receipt、tail）、`epochs/e02/evidence/registrations`（LIVE_EVIDENCE registration），production check outputs 的 `epochs/e02/evidence/checks`，以及未來 D01 的 `evidence/d01` 和 `evidence/d01/artifacts`。規則雖列出其中若干 leaf，materializer 沒有建立其父目錄；runner 也沒有在 claim 前驗證物理父路徑及其身份。Production 的 `module-cache/{clang,swift}`、`fixtures/swift-inspection` 和 `R/bin` 另須各自的已登記實際 producer 在會寫入它們的 check/build 前建立並讀回。

## e03 有界修復和驗證順序

e03 是本計畫允許的最後一個 recovery epoch；不增加第四個 epoch。保留 e01/e02 原始內容及拒絕證據。只複用本機已驗證的七個 pinned wheels，使用 task-local Python 3.13；不下載、不安裝全域依賴。現有 e02 formal source copies 的精確 bytes/hash 必須先讀回核對，live R draft 修改不得覆寫它們。

e03 evidence materializer 對 `tools`、`checks`、`evidence/{artifacts,transactions,checks,inventory,registrations}` 使用 anchored no-follow exclusive mkdir，逐層檢驗 parent，fsync parent，並以 fstat 讀回身份；目錄 refs 納入 materialization receipt。缺少任何父目錄或身份 ref 時，在 claim 前以 typed REFUSED 停止。Runner 對 leaf parent 的實際 ancestry、非 symlink directory 類型及 frozen producer receipt 中的 dev/inode/mode 逐項核對；失敗不建立 claim、不 launch child。Fixtures 同時證明缺 parent 會在 claim 前拒絕，且完整建立的 fixture 可以真實 launch/reap child 並讀回 claim、streams 和 receipt。

D01 的已登記 `tools/prepare_d01.py` 在 host capture 前建立 `evidence/d01` 和 `evidence/d01/artifacts`，各以 no-follow exclusive mkdir 與身份讀回，並發布專屬目錄 setup receipt。Production family setup 在任何依賴這些路徑的正式 claim/child 前建立 `module-cache`、其 `clang`/`swift` 子目錄及 `fixtures/swift-inspection`；build publisher 在寫入 `bin/rev28ctl` 前建立 `R/bin`。所有 setup producer、exact paths、phase、type、cap、receipt 和 readback 必須在其使用前的 frozen policy 中固定；不以 wildcard、整目錄豁免或事後 allowlist 替代。

只有完成 draft regression、完整 current namespace/ancestor/policy/receipt reconciliation，並確認除明確列為待 finalization 的 dependency receipt 外沒有差異，才可一次性 freeze e03。其後依序發布實際 dependency finalization receipt，再以全新 e03 fixed IDs 執行 E01→E02→B01 各一次，完成 baseline-tail readback。e03 B01 receipt、runner stdout、paired scan/receipt 和 tail 必須互相以 exact path/bytes/hash 綁定；e01 blocked baseline 不可代替。掃描 pair 期間停止所有 workspace 寫入。

若 e03 freeze 前 reconciliation 有未核准差異，或 e03 任一正式 publication/check 出現 material failure，保留已產生的 outputs/IDs、更新正式報告和 ledger，停止；不得重試 ID、補目錄、增加 epoch 或改 gate。這階段不做產品改動、CUA/GUI、LINE、state 寫入、Save All、commit 或 push。e03 的證據仍須交獨立 Acceptance；規劃審查豁免不是 PASS。
