# Safety Invariants

| Invariant | Candidate enforcement | Limit |
| --- | --- | --- |
| Existing Task, Issue, c6, contract, source, task-state, and history anchors remain fixed | Exact signed-field and state-fingerprint checks | Host must supply authentic roots and durable state |
| Original criterion and c6 permission criterion remain distinct | Both hashes are pinned; proof parser requires original-root hash | Raw criterion meaning is represented only by its sanitized bounded predicate |
| One operation; continuation remains 1 and retries remain 0 | At-most-one authorization event and immutable counters | In-memory candidate state is not a durable CAS store |
| Governance authorization is not resolution | Authorization leaves Issue WAIT_HUMAN and Task BLOCKED | No runtime integration is present |
| No proof or rejected proof does not resolve | Exact evidence bytes + verifier signature + narrow proof parser; rejected proof is terminal | Actual verifier/producer is not implemented or observed |
| Local issue resolution is not full implementation success | Verified state remains Task BLOCKED; no status/gate changes | Existing controller does not consume this candidate |
| All 28 gate records and metadata/order remain intact | Canonical bytes/hash/count/field checks; accepted-gates tuple must stay empty | This candidate does not independently reread live gate state |
| Six status subjects do not change | Exact six-value tuple validation | Other unprojected live state remains outside the candidate |
| Reactivation requires a separate authority | Distinct signed action bound to VERIFIED state | Authority identity depends on externally provisioned keys |
| GUI, capture, downloads, Save All, chooser, and persistent-state actions remain denied | Fixed denied-capability list in each signed action and declarative permit | No OS sandbox/network enforcement claim |
| Replays do not create a new operation or renew a terminal permit | The same signed action returns the same permit identity only while AUTHORIZED; a terminal operation returns no permit | Durable rollback and cross-process races remain unhandled |

Candidate events never rewrite prior receipts or source history. They are prospective records in a separate candidate journal. There is no gate waiver, scope reduction, stage PASS, Acceptance result, c6 replay, root retry, or automatic recovery command. A proof that fails any binding check must not be transformed into RESOLVED by caller-supplied status fields.
