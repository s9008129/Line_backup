# Rev25 Phase 2 — 診斷摘要

- **Status:** PASS (diagnostic evidence complete; root cause not over-claimed)
- **GUI_INPUT_COUNT:** `0`
- **Frozen v4/v5 modified:** `NO`
- **v6 created:** `NO — evidence does not prove a corrected card hitbox point`

## Findings

1. The historical coordinate chain is internally consistent: `[42,895]` screen px → `[21,447.5]` global logical pt → emitted `[21,448]`; System Events defines process-level `click at` in global coordinates.
2. The point is in the OCR title/text band, not a proven card hitbox. Hitbox membership and event consumption remain `UNKNOWN`.
3. Historical LINE frontmost/window geometry are recorded; current read-only checks find Safari frontmost and no available LINE process, so current state cannot answer the historical delivery question.
4. The S5 numeric result is deterministic: `0.047343` under the frozen `0.05` threshold. Lowering the threshold would only alter the numeric gate and is not a semantic route fix.
5. Attempt-07 S5 raw pre/post frames are not retained in the repository, so a delta sweep is explicitly `UNAVAILABLE`; no synthetic replacement was used.

## Next phase decision

The evidence is sufficient to document the failure boundary but insufficient to prove a new card click-point rule. Phase 3 should preserve frozen v4/v5, skip v6, perform two fresh independent reviews of the exact Rev25 plan, draft gate-6, and then stop for explicit owner authorization.
