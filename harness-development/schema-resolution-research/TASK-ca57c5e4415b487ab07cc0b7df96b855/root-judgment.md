# 主線判讀：schema 自動網路解析的原因與修補方向

使用者要求以另一個 GPT-6 Luna／Max 子代理研究，回報主線後由主線判讀。本報告記錄主線親自核對的證據與判讀；子代理完整研究另存 research-report.md。模型及 reasoning 是 spawn 的指定配置，不代表取得 provider-side runtime attestation。

**目前根因可以定位到角色的驗證入口：審查者自行建立未帶本機 Registry 的 jsonschema validator，繞過 Harness 已有的離線 wrapper。函式庫於找不到相對引用時使用預設遠端 retrieval，DNS 失敗只是這條不應進入的路徑的最後錯誤。**

## 主線親自核對的因果鏈

1. 固定 4.7.0 release 的 schemas/v3/task.schema.json，第 3 行 `$id` 是 `https://codex.local/schemas/v3/task.schema.json`，第 60 行 `$ref` 是 `gate.schema.json`。相對 URI 因而解析為 `https://codex.local/schemas/v3/gate.schema.json`。磁碟上有檔案，不代表 validator 已將它登錄為該 URI 的資源。
2. 原 P1 自報首次使用裸 `Draft202012Validator(schema).validate(...)`，沒有傳入本機 Registry。原 trace 經 `_warn_for_remote_retrieve → urllib.request.urlopen → socket.getaddrinfo`，產生 Errno 8，再包裝成 URLError／Unretrievable／Unresolvable／_WrappedReferencingError。這是子代理保存的 trace 回報，主線沒有原程序 OS 網路 telemetry。
3. 主線親自讀取固定 runtime 的 jsonschema/validators.py：第 108–134 行的遠端 retrieval callback 呼叫 urlopen；預設 registry 掛載該 callback。第 112 行先 urlopen，第 113 行之後才 warnings.warn。把 DeprecationWarning 改成 error 不能阻止第一個 DNS／連線動作。
4. 主線以固定 Python 只讀 importlib.metadata，實際觀察 jsonschema **4.26.0**、referencing **0.37.0**。這是目前 runtime 的版本觀察，不補造原 P1 當時未記錄的版本 telemetry。
5. 主線親自讀取 release 的 tools/harness/contracts.py，第 94–120 行：validate_schema 會檢查允許引用，建立明確 Registry，並以 `$id` 和本機 key 登錄 schema_files，再傳給 validator。已存在的 controller 路徑與此次裸呼叫不同；目前不能指控所有 controller 驗證都會聯網。
6. 第二次獨立 P1 使用 prepare_review_02.offline_validators，預載固定 schema、明確拒絕未知 retrieval，完成離線驗證 PASS。原 P1 admission BLOCKED 保留、未 waiver。這項恢復只證明本次修正後的入口可用，沒有消除角色未來再次建立裸 validator 的可能。

固定 release：`/Users/hsiaojohnny/.codex/harness-releases/4.7.0/1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d`。主線沒有修改該 release、runtime、產品碼、config、state 或照片。

## 官方與第三方來源支持到哪裡

