## 給下一位 Implementer 的 Prompt（由 Owner 在新主 Session 貼上）

~~~text
請以 Implementer 角色，實作 LINE 相簿導覽的有界文件修補。

Repo：/Users/hsiaojohnny/dev/Line_backup
任務目錄：docs/plans/20261030-cua-navigation/
本次採用 implementation_plan.md v2 與本 handoff.md，採用「第一切片同步五份產品文件及八組案例規格」安排，保留實作後 Simplicity Review 與獨立 Acceptance。這是 Owner 在本新 Session 提交的文件實作授權；不授權 GUI、模型矩陣或真實照片作業。

先讀 AGENTS.md、/Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md，以及上述 plan、handoff、implementation-artifact-manifest.json、analysis.md、原 plan.md、simplicity-plan-review.md 和專案 Skill。核對 Git 根目錄、branch、HEAD、worktree、dirty/untracked，保留既有成果。
新候選以本次 plan/handoff/manifest 所在交付 commit 及 hashes 識別；文件整理起點 a748cfc561a44d2347142fc7b72609584baaaffd，產品基準66ebd9d50378d3b1d533c83eaf48eaca9a72ef43。核對manifest及十份產品來源，版本或授權不符就保留原狀並報告，不改基準、reset或覆寫。

目標是補齊非列表入口、導覽動作作用依據、結果核對與異常停止。當次Escape後其實有AX/截圖觀察，失誤在輸入前缺依據，不要誤寫成未觀察或Luna特有問題。無可靠返回入口不得猜Escape、Command-W或點關閉；有可靠控制項或匹配角色/焦點的已驗證快捷鍵則應自主前進，不以一律拒絕過關。

只修改plan列出的Skill、verified-experience、inventory、backup-and-resume及使用手冊的入口/返回內容，新增behavior-cases.md與implementation.md。核心條件在SKILL必讀段，細節集中verified-experience，其餘引用。保留chooser鍵盤流程、盤點、逐本一次Save All、intent/完成讀回、UNKNOWN/受保護歷史、不重下及原檔案驗證。

不要啟動、擷取或操作LINE，不呼叫CUA，不讀寫active-task/backup-records/照片，不執行真實daily任務。不得改daily、relocation、ImageIO、OCR、tests、AGENTS、全域設定或新增控制器。只建立脫敏靜態案例規格，無原始像素就標synthetic文字案例；不執行模型矩陣或宣稱行為/GUI PASS。

按plan執行V1–V6，含文件/連結/範圍核對、git diff --check及一次既有最小回歸：
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
只用現有合適工具。缺SDK或驗證失敗就記真實結果交人，不改系統工具鏈或越界修source。同根因最多三次有證據嘗試，連續兩次無新資訊停止。

完成文件切片及本地檢查後，寫implementation.md，記精確候選、plan/handoff hashes、實際命令/exit/證據、未測項與六狀態。依專案授權逐檔add、commit、push並另建實作Draft PR；commit body含意圖、做了什麼、下一步建議、驗證與結果，讀回本體並核對遠端精確HEAD。不merge、force-push或改寫既有審查歷史。

第一切片交付後停止，由Owner另開Session啟動實作Simplicity Review；即使已是最終產品修改也保留該檢查點。不自動啟動下一正式角色、不作獨立接受、不跨角色修復/重測/結案。用繁體中文回報。
~~~

# 實作交接 v2

## 本輪請求、授權與審查地位

Owner 要求深度整理上下文、撰寫 implementation_plan.md 及以 Implementer prompt 開頭的 handoff.md；另要求完成後使用 GPT-6-luna subagent 撰寫詳細提交訊息，再 add／commit／push。本輪只整理文件，未啟動正式 Implementer、修改產品或操作 LINE。

上方 prompt 供 Owner 在新主 Session 主動提交以採用本版；存檔不等於已提交，也不建立 GUI 權限。不需要重新批准已授權的同範圍 Git 交付。

原計畫 Simplicity Review 是 **PASS**，只覆蓋 159d194b4276976d42eaa11d46f7c1ed0e4ee893 的原草稿。本版沒有新的獨立審查結果。第一切片合併採納原非阻擋建議，原三份核心及後續兩份引用文件改為一次同步；另明列 AGENTS 最小回歸。資料、架構及安全／驗收門檻保留；舊 PASS 不自動套給 v2。Owner 可另開 Plan Review 或決定重查，本稿不代替該決定。

## 精確版本與歷史保存

