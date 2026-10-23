# Harness 4.7 Issue：角色繞過離線 schema 驗證入口，觸發非預期網路解析

- Issue ID：`HARNESS-4.7-OFFLINE-SCHEMA-RESOLUTION-BYPASS`。
- 提報日期／查閱公開來源日期：2026-10-06，Asia/Taipei。
- 狀態：根因已由本機原始碼、審查者 trace 回報與上游文件交叉支持；本次主線已有離線重審恢復；**持久修補尚未實作**。
- 建議優先度：優先修補共用檢查入口與防復發測試。這是可靠性與離線權限遵守的缺陷，可能涉及網路／隱私邊界；目前不宣稱照片外洩、資料損毀、OpenAI 平台漏洞、CVE 或已確認跨版本回歸。
- 提報目的：交給負責 Harness 設計／維護的高階模型提出受審核修補方案、實作候選與獨立驗收。本文件不是直接修改不可變 release、放寬權限或發佈的授權。

## 1. 給修補模型的精準 prompt

```text
請處理 HARNESS-4.7-OFFLINE-SCHEMA-RESOLUTION-BYPASS。先完整讀此提報與必要本機證據，區分原始事件、重審恢復、較早同類紀錄與研究偏差，再按 Harness 4.7 Global Contract 提出最小修補方案。

已支持的原因：審查角色自行建立沒有本機 Registry 的 Draft202012Validator，繞過現有 contracts.validate_schema 離線入口。jsonschema4.26.0 的預設相容 retrieval callback 會把 task schema 的 https://codex.local/.../$id 與 gate.schema.json 的相對 $ref 組合成網址，並在 deprecation warning 前呼叫 urlopen。原事件在 DNS 階段失敗，沒有取得外部 schema 的回報；DNS 失敗不等於平台封網證據。

請審查正在維護的角色 packet／驗證入口／腳本呼叫路徑，讓它們共用固定離線 API／CLI，完整預載所需 schema，未知引用在本機拒絕，並記錄實際使用入口與固定資源身份。不要只加提示詞、調整警告、開網、改 DNS、換模型或只升級套件。

所有重現與負向測試必須在驗證器建立及執行前攔住 DNS／HTTP。禁止真的查 codex.local 或其他網址。測試需涵蓋正常、漏登引用、巢狀缺失引用、外部引用及角色入口使用情形，分別證明語意結果與零 DNS／HTTP 呼叫；這不等於 OS sandbox 證明。若要加平台強制隔離，另列可用性與受保護決策，不假定本機平台一定提供。

保留目前 4.7.0 release 和所有歷史 evidence；在新的可審查候選中修補，不改已綁定進行中任務的 pin，也不以4.7controller resume4.6。依真實风險處理必要獨立審查與驗收。缺平台證據保持UNKNOWN；不能以HARNESS_VERIFY的release結構PASS宣稱此Issue已修好。

請交付：受影響呼叫點盤點、最小方案與literal paths、實際修補diff、受保護的重現／正負測試及零I/O證據、既有流程相容性、獨立review結果、release採用與回退方案、六個status。對未知前版本與傳輸效果不要補造結論。不要修改LINE產品、config/state或照片；不要改寫原失敗、重設任何預算、commit/push/deploy。
```

## 2. 非技術摘要：發生了什麼

Harness 有一個工具，用來確認 AI 的工作文件符合規則。規則資料在本機，也已有正確的本機檢查入口，但審查者跳過入口，直接啟用工具的預設用法。

當工具需要另一份規則時，沒有找到已登錄的本機資料，就嘗試從網址取得。網址名稱查詢失敗，檢查因此中斷。需要修補的是「入口能被繞過，以及缺資料時仍可能自動查網路」，不是讓那個網址可以連上。

主線改回明確本機入口後，第二次獨立審查已通過；這恢復了這次任務的檢查，不代表已防止其他角色下次重犯。

## 3. 受影響環境與版本證據

| 項目 | 已觀察資料／限制 |
| --- | --- |
| Harness release | 4.7.0，固定 hash `1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d` |
| Release root | `/Users/hsiaojohnny/.codex/harness-releases/4.7.0/1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d` |
| Runtime | `/Users/hsiaojohnny/.codex/harness-runtime/4.7.0/.venv/bin/python -B` |
| 目前版本觀察 | Python3.14.3、jsonschema4.26.0、referencing0.37.0；release lock也固定這兩個套件 |
| 原始事件版本證據 | trace含Python3.14.3路徑；原角色當時沒有另外記錄jsonschema／referencing版本。不把目前版本觀察冒充原程序 telemetry |
| 任務網路政策 | 原 P1／LINE 本機工作 network OFF、browser false |
| 本對話上層執行設定 | danger-full-access、network enabled、approval never；這不是主線網路授權，也不能冒充 OS 封網 |
| 能力未知 | 原程序完整網路封包／DNS傳輸 telemetry；provider／controller admission與OS enforcement |

