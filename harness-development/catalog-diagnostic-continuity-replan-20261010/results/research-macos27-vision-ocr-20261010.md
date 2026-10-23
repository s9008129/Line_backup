# 研究報告：macOS 27 的 Apple Vision OCR 與本案規劃是否一致

日期：2026-10-10
用途：提供高階模型判斷是否維持目前 OCR 規劃，或另立有界研究／比較計畫。
研究範圍：Apple 官方文件、WWDC26 官方說明、本機系統與專案規格／候選程式的唯讀核對。未執行 OCR、未重跑候選、未操作 LINE，也未改動候選程式。

## 結論摘要

本案目前規劃的主要 API 是 Apple Vision 的 `RecognizeTextRequest`，並以舊版 `VNRecognizeTextRequest` 作診斷比較。這與 macOS 27 仍公開提供的 Vision 文字辨識 API 一致。Apple 官方文件目前仍將 `RecognizeTextRequest` 描述為直接在影像上執行辨識、回傳文字觀察結果的 request；結果可包含文字、confidence 與 bounding box。專案候選程式也直接呼叫這些 API，並記錄 API revision 和 OS 版本。

macOS 27 的確多了另一個官方 OCR 入口 `Vision.OCRTool`。Apple 將它定位為 Foundation Models 工作階段可呼叫的工具，WWDC26 說明它可協助模型讀取細小或密集文字，並提到支援 30 多種語言。不過官方公開 API 說明它回傳的是包含辨識文字的字串；文件沒有顯示它可提供本案所依賴的逐筆 bounding box、top candidates、confidence、可鎖定的 OCR revision，或完全相同的 profile 設定。因此它是新入口，不能只憑「較新」或 WWDC 的描述就認定是 `RecognizeTextRequest` 的直接替代品。

現有資料不足以判定 `OCRTool` 是否能更準確辨識本案這些 LINE 相簿標題。Apple 的「適合細小／密集文字」是一般定位，沒有本案四張影像、相同 crop、相同語言及相同評分指標的比較結果。若要回答準確率問題，需另外批准並定義一個固定、可重現、只使用既有離線影像的比較方法；不能在目前修復候選或既定 OCR profile 上臨時換 API 或調參。

有一項具體設定風險值得高階模型留意：目前 `fixed-label-live` profile 使用 `zh-Hant`，並設定 language correction 與自訂詞「相簿」「記事本」。Apple Vision 官方指南明載中文不支援 language correction 及其相關 custom words。故這兩項設定不能被當成中文辨識能受益的既定依據；應由審查者判斷，是否只記錄為無效／不適用設定，或另開計畫比較合法支援的設定。這項官方限制本身不表示要擅自修改已凍結 profile。

## 本機與專案核對事實

- 本機 `sw_vers` 回報 macOS `27.0.1`，BuildVersion `26A434`。
- `xcodebuild -version` 回報 Xcode `26.6`、Build `17F113`。
- `xcrun --show-sdk-version` 失敗：目前選用的 Command Line Tools SDK `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk` 不存在。因此本次無法用本機 SDK 確認 `OCRTool` 的符號可用性、最低 deployment target 或編譯狀態。這不推翻 `sw_vers` 的 OS 版本，但限制了本機 API 相容性核驗。
- `diagnostic-spec.json` 將主要 OCR 設為 `Vision RecognizeTextRequest`，診斷 OCR 設為 `Vision VNRecognizeTextRequest`，並明列 `apis_independent=false`。兩者是同一 Vision 框架的 API 路徑，不能宣稱為兩家互相獨立的 OCR 引擎。
- 凍結規格要求 `accurate`、`zh-Hant`／`en-US`、每筆前三個候選、bbox、confidence、固定 profile、ROI／座標轉換與來源 hash。候選 `candidate/offline_vision.swift` 直接呼叫 `RecognizeTextRequest` 或 `VNRecognizeTextRequest`，輸出前三個候選、confidence、bbox、`api_revision`、`os_version` 及影像／衍生檔雜湊。
- `candidate/profiles.json` 的 `fixed-label-live` 開啟 correction 並設定兩個 custom words；`identity-header-metadata` 關閉 correction 且不設 custom words。
- 原始 OCR 證據 JSON 內有辨識輸出與 API 名稱；早期 JSON 未見 OS／SDK 欄位。新候選的 metadata 結構已有 OS 與 API revision 欄位，但本次沒有執行它來取得新結果。

## Apple 官方資料及其意義

