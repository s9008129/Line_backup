# LINE 記事本「已下載但無法完成」的 scan binding／restart 死鎖問題提報單

- 提報日期：2026-11-14（Asia/Taipei）
- 提報對象：高階模型、架構審查者與後續接手 Agent
- 任務性質：第一性原理根因分析、狀態機證據整理與最小修法辨識；不是重下載、ledger 手改、restart scope 擴張或 GUI 授權
- 專案：`Line_backup`
- 分支：`feature/line-notes-media`
- 分析起點 HEAD：`efa2d24dfa9d9db51d43a2d1695fac63d11ee582`
- `src/line_backup_batch/notes.py` SHA-256：`ff62ac0d310238f27ae889c40bcac94d2050e8663fb4b0963807eee60347a54c`
- 目前備份狀態：`BLOCKED`
- 根因置信度：交易死鎖為 **高置信度**；「latest-only scan gate 是刻意保護、但缺少合法的舊 attempt 收斂轉換」為 **高置信度推論**；產品作者原本是否有其他設計意圖仍為 `UNKNOWN`

## 0. 隱私、授權與操作邊界

本報告可能提交至共享或公開的技術審查環境，因此已遮蔽：

- 列表顯示名稱與上下文名稱；
- 貼文作者、貼文標題及畫面中的人名；
- 完整家目錄；
- 私人照片、原始匯出檔名與貼文文字。

本報告保留 opaque 識別碼、事件序號、狀態、時間、檔案大小、device／inode、SHA-256 與命令輸出，以便和私有帳本逐項核對。

本次只做唯讀核對、既有 receipt 檢視、既有測試重跑與報告撰寫。沒有：

- 再按 LINE 下載控制；
- 再操作 chooser；
- 建立新 intent 或新 staging；
- 執行 `verify`、`download-check`、`media-kind-reconcile`、`activation` 或 `completion`；
- 改寫任何既有 intent、outcome、restart confirmation、completion、UNKNOWN 或掃描事件；
- 手動修改 `scan_id`、media key、ledger、檔案或目的地；
- 重下載、改名、刪除或覆寫原檔。

帳本在本次分析前後均為 125 個事件；tip 不變：

```text
events/00000125.json
SHA-256 = 941025ef070f342a9d248b7afd30776b6bab3ada067d762d65d8bcfb5220bfa9
```

## 1. 白話結論

真正失敗的不是下載、網路、權限、SHA-256 或影片解碼，而是 **三條彼此獨立的安全規則組合後形成循環等待**：

1. 舊 attempt 已下載完成，但它綁定的是舊盤點 `S_OLD`。
2. 完成檢查要求「attempt 綁定的盤點必須就是目前最新盤點」。因此新的 recovery scan `S_NEW` 出現後，舊 attempt 被判定 `ATTEMPT_SCAN_BINDING_CHANGED`，不能 verify。
3. restart confirmation 又要求確認後必須先完成新的 recovery scan，才能建立 v3 restart attempt；所以 `S_NEW` 是流程必要條件，不能為了讓舊 attempt 驗證而撤回。
4. 舊 attempt 不在目前 restart scope，不能直接轉成 v3。
5. 其他 restart scope 項目的 v3 intent 又要求「所有 scope 外的舊 attempt 都必須是 `STOPPED`／`NOT_SENT`」；但這個舊 attempt 是 `DOWNLOAD_FINISHED`。
6. restart progress 只辨識同一 restart ID 的 v3 intent，因此仍回報 scope 內項目是 `INTENT_REQUIRED`。

一句話：

> **下載已經成功，檔案也還在；但舊下載綁在舊盤點。重啟流程要求新盤點，完成檢查卻堅持必須是最新盤點，而重啟流程又不接納這個 scope 外的舊下載。三條路互相封鎖，沒有任何一條能在不破壞既有事實的前提下獨自走完。**

這不是「再按一次下載」可以安全解開的狀態。重下會增加新交易，卻沒有解決舊 attempt 的收斂語意。

## 2. 執行摘要

### 2.1 已確認的來源與盤點

- 指定單一列表已完成全卡片掃描：
  - 45 個 page events；
  - 51 篇貼文；
  - `scan_coverage=COMPLETE`；
  - 最新 recovery scan 為 `16279e8a441b440fbdbc7a2b9182514b`。
- 最新摘要目前呈現：
  - 51 篇中 2 篇有已細盤媒體；
  - 49 篇仍是 `DETAIL_PENDING`；
  - `NO_MEDIA=0`；
  - media projection 共 3 筆；
  - 2 筆 `COMPLETED`／`VERIFIED_PRESENT`；
  - 1 筆舊 VIDEO attempt 尚未完成收斂。

注意：`DETAIL_PENDING=49` 不代表 49 篇沒有媒體，只代表本輪尚未逐篇細盤。全卡片覆蓋已完成，逐篇媒體細盤尚未完成。

### 2.2 目前三個關鍵項目

| 項目 | 角色 | 目前狀態 | 本機檔案 |
|---|---|---|---|
| Post A／Media A | restart scope 內的已完成照片 | `COMPLETED`；`VERIFIED_PRESENT` | 存在、hash 讀回成功 |
| Post B／Media B | restart scope 內的已完成照片 | `COMPLETED`；`VERIFIED_PRESENT` | 存在、hash 讀回成功 |
| Post C／Media C | scope 外的舊 VIDEO attempt | `DOWNLOAD_FINISHED`，但 summary 顯示 `PENDING`；`scan_binding_match=false` | staging 內有 1 個穩定 JPEG |

