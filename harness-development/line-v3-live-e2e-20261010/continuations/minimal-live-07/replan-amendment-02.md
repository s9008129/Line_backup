# ML07 Amendment 02：確保既有 date-time schema 檢查真正執行

日期：2026-10-11；角色：根 Planner/主控。此為Amendment01的精確依賴補充；未執行依賴安裝或宣稱PASS。

root唯讀核對 state_v3.schema.json 宣告 date/date-time。現有jsonschema4.26的_format.py只有成功import rfc3339_validator才註冊date-time，原Harness packages亦缺少此module。官方 [jsonschema4.26格式驗證文件](https://python-jsonschema.readthedocs.io/en/stable/validate/#validating-formats) 明示缺少所需可選依賴時format可能不產生驗證錯誤。Context7所取官方repository文件與本機原碼一致。只讓import jsonschema成功不足以證明canonical strict schema已執行全部格式條件。

## 決策與固定inputs

在Amendment01同一隔離root、原Python3.13/validator/gates不變的前提，必須補兩個pure-Python wheels。五個原pins保持，完整唯一bundle為七個pins；不安裝廣泛format extras、不新增其他package。

| Package | exact wheel | bytes | SHA-256 |
|---|---|---:|---|
| rfc3339-validator 0.1.4 | rfc3339_validator-0.1.4-py2.py3-none-any.whl | 3490 | 24f6ec1eda14ef823da9e36ec7113124b39c04d50a4d3d3a3c2859577e7791fa |
| six 1.17.0 | six-1.17.0-py2.py3-none-any.whl | 11050 | 4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274 |

來源官方版本JSON：[rfc3339-validator](https://pypi.org/pypi/rfc3339-validator/0.1.4/json)、[six](https://pypi.org/pypi/six/1.17.0/json)。root已實際讀回metadata，兩者非yanked，rfc3339-validator唯一必需依賴為six。

唯一新payload GET URLs：

- `https://files.pythonhosted.org/packages/7b/44/4e421b96b67b2daff264473f7465db72fbdf36a07e05494f50300cc7b0c6/rfc3339_validator-0.1.4-py2.py3-none-any.whl`
- `https://files.pythonhosted.org/packages/b7/ce/149a00dd41f10bc29e5921b496af8b574d8413afcd5e30dfa0ed46c2cc5e/six-1.17.0-py2.py3-none-any.whl`

EPOCH/runtime/wheels預登記這兩個exactfiles；同CREATE_ONCE/regular/每wheel1MiB cap、官方bytes/hash/tag/readback。requirements.lock七pins七hash；metadata/inputmanifest/preparationreceipt/sourceclosure保留全部七項及installed file hashes。pip同--no-index/--no-deps/--require-hashes/--only-binary/--no-compile/--no-cache-dir/固定target；可加--isolated忽略環境/user pip config，所有寫入仍留本epoch的root/scratch。

## 必要驗證與停止

- 新Python子程序使用已指定PYTHONPATH，所有相關module origins落隔離root；核對rfc3339_validator及six實際bytes/hash/version，rpds extension為cp313。
- `FormatChecker().checkers`必含state schema出現的每個format；目前是date/date-time。未知/未註冊format直接BLOCKED，不視為成功。
- 真Draft202012Validator接受合法ISO日期與帶timezone RFC3339 timestamp；拒絕不存在日期、invalid date-time、缺timezone、錯誤type。確認只是合理負fixture，不改既有state或schema。
- 使用既有schema.validate及validate_state_strict完成合法state與非法timestamp/revision/type反例，拒絕外部schema retrieve，canonical nested-delta/CAS tests仍必要。
- 任一dependency/source/format drift停下報原錯誤，不自製formatchecker替代、移除format或改schemahash。

scope不擴出原R，不修全域與Harness，不豁免任何gate；正式epoch未freeze、checks未launch才納入此次bootstrap。如果source已freeze就用新epoch，不能覆寫。主控此單一新planning artifact需讀回hash加入B01 knownbootstrap/input鏈，舊plan/handoff/Amendment01原件保持。PlanReview waiver與獨立Acceptance要求沿用本輪。
