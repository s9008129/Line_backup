# Implementer直接交接

請完整讀取專案根目錄的 [E2E技術修復計畫](../../20261010_LINE全螢幕定位與相簿備份_E2E技術修復計畫.md)、authorization.json、user-plan-review-waiver.json及plan-contract.json。handoff.json與contract逐bytes相同。

目前使用者已免除本計畫獨立審查及pre-live review前置，並授權需要的實作、數量與權限；直接開始本地實作／真正LINE E2E，不因machine critical policy的required字段再次等待Plan Review。P_PLAN_REVIEW保留為使用者明確免除，不是PASS；無controller waiver receipt不等於本地授權缺失。

先記fresh baseline、dynamic state/duplicate檢查、建fullscreen helper與新profile，實測CUA開menu後完整display pixels，再完成至少兩個不同未VERIFIED相簿的閉環與實際報告。最後開menu和Save All之間允許原生capture/guard，仍各最多一次Save All/confirmation。若fail，依計畫第12節新資訊修復繼續，保留每個attempt，不只交新Plan。正式產品獨立Acceptance留到E2E/report之後，不阻擋實測或報告交付。

原scope只有本task、合法schema2 state交易及配置導出的新空backup destination。existing产品/dirty/untracked、旧task/frames/profiles与旧照片只讀。helpers/writers0；不要执行旧helper寫回其原task。

本次尚無新OCR、LINE capture、GUI、下載、state mutation或E2E result，不能寫PASS。
