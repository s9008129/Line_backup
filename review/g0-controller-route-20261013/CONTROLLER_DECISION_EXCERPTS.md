# PR #4 source verification: Controller decision excerpts

## Scope and source identity

This is a bounded, read-only source review for task `TASK-4acb4326ea2a4c50ace6f333f2de8751`, issue `a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5`, and c6 run `c6c6b55d-865f-467b-94ba-3fd669df97ec`. The accepted state facts are: task `BLOCKED`, issue `WAIT_HUMAN`, the single continuation is consumed, zero retries remain, G0 `BLOCKED`, and G1–G3 `NOT_RUN`; the original 28 required gates remain in force.

Let `Q` mean the repository-relative prefix `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/`. The four requested source files are local, untracked selected v4.8.0 bytes at `Q/runtime/resources-luna/...`; they are not files in the PR #4 Git tree. Their hashes match the corresponding source hashes in `review/g0-controller-route-20261013/EVIDENCE_MANIFEST.md`; root independently re-hashed those four files. This establishes the identity of the selected local bytes against that manifest, not the full release tree, the live installed runtime, or platform enforcement. No source was executed and no Controller, ledger, test, R2, mock, or LINE action was run.

| Source | SHA-256 | Relevant functions/lines |
| --- | --- | --- |
| `Q/runtime/resources-luna/tools/harness/controller.py` | `385bbd2abd57ed305c01c7437f449833ed09cfc7e9f07add87d6352d405a8af5` | `allocate_run` 360–425; `publish_plan` 450–512; `_compile_handoff` 514–535; `record_result` 1507–1664; `waive_gate` 1759–1796; `_pending`/`reconcile` 1813–1940; `open_issue`/`authorize_continuation` 1942–1972; `_replay_state` 2102–2106; `_advance` 2239–2312 |
| `Q/runtime/resources-luna/tools/harness/escalation.py` | `7044aa55c6cc7721205fbd95ed2643ac0debcc67701c303c563a23dbc4768451` | `open` 154–187; `claim` 206–216; `returned` 268–285; `authorize` 287–318; `guard_task` 320–358; `finish_task_run` 360–387 |
| `Q/runtime/resources-luna/tools/harness/cli.py` | `6b05f608d582e117b18e9a4554c6f1573d2e7516d3bdf56ca48555b18f9721cd` | migration imports 13; `resume` 305–323; recovery dispatch 275–286; `reconcile`/`replan` and `stage-waive` 364–394; issue dispatch 395–453 |
| `Q/runtime/resources-luna/policies/v4.8.0/workflow-routing.md` | `7c2251913507a8cc09b4a697576963aaf6694ffd7fd7af55a6eb2e813a690912` | CRITICAL route 7–13; status/gate semantics 15–21; scope/continuation 35–41 |
| Additional direct CLI dependency, `Q/runtime/resources-luna/tools/harness/migration.py` | `9364edeaae6ef7bff5f57150119b72c8a86c21bcca7e156c272c1f121ae6f3fe` | `inspect` 13–25; `fork` 42–62; `prepare` 65–125 |

The fifth file is included only because `cli.py` directly imports and dispatches the named `recover-inspect`, `recover-prepare`, and `migrate` commands. It is a narrowly scoped recovery-entry dependency, not a broader Harness search. Its selected local bytes are also not in PR #4; the hash is recorded here for transparent provenance.

## Findings for the frozen state

### Allocation has no eligible stage until an existing issue authorization succeeds

`controller.py:372–373`:

Source excerpt — `controller.py` lines 372–373:
```python
if stage != state["next_stage"] or stage not in ROLE_FOR_STAGE or state["phase"] != "IN_PROGRESS":
    raise ControllerError("stage differs from controller-owned next eligible action")
```

For the accepted current state, `phase=BLOCKED` and `next_stage=null`; `issue-prepare-continuation` in `cli.py:417–423` also refuses unless `next_stage` is `IMPLEMENT`. The only matching task recovery inside the existing issue path is `authorize_continuation`, followed by a fresh exact IMPLEMENT allocation. That authorization is not available in the current issue state, as described below. **Result:** the existing allocation path raises `ControllerError`; there is no eligible stage under the current state.

