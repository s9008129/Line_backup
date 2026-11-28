# 計畫草案 v1：記事本影片解碼診斷與完成判準

## 決策摘要

本輪角色是 Planner，結論為 `PLAN_DRAFT_COMPLETE`，不是產品 PASS。建議採用方案 C 的有界版本：只有 **ffmpeg 逐 stream 解碼**的 stderr 改作診斷證據，不再以通道是否空白單獨拒絕；ffprobe、工具版本探測、照片驗證及其他安全條件維持既有判準。此建議待 Owner 核准，尚未生效。

目標是讓「所有實際音視訊 stream 完整解碼、檔案穩定且證據可讀回」成為一致的影片完成判準，避免把 stderr 零 bytes 當成完整性的替代證明。這不保證特定 Post2 會通過，也不保證來源影片沒有播放器時間軸問題或所有靜默損壞。

任務分級：**CRITICAL**。本輪寫文件的風險低；擬議產品變更會改變影片進入 candidate／completion 的必要條件，且涉及持久化證據相容性，應保留獨立計畫審查與獨立驗收。2026-10-31 原功能開發的審查豁免不移植至本案。

| 方案 | 結果與代價 | 本草案判斷 |
|---|---|---|
| A：保持所有 stderr 拒絕 | 不改執行期；明確承認零診斷是額外產品要求，接受阻塞 | 若 Owner 要求零診斷，應另修本草案為 A；目前不是已核准政策決策 |
| B：精確 DTS allowlist | 必須證明完整診斷均可分類、綁定工具版本，測未知與混合錯誤 | 既有完整 stderr 未留存，不能只憑 preview 放行全部；不推薦本案加入 parser |
| C：完成判準與診斷分開 | 保留硬性解碼與一致性檢查；接受 exit 0 且 coverage 完整時仍可能有未知診斷的剩餘風險 | **推薦的待核准方案**；下述切片與測試僅適用 C |

不採第二 decoder、轉檔、修改時間戳、播放器自動化、全域警告解析器或新增 GUI 控制器。既有 validator、normalizer 與測試足以承載修改，不需要帳本遷移或新 CLI 開關。

