# 記事本中斷後重下與確認取代：獨立 Plan Review

## 本角色結論

**PASS（計畫審查）。** 此版有明確的需求與授權來源，範圍及資料風險有界，成功條件具可行的負責者、命令或觀察及證據來源；未發現計畫阻塞。這不是產品接受、實作授權、任何真實批次的重下同意，也不表示原列表已恢復。

新版不再要求先證明舊下載停止：以明示批次確認接受重複傳輸，保留舊 UNKNOWN／原件，將新下載複製成獨立檔案，完整驗證後才啟用。舊計畫的 PR-B01 沒有取得新停止證據；本 PASS 是審查新的恢復前提，並非將舊 BLOCKED 改判。當次 CUA 通道或前景無法可靠操作時仍須停止，沒有保證所有失聯情境都能自動恢復。

**人工下一步：** Owner 在實作前採納或調整計畫的三項預設，再決定是否另開主 Session 授權 Implementer S1。三項是受影響貼文全媒體批次、新實體路徑成為目前結果並保留舊檔、同批確認涵蓋完成前再次中斷。若實質調整方案，由 Owner 決定適用的重審；本角色不改 plan、不開始實作或後續角色。

## 請求、精確版本與獨立性

| 項目 | 本輪綁定 |
|---|---|
| 角色來源 | Owner 指定 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/02_plan_review_prompt.md`，並交付上一輪簡潔性報告與提交 |
| 使用者需求 | [Owner 意圖及重規劃要求](../20261107-notes-interruption-replan/plan-review-owner-intent.md)：自動找回、可重新下載、取代前確認、再次中斷可續、流程簡單 |
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup` |
| 分支 | `feature/line-notes-media` |
| 本輪入口 HEAD／查得遠端 HEAD | `2292aecc706105116ca4bd1745bb208e74cb3126` |
| 受審 plan／handoff 共同提交 | `c3c8827cea817db633736d9f8303c43f454fa7cd`；與入口 HEAD 及工作檔逐 bytes 相同 |
| plan SHA-256 | `86e89b5a62d12ea64fb6e75a31d394ea9fba1413677a951055d2b4114914c391` |
| handoff SHA-256 | `b444bb7c79323631e9df60b07efcaf0724e9880502e22b2f5f40e63263e02ca1` |
| 簡潔性關卡 | [simplicity-plan-review.md](simplicity-plan-review.md) 位於入口提交；其 PASS 僅限簡潔性，本輪另作完整計畫判讀 |
| 初始 Git 狀態 | index、tracked dirty、untracked 均空；其他 worktree 與忽略資料保留，未 reset／clean |
| 獨立性 | 本主 Session 未撰寫或實質參與受審計畫及其決策；僅作本次唯讀評估與報告。這是 Session 工作紀錄陳述，不是平台隔離或後端身分證明 |

行號以下均指受審共同提交中的 [plan.md](plan.md)。本輪也讀取 [handoff.md](handoff.md)、Planner 報告、舊 Plan Review 與去識別根因分析；未重讀私人帳本、媒體或原始 GUI 資產，沒有將歷史報告中的查核結果變成本輪 PASS。

同角色 native helper `plan_source_feasibility` 唯讀映射源碼／測試，未參與受審設計，未給正式接受；判定由主 Reviewer 整合負責。Owner 指定的 `gpt-6-luna` 提交訊息助手只在報告完成後梳理上下文，不參與正式判定。兩者都不是下一個正式角色。

## 目標、非目標與約束映射

