# Planner 修訂報告：B1 與每帳本一次轉接

## 本角色結論

`PLAN_DRAFT_COMPLETE`。Owner 在獨立 Plan Review 的 REVISION_REQUIRED 後另啟動 Planner，並選定「這版只處理第一次變號」。已修訂 plan／handoff 為草案 v2，收斂為每帳本一次轉接，補齊 replay 與第二次漂移拒絕的驗證規格。首版產品 schema 仍為 v1。

本輪沒有產品實作、獨立 Plan Review 或 acceptance。B1 是已回應但待獨立重審的 finding；原備份仍阻塞，不能稱修復、核准或 DONE。

## 精確基準與來源

| 項目 | 當次直接核對 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`；目前主 worktree，其他 worktree 只列出 |
| 分支／起始 HEAD | `feature/line-notes-media`／`0edf5cff88bb605b5c4608990ea6924c0d424e75` |
| 起始工作樹 | `git status --short`、`--porcelain=v1` 無輸出 |
| 環境 | Darwin 27.2.0 arm64；Python 3.9.6；Node v24.22.1 |
| v1 plan SHA-256 | `661a9f680f527fb52e50f3ed009b952e104879c177b110074833bffc5e8c6a27` |
| v1 handoff SHA-256 | `99ad7111bea2430b600b76b896e5fee5f5e78fe45746f21a96a30abe4cc62186` |
| 獨立 review SHA-256 | `d2f2ec70957004cffcab7d3ca0c649bc3bc30e8c16ba4457a2cd7bdc5babb471` |
| Simplicity Review SHA-256 | `4617b42c24bb13b77fd61844e7dfaab7743af3766811fb453aeb2325d2179872` |
| notes.py SHA-256 | `80d0ab5b61b27eee4b5ee9727eef6176ba5a489365ae1651e27f0295fc1170b0` |
| 私有證據 | `.local/line-backup/tasks/notes-volume-plan-20261108/planner-revision-b1/`；交付 receipt 與 hashes 不進公開 Git |

依 Owner 指定 01_plan_prompt、AGENTS.md、全域同版本 workflow-routing／subagent-model-policy 及中文 templates 工作。repo 的 policies 路徑不存在，初讀 exit 1，改讀 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 同版本文件，不恢復退役 Harness。原 plan／handoff、兩份 review、診斷、提報與 progress 已核對；較長輸出裁切後以小行段重讀關鍵規則。相簿 Skill 只核對隔離邊界；記事本 Skill 作為規劃限制來源，不執行日常流程。

## B1 到草案 v2 的映射

| finding／需求 | 修訂與驗證責任 |
|---|---|
| 原 before=device D0，前次 binding=device D1；第二次無法同時相等 | 取消連續轉接承諾；每帳本歷史只能有一筆，old ref 只可指 created／destination，before 仍取原事件 |
| 換 session／batch／destination 可能被誤當額度重置 | 限額定義為整份帳本，preview／confirm／graph 一致；T3／T11 要求拒絕第二筆 |
| 一次限制可能阻止 confirm crash 查回 | 精確 replay 先查，通過完整性與 current session 後查回原 data；不要求原 tip 仍是當前 tip，不新增事件／evidence |
| 原結果查回可能誤稱第二次漂移已解 | 原精確 replay 另驗當前 guard，漂移回 CURRENT_BINDING_CHANGED 與原 ref；新 preview／confirm 回 UNSUPPORTED_STATE |
| 缺第二次變號覆蓋 | T11 明列 D0→D1→D2、第二次在 v3 前、未漂移 replay、不同 evidence、換 session／destination／batch、進 v3 後拒絕及零副作用；T10 需獨立映射 T11 |
| fresh scan／UNKNOWN／availability 保護 | 保留 scan START 晚於唯一轉接；completion、staging、candidate 與 availability guard 不變，既有 OPEN_BATCH 與 UNKNOWN 不改 |
| 舊審查版本漂移 | 兩份舊 review 原樣保留，v1 PASS 不涵蓋 v2；Owner 決定 Simplicity 重查，必須另啟動 CRITICAL 獨立 Plan Review |

沒有引入最新 witness 鏈、額外持久欄位、新 event kind 以外的框架或新日常步驟。能力收斂由 Owner 選定，不是 Planner 擅自替 Owner 決定。

## 事實、推論、未知與未執行

事實：B1 是 v1 設計的邏輯矛盾；現行 notes.py 的 list gate 與 completion availability 直接比較原事件 device。本輪只讀相關程式行段，沒有重跑真實拒絕或重新取真實 witness。Owner 明示選一次轉接，精確原話在私有 decision 記錄。

推論：禁止第二筆可避免 D1 binding 與 D0 原 witness 在第二次轉接時比較，並維持 list-only 首版範圍；這是待審設計推論，不能代替獨立接受或產品測試。

未知：remount 真因、同一持久物件／clone、舊 UNKNOWN 晚到、真實完整布局、後續 gate、受控 volume、LINE／跨 Session 實際可用性。沒有新增人眼 GUI 觀察可標 OBSERVED。

產品回歸、合成產品交易、新增 CLI、T1–T11、媒體解碼、真實帳本 reattest、受控 volume、LINE、下載、跨 Session 與獨立 acceptance 全部 NOT_RUN。這輪文件檢查不建立這些 PASS。

## 實際命令與文件檢查

工作目錄是 repo 根目錄。以下是本角色核對；後續 Git 交付與 helper 實際結果另記私有 receipt，避免預填。

| 命令／檢查 | Exit／結果 |
|---|---|
| pwd、git rev-parse --show-toplevel／HEAD、git branch --show-current、git remote -v、git worktree list、git status --short／--porcelain=v1 | 各 0；核對基準與乾淨起始狀態，不修改其他 worktree |
| cat／sed／nl／rg 讀取角色、policies、templates、計畫、review、診斷與 notes.py 相關段落 | 除缺 repo policies 的已列 exit 1 外，主要讀取 exit 0；不以截斷輸出宣稱全部已見 |
| uname -srm、/usr/bin/python3 --version、node --version、test -f HTML renderer | 各 0；使用現有工具，不安裝或改設定 |
| shasum -a 256 | 0；起始來源 hashes 如上；候選 hashes 見私有 artifact-hashes.txt |
| 私有 check-documents.py、git diff --check、git diff --exit-code 基準 -- 受保護路徑 | 0；文件 scope／六狀態／B1 規則／來源不變核對通過，詳 document-checks.log；不是產品測試 |

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DOCUMENT_CHECKS_ONLY; PRODUCT_AND_REAL_ENVIRONMENT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_REVIEW_OF_V2
```

## 人工交接

下一步由 Owner 決定適用的 Simplicity 重查，並另開 CRITICAL 獨立 Plan Review 主 Session。攜帶精確交付 commit／diff、plan v2、handoff、本報告及 v1 review 與診斷。未經必要審查與核准，不進實作；再次漂移支援需要另提能力範圍，不在本版暗增。

Owner 指定一位 GPT-6-luna helper 在草案完成後梳理詳細提交訊息；helper 不是獨立 reviewer，參與與模型四層證據以私有 commit-helper.md 為準。dispatch 若失敗，主 Session 可接手相同已授權訊息整理，不換模型或 CLI／API 繞路。
