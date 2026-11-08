# 記事本重新見證 S1：實作簡潔性審查

## 本角色結論

**PASS，僅限 S1 實作簡潔性。** 受審差異沒有具體、重大、可避免而違反核准最小範圍的複雜機制。完整 witness、有限布局、既有鎖與狀態拒絕均有需求依據；沒有提前加入 S2 可寫協議。這不是功能接受、完整 T1／T2 通過或備份解除阻塞。

另有一項已證實的證據範圍落差 E1：實作報告稱快照含 active-hint fixture，但測試實際只比較 case 子樹，且將寫 hint 函式替換為 no-op。此問題不構成本角色「不必要複雜度」的判退條件，亦不能因簡潔性 PASS 而視為已解。後續功能核對必須保留此待確認事項。

## 檢查點、精確版本與獨立性

| 項目 | 綁定 |
|---|---|
| 正式角色／檢查點 | Owner 另開主 Session 啟動 Simplicity Reviewer（Implementation），S1 首個可驗證切片 |
| 目標 | 第一次 list directory device-only 漂移的受控恢復；本切片只建立唯讀預覽，不解除 binding gate |
| Repo／分支 | `/Users/hsiaojohnny/dev/Line_backup`／`feature/line-notes-media` |
| 起始 HEAD／受審候選 | `d7e8cfe81109ee6e3b8cb776d92b5d1be16b5a98` |
| 候選 parent／tree | `52fef4ab95c5843db4793c9dd5ebab5552bfb60e`／`f8d80060675b00d3bc307405c87efb943449bc36` |
| 精確差異 | 上述 parent → candidate；五份檔案：notes.py、兩份測試、implementation.md、原任務 progress.md |
| 核准來源 | `../20261108-notes-volume-identity-reattest/plan.md` v2、原 handoff、兩份 v2 review，以及本目錄 S1 handoff |
| 授權效力 | S1 handoff 保存 Owner 核准及 clone 剩餘風險接受；不把原計畫的歷史待核准字樣當成缺授權 |
| 起始工作樹 | 無 tracked dirty；既有未追蹤 Session Markdown 未讀、未修改、未 stage；其他 worktree 未整理 |
| 遠端 | 本輪 `git ls-remote` 精確回傳候選 HEAD，與本地相同 |
| 獨立性 | 本主 Session 未參與受審實作／計畫；本輪只寫審查及進度文件、私有證據，不修改產品或測試。不主張 OS／平台隔離 |
| 同角色助手 | 一位繼承主 Session 的唯讀助手整理測試對應與證據界線，未提供正式接受；主代理逐項核對來源並作成判定 |

本報告只涵蓋上述候選。審查文件的後續提交不改變受審產品身分；不同產品候選不自動沿用本 PASS。

### SHA-256

下列工作樹 bytes 均與受審候選 blob 相同；九份來源的完整核對在私有 `source-and-version-checks.json`。

| 路徑／來源 | SHA-256 |
|---|---|
| 核准 plan v2 | `937e86eb276ed025c41617d7a5fafc6c80259ea7bc0314e31fa5fc84eb3a858b` |
| 原 handoff | `a6bd06190ca677363ecb2e08847d9863d5daf99c24bb79135f3a8ae9752d71e8` |
| 獨立 Plan Review v2 | `aa97bfe28f113123331ed3a4eb05724db6ba876f487d71fb8cfebe81ba3eba21` |
| 計畫 Simplicity Review v2 | `3e09bc50544d535f1979e10086eef3092d24e53153e2fffeb85e15107a4d6f01` |
| 本目錄 S1 handoff | `5a71c958d1f00679feaf96c4e57f1fdc32cfe5f8a1a0dd4daa789f5d8769d4a0` |
| implementation.md | `a775f0aa10bee5e60c90b0b2c91762a3b3f1925a6dd316358f173bdc2ac51056` |
| src/line_backup_batch/notes.py | `aba23ed65f5e0bdd7a19095e506a54d53a87eed5d23a769dcac39677282c65eb` |
| tests/test_notes_reattest.py | `355f9c9e006b70443b303dded74262914fda4a5755b2df18b8f9ea21d35a4416` |
| tests/test_notes_locks.py | `1494a9a3c2f839900d7a5fcb99b78d11c4c5c92f590da85304849c1ae457c151` |

## 機制對應需求與成本

下列 notes.py 行號綁定受審候選；計畫行號取核准 v2。

