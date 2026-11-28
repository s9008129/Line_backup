# 問題提報單：LINE 記事本 pending naming 被錯誤投影為 LOCAL_CHANGED

## 文件狀態

- 狀態：`OPEN`；根因具高信心，仍待 `planner` 以唯讀方式獨立核對。
- 嚴重度：`HIGH`。第一個媒體已完成，但第二個媒體下載後無法完成命名發布；後續派送被全局 blocker 停止。
- 目標列表：`嘉義縣稅Soc資安討論`
- 專案：`/Users/hsiaojohnny/dev/Line_backup`
- Git 分支：`feature/line-notes-media`
- Git HEAD：`a5c3726cf954d8efefb2251778c50d4b2cae371b`
- 觀測到的 `notes.py` SHA-256：`fcd5bd4196e9963d93ca94b6025ea2c1065ff9202373afd3311b3a8a8dc4ea00`
- 提報單建立時間：`2026-11-15T23:12:40+08:00`
- 提報單路徑：`.local/line-backup/tasks/20261115-line-notes-daily-backup/issue-report-line-notes-pending-naming-20261115.md`

## 摘要

本次日常備份已完成單一列表的完整卡片盤點，共 4 篇貼文、8 個媒體項目。P1 為純文字 `NO_MEDIA`；P2 有 2 個媒體；P3 有 1 個媒體；P4 有 5 個媒體。

P2/M1 已成功下載、通過 `download-check` 的 `DOWNLOAD_ONLY` 基本檢查，並在 ledger sequence 23 建立 completion。失敗前的最新 summary 顯示它為 `COMPLETED / VERIFIED_PRESENT`。

P2/M2 已成功下載到精確的空白 staging，staging 內只有一個 regular file，大小 719764 bytes、SHA-256 `55122dd946a4feda1f00434e336952d448f33783a07215044581e6dba3467e49`。`outcome=DOWNLOAD_FINISHED` 在 sequence 25 成功寫入；`download-check` 也在 sequence 26 寫入 `PASS / PHOTO / image/jpeg / DOWNLOAD_ONLY`，並在 sequence 27 寫入 target 為 `media_002.jpg` 的 publish plan。

但是，同一次 `download-check` 在完成 verification 與 publish plan 之後，`_execute_publish()` 再次呼叫完成目錄可用性檢查。該檢查把尚未發布的 plan target `media_002.jpg` 加入同一個已完成貼文目錄的 `expected_names`，而目錄此刻實際只有 `media_001.jpg`，因此產生 `COMPLETED_DIRECTORY_CONTENTS_CHANGED`。錯誤被投影成已完成媒體 P2/M1 的 `LOCAL_CHANGED`，最後回傳：

```json
{"status":"REFUSED","reason":"COMPLETED_FILES_CHANGED_NO_REDOWNLOAD","dispatch_authorized":false}
```

`download-check` capture 的 `child_exit=4`。之後執行 `resume` 也得到相同結果與 `child_exit=4`，且沒有新增任何 ledger event。

目前不是 P2/M1 檔案損壞，也不是 P2/M2 下載失敗。高信心根因是完成目錄可用性投影把「pending publish plan 的目標」誤當成「必須已經存在的 completed target」，形成自我阻塞。

## 授權、邊界與本次唯讀調查

- 使用者提供的是日常正式備份授權及當次 LINE 前景交接；實際 GUI 只操作指定的 `嘉義縣稅Soc資安討論` 記事本列表。
- 本提報單的後續調查只做檔案、ledger、capture、observation 與程式碼的唯讀核對。
- 本次唯讀調查沒有再點下載控制、沒有再確認 chooser、沒有重下、沒有建立新的 intent 或 attempt、沒有修改 ledger／completion／staging／證據檔。
- 本提報單不把 `recovery_authorized=true`、既有 ledger 或既有 staging 當成新的 GUI 下載授權。
- 在 P2/M2 pending naming 未解前，P3、P4 及其他尚未處理媒體不得派送。

## Skill 入口與參考文件

實際讀取的入口與 references：

- `.agents/skills/line-notes-agent-cua/SKILL.md`
  - SHA-256：`00770ecb97e8d22dcc28f42ada0df691060fafd6a08aa61b4703ca26091abb33`
- `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`
  - SHA-256：`fb5636a21a194b0e9f1115eff97560b26080955de43faf2a1948f08cc3102f5c`
- `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md`
  - SHA-256：`55d8f36ad4ce06c17be3a9eeb7a2b785b475bff4f94571dbda110cc5765bf423`
- `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`
  - SHA-256：`5609bde4ec9a9f6a9a9b5c99da50c40badb3cf2d1e9921b086fcb206a7355c31`
