# Codex CLI /goal — Rev25 Bootstrap Recovery

Use this only when the local clone is still at `d06384510e13b5334414777f4d3e688b8126048c` (or another stale clean `master`) and cannot see the Rev25 repair commit/files.

```text
/goal

本輪先解除 Rev25 stale-clone blocker，解除後直接銜接 repo 內最新的 GOAL-2026-09-19-rev25-final.md。這是一個零 LINE GUI 的 bootstrap；它不授權任何 LINE 點擊。

【已知遠端事實】
GitHub repository：s9008129/Line_backup
required repair baseline：
8fb622e4f2a25a2b1297894855303fdc671dafd3

canonical plan 檔名與位置：
repo root / PLAN-2026-09-19-rev25-final.md

canonical goal：
repo root / GOAL-2026-09-19-rev25-final.md

不要再要求：
/Users/hsiaojohnny/Downloads/PLAN-20260919-rev25-final.md
那不是 canonical path，而且檔名也不同。

【Step 1 — local safety gate】
執行：
git status --porcelain=v1 --branch
git remote get-url origin
git rev-parse HEAD

只有在以下全部成立時才繼續：
1. branch = master
2. 工作樹與 index 乾淨
3. origin 指向 s9008129/Line_backup

若任何一項不成立：停止並精確回報。
禁止 stash、reset、rebase、cherry-pick、force、刪除或覆寫使用者檔案。

【Step 2 — 明確允許 fetch】
執行：
git fetch --prune origin master

fetch 是本 goal 明確授權的 network/git metadata 更新，不是 GUI 行為。

fetch 後執行：
git cat-file -e 8fb622e4f2a25a2b1297894855303fdc671dafd3^{commit}
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 origin/master
git merge-base --is-ancestor HEAD origin/master

三個 exit code 必須全部為 0。

若 required commit 在 origin/master 仍不存在，或 local HEAD 不是 origin/master ancestor：停止並回報；禁止用 reset/rebase/cherry-pick 解決。

【Step 3 — 明確允許純 fast-forward】
重新確認 git status 仍乾淨。
然後只執行其中一種：
git merge --ff-only origin/master

或：
git pull --ff-only origin master

不要兩個都做。

若無法純 fast-forward：停止，保留現場，不做任何替代修復。

【Step 4 — sync acceptance】
執行：
git status --porcelain=v1 --branch
git rev-parse HEAD
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 HEAD
test -f PLAN-2026-09-19-rev25-final.md
test -f GOAL-2026-09-19-rev25-final.md
sha256sum PLAN-2026-09-19-rev25-final.md GOAL-2026-09-19-rev25-final.md

全部成功後，讀：
PLAN-2026-09-19-rev25-final.md
GOAL-2026-09-19-rev25-final.md

接著直接依最新 GOAL 從 Phase 0 繼續，不要回到舊的 d063845-based preliminary instructions。

【仍然有效的硬限制】
- bootstrap 與 Phase 0～3 都是零 LINE GUI。
- 不點 LINE、不 bring-to-front、不捲動、不送鍵盤。
- 不點 Save All、不碰 chooser、不下載。
- 不修改 57 張既有備份。
- 不改寫 frozen evidence。
- 真正 GUI Phase 4 仍必須等最新 GOAL 規定的 gate-6 明確 owner 授權。
```