### 2.3 最新 blocker

最新 `summary` 的 `dispatch_blockers`：

```text
POST_DETAIL_PENDING
RESTART_BATCH_OPEN
STALE_MEDIA_INVENTORY
STALE_POST_DETAIL
VERIFY_REQUIRED
```

`all_known_media_complete=false`，`dispatch_authorized=false`。

### 2.4 為什麼不能宣稱完成

- Post A、Post B 的既有完成與目前檔案可讀回，但 restart batch 尚未走完。
- Post C 的下載結果可歸屬且檔案穩定，但尚未 verify／completion。
- 49 篇貼文仍待細盤。
- 目前有 scope 外舊 attempt 卡住 restart intent，屬全域派送阻塞。
- 因此整份列表不能標成全部完成，也不能把 Post A、Post B 視為已關閉 restart batch。

## 3. Opaque 識別碼

```text
local_list_id = ae9998b5-d77a-405e-adfc-8089c42ec4e0
list_key      = be605665b39e14c5079f6167ea6e60a8c84488fb78a97a2927323f9a83067506

old_scan_id   = 2cb64876460a42ba9a74a0f8cc1bfb9b
new_scan_id   = 16279e8a441b440fbdbc7a2b9182514b

post_a_key    = 2f7c3932521ee3ec9f8790889ce38b7d71db77797ee0cb578fd838f1c9b23ba1
media_a_key   = 8ebd32f894f3ead5fbb6e0b7e29389b9f6739a8d6e7edfaffe150a6906c41a95

post_b_key    = 1063ba71b39cbb4515118703a27ee99b12db40acd62833a47a54fc5ade55fb09
media_b_key   = 87dccf92ed061bea845173c262ff4460ea01d8135e3f5a383340b93ac3eb8bf5

post_c_key    = ff9c67635644a9d2900bc25f718ab1741fee863e4ff43b555e971c6028efcc6f
media_c_key   = 566f78a87da68fddeb52984e7357e04630127cc28693c029ede98a4f4604d99c
attempt_c_id  = 0a8fb5b189dd442bbceb28ac10510f1f

restart_id    = 310f90833449979abfb3200882a104fef3bf723edc07bddea1683b6467b09326
generation    = 1
scope_digest  = 8255e83fe9930c20bd1d75bee077771d2419f2cb6462d528d8abcb73c75a839b
```

## 4. 完整交易時間線

| 事件 | 事實 | 重要效果 |
|---:|---|---|
| 47 | 舊完整掃描 `S_OLD=2cb648…` COMPLETE | Post C 的來源與 media key 建立於此快照 |
| 50 | Post A 舊 intent | 後續完成於 sequence 57 |
| 57 | Post A completion | 舊完成事實仍保留 |
| 60 | Post B 舊 intent | 後續完成於 sequence 67 |
| 67 | Post B completion | 舊完成事實仍保留 |
| 69 | Post C post detail，`scan_id=S_OLD` | 舊媒體細盤仍綁定 S_OLD |
| 70 | Post C media inventory，`scan_id=S_OLD` | media 清單與順序可歸屬 |
| 71 | Post C `line-notes-intent/v2` | attempt 綁定 `S_OLD`，`effective_kind=VIDEO` |
| 72 | Post C outcome `DOWNLOAD_FINISHED` | 下載已終結，不可當成未派送 |
| 73 | 新 Session binding | 建立當次有效前景與 handoff |
| 74 | restart confirmation | scope 只含 Post A、Post B 的 `LOCAL_CHANGED` |
| 75 | 新 recovery scan START | `S_NEW=16279e8a…` 開始 |
| 76–120 | 45 個 page events | 全列表卡片覆蓋 |
| 121 | 新 recovery scan COMPLETE | 51 篇貼文；S_NEW 成為最新盤點 |
| 122–123 | Post A post/media detail 補齊 | 目前投影為 COMPLETED／VERIFIED_PRESENT |
| 124–125 | Post B post/media detail 補齊 | 目前投影為 COMPLETED／VERIFIED_PRESENT |

關鍵順序是：

```text
S_OLD 完成
  → 舊 VIDEO attempt 71 下載完成 72
  → restart confirmation 74
  → S_NEW 開始 75、完成 121
  → 舊 attempt 的 scan_id 不再是 latest
```

restart confirmation 的 scope 不含 Post C，因此 S_NEW 的出現雖然是 restart 規則要求，卻同時讓 scope 外的舊 attempt 失去 latest-only 驗證資格。

## 5. 三筆拒絕／分流輸出

### 5.1 舊 attempt 的 `download-check`

命令：`notes download-check --attempt-id 0a8fb5…`

原始 stdout：

```json
{"status":"REFUSED","reason":"ATTEMPT_SCAN_BINDING_CHANGED","dispatch_authorized":false}
```

- exit code：`4`
- receipt：`notes-capture-a69086a1df1240aa84e873bf228f5b28`
- `result.json` SHA-256：`dc74c9ee22c111a5c735f757163e8965c7696f37baf86b2f7cc108da3fcc2455`
- `stdout.bin` SHA-256：`721b758e03e4ab51d07e6734dde284c187c1d4ad0bf072e5348e75bc7f78fe77`
- `stderr.bin`：0 bytes

這證明命令不是卡在檔案 hash、suffix、非空或穩定檢查，而是在更早的 scan binding gate 被拒。