當前 release 的部分schema仍有「Harness4.6」title殘留；不能用title字樣推斷實際執行版本。以固定release／runtime／task來源為準。

## 4. 預期行為與實際行為

| 面向 | 預期 | 實際證據 |
| --- | --- | --- |
| 本機schema依賴 | 全部從固定release的本機資源解析 | 原角色沒有傳Registry，gate引用進入默認retrieval |
| 缺少資源 | 本機明確拒絕，指出缺哪份 | 嘗試解析 `https://codex.local/schemas/v3/gate.schema.json` |
| network OFF | 執行檢查本身不觸發DNS／HTTP | 原角色回報DNS Errno8；不能將失敗查詢稱為零嘗試 |
| gate／role判定 | 內容審核與執行合規分開 | 原P1 semantic PASS保留，但root admission BLOCKED、未waive |
| 恢復 | 改用明確本機入口，重新獨立驗證 | 第二次P1使用preload+retrieval refusal，正式PASS |
| 歷史 | 留原異常、修正與後續結果 | 原baseline／第一次review與admission維持原bytes；後續另存 |

## 5. 專案 case：相互分開的四組證據

### Case A：本輪 project-binding 第一次 P1

- Task：`TASK-08a0bd6da5c54d03944ce2fb994ff71b`。
- 原P1 run：`2411c72b-bf75-493d-b03d-c29eff242b23`。
- 情境：只審核將來的唯讀專案預檢方案；尚未修改產品、操作LINE或下載。
- 角色自報首次執行裸 `Draft202012Validator(schema).validate(...)`，未供本機Registry。task.schema.json的驗證先失败，尚未到planner.result.json。
- 自報exit1、wall time5.049890375秒，沒有取得remote schema response；主線沒有重跑原失敗。
- 保存的command是角色可讀摘要，不是原始完整tool wire。摘要含壓縮的for-loop，不能拿它當可執行重現腳本。

原trace回報摘要：

```text
jsonschema/validators.py:112 _warn_for_remote_retrieve
  -> urllib.request.urlopen(request)
  -> socket.getaddrinfo
  -> socket.gaierror [Errno 8] nodename nor servname provided, or not known
  -> urllib.error.URLError
  -> referencing.exceptions.Unretrievable:
     https://codex.local/schemas/v3/gate.schema.json
  -> referencing.exceptions.Unresolvable: gate.schema.json
  -> jsonschema.exceptions._WrappedReferencingError
```

證據：[trace回報](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/reviewer-trace-report.json)、[原P1完整結果](harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/plan-review-01.result.json)、[root admission BLOCKED](harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/review-01-admission.json)。

### Case B：本輪恢復與第二次獨立 P1

先保留Case A，再使用 `prepare_review_02.offline_validators`：預載固定schemas/v3與公開report schema，供明確Registry，未知retrieval立即raise。

第二次獨立P1 run `df3cecd8-7c94-4730-89af-431fe55b28e3`，對固定Plan03取得PASS；該review明示零network attempts。root核對完整結果／manifest／schema及exactHandoff。這個PASS不waive Case A，也不代表所有未來角色已被強制使用入口。

證據：[離線helper](harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/prepare_review_02.py)、[第二次P1](harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/plan-review-02.result.json)、[Handoff驗證](harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/handoff-validation.json)。

### Case C：較早另一個4.7 task的同類紀錄

`TASK-91a404524b134364bef6b57f330c1125/tooling-errors.md`保存同一gate URI與DNS Errno8，並記錄改用本機Registry。note SHA256：`46da3174c99f46ccbcd2117f4d78354fc80cabd09f13bc325c6c53e31b1944c6`。其prepare.py明確固定同一4.7.0 release。

這支持「本專案另一個task已發生相似錯誤」。note用legacy RefResolver措辭，但沒有原trace可證實該細節。使用者提到前一版Harness也遇過；目前缺少該前版本的確切pin／trace，不宣稱跨4.6→4.7根因相同。

證據：[較早note](harness-development/rev28-target-observation/TASK-91a404524b134364bef6b57f330c1125/tooling-errors.md)、[該task的prepare.py](harness-development/rev28-target-observation/TASK-91a404524b134364bef6b57f330c1125/prepare.py)。舊generator只讀，不重跑。