Source excerpt — `controller.py` lines 419–424:

```python
            if (self.state_root / "issues").exists():
                from .escalation import IssueLedger
                permission = IssueLedger(self.state_root / "issues").guard_task(task_id, stage, state["contract_sha256"], state["allowed_paths"], run_id=rid, selected_issue_id=selected_issue_id)
                if permission:
                    run["operation_scope"] = "ISSUE_CONTINUATION"
                    run["continuation_permission"] = permission
```

The original gates stay bound to the accepted Plan/Handoff. `publish_plan` rejects downgrading a user-selected non-AUTO task class and requires CRITICAL plans to include independent Plan Review and Acceptance (`controller.py:458–478`); it stores the Plan's `gate_specs` in task state (`482–484`). `_compile_handoff` verifies the accepted contract hash, copies its gate specs and evidence into state (`514–533`). `allocate_run` verifies the frozen Plan, contract, and Handoff bytes before a later stage (`380–386`). The 28-gate count is an already-verified task fact, not a count hardcoded in these source lines. These branches support preserving those original gate definitions; they do not authorize replacing them with a fresh empty gate list.

The exact CRITICAL safeguards are:

Source excerpt — `controller.py` lines 458–462:
```python
            if state["task_class"] != "AUTO" and contract["task_class"] != state["task_class"]:
                raise ControllerError("Planner changed the task risk level selected by the user")
            workflow = contract["workflow_policy"]
            if contract["task_class"] == "CRITICAL" and not (workflow["plan_review_required"] and workflow["independent_acceptance_required"]):
                raise ControllerError("CRITICAL work requires independent Plan Review and Acceptance")
```

The compiled Handoff retains the accepted gate set:

Source excerpt — `controller.py` lines 531–533:
```python
        state.update(contract_sha256=digest, handoff_sha256=digest,
                     required_gates=contract["gate_specs"], required_evidence=contract["required_evidence"],
                     allowed_paths=contract["allowed_paths"], handoff_compiler="DETERMINISTIC_FROM_REVIEWED_PLAN")
```

Before allocating later work, the controller compares the stored Plan, contract, and Handoff digests:

Source excerpt — `controller.py` lines 380–384:
```python
            if stage in {"PLAN_REVIEW", "HANDOFF", "IMPLEMENT", "ACCEPTANCE"}:
                if _sha(_read_regular(directory / "plan-contract.json", directory)) != state["plan_contract_sha256"]:
                    raise ControllerError("reviewed machine Plan contract changed")
                if _sha(_read_regular(directory / "plan.md", directory)) != state["plan_sha256"]:
                    raise ControllerError("Plan bytes changed after publication")
```

### Linked issues preserve state and budget; the current issue cannot be authorized again

`escalation.py:169–181`:

Source excerpt — `escalation.py` lines 169–171:
```python
        # Hypothesis names, model, task and observed error text do not reset identity.
        issue_id = packet.get("lineage_issue_id") or _digest({key: packet[key].strip()
            for key in ("goal", "failed_condition", "capability_boundary")})
```

The existing-record branch later in the same method is:

Source excerpt — `escalation.py` lines 174–181:
```python
            if (directory / "state.json").exists():
                item = self._load(issue_id)
                item["tasks"][packet["task_id"]] = packet["contract_sha256"]
                # Reopening a resolved condition requires explicit human judgment;
                # no silent budget reset from another task or renamed hypothesis.
                if item["state"] == "RESOLVED":
                    item["state"] = "WAIT_HUMAN"
                self._event(item, "ISSUE_LINKED", packet)
```

This links the task to the same issue record. It does not reset `continuations`; a resolved linked record is moved back to `WAIT_HUMAN`.

`escalation.py:287–291`:

Source excerpt — `escalation.py` lines 290–291:
```python
if item["state"] != "ANALYSIS_RETURNED" or item["continuations"]:
    raise EscalationError("no unused bounded continuation")
```