- `.agents/skills/line-notes-agent-cua/references/evidence-template.md`
  - SHA-256：`8a22ad1a8fd5d0fbfde173a493336aa02328886af0e59b32af8cad18c82e3869`

Skill 路由要求先查永久帳本與 active hint，再核對入口；新列表在無完整歷史或候選歧義時初始化，既有列表綁定原帳本；掃描期間先完成卡片台帳與頁面雙向對帳，再逐篇細盤與下載。

## 入口、身分與歷史核對

### 永久帳本與 active hint

- 以 `notes lists --collection /Users/hsiaojohnny/dev/Line_backup/notes-backup-records` 讀取永久索引，exit 0。
- 當時列出 6 個既有 ledger；沒有 ledger 符合本次計算出的 `list_key`。
- active hint `active-notes-task.json` 指向 `local_list_id 34c304c9-0e0f-4456-be78-d7d2b4ab3cd8`，但其 records directory 不存在。此 hint 被保存為 missing hint，沒有被當成空 ledger，也沒有被當成「沒有歷史」的證明。
- 因此本次在沒有完整歷史匹配、沒有 damaged/ambiguous ledger 的情況下初始化一個新 ledger，並保存 `recovery_authorized=true`。這不是既有 ledger 的手動補寫。

### 當次畫面與列表身分

- App bundle：`jp.naver.line.mac`
- 畫面角色：`NOTES LIST`
- 畫面 tab：`記事本` 被選取，不是相簿。
- 顯示上下文：`嘉義縣稅Soc資安討論`
- 列表 `list_key`：`53d7661a60a93263f8b9d1ba27cd3c3b32f7a2aa3b44e94fc912af9fe315dac7`
- 持久化帳本根：`/Users/hsiaojohnny/dev/Line_backup/notes-backup-records/db7005a0-3124-4e42-ac84-19dbb036b8eb`
- `session_id`：`session-158cf036-8666-4cb5-9a7e-af7133968028`
- `scan_id`：`2e07093e2ab546b983ad01ac0cbd916c`
- 列表目錄：`/Users/hsiaojohnny/dev/Line_backup/backup/記事本/嘉義縣稅Soc資安討論_53d7661a`
- destination root：`/Users/hsiaojohnny/dev/Line_backup/backup/記事本`
- 私有 task directory：`/Users/hsiaojohnny/dev/Line_backup/.local/line-backup/tasks/20261115-line-notes-daily-backup`

入口 observation `obs-20261115-001` 的 AX 較稀疏，未直接暴露標題與卡片文字；列表角色與顯示名稱由同一次 CUA 的原生截圖與 AX 聯合核對，並非只靠單一文字或舊畫面。

## 完整列表盤點

### 頁面與卡片對帳

來源卡片台帳的 ordered union 為 P1 → P2 → P3 → P4，共 4 個唯一 post key。四個 page 均由同一來源卡片的完整或部分畫面雙向對應，跨頁 overlap 為 P2、P3、P4；頂端與底端另有同卡重核。

- page 0：`obs-003`，另有頂端 `obs-002`；rows = P1、P2；`PASS_TO_SUBMIT`
- page 1：`obs-004`；rows = P2、P3；overlap = P2；`PASS_TO_SUBMIT`
- page 2：`obs-005`；rows = P3、P4；overlap = P3；`PASS_TO_SUBMIT`
- page 3：`obs-006/007/008`；row = P4；overlap = P4；`PASS_TO_SUBMIT`；bottom reached
- 待解來源片段：0
- missing or duplicate：0
- `scan_coverage=COMPLETE`

### 四篇貼文

| 編號 | 貼文身分 | post_key | 媒體數 | 狀態 |
|---|---|---|---:|---|
| P1 | `post|author=英銘|title=20261022 SOC第三季季報備忘|shown=10月20日 下午 2:45` | `1c7704cefa3d5118197ee099761d5bee37358732c6d0cbd709c53a6ccadac06a` | 0 | `NO_MEDIA` |
| P2 | `post|author=英銘|title=20260728 SOC 會後追蹤事項|shown=7月28日 下午 3:26` | `1cf01ee25b017cdd770adebe4bef8e8ce31a75370a2706a847f89173d3d64fda` | 2 | `MEDIA` |
| P3 | `post|author=英銘|title=20260728 SOC 會議資料備忘|shown=7月22日 下午 3:30` | `271eed6bdf01912fb48cb6ca81869e150afd88c7eae9a88e5d6ed5958604453e` | 1 | `MEDIA` |
| P4 | `post|author=英銘|title=20250422 PA setting mail server dos protect|shown=2025.4.22 下午 4:25` | `8d87d24a05b830f2aebe7fb447ec1c771f423190d671a6f76857cc5cc6f6381a` | 5 | `MEDIA` |