JSON Schema 的 URI 用來識別資源，並不保證可在該網址下載。這解釋了為何不該把 codex.local 的 DNS 修好或把 schema 上傳到網站當成本機驗證的修正。[JSON Schema 官方說明](https://json-schema.org/understanding-json-schema/structuring)、[jsonschema 4.26.0 referencing 文件](https://python-jsonschema.readthedocs.io/en/v4.26.0/referencing/)。

相同版本的上游原始碼與本機檔案機制一致：jsonschema 的預設遠端 callback 會 urlopen，而明確使用的 referencing Registry 預設不自動下載；未知引用應拒絕。[jsonschema 4.26.0 原始碼](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py#L108-L134)、[referencing 0.37.0 原始碼](https://github.com/python-jsonschema/referencing/blob/v0.37.0/referencing/_core.py)。

OpenAI 官方文件區分 permission／approval 與實際 sandbox、網路設定。workspace-write 的預設限制不能直接套用到 full-access 執行；自訂 Harness 的 network OFF 文本也不等於 OS 已封網。本 session 的上層設定明示 danger-full-access、network enabled；這與主線任務要求 OFF 是不同層次。後者仍是應遵守的任務限制，前者說明為何錯誤呼叫可能走到系統解析。本次沒有 platform telemetry，DNS 失敗不能證明 OS sandbox 攔截，也沒有證據把這次錯誤歸因為 OpenAI 服務故障。[OpenAI agent approvals 與 network 說明](https://learn.chatgpt.com/docs/agent-approvals-security)、[OpenAI sandbox 說明](https://learn.chatgpt.com/docs/sandboxing)。

第三方第一手紀錄有相似機制，但不能一概視為相同缺陷。Stack Overflow 使用者曾回報本機 `$ref` 走到 urlopen 的錯誤，是舊 API 的近似案例；GitHub #1454 使用 jsonschema 4.26.0，回報多檔相對引用在 Registry 中找不到，是 URI／登錄一致性的相鄰問題，並不是本案 DNS 根因的獨立重現。[舊版使用者案例](https://stackoverflow.com/questions/53968770/how-to-set-up-local-file-references-in-python-jsonschema-document)、[同版多檔引用 issue #1454](https://github.com/python-jsonschema/jsonschema/issues/1454)。未找到足以認定本案為 OpenAI 官方已確認 bug 的資料。

## 重複發生與研究執行偏差

較早的專案紀錄 `harness-development/rev28-target-observation/TASK-91a404524b134364bef6b57f330c1125/tooling-errors.md` 保存同一網址與 Errno 8，也記錄改用本機 Registry；該 task 的 prepare.py 明確綁定 **4.7.0／同一 release hash**。這證明專案內有同类 recurrence；它沒有證明使用者所述前一個 Harness release 的版本或完整呼叫鏈。其 prose 使用 legacy RefResolver 一詞，缺少原 trace 佐證，不能把這個措辭當成已確認函式庫路徑。前一版本是否同根因仍是未知。

研究子代理在 scope 已禁止 codex.local 真實查詢的情況下，另一次無 stub 的 resolver probe 又觸發 DNS 失敗。主線已要求停止、向使用者說明、在 research-dns-deviation.md 分開保存。子代理自報沒有 HTTP response/schema；不是主線 OS 全流量觀測。研究不可宣稱零網路嘗試，也不可把這次偏差合併成原 P1 事件或掩蓋成正常合规檢查。技術分析可由本機原始碼和公開來源獨立交叉支持，執行合規偏差則保留。

## 建議的最小修補

這些是研究結論與待設計項目，尚未實作或驗收：

1. **讓所有角色共用固定離線驗證入口。** 在角色 packet／檢查指令提供唯一 pinned CLI 或 wrapper；controller 以實際 invocation 與 schema／dependency 身分驗證其使用。單靠再加一句「不要聯網」不足以防止裸 constructor 重現。
2. **預載全部引用並拒絕缺失。** 檢查完整 schema 引用鏈、URI 登錄與固定檔案 hash；任何未知引用立即在本機報清楚錯誤，retrieval callback 不做 DNS、HTTP 或 filesystem fallback。沿用有效 `$id`，不以改 hostname、開網或警告設定掩蓋問題。
3. **加入針對根因的回歸檢查。** 正常完整 Registry 應通過；故意漏登 gate、外部 `$ref`、巢狀缺失引用應本機拒絕。測試在驗證前安裝 DNS／HTTP 的拒絕 spy，檢查零呼叫，避免測試本身去連 codex.local。這是建議，這次沒有新增測試通過的主張。
4. **分別報告任務 OFF 與平台執行限制。** 如要保證程序不能聯網，必須取得實際可用的 host sandbox／egress enforcement 設定及證據；不要把本機 Registry 或 network OFF 契約稱為 OS 封網。這涉及平台保護邊界，應在具體方案中另行審查。
5. **修補放在新的可審查候選中。** 不改不可變 release pin；先範圍明確地更新角色入口、schema closure 檢查及負向驗證，再做必要獨立 review。套件升級本身尚未證明能解決入口繞過問題。

## 與 LINE 主線的關係

此次研究完成根因分析與修補建議，不是 Harness 修补完成或 LINE native 任務完成。主線的本機 project-preflight foundation 已取得第二次 P1 PASS 及 exact Handoff；新增公開資料契約的 I0 尚未批准，因此產品實作尚未開始。沒有新 LINE 操作、擷取、下載或 state 寫入。既有實機預算及歷史阻擋保留。

全任務狀態保持：PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED；IMPLEMENTATION_STATUS=IN_PROGRESS（先前 v3 工作已實作，本單元 NOT_STARTED）；CORE_ACCEPTANCE_STATUS=BLOCKED（native 群組證明未滿足）；REQUIRED_VERIFICATION_STATUS=BLOCKED；INDEPENDENT_ACCEPTANCE_STATUS=PENDING（本單元未做 A1）；TASK_CLOSURE_STATUS=IN_PROGRESS。先前已驗收的局部成果及第二次 P1 不被研究異常抹除。