Substitution of current facts (`WAIT_HUMAN`, continuation count 1) fails both conditions. Exact result: `EscalationError("no unused bounded continuation")`. A new `issue-open` with this `lineage_issue_id` keeps the same state and count; a different issue root would not preserve the original issue budget.

`escalation.py:320–357`:

Source excerpt — `escalation.py` lines 335–337:
```python
            if item:
                if stage != "IMPLEMENT" or item["state"] != "CONTINUATION_AUTHORIZED":
                    raise EscalationError("selected issue is not authorized for continuation")
```

After the remaining guards, the method records consumption as:

Source excerpt — `escalation.py` lines 352–355:
```python
            if affected:
                item = next(i for i in affected if i["issue_id"] == selected_issue_id)
                item.update(state="CONTINUATION_CONSUMED", continuations=1,
                            continuation_task_id=task_id, continuation_run_id=run_id)
```

The guard allows an IMPLEMENT run only after a continuation is already authorized, then records it as consumed. It is not a recovery/reset path. Current `WAIT_HUMAN` cannot pass this guard, and an authorization would still be rejected first by `authorize` because the state/count do not qualify.

### A fresh REPLAN decision cannot route around the pending issue

`reconcile` first checks for a previously consumed, matching decision and may replay its recorded route. For a fresh valid decision with no prior receipt, the pending-issue guard runs before task-state routing:

Source excerpt — `controller.py` lines 1870–1877:
```python
            record = directory / "routing-decisions" / digest / "consumption.json"
            if record.exists():
                prior = json.loads(_read_regular(record, directory))
                self._replay_state(state, prior)
                self._verify_accepted(state)
                if before != _sha(validate_compact_state(prior["state"])):
                    _json_atomic(directory / "state.json", prior["state"])
                return prior["route"]
```

For a fresh decision, the next guard is:

Source excerpt — `controller.py` lines 1878–1881:

Source excerpt — `controller.py` lines 1878–1881:
```python
if self._pending(task_id):
    raise ControllerError("unresolved/exhausted issue requires human resolution; routing cannot reset its ledger")
if state.get("active_run_id") or state["phase"] != "BLOCKED" or not state.get("last_valid_run_id"):
    raise ControllerError("routing return requires the current accepted failed run")
```

`_pending` delegates to `IssueLedger.pending_for_task` (`controller.py:1813–1816`); that method includes every task-linked issue whose state is not `RESOLVED` (`escalation.py:193–204`). Current `WAIT_HUMAN` is therefore pending. A fresh valid `reconcile` decision with `REPLAN`, `REPAIR`, or `ABANDON` raises the exact pending-issue `ControllerError` before it can change task state. A matching previously consumed decision can only replay its recorded route if its state is still accepted or exactly the recorded pre-publication state (`_replay_state`, `controller.py:2102–2106`); it does not create a new authorization, clear the IssueLedger state, or let `guard_task` allocate while the issue remains WAIT_HUMAN.

Source excerpt — `escalation.py` lines 193–204:

```python
    def pending_for_task(self, task_id):
        with self._lock():
            summaries = []
            for path in self.root.iterdir():
                if not path.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", path.name):
                    continue
                item = self._load(path.name)
                if task_id in item["tasks"] and item["state"] != "RESOLVED":
                    summaries.append({"issue_id": item["issue_id"], "state": item["state"],
                        "consumed_run_id": item.get("continuation_run_id"),
                        "permission": item.get("permission")})
            return summaries
```

Even without that pending guard, `REPLAN` has narrower preconditions: `controller.py:1891–1892` requires the current accepted run's runtime outcome `COMPLETED` and candidate fact `FAIL` or `REVISION_REQUIRED`; current c6 candidate is `BLOCKED`, so it raises `ControllerError("unknown/runtime failure cannot authorize a product repair or replan")`. `REPAIR` is limited to one known Acceptance defect (`1901–1905`), and `ABANDON` ends at `WAIT_HUMAN` rather than reactivating IMPLEMENT (`1929–1930`).

Source excerpt — `controller.py` lines 1887–1892:

