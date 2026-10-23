# 2026-10-23 三分支收斂、歷史封存與 master 整合紀錄

## Owner 目標與最終裁決

Owner 先要求由 GPT-6 Luna 深度盤點，再由 GPT-6.1 Sol 決定可退役與可合併範圍；隨後明確要求「只保留最必要的 3 個」。第二次指示取代第一輪保守保留 28 支的方案。Sol 選定本機與 GitHub 均只保留以下三支，其他歷史改用封存 tag、私有 Git bundle 與原 worktree 保存。

| 保留分支 | 用途與精確基線 | 限制 |
| --- | --- | --- |
| `master` | 正式整合主線；本提交之前遠端為 `43eb8f9a37acfd655ce9f1c544b8a4e65ec86387` | 本提交僅合併 PR35 文件與本報告，沒有把未核准產品程式灌入主線 |
| `v43-ab/codex-rev28` | 原主工作目錄 HEAD `1b9a010aeba2e75a406d842be123d7251501548c`；遠端 tip `6e514a7029638b6ee390bde7ddf311b2c3c63f2b` | 本機原有 733 項修改保留，未重置到遠端；PR31 仍受外部禁止合併結論約束 |
| `implement/agent-resume-p0-20261022` | 本機／遠端 `fdd36a4a400ea95298a69b67e2c746f5e7d23ce5`；PR32 | 保留目前接續功能工作，未將舊 review 升級為新版核准 |

盤點起點為 35 個本機分支、33 個 origin 參照。33 個參照包含 symbolic HEAD 與兩個特殊 PR tracking refs，實際 GitHub heads 是 30 支。因此最終收斂是本機 35→3、GitHub heads 30→3；特殊 tracking refs 另外封存並移除，symbolic `origin/HEAD` 保留。

本提交整合 PR35 的 `AGENTS.md` 任務層級授權修正，以及本報告。PR34 早已在 master，不重複套用。產品程式、照片、state、grant、ledger、F/G Task、Harness 與測試框架均不在本次提交差異內。

## 產品分支不能以清理名義直接合併

