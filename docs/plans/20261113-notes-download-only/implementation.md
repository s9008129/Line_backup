# 記事本下載任務收斂：實作與交接

## 意圖與需求界線

Owner 要求 Agent 單純下載指定記事本媒體，不自行播放、拖曳時間、切倍速、分析內容，亦不為媒體種類另做 GUI 取證。Owner 已選擇取消 ImageIO／ffmpeg 完整解碼，只保留基本檔案檢查。本次修正不是把預覽影格證明成來源照片，而是把完成語意改為「下載結果已保存」，不再以來源內容種類作完成前提。

本輪不操作 LINE、真實照片、永久帳本或既有 attempt；不以這份開發交接取代日常正式 Prompt。

## 實作

- 新增 `download-check --records-root ... --session-id ... --attempt-id ...`。延用現有 latest-attempt、下載完成結果、scan binding、本機異動與不可覆寫命名交易保護；不建立下載 intent。
- 基本分類固定使用 `/usr/bin/file` magic MIME，核對工具 hash 與檔案前後一致、MIME／suffix 一致；不播放、不呼叫完整解碼器。簽章辨識不保證內容可解碼或與服務端原件一致。
- 新 `verification/v2` 與 `completion/v2` 保存 `FILE_SIGNATURE`／`assurance=DOWNLOAD_ONLY`／`content_verified=false`。保留原 intent／outcome／key；實際下載種類可以不同於 intent 種類。summary 另列 `assurance` 與 `downloaded_kind`，六類業務狀態不變。
- 新媒體可使用 `UNCLASSIFIED`，對應普通 `intent/v4`。舊媒體必須沿用 key；同一貼文與其餘身分相同時，禁止藉 UNCLASSIFIED／PHOTO／VIDEO 切換重新建 key。
- `outcome=UNKNOWN` 經合法 `reconcile=DOWNLOAD_FINISHED` 後可檢查原檔；不需要新下載或種類對帳。
- `restart resume --download-only` 使用新版 copy plan／candidate，仍需原精確 scope 與新 recovery scan。基本檢查候選不能被 legacy full-decode 接口當成完整解碼結果。
- 明確 text/plain、text/html、application/pdf、application/zip 的普通下載結果可追加 `download-exclusion/v1`，保留 staging、計 EXCLUDED、不計 completion。這只排除本次下載結果，不證明來源媒體本身不是照片或影片。未知 MIME、不支援的媒體格式、suffix 不符保留欠件；restart scope 的非媒體結果不自動修改已確認 scope。
- 舊 verification／completion／restart 事件維持可讀且不改寫；新版 assurance 與 schema 必須配對，舊讀取器會拒絕新格式，不能在寫入新事件後用舊程式繼續。
- Skill、references、手冊正式 Prompt 與記事本常駐規範同步。相簿規則及程式不變。

## 驗證與狀態

環境：Darwin 27.2.0、`/usr/bin/python3` 3.9.6、`/usr/bin/file` 5.41。

| 實際命令／範圍 | 結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0，73 tests PASS |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | exit 0，269 tests PASS |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0，包含 download-check |
| `git diff --check` | exit 0 |
| 新 download-check 與既有 media-kind-reconcile 的實際 CLI 合成案例 | 已包含於 269 項，PASS |
| 真實 GUI／LINE E2E、混合附件 chooser、跨 Session 實機恢復、外部副本 | NOT_RUN |

本次新增 36 項測試（基本簽章 14、下載／交易整合 22），完整回歸總計 342 項。新增範圍涵蓋種類不一致、UNCLASSIFIED、UNKNOWN 收斂、nonmedia 排除、來源與工具漂移、偽造 schema／事件引用、restart assurance 邊界、原件與舊事件保留，以及真正 CLI 派送。舊 strict verifier 的解碼回歸仍保留；這些是相容性測試，不會成為日常下載動作。

第一輪完整 notes 回歸有兩個舊測試預期未同步「明確非媒體應排除」；改成以真 PNG 配錯 suffix 測拒絕，文字另測 exclusion 後通過。後續 CLI 成功案例發現主 command 白名單漏列新 download-check，且既有 media-kind-reconcile 也漏列；兩者已補入並以實際 CLI 測試覆蓋。其餘 helper 測試中對新 scan 摘要及未刷新 fixture 的錯誤斷言已修正；最終完整回歸通過，不把前輪結果寫成 PASS。

原始統合 notes 測試輸出保存在專案私有 `.local/line-backup/tasks/download-only-20261113/notes-tests.log`；相簿結果由本輪命令回傳確認，私有 progress 保存摘要，不冒稱為重新保存的原始 stdout。

```text
PRIMARY_OUTCOME_STATUS=PASS（本次授權的開發實作範圍）
IMPLEMENTATION_STATUS=DONE
CORE_ACCEPTANCE_STATUS=NOT_RUN（Owner 正式日常試用）
REQUIRED_VERIFICATION_STATUS=PASS（開發回歸與 CLI）
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=PENDING_ACCEPTANCE
```

本輪子代理均為實作輔助，不構成獨立審查或接受。Owner 後續試用沿用正式日常記事本 Prompt 與有效前景交接；不需要逐項選模式或手填內部 JSON。

## 下一步建議

Owner 可另行交接必要的獨立審查，再依正式日常入口試用同一列表。由正常流程識別原 attempt 並檢查原 staging；不得為測試重下、重置帳本或自行合併 master。未實測的真實 GUI、混合附件 chooser、跨 Session 實機恢復及外部副本維持 NOT_RUN。