### 八個媒體

| 貼文/序 | media_key | visual identity | 目前狀態 |
|---|---|---|---|
| P2/M1 | `3bd78d2282b740691328787759b0d5053f1c20224556dd63099d7ec01a6556f0` | `media|visible=4660 連線規則總覽|viewer=1/2` | `COMPLETED`；summary 因本 bug 顯示 `LOCAL_CHANGED` |
| P2/M2 | `469dad4ffbcc2f34badab74b430abaaaddff55b7cc92c3ea74f9f402ca764ee9` | `media|visible=流量記錄 4660|viewer=2/2` | `PENDING`；staging 已完成下載，pending naming |
| P3/M1 | `d2394c01a7c667eadfdc93267a444b33eceb932e29aadb81aa8b500419f7b5c3` | `media|visible=本季工作事項 表格|viewer=1/1` | `PENDING`；尚未下載 |
| P4/M1 | `100a4693355e80890cc5bb9162bb52f330966ca85998fe78a7eec9c68d2d26e0` | `media|visible=DoS 防護設定檔|viewer=1/5` | `PENDING`；尚未下載 |
| P4/M2 | `7ff43aa99fd0d0976ebc2af59577ab374f1418864ed051596192509190491916` | `media|visible=DoS 規則 選項保護|viewer=2/5` | `PENDING`；尚未下載 |
| P4/M3 | `524bb5b52dba5d31396dc00f4589026fc0ab68d10d0a41bb1313f4120091f3f0` | `media|visible=DoS 規則 來源|viewer=3/5` | `PENDING`；尚未下載 |
| P4/M4 | `afe1b4d37c804da2907f373fdcde77be94ed44443e358769f4539b08d1f878af` | `media|visible=DoS 規則 一般|viewer=4/5` | `PENDING`；尚未下載 |
| P4/M5 | `bee880b11c249916ddaab06f3a8179b153a331c3ab111d78db0ee7c7598b6852` | `media|visible=DoS 規則 目的地 GSN_DMZ_Nospam_H-61.60.23.68|viewer=5/5` | `PENDING`；尚未下載 |

## Skill 觸發下的工具操作時序

下列時間為 capture request 記錄的 UTC；本機顯示為 Asia/Taipei。命令都以專案指定的 Python 3.9 執行 `python -B -m line_backup_batch.notes`，capture 會保存 request、stdout、stderr、result 與 complete。

### 1. 歷史查詢、初始化與綁定

| UTC 時間 | 工具/動作 | 主要識別 | 結果 |
|---|---|---|---|
| `2026-11-15T14:04:05Z` | `notes lists --collection .../notes-backup-records` | 6 個 ledger | exit 0；無 list key 匹配 |
| `2026-11-15T14:04:39Z` | `notes list-key ...` | 視覺身分與上下文 | exit 0；得到 `53d7661a...` |
| `2026-11-15T14:05:03Z` | `notes evidence-pack` | `init-statement.txt`、`obs-001` | exit 0；bundle `evidence/init-001` |
| `2026-11-15T14:05:12Z` | `notes init ... --recovery-authorized` | photo root、history scope | exit 0；`local_list_id=db7005a0-...` |
| `2026-11-15T14:05:32Z` | `notes evidence-pack` | `bind-statement.txt`、`obs-001` | exit 0；bundle `evidence/bind-001` |
| `2026-11-15T14:05:41Z` | `notes bind` | `session-158cf036-...` | exit 0 |
| `2026-11-15T14:05:50Z` | `notes scan start` | `scan_id=2e07093e...` | exit 0 |

### 2. 完整卡片盤點與掃描封存

- 使用 `observe` 與 `page` 讀回保存 page 0-3，ledger sequences 4-7。
- page 0 的 CLI capture：`captures/notes-capture-bfcdcf9c974e4d67a5536d9646d4a659`
- page 1：`captures/notes-capture-b988fe20e8394572b98a97f6ff2238f5`
- page 2：`captures/notes-capture-9d32ca46925546c6b0edf953dca17960`
- page 3：`captures/notes-capture-d9037e62acf441d790f57561966e250d`
- `2026-11-15T14:14:09Z`：`notes scan finish`，exit 0，scan `2e07093e...` 為 `COMPLETE`。
- 來源卡片 finish 前已重新核對頂端、底端、四頁原件與 ordered union；不是用單一捲軸值或媒體預覽變化宣稱到底。

### 3. P1-P4 逐篇細盤

