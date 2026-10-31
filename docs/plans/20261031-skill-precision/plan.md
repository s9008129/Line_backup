# 已核准計畫：LINE 相簿一次貼上、完整執行

## 來源與基線

Owner 在本對話確認三項選擇後，對完整 proposed_plan 明示「Implement the plan.」。本檔保存該計畫的實作契約摘要；不是另啟 Planner 或補造正式審查批准。原始交接見 [handoff.md](handoff.md)，診斷見 [issue-analysis.md](issue-analysis.md)。

- repository：`/Users/hsiaojohnny/dev/Line_backup`
- branch：`fix/save-all-gate-20261030`
- baseline：`bd04e091005581435831e5bbe99bb75fbbc34d49`
- 保護既有未追蹤 `docs/plans/20261030-save-all-gate/acceptance.md`，不讀取內容、不修改、不提交。
- 只做專案指令、Skill／references、使用手冊與任務報告；不變更 daily、資料格式、全域設定或真實照片，不操作 LINE／CUA。

## 已由 Owner 決定

1. system prompt 的優化範圍限專案內 AGENTS.md、Skill 及 Owner 範本，不更動全域或平台指令。
2. 先開好指定列表，再提交一次正式 Prompt；提交同時授權並交接前景，仍須核對畫面。
3. 個別歷史 PROTECTED_HISTORY 可保留並跳過，繼續其他已核對項；有未解項不稱全列表完成。活動下載、未解派送與命名交易不可跳過另送。

## 交付行為

- 常駐指令保存邊界；Skill／references 保存工具路由、操作條件與單一 Save All 流程；手冊唯一 Owner Prompt 只提供當次目標、授權、兩個可填欄位、前景及例外契約。
- BACKUP_ROOT 留空為目前專案 backup/，其他 root 僅限工具支援的專案內絕對路徑。EXCLUSIONS=[] 不解除舊排除或歷史保護；恢復預設授權。
- 自適應限當次已支援方法：重觀察／重定位、補 popup 觀察與座標映射、小步捲動補頁及更新盤點。不可猜 API／快捷鍵、換下載入口、跨列表、重送或修改程式／帳本解鎖。
- 保存實際提交的授權／交接來源；不以示例或工具簿記代替。恢復只限已確認 STOPPED／NOT_SENT 且符合原授權；UNKNOWN 保留且不重送。
- 在入口核對、完整盤點、每本完成／阻塞及最終對帳回報，正常階段交界不等新指令。
- 六類狀態對帳；完整覆蓋且待下載、先前未完成、未知、受保護歷史均為零才報全部完成。
- 已知 UNKNOWN 收斂、FLAT_V1 名稱校正、OS exactly-once 與跨 Session 實測限制保留，不增加新控制器或框架。

## 檢查與交接

- Skill frontmatter 驗證、引用連結、規則一致性、git diff --check。
- 最小回歸：`PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`。
- 合成案例評估下一步、是否詢問、是否重送／越界、證據與停止範圍；不能用字串命中或自評取代 GUI／獨立驗收。
- Owner 另開主 Session 交接至少兩本合格未備份項，驗收一次 Prompt 至最終對帳；跨 Session 恢復另驗，不預填通過。
- 此文件切片可作第一個且最終實作候選；按既有角色契約交回人工安排複雜度審查及獨立驗收，不自動啟動或修補另一角色。
- 持續 Git 授權限同範圍 commit／push／Draft PR，不 merge 或操作真實資料。
