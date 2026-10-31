# Save All 根因與修正設計

## 第一性原理

任務需要的是「指定列表的合格相簿安全寫入新目的地」，不是看到照片就下載。授權、身分、觀察、輸入可達性與派送結果是獨立條件：主視窗沒顯示 popup，只否定該來源的完整性；不否定授權或證明選單未開。click 逾時只表示結果不明，不能證明未派送。

已證主因是將可補足的觀察缺口轉成要求 Owner 代操作。產品內的促成缺口包括：模糊「單本照片頁」把合格詳細頁與未知入口混用；Save All 順序分散；替代下載未在決策點封閉；舊 B02 預期答案未限定需要返回的階段；缺少 popup 負向案例；實測能力摘要過期。

初始是否按過「選擇項目」或逐張下載仍 UNKNOWN，原始 trace 未保存。模型先驗只是推論，沒有跨模型、provider 或內部機制證據。來源為前版根因報告及 Issue #44，不重建歷史。

## 最小修正

- 入口與返回條件集中於 verified-experience；合格詳細頁可進下載，未知入口或確需返回的階段才處理返回。
- Save All 的完整順序集中於 backup-and-resume；SKILL 保留入口規則與路由，其他文件引用。
- visual-grounding 只負責當次觀察與映射。共同文字框可提供候選位移，不能單獨證明同尺度；另核對單位、軸向、裁切並以其他穩定位置交叉核對。
- 結果不明先對帳，不重送；沿用既有 daily 的不可改寫 UNKNOWN 限制，沒有新增事件種類或資料格式。
- 每次開選單與 Save All 分記；Agent 記錄不能冒充 OS 點擊審計。

座標原則參考 [Apple](https://developer.apple.com/library/archive/documentation/GraphicsAnimation/Conceptual/HighResolutionOSX/APIs/APIs.html)，結果不明與重試副作用原則參考 [AWS Builders Library](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)。這些支持設計原則，不證明 LINE 的實際 GUI。

## 證據與相容性

既有四本／141 張獨立 E2E PASS 保留原範圍。新版文字行為、簿記回歸、GUI、獨立驗收分列，不回填舊案例 NOT_RUN，不修改舊 artifact bindings。新規範不能提供平台硬性攔截；跨 Session 恢復與名稱校正仍未測。

本次只改六份產品文件及本目錄文件。未更動 src、tests、AGENTS、daily schema、照片、active-task 或 backup-records；未啟動或操作 LINE。來源 hashes 見 source-manifest.json。