- 逐篇使用 `observe post`、`post`、`observe media`、`media` 保存貼文與媒體明細。
- 四篇均有 post detail；P1 的 media inventory 為空，記為 `NO_MEDIA`。
- P2/P3/P4 的媒體明細保存於 ledger，total = 8。

### 4. P2/M1 成功路徑

- `2026-11-15T14:33:57Z`：`notes intent`，media key `3bd78d22...`，得到 attempt `734ae5c7ec9a48ec9f1b98c49329b4ec`，空白 staging 為 `.line-notes-incoming-94635695e649432db5d2cc3e108f3c99`，exit 0。
- GUI 入口：LINE notes media viewer `英銘(1/2)`；控制擁有者是 LINE notes viewer toolbar。
- observations：`obs-20261115-039` 至 `obs-20261115-044`。
- 下載控制呼叫：`download-p2-media1-734ae5c7ec9a48ec9f1b98c49329b4ec-001`，次數 1。
- chooser：看到 LINE `儲存` save panel；由 Go to Folder 設到精確 staging；確認前 readback 與目的地一致；未見 Save All。
- chooser 最終確認：`chooser-p2-media1-confirm-001`，次數 1。
- 結果：`obs-044` 顯示「下載完畢。」；staging 只有 `LINE_NOTE_261115_1.jpg`，350654 bytes，SHA-256 `de931cf3ab56931b82ba8f8d66515e6b3bc846aef807967058e49a4505b37496`。
- `2026-11-15T14:40:02Z`：`notes evidence-pack` 生成 `evidence/outcome-P2-M1-v1`。
- `2026-11-15T14:40:16Z`：`notes outcome` 寫入 sequence 17，`DOWNLOAD_FINISHED`，exit 0。
- `2026-11-15T14:40:26Z`：`notes download-check`，exit 0；sequence 18 的 verification 為 `PASS / PHOTO / image/jpeg / DOWNLOAD_ONLY`，並建立 sequence 19 的 plan、20-22 的 publish-progress、23 的 completion。
- completion target：`.../7月28日 下午 3 26_1cf01ee2/media_001.jpg`，350654 bytes，SHA-256 與 source 相同。
- `2026-11-15T14:40:44Z`：summary 顯示 P2/M1 `COMPLETED / VERIFIED_PRESENT`，P2/M2 `PENDING`，`unresolved_attempts=[]`，`dispatch_blockers=[]`。

### 5. P2/M2 下載與 pending naming

- `2026-11-15T14:43:59Z`：`notes intent`，media key `469dad4f...`，得到 attempt `8aad192df9ec49d7b9cda3b38258c14d`，空白 staging 為 `.line-notes-incoming-3d736d0300f24817853812120ae96b05`，exit 0。
- GUI 入口：LINE notes media viewer `英銘(2/2)`；observations `obs-20261115-049` 至 `obs-20261115-054`。
- 下載控制呼叫：`download-p2-media2-8aad192df9ec49d7b9cda3b38258c14d-001`，次數 1。
- `obs-050`：LINE `儲存` save panel；AX 顯示 `save-panel`、`saveAsNameTextField`、`OKButton`、`CancelButton`，沒有 Save All。
- `obs-051`：Go to Folder。
- `obs-052`：PathTextField 讀回精確 staging 路徑。
- `obs-053`：save panel 的位置欄顯示 `.line-notes-incoming-3d736d0300f24817853812120ae96b05`，save as 名稱為 `LINE_NOTE_261115_1`。
- chooser 最終確認：`chooser-p2-media2-confirm-001`，次數 1。
- `obs-054`：save panel 關閉，回到 `英銘(2/2)` viewer。
- staging 結果：只有一個 regular file，非 symlink，719764 bytes，SHA-256 `55122dd946a4feda1f00434e336952d448f33783a07215044581e6dba3467e49`；原始 stat 與 sequence 26 manifest 完全一致。
- `2026-11-15T14:49:21Z`：`notes evidence-pack` 生成 `evidence/outcome-P2-M2-v1`；bundle SHA-256 `ffe83f7e15983ce74d4c8b0d95ef0a1334e9d04b01f34b4365bcb158a1664592`。
- `2026-11-15T14:49:32Z`：`notes outcome` 寫入 sequence 25，`DOWNLOAD_FINISHED`，exit 0。

### 6. `download-check` 失敗

命令：

```sh
notes download-check \
  --records-root /Users/hsiaojohnny/dev/Line_backup/notes-backup-records/db7005a0-3124-4e42-ac84-19dbb036b8eb \
  --session-id session-158cf036-8666-4cb5-9a7e-af7133968028 \
  --attempt-id 8aad192df9ec49d7b9cda3b38258c14d
```