```python
            consumption = json.loads(_read_regular(root / "consumption.json", directory))
            result = _validate(_read_regular(root / "submissions" / consumption["admission_sha256"] / "candidate-result.json", directory), "result.schema.json")
            self._verify_consumed_run(directory, state, run["run_id"])
            self._verify_accepted(state)
            if state["runtime_fact"]["outcome"] != "COMPLETED" or result["candidate_fact"] not in {"FAIL", "REVISION_REQUIRED"}:
                raise ControllerError("unknown/runtime failure cannot authorize a product repair or replan")
```

### Result replay is idempotent only for the exact current consumed state

`controller.py:1518–1530` replays a consumed result only when the new input digest exactly matches the stored admission. `_replay_state` then allows only the accepted state or its recorded pre-publication state (`2102–2106`):

Source excerpt — `controller.py` lines 2105–2106:
```python
if current not in {accepted, consumption.get("before_state_sha256")}:
    raise ControllerError("consumed decision is not the current state; historical route cannot be replayed")
```

This prevents using an old result to resurrect its prior route after later state changes. It does not unconsume c6 or create another continuation. `record_result` has a separate same-input admission idempotency check (`controller.py:1518–1530`); replaying a result is not an issue reopening or a new c6 authorization.

### A partial diagnostic is not a local-only successful IMPLEMENT result

`controller.py:1595–1601` validates required ROLE-owned gates for the current stage before admission. Then `1613–1614` defines `passed` as runtime `COMPLETED` and candidate `PASS`. For an IMPLEMENT issue continuation, the same `passed` value is passed to `IssueLedger.finish_task_run` (`1631–1638`). The ledger accepts a resolution only when the exact permitted success criterion and nonempty verified files match (`escalation.py:369–387`); `TARGETED_DIAGNOSTIC` proven evidence yields `DIAGNOSTIC_COMPLETE_WAIT_HUMAN`, not a resolved issue (`382–385`). Remaining pending issues force task phase `BLOCKED`, `next_stage=None`, and route `WAIT_HUMAN` (`controller.py:1639–1642`).

`_advance` returns `WAIT_HUMAN` whenever an IMPLEMENT result is not passed (`controller.py:2248–2269`). Only after a passed result does the stage update IMPLEMENTATION_STATUS to `COMPLETE`; CRITICAL tasks route to Acceptance (`2291–2300`). Thus the inspected code does not expose a local-only diagnostic admission that resolves the issue while avoiding the whole stage’s required gates. This is a control-flow finding, not a claim that an observed run had such a defect.

### Issue dispatch commands do not reopen the current WAIT_HUMAN record

The relevant CLI branches (`cli.py:409–453`) dispatch `issue-open`, `issue-authorize`, `issue-prepare-continuation`, `issue-submit-continuation`, `issue-status`, `issue-return`, `issue-claim`, `issue-invoked`, and `issue-fail` to the ledger/controller methods above. The automatic `claim` requires `STOPPED` and zero prior reviews (`escalation.py:206–216`); `returned` requires `REVIEW_INVOKED` and a bound completed receipt (`268–285`); `fail_dispatch` only accepts `REVIEW_CLAIMED` or `REVIEW_INVOKED` (`260–266`). Current `WAIT_HUMAN` does not satisfy those dispatch states. There is no CLI route that clears `WAIT_HUMAN` or resets the consumed count.

The only same-issue CLI authorize/prepare route delegates to the guards already reviewed.

Source excerpt — `cli.py` lines 415–423:
```python
            elif name == "issue-authorize":
                output = core.authorize_continuation(args.task, args.issue)
            elif name == "issue-prepare-continuation":
                state = core.inspect(args.task)
                if state.get("next_stage") != "IMPLEMENT":
                    raise ControllerError("selected issue has no authorized continuation action")
                prompt = ROOT / f"prompts/v{RELEASE_VERSION}" / PROMPTS["IMPLEMENT"]
                policy = ROOT / f"policies/v{RELEASE_VERSION}/workflow-routing.md"
                output = core.allocate_run(args.task, "IMPLEMENT", controller_path=ROOT / "tools/harness/controller.py", schema_path=ROOT / "schemas/v3/result.schema.json", prompt_path=prompt, policy_path=policy, selected_issue_id=args.issue)
```

