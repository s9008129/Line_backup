# Recovery State Machine

The state machine is a pure candidate model. It proposes a bounded governance operation against the existing lineage without allocating a new real task, issue, run, continuation, or retry.

```text
BLOCKED + WAIT_HUMAN + no operation
  └─ signed governance authorization
       → BLOCKED + WAIT_HUMAN + one AUTHORIZED operation + declarative permit
            ├─ signed verifier rejection of bound raw evidence
            │    → BLOCKED + WAIT_HUMAN + terminal FAILED operation
            └─ signed verifier attestation + exact original-criterion proof
                 → BLOCKED + RESOLVED + VERIFIED operation
                      └─ separate signed governance reactivation
                           → IN_PROGRESS + RESOLVED + next_stage=IMPLEMENT
```

The initial facts are pinned: original Task/Issue/c6 IDs, task-state and contract hashes, history-anchor hashes, distinct original-root and c6 permission criterion hashes, continuation count 1, retry count 0, six original status subjects, and the full ordered 28-gate catalog. The root task/module boundary `Q` is only a repository-relative outer boundary; it is not an asserted canonical runtime path.

Every signed action has an exact field set and must match the pinned IDs, criteria, contract, task state, gate catalog, history anchor, budget values, denied capabilities, action scope, and expected current-state fingerprint. Governance and verifier keys come from separate host-owned trust maps. The maps are copied on construction; identical role IDs or key bytes are rejected. The candidate does not provision or anchor production keys.

Authorization is one-per-original-root and does not resolve the Issue. Replaying the same authorization is idempotent; it returns the same permit only while the operation is still AUTHORIZED. A terminal operation returns no permit and a different decision cannot reauthorize it. The returned permit contains no command, process, or execution callback.

Completion compares the exact supplied evidence bytes to a separately signed digest and length, binds that attestation to the new operation and original IDs, and parses a narrow canonical proof. The proof must cite the original criterion hash (not the c6 permission hash as a substitute), same frozen contract, the `Q` boundary, an independently host-anchored canonical module-path digest, a complete normalized module/closure manifest under `Q`, and exactly JavaScript, Python, and Swift agreement over that same binding. The verifier's signature is required. A validly signed rejection is terminal and leaves the Issue WAIT_HUMAN; missing or malformed proof fails without changing the state. A verified Issue remains separate from task completion.

Reactivation requires another signed action bound to the verified state. It changes only eligibility for the remaining IMPLEMENT stage. It does not change any of the six statuses, accept a gate, mark the IMPLEMENT stage complete, create independent Acceptance, or reset budgets.

The event journal stores canonical signed envelope bytes and the raw proof bytes for the completion event. Each state validation checks event sequence, previous-event digest, event signature, exact action/scope, raw evidence digest/length, parsed proof, and derives the operation state from the event history. This guards against caller mutation of returned immutable values, but without durable storage and an atomic host compare-and-swap it does not prevent cross-process rollback or concurrent duplicate transitions.