| 項目 | 來源 |
|---|---|
| Repo／規劃分支 | /Users/hsiaojohnny/dev/Line_backup／plan/cua-navigation-20261030 |
| 本輪文件起點 | a748cfc561a44d2347142fc7b72609584baaaffd，原 clean |
| 產品基準 | 66ebd9d50378d3b1d533c83eaf48eaca9a72ef43，未合併搬移候選，非 master 接受結果 |
| 原草稿 | 159d194b4276976d42eaa11d46f7c1ed0e4ee893 的 plan／analysis／role-report／兩份manifest／舊handoff |
| 原簡化報告 | a748cfc561a44d2347142fc7b72609584baaaffd 的 simplicity-plan-review.md |
| 新交付 | 本目錄 implementation_plan.md、新 handoff.md、implementation-artifact-manifest.json；最終 commit／遠端精確 HEAD 見本輪交付訊息與私有 progress |
| 規劃 Draft PR | [#42](https://github.com/s9008129/Line_backup/pull/42)，未合併 |

新 manifest 綁定新文件及來源 hashes。從**同一交付 commit**讀取 manifest 與文件，不混合浮動分支的不同時點。可用下列命令定位交付，再以 git show <交付commit>:<完整路徑> 取出核對；文件整理起點不含新文件，不能當新交付 commit。

~~~sh
git log --oneline -- docs/plans/20261030-cua-navigation/implementation-artifact-manifest.json
~~~

舊 artifact-manifest.json 保留原位元內容，在原草稿 commit 驗證五份 artifact。新版 handoff 與舊 hash 不符是版本分離，不可為讓舊檢查過關改 manifest 或審查報告。若新 manifest、十份產品來源或指定候選不符，停止交人，不能藉版本分離忽略漂移。

本輪新稿由原審查 Session 按 Owner 後續指示整理，不聲稱本 Session 對新稿有獨立審查資格。下一位實作者也不能以同 Session 自評或 helper 取代獨立接受。

## 必須攜帶的輸入

1. Owner 原目標、本輪文件／Git 指示與最前方 prompt，不只帶上一輪結論。
2. 同一交付 commit 的 implementation_plan.md、新 handoff.md、implementation-artifact-manifest.json。
3. 原 plan.md、analysis.md、role-report.md、source-manifest.json、歷史 artifact-manifest.json 及 Git 中舊 handoff 的入口。
4. simplicity-plan-review.md 與原候選；只引用其版本內的 PASS。
5. 專案 Skill／必要 references；保留既有搬移成果及其他 worktree，不擴入本次 diff。
6. 如需事件背景，讀 .local/line-backup/planning-20261030-escape/evidence/incident-summary.md；它是脫敏摘要、非完整 trace，沒有原始像素。缺私有摘要先用公開 analysis 事件表，不為補證據操作 LINE；仍缺必要事實才列阻塞。

## 事實、推論與未知

- 事實：Agent 猜 Escape 後有 AX／截圖觀察；原視窗消失、聊天主畫面出現，Owner 關窗回報屬 OBSERVED。Skill 未完整定義非列表入口與返回作用依據；daily／既有 unittest 不約束 CUA 語義選擇。
- 推論：入口分支及動作前後條件是最小指令修補；正向案例必須確認自主能力仍在。
- 未知：內部模型原因、跨模型遵循率、provider 身分／usage、各 LINE 版本鍵盤效果與新流程實機結果。單次事件不能歸因 Luna，也不能宣稱文件保證任意模型安全。

## 檢查責任與停止點

本輪只查文件、版本與傳遞完整性，命令／結果／checkpoint 存在 .local/line-backup/planning-20261030-escape/implementation-handoff/progress.md。先前審查檢查不移作本輪產品驗證。

| 下一項 | 責任人／輸入 | 交付或停止點 |
|---|---|---|
| 文件切片及 V1–V6 | Owner 新開 Implementer，採用本版精確文件 | 五份產品文件、B01–B08規格、implementation.md、本地檢查與精確commit／Draft PR；交付後停止 |
| 實作 Simplicity Review | Owner 另開正式 Session，候選／diff／報告 | 評實作最小性；不以原計畫 PASS 代替 |
| 模型行為矩陣 | Owner 指定模型／effort／次數／執行Session | 同版Skill／案例／工具能力、原始回答與四層模型證據；目前 NOT_RUN |
| 獨立導覽與真實備份 Acceptance | Owner 另開獨立 Session，重新授權指定列表及交前景 | 有據返回／無據停止、完整列表與逐檔／完成讀回；至少兩本才證明跨本，缺條件 NOT_RUN |

Implementer 不需要照片、真實紀錄或 GUI 前景。版本／來源／權限／寫入衝突不符、安全 FAIL、超範圍或驗證無法完成時，保留證據交人；不修其他角色拒絕、不自動重測至過。未完成條件不降門檻，Git／hash／部署完整性不當成獨立接受。

## 交接時六狀態

PRIMARY_OUTCOME_STATUS: IMPLEMENTATION_HANDOFF_READY
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: PENDING_HUMAN_HANDOFF

REQUIRED_VERIFICATION_STATUS 指產品及後續適用驗證；本輪文件核對另記結果，不覆蓋未測狀態。Owner 在新 Session 提交前，這是具體可採用的交接稿，尚未執行產品修復。