### 5.2 restart scope 項目的 v3 intent

命令：`notes intent --media-key 87dccf… --restart-id 310f90…`

原始 stdout：

```json
{"status":"REFUSED","reason":"ANOTHER_MEDIA_ATTEMPT_UNRESOLVED","dispatch_authorized":false}
```

- exit code：`4`
- receipt：`notes-capture-bee30f47910c43ac9ace3b47b346ad0d`
- `result.json` SHA-256：`41a9583a1de8ac69df155fb85393e2d8015c868ca668d99deefc59ccd9d0156e`
- `stdout.bin` SHA-256：`20d042f2cd659ac4b5f58d86131e568ff0bf83ba1a3f28a2ff38b0a98637cc68`
- `stderr.bin`：0 bytes
- 未建立 intent、未建立 staging、未按任何下載控制。

這裡的「ANOTHER_MEDIA_ATTEMPT」就是 scope 外、已 `DOWNLOAD_FINISHED` 的 Post C attempt。

### 5.3 restart preview

命令：`notes restart preview`

摘要：

```json
{
  "status": "OPEN_BATCH",
  "restart_required": true,
  "restart_id": "310f90833449979abfb3200882a104fef3bf723edc07bddea1683b6467b09326",
  "generation": 1,
  "scope_digest": "8255e83fe9930c20bd1d75bee077771d2419f2cb6462d528d8abcb73c75a839b",
  "estimated_extra_bytes": 294040
}
```

- scope 內兩項均為 `action=INTENT_REQUIRED`；
- receipt：`notes-capture-6cc6b9af78104ebaa453d4bfe0be3a32`
- `result.json` SHA-256：`fb2ba0f481eaaa2a77ddef0dc00c6c59b673d4afe564823391009e2a99abd991`
- `stdout.bin` SHA-256：`28a909a277ffec1bb38058f7d3e9519f79328ce7cf84df72af05fcaffb5ce7c4`
- `stderr.bin`：0 bytes

### 5.4 `resume` 的唯讀重跑

本次在沒有其他 notes 命令並行時重跑 `resume`，exit code 為 `0`：

```json
{
  "action": "NO_NAMING_TRANSACTION",
  "pending": [
    {
      "media_key": "566f78a87da68fddeb52984e7357e04630127cc28693c029ede98a4f4604d99c",
      "attempt_id": "0a8fb5b189dd442bbceb28ac10510f1f",
      "action": "SCAN_BINDING_REVIEW_REQUIRED"
    }
  ],
  "dispatch_authorized": false
}
```

這證明：

- 沒有 pending naming transaction；
- 系統明確要求 scan binding review；
- `resume` 沒有提供可安全自動接續的下一步；
- 重跑前後 tip 均為 `941025ef…bfa9`，沒有新增事件。

### 5.5 `NOTES_LOCK_BUSY` 的排除

先前曾出現：

```json
{"status":"REFUSED","reason":"NOTES_LOCK_BUSY","scope":"collection","dispatch_authorized":false,"retry_safe":false}
```

- receipt：`notes-capture-7f5b74d537dd41c39b4cfe940d5d79d2`
- 原因是同一時間並行執行多個 notes 命令造成鎖競爭。
- 串行重跑後 `resume` exit 0，故 `NOTES_LOCK_BUSY` 不是本次產品根因，也不是要提交給高階模型的主要缺陷。

## 6. 帳本事件證據

### 6.1 舊 scan

```text
sequence 47
scan_id  = 2cb64876460a42ba9a74a0f8cc1bfb9b
schema   = line-notes-scan/v1
event SHA-256 = 3bb8a6782272ed23aa88155c4eafa696ea7612dbe277a0f1740c4d77bcfa327d
```

### 6.2 Post C intent

```text
sequence 71
schema        = line-notes-intent/v2
attempt_id    = 0a8fb5b189dd442bbceb28ac10510f1f
post_key      = ff9c67635644a9d2900bc25f718ab1741fee863e4ff43b555e971c6028efcc6f
media_key     = 566f78a87da68fddeb52984e7357e04630127cc28693c029ede98a4f4604d99c
scan_id       = 2cb64876460a42ba9a74a0f8cc1bfb9b
effective_kind= VIDEO
session_id    = notes-20261113-1528-foreground02
event SHA-256 = b39c5ece72a043e949811423d8054be6b382c2f68282e893a210ea2a813d31be
```

intent 的目的地是全新的 staging：

```text
<LIST_DIR>/.line-notes-incoming-bd7945b0e62f4842a4662435d843a6f2
directory_device = 16777234
directory_inode  = 149674165
```

### 6.3 Post C outcome

```text
sequence 72
schema       = line-notes-outcome/v1
outcome      = DOWNLOAD_FINISHED
attempt_id   = 0a8fb5b189dd442bbceb28ac10510f1f
evidence     = evidence/5fd1fbeb724f4d529ac800dd8a4c5661de6ab3fe2b43086c0d55d348f28b658b
event SHA-256= af2df3f7ea3addfb2a77966d941783539f994963b280aa7774061a5787de39fe
```

outcome evidence bundle 的 context 明確寫入：

```json
{
  "attempt_id": "0a8fb5b189dd442bbceb28ac10510f1f",
  "media_key": "566f78a87da68fddeb52984e7357e04630127cc28693c029ede98a4f4604d99c",
  "post_key": "ff9c67635644a9d2900bc25f718ab1741fee863e4ff43b555e971c6028efcc6f",
  "scan_id": "2cb64876460a42ba9a74a0f8cc1bfb9b"
}
```

