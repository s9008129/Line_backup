# ML07 Amendment 01：固定 Python 的隔離 schema 依賴

日期：2026-10-11；角色：根 Planner/本輪主控。狀態：核准的有界環境準備，不是 implementation 或驗證 PASS。

## 問題與決策

Implementer 實測指定 Python3.13 import jsonschema 得 ModuleNotFoundError。既有 canonical schema.validate 依賴 jsonschema/referencing；本機 Harness runtime symlink 的 Python3.14 已不存在。root 唯讀調查證明 pip cache 的四個 pure-Python wheels 可用，但 rpds 僅有 cp314 原生 wheels，不能供 cp313 使用。不得改名或載入 ABI 不相符的 extension。

主控依使用者授權的 best-practice 自主處理與本輪 implementation 權限，核准只在既有 allowed R 中準備隔離依賴。此 amendment 精確取代原附件 §7.1「不得安裝依賴」的部分：允許以下五個 pinned binary wheels 在本 epoch 隔離 root 的安裝。固定 Python executable/hash、canonical validator、state schema、資料/安全/gate 邊界、全域環境、immutable Harness 及原 machine contract bytes 不變。Plan Review 沿用本輪明確 USER_WAIVED_NOT_RUN，最後 Acceptance 仍 required；不宣稱 native controller/validation 恢復。

正式 E01/E02 尚未 launch、epoch 尚未 freeze，因此將此準備納入本次 bootstrap/output policy/source closure，沒有搬用舊 PASS。本輪 plan/handoff 原件不覆寫，Implementer 與 Acceptance 必須一起讀本 amendment。

## 唯一 pinned artifacts

下列 bytes/hash 已從 PyPI 官方版本 JSON 唯讀核對；四個純 Python cache bodies hash 同官方吻合。rpds 選定 macOS arm64 CPython3.13 wheel；所有版本均非 yanked。

| Package | Wheel | bytes | SHA-256 |
|---|---|---:|---|
| jsonschema 4.26.0 | jsonschema-4.26.0-py3-none-any.whl | 90630 | d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce |
| referencing 0.37.0 | referencing-0.37.0-py3-none-any.whl | 26766 | 381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231 |
| jsonschema-specifications 2025.9.1 | jsonschema_specifications-2025.9.1-py3-none-any.whl | 18437 | 98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe |
| attrs 26.1.0 | attrs-26.1.0-py3-none-any.whl | 67548 | c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309 |
| rpds-py 2026.6.3 | rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl | 338203 | f4d78253f6996be4901669ad25319f842f740eccf4d58e3c7f3dd39e6dde1d8f |

來源 [jsonschema](https://pypi.org/pypi/jsonschema/4.26.0/json)、[referencing](https://pypi.org/pypi/referencing/0.37.0/json)、[specifications](https://pypi.org/pypi/jsonschema-specifications/2025.9.1/json)、[attrs](https://pypi.org/pypi/attrs/26.1.0/json)、[rpds](https://pypi.org/pypi/rpds-py/2026.6.3/json)。

rpds 唯一授權 payload GET URL：

`https://files.pythonhosted.org/packages/f3/6b/686d9dc4359a8f163cfbbf89ee0b4e586431de22fe8248edb63a8cf50d49/rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl`

其餘四個優先使用已驗證本機 pip HTTP cache bytes，若 cache 消失，僅可讀取對應官方版本 JSON 指明、且吻合上表 hash/bytes 的 files.pythonhosted.org wheel。不得選 latest、sdist、extra packages、不同 interpreter/arch wheel 或未知 mirror。Host 準備的 metadata/payload GET 不帶使用者檔案或憑證；產品程式 network=OFF 不變。

## 精確範圍與步驟

- EPOCH/runtime/wheels：exact five filenames、CREATE_ONCE、regular、每項 cap 1MiB，預登記來源/producer/hash。先 bytes/hash/tag/ZIP entries驗證，再 exclusive/no-follow/fsync/readback publication。ZIP 不准 absolute/..、symlink、special entries；不執行 sdist/build hooks。
- EPOCH/runtime/requirements.lock、dependency-input-manifest.json、dependency-preparation-receipt.json：CREATE_ONCE、exact phase RUNTIME_PREPARE、root/Implementer host producer；納入 bootstrap policy。Manifest 保存官方 metadata/source、cache origin、bytes/hash、版本與相容 tag。
- EPOCH/runtime/site-packages：唯一 pip producer install root，64MiB cap；EPOCH/tmp/pip-cache 與 pip scratch 精確登記。輸入五wheel與鎖檔 frozen；local pip --no-index --no-deps --only-binary=:all: --require-hashes --no-compile --disable-pip-version-check --no-cache-dir --target 該 root 安裝。不得改 HOME/CODEX_HOME、全域sitepackages、既有runtime或系統設定。
- requirements.lock 精確五行 version==pin 和 --hash=sha256:上表值；使用原指定 Python 的 -B -m pip。完成後凍結整個 dependency namespace，每個檔案 bytes/hash/type/link target，來源 closure/runtime binding包含實际使用依賴，而非只有 wheel hash。
- 子程序 PYTHONPATH 為 ROOT/src:EPOCH/runtime/site-packages，PYTHONNOUSERSITE=1、PYTHONDONTWRITEBYTECODE=1；其他原 env guards 保持。host與fixture/CUA bridge 的 Python validator一致使用該 interpreter/依賴 root。各匯入module origin/版本必須落在該 frozen root，並記錄 actual rpds cp313 extension hash。
- 準備後用真 Draft202012Validator、referencing Registry 和既有 schema.validate/validate_state_strict 做正反 fixture（合法state、非法revision/type/extra field、nested delta/receipt conflict），不修改真state。檢查 schema宣告的每種format實際被FormatChecker覆蓋；若缺 optional format checker，不靜默忽略或增裝未核准依賴，交主控精確問題。
- 僅解決產品與E01 transaction fixture的依賴缺失，不拿這套 Python/依賴冒充原 Harness stage runtime/發出的 validators，不恢復 native writer allocation。

## 停止與證據

任何 URL/tag/bytes/hash/type/範圍不符即停止，不 fallback version 或 source build。Host fetch timeout 30秒、單payload1MiB；不重用已碰撞輸出。安裝子程序180秒/每stream2MiB，記錄argv/env/exit/streams和父目录before/after；失敗保留新 root 不清理未知檔，正式checks保持NOT_RUN。

原已取得metadata anchor中沒有本amendment及dependency outputs，B01需要把它們作事前核准的新bootstrap delta逐項對帳；parent在對账/scan期間不再寫工作區。實際修復及測試記入E2E報告與attemptledger，不因環境問題換continuation/reset產品collection。root本amendment文件publication為單一known planning artifact，Implementer讀回bytes/hash加入input manifest。