| 需求／約束 | 計畫位置 | 審查判讀及來源 |
|---|---|---|
| 同一日常 Prompt 自動找回，不要求內部 key 或開發文件 | L95–98、162、175–177 | 擴充 lists／memory 與唯一下一步，操作知識回到 Skill／references／手冊。現 Skill 的日常責任及手冊第 5 節支持此入口；日常成果不可只靠本計畫才能重現 |
| 重新下載前明確確認「所有」的範圍 | L73–87、104–106 | 明列需要重新開始的受影響貼文及其全部可備份媒體，包含 completed sibling；不默縮單檔或擴整庫。拒絕、沉默、啟動 Prompt、一般繼續不作批次同意 |
| 同意可跨 Session，變更不得沿用 | L87、98、105、110、133 | 確認綁 scope digest、event refs、版本、路徑策略與回覆；重入讀回，新觀察另立引用；來源／身分／策略改變重做確認。expected tip 加持鎖重算限制合作 CLI 的並行變更 |
| UNKNOWN 可恢復且保留真實歷史 | L106–112、133、144 | 新確認關聯只讓舊 attempt 退出本批候選，不偽造 STOPPED／NOT_SENT。現 writer `notes.py:2677` 與 graph `:1604` 都需同步調整；計畫已涵蓋，不能只鬆 writer |
| 舊完成、LOCAL_CHANGED 與未涵蓋異常 | L73–75、112、123–125 | 同篇完整恢復有明示範圍；舊完成不改，scope 外 LOCAL_CHANGED 仍擋，scope 內只安全引用舊路徑。純 LOCAL_MISSING、排除及受保護不因批次解除；缺項不假稱全完成 |
| 新結果不被舊下載晚到寫入污染 | L116–120、146–148 | 每 attempt 新 raw，candidate 從不交給 LINE，獨立 bytes copy／inode，來源前後核對。`notes.py:3492–3521` 現 hard link 發布不能直接沿用；`media_verify.py:252–281` 的 exclusive copy 可重用但不是持久發布已存在 |
| 驗證後取代、再次中斷仍能判讀 | L118–140 | 先持久計畫、candidate 自身驗證、一筆 activation 選目前版本；回覆遺失讀 chain，不重送或猜認半檔。啟用前舊版仍是目前結果，已驗新檔可留存續做 |
| scan／bind／pending 不成為繞過路徑 | L96–98、112、156 | 保留中斷盤點；新 scan 只做恢復評估，不改舊 attempt 的 scan，也不解下載 gate。現 `notes.py:1822`、`:1991`、`:2155` 的直接依賴已列入白名單及 C06 |
| 外部 GUI／writer 保證有界 | L142–152、210、220 | 不以重啟 App、等待或取消 chooser 證明停止；未返回輸入不並行新輸入，通道失效／歸屬不明即停。鎖不代表 LINE、GUI 或外部程序隔離，不承諾 exactly-once 或來源原子快照 |
| 不擴相簿／資料／歷史範圍 | L15、25–42、125、156 | 產品白名單必要且有上限；不改 daily／共用帳本層／Swift、真實資料或舊方案，不刪清理／搬舊檔、不 merge master。新事件不授權退版寫入，不改舊 bytes |

這些是可審閱的設計預設，不是 Owner 已同意某一批真實資料。計畫採納、S1 開發、當次日常前景及批次確認各有不同作用；本輪只獲審查與成果 Git 交付授權。

## 風險、最小性與人工關卡

**CRITICAL 合理。** UNKNOWN 重新開始、同篇已完成媒體重下、LOCAL_CHANGED 例外與目前版本投影均涉及資料／授權或相容性，不能當作文件小修。計畫保留人工啟動的計畫 Simplicity Review、獨立 Plan Review、首切片 Simplicity Review 及最終獨立接受，符合全域同版工作路由；本輪不建立退役 controller，也不讓 helper 代簽正式關卡。

L60–67 已比較文件限定、直接覆寫、舊路徑搬開再放回與獨立版本。獨立 copy 消除與 raw 共用 inode 的直接風險；單筆 activation 減少多目錄切換與另一 current 檔的協調。空間增加與未採用檔保留是明示成本，磁碟不足停止，不以自動清理補救。沒有證據顯示必須擴成通用交易框架、背景服務或資料遷移。

源碼與測試的直接依賴均在允許路徑內。S1 是離線垂直路徑，不能提前當日常可用；S2 另由 Owner 交辦，才將新例外整合回 AGENTS／Skill／手冊，避免產品可用性依賴開發文件。實作需超出白名單、原地覆寫或更改驗證標準時，既定停止／人工決定保留。

## 成功條件、負責者與驗證可操作性

以下是對未來檢查設計的評估，不是它們的執行結果。實作／實機證據都須綁定當次完整候選 SHA；本輪 plan hashes 不冒充未來產品身分。

