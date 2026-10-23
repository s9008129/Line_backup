# 研究期間新增的 DNS 查詢：分開保存

2026-10-06，研究子代理 `/root/schema_resolution_research` 主動向主線回報：研究中直接呼叫 `Draft202012Validator(...)._resolver.lookup("gate.schema.json")`，該次呼叫沒有 urllib stub，因而觸發真實 `urlopen` 與 `socket.getaddrinfo`；`codex.local` DNS 解析回傳 `gaierror Errno 8`，後續包裝為 `URLError → Unretrievable → Unresolvable`。子代理表示沒有收到 HTTP response 或外部 schema。

這是研究子代理自報的新事件，與原始 P1 的查詢分開。主線沒有該子代理程序的 OS 網路遙測，因此不推論「程序完全無網路」或所有外部效果已被監測。完整命令、trace 與時間若子代理提供，另存於最終研究回報；此處不補造缺失內容。

研究 scope.md 已明文禁止再次對 codex.local 進行真實 DNS/HTTP 查詢。公開來源的唯讀搜尋雖然已獲使用者授權，這次對 codex.local 的無防護重現仍違反研究的具體執行限制。主線收到回報後，立即要求停止所有 resolver／網路重現，僅整理既有證據及來源，並已向使用者說明。

此事件不消耗 LINE 實機、產品實作或下載預算，不豁免原始 P1 的 admission BLOCKED，也不改變第二次獨立 P1 的離線驗證結果。它限制了研究執行合規性的主張；不能將整個研究標為零網路嘗試。

子代理後續提供的精確片段是：先從 pinned task.schema.json 建立 `v = Draft202012Validator(schema)`，再執行 `print("resolver lookup url:", v._resolver.lookup("gate.schema.json").resolver._base_uri)`。該程序沒有 monkeypatch。這是回報的命令片段，不是主線取得的完整 shell wire 或自行重跑的結果。

自報 trace：`urllib.request.urlopen → socket.getaddrinfo → socket.gaierror [Errno 8] nodename nor servname provided, or not known → urllib.error.URLError → referencing.exceptions.Unretrievable('https://codex.local/schemas/v3/gate.schema.json') → referencing.exceptions.Unresolvable('gate.schema.json')`。工具 wall time 為 4.993664313 秒；其後 clock 讀值為 `2026-10-06 05:39:22 UTC`，只能當成回報後的時間界限，不能當成命令的精確起訖。

前一個獨立程序雖然有 patch urllib.request.urlopen，但最小 validation 先產生 ValidationError，callback 呼叫數為零，相關 assertion 失敗。因此那次沒有證明裸 validator 的 retrieval 機制，也沒有證明 probe 本身充分；不可把零 callback 解讀成永久沒有網路風險。
