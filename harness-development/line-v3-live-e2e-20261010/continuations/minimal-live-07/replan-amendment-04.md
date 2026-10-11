# Replan amendment 04：e02 凍結前的輸入與歷史 evidence 對帳

日期：2026-10-11。此修正由 root Planner 核准，僅整理 e02 evidence freeze 前的精確來源、生命週期與差異對帳。它不改原 plan、handoff、machine contract、risk class、required gates、產品介面或 LINE 操作授權；此核准不代表正式 Plan Review PASS。原 e01 全部 immutable receipts 與結果均保留。

## 明確指定的唯讀 user input

使用者在本輪明確要求深讀 root 下的 `codex-session-01a12976-2554-7ed0-8d4c-356688f674ee.md`。此來源是 `READ_ONLY_USER_INPUT`：不得修改、移動、刪除或覆寫，也不建立任何 root 外部 output rule。原使用者輸入明確存在於目前工作區，但 2026-10-11 06:09:58.275012 UTC 的舊 namespace anchor 尚未包含此 path；舊 anchor 保持原 bytes，不倒填新 path。

本 amendment 核准在 R 內以 exact `evidence/read-only-user-input-01.json` 保存 source bytes 的 immutable annex，另有 exclusive/readback receipt。Annex 明列 task、使用者引用來源、原始絕對路徑、來源目前完整 fstat identity/type/mode/uid/gid/size/birth/mtime/ctime/hash、publisher `context_history`、decision owner `root_planner`、source producer/write authority 為 null，以及觀測 UTC。Annex 自身的 bytes/hash 不嵌入 annex；只記錄於獨立 exclusive/readback receipt。先前在本輪首次寫入前已存在的事實由 root 與來源 birth/mtime 提供；06:09 anchor 時的缺席由原壓縮 records hash 驗證。11:14 前的 bytes 與建立者未知，必須保持 UNKNOWN。

來源 path 僅作讀取，不由本次工具寫入、建立或給予外部產物權限。Annex 和 receipt 是 R 內兩個精確 CREATE_ONCE output。e02 B01 的兩個實際 inventory scan 與 B02 preservation scan 均須重新讀回該 root source，驗證完整 path/dev/ino/actual regular type/mode/uid/gid/size/birth/mtime/ctime/SHA 與 annex 相符；scanner 未記錄 birthtime，故每次另附當次 no-follow fstat/hash readback，絕不宣稱 scanner 原生保存此欄。path 消失、被替換、內容或任一 identity 欄位漂移、意外 sibling，均 BLOCK。

## Anchor 身份與可變 metadata

對 exact allowlisted FIFO，舊 anchor `S` 到 scanner `FIFO` 的表示變化只可在精確 path、actual FIFO subtype、lstat-only (`content_read=false`, `content_hash=null`) 全欄 dev/ino/mode/uid/gid/size/mtime/ctime 完全相符時正規化。未知 special path、錯誤 FIFO subtype、或任一 identity/time/size 改變仍阻擋。一般 regular/directory/symlink 先比較穩定身份：actual type、dev、ino、mode、uid、gid。Directory size/mtime/ctime 僅能在實際 direct-child delta 通過每個 child 的精確合法 policy/receipt 後解釋；無 child delta 的 metadata 改變阻擋。Regular file 的 size/times/content hash 進入 exact lifecycle/readback/receipt 判定，不可使 identity predicate 過早遮蔽政策；symlink target 仍須完全相符。

凍結前實際 12 筆 metadata delta 為：1 個已知 FIFO 的 `S`/`FIFO` label，metadata 全相同；10 個因已登記子項增加而變更 size/mtime/ctime 的 R/e01/evidence/tools directories；及 `R/tools/evidence_io.py` 一個 DRAFT source 的 size/content/times 變動。十個 directory 必須各由現場 child set 對帳，不得整目錄豁免。已知 `R/epochs/e01/tmp/pip-cache` 是 anchor 後唯一 e01 tmp child；只依原 e01 frozen policy exact CREATE_ONCE directory rule、原 dependency prep policy/observation/receipt hash chain與 current lstat empty-directory readback 對帳。原 e01 dependency receipt 並無 directory inode ref，故其歷史 inode/ref 為 UNKNOWN；不可補造、歸給 e02 或擴大 e01 scratch 規則。