Those source guards are:

Source excerpt — `escalation.py` lines 209–210:
```python
            if item["state"] != "STOPPED" or item["reviews"]:
                raise EscalationError("automatic review already claimed or human intervention required")
```

Source excerpt — `escalation.py` lines 271–272:
```python
            if item["state"] != "REVIEW_INVOKED":
                raise EscalationError("no actual review invocation to complete")
```

Source excerpt — `escalation.py` lines 263–265:
```python
            if item["state"] not in {"REVIEW_CLAIMED", "REVIEW_INVOKED"}:
                raise EscalationError("dispatch is already terminal")
            item["state"] = "WAIT_HUMAN"
```

`finish_task_run` only processes the same task while the issue state is still `CONTINUATION_CONSUMED` and the run ID matches.

Source excerpt — `escalation.py` lines 366–368:
```python
                if item.get("continuation_task_id") == task_id and item["state"] == "CONTINUATION_CONSUMED":
                    if not run_id or run_id != item.get("continuation_run_id"):
                        raise EscalationError("continuation completion run mismatch")
```

Current issue state `WAIT_HUMAN` does not match this condition, so the finish method has no state transition for it.

`resume` is read-only: `cli.py:305–323` calls `core.inspect`, renders a status projection, and returns. It does not invoke reconcile or authorize. Legacy release mismatch is rejected at `314–315` with an instruction to use the original immutable CLI.

Source excerpt — `cli.py` lines 313–323:
```python
            state = core.inspect(args.task)
            if name == "resume" and state.get("release_version") != RELEASE_VERSION:
                raise ControllerError("legacy release state is read-only; operate it with its original immutable release CLI and resources")
            projection = {k: state.get(k) for k in ("task_id", "release_version", "phase", "next_stage", "active_run_id", "active_issue_id",
                "convergence", "last_handoff_summary", "statuses", "runtime_fact", "candidate_fact", "validation_fact", "reconciliation_reason")}
            projection["action"] = "角色工作由操作者目前使用的平台執行；控制器不會在背後啟動模型。各階段可使用平行幫手，實作階段可依計畫分派隔離的作者。"
            if name == "status" and getattr(args, "json", False):
                print(bounded_inspect(projection))
            else:
                print(_friendly_status(state))
            return 0
```

This exact branch returns a status projection and does not write state or allocate a run.

`stage-waive` records a separate user decision and is not issue recovery. `controller.py:1766–1769` requires no active run, implementation `COMPLETE`, and independent Acceptance either `PASS` or `NOT_REQUIRED`:

```python
            if state.get("active_run_id") or state["statuses"]["IMPLEMENTATION_STATUS"] != "COMPLETE":
                raise ControllerError("a waiver can be recorded only after implementation is finished")
            if state["statuses"]["INDEPENDENT_ACCEPTANCE_STATUS"] not in {"PASS", "NOT_REQUIRED"}:
                raise ControllerError("a waiver cannot replace required independent Acceptance")
```

The existing redacted `evidence/route-status.redacted.json` projects the Controller statuses as `IMPLEMENTATION_STATUS=ESCALATED`, `INDEPENDENT_ACCEPTANCE_STATUS=PENDING`, and `CORE_ACCEPTANCE_STATUS=NOT_RUN`; its separate task projection has `phase=BLOCKED` and `candidate_fact=BLOCKED`. This is a whitelist derivative, not raw-chain verification. The waiver predicate therefore fails on the two required statuses; phase alone is not the predicate. Waivers also remain visible under policy `workflow-routing.md:19–21` and cannot erase the issue record.

The route-decision envelope requires trusted-operator authority and exact action/authority agreement (`controller.py:1855–1868`):

Source excerpt — `controller.py` lines 1861–1868:
```python
            if decision["source"] != "TRUSTED_OPERATOR" or decision["authority"] != authority or decision["action"] != operation:
                raise ControllerError("routing decision authority/action mismatch")
            for key in ("authority", "reason", "failed_condition", "permitted_action", "success_criterion", "stop_condition"):
                if not isinstance(decision[key], str) or not decision[key].strip():
                    raise ControllerError("routing decision requires nonempty " + key)
            if operation not in {"REPAIR", "REPLAN", "ABANDON"}:
                raise ControllerError("unsupported supervised reconciliation operation")
            self._verify_routing_files(directory, decision)
```