| 新增機制／位置 | 必要需求、既有原語與成本判讀 |
|---|---|
| NotesReattestError、reattest_need；notes.py:78、:98、:6799 | plan:109–111 要求 reason、差異分類與事件引用。局部錯誤載體避免以字串混入私人細節，沒有第二套通用錯誤框架；其他命令仍走既有 handler |
| 路徑與目錄 wrapper；:2215–2261 | plan:53 要 canonical、專案內、path／inode 不變。沿用 directory_info；wrapper 只附 reattest 分類，不改通用 guard，也沒有略過原 st_dev |
| OPEN_BATCH／不支援狀態；:2263–2302 | plan:51–52、:57–58 限唯一未 activation 批次，拒絕 v3／candidate／pending naming。沿用 _restart_open_confirmation 與 _pending_publish_plans，沒有新 batch 狀態機 |
| scope／availability 核對；:2304–2334 | plan:57 要 scope 外未解與 LOCAL_CHANGED 拒絕，scope 內 UNKNOWN 保留可觀測。重用既有投影而非重定義完成或結果；沒有因空 staging 推定 STOPPED |
| bounded witness 收集；:2336–2448 | plan:54–56、:82–90 要所有合格 completion、已登錄 staging、單一 device mapping。完成而缺席 staging 與未解空 staging 是兩種既定狀態，不能合併成「不存在就略過」 |
| list 與 completion 名稱集合；:2450–2543 | plan:55–56 要精確聯集與未知子項拒絕。分別檢查 list 和貼文目錄，避免只查一層或依 staging 前綴認領；未增加通用布局支援 |
| 檔案 witness 與有界重查；:2545–2627 | plan:55、:90、:138–140 要 metadata／SHA-256、regular／nlink=1／無 symlink 與可見漂移拒絕。沿用 _read_regular 的 no-follow、fd 前後 stat 與 path 身分核對，沒有新增 reader、背景 watcher 或無限重讀 |
| 唯讀協調、排序、digest、NO_CHANGE；:2629–2676 | plan:82–87、:96、:101 要鎖內驗帳／session、固定結構與穩定 digest。沿用 locked、encoded、digest；NO_CHANGE 使用空 witness。沒有保存 evidence／事件、建媒體目錄、更新 hint 或新增可寫 confirm |
| CLI 與 lock 分類；:6471–6479、:6779–6820 | plan:67、:96、:107 要新 preview 命令與 read-only lock busy 分類；只接一個子命令及原錯誤邊界，沒有新的授權入口或鎖 |
| 合成 fixture；test_notes_reattest.py:57–293 | plan:165、T1 要合法 completion＋UNKNOWN＋restart confirmation＋device drift。以既有 API 建立帳本，再改合成舊 device 並重算鏈，避免真實 volume／資料；不是新產品框架 |
| 13 tests 與 lock 既有案例延伸；:338–577、test_notes_locks.py:192–200 | 對應 T1／T2、必填與 lock；各負例有具體 safeguard。沒有因測試加入新 kind 或提前寫 S2；不以行數或案例數量單獨判多餘 |

完整 witness 與舊 availability 的核對有部分重疊，但目的不同：前者容許精確 device-only 映射，後者辨識 scope 外既有異常。直接移除其中之一會失去核准防護；本輪未找到保留全部邊界的必要簡化。所有新增機制均有對應需求，無 speculative 通用化、控制器、連續 witness 鏈或新服務。

## 阻塞 finding、證據落差與非阻塞事項

**簡潔性阻塞 finding：無。** 未要求改計畫、降低 gate 或新增產品能力。以下是保留給後續功能與證據核對的事項，不等同功能 PASS。

### E1：active hint 的純讀證據描述超過測試範圍

- 需求：S1 handoff「T1 純讀／事故形狀」與 plan T1 要 events／evidence／active hint／媒體樹前後不變。
- 來源：implementation.md:42 宣稱比較含 active-hint fixture；私有 checks.md 也列該樹形。
- 實際測試：test_notes_reattest.py:25–33 將 hint 與 evidence-packs 建在 self.base；:60 建 self.base/case-*；:330／336、:340／380、:384／390、:570／577 只 snapshot ledger['case']。case 中有 records/events、已保存的 ledger evidence 與 photos；case 外 hint 和 evidence-packs 沒被比較。
- 同時 :35–38 將 _write_active_hint 替換為 no-op，且沒有對呼叫作 assert_not_called。因此即使誤呼叫該函式，這些快照也不能偵測。
- 影響：保留原 logs 的 13 tests OK 事實，但不能推得 active hint 的必要純讀證據完整，也不能稱所有 T1 要求已通過。靜態閱讀未見新 preview 寫入 hint，這是來源判讀，不能替代相應動態證據。
- 最小方向：由 Owner 決定後續同範圍實作／驗證交接，將合成 hint 納入真實可觀察的比較或寫入呼叫斷言，並修正證據敘述。不要求接觸真實 active hint、增加產品功能或在本 Reviewer 內修復／重測。原實作報告與 logs 保留原樣，本報告記錄更正界線。

### E2：成功 witness 的覆蓋界線

成功案例僅斷言一份 completion 與兩份 staging（:354–359），不能單獨證明多 completion／同目錄多檔的完整聯集與排序。產品碼有分組、聯集、逐項核對與排序；未見已證實漏收。hash／size 負例同時可能改時間屬性，不能由其 PASS 證明每一欄檢查獨立有效。這些是覆蓋界線，後續按核准 T1／T2 評估，不在本輪擴充測試。

無另列純風格或行數縮減建議。尤其不建議刪除必要名稱集合、逐檔 witness、scope／session／lock 檢查以換取較短程式。

