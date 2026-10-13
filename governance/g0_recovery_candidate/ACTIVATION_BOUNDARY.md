# Activation Boundary

This candidate is not active and cannot be safely applied to the existing v4.8.0 controller as-is. The existing implementation does not enforce the new authority envelope, verifier attestation, proof schema, journal, or host-binding fields. The returned state is a model value, not a native Controller transition or durable issue-ledger event.

Activation requires a separately versioned, reviewed integration and explicit governance authorization. The original v4.8.0 runtime and c6 remain pinned and cannot consume these candidate state values as-is. At minimum, future integration must provide:

1. A trusted host adapter that obtains the original Task/Issue/c6 snapshot, exact six statuses, gate records, immutable history prefix, and frozen source/contract binding without trusting caller payloads.
2. A canonical runtime module-path anchor derived from the preserved original context. Current binding is UNBOUND; `Q` is only the repository-relative outer boundary. A task root cannot stand in for the actual module path.
3. A real producer/verifier that observes the original criterion's full runtime task-module closure and establishes same-contract, same-task/path, JavaScript/Python/Swift agreement. A signed declaration or manifest alone does not prove those files were read or complete.
4. Independently provisioned role-separated keys, a host policy for authorized human decisions, and a verifier identity bound to the real evidence producer. The sample HMAC helper and shared-key model do not prove human identity or non-repudiation.
5. A durable append-only journal with atomic compare-and-swap, idempotency across processes, concurrency control, and rollback protection. The current candidate only validates an in-memory event chain.
6. A versioned, independently reviewed controller/ledger integration that resolves only the original issue after verified original-criterion evidence and separately reactivates only remaining IMPLEMENT work. It must preserve all original receipts/events, continuation 1, retries 0, all 28 gate records, all six statuses, CRITICAL Plan Review/Acceptance requirements, and deny GUI/download/save/chooser authority.
7. Independent security and compatibility review plus the applicable formal Plan Review, deterministic handoff, implementation verification, and Acceptance gates before any real runtime action or G1–G3 work.

Until every prerequisite is satisfied, the only acceptable real-lineage behavior is the existing BLOCKED + WAIT_HUMAN stop. The candidate's synthetic positive test cannot change that. Rollback for this isolated candidate is to discard its branch; it has no installation or migration step. If a separately approved future integration is ever activated, rollback must disable its entry fail-closed while retaining all original and prospective events, receipts, and consumed-count facts. Rollback must never erase or rewrite history, reset a budget, or restore a reusable old allowance.