目前 pip-cache lstat/type/mode/owner/inode 與空目錄內容另以 `evidence/e01-pip-cache-current-readback-01.json` 和專屬 receipt CREATE_ONCE 固定，僅代表本輪目前 readback，不回填歷史 identity。兩次 B01 scan 與 B02 會逐欄核對此本輪 readback，並再次驗證 frozen E01 policy、dependency input manifest、install observation `TMPDIR`、exit 0 與原 receipt 的 artifact refs。

## E01 兩個歷史來源 bytes 的唯讀恢復

E01 source freeze 有兩個來源檔雜湊無法由目前 R draft 直接驗證：`tools/prepare_dependencies.py` 與 `tools/prepare_epoch.py`。root 只讀核對使用者明確提供的 session transcript，並恢復出與 E01 source freeze 完全相同的原始 bytes；這不授權回寫舊路徑，也不改變 E01 結果或歷史 metadata。核對來源為本文件所指的 user-input annex 及其 receipt；精確 transcript 行範圍、抽取方法、bytes/hash、目前舊路徑 drift 與未知歷史 metadata 由 `evidence/historical-source-recovery-01/recovery-manifest.json` 記錄，另有獨立 exclusive/readback receipt。

恢復的兩個來源只以 exact CREATE_ONCE archive 留在上述新目錄；不執行舊工具、不復原舊 R 路徑、不補造 inode/time/creator。e02 evidence source closure pin 恢復檔、manifest、receipt 與 recovery producer；B01/B02 必須再讀取並核對兩個恢復檔與原 E01 source hashes、完整 recovery receipt chain。任一不符都阻擋。E01 原有兩個 PASS 與 B01 FAIL 保持原樣；恢復內容本身不構成任何 gate PASS。

## Mutable collaboration record

`R/代理協作開發紀錄.md` 由 `collaboration_recorder` 持有，其初始已知讀回為 9,214 bytes、SHA-256 `faff5c6a9cc0b7e7cbfbaa002da6cbfb02d9190df97ac4426e56810b1d76bb9b`。本實作者不改該檔。e02 executable source closure 不 hash live mutable log；另在 R 建立 exact immutable snapshot 與獨立 receipt，記錄來源精確 path/producer/初始 bytes/hash/readback。source freeze 只 pin snapshot/receipt。後續 recorder append 依 exact collaboration_recorder REPORT rule 發生，最新 live log hash 由正式 report manifest/tail capture，不回寫 freeze。

## 固定 families、D01 與 production outputs

保留既核准的 e02 evidence/production 雙 family 和固定 check-ID mapping；不重寫、不搬移、不重跑 e01 IDs。e02 evidence source freeze 不收尚未完成的 product source。政策在 B01 前預先登記 D01 host spec/claim/registration/raw outputs，以及未來 D01 `tools/prepare_d01.py`、`tools/run_d01.py` 的 exact draft source paths；這兩個 producer 必須在 D01 前真實完成並各自讀回，其 late D01 spec freeze 綁定實際 bytes/hash，不能以不存在來源先作 PASS。D01 仍是 genuine CUA host operation，不包成 CLI/mock，也不做任何 Save All。

同一政策預先登記 plan 中六個 live modules（`host_io.mjs`、`live_analyzer.mjs`、`live_classifier.mjs`、`live_runner.mjs`、`live_entry.mjs`、`chooser_locators.mjs`）、`checks/validate_real_frame.py`、runtime-binding/grants/authorization/waiver/attempt-extension、固定 executable/decoder refs、N/P/S product checks、fixture/build/module-cache exact paths、check outputs 和 report tail outputs。`tools/prepare_production_family.py` 是獨立 late production-family DRAFT producer；production sources 完成後、第一個 production check 前才 CREATE_ONCE freeze，不能覆寫 evidence family freeze 或事後擴展 policy。Swift 五 literal paths 仍保留給 implementation_feasibility，交接前本實作者不可改；所有產品 edits 延至 D01 後，無 stubs。

正式 materialization 前須先完成不消耗 ID 的實際 namespace/policy/readback reconciliation。正式 e02 E01、E02、B01 各最多一次；只有 pair、anchor、所有已知 bootstrap delta、Git/protected preimages、source annex readback 與 tail audit 全部 PASS 才能向 D01 前進。若出現未解 delta 或 drift，保留證據並停止。兩個 B01 scans 期間停止所有工作區寫入。
