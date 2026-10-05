# 獨立審查後交接

Plan Review PASS。plan-contract.json 將 byte-for-byte 複製為 handoff.json，按 frozen literal paths 序列修復身份／snapshot缺口，再跑新 red-green、build／full tests／replay／provenance／preservation，最後獨立 Acceptance。已授權本機步驟不用再次詢問。

共享單一 CG snapshot 指 NativeObservationSession 明確呼叫 cgInventory 的那份資料；ProductionObservationSource 的 AX matching 仍會自行讀 CG provider。本輪不宣稱整個 OS acquisition 是原子操作或總共只有一個 OS CG call。

保持既有 dirty work、历史資料與权利。LINE／production／download未執行；真正需要當下 LINE 畫面才請使用者開到前景。沒有 native controller admission receipt；不手改controller state。
