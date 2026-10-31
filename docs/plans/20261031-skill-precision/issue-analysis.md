# Issue #46：責任契約分散的有界診斷

## 文件身分

本檔由實作階段保存前一輪唯讀診斷；不是本輪新開的正式 Reviewer，也不構成獨立驗收。分析輸入為 Issue #46、原 handoff、現行文件與程式，基線 `bd04e091005581435831e5bbe99bb75fbbc34d49`。前輪受 Plan Mode 限制未寫檔；Owner 現已明示實作核准計畫。

## 選定根因與最小重現

選定根因：Owner、常駐指令及 Skill 的責任契約分散，重複及衝突使同一狀態可能得到不同下一步。可由基線文件重現：手冊將返回／popup／CLI 詳細順序放進 Owner Prompt；inventory 第 53 行說有受保護歷史不可下載，但 backup-and-resume 的下載前規則要求跳過受保護歷史。這是可核對的文字衝突；它造成每一個真實事故的因果關係尚未證實。

## 事實、推論及未知

- 事實：基線 Skill 已寫明一次授權、不逐本請示、自動恢復及授權／觀察／定位／派送狀態的區分。「完全沒有自適應授權」不是可靠根因。
- 歷史報告：20261030-cua-navigation/analysis.md 記載 Escape 後相簿視窗消失；原始像素未保存，屬公開事件整理及 OBSERVED，不是本輪重播。
- 歷史報告：SaveAll 根因紀錄記載補觀察 popup 及特定 Session 四本／141 張結果。save-all-gate/implementation.md 的 11/11 是 synthetic 文字案例，自評且新版 GUI／獨立 acceptance 為 NOT_RUN。Issue #46 另記五本／86 張，範圍不合併。
- 程式事實：daily.py outcome 只接受第一筆結果；complete 需 DOWNLOAD_FINISHED，明確 UNKNOWN 不能改寫。未完成上一 attempt 會阻擋下一本。此能力限制不能靠更多授權文字解除。
- 推論：分工精簡、單一決策規格及真實任務評估有望減少誤停和重複索權；需新版行為與 GUI 證據驗證，不能直接當作成效。
- 未知：最新任務完整原始操作 trace、所有實際問題及各自因果鏈、任意環境成功率、跨 Session 恢復的完整獨立證據。

## 既有嘗試與新增資訊

導覽分析指出「操作後觀察」不能取代輸入前作用依據；Save All 實機紀錄指出主視窗漏 popup 時另有允許的觀察來源可補；後續文件修補新增 11 個合成決策案例；Issue #46 則只交付規格而未落實精簡。這些來自不同問題／切片，不能加總成同一根因的重試次數。本輪診斷沒有執行 GUI 或重新下載。

替代解釋包括工具缺少可靠畫面／映射、入口交接不明，以及紀錄能力限制。若精簡後仍在證據充足的相同案例反覆索權，將反駁「文件分工足以改善遵循」的假說，需保留 trace 再診斷，不能一味加長 Prompt。

## 唯一路由

`IMPLEMENTER_FIX`：依已核准 plan.md 做專案文件與提示詞一致化。成功檢查為同一份範本明確授權及交接、無相互衝突的停止規則、合成行為與本機回歸證據，GUI 與獨立驗收另交接。需要改 UNKNOWN 收斂能力、格式、資料、全域設定或下載入口時停止，不擴張本切片。

## 來源與實際唯讀核對

- [原始交接](handoff.md)、[Save All 分析](../20261030-save-all-gate/analysis.md)、[Save All 實作](../20261030-save-all-gate/implementation.md)、[導覽分析](../20261030-cua-navigation/analysis.md)。
- 前輪實際執行 Git status、rev-parse、worktree list、show、ls-remote，以及 cat／sed／rg 唯讀檢查；`git diff --check` exit 0。本機及遠端精確 HEAD 均為上述基線。
- 官方 [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 與 [Skills](https://learn.chatgpt.com/docs/build-skills) 支持持久指引及按需載入；[Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use) 支持當次畫面／動作後觀察；[評估原則](https://developers.openai.com/api/docs/guides/evaluation-best-practices) 支持以任務及歷史失敗設計評估。這是設計依據，不證明本機具備某個 API 或已經 E2E 通過。

前輪診斷狀態為 ANALYSIS_COMPLETE；實作、core acceptance 與獨立 acceptance 為 NOT_RUN。未建立正式驗收結論。