| 檢查 | 負責者／精確候選與方法 | 本輪判讀 |
|---|---|---|
| P1–P3 | Planner、Owner 啟動的 Simplicity Reviewer、獨立 Plan Reviewer；共同提交、hashes、各角色報告 | 來源齊全；P2 既有 PASS 範圍保留，P3 由本報告判定，不代替後續產品接受 |
| V1／S1 | Implementer；候選 SHA＋兩篇隔離合成 fixture，未確認拒絕→確認→candidate→activation→新物件重開，前後 manifest／hash | 可執行。現 `test_notes_records.py:49–105` 有隔離帳本、patched active hint、可注入 verifier；`:195`、`:282`、`:347` 有生命週期、UNKNOWN 與發布中斷基礎 |
| V2／C01–C12 | Implementer；新 `test_notes_restart.py` 及既有 records／regressions，保存命令、exit、故障位置與重開結果 | 可用 mock 注入 copy／fsync／append 邊界、保留舊 fd 寫入、重開物件比對事件 bytes。矩陣涵蓋確認／scope、scan、舊 pending、copy／啟用、相容性、4／70；全部仍是必需，切片不豁免 |
| 真實合成媒體解碼 | Implementer S1；候選 SHA、實際 decoder binary／來源、固定 ffmpeg／ffprobe、命令及結果 | 已有 `test_notes_media_verify.py:29` 合成 PNG、`:42–66` 建置既有 decoder、`:216–245` 影片 fixture 基礎。本輪只核對工具存在及 binary hashes，未編譯／解碼；S1 不能用 mock 或被 skip 的測試充作此證據 |
| V3 | Owner 另開首切片 Simplicity Reviewer；S1 精確 SHA、V1／當時已完成 V2 | 有明確輸入、負責者及停止點；未解阻塞交 Owner，不跨角色自修 |
| V4／最小回歸 | Implementer 最終候選；L205–207 三條命令、help／文件對照、日常入口及相簿相容性 | 命令具體可行；exit 70、範圍外差異或必要測試缺項須如實保留。產品未改，本輪不為審查重跑回歸 |
| G1–G2 | Owner 日常任務 Agent；Owner 指定且允許重下的測試列表、有效前景／批次確認、同正式 Prompt、跨 Session 原件、檔案驗證與啟用 | 場景與證據責任可操作，不要求先在本次 Review 下載。以允許的暫停／交接產生中斷，不強退／斷網／破壞資料；未實測窗口維持 NOT_RUN |
| A1／三層成功 | Owner 另開獨立接受者，映射精確候選 V1–V4／G1–G2；原列表套用另有當次日常授權及精確確認 | 離線機制、指定環境恢復、原列表實際完成分報。測試列表成功不完成原列表；獨立接受不能由實作者或其 helper 簽發 |

新測試命令為 `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py`。現有最小回歸三命令及 S1／S2 分界位於 plan L196–208；未來記錄須包含失敗／跳過，不只保留最終 exit 0。

## 阻塞與非阻塞建議

**阻塞：無。** 沒有因尚未完成未來實作／GUI 驗收而拒絕計畫，也沒有把源碼判讀當成恢復能力已證明。

以下建議均落在既有相容性與矩陣內，不新增 gate 或擴張功能：

| ID | 計畫／源碼位置 | 實作時應保留的核對 |
|---|---|---|
| PR-N01 | L110、123、156、C11；`notes.py:1635`、`:1668`、`:1761` | 舊 verification／publish／completion 目前與全帳本 latest attempt 比較。S1／C11 要有「舊 verification＋completion 已存在，再追加 restart attempt，重開仍可重放完整歷史」；只測從未驗證過的 UNKNOWN 不足 |
| PR-N02 | L98、110、C05–C07；`notes.py:2155–2184` | 新 Session 的來源核對另立引用，writer 與 replay 一起驗；不能只放寬 verify 或重標原 scan。計畫已明定此契約 |
| PR-N03 | L29、117、156、C11；`notes.py:3269–3320` | 新版本啟用後，同篇後續一般新增媒體的目的地與編號仍須相容；現程式只讀直接子目錄與舊 completion／publish-plan，不能只改摘要投影 |
| PR-N04 | L158、196、V4；`test_notes_media_verify.py:42–66`、`:216–245` | 既有工具不可用時可 SkipTest；測試程序 exit 0 不代表必要真實解碼已跑。報告分列 skips，實際解碼缺項仍 NOT_RUN，遵循 S1 原要求 |

沒有以文風、檔案數或測試數單獨構成的拒絕，也沒有要求為建議另開新操作命令。

## 實際檢查、事實、推論與未知

本輪在 repo 根目錄，以 macOS 27.2／26B123、Python 3.9.6、Node v24.22.1 作唯讀核對。原始命令／環境、29 份來源 manifest、來源助手摘要、進度、文件檢查及後續交付證據保存在私有任務區 `.local/line-backup/tasks/20261107-notes-restart-overwrite-plan-review/`；公開成果僅本報告，不提交真實帳本或私人媒體。

