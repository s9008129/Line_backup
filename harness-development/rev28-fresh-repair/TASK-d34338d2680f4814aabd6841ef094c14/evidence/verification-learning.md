# 本輪檢查學到的資訊

baseline-observation：現有 10 tests／0 failure。red-observation：15 tests／25 個 assertion failure，重現接受 process／signing／AX 變更及 mixed／invalid CG。修正後 final focused 21／0，full suite 267／0。

首次 replay exit 1，當時 check.py 的指令紀錄檔名 replay.json 與工具指定報告同名，report 被 command record 覆蓋；該次詳細 failure report 已不可復原。保留 command record／exit 1，不把它當作報告或 PASS。第二次分開檔名，保存 historical-replay-02.json 的 FAIL：nested Swift 使用 compiler 6.3.3，卻取得 CLT SDK 6.4，package manifest 無法編譯。不是移除 gate 的理由。

check.py 後續 command record 改用 .command.json，不再与工具輸出同名。第三次使用與成功 Swift checks 相同的 pinned Python 執行 replay tool：exit 0、20 fixtures、verdict PASS、failures=[]；historical-replay-03.json SHA 為 81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261。不修改全域選擇、不改 Package.swift、不掩蓋兩次既有 FAIL。compiler 6.3.3／Xcode MacOSX26.5.sdk 由當下唯讀 xcrun／Swift 查詢核實；system Python 路徑造成的 SDK 差異以實測失敗與成功記錄為界，不對未觀察的 launcher internals 作推論。

本輪產品修改為一個有證據的 native identity root issue 嘗試；replay 執行環境有三次檢查（第一次細節遺失、第二次取得 SDK 錯配、第三次相同 candidate 通過）。沒有追加產品 retry、重置 download／dispatch 或歷史 composition 額度。