## 實際檢查、事實與未執行

本輪工作目錄為 repo 根；當次環境為 Darwin 27.2.0 arm64、/usr/bin/python3 3.9.6、Node v24.22.1。repo 無同版本 policies，依 S1 handoff 指定讀取全域 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 的 workflow-routing 與 subagent-model-policy，以及 role-report.template；沒有恢復退役 Harness。

| 本輪實際命令／動作 | 結果 |
|---|---|
| pwd、git status --short、git rev-parse --show-toplevel／HEAD、git branch --show-current、git worktree list --porcelain、git remote -v | 各所在工具命令 exit 0；核對 root、候選及既有 untracked，未修改其他 worktree |
| git show 候選 metadata／本體、git diff parent candidate（完整 diff 另存）、git ls-remote origin refs/heads/feature/line-notes-media | exit 0；確認 parent、tree、差異與精確遠端 HEAD |
| git diff --check d7e8cfe^ d7e8cfe | exit 0；僅差異格式核對 |
| 私有 Python 來源與版本核對腳本 | exit 0；九份來源 matches_candidate=true；前四份核准來源 hashes 與交接一致；每條子命令 exit 保存於 JSON |
| cat／nl／sed／rg 閱讀 Prompt、policies、template、plan、handoff、既有 reviews、實作、程式與測試、歷史 logs | 成功讀取工具 exit 0；長輸出曾截斷，關鍵條款與新增程式已按行段重讀；一次工具呼叫於 dispatch 前中止，未執行命令，後續同一唯讀讀取成功 |
| 同角色助手 | 回報三次唯讀命令 exit 0，含兩份測試與候選無差異核對；本主代理另查 E1 原行與報告位置 |
| 私有助手摘要寫入腳本 | 首次 stdin 未宣告 UTF-8，SyntaxError、exit 1，未執行寫入；加入編碼宣告後 exit 0。沒有操作產品或真實資料 |

私有證據：`.local/line-backup/tasks/notes-reattest-s1-simplicity-20261108/`，含候選完整 diff、來源／版本／歷史 log hashes、個別命令輸出；交付 checks、commit 本體與遠端回讀另存該目錄。私有原始證據不納入提交。

**歷史測試證據，非本輪重跑：** 讀取原 S1 logs 及其 SHA-256，與 checks.md 相符：preview 13 tests／exit 0、CLI help／exit 0、locks 7 tests／exit 0。這支持原命令成功，沒有消除 E1／E2，也不是本角色重新接受 T1／T2。

**事實：** 候選只增加唯讀預覽及配套合成測試；原 list directory guard 仍比 device／inode；沒有新 event kind、confirm、有效 binding resolver 或 freshness gate。來源 hashes 相符。

**推論：** 現有成本由核准完整 witness 及拒絕邊界驅動，沒有證據支持刪除重大機制仍保留全部需求。靜態未見寫入路徑不代表完整動態純讀驗證已成立。

**未知：** device 改變原因、同一持久物件／matching clone、舊 UNKNOWN 晚到、真實 list 完整集合、其他 gate、真實 volume 及跨 Session 能力。本信任模型仍不能識別完全相符 clone。

**NOT_RUN：** 本輪產品測試、完整 T1／T2 接受、完整回歸、S2／T3–T11 後續驗證、真實帳本 preview／confirm、受控 volume、LINE／chooser／下載／解碼、跨 Session、獨立 acceptance。這些不屬本輪唯讀簡潔性檢查；沒有新增實機 OBSERVED。正式功能測試與驗收仍由各自人工關卡負責。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: SIMPLICITY_IMPLEMENTATION_REVIEW_PASS_S1
IMPLEMENTATION_STATUS: S1_CANDIDATE_IMPLEMENTED; PRODUCT_UNCHANGED_BY_REVIEW; S2_NOT_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_REVIEW_SOURCE_VERSION_DIFF_CHECKS; HISTORICAL_S1_CHECKS_EXIT_0; E1_E2_EVIDENCE_LIMITS_OPEN; PRODUCT_RETEST_AND_FULL_REGRESSION_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_OWNER_NEXT_HANDOFF
```

## 人工交接與停止

本輪簡潔性關卡已完成，S2 尚有核准計畫中的實作工作。由 Owner 決定下一個 Implementer 交接，攜帶精確 S1 候選、本報告、核准 plan／handoff、原 implementation 與 logs，明列 E1／E2。這不是自動開始 S2、修復、retest、Acceptance 或日常備份；不因角色順序重做已完成的計畫關卡。

沒有因此獲得真實轉接或 LINE 授權，原備份維持 BLOCKED。若候選實質變更，由人決定適用重查。本輪依 Owner 明示要求，在審查產物完成後交 GPT-6 luna helper 梳理上下文及草擬詳細 commit 訊息，再逐檔提交與普通推送；該助手不作正式審查或獨立接受。模型請求／平台回報／provider usage 分層記錄於私有 delivery receipt，不預填執行成功或後端身分。