因此這不是「不知道有沒有下載」的 UNKNOWN；事實是已下載完成，尚未 verify／publish／completion。

### 6.4 restart confirmation

```text
sequence 74
schema        = line-notes-restart-confirm/v1
restart_id    = 310f90833449979abfb3200882a104fef3bf723edc07bddea1683b6467b09326
generation    = 1
scope_digest  = 8255e83fe9930c20bd1d75bee077771d2419f2cb6462d528d8abcb73c75a839b
expected_tip  = sequence 73 / 26f9ccfb55468b39cee99e0f73047f04749849c26b501649fca511fc93bfaf4c
event SHA-256 = 929a5a8f8b8447eac704519273d406640eaf11acea259da9b99981341303f7d5
```

scope 只有：

| post | media | 原因 | prior attempt | prior completion |
|---|---:|---|---:|---:|
| Post A | Media A | `LOCAL_CHANGED` | sequence 50 | sequence 57 |
| Post B | Media B | `LOCAL_CHANGED` | sequence 60 | sequence 67 |

Post C／attempt C **不在 scope 內**。這是死鎖成立的必要條件之一。

### 6.5 新 recovery scan

```text
sequence 75 START
scan_id       = 16279e8a441b440fbdbc7a2b9182514b
event SHA-256 = 44f299d9a948221fc4c2380d67c5d086b390b77cf545ebae287256a6624cb422

sequence 121 COMPLETE
posts         = 51
event SHA-256 = 36f8c90a33d93970453acf8ec916c5c02465cc692d719875504e5ef8b2961f69
```

sequence 121 之後，`S_NEW` 成為最新完整掃描；Post C 的 intent 仍綁定 `S_OLD`。

### 6.6 最新兩篇候選細盤

```text
sequence 122  Post A post detail  SHA-256 1d775faa95e40c20480e2c793e234190d334985996f1ea8339b51d7c77de60e1
sequence 123  Post A media detail SHA-256 8c4125b25aa8aeacb076c055d26301cb04065918a4b0ccd1bd4e117dbbe1561a
sequence 124  Post B post detail  SHA-256 c0ed199d1a9938e627ef0d9ee327f0794b636457fc89f8070e9f707796995342
sequence 125  Post B media detail SHA-256 941025ef070f342a9d248b7afd30776b6bab3ada067d762d65d8bcfb5220bfa9
```

四筆細盤均綁定 `S_NEW=16279e8a…`，並提供對應 evidence bundle：

```text
Post A post : 5c11e048bea37a5025284b704fe84881b6bd5632f4cc63ef5675606640876b47
Post A media: f028561437b03fb5b39dcbd4a49d4ef52faa97ed569d8fdb0c4da8d11488b742
Post B post : b65ac8acbefe44a3a28c0b85eadd56aa8acdb8de55f90377c1f2706ff1856660
Post B media: 8d26530734ed62ccaf723461b592a39bc27bd428c3d3739e0a91a94f298fa920
```

這使最新投影不再出現 `COMPLETED_FILES_CHANGED`，但 restart batch 仍開放，因為 v3 attempt 尚未建立。

## 7. 本機檔案與 GUI 證據

### 7.1 Post C staging

staging 內只有一個 regular file：

```text
bytes       = 420959
device      = 16777234
inode       = 149675395
mode        = -rw-r--r--
nlink       = 1
SHA-256     = 72999b7bddd960864fb540f440a882ccc6697ff7bfa269e8dc04f26d0019c2b2
file(1)     = JPEG image data, JFIF 1.02, 1580x954, components 3
xattr       = com.apple.quarantine: ...;LINE;
```

沒有觀察到 symlink。三次 readback 樣本的 inode、size、mtime、ctime 與 SHA-256 均穩定。

ImageIO audit：

```json
{
  "decoded": true,
  "contentType": "public.jpeg",
  "width": 1580,
  "height": 954,
  "verdict": "PASS"
}
```

這證明目前檔案是完整可解碼 JPEG；它不證明來源一定是照片，也不證明影片已被保存成完整影片。

### 7.2 Post A、Post B 的完成檔

目前檔案：

| post | bytes | device | inode | SHA-256 | 容器 |
|---|---:|---:|---:|---|---|
| Post A | 177471 | 16777234 | 149613405 | `b124255676f15f69f8517c6975744cccfadcfbb0f85359a2f7b19ca4489eba20` | JPEG 1039×1455 |
| Post B | 116569 | 16777234 | 149615078 | `704ab9e1779215af10d562a4093460042df6b9369eeb4cfb3c3ca91b11720074` | JPEG 1062×1542 |

兩者目前 projection 均為 `COMPLETED`／`VERIFIED_PRESENT`，且沒有 symlink。

### 7.3 GUI 觀察

Post B 的最新 viewer AX 標題形如：

```text
Window: "<MASKED_AUTHOR>(1/1)", App: LINE.
```

保存的 viewer 截圖：

- 1280×960；
- SHA-256 `0f72cfb30a7fc7ee5c85d1b2f92870114665609956ff43a718cc0e56cee5ea87`；
- 對應 input receipt 為 `App.click([100,650])`，`success=true`；
- 觀察時間 `2026-11-13T14:41:57.336Z` 至 `2026-11-13T14:41:58.183Z`。

本次根因分析沒有再操作 GUI；LINE 仍停在該 viewer。上述只能記為先前的 GUI `OBSERVED`，不是本次新 E2E。

