# 來源身分使用者事實（禎／楨）— 2026-09-16

用途：B1 Scoped Blocker 的合法證據路徑之一——「一筆精確保留的使用者事實」——的第一手逐字保存。
本目錄**只保存證據**：是否足以使 `SOURCE_CORRESPONDENCE=CONFIRMED`（同一來源）由接手任務的
plan／review 判定；未判定前維持 `UNRESOLVED`，且**禁止合併或改寫「禎」「楨」字串與 canonical key**。

## 檔案

| 檔案 | Bytes | SHA-256 |
|---|---:|---|
| `source-identity-user-fact.json` | 5530 | `8af8c6fc1459bb77183f81122a23bd10799fb79060fb04f86abb792600e00fa4` |

## 內容摘要（原文以 JSON 為準）

- 提問（2026-09-16 18:57:19）：LINE 所見群組是「禎」還是「楨」？＋既有 57 張是否即該群組 2024/05/13～05/17 的備份？
- 回答（2026-09-16 19:29:21，使用者本人）：「正確是「禎」」（第 1 問）；第 2 問未答。
- 唯讀複核（2026-09-16 19:32:16）：正式 config／state／run_log 之 SHA-256 與既有 57 張（17,924,900 bytes）皆未變動。

## 複驗

```bash
cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
shasum -a 256 evidence/20260916-user-fact/source-identity-user-fact.json
```
