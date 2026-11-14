# Notes v1 凍結相容 fixture

此目錄只含合成、去識別化的 Notes v1 帳本，用於證明新 reader 可讀舊資料，且不會把 legacy opaque evidence 升格成 v2。

- 來源 writer：commit `e89f856582a7a4101c1ecb15fc416faf5ed8ac36` 的 `src/line_backup_batch/notes.py`。
- `notes.py` SHA-256：`9cdb1f75d19ae61939b98fbea3c0fbe95367e8caef6f69b1c3724946804c36f9`。
- `fixture.json` 記錄 event 種類、固定 list UUID、來源版本與 legacy evidence digest。
- `golden.json` 是同一凍結 writer 重開 fixture 後的 `summary`／`memory` 投影；根路徑已改成 `__NOTES_V1_BASE__`。
- `collection_template/` 保留舊 writer 的 v1 event 結構與 opaque evidence bytes。測試複製到隔離 temp 後，只替換根路徑並重建依路徑改變的既有 hash chain；不會改用新 writer 產生 events。

測試另核對讀取前後 event bytes 完全不變、legacy evidence 分類保持 `LEGACY_OPAQUE`，以及新寫入仍以 `EVIDENCE_BUNDLE_REQUIRED` 拒絕舊 opaque 格式。
