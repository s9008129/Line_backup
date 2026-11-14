# Issue #50 記事本派送證據流程：實作報告

## 本角色結論

- 角色／階段：Implementer 的第一個可驗證切片；本切片就是完整文件候選。依 STANDARD 流程，交付後停止，等待 Owner 另開主 Session 啟動 implementation Simplicity Review。
- 核准輸入：[plan.md](plan.md)、[handoff.md](handoff.md)、[plan-review.md](plan-review.md) 與 [simplicity-plan-review.md](simplicity-plan-review.md)。計畫 SHA-256 為 `4569ed0e9bd80f16665d9a71c61d87981203c19c40b084ad62758743dacc9634`；交接版 SHA-256 為 `00088cbf97cfcf7a70abeb105e9bdc2d2a5009ce5b8cea4efa17c075fd3ed073`。
- 完成內容：計畫第 4 節的六項文件要求均已落到最終 Skill、三份既有 reference、新的證據範本與 C1–C9 判定案例；未改 `plan.md`、兩份審查、`notes.py`、事件格式、CLI、相簿程式或測試。
- 本次沒有操作 LINE GUI、下載媒體、讀寫真實 ledger／照片區、解除舊 `UNKNOWN`、跨列表、合併 `master` 或關閉 Issue。原 Issue 的核心 acceptance 仍為 `BLOCKED`。
- 同角色 helper：本實作先後以多個唯讀 helper 做分段／平行核對；另有一次 thread-limit 及兩次因工具不支援指定 reasoning 參數而未啟動，均由主 Session 繼續，未改用其他模型入口。所有 helper 的意見均在主 Session 以文件或程式證據複核後才採用。未提供 model override；本報告不把 request 參數、UI 顯示或 provider 用量互相替代，也不把 helper 當成獨立審查或 acceptance。

## 基線與候選