## The actual recovery-named commands

`cli.py:13,275–286` imports and dispatches `migrate`, `recover-inspect`, and `recover-prepare`. The direct dependency `migration.py` is therefore reviewed rather than treating those names as absent.

- `recover-inspect` is explicitly read-only and returns source state identity, run IDs, and `review_count=UNKNOWN`, `continuation_count=UNKNOWN`, `historical_acceptance=NOT_RECERTIFIED` (`migration.py:13–25`). It makes no admission.
- `migrate --mode fork` requires a nonempty recorded authority and new destination, copies the source tree, and marks historical results preserved but not recertified (`42–62`). It does not update the original task or its IssueLedger. It is a fork, not admission for the same blocked task and consumed issue.
- `recover-prepare` requires a decision bound to source state SHA, action `FRESH_PLAN`, nonempty scope/reason, and `preserve_history=true` (`65–80`). It writes a new `TASK-RECOVERY-*` task with next stage `PLAN`, `required_gates=[]`, no contract, and inherited review/continuation counts `UNKNOWN` (`89–119`). It leaves the original source untouched (`120–125`). The command is an existing, human-authorized fresh-lineage procedure, but it does not preserve the required original 28 gates or establish the known issue count in an admissible task. It is outside the present authorization, which prohibits creating a new task/issue/retry.

Source excerpt — `cli.py` lines 275–280:

```python
        if name == "migrate":
            if args.mode == "dry-run":
                print(bounded_inspect(diagnose(Path(args.source)))); return 0
            if not args.destination or not (args.authority or "").strip():
                raise ControllerError("non-mutating fork requires --destination and recorded --authority")
            print(bounded_inspect(fork_legacy(Path(args.source), Path(args.destination), authority=args.authority))); return 0
```

Source excerpt — `migration.py` lines 42–56:

```python
def fork(source: Path, destination: Path, *, authority: str) -> dict[str, Any]:
    """Non-mutating lineage fork: copies a legacy task; never mutates or recertifies it."""
    if not authority.strip():
        raise MigrationError("fork requires recorded user/controller authority")
    source = source.resolve(strict=True)
    destination = Path(destination)
    resolved_destination = destination.resolve()
    if resolved_destination.exists() or resolved_destination == source or source in resolved_destination.parents:
        raise MigrationError("fork destination must be new and outside the source lineage")
    report = diagnose(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, resolved_destination, symlinks=True)
    lineage = {"lineage_version": "1", "fork_id": str(uuid.uuid4()), "source": str(source),
               "source_state_sha256": report["source_state_sha256"], "authority": authority,
               "historical_results_preserved": True, "historical_verdicts_recertified": False,
```

The recovery command dispatch is:

Source excerpt — `cli.py` lines 281–286:
```python
        if name == "recover-inspect":
            print(bounded_inspect(recover_inspect(Path(args.source)))); return 0
        if name == "recover-prepare":
            repo = Path(args.repo).resolve(strict=True)
            state_root = _state_root_inside(repo, args.state_root or repo / "harness-development/supervised-tasks")
            print(bounded_inspect(recover_prepare(Path(args.source), state_root, Path(args.decision)))); return 0
```

The human decision must bind the source hash and select the fresh-plan action.

Source excerpt — `migration.py` lines 74–80:
```python
    required = {"source_state_sha256", "action", "scope", "reason", "preserve_history"}
    if not isinstance(decision, dict) or not required.issubset(decision):
        raise MigrationError("decision file lacks source identity, action, scope, reason and history disposition")
    if decision["source_state_sha256"] != source_hash or decision["action"] != "FRESH_PLAN":
        raise MigrationError("human decision does not bind this source and FRESH_PLAN action")
    if decision["preserve_history"] is not True or not all(isinstance(decision[k], str) and decision[k].strip() for k in ("scope","reason")):
        raise MigrationError("decision must preserve history and state a nonempty scope/reason")
```