| PR | 真實依據 | Sol 裁決 |
| --- | --- | --- |
| [#31](https://github.com/s9008129/Line_backup/pull/31) | 外部 review 明確 `NOT_APPROVED_TO_MERGE`；相對 master 約 1,900 檔、80 萬新增行，含舊實驗與證據 | 保留分支及原實機工作目錄；本次不 merge |
| [#32](https://github.com/s9008129/Line_backup/pull/32) | 外部 review 為 `CHANGES_REQUIRED`；已有後續修正與離線證據，未見新版正式核准；原生取消接續未驗證 | 保留為現行開發分支，下一步做精確新版 review |
| [#33](https://github.com/s9008129/Line_backup/pull/33) | 外部 review 指出 fixture generator 可遞迴刪除任意既有 case 目錄，要求修正；未見正式新核准 | 封存本機／遠端不同 tip、未提交內容及完整 review；退役分支，不 merge 產品內容 |

PR33 本機原 tip `52be0de27c49ea9e9c1703d3b3aef8025ff31991` 落後遠端 `a2dc364df9d7` 兩個 commit，沒有 local-only commit，但 worktree 有 3 項變更；已分別封存兩個 tip，沒有 reset 或覆蓋 dirty 工作。遠端 `bbf9b13`、`a2dc364` 是 CI 手動同意與費用防線修正，不構成 fixture 安全問題已解決的證據。

## 封存與退役方法

1. 保存原 local／remote ref 與完整 SHA，逐支查 ancestry、patch／檔案差異、PR、review 及 worktree 狀態。不能只憑日期或分支名稱判定內容可丟棄。
2. 建立本機 annotated archive tags，包含 local 與 remote 各自 tip。無法證明已合併的 fork 也完整保留，不以刪 ref 冒稱已 merge。
3. 建立完整 Git bundle，驗證成功且核對 hash 後才退役分支。歷史 tags 與 bundle 不推送，以免發布舊私人證據或觸發舊 workflow 的 tag 事件。
4. 可達 worktree 在原 SHA `checkout --detach`，比對前後 porcelain、staged 與 unstaged binary diff hashes；既有檔案及 untracked 內容留在原目錄。沒有對 dirty worktree 使用 reset、stash 或 clean。
5. 失聯 worktree 保留登記；先備份 worktree Git metadata，再用 `git --git-dir=<原 worktree gitdir> update-ref --no-deref HEAD <原SHA> <預期原SHA>` 將 HEAD 固定為原 commit。核對 HEAD 與 index hash。這是 metadata 操作，不代表已檢查未掛載磁碟中的檔案；掛載後仍須重查。
6. 確認全部退役分支不再被 symbolic worktree HEAD 占用、tag 指向預期 SHA 後，才逐名移除 local branch refs。部分使用 `-D`；安全依據是已驗證封存，不假稱它們已合併 master。
7. 遠端退役以精確舊 SHA lease、atomic push 刪 ref，避免刪掉盤點後有人更新的分支。先保存 GitHub PR 的 body、reviews、comments、commits、checks 與 SHA 對照。

共保留 54 筆 worktree 登記；盤點時 23 筆顯示 prunable，沒有執行 worktree prune 或刪工作目錄。兩個已合併文件 worktree 先前已乾淨 detach；三分支收斂階段另處理 22 筆，其中 12 個可達 worktree 的前後工作狀態與 staged／unstaged 差異相同，10 個失聯 worktree 僅處理 Git metadata，index hashes 未變。總計 24 個 worktree 改為同 SHA detached HEAD。

**Git tag／bundle 不包含未提交檔案。**未提交內容仍留在原 worktree；可達退役 worktree 另存私有 staged／unstaged patches 及 untracked 狀態清單。沒有將這些私有資料加入公開 repo。失聯磁碟的未提交內容屬未觀察狀態，不宣稱完成檔案內容驗證。

## 退役內容的重要個案

| 原分支／內容 | SHA／保存依據 | 裁決 |
| --- | --- | --- |
| `backup/rev28-before-v43-stage04-20260929-050811` | `67c4fad9` 是保留 v43 HEAD 的祖先 | 封存後刪分支別名 |
| `fix/capture-first-single-writer-20261016` | `9fd43096` 是原 handoff tip `66c852cb` 祖先；兩者都已 tag／bundle | 封存後退役 |
| 兩個 `handoff/one56-trial-20261018-...` aliases | 同為 `d979d873691c271b43134bc7b6995730fdfd6ab8`；此 fork 有獨有 commit | 明確由 tag／bundle 保存，不當成已合併 |
| `rev28-prelive-finalization` 與 Luna alias | 同為 `9cbaa114`，且為 v43 祖先 | 別名及失聯 worktree 原 HEAD 均已保存 |
| PR34 head | `32224722011789fd2b2d9a6f37cbf4402c50eeac`，已合併 master | 退役 local／remote head，文件 worktree 保留 |
| PR35 head | `35a8bfd2589c0681ba3979136d96d2a7227cd571` | 由本整合提交合併；遠端 head 待 master 推送讀回包含此 SHA、PR35 顯示 MERGED 後才刪 |
| PR12 governance head | `39584bbdab9874ebae8974e9371d97a33281c061` 是原 pilot 遠端 `516932df` 祖先 | 兩個 tip 皆已保存；PR12 原合併目的地是 pilot，並非 master |
| 原 `harness-v4.3-validation` | `d8be99904a46`，有獨有 legacy 驗證封存 | 只封存，不修改 Harness、不假稱已整合 |
| 原 `rev28-ci-prelive-hardening` | `7acfdff571ca`，22 檔含 workflow 與產品差異 | 完整封存，不 merge 未審內容 |

## 原 35 個本機分支逐支結果

這是相對 `origin/master@43eb8f9` 的盤點快照，落後／領先數不是功能完成度。worktree／PR 欄描述退役前狀態；失聯不代表沒有資料。裁決欄依 Owner 最後的三分支要求更新。

| 原本機分支 | 原 tip | 落後／領先 | 退役前 worktree／PR | 最終裁決 |
| --- | --- | --- | --- | --- |
| `backup/rev28-before-v43-stage04-20260929-050811` | `67c4fad9` | 8／91 | 無 | 封存後退役分支名稱；未提交內容留原 worktree |
| `codex/pr17-pre-down-evidence-only` | `8785174c` | 8／226 | 乾淨／#18 | 封存後退役分支名稱；未提交內容留原 worktree |
| `docs/agent-resume-handoff-20261022` | `0491393b` | 6／3 | 乾淨／#30 | 封存後退役分支名稱；未提交內容留原 worktree |
| `docs/agent-task-adaptive-authorization-20261023` | `35a8bfd2` | 0／1 | 乾淨／#35 | 封存後退役分支名稱；未提交內容留原 worktree |
| `docs/line-album-agent-cua-skill-20261023` | `32224722` | 1／0 | 乾淨／#34 MERGED | 封存後退役分支名稱；未提交內容留原 worktree |
| `docs/line-two-album-title-click-20261020` | `ba169556` | 8／184 | 失聯／#21 | 封存後退役分支名稱；未提交內容留原 worktree |
| `evidence/two-album-formal-e2e-20261021` | `0478ad69` | 8／184 | 失聯／#26 | 封存後退役分支名稱；未提交內容留原 worktree |
| `fix/capture-first-single-writer-20261016` | `9fd43096` | 8／188 | 無 | 封存後退役分支名稱；未提交內容留原 worktree |
| `fix/g0-governance-recovery-candidate-20261013` | `9b2fc1e9` | 8／175 | 失聯／#5 | 封存後退役分支名稱；未提交內容留原 worktree |
| `fix/g1-runtime-compatibility-20261013` | `ed22d202` | 8／182 | 失聯／#7 | 封存後退役分支名稱；未提交內容留原 worktree |
| `fix/sck-diagnostic-capture-first-20261015` | `2bd94af4` | 8／185 | 修改 8 項 | 封存後退役分支名稱；未提交內容留原 worktree |
| `handoff/one56-trial-20261018` | `66c852cb` | 8／212 | 乾淨／#13 | 封存後退役分支名稱；未提交內容留原 worktree |
| `handoff/one56-trial-20261018-d6de-backup` | `d979d873` | 8／210 | 無 | 封存後退役分支名稱；未提交內容留原 worktree |
| `handoff/one56-trial-20261018-preapproval` | `d979d873` | 8／210 | 無 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/agent-resume-ci-20261022` | `52be0de2` | 8／180 | 修改 3 項／#33 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/agent-resume-p0-20261022` | `fdd36a4a` | 6／21 | 乾淨／#32 | 保留：接續功能 PR32 |
| `implement/human-one56-a56-20261018` | `ef428da1` | 8／221 | 修改 13 項／#14 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/line-two-album-pilot-v1-20261014` | `4a0a4b96` | 8／177 | 乾淨／#10 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/line-two-album-v4-1-20261021` | `6a81326c` | 8／221 | 修改 3 項／#24 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/native-auto-click-f1-20261019` | `ed605b76` | 8／222 | 修改 5 項 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/native-auto-click-f1-cs-20261019` | `60939e4a` | 8／223 | 無／#17 | 封存後退役分支名稱；未提交內容留原 worktree |
| `implement/one-scroll-slice-20261016` | `22cee2bc` | 8／191 | 乾淨 | 封存後退役分支名稱；未提交內容留原 worktree |
| `master` | `43eb8f9a` | 0／0 | 合併準備中 | 保留：正式整合主線 |
| `plan/native-auto-click-20261019` | `ed605b76` | 8／222 | 乾淨／#16 | 封存後退役分支名稱；未提交內容留原 worktree |
| `plan/two-album-auto-20261019` | `c563cba5` | 8／220 | 無／#15 | 封存後退役分支名稱；未提交內容留原 worktree |
| `rev28-prelive-finalization` | `9cbaa114` | 8／92 | 無／#1 CLOSED | 封存後退役分支名稱；未提交內容留原 worktree |
| `review/g0-controller-route-20261013` | `1f8653a2` | 8／175 | 失聯／#4 | 封存後退役分支名稱；未提交內容留原 worktree |
| `review/line-one-click-diagnostic-20261014` | `8141a129` | 8／177 | 無／#8 | 封存後退役分支名稱；未提交內容留原 worktree |
| `review/line-two-album-e2e-public-20261014` | `26a0856d` | 8／2 | 失聯／#9 | 封存後退役分支名稱；未提交內容留原 worktree |
| `review/pre-down-evidence-only-20261019` | `60939e4a` | 8／223 | 外接磁碟失聯 | 封存後退役分支名稱；未提交內容留原 worktree |
| `review/runtime-entrypoint-20261013` | `e8286481` | 8／175 | 失聯／#6 | 封存後退役分支名稱；未提交內容留原 worktree |
| `review/sck-freshness-preflight-20261015` | `d0a4d65e` | 8／187 | 乾淨／#11 | 封存後退役分支名稱；未提交內容留原 worktree |
| `v43-ab/codex-rev28` | `1b9a010a` | 8／177 | 修改 733 項／#31 | 保留：原主工作目錄與 PR31 |
| `v43-ab/deepseek-rev28` | `472c283c` | 8／107 | 失聯 | 封存後退役分支名稱；未提交內容留原 worktree |
| `v43-ab/luna-rev28` | `9cbaa114` | 8／92 | 失聯 | 封存後退役分支名稱；未提交內容留原 worktree |

## GitHub 退役與 PR 狀態

實際遠端 30 支 heads 中，只保留三支指定分支。提交準備時已退役 26 支；最後 PR35 head 刻意保留到 master 推送且合併狀態讀回後才刪。刪除使用 expected SHA lease；沒有 force-push 改寫任何保留分支的歷史。

GitHub 共 29 份既有 PR metadata／review 快照已私有保存並逐份計算 SHA-256。退役分支對應的 PR 是 **CLOSED／封存，不是 MERGED／批准**。提交準備時，原本 OPEN 而因分支退役變成 CLOSED 的 PR 為：

#33, #30, #26, #24, #21, #18, #17, #16, #15, #14, #13, #11, #10, #9, #8, #7, #6, #5, #4, #3, #2（共 21 份）。

目前仍 OPEN 的只有 #31、#32、#35；本提交推送後 #35 應成為 MERGED，#31／#32 保留 open 並沿用原審查狀態。所有舊 review 仍可透過原 PR URL 與私有快照追溯；恢復歷史分支不會自動使 review 或 E2E 通過。

## 本機私有證據與保存查核

私有封存目錄名為 `Line_backup-branch-archive-20261023`，位於原 repo 同層，沒有加入 Git 或上傳。其內容包含：

- `baseline.json`、`three-branch-baseline.json`：原 ref／SHA、保留三支決策、PR 對照及主工作目錄基線。
- `archive-manifest.json`、`retired-branches.bundle`、`bundle-verification.txt`：完整歷史、tag mapping、bundle hash 與最終實際檔名的驗證紀錄。
- `github-pr-snapshots/`：29 份完整 PR 上下文及 reviews、comments、checks 快照。
- `worktree-metadata-before-three-branches/`：改動 worktree HEAD 前的 Git metadata 備份。
- `worktree-change-preservation/`、`worktree-detach-plan.json`、`worktree-detach-receipts.json`：dirty patches、狀態 hashes、同 SHA detach 方法及前後比對。
- local／remote 刪 ref 收據與推送後讀回；保留所有原工作目錄，不假稱 bundle 備份了 untracked 照片內容。

封存共 68 個本機 archive tags，包含 61 個 local／remote／特殊 tracking ref 對照及首輪 7 個短名稱 tags。最終 bundle 為 219,015,527 bytes，SHA-256 `13bc6bf2961dbade7d8d5a9246c8957370d933a25857f02aa59ad117c516dc73`；已針對最終實存檔名 `retired-branches.bundle` 執行 `git bundle verify` 並成功。首輪暫存檔改名的路徑疑義已由最終檔案重新驗證消除。

原主工作目錄保存基線：

- HEAD `1b9a010aeba2e75a406d842be123d7251501548c`，原 733 項狀態保留。
- porcelain 狀態 SHA-256：`729fa07dedc40ec2d691bb3149aee7b4f30824d2ecbd6a0053f576bca47fe34f`。
- 非 AGENTS 既有 tracked dirty binary diff SHA-256：`aa286db95b9d0a3809d4d0ad05f05e64f64061f83c88f3fd50bf1ffca634528d`。

盤點使用 Git refs、worktree、status、binary diff、ancestry、逐來源差異及 GitHub 真實 reviews；Sol 做最終裁決。提交前另由 Luna 深度閱讀實際整合差異與保存證據，草擬包含「意圖／做了什麼／驗證與結果／下一步的建議」的提交訊息，Sol 核對後才 add、commit、push。

驗證是 Git／文件整理驗證：`git diff --cached --check`、提交路徑與父提交核對、原工作狀態 hashes、bundle verify、分支和 PR 讀回；不冒稱產品測試或 LINE E2E。未操作 LINE、Save All、取消、下載或原圖驗證；未新增／重跑無關測試。master 及本次整合 tree 沒有 `.github/workflows/`，未派送 Actions，推送後仍需核對是否實際有 run。

## 還原與下一步

例如要恢復原 handoff fork：`git branch restored-one56 archive/20261023/local/handoff/one56-trial-20261018-preapproval`。遠端原 tip 對照位於 `archive/20261023/remote/<原分支名>`；local 與 remote 原先不同時，各自保留不同 SHA。也可先驗證私有 bundle 再匯入所需 tag；完整 bundle 含舊歷史證據，請保留本機，不公開上傳。

新工作以 master 為整合基底；接續功能仍在 PR32。優先核對 PR32 精確新版 source、現有修正與外部 review，不從封存資料重播 Save All。PR31 留作既有實機來源及 733 項未提交工作的保護分支。失聯 worktree 掛載恢復後再核對原 SHA、index 與未提交內容；不要為減少登記數而 prune。