- Capture：`runs/notes-capture-535c15db41ad4f9e87501b28cc3f5555`
- 開始：`2026-11-15T14:49:43.575552Z`
- 結束：`2026-11-15T14:49:44.084128Z`
- `child_exit=4`、`outer_exit=4`、`status=CHILD_FINISHED`
- stdout 恰好是：

```json
{"status":"REFUSED","reason":"COMPLETED_FILES_CHANGED_NO_REDOWNLOAD","dispatch_authorized":false}
```

- stderr 為空。
- 此次命令在拒絕前已追加：
  - sequence 26 verification，`PASS / PHOTO / image/jpeg / DOWNLOAD_ONLY`
  - sequence 27 publish-plan，transaction `01633657e2f140979513d73b12a37011`，target `media_002.jpg`，verification sequence 26
- 沒有 publish-progress、completion 或任何新 outcome。

### 7. `resume` 失敗且未新增事件

- 先查 `resume --help`，exit 0。
- 再執行 `notes resume --records-root ...`，capture `runs/notes-capture-21da05a557b7478d90413c33a1c68070`。
- 開始：`2026-11-15T14:52:18.419536Z`
- `child_exit=4`、`outer_exit=4`
- stdout 與 `download-check` 完全相同：

```json
{"status":"REFUSED","reason":"COMPLETED_FILES_CHANGED_NO_REDOWNLOAD","dispatch_authorized":false}
```

- ledger 仍停在 sequence 27；沒有新增 event。

## Ledger 時序

### P2/M1

| sequence | kind | 關鍵內容 |
|---:|---|---|
| 16 | intent | attempt `734ae5c7...`；staging `.line-notes-incoming-94635695...` |
| 17 | outcome | `DOWNLOAD_FINISHED` |
| 18 | verification | `PASS / PHOTO / image/jpeg / DOWNLOAD_ONLY` |
| 19 | publish-plan | transaction `44c9cb9e...`；target `media_001.jpg` |
| 20 | publish-progress | `DIRECTORY_READY` |
| 21 | publish-progress | `FILE_LINKED` |
| 22 | publish-progress | `SOURCE_REMOVED` |
| 23 | completion | `media_001.jpg`；350654 bytes；hash 與 source 相同 |

### P2/M2

| sequence | kind | 關鍵內容 |
|---:|---|---|
| 24 | intent | attempt `8aad192d...`；staging `.line-notes-incoming-3d736d...`；identity `UNCLASSIFIED` |
| 25 | outcome | `DOWNLOAD_FINISHED`；evidence bundle `ffe83f7e...` |
| 26 | verification | `PASS / PHOTO / image/jpeg / DOWNLOAD_ONLY`；manifest 719764 bytes；SHA-256 `55122dd9...` |
| 27 | publish-plan | transaction `01633657...`；target `media_002.jpg`；target directory existed；尚無 progress/completion |

sequence 27 的 `previous_sha256` 是 `9c937d0fca6e1e5f0852cf46d9a9adb6dd2dd02b1f28180217558405c433072b`。這表示 ledger 已形成可接續的 pending naming transaction，但尚未完成 publish。

## GUI 證據

### P2/M2 關鍵 observations

- `obs-20261115-050`
  - AX window：`儲存`
  - app：LINE
  - save panel：`save-panel`
  - save as name：`LINE_NOTE_261115_1`
  - buttons：`OKButton`、`CancelButton`
  - 未見 `Save All`
- `obs-20261115-051`
  - GoToWindow
  - PathTextField 值為精確 staging 路徑
- `obs-20261115-052`
  - PathTextField 值為 `/Users/hsiaojohnny/dev/Line_backup/backup/記事本/嘉義縣稅Soc資安討論_53d7661a/.line-notes-incoming-3d736d0300f24817853812120ae96b05`
  - 前往列也顯示同一路徑
- `obs-20261115-053`
  - save panel 位置欄：`.line-notes-incoming-3d736d0300f24817853812120ae96b05`
  - 上一層為 `記事本`，再上一層為列表目錄
- `obs-20261115-054`
  - 回到 LINE viewer `英銘(2/2)`
  - save panel 已關閉

### 輸入次數與未知性

- `download-p2-media2-...-001.diagnostic.json` 記錄 `status=INVOKED`，`download_control_call_count=1`。
- `chooser-p2-media2-confirm-001.diagnostic.json` 記錄 `status=INVOKED`，`chooser_confirm_call_count=1`。
- 原始 CUA 回傳為 `UNDEFINED`；`native_dispatched_target` 與 `receipt_target_match` 都是 `UNKNOWN`；receipt 不是 OS event trace。
- 這是輔助工具的限制，不是本次 bug 的根因；本次錯誤是在 CLI ledger 內部發生。