The relevant initial fields of the new task are:

Source excerpt — `migration.py` lines 102–104:
```python
    state = {"schema_version":"3", "task_id":task_id, "release_version":RELEASE_VERSION,
        "repository":str(repo), "goal":goal, "task_class":"CRITICAL",
        "start_snapshot_sha256":snapshot_digest(start), "phase":"IN_PROGRESS", "next_stage":"PLAN",
```

Source excerpt — `migration.py` line 110:
```python
        "plan_revisions":0,"accepted_gates":{},"required_gates":[],"required_evidence":[],
```

Source excerpt — `migration.py` lines 113–114:
```python
        "inherited_history":{"review_count":"UNKNOWN","continuation_count":"UNKNOWN",
        "source_task_id":report.get("task_id"),"source_state_sha256":source_hash,"lineage_equivalence":"UNKNOWN"},
```

These exact fields (`migration.py:102–115`) demonstrate why the human-authorized recovery command does not preserve the current task's known budget and gates.

## Completion, gates, and criticality excerpts

Required ROLE-owned gates are validated before a candidate can be admitted as PASS (`controller.py:1592–1601`):

Source excerpt — `controller.py` lines 1592–1601:
```python
                specs = [GateSpec.from_dict(g) for g in state.get("required_gates", [])]
                validate_gate_results(specs, result["gate_results"], phase=run["stage"],
                    verified_evidence_ids=verified, producer=run["role"])
                if result["candidate_fact"] == "PASS":
                    if not verified:
                        raise ControllerError("PASS needs actual evidence files")
                    needed = {g.gate_id for g in specs if g.required and g.phase == run["stage"] and g.owner == "ROLE"}
                    passed = {g["gate_id"] for g in result["gate_results"] if g["verdict"] == "PASS"}
                    if not needed.issubset(passed):
                        raise ControllerError("assigned required gates did not pass")
```

The same stage-wide `passed` value depends on runtime completion and candidate PASS, and is sent to `_advance` (`controller.py:1613–1622`):

Source excerpt — `controller.py` lines 1613–1622:
```python
            runtime_success = comp["outcome"] == "COMPLETED"
            passed = runtime_success and result["candidate_fact"] == "PASS"
            permission = run.get("continuation_permission", {})
            if permission.get("repair_decision_sha256") and not any(
                    m["observation"] == permission["success_criterion"] for m in result["evidence_manifests"]):
                passed = False
            pending = self._pending(task_id)
            if pending and not all(i["state"] == "CONTINUATION_CONSUMED" and i.get("consumed_run_id") == run["run_id"] for i in pending):
                passed = False
            route = self._advance(state, run, inv, result, passed)
```

For an IMPLEMENT continuation, that same `passed` value reaches issue finishing (`controller.py:1631–1642`):

Source excerpt — `controller.py` lines 1638–1642:
```python
                IssueLedger(self.state_root / "issues").finish_task_run(task_id, passed, run_id=run["run_id"], evidence=evidence)
                if self._pending(task_id):
                    state["phase"] = "BLOCKED"; state["next_stage"] = None
                    state["statuses"]["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
                    route = "WAIT_HUMAN"
```

The ledger requires the exact bounded criterion and verified files, then keeps a proven targeted diagnostic in a human-waiting state (`escalation.py:366–387`):

Source excerpt — `escalation.py` lines 366–371:
```python
                if item.get("continuation_task_id") == task_id and item["state"] == "CONTINUATION_CONSUMED":
                    if not run_id or run_id != item.get("continuation_run_id"):
                        raise EscalationError("continuation completion run mismatch")
                    proven = (accepted and isinstance(evidence, dict) and
                              evidence.get("condition") == item["permission"]["success_criterion"] and
                              isinstance(evidence.get("verified_files"), list) and bool(evidence["verified_files"]))
```

The listed files must also be re-read beneath the task root and match recorded bytes and SHA-256 (`escalation.py:374–380`):

Source excerpt — `escalation.py` lines 375–380:

