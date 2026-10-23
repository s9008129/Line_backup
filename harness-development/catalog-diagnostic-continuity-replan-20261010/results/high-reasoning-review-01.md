# 獨立 pre-live 審查 01：FAIL，交回 Planner 重計畫

本文件保存已在對話完成的唯讀審查結論，並依使用者後續明確指示，與完整 JSON 一起發布到 Git。審查當時沒有寫檔或 commit；本次是另行授權的文件保存與提交。JSON 中「本輪未寫檔／commit」描述審查階段，不描述後續發布階段。

完整角色結果：[high-reasoning-review-01.result.json](high-reasoning-review-01.result.json)。本地審查不是 controller receipt：未取得 issue claim、analysis_path、固定 validation/return 指令；validation_fact=NOT_RUN，controller admission=BLOCKED。

## 審查綁定與結論

- candidate hash：`646145c69265cc33aae2ceaa860efa97048b04cc0e4c17c6bdea69902e11a5b6`。
- packet SHA-256：`cd6edf3edbf44d68ac318d0f508914f83ab771aab989d4b0f1e4fe20a5d315c4`。
- contract SHA-256：`0c141010ecd092e3b2556bacf3488bd53d2897d5a234f2b4f4eb2c4945d0818d`。
- 裁決：**PRE_LIVE_REVIEW FAIL**；唯一建議路由：**PLANNER_REPLAN**。
- 審查者未參與受審候選；審查階段沒有 helpers、runner/OCR 重跑或 LINE 輸入。後續使用者要求的 GPT-6 Luna（xhigh）子代理只讀上下文、撰寫提交訊息，不是另一份 Acceptance。

## 保留的正向事實

封包 21 筆、gate evidence 14 筆、implementer evidence 10 筆 hash/bytes 相符；43 筆 replay 與來源逐 bytes 相符；source manifest 的 REQUIRED_CURRENT_HASH 無差異。四幀 RGBA guard 相同，三段 D 及 suffix-prefix ordered overlap 可由保存資料獨立重算，scan-003 的原始「相溥」保留，replay 永遠不授予 live 權限。方向四角 RGB 與預期相符、alpha=255。16 個 derivative 的 nearest 2x 像素可以獨立核對，但其 ROI 全是全圖。

歷史 preservation.before/after-02 的保護集合及 Git 基線相等；該歷史 PASS 不改寫。審查時 HEAD 已是 `5fb43999b3705fbffa59dbd244a432ad84ebf257`，parent 是快照所用 `4a7a36f5bf0af197a18d1f7ed3add4b7f77e51c3`，因此原快照不能當提交後保存證據。審查直接重驗記錄中的 backups 239 筆、canonical state 3 筆、舊 task 93 筆、產品來源 92 筆及凍結文件 10 筆 hash 相符，tracked diff hash 也相同。

## 阻擋實機的缺口

1. 所有新 OCR 實際使用全圖 ROI `[0,0,654,1286]`；規格要求的局部 ROI 與非零 crop-origin 轉換沒有實際驗證。R17 的零 origin 算式不足以補足。
2. 評估器會略過 legacy 的有效次候選身份衝突與日期框位置檢查；另有 ambiguous count row 時仍可能允許 scroll。candidate/profile/decoder/binding hashes 只是回傳欄位，未驗證後仍可能顯示 binding VALID。
3. indicator UNKNOWN 時仍延伸 chain；fresh safety UNKNOWN 時禁止 scroll，但仍延伸 chain 且 stop_reason 為 null。
4. R06 缺 age，未隔離 safety 條件；R08 未驗證 persist/readback 和 refresh 計數；R12 未驗證 terminal stop 及 non-adjacent reappearance；R18 將政策常數直接記 PASS；R19 只比較 hash 不同，未證明拒絕重用流程。
5. frame manifest 先 exclusive-create，之後以 write mode 覆寫，違反 append-only；問題單仍寫 CORE_ACCEPTANCE_STATUS=PENDING，與定稿 implementer 的 NOT_RUN 不一致。未找到 29 項 unittest 保存執行紀錄，僅確認 source 有 29 個方法。

七個唯讀記憶體測例的觀察如下；它們使用保存的資料與合成修改，沒有 UI 輸入或 native 證據，工具輸出保存在對話中，沒有獨立測試紀錄檔或 controller receipt。

| Fixture | 實際結果 |
|---|---|
| positive control | scroll=true、chain=true |
| legacy 張數首候選 65，另有效候選 66 | 未報 conflict，scroll=true、chain=true |
| legacy 日期框移到 viewport 外 | 仍 identity COMPLETE，scroll=true、chain=true |
| 加入日期和 6O 的 ambiguous count row | ambiguous=1，scroll=true、chain=true |
| candidate/profile/decoder/binding hashes 改全零 | binding VALID，scroll=true、chain=true |
| 移除相簿 indicator | indicator UNKNOWN、scroll=false、chain=true |
| fresh safety UNKNOWN | scroll=false、chain=true、stop_reason=null |

以上不能由原「19 PASS」記錄補足，也不推論蓄意造假。原 gate manifest 不改寫，角色 JSON 的 gate_results=[]，不簽發任何新 gate receipt。

## 六項狀態與下一步

PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED；IMPLEMENTATION_STATUS=IN_PROGRESS；CORE_ACCEPTANCE_STATUS=NOT_RUN；REQUIRED_VERIFICATION_STATUS=INCOMPLETE；INDEPENDENT_ACCEPTANCE_STATUS=PENDING；TASK_CLOSURE_STATUS=REPLAN_REQUIRED。

唯一下一步是交給 Planner 準備 bounded replan，精確明列修復範圍、必要行為測試、候選重新凍結後哪些證據失效，以及已消耗「歷史 3＋追加 1」的方法額度如何處理。審查中指定的建議新增計畫路徑是 `results/pre-live-replan-01.md`；本次沒有產出或執行該新計畫。

待新計畫完成必要審查与授權後，才由 Implementer 做針對性修正及驗證。不得自行開始第五種方法，不以新 task 重設預算。live 保持 0/6；同候選離線與獨立 pre-live 審查 PASS，加上使用者新的 LINE 前景就緒協調後，才可開始唯一一次最多六次 scroll 的實機；最終獨立 Acceptance 仍必要。本次文件提交沒有修改候選、凍結輸入、舊任務、產品、canonical state 或照片，也沒有執行實機或解除正式 admission。
