# Mac LINE 中斷接續 Runbook

適用版本：PR #32、`implement/agent-resume-p0-20261022`、Owner manifest 已建立。
本文件只描述既有 CLI／Node wrapper；不是 Save All 授權，也不代表實機 E2E PASS。

## 1. 開始前固定事實

```sh
git rev-parse HEAD
shasum -a 256 scripts/line_backup_agent_resume.py scripts/line_backup_agent_resume_cua.mjs
export TASK_ID='<Owner manifest task_id>'
export ROOT="$HOME/Library/Application Support/LineBackup/agent-resume"
```

必須同時具備：正確 task、當次 Mac 前景授權、LINE 群組／視窗可辨識、Owner 對新的 eligible 相簿授權。缺少任一項就停止，不以舊 Session 記憶或舊點位補足。

## 2. 唯讀快速恢復

```sh
/usr/bin/python3 -B scripts/line_backup_agent_resume.py \
  inspect --root "$ROOT" --task "$TASK_ID"
```

先核對 `checkpoint_sha256`、`generation`、`manifest_binding_sha256`，再讀：

- `task_phase`
- `next_safe_album_key`
- `next_safe_album_identity`
- `next_safe_ordinal`
- `next_safe_action`
- `first_blocker`、`pending_input`、`owner_action`
- `resume_metrics`（特別是 `prior_verified_rehash_bytes`、`prior_verified_decode_calls`）

正常結果只會是 `READY_TO_DISPATCH`、`READY_TO_VERIFY` 或 `COMPLETE`。
`BLOCKED_AND_PRESERVE_WHOLE_TASK`、`first_blocker != null` 或 `pending_input=true` 時：

1. 不按 Save All／Chooser。
2. 不刪除 lock、checkpoint、照片或臨時檔。
3. 只有 Owner 要求完整性稽核或核對既有 VERIFIED 內容時，才執行唯讀 deep reconcile：

```sh
/usr/bin/python3 -B scripts/line_backup_agent_resume.py \
  reconcile --root "$ROOT" --task "$TASK_ID"
```

`reconcile` 會對既有 VERIFIED 相簿重新 SHA-256 與 ImageIO decode，屬明確的完整稽核，不是每次恢復的必經步驟；它不會把 UNKNOWN 升級為 VERIFIED。

## 3. 接上既有 PR28 Agent 入口

使用既有 PR28 的 `app` handle 與 GUI host identity，不建立新的 OCR／AX／GUI framework：

```js
import {openAgentResumeSession} from './scripts/line_backup_agent_resume_cua.mjs';

const session = await openAgentResumeSession({
  taskId,
  host: existingPr28HostIdentity,
  app: existingPr28App,
});
const state = session.preflightResult;
```

`preflightResult` 是本次快速 preflight 的 checkpoint 視圖；不得把上一 Session 的截圖、AX／OCR 結果或座標當成目前證據。

## 4. FRESH GUI 定位

1. 重新取得 LINE 當前群組、視窗、列表的 screenshot + AX + Vision OCR。
2. 以 `next_safe_album_identity` 的日期、張數、名稱及 disambiguator 交錯核對；舊畫面位置只可當 hint。
3. 目標不在當前可見區域時，做有界捲動；每次保留前後截圖／AX／OCR 與可觀察位移。
4. 進入詳細頁後，再核對相簿身分與照片總數；不同群組、不同日期／張數或不明卡片不得點擊。
5. 只有 fresh identity 成立、目的地仍為空，且 grounding evidence 是當次保留的原始檔 bytes SHA-256，才可呼叫：

```js
await session.saveAll({
  albumKey: state.next_safe_album_key,
  grounding: freshSaveAllGrounding,
  resultEvidenceSha256: sha256OfRetainedSaveAllEvidence,
});
```

接著依 Chooser 的當次畫面重新核對，再呼叫一次 `session.confirmChooser(...)`。這兩個呼叫各自只允許觸發既有 `app.click(point)` 一次；未知結果不得重呼。

## 5. 驗證與下一本

Chooser `RETURNED` 且檔案數與相簿 identity 一致後，只驗證目標相簿：

```js
await session.verifyAlbum({albumKey: state.next_safe_album_key});
await session.close();
```

再執行第 2 節的 `inspect`。成功時目標應為 `VERIFIED`，`next_safe_ordinal` 指向下一本；先前 VERIFIED 相簿的快速恢復指標應維持：

```text
prior_verified_rehash_bytes=0
prior_verified_decode_calls=0
```

若目標為 partial、UNKNOWN 或缺少 Save All／Chooser RETURNED 證據，輸出精確 blocker 並保留所有檔案；不得重送、猜 RETURNED、升級 VERIFIED，或以 `--force`／刪 checkpoint 繞過。

## 6. Reboot／新 Session 驗收順序

1. 第一本新相簿 F 完成 Save All、Chooser、逐檔 SHA-256／ImageIO、VERIFIED readback 與 clean close。
2. Owner 正常重啟 Mac，關閉舊 Codex Session；不沿用舊 host／舊點位。
3. 新 DeepSeek Session 只執行第 2 節 `inspect`，確認 F 已被跳過且 `next_safe_ordinal` 指向下一本。
4. 以 fresh GUI evidence 定位不同的 eligible 相簿 G，完成 G 的 Save All、下載、驗證與狀態讀回。
5. 若 F 或 G 的狀態是 UNKNOWN／PARTIAL，停止並只交付 blocker；本 Runbook 不提供自動重送路徑。

真實 Mac E2E 尚未由本文件產生；完成兩本不同相簿的實機下載、完整驗證與新 Session 接續前，維持 `CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY`。
