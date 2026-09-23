# Rev27c root-cause classification — attempt-05 Save All locator false-negative

Artifact: `evidence/20260923-rev27c-save-all-locator/attempt-01/root-cause-classification.md`
Companion (machine-readable): `root-cause-classification.json`
Method: read-only re-reading of attempt-05 evidence on disk, the frozen v7-class
locator source, and this round's v8 offline replays. No live capture, no LINE
interaction, GUI input = 0.

Labels: `OBSERVED` = directly on disk evidence · `INFERRED` = derived, with the
reasoning stated · `UNKNOWN` = honestly unresolved.

## Q1. Did the locator require the exact OCR content of every menu item?

**YES — OBSERVED.** The frozen v7-class locator (sha256 `ea09c1ca…4012a`,
byte-identical copies in attempts 02–05) required for **each** of the five
reference items an exact substring hit in its OCR row and strict top-to-bottom
order before it would derive any candidate. attempt-05's own result artifact
records:

```
cross_check.reference_hits = { 選擇項目:[0], 修改相簿名稱:[], 儲存全部:[2], 刪除相簿:[3], 分享相簿:[4] }
cross_check.strict_order = false
verdict = MENU_CONTENT_UNEXPECTED (exit 5), reason "reference item order not found around the identified row"
```

## Q2. Was the target「儲存全部」itself read correctly?

**YES — OBSERVED.** It was row 2 of the OCR rows with text exactly `儲存全部`
(band `[1282.667, 327.333, 1385.0, 375.667]`). The v8 replay of the same frame
records the three target words at confidences `96.955 / 96.985 / 96.556` and
`row_match_tiers[2] = EXACT`.

## Q3. Was the failure caused only by the other (non-target) item?

**YES — OBSERVED.** Exactly one of the five reference hits was empty:
`修改相簿名稱`, whose row OCR read `修改相簿名般` — one glyph, 稱 → 般, word
confidence 49.772. The other four rows hit exactly. So the entire refusal is
explained by that single non-target glyph; nothing else about the frame was
wrong.

## Q4. Is the reference item's exact text a necessary safety signal?

**NO — INFERRED.** The exact text of a *non-target* reference item is not a
necessary safety signal for candidate establishment. What actually protects the
click is:

1. the menu surface was affirmatively detected **on this frame** (detector
   verdict + bbox + window geometry, all SHA-bound to the same frame);
2. the target string must be **exact** and occupy **exactly one** OCR row
   inside the verified popup bbox;
3. that row must be the **middle row** (3rd of exactly five, in the reference
   order) with neighbors still matching `修改相簿名稱`-ish / `刪除相簿`-ish
   within **one substituted character**;
4. the candidate must lie in the row's **safe interior**, clear of row edges
   and both neighbor rows, inside the addressable region, and pass the
   popup-shape / band-in-bbox / separation rules.

A single-glyph misread of a neighbor row changes none of these facts. The v7
strictness never influenced row geometry or the candidate either — it only
decided whether to continue at all.

**Residual risk (UNKNOWN):** there is no formal proof that no other popup could
present the same five-row shape with「儲存全部」as the middle row. This is a
bounded risk reduction, not a proof. The bound is: one substituted character
per non-target row, length-equal only, no insertions/deletions, target
tolerance 0, exactly five rows in reference order, full geometry gates — plus
the live-route gates outside the locator (single-ellipsis provenance, baseline
tripwire, staging preflight, durable intent, at-most-once dispatch) and the
human owner authorization for every live round.

## attempt-05 frame: v7 vs v8, side by side

| row | v7 OCR text | v7 hit | v8 CJK row | v8 tier |
|---|---|---|---|---|
| 0 | `選擇項目-` | 選擇項目 ✓ | 選擇項目 | EXACT |
| 1 | `修改相簿名般` | 修改相簿名稱 ✗ | 修改相簿名般 | TOLERANT_1_SUB |
| 2 | `儲存全部` | 儲存全部 ✓ | 儲存全部 | EXACT |
| 3 | `刪除相簿t` | 刪除相簿 ✓ | 刪除相簿 | EXACT |
| 4 | `分享相簿` | 分享相簿 ✓ | 分享相簿 | EXACT |

v7: `MENU_CONTENT_UNEXPECTED` (exit 5), no candidate.
v8: `ELIGIBLE` (exit 0), candidate frame px `[1297.333, 351.5]`, app-local pt
`[319.667, 134.75]` — unique, re-derived from this frame's own OCR and bound
geometry, and byte-identical over two replay runs.

## Conclusion

attempt-05 was a genuine **fail-closed false-negative**. The v8 revision removes
exactly that dependency (one substituted character tolerated on each
**non-target** row) while the target itself, the menu surface, structure/order
and all geometry remain hard gates. No manual override, no fuzzy target match,
no historical coordinates, no geometry relaxation, GUI input 0.