## 範圍與基準

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`，主工作目錄。
- 分支：`feature/line-notes-media`；產品基線：`2f53bebd0875239312dacb0cb2cf843792a6377d`。
- 起始 tracked／index 無差異；唯一 untracked 是 Owner 已建立的 `issue提交單.md`，含私人資訊，原樣保留、不 stage、不推送。只提交 [遮蔽來源摘要](issue-context.md)。
- 遠端讀取時同分支也指向上述 HEAD；交接接收者仍須重新核對，不能以此保證之後不變。
- 本輪可寫：本目錄五份 Markdown，以及 `.local/line-backup/tasks/20261110-notes-video-stderr-policy-plan/` 的規劃證據。HTML 頁依 Answer me with HTML 的全域設定輸出，並非產品檔案或原始證據。
- 本輪禁止：產品修改、執行產品測試／解碼、LINE／GUI、真實照片與帳本讀寫、verify、resume、activation、reattest、restart confirm、下載。
- 手動流程來源為使用者指定的 `01_plan_prompt.md`；專案內無 `policies/v4.9.0/`，本輪讀取 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 的兩份手動政策，不建立 controller、不復活退役流程。

核准 C 後，未來 Implementer 的產品可寫範圍僅限：

| 路徑 | 允許改變 |
|---|---|
| `src/line_backup_batch/media_verify.py` | ffmpeg 解碼 stderr 的判準、既有診斷欄位一致性、必要 policy 識別；保留 probe／版本探測 gate |
| `src/line_backup_batch/notes.py` | 對應 normalizer 與 `_validate_verification_payload`／`_validate_video_decode_stream` 的一致政策；普通 verification 與 restart candidate 共用，不改派送／activation 條件 |
| `tests/test_notes_media_verify.py` | 解碼診斷與真實合成影片反例 |
| `tests/test_notes_regressions.py` | 新舊證據載入、未知 policy／矛盾欄位／偽造 coverage 拒絕 |
| `tests/test_notes_restart.py` | 合成批次 mixed-policy candidate 重開、驗證與 activation 回歸 |
| `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md` | 只更新影片解碼成功判準、診斷證據與版本相容性說明 |
| 本任務目錄及對應私有證據目錄 | 實作／驗證／交接報告；不得在計畫旁預填獨立批准 |

不修改 `daily.py`、`record_store.py`、`image_decode.swift`、相簿 Skill、既有相簿介面／事件，或 notes CLI 參數／退出碼。`AGENTS.md` 已規定有效影像與完整解碼，本案無須加入操作細節。歷史已核准 `docs/plans/20261031-notes-media/plan.md`／handoff 保持原版本，以本次核准計畫作後續增補，不回寫歷史成為「當時已核准」。正式啟動 Prompt 不增步驟。

## 證據、推論與未知

1. **本輪直接核對：** Skill reference 明文要求 stderr 空白；runtime 在 coverage 前拋出 `DECODE_STDERR`；persisted decode validator 同樣強制空白。ffprobe 另有 `PROBE_STDERR`／載入器空白條件，工具版本檢查另有 `VIDEO_TOOL_VERSION_STDERR`。定位見 [來源摘要](issue-context.md)。
2. **歷史事實：** `81d9db40a702a145cd2e2e9004cc01ce6df912e3` 同時加入嚴格條文及程式，未修改原始 plan；不能由提交歷史推定作者動機或證明未曾有其他口頭批准。
3. **提交單記錄、未於本輪重測：** Post1 已有新 candidate、尚未 activation；Post2 有 `DOWNLOAD_FINISHED`，verify 因非空 stderr 拒絕，沒有 candidate／completion；列表未完成。Post2 的 exit 0／progress end 不能補造 coverage PASS。完整 stderr 未保存，不能聲稱全篇都只有 DTS 訊息。
4. **新增官方來源：** FFmpeg n7.1.1 的相同 DTS 訊息由 `AV_LOG_ERROR` 輸出並回傳 `EINVAL`。官方對 `-xerror` 與 `explode` 的說明不能證明每筆 log 都必然造成非零最終退出。不得稱已證明無害或以純「warning」字眼消除風險。見 [FFmpeg mux.c](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/libavformat/mux.c#L758-L767)、[ffmpeg 選項](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/ffmpeg.texi#L2188-L2189)、[codec 選項](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/codecs.texi#L191-L214)。
5. **尚未知：** Post2 全部診斷內容、所有 stream 的 coverage、播放器表現、現時檔案／來源／帳本有無變化、實際 binary 與原始碼路徑的完整關係。本輪沒有讀媒體、ledger 或重跑驗證。不能宣稱解除任何 blocker。

## C 的具體成功條件

### 完成判準

所有既有硬性條件必須同時成立：固定成對工具與 binary hash；有效容器與至少一條非封面的影像；全部實際音視訊 stream 精確映射且無漏流／重複；保留 `-err_detect explode`、`-xerror` 與現有 loglevel；真正整數 exit 0；stdout EOF、合法且到 end 的進度；duration／frame coverage 依現有容差計算；watchdog；檔案／檔集及工具前後穩定；來源與目的地身分；manifest、candidate／completion 保存及讀回。

**唯一政策變動：** 對 ffmpeg 解碼，非空 stderr 不再單獨觸發拒絕；不依 DTS／未知字串決定成功。未知診斷與已知 DTS 診斷都保存為診斷，若其餘條件成立可通過；不新增日常人工核准步驟。這是一項必須由 Owner 明確認可的政策取捨，不是已證明所有診斷無害。非零退出、無合法 EOF／coverage、工具或檔案漂移仍拒絕。現有照片、ffprobe、工具版本探測的 stderr 拒絕不變。

保留真實 `stderr_empty`、非負整數 bytes、SHA-256 與 preview，不把 false 改 true、不清空 log、不降低 loglevel、不改工具 pin。載入器核對 `stderr_empty == (stderr_bytes == 0)`；空內容 hash 必須一致，preview 型別／長度須合理。hash＋有限 preview 不能還原完整 stderr；C 不靠字串分類，故本案不新增完整 log 存放框架或宣稱已審閱所有診斷。

若合成壞檔實驗顯示真正解碼失敗在保留 flags 下仍以 exit 0、完整 coverage 通過，應停止並交 Owner 重決策；不能為了達到本案結果補入未核准 parser、換工具或刪除反例。

### 持久化與相容性

- 僅在既有 verification payload 增加明確的影片解碼 policy 識別，字面名稱由 Implementer 選定並記錄；不更動事件外框或重寫歷史。相同識別由 runtime、normalizer 與 loader 使用。
- **缺少識別＝舊嚴格政策**：舊 clean 證據仍可讀；缺少識別但非空 stderr 仍拒絕。不能把舊 malformed 證據重新解釋成 C。
- 明確的新識別才允許診斷非空，並重算全部 coverage；未知識別、型別錯誤與欄位矛盾拒絕。同一批次可包含原 Post1 型舊 clean 證據與新政策證據。
- 舊 reader 可能拒絕新政策非空診斷，須以基線 reader 的合成 fixture 驗證其安全拒絕並記錄限制；不承諾舊版能讀新政策。新寫入後不可因回退程式而刪改事件。
- 真實資料啟用前，Owner／執行者須確認後續 Session 使用相容版本；本計畫不授權寫入。若 additive payload 無法滿足上述相容性，需要事件遷移或新 CLI，停止回報邊界變更。

## 第一個可驗證切片與後續切片

**S1（第一切片）：** 同步修改兩份來源與對應測試：逐 stream runtime、normalizer、普通 verification 與 restart-candidate loader 都遵守上述 C／legacy 分流。補足程式產生的 stderr 診斷 subprocess 測試、coverage 反例、新舊 evidence 重開測試；使用合成檔案與隔離帳本，不讀真實資料。小型 policy 識別是證據來源標記，不建立可讓 Agent 任選標準的 CLI 模式。

S1 可核對證據是：診斷非空＋exit 0＋完整 coverage 的同一組 evidence 在寫入與重開後結果一致；舊證據仍維持原政策；負例仍拒絕。S1 結束由人啟動實作 Simplicity Review，不能自派 Reviewer。若已無剩餘實作，直接交下一適用驗證，避免製造空切片。

**S2（必要時）：** 在 S1 審查後完成 Skill 對齊、合成有聲／無聲與多 stream、截斷／損壞影片、mixed-policy restart lifecycle、全套必要回歸及報告。S1 即可完成這些工作時不刻意拆開。實作報告須列 actual／skip／退出碼，不把 injected 或 subprocess 診斷 fixture 當成真實影片事故已重現。

## 檢查、責任與停止條件

下列是**未執行的未來檢查**，不是 Planner 本輪結果。

| 檢查 | Owner | 足夠證據／停止條件 |
|---|---|---|
| 計畫簡潔性＋獨立計畫審查 | 人工另開 Simplicity Reviewer／Plan Reviewer 主 Session | 對精確草案 commit 審查 C 的語意、剩餘風險、相容性；任何拒絕回報停止，不啟動實作 |
| policy 邊界與 runtime／loader 一致 | Implementer | clean、DTS、未知診斷在 exit 0＋合法 coverage 下通過；非零退出、缺 EOF、coverage 短少、漏 stream、停滯、漂移仍拒絕；檢查 bytes/hash/preview 未被清洗 |
| 舊證據與偽造負例 | Implementer | legacy clean 可讀；legacy 非空、未知 policy、bool／float 冒充整數、矛盾 stderr、偽造 coverage 拒絕；無完成事件落入拒絕案例 |
| 真實合成媒體 | Implementer | 固定工具產生並驗證有聲／無聲、多 stream、截斷與損壞 fixture；全 stream coverage。工具不可用或必要案例 skip＝NOT_RUN，不能改 pin 降標準 |
| restart 相容性 | Implementer | 合成批次中舊 clean＋新診斷 candidate 重開、activation／completion 讀回；同一非空新證據由基線 loader 安全拒絕；舊 UNKNOWN、舊完成事件、派送規則不變 |
| S1 實作簡潔性審查 | 人工另開主 Session | 對第一可驗證候選；helper 不簽發接受 |
| 核心條件獨立驗收 | 人工另開獨立驗收主 Session | 對精確產品候選重現合成正負例、政策來源一致及相容性；不是 LINE E2E |
| 真實 Post2／整份列表 | Owner 正式日常 Prompt，另定精確資料範圍 | 本案不執行。若後續只授權既有 attempt 重新驗證，須先另定版本、檔案、綁定、次數及可寫事件範圍；verify 本身會寫 candidate，不是假唯讀；activation 須另有明確範圍 |

Implementer 必跑命令（每項獨立保存退出碼；測試僅可用合成／隔離 fixture）：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_media_verify.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_regressions.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

若 full notes suite 已包含同候選的前三組並有分組結果，不為湊命令重跑相同測試。Swift 只用既有相符 SDK；ffmpeg／ffprobe 不安裝、不升級。核心需求對應的 skip 保持 NOT_RUN。

GUI、混合附件 chooser、跨 Session 實機恢復、外部副本、服務端位元一致均不由離線測試推定。後續日常成果確認沿用手冊正式記事本 Prompt，不使用 Harness Acceptance／E2E Prompt 操作真實備份。本案獨立驗收只評離線產品條件，整份列表完成仍待另行日常執行證據。

## 風險、恢復與授權邊界

- 外部 writer 可改來源／檔案，GUI 前景、帳本與工具可能在交接後改變；現有前後檢查不能提供原子快照、OS 隔離、exactly-once 或服務端原始位元保證。
- 不改既有 completion／UNKNOWN／candidate／staging，不重送、不換目錄繞 gate；不修改 restart scope／generation、reattest／activation 流程或目前 LOCAL_CHANGED 判定。
- 產品尚未寫新政策事件時可撤回程式候選；寫入後只回退程式可能造成舊 reader 拒絕，應保留原件並停寫，不刪事件恢復可讀性。實際資料回復須另行授權。
- 同根因最多三次有證據嘗試，連續兩次無新資訊停止；既有真實 verify 拒絕不因換 Session 歸零。本案不消耗新的真實 verify 嘗試。
- 分支／HEAD 不符、外部新增 dirty、讀寫衝突、工具拒絕、意外接觸真實資料或需要超出 allowlist 的變更，保存證據並停止依賴動作。不得 merge master、force-push 或啟動下一角色。

## 人工檢查點與初始狀態

下一步由 Owner 決定是否採 C（包含未知診斷的剩餘風險與 probe 維持嚴格），並啟動**計畫 Simplicity Review → 獨立 Plan Review**。通過且 Owner 核准此計畫後，才由另一主 Session 開始 Implementer。後續依 S1 檢查點與獨立驗收交接；每一步均由人啟動，不自動接續。

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE; BACKUP_NOT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: PLANNER_SOURCE_AUDIT_ONLY; PRODUCT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_OWNER_POLICY_AND_PLAN_REVIEW
```

這些是本輪規劃邊界。舊候選／舊計畫的 PASS 不涵蓋本次政策；本輪 Git 交付不代表核准、實作或任務結案。