| 實際命令／查核 | 結果／退出碼及證明範圍 |
|---|---|
| `git rev-parse --show-toplevel`、`git branch --show-current`、`git rev-parse HEAD` | PASS／0；repo、branch、入口候選 |
| `git status --porcelain=v1 --untracked-files=all`、`git worktree list --porcelain` | PASS／0；初始乾淨；其他 worktree 保留，不證明 OS 隔離 |
| `git ls-remote origin refs/heads/feature/line-notes-media` | PASS／0；當次遠端與入口 HEAD 相同，非未來 writer 排除保證 |
| `git log -1 --format=%H -- <plan>`、逐來源 `git show`／`git rev-parse <SHA>:<path>` | PASS／0；24 份 repo 來源與入口 bytes 一致，plan／handoff 另與共同提交一致；加上 5 份全域角色／政策／模板／Skill 的 hashes 共 29 份。這是版本核對，不表示逐行全面稽核每一來源 |
| `/usr/bin/python3 -B .local/line-backup/tasks/20261107-notes-restart-overwrite-plan-review/check_review.py snapshot` | PASS／0；保存上述來源與 11 項 Git／環境命令原件。只讀核對固定 ffmpeg／ffprobe binary SHA-256 均匹配現程式 pins；既有 SDK 存在及 `xcrun --find swiftc` 成功不證明編譯／解碼通過 |
| `cat`、`rg -n`、`sed -n`、`nl -ba` 與同角色來源核對 | 完成／0；需求、plan／handoff、政策與相關源碼／測試映射。廣泛搜尋輸出曾截短，關鍵引用另用精確行段核對；一次 exec 在 dispatch 前中止，沒有 shell 結果，不列為修復 attempt |
| 同腳本 `check`、`git diff --check` | PASS／0；來源 hashes 不變、報告 UTF-8／相對連結／六狀態／空白及只新增本報告。實際結果見私有 `document-checks.json`，只驗文件交付 |
| 產品最小回歸、V1–V4、C01–C12、編譯／解碼、真實 LINE／CUA、原帳本／媒體、G1–G2、Owner 試用及 A1 | **NOT_RUN**；本輪無實作或真實任務／前景授權，未執行這些檢查 |

- **事實：** 源碼存在 recovery graph、scan、completion 與 hard link 發布的直接依賴；計畫已明列同步修改及驗證。版本／文件查核不改這些產品行為。
- **推論：** 在 Owner 明確接受重複傳輸及新實體路徑的前提下，獨立副本與單筆啟用可支持有界恢復，不必先取得舊下載終態；此推論仍待實作與實機證據。
- **未知：** 新 schema／graph／投影／copy 的實際正確性、當次 chooser／晚到輸入、LOCAL_CHANGED 成因、來源可用性、空間需求及實機跨 Session 表現。沒有本輪 GUI `OBSERVED`，不核對或宣稱外部副本已驗證。
- 原根因歷史嘗試不重設，本輪沒有下載、reconcile 或產品修復 attempt；同根因最多三次及兩次無新資訊停止仍適用。

四層模型證據分開：配置預設未用於判定；來源助手 dispatch 未提供 model／effort override，僅能證明呼叫請求；提交助手依 Owner 明示選擇請求 `gpt-6-luna`。實際平台顯示只按工具回傳保存，無顯示則 UNKNOWN；沒有 provider-reported usage 原件，後端身分、token 成本與節省均 UNKNOWN。

## 六項狀態與人工交接

```text
PRIMARY_OUTCOME_STATUS: PLAN_REVIEW_PASS
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

PRIMARY 僅代表本次獨立計畫判定；REQUIRED 指產品／行為／實機必要驗證，INDEPENDENT 指最終產品接受。文件與來源檢查已通過，原備份及新版機制尚未實作／驗證，不能標整體 DONE。

Owner 的下一個具體步驟是採納或調整上述三項預設，再攜受審共同提交的 plan／handoff、需求澄清、計畫簡潔性報告及本報告，另開主 Session 決定是否授權 S1。若採納原版，S1 按 L158–160 的離線垂直路徑及 V1／指定 C 項交付；首切片完成後回到 Owner 啟動下一關卡。本 Reviewer 完成報告及已授權 add／commit／push 即停止，不自動啟動實作、跨角色修補、重測或結案。