### 7.4 舊 Post C 的 GUI／chooser 證據

既有 outcome statement 與 receipts 顯示：

- 下載控制只派送 1 次；
- 出現 LINE 儲存 panel；
- `saveAsNameTextField` 有預填名稱；
- Go to Folder 套用成功；
- pre-confirm path／device／inode／空目錄核對一致；
- 最終儲存只按 1 次；
- panel 關閉後回到同一 viewer；
- 截圖看到下載完成提示，但提示文字不在 AX；
- staging 隨後出現穩定檔案。

因此 `DOWNLOAD_FINISHED` 是有證據的 outcome，不是猜測。

## 8. 程式碼第一性原理證據

### 8.1 兩種 scan 一致性語意同時存在

#### A. verify／download-check 的 latest-only gate

`_attempt_scan_binding_matches()`，`src/line_backup_batch/notes.py:3672-3693`：

```python
latest, scans = self._open_scan()
if (latest is None or scans[latest]['complete'] is None or
        bound != latest):
    return False
```

它要求 attempt 的 `scan_id` **等於目前最新 scan**，不是只要求該 scan 仍存在且證據相符。

`verify()` 在 `src/line_backup_batch/notes.py:6626-6627` 呼叫：

```python
self._require_attempt_scan_binding(
    projection['attempts'][attempt_id])
```

`download_check()` 在 `src/line_backup_batch/notes.py:6600-6603` 直接轉呼叫 `verify()`，所以同樣先遇 latest-only gate。

#### B. origin-scan 驗證只要求來源 scan 仍有效

`_validate_attempt_origin_scan()`，`src/line_backup_batch/notes.py:6179-6200`：

```python
_latest, scans = self._open_scan()
scan = scans.get(scan_id)
need(scan is not None and scan['complete'] is not None,
     'ATTEMPT_SCAN_BINDING_CHANGED')
...
```

此函式取得 `_latest` 卻不使用它來要求 `scan_id == latest`。它只確認：

- attempt 的來源 scan 存在；
- 來源 scan 已 COMPLETE；
- post 在該 scan 中；
- post detail 的 `scan_id` 與來源 scan 一致；
- media projection 的 post／media／scan 身分一致。

這證明系統內同時存在：

```text
origin binding semantics：來源 scan 仍有效即可
latest-only semantics   ：來源 scan 必須仍是最新 scan
```

目前 verify／download-check 採用後者，但 restart 流程會主動製造一個新的 scan，於是把較早、已完成且不在 restart scope 的 attempt 永久推離後者。

### 8.2 latest-only 是刻意的，不是偶然 typo

測試 `tests/test_notes_regressions.py:2029-2058` 明確建立：

1. attempt；
2. `DOWNLOAD_FINISHED`；
3. 再追加一個 historical scan；
4. 呼叫 verify；
5. 期待 `ATTEMPT_SCAN_BINDING_CHANGED`。

本次重跑：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest \
  tests.test_notes_regressions.NotesRegressionTests.test_verify_and_pending_resume_reject_attempt_after_new_scan
```

結果：

```text
Ran 1 test in 0.160s
OK
```

所以不能把問題描述成「latest-only gate 壞掉」。較精確的描述是：

> **latest-only gate 被刻意實作，但缺少一個能把「已完成、來源證據仍有效、但不在最新 scan」的舊 attempt 合法收斂的語意。**

### 8.3 restart confirmation 必然製造新 scan

`src/line_backup_batch/notes.py:4906-4911` 要求：

```python
latest_scan = ...
need(latest_scan is not None and
     latest_scan['sequence'] > confirmation['sequence'],
     'POST_CONFIRMATION_RECOVERY_SCAN_REQUIRED')
```

`_validate_restart_scope_current()`，`src/line_backup_batch/notes.py:6202-6209` 也要求最新 scan 的 sequence 大於 confirmation。

因此：

- restart confirm 後一定要有新的 recovery scan；
- 新 scan 一旦完成，就成為 latest；
- 舊 attempt 若仍綁定 confirmation 前的 scan，就永遠過不了 latest-only verify。

這不是 Agent 忘記更新 `scan_id`，而是 append-only 歷史中不能也不應改寫舊 intent。

### 8.4 restart progress 只認 v3

`_restart_progress()`，`src/line_backup_batch/notes.py:4747-4798`：

```python
attempt_ids = [
    attempt_id
    for attempt_id in attempts['attempts_by_media'].get(key, [])
    if attempts['attempts'][attempt_id]['schema'] ==
       'line-notes-intent/v3' and
       attempts['attempts'][attempt_id]['restart_id'] == restart_id
]
...
elif latest_attempt is None:
    action = 'INTENT_REQUIRED'
```

它不把 scope 外舊 v2 的 `DOWNLOAD_FINISHED` 視為該 restart 的已收斂結果，也不把任何 v2 attempt 納入 progress。結果是 scope 內項目持續顯示 `INTENT_REQUIRED`。

### 8.5 v3 intent 被全域未決 attempt gate 阻擋

`_restart_intent()`，`src/line_backup_batch/notes.py:4947-4956`：

```python
resolved = set(self._completion_projection()[0])
resolved |= set(self._active_media_versions())
for other_key, attempt_id in attempts['latest_by_media'].items():
    if other_key in scope_media:
        continue
    if other_key in resolved:
        continue
    result = self._attempt_result(attempt_id, attempts)
    need(result in ('STOPPED', 'NOT_SENT'),
         'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED')