| 項目 | 實際值 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup` |
| Branch | `feature/line-notes-media` |
| 起始 HEAD／遠端 | `23af9693c64e6f84d06d1da3e44be49bab423468`；`origin/feature/line-notes-media` 相同 |
| 起始工作樹 | 乾淨；沒有需保留的無關 dirty／untracked 變更 |
| 計畫基準 | `abd363c3c6154314ed7af252f707522e4ad70517` |
| 審查交付 | `005f08986f3b52f6e03d5711a9d39ee12c5c9976` |
| 最終候選 | 本報告、下列六份 Skill 文件共同構成的 commit；完整 commit ID 以 push 後 `git rev-parse HEAD` 及遠端精確 HEAD 核對 |

最終 Skill 候選的 SHA-256：

| 檔案 | SHA-256 |
|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | `3056b400b34833ce0558b252f0083bdb9e3957bef1b468921ec64b23a58908e1` |
| `references/download-and-ledger.md` | `0c68cdefd2a58fddea430dfb2a360f3b84f0bfbddda79a9e61bbc2fc4ebfa652` |
| `references/evidence-decision-cases.md` | `709e4c7b3823bdeb8b1fa420e1f8961f50c70cf0acc131c69432bf5ffb02f150` |
| `references/evidence-template.md` | `c7e0ac942b9a9af4d76190372a241d46187874abe69ba4400eb0273d7cefd1e2` |
| `references/gui-inventory.md` | `5e0b128edeefe2cc401c6b388c8f8d6629d209940e57f5bcdcba8143f04a93ee` |
| `references/verification-and-recovery.md` | `d6e28c1ff3346e482abe008d53c955367d73a14c076f8dac551be2cf6b64bbe7` |

## 變更範圍與行為

| 路徑 | 狀態 | 行為 |
|---|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | modified | 主流程摘要 intent 前後定位、下載控制與 chooser 各自至多一次、outcome／reconcile 分流、未收斂停止及恢復授權硬邊界 |
| `references/download-and-ledger.md` | modified | 作為單項交易與操作順序唯一來源；補預檢、intent 讀回後再定位、兩個呼叫計數、第一筆 outcome、停止與恢復 CLI 條件 |
| `references/gui-inventory.md` | modified | 新增來源／範圍、popup 缺席、時鐘、座標映射、控制、input 回傳及 chooser／檔案歸屬的觀察界限 |
| `references/verification-and-recovery.md` | modified | 新增證據與允許行為矩陣、充分／不足完成及停止證據、UNKNOWN 與恢復順序 |
| `references/evidence-template.md` | added | 自由文字 evidence 範本；三層 key、attempt／事件引用、原目的地、來源與尺寸、時鐘、映射、輸入、chooser、驗證及未知欄位 |
| `references/evidence-decision-cases.md` | added | C1–C9 假設案例；每例均有前提、觀察、可支持命題、允許動作、禁止推論與缺少證據 |

## 計畫要求對照

| `plan.md` 第 4 節要求 | 最終文件落點 | 案例／檢查 |
|---|---|---|
| intent 前資格／來源／控制預檢 | `download-and-ledger.md:103`；`SKILL.md:55`；`gui-inventory.md:81` | C1、C6 |
| intent 保存讀回後再次定位 | `download-and-ledger.md:104-105`；`evidence-template.md:12,16` | C1、C6 |
| 下載控制與 chooser 各自至多一次並分記原始回傳 | `download-and-ledger.md:106-107`；`evidence-template.md:17-18` | C2、C3、C9 |
| popup 未涵蓋不得判不存在 | `gui-inventory.md:69,78`；`evidence-template.md:14,124` | C3 |
| 三層 key、attempt、原目的地、來源／範圍／尺寸、時間／時鐘、映射、控制、input、chooser／檔案歸屬 | `evidence-template.md:11-21`；骨架 `:28-103` | C1–C9 共同引用範本 |
| 缺值 `UNKNOWN`、工具計算／讀回 hash、唯一檔名、私有區域 | `evidence-template.md:5,116-120,124` | 文件檢查；未宣稱 CLI 驗證語意 |
| 無 outcome 與已有 `outcome=UNKNOWN` 分流；未收斂不 verify／新 attempt／下一項 | `download-and-ledger.md:108-109`；`SKILL.md:56`；`verification-and-recovery.md:26,134` | C3、C5、C6、C7、C8 |
| 恢復需 STOPPED／NOT_SENT、持久化授權與 recovery evidence | `download-and-ledger.md:124,128`；`verification-and-recovery.md:133,138`；`SKILL.md:65` | C9 |
| 判定案例六個必要區段與充分／不足完成、停止證據 | `evidence-decision-cases.md:5-84` | C1–C9；每個標籤各 6 次 |
| 影片播放結束不是下載完成；照片 toast 不是所有影片必要條件 | `verification-and-recovery.md:33`；`evidence-decision-cases.md:41-48,68-75` | C5、C8 |
| 沿用既有 `--evidence FILE`，不新增 schema／parser | `download-and-ledger.md:113`；`verification-and-recovery.md:18`；`evidence-template.md:3` | C1–C9 假設案例共同界限 |

操作順序只維護在 `download-and-ledger.md`；GUI reference 管定位與觀察，verification reference 管結果與驗證，主 Skill 只摘要並連結。

## 實際檢查與證據

環境：macOS 27.0.1（26A434）、`/usr/bin/python3` 3.9.6、Ruby 2.6.10；所有命令的工作目錄均為 repo root。私有證據位於 `.local/line-backup/tasks/20261101-issue50-implementation/`，不納入 commit。

| 檢查 | 實際命令 | Exit | 結果／證據 |
|---|---|---:|---|
| 每日回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | 73 tests，317.770s；`test-daily-final.log` |
| notes CLI 入口 | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | 子命令與 0／2／4／70 契約可見；`notes-help-final.log` |
| 記事本回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | 82 tests，8.333s；`test-notes-final.log` |
| 差異格式 | `git diff --check` | 0 | 無輸出；`diff-check.log` |
| 相對連結與錨點 | `ruby .local/line-backup/tasks/20261031-notes-media/check_notes_skill_links.rb .agents/skills/line-notes-agent-cua` | 0 | 全部 local Markdown 連結可解析，`links=25`；`link-check-final.log` |
| Skill frontmatter／引用 | `ruby .local/line-backup/tasks/20261031-notes-media/validate_notes_skill.rb .agents/skills/line-notes-agent-cua` | 0 | `frontmatter=ok references=6`；`skill-format-final.log` |
| 案例與關鍵欄位 | `/usr/bin/python3 -B .local/line-backup/tasks/20261101-issue50-implementation/check_evidence_docs.py` | 0 | C1–C9 均存在，每例 6 個必要標籤；關鍵欄位均在範本；`document-consistency-final.log` |

測試使用隔離 fixture；`notes --help` 與簿記入口通過不是 GUI、真實下載或 E2E 證據。`git diff --check` 只檢查 whitespace error，不代替語意審查。

## 事實、推論、未知與停止條件

- 事實：本輪只修改核准的六個 Skill 文件並新增本報告；`plan.md`、兩份審查、`src/`、`tests/` 與相簿 Skill 均無差異。起始 HEAD 與遠端一致，工作樹在實作前乾淨。
- 事實：指定四項本機檢查與三項文件檢查均 exit 0；完整輸出保存在私有任務目錄。
- 推論：證據矩陣、操作順序、範本及案例可降低把 input 回傳、chooser、下載結果、檔案驗證及 completion 混為一談的風險；尚未以真實 LINE 操作驗證。
- 未知：真實 popup／chooser 的來源與延遲行為、Computer Use 原始回傳格式、原 click 觸發因素、充分停止 receipt 是否能取得，以及真實混合附件與跨 Session 能力。
- 停止條件：需要縮小 blocker、改事件／資料語意／CLI／公共介面、跨列表或改用相簿入口繞過；缺授權／前景、恢復授權未持久化、必要能力不足、工具拒絕、發現新根因、身分或寫入衝突、`notes` exit 70、無新資訊的重複查證，均停止並交人決定，不換入口或降低證據標準。

## 未執行項目

| 項目 | 狀態 |
|---|---|
| 真實 LINE 記事本 GUI／popup／chooser | `NOT_RUN` |
| 真實下載、照片／影片及混合附件 | `NOT_RUN` |
| 真實 ledger、舊 `UNKNOWN` 調和或恢復 | `NOT_RUN` |
| 跨 Session 恢復 | `NOT_RUN` |
| Implementation Simplicity Review | 待 Owner 啟動 |
| Independent Acceptance／Issue #50 關閉 | `NOT_RUN`／`BLOCKED` |

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS=EVIDENCE_FLOW_DOCS_IMPLEMENTED
IMPLEMENTATION_STATUS=DONE
CORE_ACCEPTANCE_STATUS=BLOCKED
REQUIRED_VERIFICATION_STATUS=PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=BLOCKED
```

`IMPLEMENTATION_STATUS=DONE` 只表示核准的文件切片已完成且有實際檢查證據；不是產品 acceptance，也不是 Issue #50 `DONE`。`REQUIRED_VERIFICATION_STATUS=PARTIAL` 表示指定本機回歸與文件檢查通過，但真實 GUI／下載／跨 Session 仍 `NOT_RUN`。

## 人工交接

Owner 應在獨立主 Session 啟動 implementation Simplicity Review，攜帶本報告、精確 push commit 與遠端 HEAD。若審查認為已無剩餘實作，依 4.9 流程交下一個適用角色，不重開 Implementer；本角色不自派 Review、Acceptance 或 E2E，也不合併 `master`、force-push 或關閉 Issue。
