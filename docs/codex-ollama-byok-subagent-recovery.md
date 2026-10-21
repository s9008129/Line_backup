# Codex CLI × Ollama Cloud BYOK 原生子代理：修復紀錄與防復發 Runbook

> **狀態：RESOLVED（已在 Line_backup 正式專案完成有限範圍驗證）**  
> 日期：2026-10-21（Asia/Taipei）  
> 環境：macOS、Codex CLI `0.163.0`、Ollama Cloud、`deepseek-v4.1-flash:1017`  
> 事故：[#19](https://github.com/s9008129/Line_backup/issues/19)  
> 範圍：Native `spawn_agent` 的父子模型繼承、單一 child 推論及原生唯讀 Shell 工具。**不是**所有多代理／MCP／GUI／E2E 功能的全面 PASS。

## 一分鐘版本（下次先讀）

**不要為 Ollama BYOK 子代理指定獨立模型；在有效設定中讓子代理直接繼承 Parent 的 model/provider。**

本專案原有 `.codex/config.toml` 之 `[agents]` 段落包含：

```toml
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "medium"
```

BYOK 啟動時若額外強制 `agents.default_subagent_model="deepseek-v4.1-flash:1017"`，Codex `0.163.0` 會要求此名稱通過 **offline model catalog** 驗證。該 catalog 缺少 DeepSeek，因此即使 Parent 可以正常推論，原生 Child 仍先被 `Unknown model ... for spawn_agent` 阻擋。

已成功的最小修正：**只註解專案中上述兩行，不更改其他設定；BYOK 的 CLI 啟動參數也不再覆寫子代理 model/effort。** 另於 `spawn_agent` 呼叫時不傳 `model`、`reasoning_effort`、`agent_type`，不使用自訂會改模型的 Role。Child 因而繼承 Parent 實際解析的 DeepSeek + `ollama_cloud`。

## 已核實的原因與易混淆事件

1. **第一層（本 Issue 實際阻擋）**：Codex 的 `requested_model.or(agent_default_subagent_model)` 會觸發離線模型目錄精確比對。模型不在目錄中就拒絕建立 Child。這是本機配置解析／目錄驗證問題，不能據此宣稱 Ollama Cloud API 當機。
2. **原始碼的正常繼承能力**：`build_agent_shared_config` 會先複製 Parent 的 `model_info().slug` 及 `turn.provider.info()`。在不發生 Child 模型覆寫時，可避免第一層驗證；已完成實機 PASS。
3. **另一個、未普遍修復的問題**：曾用目錄內的 `gpt-6.1-sol` 模型名稱配 `ollama_cloud` 試建三個 native threads，HTTP 400 `unknown input item type: "additional_tools"`。這是 GPT-name 的 `use_responses_lite=true` metadata 導致的測試結果，**不能**推論所有真正繼承 DeepSeek 的 Child 都必然有相同錯誤；已成功的 DeepSeek Child 沒有此錯。
4. **工具等待是另一個問題**：GitHub MCP mutation / approval 與 Playwright 工具曾卡住；另見 [Issue #20](https://github.com/s9008129/Line_backup/issues/20)。不要拿它們的長等待當作子代理推論逾時。
5. **Codex App 文件工具**：`mcp__codex_apps__codex_document_control_list_document_sessions` 一次唯讀呼叫成功、`isError=false`；回應 `No connected Codex document sessions were found.` 只代表目前沒有連線的文件工作階段，並非錯誤，也不是所有 App 工具都已驗證。

官方程式碼定位：
- [0.163.0 child_config.rs](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/core/src/agent/child_config.rs)
- [0.163.0 client.rs](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/core/src/client.rs)
- 相關尚未一併結案的上游相容性案例：[Codex #39532](https://github.com/openai/codex/issues/39532)、[Codex #31882](https://github.com/openai/codex/issues/31882)。

## 已執行的修復（2026-10-21）

**修改範圍僅為本機專案 `Line_backup/.codex/config.toml` 的兩行；不得據此假定遠端 repo 也已部署同樣設定。** 修復用 Shell Script 已先備份原檔，再註解兩個配置鍵：

```toml
[agents]
# default_subagent_model = "gpt-6-luna"
# default_subagent_reasoning_effort = "medium"
```

備份慣例：`~/.codex/backups/line_backup/config.toml.before-deepseek-fix.*.bak`。現場使用者已收到精確還原指令。不要任意 `git reset` 或 `git checkout`，因現場有大量既有未提交變更。

**BYOK 啟動要點：** 用新 Session，指定 `-m "deepseek-v4.1-flash:1017"`、`model_provider="ollama_cloud"`、`base_url="https://ollama.com/v1"`、`wire_api="responses"`、`env_key="OLLAMA_API_KEY"`、`requires_openai_auth=false`，啟用 `features.multi_agent=true`；本次驗證採 V1（`features.multi_agent_v2=false`）及 `--sandbox read-only`。**不得加** `-c 'agents.default_subagent_model=...'` 或 `-c 'agents.default_subagent_reasoning_effort=...'`。

不要在命令列放入 API Key 原文；憑證從既有 `OLLAMA_API_KEY` 環境變數取得。下列命令只顯示必要設定（不包含金鑰）：

```bash
cd ~/Documents/ChatGPT/Line_backup
codex \
  -m "deepseek-v4.1-flash:1017" \
  -c 'model_provider="ollama_cloud"' \
  -c 'model_providers.ollama_cloud.name="Ollama Cloud"' \
  -c 'model_providers.ollama_cloud.base_url="https://ollama.com/v1"' \
  -c 'model_providers.ollama_cloud.env_key="OLLAMA_API_KEY"' \
  -c 'model_providers.ollama_cloud.wire_api="responses"' \
  -c 'model_providers.ollama_cloud.requires_openai_auth=false' \
  -c 'model_providers.ollama_cloud.supports_websockets=false' \
  -c 'model_providers.ollama_cloud.supports_standalone_web_search=false' \
  -c 'features.multi_agent=true' \
  -c 'features.multi_agent_v2=false' \
  --sandbox read-only
```

啟動後：
1. 使用 `/status`、`/debug-config` 確認實際 Parent model/provider 與設定優先序；不得有 Child model/effort 覆寫。
2. 只呼叫一個 native `spawn_agent`；不傳 `model`、`reasoning_effort` 或 `agent_type`；先做 `17+25` → `CANARY_42` 的唯讀 canary，失敗即停止，不改 GPT/Luna/Sol 退路，也不以外部 `codex exec` 冒充 native child。
3. **不要只信工具回覆的成功字串**，要在該 Session 使用的 `CODEX_HOME/state_5.sqlite` 中唯讀查驗 `threads.id`、`model`、`model_provider`、`cli_version`。例如：
   ```bash
   sqlite3 -readonly "${CODEX_HOME:-$HOME/.codex}/state_5.sqlite" \
     "SELECT id, model, model_provider, cli_version FROM threads WHERE id = '填入實際 child_id';"
   ```
   若 Session 曾以臨時 `CODEX_HOME` 啟動，請使用該 Session 的實際路徑，不能誤查全域 DB；無資料／欄位就回報 `UNVERIFIED`。
4. 基本成功後才允許一個唯讀 Shell tool probe；避免大量輸出（例如 `git status --short` 在本專案曾產生 761 行）與不必要重試。

## 實機驗收紀錄

| Gate | 環境與證據 | 結果 |
|---|---|---|
| A：隔離環境原生 spawn / 推論 | Child `01a15e1b-96db-7a82-b4a7-9ae943f2931d`；`state_5.sqlite` 讀回 `deepseek-v4.1-flash:1017` / `ollama_cloud`；回覆 `CANARY_42` | **PASS** |
| B：正式 `Line_backup` 專案原生 spawn / 推論 | Child `01a15e33-988f-70a2-bc5f-58a4a7fe0ac5`；Parent/Child 皆 `deepseek-v4.1-flash:1017` / `ollama_cloud`；回覆 `CANARY_42` | **PASS** |
| C：正式專案 native tool | Child `01a15e39-aae2-70c3-8c79-f610c317b377`；`exec_command` 三次：`pwd`、`git rev-parse --show-toplevel`、`git status --short`，exit 0；模型及 Provider 讀回一致，`HTTP_ERROR=NONE` | **PASS** |
| D：Codex App 唯讀工具 | `mcp__codex_apps__codex_document_control_list_document_sessions`；`isError=false`，目前 executors 空陣列 | **PASS（限此工具）** |
| E：三個 DeepSeek 原生子代理並行 / Role / MCP / 完整 LINE E2E | 無三 child 並行成功證據；未觸碰正式 LINE GUI | **NOT_RUN** |

以上 A–D 的 PASS 均來自使用者於 2026-10-21 提供的實機 Agent 回報及資料庫唯讀核對；不是 GitHub Actions 的重新執行，亦不代表 E2E 驗收。

## 防復發規則

- **區分 BYOK 與 OpenAI 的不同入口**：DeepSeek Session 直接繼承；若需要原本 Sol Parent → Luna Child，應僅在 **Sol Session 啟動參數** 額外指定 `agents.default_subagent_model="gpt-6-luna"` 與 `agents.default_subagent_reasoning_effort="medium"`；不把這組預設硬塞回所有人共用的專案設定。
- **Codex CLI 更新後先做 canary**：每次版本／模型供應商／Profile 改動後，以「一個 native Child + state DB 身分核對 + 一個唯讀工具」快速驗證，再跑昂貴任務。
- **若遇 `Unknown model`**：先查 project/user/CLI/profile 的有效 `agents.default_subagent_model` 與 Role，再檢查離線 catalog；不要直接認定 BYOK 不支援多代理。
- **若遇 HTTP 400 `additional_tools`**：記錄**實際 child model/provider 和請求 metadata**，不要直接動全域 cache 或抄 GPT metadata 到 DeepSeek；另外立案 provider/request-schema 相容性問題。
- **不做靜默 fallback**：遵循 `BYOK_ONLY_FAIL_CLOSED`。Parent/Child 模型或 Provider 無法證實，停止並回報；不能偷偷派 GPT/Luna/Sol。
- **保持邊界**：不改 Harness V4.8.0、LINE 備份產品、grant、ledger、歷史 VERIFIED；也不將工具驗證當作 LINE E2E 證據。
- **可回退**：若要恢復舊專案行為，先檢查備份與目前 diff，再用當次備份還原 `.codex/config.toml`；但恢復舊 `gpt-6-luna` 預設會使 BYOK 原生繼承再次被覆寫，需重新跑 canary。

## Close-out

**本地操作性問題已修復、單一原生 DeepSeek Child 與原生唯讀工具均有實機 PASS，故專案 Issue #19 可標記 `closed / completed`。**

這不等於上游所有第三方 Provider 問題已修復；三 DeepSeek children 並行、V2、複雜工具/MCP、正式 LINE GUI 自動備份，均未被這次驗收涵蓋。如未來版本再出現同型失敗，引用本文件及 Issue #19，依上述 Gate 比對新版本後另開 regression issue。
