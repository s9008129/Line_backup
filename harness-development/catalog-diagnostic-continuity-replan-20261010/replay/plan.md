指定群組相簿列表的無下載診斷。使用者提供 screenshot 並明確說已就緒；已允許前景盤點。以本次 current AGENTS4.8 契約執行，不 resume 舊4.9控制器。

STANDARD：獨立 Plan Review → exact Handoff → bounded diagnostic implementation。不修改產品、config、state、registry、照片或 Git。此診斷不是 skill 的 backup/resume transaction，沒有 writer/intent/dispatch entitlement；只寫 task-local證據，不將結果當 production catalog admission。skill 的fresh/context/single-scroll/overlap/actioneffect仍適用。正式產品缺失不能由本診斷PASS代替。

只允許 documented cua_repl getApp/getAXStateAndScreenshot 及 App.scroll；不 click、鍵盤、setValue、相簿開啟、menu、SaveAll、chooser、download。觀察完整metadata日期/count行建立相簿 identity；thumbnail/card可部分可見但不可クリック。完整卡片同framebinding只對開啟 gate，本次無開啟。

先核對 canonicalconfig/state與 prior user-confirmed rendered群組title（目前header晏謙允禎成長日記，設定旻謙允禎成長日記；10/9 sourcejoin保存同群組確認，不改config）。唯一root=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup。

新task scope=harness-development/catalog-diagnostic-20261010/。baseline config/state/hash、Git head/branch/index、原始userPNG hash及 fresh image/AX 全保存。本次 raw captures append-only。Scroll前寫/readback task-localtrace，單一scroll後立即freshobservation；每步輸入後以前後日期/count/metadata行與移動判定effect。坐標由当前654×1286 frame的列表viewport導出，使用非操作metadata文字區附近作scrolltarget；scroll不點擊。每步 .25 page。最多12次scroll（含recovery），最多3 recovery cycles；UNKNOWN effect只能bounded observe，不resend。任何menu/dialog/viewer/identity/layoutdrift立即停止。LOW unlocatableAX focus欄位不能推翻正確fresh list畫面；本次不用keyboard。

保留每個完整metadata身份與partial標記，要求每相鄰frame至少一個相同date/count完整metadata row；有gap則停止，不追加blind scroll。本次只測bounded discovery，不宣稱fullcoverage；只有實際top/bottom連續證據才可另行宣告完整。本次初始top目前supported scrollbar0及第一張，bottom未見。

G1 authority/currentcontext；G2 safe per-step singleaction/effect/overlap；G3 currentconfig/state/Git preserved。owner IMPLEMENTER，GOAL_CRITICALITY=REQUIRED，EVIDENCE_ROLE=TOOL_VERIFICATION，CLOSURE_GATE=true。Visual判讀只記OBSERVED，tooltransport RETURNED/ERROR；G2 PASS只能表示受控診斷trace与明确觀察檢查成立，不表示nativeOCRcertification/完整catalog。

一次有意義實機診斷；材料漂移或未知無新資訊就停止保留facts/unknowns。沒有新下載目標授權。正常例外報告由root；新獨立Acceptance無必要（無產品/資料變更）。controller admission NOT_RUN、OS enforcement UNKNOWN。

Review01 有界修正：保存 plan01/contract01/原FAIL。新增task-local legacyVisionOCR，逐bytes複製既有menu_ocr.swift並新編譯；只處理CUA保存PNG，不擷取螢幕或生成input。每個frame保存rawOCR文本/confidence/bbox及stdout/exit，日期/count完整metadata以可見bounds與confidence>=0.95配對。header必須同frame實際OCR精確為priorconfirmed renderedtitle，並含相簿tab。OCR不取代visual安全檢查、不生成cardclick或SaveAllauthority。

新G1=機械核對選定root/config/state/proofhash及freshOCR header與相簿文本，G2=機械核對每步pretracepersist/readback、singleScroll預算、postcapture/rawOCR、相鄰完整date/count行交集與row-coordinate位移（或AXscrollvalue）；G3=controls/Git保持。requiredclosure只對上述實際mechanicalevidencePASS。Visual surface/safety/metadata/card/fullboundary判斷只存OBSERVED；無法機械證明的boundary/完整collection/nativeownership認證明示UNKNOWN/NOT_RUN，非本bounded診斷closure要求。任何requiredOCR配對/交集/位移缺失使G2未滿而停止，不降requiredness，不請waiver。

既有state writer要求不被變更：此獨立診斷不執行skill backup/resume、不修改canonicalstate。此材料無法admitproductioncatalog；真正產品catalog仍需reviewedcanonicalwriter。上限12次scroll只是測少量連續frame，不承諾全列表，適當停止後直接報部分發現與下一步，不擴大測試。

Replacement Plan03（same root issue最終offscreenattempt3，不重設舊嘗試）：原threshold.95及alias-only gate FAIL永遠保存，並未满足或waive。actualscale2probe兩API現已讀取canonicalheader/相簿/date/count；date分隔~與～以ISO日期語意正規化，無CJK模糊置換。 新gate只claim machine recognition agreement，不claimhigh/calibratedconfidence、不claim兩API獨立（同Vision可能共享錯誤）。此diag未修改任何productionevidencepolicy。

每freshCUAframe保持654×1286，完整sourcePNGimmutable。tasklocalCGContext .none2x derivative，保存source/derivativehash、geometrymapping（所有OCRbbox除2）。兩API對同derivative認字，保存stdout/stderr/exit/rawconfidence/bbox；modern保留top2候選，legacywrapper原本僅輸出top1，legacycompetingcandidates=UNKNOWN，不聲稱不存在。

機械門檻：原scopeG1/G2由matching兩API主候選支持。header exactconfigured旻謙允禎成長日記或原具體userconfirmedalias晏謙允禎成長日記，且兩API同一text；相簿exacttext，無相溥替代。每個配對metadata必須date完整startyear與ISOdateconsistent + countpositiveinteger；normalized日期/count身份same、source座標bbox中心maxaxis差<=6px、intersectionoverunion>=.45。這是OCRparagraphboxagreement，不是clicksafemargin；不生成clickauthority。每行date/count唯一，xleft<350、y>=205、count完整bottom<1281、count在date下方且距離<=60px，date/county幾何皆匹配；候選若包含不同有效身份或相同frame重複日期/count則拒絕歧義。header/tab同樣boxagreement。

每相鄰freshframe至少一個完整metadataISO身份交集；相同身份date行upwarddelta>5px支持requesteddownwardmovement。原始visuals/safety/top/bottom/wholecardvisibility仍OBSERVED。失配不調tolerance、不改confidences、不再probe；停止輸入保留partial。最多12次single .25pagescroll，此goal適當以6次成功scroll完成bounded證明即可停止；沒有fullscan聲明。不得要求user人工解讀tab以換PASS。