```python
                            for descriptor in evidence["verified_files"]:
                                raw, _ = read_stable_beneath(self.root.parent / task_id, descriptor["path"])
                                if not raw or len(raw) != descriptor["bytes"] or hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
                                    proven = False
                        except (ContractError, OSError, KeyError, TypeError):
                            proven = False
```

Source excerpt — `escalation.py` lines 382–385:
```python
                    if proven and route == "TARGETED_DIAGNOSTIC":
                        item["state"] = "DIAGNOSTIC_COMPLETE_WAIT_HUMAN"
                    else:
                        item["state"] = "RESOLVED" if proven else "WAIT_HUMAN"
```

The unpassed IMPLEMENT branch of `_advance` stays blocked:

Source excerpt — `controller.py` lines 2260–2269:
```python
        if not passed:
            if stage == "PLAN_REVIEW" and result["candidate_fact"] == "REVISION_REQUIRED" and state["plan_revisions"] < 2:
                state["plan_revisions"] += 1; state["next_stage"] = "PLAN"
                state["plan_sha256"] = None; state.pop("reviewed_plan_sha256", None)
                return "PLAN"
            state["next_stage"] = None; state["phase"] = "BLOCKED"
            statuses["TASK_CLOSURE_STATUS"] = "FIX_REQUIRED" if stage == "ACCEPTANCE" else "HIGH_REASONING_REVIEW_REQUIRED"
            if stage == "IMPLEMENT": statuses["IMPLEMENTATION_STATUS"] = "ESCALATED"
            if stage == "ACCEPTANCE": statuses["INDEPENDENT_ACCEPTANCE_STATUS"] = "FAIL"
            return "WAIT_HUMAN"
```

For a passed IMPLEMENT stage, CRITICAL work requires independent Acceptance:

Source excerpt — `controller.py` lines 2291–2299:
```python
        elif stage == "IMPLEMENT":
            state.setdefault("implementer_actor_ids", []).append(invitation["actor_id"])
            statuses["IMPLEMENTATION_STATUS"] = "COMPLETE"
            workflow = state["workflow_policy"]
            acceptance_required = (state["task_class"] == "CRITICAL" or
                workflow["independent_acceptance_required"] or
                any(g["required"] and g["phase"] == "ACCEPTANCE" for g in state["required_gates"]))
            if acceptance_required:
                statuses["TASK_CLOSURE_STATUS"] = "READY_FOR_INDEPENDENT_ACCEPTANCE"; route = "ACCEPTANCE"
```

The policy keeps those independent roles and evidence semantics explicit (`workflow-routing.md:9,13,21`):

Source excerpt — `workflow-routing.md` line 9:
```markdown
- CRITICAL: Planner → independent Plan Review → deterministic Handoff → Implementer → independent Acceptance.
```

Source excerpt — `workflow-routing.md` line 13, opening sentence:
```markdown
The user's original request authorizes listed edits within frozen paths and declared local checks.
```

Source excerpt — `workflow-routing.md` line 21:
```markdown
Every gate freezes owner, phase, source, goal criticality, evidence role, closure gate, and reuse. A role cannot pass a future-phase or human-owned gate. `HUMAN_OBSERVATION` receipts are stored as `OBSERVED`, remain separate from tool-verified `PASS`, and never silently waive a requirement.
```

The policy lines above do not specifically name GUI or download actions; those boundaries come from the Chief Reviewer Directive and preserved project authorization, not an expanded reading of this policy.

## Source conclusion

For the required invariant—continue the original task and same issue without resetting its consumed continuation or changing any of its 28 required gates—the reviewed entrances yield **NO_SUPPORTED_ROUTE**. The exact blocker is the absence of a supported transition from `WAIT_HUMAN` with continuation count 1 to a state that can be authorized and allocated, while `reconcile` explicitly refuses unresolved/exhausted issues and issue authorization requires an unused `ANALYSIS_RETURNED` continuation. This conclusion is limited to the selected source bytes and named recovery dependency. The installed full release tree and platform enforcement were not reverified in this review; runtime binding remains unproven.
