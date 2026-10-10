# 兩支 LineNativeAXGUIBridge 程式的根因研究

本文件整理本次 Planner 唯讀研究、唯一 GPT-6 luna research helper 的官方資料查核，以及實際 CUA 記憶體觀察。來源hash和重新核對結果見input-manifest.json、research-facts.json。研究沒有修改外部部署、TCC、LINE、state/config或備份檔案，也沒有執行兩支bridge的request/navigation/readiness命令。

## 1. 程式、來源與信任邊界

安裝根：/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge。

| 程式 | 實際bytes／SHA-256 | Manifest對應 |
|---|---|---|
| bin/line-native-ax-gui-session-bridge | 578832／e708e3c671fc946421a9ef68b5bb4efc3cb3b5b1147cf88137b46509bbf5f52a | size/hash/CDHash吻合；codesign verify通過 |
| bin/line-native-ax-readonly-scrollbar-probe | 1347312／cf8d830a454977497d527d210c1c40f6f74c89a7489c181510b075b494dd45e0 | manifest為1343872／79f52f8e551c4dd2ff4902361ee04a523ea76b3f76aa7c519fdac141d20715b9；CDHash也不同 |

probe實際CDHash為efc3fb4690d6d504b2f83189116723da70d8e368，manifest為639479d424767a2a54e5b7b21aa520122c6fbeba。簽章是ad-hoc；完整性驗證不能補成deployment source provenance。不能從差異推斷被攻擊或哪個版本更正確。

來源候選：/Users/hsiaojohnny/Documents/Codex/2026-09-12/line-native-ax-gui-session-bridge及line-native-ax-readonly-scrollbar-probe。兩個目錄的git rev-parse均回not a git repository。來源可以說明設計，不能據此宣稱已與安裝binary完成可重現build對應。

主要來源hash：

- bridge Sources/LineNativeAXGUISessionBridge/main.swift：bd2209b984836fe43addcd8c82eb602f521443d3a226cbfac722364fc6ea82a4。
- probe Sources/LineNativeAXReadonlyScrollbarProbe/main.swift：8ebedcf63793f6e8ceb50bd06a8386802fef1088cd08b90093aa708ba55fdf16。
- probe MenuObservationRuntime.swift：623b224e74c397fc5e9e2411993733ec7c54ab00a17aba585829e3d9d2a88590。

## 2. 真正功能與幫助程度

bridge透過Aqua LaunchAgent在GUI session運行，用private requests/claims/responses、request TTL、flock／exclusive claim、nonce session及controller timeout維持派送與回應一致性。request older/newer會呼叫controller --navigate；因此它的operation allowlist並非全為唯讀。它能解決GUI-session execution問題，但其heartbeat只證明服務在運行，不證明AX信任、screen capture或G_CATALOG。

probe預設唯讀raw AX traversal，提供focused window、role、attributes、position/size、scrollbar association及min/max/value。explicit --navigate older/newer／--scroll-action會呼叫AXUIElementPerformAction；不能因程式名稱含readonly就讓所有模式成為合法旁證。

C04 menu-observe-session使用AXObserver、WindowServer pre/post snapshots和bounded system-wide hit-test。它不發出ellipsis或menu item click，但要先收到target-binding及外部ellipsis完成訊號，才有post觀察。這條路可以支援某些menu语意觀察；目前缺少raw CUA screenshot留存、ScreenCaptureKit/full-display配對和本task grant/runtime membership，不能直接變成現有frame-support輸入。

MenuObservationRuntime.swift的menuWindowSnapshot讀CGWindowNumber、OwnerPID、Bounds、layer、onscreen等；menuReadiness僅AXIsProcessTrusted／AX root-read，optional_screen_recording_gate=NOT_REQUESTED。otool依賴與查閱來源未提供本次必要SCK screenshot export。原生window bounds本身不證明CUA影像的crop origin或scale。

最後既存readiness（request 5e75ec84-9c49-4779-a0d8-26975de4e528）為2026-09-15T05:03:18.672Z：ax_is_process_trusted=false、AX error -25211、TCC_TRUST_DENIED、response READINESS_BLOCKED。這是歷史失敗；沒有今日readiness invocation。launchctl/ps在研究中確認daemon PID773正在運行，但它與今日AX/screen capture可用性是不同事實。

結論：復用request identity、read-only traversal、窗口旁證與fail-closed思想；正式production在本repo既有native sensor plane補接口，保留CUA為唯一GUI actuator，避免第二套下載/state authority。外部兩支程式不成為全域門檻，也不直接接入當前grant。

## 3. 實際 CUA／程式根因

CUA工具文件：StateAndScreenshot={state:string,screenshot?:Uint8Array}，getAXStateAndScreenshot可關閉emit、開啟disableDiffing。相同persistent kernel成功import node:fs/promises和node:crypto，唯讀讀到deployment-manifest.json（4424 bytes、SHA b5a5c7e490880fd9c2de2251c570943ccd40a4917c5d359cfdfa6ffbd1de430a）。fs.writeFile函數存在，但本次沒有呼叫writeFile。