## 本機檔案對帳

### P2/M1 完成目錄

路徑：

```text
/Users/hsiaojohnny/dev/Line_backup/backup/記事本/嘉義縣稅Soc資安討論_53d7661a/7月28日 下午 3 26_1cf01ee2
```

目前只有：

```text
media_001.jpg
```

觀測到的 identity：

- regular file
- device `16777233`
- inode `151151796`
- nlink `1`
- size `350654`
- mtime_ns `1794753379906751901`
- ctime_ns `1794753627177904825`
- SHA-256 `de931cf3ab56931b82ba8f8d66515e6b3bc846aef807967058e49a4505b37496`

這些值與 sequence 23 completion 完全吻合。沒有缺 completed 檔、沒有額外檔、沒有 symlink、沒有 hash/stat/inode 漂移。

### P2/M2 staging

路徑：

```text
/Users/hsiaojohnny/dev/Line_backup/backup/記事本/嘉義縣稅Soc資安討論_53d7661a/.line-notes-incoming-3d736d0300f24817853812120ae96b05
```

目前只有：

```text
LINE_NOTE_261115_1.jpg
```

觀測到的 identity：

- regular file
- device `16777233`
- inode `151154371`
- nlink `1`
- size `719764`
- mtime_ns `1794754036402179690`
- ctime_ns `1794754036402179690`
- SHA-256 `55122dd946a4feda1f00434e336952d448f33783a07215044581e6dba3467e49`

這與 sequence 26 manifest 完全一致。`media_002.jpg` 尚未建立，亦無 completion；這符合 pending publish plan 的狀態，不是損壞狀態。

## 失敗訊息與 summary 投影

### 失敗前的 summary

Capture：`runs/notes-capture-04cc097987d84e36a1fa20bf17cc2585`

```text
status_counts = COMPLETED:1, PENDING:7, 其他:0
local_counts  = VERIFIED_PRESENT:1, LOCAL_CHANGED:0, NOT_APPLICABLE:7
unresolved_attempts = []
dispatch_blockers = []
all_known_media_complete = false
```

### 失敗後的 summary

Capture：`runs/notes-capture-2051b7884e724fc9947c238476b3e578`

```text
scan_coverage = COMPLETE
status_counts = COMPLETED:1, PENDING:7, 其他:0
local_counts  = VERIFIED_PRESENT:0, LOCAL_CHANGED:1, NOT_APPLICABLE:7
unresolved_attempts = P2/M2, DOWNLOAD_FINISHED, pending_naming=true, scan_binding_match=true
dispatch_blockers = COMPLETED_FILES_CHANGED, PENDING_NAMING, VERIFY_REQUIRED
all_known_media_complete = false
```

P2/M1 的 status 仍是 `COMPLETED`，但其 `local_files` 從 `VERIFIED_PRESENT` 變成 `LOCAL_CHANGED`。這是 projection 的附帶效果，不是 completion 事實被改寫，也不是原始檔案改變。

## 程式路徑與根因鏈

### 相關位置

- `src/line_backup_batch/notes.py:4406-4494`：`_completion_availability`
  - `4421-4425`：讀取 pending publish plans，建立 `plan_names`
  - `4456`：`expected_names |= plan_names.get(directory_string, set())`
  - `4457`：再加入 active names
  - `4458-4464`：要求 `actual_names == expected_names`
  - `4484-4487`：任何 `NotesError/DailyError/OSError/ValueError` 都把該目錄所有完成媒體投影成 `LOCAL_CHANGED`
- `src/line_backup_batch/notes.py:4502-4507`：`_assert_no_local_changed`
- `src/line_backup_batch/notes.py:5918-5952`：`_append_publish_plan`
  - `5934-5935`：建立 plan 時要求 target path 尚不存在
  - `5951-5952`：先 append plan，再在下一個步驟執行 publish
- `src/line_backup_batch/notes.py:5973-5990`：`_target_names_for_directory`，將 completion、publish-plan、restart-copy-plan、restart-candidate 的 target 名稱合併
- `src/line_backup_batch/notes.py:6006-6027`：`_ensure_publish_directory`，在 publish 路徑另有一套 allowed-target 檢查
- `src/line_backup_batch/notes.py:6063-6079`：`_execute_publish` 開頭對 BASIC verification 再次呼叫 `_require_download_settlement`
- `src/line_backup_batch/notes.py:6265-6282`：`_require_download_settlement`，最後呼叫 `_assert_no_local_changed`
- `src/line_backup_batch/notes.py:6684-6687`：`download_check` 只是 `verify(download_only=True)`
- `src/line_backup_batch/notes.py:6708-6713`：verify 一開始先做 settlement 檢查
- `src/line_backup_batch/notes.py:6778-6789`：append verification 後 append publish-plan，再呼叫 `_execute_publish`
- `src/line_backup_batch/notes.py:6791-6819`：resume 對 BASIC verification 也先做 settlement 檢查