### Case D：研究子代理又誤觸一次DNS

使用者指定另一個 GPT-6 Luna／Max 子代理做研究，允許公開來源搜尋與本機只讀。研究scope另明文禁止再次對codex.local發真實DNS／HTTP。

研究者先做有urllib stub的最小驗證，但資料先不符合schema、產生ValidationError，沒有到retrieval；這次stub零呼叫並沒有證明研究假說。之後它在另一個程序無stub執行 `v._resolver.lookup("gate.schema.json")`，又進入真實urlopen／getaddrinfo，DNS Errno8，未收到HTTP response／schema的自報。

自報wall time4.993664313秒；之後clock讀值2026-10-06 05:39:22 UTC，只是after-observation界限，不是精確命令時間。root要求停止、向使用者說明，另存偏差。此事件不能合併到Case A，也不能把研究整體描述成零lookup或完全遵守scope。

證據：[研究scope](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/scope.md)、[偏差紀錄](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/research-dns-deviation.md)、[完整研究](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/research-report.md)。模型與reasoning是實際spawn請求配置，不主張provider-side attestation。

## 6. 根因：工具行為、入口缺口與平台邊界

### 6.1 已由原始碼支持的直接原因

固定 task.schema.json：第3行 `$id` 為 `https://codex.local/schemas/v3/task.schema.json`；第60行 `gate_specs.items.$ref` 為 `gate.schema.json`。引用依 `$id` 組合成上述gate URI，並不因磁碟有同名檔案就自動成為已登錄resource。