2026-10-10T15:23:02.304Z request、15:23:02.381Z return，duration約76.282ms。screenshot為Buffer／[object Uint8Array]，isView=true、instanceof Uint8Array=false、BYTES_PER_ELEMENT=1、byteOffset=0、183645 bytes。new Uint8Array(raw)在記憶體中正規化後instanceof=true，原hash與新hash均2e93f01caf5ade784f7e409f91a376fe99badcd828dc9aa266439692d3b297d6。AX為1299 bytes、SHA511c6cf8ad8709ca1fc5b595e26ebcec9e02d0bd73dc9e42e32b92e2b0eb90f2。

畫面可見canonical相簿列表、2024/06/02～06/07／65張，僅一張完整card；AX為匿名rows、scrollbar0、focused text field。以上是tool-return/視覺OBSERVED，raw image與AX沒有落到workspace；本文件不得被當作capture artifacts或fresh native geometry。沒有點擊、scroll、download、intent或state mutation。

現有createRetain已能保存screenshot與AX並readback；createHostedSession與createNavigationObserver卻先用instanceof拒絕跨realm bytes。這比「host無file reference所以不能保存」更接近可重現根因。

live_classifier的schema檢查只驗證注入analyzeCapture；test_live_classifier正例為ALBUM_DETAIL且cards=[]，不能證明ALBUMS/card。boundary keys的排序結果應為frame_id,indicator_index,maximum,minimum,session_id,source,value,version，現literal為version,frame_id,session_id,source,indicator_index,minimum,maximum,value，必然不相等。producer hook漏回intersectionPx，chooser卻用captured.support.intersectionPx做inside校驗。Chooser path field與confirmation controller的可見生命周期也未與phase相符。

Python3.14 frozen interpreter實際路徑不存在；3.13已唯讀確認可啟動。v4.8 native stage runtime仍失效，本次不修global環境。產品3.13重新binding與正式Harness native validation必須分列。

## 4. GPT-6 luna 官方研究

helper canonical task：/root/native_evidence_research。explicit model=gpt-6-luna、read-only、無nested agents；helper已完成。其報告提供下列官方依據，未證明任何runtime gate已PASS：

- Node fs.writeFile接受TypedArray，直接保存bytes後仍需length/hash readback。[Node fs.writeFile](https://nodejs.org/api/fs.html#fswritefilefile-data-options-callback)
- SCShareableContent列出apps/windows/displays；SCWindow有owningApplication與frame，CGWindowListCopyWindowInfo提供目前user session窗口資訊。API本身不描述CUA crop origin。[SCShareableContent](https://developer.apple.com/documentation/screencapturekit/scshareablecontent)、[SCWindow.frame](https://developer.apple.com/documentation/screencapturekit/scwindow/frame)、[CGWindowListCopyWindowInfo](https://developer.apple.com/documentation/coregraphics/cgwindowlistcopywindowinfo(_:_:))
- SCDisplay／SCContentFilter／SCStreamConfiguration需按實際display、contentRect、pointPixelScale、includeMenuBar及image width/height核對。多螢幕／Retina不能套固定scale。[SCDisplay](https://developer.apple.com/documentation/screencapturekit/scdisplay)、[SCContentFilter](https://developer.apple.com/documentation/screencapturekit/sccontentfilter)、[SCStreamConfiguration](https://developer.apple.com/documentation/screencapturekit/scstreamconfiguration)、[Apple capture sample](https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-in-macos)
- AXIsProcessTrusted與Screen/System Audio Recording是分別的權限；其中一個true不證明另一個。[AXIsProcessTrusted](https://developer.apple.com/documentation/applicationservices/1460720-axisprocesstrusted)、[Apple screen recording access](https://support.apple.com/guide/mac-help/control-access-screen-system-audio-recording-mchld6aa7d23/mac)
- ad-hoc signature沒有signing identity，不能單獨證明source/build provenance。[Code Signing Services](https://developer.apple.com/documentation/security/code-signing-services)、[ad-hoc flag](https://developer.apple.com/documentation/security/seccodesignatureflags/adhoc)

CUA公開官方網頁文件未找到；型別以當前工具回傳文件為依據。官方文件不提供特定CUA/native擷取的原子同步或五秒latency SLA，須以本task實測證據判定。

## 5. 未知與下一步

今日native producer AX／screen capture permissions、raw card container/native AX availability、v2 pixel detector準確性、multi-display映射、完整catalog耗時、chooser layout及pre-intent latency仍UNKNOWN。下一步依plan實作production鏈、在隔離fixtures測所有positive／negative cases，再fresh實機驗證。任一必要unknown不得由文字摘要、manifest assertion或舊PASS補成工具PASS。