### 精確時序

1. `download_check()` 呼叫 `verify(download_only=True)`。
2. verify 在 sequence 26 產生 BASIC verification。
3. verify 在 sequence 27 產生 publish-plan，target 為 `media_002.jpg`。
4. verify 呼叫 `_execute_publish(seq27 plan)`。
5. `_execute_publish()` 看到 BASIC verification，呼叫 `_require_download_settlement()`。
6. `_require_download_settlement()` 呼叫 `_assert_no_local_changed()`。
7. `_completion_availability()` 取得 P2/M1 completion，並取得 seq27 的 pending plan。
8. 對 P2/M1 的目錄，`plan_names` 包含 `media_002.jpg`。
9. 因此 `expected_names = {media_001.jpg, media_002.jpg}`。
10. 目錄實際 contents 只有 `{media_001.jpg}`；`actual_names != expected_names`。
11. 拋出 `COMPLETED_DIRECTORY_CONTENTS_CHANGED`。
12. 外層 catch 把 P2/M1 的所有 completion 投影成 `LOCAL_CHANGED`。
13. `_assert_no_local_changed()` 拋出 `COMPLETED_FILES_CHANGED_NO_REDOWNLOAD`。
14. CLI 回傳 exit 4，拒絕 dispatch。
15. 之後的 resume 在 `6810` 先做相同 settlement，故尚未走到 seq27 publish 就再次失敗。

### 唯讀內部重現

以 `NotesRecords` 唯讀載入此 ledger，未修改 events，得到：

```text
pending plans:
  seq 27 -> media_002.jpg

completions: ['media_001.jpg']
pending:     ['media_002.jpg']
actual:      ['media_001.jpg']
expected:    ['media_001.jpg', 'media_002.jpg']
availability: P2/M1 -> LOCAL_CHANGED
```

這直接證明 `LOCAL_CHANGED` 是 projection bug；不是媒體檔真的漂移。

## 事實、推論與未知

### 已確認事實

- 列表盤點為 4 篇、8 個媒體；scan coverage 是 `COMPLETE`。
- P2/M1 已有合法 completion，完成檔目前與 completion 的 stat/hash 完全吻合。
- P2/M2 已有 `DOWNLOAD_FINISHED`、BASIC verification PASS，且 staging 檔案目前與 verification manifest 完全吻合。
- seq27 是尚未完成的 publish plan，沒有 completion。
- `download-check` 與 `resume` 都在同一個假 `LOCAL_CHANGED` 阻塞點 exit 4。
- `resume` 沒有新增 ledger event。
- 失敗前 summary 沒有 `LOCAL_CHANGED`；失敗後才有。
- 失敗後 P2/M2 unresolved attempt 是 `DOWNLOAD_FINISHED` 且 `pending_naming=true`。

### 高信心推論

- 本次 blocker 的根因是 `_completion_availability()` 同時把 completion names 與 pending plan names 視為 expected actual names。
- `_append_publish_plan()` 已要求建立 plan 時 target 不存在，因此把該 target 當成「現在就必須存在」與它自己的建立契約矛盾。
- 這個問題只在同一貼文已有 completed sibling、且下一項 pending plan 指向同一目錄時出現；單一媒體的 pending naming 測試不會暴露它。
- 不應為了解鎖而刪除 plan target 檢查、手動建立 `media_002.jpg`、刪除 staging、重下或新開 attempt；這些都會破壞既有證據或繞過安全檢查。

### 尚未證明或未知

- CUA 是否真的把點擊送到 native hit target 是 `UNKNOWN`；receipt 不是 OS event trace。
- P2/M2 原始服務端媒體種類仍為 `UNKNOWN`；sequence 26 只證明下載檔的 magic/suffix 基本分類為 PHOTO。
- `DOWNLOAD_ONLY` 沒有 ImageIO/ffmpeg 完整解碼，也不保證來源原件或內容完整。
- 本次沒有再操作 GUI，因此沒有新的畫面觀察；所有 GUI 事實均來自既有 observation 原件。
- 尚未在真實完整 E2E、跨 Session、混合附件 chooser 或完整列表下載中驗證修復。

## 修復方向

以下是供 planner 獨立評估的安全方向，尚未實作：

