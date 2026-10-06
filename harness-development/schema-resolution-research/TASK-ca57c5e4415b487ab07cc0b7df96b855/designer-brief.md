# 可交給 Harness 4.7 設計者的回報

我們在使用 Harness 4.7 時，遇到原本應只在本機進行的文件規則檢查，意外查詢網路。查詢失敗，沒有取得外部規則資料，但它違反該角色的離線要求。較早的另一個 4.7 任務也有同類紀錄；使用者提到前一版本遇過，但目前尚未核對前一版本的原始證據。

研究已定位原因：審查角色跳過 Harness 原本提供的離線檢查入口，自己建立預設檢查工具。工具找不到一份被引用的規則時，會自動嘗試從網址取得；網址名稱查詢失敗，才報出這次錯誤。Harness 已有可用的離線入口，本次改用它後的獨立重審已通過；但尚未防止其他角色再次繞過入口。

請先提出範圍清楚的修補方案，再實作。修補應做到：

1. 各角色的文件檢查使用一致、固定的離線入口，且能核對實際使用紀錄。不能只多寫一句「請勿上網」。
2. 必要規則在檢查前全部載入。缺少任何一份時，就在本機停下並說清楚缺哪份；禁止自行向網路索取。
3. 加入能驗出此次問題的測試：正常資料可通過；故意缺少規則、引用外部網址、引用鏈中缺資料，都必須在本機拒絕。測試須先攔住 DNS／HTTP，再確認零呼叫，不能為重現問題而真的發出查詢。
4. 清楚區分「角色被要求離線」與「執行平台已強制封網」。沒有平台證據時，不能宣稱作業系統已阻止網路。若修補需要改平台權限或執行隔離，請把它列為獨立決策。
5. 保留原始異常與修正後重審紀錄。不要把先前失敗改寫成成功，也不要因局部異常就否定所有已證明的專案成果。
6. 在新的修補候選或修訂版本中做變更，保留目前不可變的 4.7 release 與已綁定任務。修補通過必要獨立審查後，再規劃新任務採用；不要直接改舊 release 或悄悄換掉進行中任務的版本。

驗收時，請分別回答：根因是否被修補、各角色是否確實使用正確入口、負向測試是否零 DNS／HTTP、平台封網是否有實際證據，以及既有流程是否仍可使用。未驗證的項目請保持未知，不要只給一個籠統的「已修好」。

目前證據不支持把問題當成 OpenAI 服務故障，也不支持以更換模型、修好 DNS、開啟網路或只升級套件作為充分修正。

## 給設計者的技術定位

- 固定 release：Harness 4.7.0，hash `1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d`。
- 目前 runtime 版本觀察：jsonschema 4.26.0、referencing 0.37.0；原事故當時的套件版本未獨立記錄，不補造 telemetry。
- task schema 的 `$id` 是 `https://codex.local/schemas/v3/task.schema.json`，`gate_specs.items.$ref` 是 `gate.schema.json`。
- 原角色自報使用裸 `Draft202012Validator(schema).validate(...)`，未帶明確 Registry。URI 被組合為 `https://codex.local/schemas/v3/gate.schema.json`。
- 本機 validators.py 與同版本上游原始碼顯示 `_warn_for_remote_retrieve` 在 warnings.warn 前呼叫 urllib.request.urlopen。因此 warning-as-error 不阻止第一次查詢。
- 原角色自報 trace：getaddrinfo／gaierror Errno 8 → URLError → Unretrievable → Unresolvable／_WrappedReferencingError；未取得 HTTP response/schema。沒有原程序的完整 OS 網路紀錄。
- 現有 `tools/harness/contracts.py:validate_schema` 已建立明確本機 Registry；角色裸呼叫繞過了它。主線重審 helper 另明確拒絕未知 retrieval，第二次獨立 P1 通過。
- 研究子代理另一次無防護 resolver probe 也誤觸相同 DNS 查詢。這違反研究的具體限制，已停止且分開保存；不能把整段研究宣稱零網路嘗試。這支持改善執行路徑與防護，不代表可以單靠提示詞消除問題。

參考：[同版 jsonschema 原始碼](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py#L108-L134)、[jsonschema 官方引用說明](https://python-jsonschema.readthedocs.io/en/v4.26.0/referencing/)、[OpenAI 網路與隔離說明](https://learn.chatgpt.com/docs/agent-approvals-security)。

專案內完整證據：[主線判讀](root-judgment.md)、[研究報告](research-report.md)、[研究偏差紀錄](research-dns-deviation.md)、[原 P1 trace 回報](reviewer-trace-report.json)。這些相對連結僅在保留資料夾時有效；將文字交給其他對話時，應一併提供必要文件。此回報尚未傳送給任何其他對話、服務或維護者，也不構成直接修改 Harness 或放寬權限的授權。
