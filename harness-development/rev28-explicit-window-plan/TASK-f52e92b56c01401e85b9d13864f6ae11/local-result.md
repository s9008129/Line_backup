# 本機 v3 元件驗收結果

2026-10-06：使用者「同意」授權的本機 explicitLineWindows v3 元件已實作完成，獨立 A1 正式 PASS。完整驗收見 [acceptance.result.json](acceptance.result.json)，保存核對見 [acceptance-archive-validation.json](acceptance-archive-validation.json)。

- 新 profile 精確綁定 LINE 主視窗與符合條件的子視窗、display/filter/crop/scale，以及原始 request 與 settling 證據；session 成功返回與計數前、保留 packet 載入時使用同一驗證。Production factory 拒絕此 diagnostic-only profile。
- 隔離後 focused 60/0、完整 302/0/0 skip；實際 CLI 與 loader build、4 個 CLI 拒絕案例、舊 externally anchored v1 載入、合成 v3 載入及 10 個重新綁定 anchor 的語意竄改拒絕皆 PASS。
- 凍結 source52 SHA256：`02b17aaa488c80f77056ed7e34f03d0a0d51ce4dd0a165d4dda0a65f999037b0`。只變更 13 個授權產品路徑；產品 candidate 3/3，另列 task-only runner recovery 1。
- 獨立完整 64817 項保存核對通過。原 Git HEAD/index、未 staged 狀態、設定、revision16 備份狀態及已完成的 57 張照片（17,924,900 bytes）保留。

原測試曾寫入 system temporary directory，歷史 I5 隔離 FAIL 保留且未 waiver；歷史外部 filesystem effects 未完整稽核。目前 PASS 來自已審查的 task-only package/test-root 副本。此證據不宣稱 OS sandbox、network denial 或實機畫面正確。

六個狀態：PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED；IMPLEMENTATION_STATUS=COMPLETE；CORE_ACCEPTANCE_STATUS=PASS；REQUIRED_VERIFICATION_STATUS=PASS；INDEPENDENT_ACCEPTANCE_STATUS=PASS；TASK_CLOSURE_STATUS=IN_PROGRESS。

這次沒有操作 LINE、擷取真實 v3 畫面、下載、輸入、network、commit 或 push。合成 v3 不是實機像素證據。目前不需要把 LINE 切到前景。

整套 native 備份仍未完成；真實 v3 render、校準、popup ownership/occlusion、current target/composer、PhaseB、entitlement 與 reusable workflow 尚未證明。下一步須先提出具體的新實機診斷方案並取得必要明示 grant，才可執行；本機「同意」與 A1 PASS 不授權自動擷取，也不重設原 production 3/3、child 2 或 count-only 1 預算。已完成的 57 張不得重新下載。