1. 分離「completed target 必須存在」與「pending plan target 在 publish 前允許不存在」。
2. 對 completion 目錄維持嚴格檢查：已完成檔案缺失、額外檔、symlink、device/inode/stat/hash 漂移仍必須拒絕。
3. pending plan target 若尚未存在，不得被當成 completed directory 損壞；若已存在，必須只當成該 transaction 的候選 target，並由 publish 路徑核對 transaction、source manifest、非 symlink、單一 link、device/inode/hash 等身分。
4. 不要把 pending plan names 簡單從所有檢查移除；`_ensure_publish_directory` 與 `_execute_publish` 仍需處理中斷後 target 已存在的恢復情境。
5. 既有 sequence 27 transaction 應優先評估能否在原 ledger 上安全接續 publish；不得重下、不得建立替代 attempt、不得手改 ledger/evidence。
6. 修正後的安全驗證順序應是：先在唯讀 fixture 重現、再執行 regression tests、再由 planner 確認既有 ledger 的 resume 路徑；不要在未確認前直接操作真實 ledger。

## 建議回歸測試矩陣

### 正向

- 同一 post 已有 `media_001` completion、`media_002` pending plan，但 `media_002` 尚未存在：availability 不得回 `LOCAL_CHANGED`；`download-check`／`resume` 可安全接續。
- 同一 post 已有 completed sibling，pending plan target 因先前的中斷而已存在且與 transaction/source identity 完全一致：只允許該 plan 的候選 target，仍須完整核對。
- 既有 seq27 類型的 BASIC publish plan：resume 只建立一個 completion，不建立第二個 intent、verification 或 publish-plan。

### 負向

- completed target 真的缺失：仍拒絕。
- completed directory 出現未屬允許環境附屬項的額外檔：仍拒絕。
- completed 或 pending 候選是 symlink：仍拒絕。
- completed target 的 hash、size、device、inode、mtime、ctime 任一漂移：仍拒絕。
- pending target 已存在但 transaction/source/inode/hash 不匹配：publish 必須拒絕，不能誤發布。
- `download-check` 與 `resume` 的錯誤路徑不得寫入新 completion，也不得重送下載。

### 既有測試缺口

- `tests/test_notes_records.py:1005` 的 naming interruption 是單一媒體情境，沒有 completed sibling。
- `tests/test_notes_regressions.py:1675` 驗證 pending publish 被 local change 阻擋，沒有驗證「completed sibling + pending plan」的成功接續。
- `tests/test_notes_download_only.py:214` 有 pending BASIC publish 的 recovery/bind 接續，但沒有同一 post 多媒體 completed sibling 情境。

## 既有 ledger 的安全恢復方案

目前只可提出，不可直接執行：

1. 先讓 planner 獨立確認 `_completion_availability()` 的 projection bug 與最小修正。
2. 修正後先在合成 fixture 或複製 ledger 上驗證，不碰真實 ledger。
3. 若確認既有 sequence 27 的 transaction、verification、source manifest 與 staging 仍完整，評估以日常 `resume`（BASIC verification 分支）接續既有 plan，而不是重下或新 attempt。
4. 若 resume 成功，預期只會建立既有 transaction 的 publish-progress 與 `media_002.jpg` completion；不得建立新的 intent、verification 或 publish-plan。
5. resume 後再以 `summary` 與 completion 讀回核對：P2/M1、P2/M2 均為 `COMPLETED`、沒有 pending naming、沒有 `LOCAL_CHANGED`；檔案 stat/hash 與 completion 一致。
6. 若 planner 認為既有 plan 不可安全接續，則停止並回報；不得為了完成本次備份而手改 ledger、覆寫 completion、刪除 staging 或重下。

## NOT_RUN

- 真實完整 LINE 記事本 E2E：`NOT_RUN`
- 跨 Session 的正式恢復：`NOT_RUN`
- 完整列表剩餘媒體下載：`NOT_RUN`
- P3、P4 的媒體下載：`NOT_RUN`
- 混合附件 chooser 的真實操作：`NOT_RUN`
- ImageIO/ffmpeg 完整解碼與內容完整性：`NOT_RUN`
- 修正程式後的實際 regression run：`NOT_RUN`
- 既有 ledger 的真實 resume 解鎖：`NOT_RUN`

## 目前結論

這不是 P2/M1 檔案遺失或損壞，也不是 P2/M2 下載失敗；而是 pending publish plan 被錯誤納入 completed directory 的 expected names，導致下載檢查在寫入 verification/publish-plan 後自我拒絕。現階段唯一安全做法是保留原檔與 ledger，讓 planner 獨立核對根因與最小修復，再決定是否可用既有 sequence 27 transaction 接續。未解前，不能宣稱整份列表完成，也不能派送 P3/P4。