```

Post C：

- 不在 scope；
- 沒有 completion；
- 沒有 active version；
- result 是 `DOWNLOAD_FINISHED`；
- 因此不屬於 `STOPPED`／`NOT_SENT`。

所以第一次為 Post B 建立 v3 intent 時，立刻被拒絕。

一般 v2 intent 也有類似 gate：`src/line_backup_batch/notes.py:5040-5049`。這使問題不是只影響 restart，也讓其他普通新 intent 無法越過 scope 外舊 attempt。

### 8.6 kind reconcile 也被兩層 gate 擋住

`media_kind_reconcile()`，`src/line_backup_batch/notes.py:5354` 先呼叫 latest-only scan binding；接著 `src/line_backup_batch/notes.py:5367-5368` 要求沒有 open restart。

目前：

- `scan_binding_match=false`；
- `restart_batch_open=true`。

即使把 VIDEO/JPEG 類型差異視為後續問題，現有 reconcile 入口也無法到達。這不是目前的直接錯誤，但會阻擋任何以合法事件修正類型的下一步。

## 9. 死鎖的狀態機表示

### 9.1 個別狀態

```text
S_OLD = latest complete scan
attempt C:
    scan_id = S_OLD
    result  = DOWNLOAD_FINISHED
    scope   = outside restart R

restart R:
    confirmed
    scope = {A, B}

S_NEW = post-confirmation recovery scan
latest = S_NEW
```

### 9.2 三條規則

```text
Rule V（verify）
    attempt C 可以 verify
    iff C.scan_id == latest

Rule R（restart intent）
    v3 intent for A/B 可以建立
    iff all scope-外 unresolved attempts 都是 STOPPED/NOT_SENT

Rule P（restart progress）
    A/B 被視為已接續
    iff 存在同 restart_id 的 v3 attempt
```

### 9.3 實際循環

```text
S_NEW 出現
  → Rule V 拒絕 C 的 verify
  → C 無法 completion
  → C 不是 STOPPED/NOT_SENT
  → Rule R 拒絕 A/B 的 v3 intent
  → 沒有 v3 attempt
  → Rule P 持續回報 INTENT_REQUIRED
  → restart batch 不能關閉
  → 也不能用新的正常 intent 繞過
