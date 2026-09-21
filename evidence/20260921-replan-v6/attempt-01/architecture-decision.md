# Phase B — S3 安全判定架構決策（architecture-decision）

- **TASK**: LINE Album Backup；`旻謙允禎成長日記` / `2024/05/13～05/17` / count 57
- **GUI_INPUT_COUNT**: `0`（本文件純離線設計決策）
- 前置證據：`v4-failure-analysis.md` / `.json`（Phase A）

## B.1 S3 真正需要證明的是什麼？

S3 的唯一任務：在 **current frame** 上，決定「一個可派送（但本輪永不派送）的候選點」是否位於**正確目標卡**的**安全 interior**。必須維持的性質（A–G）：

| # | 必須維持的性質 | 判定方式（本輪提案） |
|---|---|---|
| A | exact target identity | 對 current frame 做 OCR，title 必須匹配 `2024/05/13~05/17`（machine-read，非記憶） |
| B | expected count 不 mismatch | current frame 的 count OCR；可讀且非 57 → refuse；不可讀 → 記錄（沿用 frozen 語意） |
| C | candidate 由 immediate frame 推導 | `[tx0+12, center_y]` 由本 frame 的 OCR title bbox 導出；無歷史座標、無 v4 fallback |
| D | candidate 位於 target card 的安全內部區域 | caption strip 必須由上、下兩個 **content band** 夾住（band 以 ROI 內「每列內容佔比」判定），candidate 與兩 band 的距離 ≥ `sep_min` |
| E | 與上／下相鄰 card、其他 destructive UI 有足夠 separation | strip 內除 title/count 外必須**恰好只有一個** content cluster（該卡的 ⋮），且 candidate–⋮ 間距 ≥100 px、大小有界 |
| F | 不使用 historical coordinate | geometry 必須綁定 **frame SHA-256**；工具原始碼不得含歷史點；自測驗證候選點隨 frame OCR 變動 |
| G | uncertainty ⇒ fail closed | 任何無法建立 ROI / 無法解析結構 / strip 內容歧義 → 一律 refuse，無 best-effort ELIGIBLE |

**選型標準（唯一）**：哪個方案能最直接證明「這個由 current-frame 推出的點，確實在正確 target card 的安全 interior」。**不以「哪個比較容易 pass」作為標準。**

## B.2 三個架構選項評估

| 維度 | Option 1：維持 full-screen whole-row mean（status quo v4） | Option 2：LINE-window ROI + 整列 mean（改良 domain） | Option 3：current frame 的 target-card local ROI＋局部結構證據（本輪採用；含 Option 2 的 ROI 來源） |
|---|---|---|---|
| 核心安全論證 | 無：row 平均混合整個螢幕；通過與否由無關內容決定 | 「在窗口範圍內，candidate 上下找得到亮列」 | 「在窗口 ROI 內，以本 frame 的局部結構證明：candidate 位於 target card 的 caption strip，strip 由上下 content band 夾住，且 strip 內唯一的控制點是 ⋮，距離足夠」 |
| Safety property 強度 | 最弱：margin_above 可量到 wallpaper/menu bar（Phase A 已證；904/338/1074 px） | 中：band 位置改由窗口內容決定，但仍是「整列亮度」單一統計 | 最強：band、strip、控制點三者都以**本 frame、本 ROI 的局部內容**定義，並互相交叉約束 |
| Failure mode | domain mismatch（已證）；pass 依賴螢幕上無關亮列（arrangement-luck） | ROI 取得方式不受約束時，可能截窄/位移，使 band 落在錯誤位置而不自知；無法偵測 strip 內其他控制點或歧義 | 抽取不確定時的 refusal 較多；常數需以證據校準（已記錄理由）；title 不可讀時無法進行（但此為 A 的必要條件） |
| False-positive risk | 高（Phase A：三個畫面都靠無關列產生 margin_above） | 中（ROI 內「任一列」變亮即可當 band；未證 strip 屬於 target card、未證 ⋮ 距離） | 低：要同時滿足 (i) title 在 ROI 內縮排≥8px 且右尾≥120px、(ii) 上下 content band ≥20 列、(iii) strip ≥40 列且內容佔比≤0.30、(iv) strip 內恰好一個 ⋮ cluster、(v) candidate 距兩 band ≥max(24, title_h)=27px、(vi) candidate 距 ⋮ ≥100px |
| False-negative risk | 低（幾乎都 UNSAFE；無安全意義） | 中（ROI 邊界略偏即可能誤 refuse） | 中（多項 fail-closed 條件使部分「其實安全」的畫面被拒絕；本輪接受，因為拒絕成本遠低於誤點） |
| Dependency | 無（現狀） | 需要「LINE window geometry」輸入與其 provenance | 同 Option 2 的 geometry 輸入，加上 frozen OCR（title/count）與本 frame 背景色取樣 |
| 需要 GUI input？ | 否 | 否（geometry 可由 read-only AX window bounds 或離線抽取取得） | 否 |
| 是否維持 fail-closed | 是，但「安全的 UNSAFE」與「碰巧的 ELIGIBLE」無法區分 | 是（未達門檻即拒絕），但通過時的安全論證仍薄弱 | 是：每個無法證明的結構都對應明確 refusal code（7/8/9/10/11） |