本機 jsonschema4.26.0 的 validators.py 第108～134行，default `_REMOTE_WARNING_REGISTRY` 使用 `_warn_for_remote_retrieve`。callback先 `urlopen(request)`，才 `warnings.warn(...)`。預設相容路徑因此可在未登錄引用時發出網路動作，甚至DNS失敗前根本沒發警告。把warning改成error不足以防護。[同版本原始碼](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py#L108-L134)。

### 6.2 Harness已有正確路徑，但本次呼叫繞過了它

固定 `tools/harness/contracts.py:94–120` 的 `validate_schema` 已檢查允許引用、建立明確Registry、以child `$id`及本機key登錄schema_files，再傳入validator。不能據本case斷言「controller的所有檢查都有網路漏洞」。

觀察到的缺口在角色自行建validator與臨時驗證程式。修補需查明現有role packet／CLI是否要求、提供並核對固定入口，以及agent ad-hoc命令如何受約束；目前只證明入口被繞過，尚未完成全release callsite audit。controller result-schema的fragment-only檢查應另外盤點，不應以所有bare constructor都必然联網的說法做全文替換。

### 6.3 任務OFF不等於平台強制封網

本次角色的任務要求OFF；上層執行設定允許網路。這解釋錯誤程式可能走到系統解析，但不豁免角色偏差。未知原程序platform enforcement，不把DNS失敗當sandbox拒絕，不把library Registry當OS隔離。

**主線綜合推論：**一次事件的直接原因是缺Registry的fallback；反覆風險來自標準入口可被role繞過，以及指示限制缺少足夠的執行防護。這需要流程／入口／證據修補；不是已確認的OpenAI服務中斷或模型架構bug。

## 7. 官方與第三方佐證，以及能支持到哪裡

### OpenAI 官方

[Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security) 區分sandbox技術邊界與approval決策，並說明workspace-write網路設定、command proxy與web/app/MCP等不同通道。這支持「任務指示、平台設定及實際執行證據需分開」。不證明本案用到哪個OS隔離，也不是本案bug公告。

[Sandbox](https://learn.chatgpt.com/docs/sandboxing) 說明command會繼承平台sandbox邊界。這支持在具體環境確認實際限制；不能把文件描述的預設行為直接當成本次full-access程序的測量。

### JSON Schema／函式庫官方與維護者原始碼

[JSON Schema structuring](https://json-schema.org/understanding-json-schema/structuring) 說明schema資源識別與引用關係；ID看起來像網址，不保證必須在該處提供下載。

[jsonschema4.26.0引用文件](https://python-jsonschema.readthedocs.io/en/v4.26.0/referencing/) 說明不應假定schema URI可下載，也說明明確Registry的資源登錄／retrieval配置。搭配[同版本validators.py](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py#L108-L134)，可辨別bare validator的相容預設與明確Registry行為。

[referencing0.37.0 Registry原始碼](https://github.com/python-jsonschema/referencing/blob/v0.37.0/referencing/_core.py#L293-L329) 的普通Registry預設拒絕retrieval；與jsonschema給bare validator的相容registry不同。不能從「Registry預設安全」推論「不傳Registry也安全」。

### 第三方第一手案例

[Stack Overflow：How to set up local file references in python-jsonschema document?](https://stackoverflow.com/questions/53968770/how-to-set-up-local-file-references-in-python-jsonschema-document)：使用者的本機 `$ref` 經由urlopen報錯，回答提供預載schema store方法。屬較舊API時期、相似症狀與機制，不能當成4.26.0版本相同事故或本Harness缺陷公告。

[python-jsonschema issue #1454：Validation fails with multi-file schemas with relative file names](https://github.com/python-jsonschema/jsonschema/issues/1454)：使用者明示jsonschema4.26.0、Python3.10，已有Registry卻因相對URI與登錄key對不上得到Unresolvable。它是相鄰但不同原因，支持測完整引用鏈／canonical IDs的必要性，不是本案DNSfallback的獨立同根因重現，也不代表維護者已接受其bug判斷。

未找到足以把本案認定為OpenAI官方已確認缺陷的公告。不能把上述類似案例說成「大家遇過完全同一個Harness bug」。

## 8. 安全重現範本：禁止真實DNS／HTTP

原失敗指令與無stub的resolver lookup只作歷史說明，**不要照抄執行**。以下最小案例保留相同ID／相對引用機制，不含私人專案資料；此提報沒有執行這個新範本，修補者須在受審核檢查內執行並保存實際結果。

```python
from unittest.mock import patch
from urllib.error import URLError
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

BASE = "https://codex.local/schemas/v3/"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
schema = {
    "$schema": DRAFT,
    "$id": BASE + "task.schema.json",
    "type": "object",
    "properties": {"gate": {"$ref": "gate.schema.json"}},
    "required": ["gate"],
}
child = {"$schema": DRAFT, "$id": BASE + "gate.schema.json", "type": "integer"}
http_attempts = []

def block_http(request, *args, **kwargs):
    http_attempts.append(request.full_url)
    raise URLError("TEST_BLOCKED_BEFORE_NETWORK")

def refuse_retrieval(uri):
    raise RuntimeError("LOCAL_RESOURCE_MISSING: " + uri)

# Guard先安裝，之後才建立／執行validator；stub不呼叫原urlopen。
with patch("urllib.request.urlopen", side_effect=block_http), \
     patch("socket.getaddrinfo", side_effect=AssertionError("DNS forbidden")) as dns:
    failed = False
    try:
        Draft202012Validator(schema).validate({"gate": 1})
    except Exception:
        failed = True
    assert failed
    assert http_attempts == [BASE + "gate.schema.json"]
    assert dns.call_count == 0

    # 明確本機Registry成功；如遺漏resource，callback只在本機拒絕。
    registry = Registry(retrieve=refuse_retrieval).with_resources([
        (schema["$id"], Resource.from_contents(schema)),
        (child["$id"], Resource.from_contents(child)),
    ])
    http_attempts.clear()
    Draft202012Validator(schema, registry=registry).validate({"gate": 1})
    assert http_attempts == []
    assert dns.call_count == 0
```

預期第一段攔截一次「打算retrieval」而不做DNS；第二段本機成功且不進HTTP。這證明特定檢查路徑，不證明OS全程序封網。負向版本還需測漏登child／巢狀child／外部URI，確認本機refusal與zero I/O；不能只靠缺required欄位造成早期ValidationError而宣稱已驗到ref。

## 9. 對 Harness 與 LINE 專案的實際影響

| 主體 | 已證影響 | 限制／可能風險 |
| --- | --- | --- |
| Harness | 審查中斷、需要重審；同類事件在其他task與研究再次出現 | 別的角色若繞入口，可能同樣失敗；可解析URI也可能真的連出，需修補而非依賴DNS失敗 |
| 合規／證據 | 原semantic PASS不能等同整個role完全符合OFF；已另記admission BLOCKED | 內容判斷可保留，不可抹去偏差或把所有已證成果一概否定 |
| 隱私／資料 | 沒取得外部schema的角色回報；本case沒有LINE操作／下載／state寫入 | 沒有原OS全流量觀察，不能保證全部external effects已被監測；沒有證據顯示照片外洩 |
| LINE進度 | 原審查需恢復；第二次離線P1已PASS | 七路徑預檢可在正確入口下續作；完整native尚未完成，另有群組證明等既有阻擋 |
| 已備份57張 | source/config/state/Git與照片保存已由既有checks及本輪文件準備核對 | 不因本issue重新下載、不回退state、不放寬duplicate barrier |

最新LINE本機同意已由使用者於2026-10-06取得：[授權receipt](harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/user-consent-20261006.json)。這不是Harness修補授權，也不批準新capture/download；另見[專案交接](20261006_handoff.md)。

## 10. 最小修補方向與不可越界事項

1. 盤點被維護的role檢查入口／packet／ad-hoc instructions，把固定offline API／CLI做成各role實際可用且可稽核的標準。舊completed evidence及故意測bare fallback的負向fixture保持歷史，不能盲目全文取代。
2. 預載完整固定schema依賴，核對canonical ID與內容身分；未知引用立即拒絕、不HTTP／DNS，也不臨時搜尋其他filesystem root。檢查完整graph與所有實際支援引用形式，不擴成不必要的schema重設計。
3. 角色證據記錄實際入口／argv或API、固定release／runtime／schema hash及檢查結果；不要用宣稱role policy就自動當成使用正確入口。
4. 防護測試必須在任何resolver工作前先阻斷網路呼叫；將「可連網址」「本機未登錄」「巢狀缺失」都以本機stub模擬。測試本身不能犯Case D。
5. 平台隔離作為另一層保護：先確認host真的支持哪些限制；若要改執行權限，另列具體方案與必要protected決策。入口修正不能聲稱OS封網；強制封網也不能代替正確文件驗證。
6. 保留immutable4.7.0，建立新修補候選／版本；依風險freeze literal scope、gates、必要獨立review。進行中LINE沿既有pin與已審核helper走，新版採用另明定，不能偷偷換版本。

不採為充分修補：只提示agent小心、只換模型、只把warning當error、修好codex.local DNS、部署schema到網站、開網讓錯誤消失、直接升級套件卻未驗原入口缺口，或降低networkOFF／gate requiredness。

## 11. 驗收標準：逐項證明，不只給「已修好」

| 驗收項目 | 必要證據 |
| --- | --- |
| 標準入口正常 | 固定local schema graph、實際正常task/result validation成功，沒有fallback |
| 漏登根／child／巢狀依賴 | 本機具體refusal；DNS與HTTP spy零呼叫；未早期schema錯誤遮蔽目標引用 |
| 外部與錯URI／key | 本機拒絕；不向網站、DNS、替代root索取；錯誤有足夠定位資訊 |
| 角色入口使用 | 當前supported role packet／維護中腳本的實际path證據；繞路案例可辨別／拒絕，不把一般文字lint當OS強制隔離 |
| 行為與相容性 | 既有v3 task/result有效／無效資料行為維持；必要舊release恢復路徑仍綁自己的pin |
| 證據政策 | 原 Case A／C／D留存，semantic與compliance分開；無隱性waiver或歷史PASS重簽 |
| 安全語意 | OFF任務不被研究／web／其他工具權限擴張；平台不可用則UNKNOWN，不能虛稱sandbox |
| 真正獨立驗收 | reviewer未參與被審diff；讀實際log／hash／scope preservation，符合凍結risk／gate要求 |
| Release交付 | immutable舊release保留；新候選身份、採用條件及回退方案明確；release結構PASS不代替Issue驗收 |

修補者先提出具體gates與scope；上述是提報的目標，不是已執行的PASS。最終按 Global Contract 回報六個status；未達項保留，不能因budget不足自稱完成。

## 12. 附件與仍需確認事項

完整[主線判讀](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/root-judgment.md)、[子代理研究](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/research-report.md)、[root v3研究記錄](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/root-result.json)、[研究archive驗證](harness-development/schema-resolution-research/TASK-ca57c5e4415b487ab07cc0b7df96b855/archive-validation.json)。其中v3形狀驗證PASS不是研究執行合規PASS，root-result也不是原subagent tool wire。

仍未知：前一Harness版本原始pin／trace；原程序完整network telemetry；整個release的callsite覆蓋；host能否提供需要的OS強制限制；修補實作與獨立驗收結果。

本文件沒有把Issue送到GitHub、OpenAI或其他對話，沒有patch／package upgrade／release修改／commit。交給另一個模型時，若它能讀同一工作區，依相對附件索引讀取；若沒有工作區存取，請一併提供研究報告、主線判讀、原trace、Case C note及Case D偏差紀錄，不必提供私人照片或完整state。附件不自動授權修補者讀寫私人備份或全域設定。