```

這裡沒有任何單一函式「明顯算錯」；問題在三條規則缺少共同的收斂狀態與轉換規則。

## 10. 第一性原理拆解

### 10.1 來源快照不是交易本身

scan 回答的是「某個時刻，列表中有哪些卡片、貼文與媒體」。attempt 回答的是「對某個 media key 派送了什麼、下載到哪裡、得到什麼 outcome」。

兩者是不同層：

- scan 是可重複觀察的來源快照；
- attempt 是不可重送的交易；
- completion 是不可變的完成事實。

舊 attempt 綁定 S_OLD 是正確的 provenance；它不應因 S_NEW 出現而被偽裝成綁定 S_NEW。但這也不代表 S_NEW 可以讓舊 attempt 的下載結果失去可驗證性。

### 10.2 「來源仍有效」與「仍是最新」不是同一命題

如果 requirement 是防止拿過期媒體清單驗證：

- 應證明舊 scan 的 post／media identity 與 attempt 的 destination／outcome 仍一致；
- 而不是無條件要求 bound scan 必須等於 latest。

如果 requirement 是只允許最新庫存完成新派送：

- 應把它放在新 intent 建立；
- 不應讓已完成、不在 restart scope、且來源證據完整的舊 attempt 永遠無法收斂。

目前的 latest-only gate 把「新派送資格」與「舊交易驗證資格」混成同一條件。

### 10.3 restart scope 是精確授權，不應被隱式擴張

restart confirmation 的 scope 只有 A、B。不能因為 C 造成阻塞，就把 C 擅自加入 scope、改 scope digest、重建 confirmation 或重下 C。

同時，scope 外 C 也不能被當成空氣；它的已下載事實必須有合法方式收斂。

### 10.4 completion 不可改寫

Post A、Post B 已有舊 completion。即使 restart batch 要建立新版本：

- 舊 completion 不可覆寫；
- 原目錄與 hash 不可被新結果取代；
- 必須保留舊事實，再追加新版本事件。

因此不能用手改 completion 或把舊 completion 刪掉來「解鎖」。

### 10.5 restart progress 需要穩定的交易身分

restart 的進度判定只看 `line-notes-intent/v3 + restart_id`，但 scope 外舊 v2 仍是 `latest_by_media` 的阻塞來源。這是「progress 的視角」和「dispatch gate 的視角」不一致：

- progress 看不到舊 v2；
- gate 卻被舊 v2 阻擋。

這使 UI／CLI 同時顯示：

```text
scope media: INTENT_REQUIRED
other media: DOWNLOAD_FINISHED
dispatch_authorized: false
```

看似可繼續，實際每一步都被拒。

## 11. 次要但獨立的 VIDEO／JPEG 風險

Post C 的 intent 凍結 `effective_kind=VIDEO`，但 staging 實際是 JPEG：

- viewer AX 曾看到影片式控制；
- chooser 產出 JPEG；
- ImageIO 完整解碼為 1580×954；
- outcome statement 已明記 `type_match=MISMATCH`；
- 沒有執行 `media-kind-reconcile`；
- 沒有把 JPEG 冒充 VIDEO completion；
- 沒有把 JPEG 自動改記 PHOTO completion。

這代表即使高階模型決定修正 scan binding 死鎖，還必須決定：

1. 來源種類 VIDEO 與輸出容器 JPEG 的產品語意；
2. JPEG 是原始照片、影片預覽影格，還是 LINE 導出的其他形式；
3. 日常 `download-check` 應以 magic MIME 的實際輸出種類記 completion，還是要求來源種類與輸出種類一致；
4. `media-kind-reconcile` 與 open restart 的先後順序。

現有 `download-check` 在 `src/line_backup_batch/notes.py:6652-6668` 會以 `_basic_file_check()` 的實際 kind 取代 intent 的 kind，因此若 scan gate 被合法解開，JPEG 可能被視為 `PHOTO` 並記 `DOWNLOAD_ONLY`。但本次沒有實測，不能宣稱它能直接完成，也不能拿來繞過目前 gate。

## 12. 根因候選與置信度

### H1：scan binding 語意不一致（高置信度）

證據：

- `_validate_attempt_origin_scan()` 接受 origin scan；
- `verify()`／`download_check()` 要求 latest-only；
- restart confirm 必然新增 scan；
- 測試刻意期待跨 scan verify 被拒。

結論：

> latest-only 本身是刻意保護，但沒有為「完成下載、來源 scan 仍有效、但不在最新 scan」的舊 attempt 定義合法收斂路徑。

### H2：restart scope 與全域未決 attempt gate 組合缺陷（高置信度）

證據：

- restart progress 只認 v3；
- v3 intent 要求 scope 外 attempt 為 STOPPED／NOT_SENT；
- Post C 為 DOWNLOAD_FINISHED 且不在 scope；
- 因而 v3 intent 被 `ANOTHER_MEDIA_ATTEMPT_UNRESOLVED` 拒絕。

結論：

> restart 的 scope 是精確授權，但 scope 外已完成下載的舊 attempt 沒有「已下載、待驗證但被新 scan 阻擋」這個可被 restart gate 接受的收斂狀態。

### H3：舊 attempt 的 VIDEO/JPEG 類型不一致（中至高置信度，但不是第一個拒絕點）

證據：

- intent 為 VIDEO；
- staging 為 JPEG；
- outcome evidence 明記 mismatch；
- 尚未 verify；
- kind reconcile 被 latest scan 與 open restart 雙重阻擋。

結論：

> 即使 H1 被修好，也還需要決定實際輸出種類與完成語意；不能直接把 JPEG 當成 VIDEO 完成。

### 已排除或降級的原因

- **鎖競爭**：串行重跑成功，`NOTES_LOCK_BUSY` 不是根因。
- **網路／GUI 未送出**：下載控制、chooser、post-confirm readback 與穩定檔案均有證據。
- **檔案損壞**：JPEG Hash 穩定，ImageIO 完整解碼 PASS。
- **權限問題**：staging 檔案可寫、可讀、可 stat、可 hash、可解碼。
- **單純 suffix 驗證錯誤**：目前命令在 `ATTEMPT_SCAN_BINDING_CHANGED` 就停止，尚未走到 suffix 檢查。
- **單純 ledger 損壞**：125 個事件與 previous_sha256 鏈可讀，tip 可定位；問題是狀態組合不可達完成，不是 JSON 損壞。

## 13. 最小合成重現

不要用真實帳本重現。可在 fixture 內建立：

```text
1. 建立 S1、post P、media M、post detail、media inventory。
2. 建立 v2 intent，綁定 S1。
3. 寫入 outcome=DOWNLOAD_FINISHED。
4. 建立 restart confirmation，scope 只含另一篇 X，不含 M。
5. 建立 S2 recovery scan，讓 S2 成為 latest。
6. 對 M 執行 verify，預期 ATTEMPT_SCAN_BINDING_CHANGED。
7. 對 X 執行 restart intent，預期 ANOTHER_MEDIA_ATTEMPT_UNRESOLVED。
8. reload 後執行 resume，預期 M 的 action=SCAN_BINDING_REVIEW_REQUIRED。
```

最小反證：

- 若新增「origin scan 仍有效時可 verify」的精確 reconciliation 規則，第 6 步應成功且不改寫舊 intent；
- 或若 restart gate 對 scope 外 `DOWNLOAD_FINISHED` 有合法收斂分類，第 7 步應成功；
- 或若 restart progress 能辨識 scope 外未決 attempt 並阻止 `INTENT_REQUIRED`，至少要避免假可繼續；
- 但只要能「重下」而沒有處理舊 attempt，就不算修好死鎖，只是增加第二個交易。

## 14. 為何不能用常見 workaround

### 14.1 不能重下

- 重下不會讓舊 attempt 的 `scan_id` 變成 S_NEW；
- 舊 attempt 仍會是 `latest_by_media` 的阻塞來源；
- 新 intent 也可能先被同一 gate 拒絕；
- 重下會增加不可逆交易與檔案歧義。

### 14.2 不能手改 `scan_id`

- intent 是追加式歷史，`scan_id` 是來源 provenance；
- 改寫會破壞 previous SHA-256 鏈與事件不可變性；
- 也不能誠實表示當時媒體細盤／派送發生在哪個 scan。

### 14.3 不能改寫 outcome 成 `STOPPED`

- 已有 GUI、chooser、檔案與 decode 證據支持 `DOWNLOAD_FINISHED`；
- 改成 `STOPPED` 會製造虛假歷史，並讓已下載檔案失去交易歸屬。

### 14.4 不能直接擴張 restart scope

- 現有 scope 有明確 confirmation、generation、scope digest；
- Post C 未經該次精確 scope 授權；
- 直接加入會繞過 Owner 對新路徑與額外空間的確認。

### 14.5 不能把 `download-check` 改成忽略 latest scan

- 最新 scan 是防止舊媒體清單污染新派送的保護；
- 直接拿掉會讓任何舊 attempt 都能在來源已變化時被誤驗證；
- 較安全的方向應是明確的 origin-scan reconciliation，而不是全域放寬。

## 15. 對目前任務的影響

- 指定列表的全卡片覆蓋已完成。
- Post A、Post B 已有完成檔案，且目前檔案存在。
- Post C 已有下載檔案，不能重送、不能假冒完成。
- restart batch 內兩個 candidate 仍 `INTENT_REQUIRED`，但 v3 intent 被 scope 外舊 attempt 阻擋。
- 最新狀態不是 `COMPLETED`，而是 `BLOCKED`。
- 49 篇 `DETAIL_PENDING` 尚未細盤；即使 `POST_DETAIL_PENDING` 本身不必然阻擋其他合格篇，目前的 `ANOTHER_MEDIA_ATTEMPT_UNRESOLVED` 是更高階的全域阻塞。

## 16. 建議高階模型回答的問題

1. 舊 attempt 的完成驗證應該用「origin scan 仍有效」還是「必須 latest scan」？若要保留 latest-only，應如何在不改寫舊 intent 的前提下允許合法的舊 attempt 收斂？
2. restart confirmation 的 recovery scan 是否應把 scope 外未決 attempt 一起納入「必須先解決」的前置條件，而不是讓 confirm 成功後才形成死鎖？
3. restart progress 只辨識 v3 是否應改成能顯示「scope 外舊 attempt 阻擋中」，避免表面 `INTENT_REQUIRED` 但實際不可派送？
4. VIDEO intent 下載成 JPEG 時，日常 `download-check` 應記哪個 kind？是否需要新的「actual output kind」事件，而不是要求來源 kind 與容器一致？
5. 是否需要一個明確、不可覆寫的 `attempt-resolution` 或 `scan-binding-reconcile` 事件，讓已下載、來源仍有效但不在最新 scan 的 attempt 進入 verify，且不建立新下載？
6. 這些規則修正後，如何用 state-machine 測試保證：
   - 不重送；
   - 不覆寫既有 completion；
   - 不擴張 restart scope；
   - 不讓舊 UNKNOWN 被誤解鎖；
   - 不把 scope 外項目誤記成已完成或已停止？

## 17. 實際執行與未執行項目

### 已實際執行

- 讀取 `SKILL.md` 與相關入口說明；
- 讀取 125 個永久事件與 tip；
- 重跑 `summary`、`restart preview`、`resume` 的唯讀投影；
- 讀取既有 receipt 與 command stdout；
- 核對 staging、Post A、Post B 的 stat／SHA-256／file type；
- 重跑一條既有 regression test；
- 建立本報告。

### `NOT_RUN`

- 真實 LINE 下載控制未在本輪再次派送；
- 真實 chooser 未在本輪再次確認；
- 未進行新的完整 E2E 下載；
- 未驗證跨 Session 後可完成 Post C；
- 未測試混合附件 chooser；
- 未執行 `download-check` 成功路徑；
- 未執行 `media-kind-reconcile`；
- 未執行 activation／completion；
- 未證明 JPEG 是照片或影片預覽；
- 未證明 latest-only 是產品作者唯一接受的語意，只證明目前程式與測試如此。

## 18. 六類狀態分開回報

```text
PRIMARY_OUTCOME_STATUS       = BLOCKED
IMPLEMENTATION_STATUS        = NO_CHANGES_TO_PRODUCT
CORE_ACCEPTANCE_STATUS       = BLOCKED
REQUIRED_VERIFICATION_STATUS = PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS= NOT_RUN
TASK_CLOSURE_STATUS          = BLOCKED
```

其中：

- `PRIMARY_OUTCOME_STATUS=BLOCKED`：指定列表備份未完成；
- `IMPLEMENTATION_STATUS=NO_CHANGES_TO_PRODUCT`：本報告沒有修改產品程式或真實交易；
- `CORE_ACCEPTANCE_STATUS=BLOCKED`：Post C 與 restart batch 未收斂；
- `REQUIRED_VERIFICATION_STATUS=PARTIAL`：來源、事件、檔案、投影與既有測試有核對；沒有完成新的真實下載驗證；
- `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`：沒有獨立角色或外部審查；
- `TASK_CLOSURE_STATUS=BLOCKED`：根因問題仍需產品語意決策與合法修法。

## 19. 最終判決

目前最精確的產品缺陷描述不是「下載失敗」，而是：

> **系統能正確保存下載完成，也能正確要求新 recovery scan；但它沒有一個合法狀態，讓「來源 scan 已不是 latest、但來源證據仍完整且已完成下載」的舊 attempt 完成 verify。restart 的 scope 又只接納 v3，且 v3 被 scope 外舊 attempt 的全域 gate 阻擋，造成 append-only 安全規則彼此鎖死。**

Post A、Post B 的完成不能被誤稱為整份列表完成；Post C 也不能被重下或假冒完成。最高價值的下一步是先把這三個狀態語意（origin scan、latest scan、restart scope）定義成一個可測試的收斂狀態機，再決定是否需要新事件或只修正 gate 的判斷範圍。
