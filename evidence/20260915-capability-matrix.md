# LINE Save All route capability matrix — 2026-09-15

This is a read-only handoff reconciliation. No LINE GUI observation or input
was performed in this execution. Historical PASS/complete wording is retained
as provenance only.

| Capability | Direct `mcp__cua_repl` runtime | Native bridge/controller route | Classification and consequence |
| --- | --- | --- | --- |
| Acquire LINE app/surface and fresh screenshot/state | The runtime tool documents native-app control and fresh state/tab/app acquisition; this execution did not initialize it because the GUI-observation authorization/ledger was not present. | Source and historical controller artifacts define a GUI-session route, but current service is not healthy. | `HISTORICAL` for direct CUA success; current execution `UNKNOWN`. A screenshot alone cannot authorize a transaction. |
| Identify canonical group and album | 2026-09-13 historical direct-CUA evidence reports user-confirmed group, bounded native scroll, and fresh 57-card open. | Historical C04 design requires a fresh binding and exact target provenance. | `HISTORICAL`, not current proof. The user's `禎` and config/state `楨` remain distinct and unresolved. |
| Observe the transient album menu | Direct CUA history reports the popup was not present in screenshot/full AX data; it does not prove the menu was absent or that the runtime cannot expose it. | Controller source implements read-only A/B/C menu observation and exact `儲存全部`/`Save All` correlation; offline fixtures pass, but no current live menu result exists. | `UNKNOWN` for direct CUA; `HISTORICAL` for bridge design/fixtures. No route is eligible to dispatch. |
| Affirmatively identify the real Save All item | No current documented/evidenced direct-CUA menu-item observation. Historical formula/row order is explicitly non-authoritative and one prior coordinate activated Rename. | Installed help exposes `menu-observe-session`; current installed binary is not byte-identical to the current source release, and service is `spawn scheduled`/last exit 1. | `UNAVAILABLE` as a current affirmative proof. Requires one fresh, authorized, read-only observation or a separately validated route. |
| Map observed bounds to safe click point | Direct CUA click capability is documented by the runtime surface, but current coordinate mapping and menu-row margin are not observed. | Controller source defines bounded global hit-testing; no current live provenance/geometry result. | `UNKNOWN`; historical coordinates cannot be reused. Formula-only targeting is prohibited. |
| Click ellipsis/menu item | Direct CUA can operate UI in principle, but this execution has no new GUI authorization; no click occurred. | The bridge/controller contract explicitly forbids AXPress/AX writes and allows only a separately authorized Computer Use click for production. | `UNAVAILABLE` for this execution. No action ledger increment. |
| Use folder chooser / Go to Folder | Historical direct-CUA evidence reports Go to Folder succeeded in other trials; not current. | Controller procedure specifies chooser continuation only after a confirmed Save All trigger; current service readiness is blocked. | `HISTORICAL`; not sufficient to authorize a new download. |
| Persist intent/at-most-once dispatch | Skill/state contract specifies the required write/read-back barrier. Current selected backup state is clean (`revision=39`, no writer/current run); no new intent was written. | Offline bridge/controller tests exercise related zero-action contracts, but do not prove the backup state's live implementation. | `VERIFIED` as policy/clean current state; live production transaction `NOT_RUN`. |
| Verify files and state read-only | Fresh verify-only completed for the existing 57-file destination with three stable samples and per-file SHA-256/byte length. | Not dependent on bridge. | `VERIFIED` for current filesystem and registry consistency; source correspondence remains blocked by the group-name mismatch. |

## Route decision

`ROUTE_DECISION_STATUS: BLOCKED_PENDING_ONE_AUTHORIZED_OBSERVATION`

The shortest safe next experiment is a single read-only direct Computer Use
observation of the already specified target, with at most one ellipsis click,
then immediate post-observation and stop. It must report whether the actual
menu item text/role/bounds can be observed; it must not click Save All, use
AXPress/AX writes, type into a field, open a chooser, write backup state, or
retry on uncertainty. A failure or unknown result changes the next step to
bridge deployment/readiness review only if a fresh independent Revision 34
plan review authorizes that deployment; it does not authorize a second GUI
trial.

The currently installed bridge is a concrete runtime/config difference: its
binary is not byte-identical to the current source release, its persistent
lock contains legacy `pid=794`, and current `launchctl print` reports
`spawn scheduled`, `active count=0`, `last exit code=1`. This proves the
installed bridge cannot currently be treated as a ready production route; it
does not prove the bridge is necessary if direct CUA succeeds.
