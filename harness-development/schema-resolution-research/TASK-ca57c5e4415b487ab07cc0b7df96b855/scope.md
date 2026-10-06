# Schema 自動解析異常：使用者明示的獨立研究

使用者要求另一個 subagent、GPT-6 Luna、Max reasoning，研究審查時 schema 工具自動網路解析與DNS失敗的根因，包含OpenAI官方資料及第三方第一手案例，回報主線由主線判讀。

本研究授權public read-only internet search/open與本機read-only source/版本/已保存exception evidence。網路授權只屬本研究，不修改主線project-binding Plan的networkOFF，不豁免原P1 lookup，也不授權native/GUI/input/download、product/harness/globalcodex修補、套件更新、commit/push或向第三方傳送privateproject內容。Search只公開library/error/reference機制，不提供照片/群組/私人path/完整task資料。此研究agent不寫檔、不再spawn agents；回傳研究正文/來源/證據，由root保存本task。root主線P1可在離線設定修正後獨立續做。

已知原P1 run2411c72b-bf75-493d-b03d-c29eff242b23自報：裸schema validator未提供local Registry，嘗試解析https://codex.local/schemas/v3/gate.schema.json，DNS失敗，Unresolvable，沒有取得remote schema；改用local Registry後valid。完整result與rootadmission在harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/plan-review-01.result.json、review-01-admission.json。原trace需另確認，不將自報當OSnetworktelemetry。

待驗假說：實際Python jsonschema/referencing在$id/$ref絕對URI與缺registry時的resolution path；URI是identifier不是必須存在的URL；local-resource bootstrap/IDs/版本／schemas引用closure是否完整；OFF policy僅instruction與現實OSenforcement區別；角色自行建立裸validator而未使用pinnedwrapper是否rootcause；歷史同樣failedlookup證據是否真的同根因。不要先假設OpenAI服務DNS故障或模型bug。

讀取pinning/resources：/Users/hsiaojohnny/.codex/harness-releases/4.7.0/1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d；Python /Users/hsiaojohnny/.codex/harness-runtime/4.7.0/.venv/bin/python -B。禁止再對codex.local發真實DNS/HTTP request；可用in-memory callback證明裸validator嘗試retrieval以及localregistry failclosed，patch/stub urllib並assertzero實際I/O，只在完全理解hook後做微型CPU-only repro。不能對服務做能力probe或更新套件。

研究回傳需分local已證／第一手外部相似機制／OpenAI官方能或不能支持／inference／unknown，提供精確links、版本與excerpt位置。提出release-layer根因和最小安全修補選項，但不得修改release。實際requested model為gpt-6-luna reasoningmax；toolmetadata模型選擇是請求配置，不主張provider/controlleradmission實測。