### 為什麼不是 Option 1

Phase A 已證明：v4 的三個 `margin_above` 是 wallpaper/menu bar 的距離；`band_bottom` 在此 domain 下數學上永遠不可能由窗口內容產生（窗口列貢獻上界 72.7 < 100）。Option 1 的任何「通過」都是無關螢幕內容的巧合。

### 為什麼不只做 Option 2

Option 2 修好了 domain，但「候選點是否在**這張卡**的安全 interior」仍只有**一條**證據：窗口內某列亮不亮。它無法排除：ROI 內其他列（卡片 header、上鄰卡 grid、捲軸）作為假 band；strip 是否真的屬於 target card；candidate 是否貼近 ⋮ 或其他破壞性控制。Option 2 的通過仍然只是「有亮列」而不是「結構正確」。

### 本輪採用：Option 3（與 Option 2 的 ROI provenance 合併）

- **分析域**：`--window-geometry` 輸入的 LINE-window ROI（frame SHA-256 綁定；live 由 read-only AX 觀測換算，離線由 frame 自身像素決定性抽取），並在 ROI 內以「相對本 frame 背景色（中位數）的內容佔比」定義 band/strip。
- **局部性**：band 由「每一列的內容像素佔 ROI 寬度比例 ≥0.45」決定；strip 由「佔比 ≤0.30」決定；兩者都在 candidate 的 ±500px（且 clamp 在 ROI 內）內量測。
- **交叉約束**（把 ROI 從「被信任的輸入」變成「被 frame 驗證的區域」）：
  - candidate 距 ROI 左右緣 ≥16 px；
  - title 四側縮排 ≥8 px 且 ROI 右尾 ≥120 px；
  - strip 內唯一 cluster 必須是 ⋮（寬≤48、高≤80、距 title ≥100 px、距 candidate ≥100 px）。
  在這些約束下，任何能被接受的 ROI 必須同時容納 candidate（x≈39）與 caption 右端的 ⋮（x≈617–621）→ ROI 寬度實質被 frame 自己逼到接近整張卡寬；截窄的 ROI 會因「找不到 ⋮」或「右尾不足」而 refuse。
- **座標轉換的明示**：ROI 與 candidate 全部以 **current-frame 截圖像素座標**表示；live 路徑的換算＝ read-only AX window bounds（points）× 擷取 scale（本環境 2×；`attempt-07/screen-probe.json` 記錄 desktop 1147×745 pt ↔ 2294×1490 px，Retina 2x）＝ frame 像素；離線路徑則直接在 frame 像素上抽取（identity transform）。**兩條路徑都不使用任何歷史座標。**

## B.3 與 A–G 的對應

A→title OCR（exit 2）；B→count OCR（exit 5）；C→候選點公式（exit 11 前導檢查）；D→band+strip+sep_min（exit 9/4）；E→strip 唯一 cluster+間距（exit 10）；F→geometry SHA 綁定（exit 7/8）+ 自測；G→所有 refusal code。詳見 `evidence/20260916-route/tools/v6/README.md`。

## B.4 否決記錄（刻意不做的事）

- 不把 `bright=100` 或任何 v4 常數調鬆／調緊以求 pass。
- 不為 `2024/05/13～05/17` 或任何畫面寫特例座標。
- 不改 frozen v4/v5；v6 不呼叫 v4 作為 fallback。
- 不重寫 ellipsis locator、S5 verifier、menu detector（v6 只做 album-card S3 safety location）。
- 不把 offline `ELIGIBLE` 當成 live 授權。
