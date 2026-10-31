# 永久帳本實作報告

## 目前候選與授權

規格見 [plan.md](plan.md)，交接見 [handoff.md](handoff.md)。Owner 明示本次不需要獨立審查、過度工程化審查或 independent acceptance；未執行也不宣稱獨立PASS。必要本機測試與遷移對帳仍由實作者執行。

起始 HEAD：e573e0522dd11d10d7d5f43eb03bfc4d4c399843，原分支 fix/save-all-gate-20261030；本次候選隔離於 fix/permanent-backup-records-20261031。產品不 merge。既有兩份未追蹤驗收文件原樣保留、不提交。

## 已實作

- 永久帳本 collection、UUID索引、獨立 records_root、必要證據保全與遷移收據；舊帳本原位元保留，舊入口拒絕寫入。
- 完成事實與本機照片現況分離；整本缺席保留完成與不重下，部分缺檔/hash/inode/symlink異常阻止新派送。
- 新批次目的地以追加事件綁定，舊completion路徑不改；UNKNOWN/pending不解除。
- 新CLI與Skill/references/唯一Prompt/README/記憶說明同步，照片預設backup，紀錄在backup-records；Owner不多填UUID或JSON。
- ImageIO、離線OCR與GUI定位方法保留；永久私人紀錄加入Git忽略。

同角色助手分別協助文件與合成測試，未提供獨立審查/驗收；dispatch未指定model/effort override，未取得provider usage或成本量測。

## 實際驗證

所有命令工作目錄：/Users/hsiaojohnny/dev/Line_backup；Python為 /usr/bin/python3，使用現有相符Swift SDK編譯合成測試decoder，不修改系統工具鏈。

| 檢查 | 命令或方法 | 結果 | 私人證據 |
|---|---|---|---|
| 既有紀錄回歸 | PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py | 73項PASS，exit 0 | daily-tests.log |
| 舊搬移相容 | PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_relocation.py | 3項PASS，exit 0 | relocation-tests.log |
| 永久帳本與CLI | 同上 unittest discover，pattern=test_permanent_records.py | 18項PASS，exit 0 | permanent-tests.log |
| 遷移前盤點 | 三份帳本、所有原紀錄SHA-256及照片SHA-256/metadata | PASS：3份帳本、10本完成、626個照片檔、0 pending | migration-before.json |
| 證據盤點 | 既有reference與實際digest比對 | PASS，0 evidence drift | evidence-preflight.json |

私人證據均位於 .local/line-backup/tasks/20261031-permanent-records/，不提交。早期文件連結檢查因尚未寫本報告而發現implementation.md缺檔；已建立報告，最終文件檢查稍後記錄，不把早期失敗改寫為PASS。

## 遷移與整合結果

- 真實三份帳本已安全複製至永久區；逐份 UUID、原始事件/anchors hashes 與 10 本完成事實核對一致。照片區 626 個檔案的SHA-256、大小、mtime、ctime、inode均未變；不代表這626個檔案全經本輪像素解碼。
- 原始帳本保留，新版舊入口與舊relocation寫入入口拒絕再寫；active-task已切換v2永久records_root並讀回。
- 實際遷移命令：`PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/20261031-permanent-records/migrate_current_records.py`，exit 0。私有證據 migration-run.log、migration-after.json、active-task-before.json、groups-readback.json、active-memory-readback.json。
- 真實CLI讀回 groups=3、memory schema=v2、dispatch_authorized=false，exit 0。沒有修改completion或把人工聲明升格。
- 文件檢查：14份Markdown、52個本地引用、程式區塊、Skill基本frontmatter及私人帳本Git忽略均PASS；git diff --check exit 0。早期缺少報告的連結已由建立本檔解決。
- 全部必要本機回歸為73＋18＋3＝94項PASS。新版測試包含合成ImageIO、實跑CLI、照片刪除/漂移、UNKNOWN/pending、跨列表、帳本/索引異動、遷移中斷與重跑、證據保全、已知帳本缺失及Finder metadata。
- 同角色助手的測試不是獨立驗收；本次獨立審查/independent acceptance依Owner明示免除，標NOT_APPLICABLE_OWNER_WAIVED而非PASS。

## 交付與限制

Git checkpoint/推送與遠端HEAD核對於本報告完成後執行，精確產品候選以提交與Draft PR為準。未操作LINE、Save All或外接硬碟，未刪除或搬動照片；外接副本未驗證。記錄保存範圍為保留本專案的永久帳本，不包含整個專案或磁碟遺失。

PRIMARY_OUTCOME_STATUS: PASS
IMPLEMENTATION_STATUS: COMPLETE
CORE_ACCEPTANCE_STATUS: PASS_LOCAL_REQUIREMENTS
REQUIRED_VERIFICATION_STATUS: PASS
INDEPENDENT_ACCEPTANCE_STATUS: NOT_APPLICABLE_OWNER_WAIVED
TASK_CLOSURE_STATUS: PENDING_GIT_DELIVERY

## 產品與測試候選來源SHA-256

- src/line_backup_batch/daily.py：`20031ef9c8ad6f5eb695cee192568c3afd1a75c3b213591cb3f9254e9a83f970`
- src/line_backup_batch/record_store.py：`f42922c725b463f25d02b30a5584837b547f41cda3c507cdb8bef77f7938ae03`
- src/line_backup_batch/relocation.py：`abd8d0a3a8a7b0edc012d522db277334cf1565a48b31130fc1d4e91ff49827a1`
- tests/test_daily_records.py：`cf6961d4b49cd8f7f3beebe0319d1efbe6954835509705c50294c6d9e8bdfd09`
- tests/test_permanent_records.py：`22610ab940ce6cb99f324eb432e8b813281c60e1efe0ffd41def3db7f4e07713`
- tests/test_relocation.py：`1be230121a8901d03e7fff745759b6abf5e537133331523481783091af1875c3`