1. [RecognizeTextRequest](https://developer.apple.com/documentation/vision/recognizetextrequest)：Apple 定義此 request 可直接在影像上執行，並產生描述辨識文字及其位置的 `RecognizedTextObservation`。API 有 recognition level、語言、自動語言偵測、語言修正、自訂詞與 revision 等控制項。這和本案需要逐區域辨識及保留候選／座標的資料形狀較一致。
2. [VNRecognizeTextRequest](https://developer.apple.com/documentation/vision/vnrecognizetextrequest)：舊式 Vision request 仍由 Apple 文件描述為找出並辨識影像文字的 API，回傳 `VNRecognizedTextObservation`。這支持「modern／legacy 是同框架的兩種 API 介面」之說；不是獨立 OCR 廠商交叉驗證。
3. [OCRTool](https://developer.apple.com/documentation/vision/ocrtool)：Apple 標示此 API 為 Beta。它是 Vision 與 Foundation Models 整合的一項 `Tool`，須加入 `LanguageModelSession`；官方概述指出輸出為含辨識文字的字串。公開介面還允許替工具命名與描述，讓模型判斷何時呼叫。這代表它處在「模型可呼叫的影像工具」流程，不是候選程式目前直接呼叫的逐筆 OCR request。
4. [WWDC26：What’s new in image understanding](https://developer.apple.com/videos/play/wwdc2026/237/)：Vision 團隊介紹 Foundation Models 圖像輸入與 image-based tool calling，指出 Vision OCR tool 對很細或密集的文字有幫助，並稱可讀取 30 多種語言。這是值得研究它對細小標籤是否有幫助的官方訊號，但不是本案影像上的準確率保證，也沒有說明每一種輸出欄位或重現性保證。
5. [Recognizing Text in Images](https://developer.apple.com/documentation/vision/recognizing-text-in-images)：Apple 說明 Vision 有 fast／accurate 辨識路徑、request revision 與語言設定；其指南亦明載中文不支援 language correction 或相關 custom words。這和本案固定標籤 profile 的設定直接相關。應依官方文件界定設定效果，不應推定中文會受益。
6. [RecognizeTextRequest.Revision](https://developer.apple.com/documentation/vision/recognizetextrequest/revision-swift.enum)：Apple 將 revision 定義為該 request 使用的演算法或實作版本。因而新結果應連同 API revision 與 OS 版本保存；只記「macOS 27」仍不足以識別實際 Vision OCR 實作版本。

## 與既有計畫的一致性判讀

- **一致處**：採用 `RecognizeTextRequest` 作主要直接辨識 API，符合 Apple 現行 Vision API 文件，也符合候選所需的 observations、bbox、候選與 confidence。保留 `VNRecognizeTextRequest` 作診斷比較，和規格有明確記錄 API 非獨立的做法一致。
- **新資訊但未自動改變規格**：macOS 27 的 Beta `OCRTool` 是新增的 Foundation Models 工具入口。Apple 表示它對細小／密集文字有幫助；值得高階模型決定是否另做封閉比較，但這不是現有契約已納入的 API，也未證明可滿足目前的輸出／綁定需求。
- **不可由文件下結論處**：哪個 API 對這些特定繁體中文相簿標籤較準、結果是否穩定、OCRTool 是否回傳可恢復幾何／候選資料、支援哪些繁體中文細節、結果能否綁定固定 revision，以及 Foundation Models 模型版本變動是否影響 OCRTool 取字結果。公開文件不足以回答這些本案特定問題。
- **信心**：對「專案目前呼叫哪個 API」及「OCRTool 與直接 request 的公開介面差異」信心高；對「OCRTool 會否改善本案辨識率」無法判定，需在獲准的獨立比較中實測。

## 提交高階模型的判斷問題

請判斷以下事項，不要將研究報告視為執行授權：

1. 是否維持凍結 replan 的 `RecognizeTextRequest` 主路徑，先完成既定修復；或另行建立只用既有離線素材比較 `RecognizeTextRequest` 與 `OCRTool` 的研究計畫？
2. 若允許比較，是否將 `OCRTool` 僅作旁路比較，不作候選替換；應如何處理它缺少明示 bbox／top-candidates／confidence／revision 的問題？
3. 鑑於 Apple 表示中文不支援 correction／custom words，現有 `fixed-label-live` 中這兩個設定應如何依契約分類與記錄？此判斷是否要求新 plan review 才能修改凍結 profile？
4. 比較評分是否應事先固定可辨識字元正確率、標題／metadata 區域定位、錯誤候選衝突率、完整同一候選 binding 及重現欄位；任何比較均不得用結果反向調整既定門檻或挑選較好看的候選。

本報告沒有建立 PASS、沒有更改 OCR profile，也沒有消耗本案方法額度。若高階模型認為有必要改 API、profile、requiredness、證據政策或 gate，請先依 harness 路由建立及審查新計畫，再執行。
