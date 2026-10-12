"""Supervised v3 controller. Trusted operators import facts; roles never own routing.

Native supervision offers ROLE_POLICY and POST_IDENTITY_AUDIT, not OS isolation.
No method here launches a worker or grants network/browser capabilities.
"""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import stat
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .budgets import validate_compact_state
from .contracts import (ContractError, GateSpec, path_is_within_scope, safe_relative_path, validate_contract_arrays,
                        validate_gate_results, validate_json_bytes)
from .lifecycle import Journal
from .snapshots import snapshot, snapshot_digest, compare
from .status import StatusFacts
from .version import RELEASE_VERSION
from .writers import Writers, WriterError, transaction as writer_transaction

ROLE_CONFIG_KEYS = {"PLANNER":"planner", "PLAN_REVIEWER":"plan_reviewer", "HANDOFF_COMPILER":"handoff_compiler", "IMPLEMENTER":"implementer", "ACCEPTANCE_REVIEWER":"acceptance_reviewer", "HIGH_REASONING_REVIEWER":"high_reasoning_reviewer"}


class ControllerError(RuntimeError):
    pass


ROLE_FOR_STAGE = {"PLAN": "PLANNER", "PLAN_REVIEW": "PLAN_REVIEWER", "HANDOFF": "HANDOFF_COMPILER",
                  "IMPLEMENT": "IMPLEMENTER", "ACCEPTANCE": "ACCEPTANCE_REVIEWER"}
SCHEMAS = Path(__file__).resolve().parents[2] / "schemas/v3"
SCHEMA_VALIDATION_SELECTOR = "schemas/v3/schema-validation-receipt.schema.json"
SCHEMA_API_VERSION = "1"
ISSUE_SCHEMA_VALIDATIONS = {
    "ANALYSIS": ("schemas/v3/high-review-analysis.schema.json", "HIGH_REVIEW_ANALYSIS"),
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value: Any) -> str:
    return _sha(json.dumps(value, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8"))


def _read_regular(path: Path, root: Path | None = None) -> bytes:
    path = path.absolute()
    if root is not None:
        try:
            rel = path.relative_to(root.absolute())
        except ValueError as exc:
            raise ControllerError("file escapes its evidence root") from exc
        current = root.absolute()
        for part in rel.parts:
            current /= part
            if current.is_symlink():
                raise ControllerError("evidence or contract traverses a symlink")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ControllerError("evidence or contract is not a regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read()
        after = os.fstat(fd)
        named = path.stat(follow_symlinks=False)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode)
        if identity(before) != identity(after) or identity(after) != identity(named):
            raise ControllerError("file changed during verification")
        return raw
    finally:
        os.close(fd)


def _json_atomic(path: Path, value: dict, *, immutable: bool = False) -> None:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2).encode() + b"\n"
    if path.name == "state.json":
        raw = validate_compact_state(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and immutable:
        if _read_regular(path) != raw:
            raise ControllerError("immutable fact conflicts with existing bytes")
        return
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".candidate-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _write_immutable_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o400)
    except FileExistsError:
        if _read_regular(path) != raw:
            raise ControllerError("immutable input snapshot conflicts with existing bytes")
        return
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _schema_validation_matrix(stage: str) -> list[dict[str, str]]:
    values = [{"purpose": "CONTRACT", "schema_selector": "schemas/v3/task.schema.json",
               "input_kind": "PUBLISHED_CONTRACT" if stage == "PLAN" else "PINNED_CONTRACT"},
              {"purpose": "RESULT", "schema_selector": "schemas/v3/result.schema.json",
               "input_kind": "ROLE_RESULT"}]
    if stage == "ACCEPTANCE":
        values.insert(1, {"purpose": "IMPLEMENTATION_RESULT", "schema_selector": "schemas/v3/result.schema.json",
                          "input_kind": "ACCEPTED_IMPLEMENTATION_RESULT"})
    return values


@contextmanager
def task_lock(state_root: Path, task_id: str):
    if not task_id or "/" in task_id or "\\" in task_id or task_id in {".", ".."}:
        raise ControllerError("unsafe task ID")
    locks = state_root / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    fd = os.open(locks / (task_id + ".lock"), os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ControllerError("another controller owns this task") from exc
        yield
    finally:
        os.close(fd)


def _validate(raw: bytes, name: str) -> dict:
    from .schema_validation import SchemaBundle
    short = name.split("#", 1)[0]
    selector = name
    if not short.startswith("schemas/"):
        path = f"schemas/v3/{short}"
        selector = path + ("#/$defs/" + name.split("#", 1)[1] if "#" in name else "")
    bundle = SchemaBundle.load(Path(__file__).resolve().parents[2])
    bundle.validate(selector, raw)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControllerError("contract must be UTF-8 JSON") from exc


class CandidateController:
    def __init__(self, *, state_root: Path, repo: Path, release_root: Path | None = None,
                 resource_root: Path | None = None, effective_config: dict[str, Any] | None = None):
        self.repo = repo.resolve(strict=True)
        # Canonicalize against the resolved repository. Ancestors above the repo
        # (e.g. the macOS /var -> /private/var symlink) are outside the guarded
        # boundary; only symlink components inside the repository may escape it.
        candidate = Path(state_root)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve(strict=False)
        try:
            rel = resolved.relative_to(self.repo)
        except ValueError as exc:
            raise ControllerError("supervised state must remain inside the repository") from exc
        safe_relative_path(rel.as_posix())
        if not rel.parts or rel.parts[0] != "harness-development" or len(rel.parts) < 2:
            raise ControllerError("fresh supervised state belongs under harness-development/<root>")
        walk = self.repo
        for part in rel.parts:
            walk = walk / part
            if walk.is_symlink():
                raise ControllerError("state root traverses a symlink")
        self.state_root = self.repo / rel
        self.release_root = release_root
        self.resource_root = Path(resource_root or os.environ.get("HARNESS_RESOURCE_ROOT") or Path(__file__).resolve().parents[2]).resolve(strict=True)
        self.effective_config = effective_config or {"mode": "NATIVE_SUPERVISED"}
        if self.effective_config != {"mode": "NATIVE_SUPERVISED"}:
            raise ControllerError("unsupported runner, egress, or assurance configuration")

    def _snapshot(self) -> dict:
        value = snapshot(self.repo)
        prefixes = [self.state_root.relative_to(self.repo).as_posix(), "harness-development/.writer-coordination"]
        value["entries"] = [e for e in value["entries"] if not any(e["path"] == prefix or e["path"].startswith(prefix + "/") for prefix in prefixes)]
        # Status is measured, but state artifacts are excluded from product identity.
        value["status"] = [e for e in value["status"] if not any(str(v) == prefix or str(v).startswith(prefix + "/") for v in e.values() for prefix in prefixes)]
        return value

    def _load(self, task_id: str, *, read_only: bool = False) -> tuple[Path, dict]:
        if not task_id or "/" in task_id or "\\" in task_id or task_id in {".", ".."}:
            raise ControllerError("unsafe task ID")
        directory = self.state_root / task_id
        try:
            state = json.loads(_read_regular(directory / "state.json", self.state_root))
        except (OSError, ValueError) as exc:
            raise ControllerError("task state unavailable") from exc
        if state.get("schema_version") != "3" or state.get("task_id") != task_id or state.get("repository") != str(self.repo):
            raise ControllerError("legacy or foreign state is read-only")
        if not read_only and state.get("release_version") != RELEASE_VERSION:
            raise ControllerError("legacy release state is read-only; operate it with its original immutable release CLI and resources")
        return directory, state

    def inspect(self, task_id: str) -> dict:
        _, state = self._load(task_id, read_only=True)
        return state

    def create_task(self, goal: str, *, task_class: str = "STANDARD", allowed_paths: list[str] | None = None,
                    capability_policy: dict | None = None, runtime_policy: dict | None = None) -> dict:
        if not goal.strip() or task_class not in {"AUTO", "QUICK", "STANDARD", "CRITICAL"}:
            raise ControllerError("task requires a goal and valid class")
        if capability_policy not in (None, {"network": "OFF", "browser": False, "destinations": []}):
            raise ControllerError("network/worker browser adapters are unsupported")
        paths = allowed_paths or []
        for path in paths:
            safe_relative_path(path)
        task_id = "TASK-" + uuid.uuid4().hex
        with task_lock(self.state_root, task_id):
            directory = self.state_root / task_id
            directory.mkdir(parents=True, exist_ok=False)
            start = self._snapshot()
            _json_atomic(directory / "start-snapshot.json", start, immutable=True)
            state = {"schema_version": "3", "task_id": task_id, "release_version": RELEASE_VERSION,
                "repository": str(self.repo), "goal": goal, "task_class": task_class,
                "start_snapshot_sha256": snapshot_digest(start), "next_stage": "PLAN", "phase": "IN_PROGRESS",
                "plan_sha256": None, "contract_sha256": None, "handoff_sha256": None,
                "active_run_id": None, "run_ids": [], "allowed_paths": paths,
                "statuses": StatusFacts().project(), "plan_revisions": 0, "accepted_gates": {},
                "workflow_policy": None, "human_observations": {}, "waived_gates": {},
                "convergence": {"meaningful_attempts":0,"consecutive_no_progress":0,
                    "last_attempt":"尚未開始","information_gain":False,"stuck":False}}
            _json_atomic(directory / "state.json", state)
            Journal(directory / "events.jsonl").append("TASK_CREATED", {"task_id": task_id, "goal_sha256": _sha(goal.encode())})
            return state

    def _run(self, directory: Path, state: dict, run_id: str | None = None) -> tuple[Path, dict]:
        rid = run_id or state.get("active_run_id")
        if not rid or rid not in state["run_ids"]:
            raise ControllerError("no controller-allocated run")
        root = directory / "runs" / rid
        run_bytes = _read_regular(root / "run.json", directory)
        if state.get("run_sha256", {}).get(rid) != _sha(run_bytes):
            raise ControllerError("immutable run bytes changed")
        run = _validate(run_bytes, "run.schema.json")
        if run.get("release_version") != RELEASE_VERSION:
            raise ControllerError("old runs require their original immutable release CLI and resources")
        if run["effective_runtime_configuration"] != self.effective_config:
            raise ControllerError("legacy/non-supervised run admission is forbidden")
        if run.get("resource_root") != str(self.resource_root):
            raise ControllerError("run resource root differs from immutable selected resources")
        _, digest = self._resource_inventory()
        if digest != run.get("release_sha256"):
            raise ControllerError("selected immutable resource inventory changed")
        return root, run

    def _resource_inventory(self) -> tuple[list[dict], str]:
        inventory_file = self.resource_root / f"templates/v{RELEASE_VERSION}/resource-inventory.json"
        try:
            listed = json.loads(_read_regular(inventory_file))
        except (OSError, ValueError) as exc:
            raise ControllerError("selected release exact resource inventory is unavailable") from exc
        if not isinstance(listed, list) or not listed or any(not isinstance(x, str) for x in listed):
            raise ControllerError("selected release exact resource inventory is malformed")
        if len(listed) != len(set(listed)):
            raise ControllerError("selected release exact resource inventory has duplicate paths")
        roots = sorted(set(listed + [f"templates/v{RELEASE_VERSION}/resource-inventory.json"]))
        entries = []
        for rel in roots:
            safe_relative_path(rel)
            path = self.resource_root / rel
            if path.is_symlink() or not path.is_file():
                raise ControllerError("exact resource inventory contains a missing or unsafe file: " + rel)
            raw = _read_regular(path)
            entries.append({"path":rel,"bytes":len(raw),"sha256":_sha(raw)})
        if not entries: raise ControllerError("immutable resource inventory is empty")
        entries.sort(key=lambda e:e["path"])
        return entries, _sha(json.dumps(entries,sort_keys=True,separators=(",",":")).encode())

    def _role_policy(self, role: str) -> dict:
        defaults = self.resource_root / f"templates/v{RELEASE_VERSION}/runtime-defaults.json"
        if not defaults.is_file():
            raise ControllerError("selected release runtime defaults are missing")
        value = json.loads(_read_regular(defaults))
        key = ROLE_CONFIG_KEYS[role]
        configured = value.get(key)
        if not isinstance(configured, dict) or not isinstance(configured.get("model"), str):
            raise ControllerError(f"configured model unavailable for {role}; no fallback")
        return {"role": role, "model": configured["model"],
                "reasoning_effort": configured.get("reasoning_effort", "default/unspecified"),
                "runtime_defaults_sha256": _sha(_read_regular(defaults)),
                "fallback_requires_existing_user_authorization": value.get("fallback_requires_existing_user_authorization") is True}

    def delegation_limits(self) -> dict:
        defaults = json.loads(_read_regular(self.resource_root / f"templates/v{RELEASE_VERSION}/runtime-defaults.json"))
        result = {"max_parallel_read_only_helpers": defaults.get("max_parallel_read_only_helpers", 2),
                  "max_parallel_writers": defaults.get("max_parallel_writers", 0)}
        if any(type(v) is not int or not 0 <= v <= 4 for v in result.values()):
            raise ControllerError("configured delegation capacity must be an integer from zero to four")
        return result

    def _writer_action(self, task_id: str, worker_id: str, *, action: str, run_id: str | None = None, **kwargs) -> dict:
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            root, run = self._run(directory, state, run_id)
            if run["stage"] != "IMPLEMENT" or state.get("active_run_id") != run["run_id"]:
                raise ControllerError("writer operation requires the active IMPLEMENT run")
            if state.get("phase") != "IN_PROGRESS" or self._pending(task_id):
                raise ControllerError("unresolved task blocker prevents writer operation")
            try:
                with writer_transaction(self) as coordination:
                    writers = Writers(self, directory, state, root, run)
                    result = getattr(writers, action)(worker_id, coordination=coordination, **kwargs)
                    if action in {"finish", "merge"}:
                        _validate(json.dumps(result).encode(), "writer-receipt.schema.json")
                    _json_atomic(directory / "state.json", state)
                    Journal(directory / "events.jsonl").append("WRITER_" + action.upper(), {
                        "run_id": run["run_id"], "writer_id": worker_id,
                        "allocation_sha256": state["writer_allocations"][run["run_id"]][worker_id]["sha256"]})
                    return result
            except (WriterError, ContractError, OSError, ValueError) as exc:
                raise ControllerError(str(exc)) from exc

    def allocate_writer(self, task_id: str, worker_id: str, *, worktree: Path, allowed_paths: list[str],
                        actor_id: str, platform_session_id: str, invitation_bytes: bytes,
                        run_id: str | None = None, issue_id: str = "ROOT", attempt_index: int = 1) -> dict:
        return self._writer_action(task_id, worker_id, action="allocate", run_id=run_id,
            worktree=worktree, allowed_paths=allowed_paths, actor_id=actor_id,
            platform_session_id=platform_session_id, invitation_bytes=invitation_bytes,
            issue_id=issue_id, attempt_index=attempt_index)

    def finish_writer(self, task_id: str, worker_id: str, *, completion_bytes: bytes,
                      run_id: str | None = None) -> dict:
        return self._writer_action(task_id, worker_id, action="finish", run_id=run_id,
                                  completion_bytes=completion_bytes)

    def merge_writer(self, task_id: str, worker_id: str, *, run_id: str | None = None) -> dict:
        return self._writer_action(task_id, worker_id, action="merge", run_id=run_id)

    def allocate_run(self, task_id: str, stage: str, *, controller_path: Path, schema_path: Path,
                     prompt_path: Path, policy_path: Path, effective_config: dict | None = None,
                     selected_issue_id: str | None = None) -> dict:
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            if state.get("active_run_id"):
                if self._pending(task_id):
                    raise ControllerError("unresolved STOP prevents active run resume")
                _, active = self._run(directory, state)
                if stage == active["stage"]:
                    return active
                raise ControllerError("active run must be completed before another stage")
            if stage != state["next_stage"] or stage not in ROLE_FOR_STAGE or state["phase"] != "IN_PROGRESS":
                raise ControllerError("stage differs from controller-owned next eligible action")
            if effective_config is not None and effective_config != self.effective_config:
                raise ControllerError("unsupported runtime configuration")
            if stage in {"PLAN_REVIEW", "HANDOFF"} and not state["plan_sha256"]:
                raise ControllerError("published Plan is missing")
            if stage in {"IMPLEMENT", "ACCEPTANCE"} and not state["handoff_sha256"]:
                raise ControllerError("frozen Handoff is missing")
            if stage in {"PLAN_REVIEW", "HANDOFF", "IMPLEMENT", "ACCEPTANCE"}:
                if _sha(_read_regular(directory / "plan-contract.json", directory)) != state["plan_contract_sha256"]:
                    raise ControllerError("reviewed machine Plan contract changed")
                if _sha(_read_regular(directory / "plan.md", directory)) != state["plan_sha256"]:
                    raise ControllerError("Plan bytes changed after publication")
            if state["handoff_sha256"] and _sha(_read_regular(directory / "handoff.json", directory)) != state["handoff_sha256"]:
                raise ControllerError("Handoff bytes changed after freezing")
            pre = self._snapshot()
            rid = str(uuid.uuid4()); root = directory / "runs" / rid
            binding_paths = {"controller": controller_path, "schema": schema_path, "prompt": prompt_path, "policy": policy_path}
            validation_sources = {str(p.resolve()): _sha(_read_regular(p)) for p in list(Path(__file__).parent.glob("*.py")) + list(SCHEMAS.glob("*.schema.json")) + list(binding_paths.values())}
            resource_inventory, resource_digest = self._resource_inventory()
            from .schema_validation import SchemaBundle
            schema_bundle = SchemaBundle.load(self.resource_root, verified_release_root=self.release_root)
            if schema_bundle.resource_inventory_sha256 != resource_digest:
                raise ControllerError("schema bundle inventory differs from the immutable run resource inventory")
            schema_descriptor = schema_bundle.validation_descriptor(_schema_validation_matrix(stage))
            bindings = {name + "_sha256": _sha(_read_regular(path)) for name, path in {
                "controller": controller_path, "schema": schema_path, "prompt": prompt_path, "policy": policy_path}.items()}
            run = {"run_format_version": "3", "run_id": rid, "task_id": task_id, "stage": stage,
                "role": ROLE_FOR_STAGE[stage], "operation_scope": "STAGE", "release_version": RELEASE_VERSION, "release_sha256": resource_digest,
                "resource_root": str(self.resource_root), "resource_inventory": resource_inventory,
                **bindings, "validation_sources": validation_sources, "contract_sha256": state["contract_sha256"], "plan_sha256": state["plan_sha256"],
                "handoff_sha256": state["handoff_sha256"], "plan_contract_sha256": state.get("plan_contract_sha256"), "source_sha256": snapshot_digest(pre),
                "effective_runtime_configuration": self.effective_config, "network_access": False, "browser_access": False,
                "model_policy": self._role_policy(ROLE_FOR_STAGE[stage]),
                "offline_schema_validation": schema_descriptor,
                "assurance": ["ROLE_POLICY", "POST_IDENTITY_AUDIT"], "invitation_nonce": uuid.uuid4().hex,
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}
            repair = state.get("bounded_repair")
            if stage == "IMPLEMENT" and repair and not repair.get("run_id"):
                decision = json.loads(_read_regular(directory / repair["decision_path"], directory))
                self._verify_routing_files(directory, decision)
                run["continuation_permission"] = {k:decision[k] for k in
                    ("contract_sha256", "allowed_paths", "success_criterion", "stop_condition")}
                run["continuation_permission"].update(action=decision["permitted_action"],
                    repair_decision_sha256=repair["decision_sha256"])
                repair["run_id"] = rid
            _validate(json.dumps(run).encode(), "run.schema.json")
            if (self.state_root / "issues").exists():
                from .escalation import IssueLedger
                permission = IssueLedger(self.state_root / "issues").guard_task(task_id, stage, state["contract_sha256"], state["allowed_paths"], run_id=rid, selected_issue_id=selected_issue_id)
                if permission:
                    run["operation_scope"] = "ISSUE_CONTINUATION"
                    run["continuation_permission"] = permission
            _validate(json.dumps(run).encode(), "run.schema.json")
            _json_atomic(root / "pre-snapshot.json", pre, immutable=True)
            _json_atomic(root / "run.json", run, immutable=True)
            if stage in {"PLAN_REVIEW", "HANDOFF"}:
                contract_raw = _read_regular(directory / "plan-contract.json", directory)
                _write_immutable_bytes(root / "origin-contract.json", contract_raw)
            elif stage in {"IMPLEMENT", "ACCEPTANCE"}:
                contract_raw = _read_regular(directory / "handoff.json", directory)
                _write_immutable_bytes(root / "origin-contract.json", contract_raw)
                _write_immutable_bytes(root / "origin-handoff.json", contract_raw)
            if state.get("plan_sha256") and (directory / "plan.md").is_file():
                _write_immutable_bytes(root / "origin-plan.md", _read_regular(directory / "plan.md", directory))
            state["run_ids"].append(rid); state["active_run_id"] = rid
            state.setdefault("run_sha256", {})[rid] = _sha(_read_regular(root / "run.json", directory))
            _json_atomic(directory / "state.json", state)
            Journal(directory / "events.jsonl").append("RUN_ALLOCATED", {"run_id": rid, "stage": stage})
            return run

    def publish_plan(self, task_id: str, plan: bytes, *, contract_bytes: bytes, run_id: str | None = None, **untrusted) -> str:
        if untrusted:
            raise ControllerError("caller review flags cannot authorize publication")
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            if state["next_stage"] != "PLAN" or state["phase"] != "IN_PROGRESS" or self._pending(task_id):
                raise ControllerError("only the allocated Planner can publish Plan bytes")
            run_root, run = self._run(directory, state)
            if run["stage"] != "PLAN" or (run_id is not None and run_id != run["run_id"]):
                raise ControllerError("publication differs from the active Planner run")
            if not plan.decode("utf-8").strip():
                raise ControllerError("Plan is empty")
            contract = _validate(contract_bytes, "task.schema.json")
            if (contract["task_id"], contract["goal"]) != (task_id, state["goal"]):
                raise ControllerError("Plan contract differs from task identity")
            if state["task_class"] != "AUTO" and contract["task_class"] != state["task_class"]:
                raise ControllerError("Planner changed the task risk level selected by the user")
            workflow = contract["workflow_policy"]
            if contract["task_class"] == "CRITICAL" and not (workflow["plan_review_required"] and workflow["independent_acceptance_required"]):
                raise ControllerError("CRITICAL work requires independent Plan Review and Acceptance")
            limits = self.delegation_limits()
            if any(workflow.get(k, 0) > limit for k, limit in limits.items()):
                raise ControllerError("Plan delegation capacity exceeds selected runtime defaults")
            validate_contract_arrays(gate_specs=contract["gate_specs"], required_evidence=contract["required_evidence"], allowed_paths=contract["allowed_paths"], phase="PLAN")
            for gate in contract["gate_specs"]:
                if gate["required"] and gate["phase"] == "HANDOFF":
                    raise ControllerError("Handoff is a deterministic compiler step; required checks belong to Implement, Acceptance, or Post-check")
            if state["allowed_paths"] and any(
                not any(path_is_within_scope(path, scope) for scope in state["allowed_paths"])
                for path in contract["allowed_paths"]
            ):
                raise ControllerError("Plan expands the write scope you authorized when starting this task")
            if workflow["independent_acceptance_required"] and not any(
                gate["required"] and gate["phase"] == "ACCEPTANCE" for gate in contract["gate_specs"]
            ):
                raise ControllerError("independent Acceptance needs at least one required Acceptance gate")
            (directory / "plan-contract.json").write_bytes(contract_bytes)
            state["plan_contract_sha256"] = _sha(contract_bytes)
            state["task_class"] = contract["task_class"]
            state["required_gates"] = contract["gate_specs"]
            state["required_evidence"] = contract["required_evidence"]
            state["workflow_policy"] = workflow
            digest = _sha(plan)
            path = directory / "plans" / (digest + ".md")
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(plan)
            (directory / "plan.md").write_bytes(plan)
            publication_value = {
                "plan_sha256": digest,
                "plan_contract_sha256": _sha(contract_bytes),
                "plan_path": f"runs/{run['run_id']}/publications/{digest}_{_sha(contract_bytes)}/plan.md",
                "contract_path": f"runs/{run['run_id']}/publications/{digest}_{_sha(contract_bytes)}/contract.json",
            }
            publication_dir = directory / f"runs/{run['run_id']}/publications/{digest}_{_sha(contract_bytes)}"
            _write_immutable_bytes(directory / publication_value["plan_path"], plan)
            _write_immutable_bytes(directory / publication_value["contract_path"], contract_bytes)
            _json_atomic(directory / "plan-publication.json", publication_value)
            publication_raw = _read_regular(directory / "plan-publication.json", directory)
            _write_immutable_bytes(publication_dir / "publication.json", publication_raw)
            state["plan_sha256"] = digest; state.pop("reviewed_plan_sha256", None)
            _json_atomic(directory / "state.json", state)
            Journal(directory / "events.jsonl").append("PLAN_PUBLISHED", {
                "run_id": run["run_id"], "plan_sha256": digest,
                "plan_contract_sha256": _sha(contract_bytes),
                "plan_path": publication_value["plan_path"],
                "contract_path": publication_value["contract_path"],
                "publication_sha256": _sha(publication_raw),
            })
            return digest

    def _compile_handoff(self, directory: Path, state: dict) -> str:
        """Freeze the reviewed Plan mechanically; no model or approval prompt is needed."""
        raw = _read_regular(directory / "plan-contract.json", directory)
        if _sha(raw) != state.get("plan_contract_sha256"):
            raise ControllerError("Handoff compiler input differs from the accepted Plan")
        contract = _validate(raw, "task.schema.json")
        if state["allowed_paths"] and any(
            not any(path_is_within_scope(path, scope) for scope in state["allowed_paths"])
            for path in contract["allowed_paths"]
        ):
            raise ControllerError("compiled Handoff expands the authorized write scope")
        digest = _sha(raw)
        path = directory / "handoff.json"
        if path.exists() and _sha(_read_regular(path, directory)) != digest:
            raise ControllerError("frozen Handoff cannot be replaced")
        if not path.exists():
            path.write_bytes(raw)
        state.update(contract_sha256=digest, handoff_sha256=digest,
                     required_gates=contract["gate_specs"], required_evidence=contract["required_evidence"],
                     allowed_paths=contract["allowed_paths"], handoff_compiler="DETERMINISTIC_FROM_REVIEWED_PLAN")
        gate_lines = "\n".join(f"- {g['gate_id']}: {g['phase']} / {g['goal_criticality']} / {g['evidence_role']} / {g['closure_gate']}" for g in contract["gate_specs"])
        summary = ("# 執行交接\n\n"
                   f"目標：{contract['goal']}\n\n"
                   f"風險級別：{contract['task_class']}\n\n"
                   "允許修改的範圍：\n" + "\n".join(f"- `{p}`" for p in contract["allowed_paths"]) +
                   "\n\n需要完成的檢查：\n" + gate_lines +
                   "\n\n使用者授權：依已審閱的計畫完成上述範圍內的工作與列出的檢查；不包含 commit、push 或 deploy。\n")
        if contract["workflow_policy"].get("max_parallel_writers", 0):
            summary += (f"\n平行寫入容量：{contract['workflow_policy']['max_parallel_writers']}；"
                        "僅在實作階段分派，每位作者使用外部獨立 worktree、互斥範圍及控制器記錄。所有檢查在合併後執行。\n")
        handoff_md = directory / "handoff.md"
        if handoff_md.exists() and _read_regular(handoff_md, directory).decode("utf-8") != summary:
            raise ControllerError("deterministic Handoff summary changed after freezing")
        if not handoff_md.exists():
            handoff_md.write_text(summary, encoding="utf-8")
        return digest

    def publish_handoff(self, task_id: str, contract_bytes: bytes, *, run_id: str | None = None) -> str:
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            if state["next_stage"] != "HANDOFF" or state["phase"] != "IN_PROGRESS" or self._pending(task_id) or state.get("reviewed_plan_sha256") != state["plan_sha256"]:
                raise ControllerError("Handoff requires the accepted reviewed Plan")
            root, run = self._run(directory, state)
            if run["stage"] != "HANDOFF" or (run_id is not None and run_id != run["run_id"]):
                raise ControllerError("publication differs from the active Compiler run")
            if _sha(contract_bytes) != state["plan_contract_sha256"]:
                raise ControllerError("Handoff differs from reviewed machine Plan")
            contract = _validate(contract_bytes, "task.schema.json")
            if (contract["task_id"], contract["goal"], contract["task_class"]) != (task_id, state["goal"], state["task_class"]):
                raise ControllerError("Handoff differs from frozen goal identity")
            if contract["capability_policy"] != {"network": "OFF", "browser": False, "destinations": []}:
                raise ControllerError("unsupported adapter capability")
            validate_contract_arrays(gate_specs=contract["gate_specs"], required_evidence=contract["required_evidence"],
                allowed_paths=contract["allowed_paths"], phase="HANDOFF")
            if state["allowed_paths"] and any(
                not any(path_is_within_scope(path, scope) for scope in state["allowed_paths"])
                for path in contract["allowed_paths"]
            ):
                raise ControllerError("Handoff expands approved write scope")
            digest = _sha(contract_bytes)
            path = directory / "handoff.json"
            if path.exists() and _sha(_read_regular(path, directory)) != digest:
                raise ControllerError("frozen Handoff cannot be replaced")
            path.write_bytes(contract_bytes)
            _write_immutable_bytes(root / "origin-contract.json", contract_bytes)
            _write_immutable_bytes(root / "origin-handoff.json", contract_bytes)
            state.update(contract_sha256=digest, handoff_sha256=digest, required_gates=contract["gate_specs"],
                required_evidence=contract["required_evidence"], allowed_paths=contract["allowed_paths"],
                handoff_compiler="ROLE_REVIEWED_EXACT_PLAN")
            _json_atomic(directory / "state.json", state)
            return digest

    def _provenance(self, directory: Path, run: dict, result_bytes: bytes, invitation: bytes, completion: bytes) -> tuple[dict, dict]:
        inv = _validate(invitation, "run.schema.json#invitation")
        comp = _validate(completion, "run.schema.json#completion")
        for record in (inv, comp):
            for key in ("task_id", "run_id", "stage", "role", "invitation_nonce"):
                if record[key] != run[key]:
                    raise ControllerError("native provenance differs from allocated run")
            raw = _read_regular(directory / safe_relative_path(record["raw_path"]), directory)
            if not raw or _sha(raw) != record["raw_sha256"]:
                raise ControllerError("native platform record is missing or changed")
            try:
                captured = json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ControllerError("raw native platform record is not structured JSON") from exc
            if not isinstance(captured, dict) or captured.get("capture_kind") not in {"INVITATION", "COMPLETION"}:
                raise ControllerError("raw native record lacks trusted capture envelope")
            for key in ("task_id", "run_id", "stage", "role", "invitation_nonce", "actor_id", "platform_session_id"):
                if captured.get(key) != record.get(key):
                    raise ControllerError(f"raw native capture contradicts imported descriptor: {key}")
            if captured.get("capture_kind") == "INVITATION":
                policy = run.get("model_policy", {})
                if (record.get("requested_model") != policy.get("model") or
                    record.get("requested_effort", "default/unspecified") != policy.get("reasoning_effort")):
                    raise ControllerError("invitation request differs from configured model/effort")
                configured_effort = policy.get("reasoning_effort", "default/unspecified")
                if captured.get("requested_model") != record.get("requested_model"):
                    raise ControllerError("raw request does not prove explicit configured model")
                if configured_effort != "default/unspecified" and captured.get("requested_effort") != configured_effort:
                    raise ControllerError("raw request does not prove configured reasoning effort")
                if configured_effort == "default/unspecified" and captured.get("requested_effort") not in (None, ""):
                    raise ControllerError("unspecified effort was presented as an explicit request")
            reported = captured.get("reported_model")
            if reported not in (None, "UNKNOWN") and reported != record.get("reported_model"):
                raise ControllerError("reported model differs from raw platform response")
        if comp["platform_session_id"] != inv["platform_session_id"] or comp["actor_id"] != inv["actor_id"]:
            raise ControllerError("completion differs from invited native worker")
        if comp["result_sha256"] != _sha(result_bytes):
            raise ControllerError("completion result digest mismatch")
        policy = run.get("model_policy", {})
        for record in (inv, comp):
            if record.get("requested_model") != policy.get("model"):
                raise ControllerError("native request model differs from configured role model")
            if record.get("requested_effort", "default/unspecified") != policy.get("reasoning_effort"):
                raise ControllerError("native requested effort differs from configured role effort")
            if record.get("reported_model") not in (None, policy.get("model")):
                raise ControllerError("provider reported a contradictory model")
            if record.get("reported_effort") not in (None, policy.get("reasoning_effort")):
                raise ControllerError("provider reported a contradictory reasoning effort")
        return inv, comp

    def _verified_invitation(self, directory: Path, run: dict, invitation_bytes: bytes) -> tuple[dict, bytes]:
        inv = _validate(invitation_bytes, "run.schema.json#invitation")
        for key in ("task_id", "run_id", "stage", "role", "invitation_nonce"):
            if inv[key] != run[key]:
                raise ControllerError("native invitation differs from allocated run")
        raw = _read_regular(directory / safe_relative_path(inv["raw_path"]), directory)
        if not raw or _sha(raw) != inv["raw_sha256"]:
            raise ControllerError("native invitation capture is missing or changed")
        try:
            captured = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ControllerError("native invitation capture is not structured JSON") from exc
        if not isinstance(captured, dict) or captured.get("capture_kind") != "INVITATION":
            raise ControllerError("raw platform record is not an actual INVITATION capture")
        for key in ("task_id", "run_id", "stage", "role", "invitation_nonce", "actor_id", "platform_session_id"):
            if captured.get(key) != inv.get(key):
                raise ControllerError(f"raw invitation contradicts imported descriptor: {key}")
        policy = run.get("model_policy", {})
        if inv.get("requested_model") != policy.get("model"):
            raise ControllerError("invitation request differs from configured model")
        configured_effort = policy.get("reasoning_effort", "default/unspecified")
        if inv.get("requested_effort", "default/unspecified") != configured_effort:
            raise ControllerError("invitation effort differs from configured role effort")
        if captured.get("requested_model") != inv.get("requested_model"):
            raise ControllerError("raw invitation does not prove the configured model request")
        if configured_effort != "default/unspecified" and captured.get("requested_effort") != configured_effort:
            raise ControllerError("raw invitation does not prove the configured reasoning effort")
        if configured_effort == "default/unspecified" and captured.get("requested_effort") not in (None, ""):
            raise ControllerError("unspecified effort was presented as an explicit request")
        reported = captured.get("reported_model")
        if reported not in (None, "UNKNOWN") and reported != inv.get("reported_model"):
            raise ControllerError("reported model differs from raw platform response")
        return inv, raw

    def _schema_bundle_for_run(self, run: dict):
        from .schema_validation import SchemaBundle
        descriptor = run.get("offline_schema_validation")
        if not isinstance(descriptor, dict) or descriptor.get("api_version") != SCHEMA_API_VERSION:
            raise ControllerError("run has no supported frozen offline schema descriptor")
        if descriptor.get("resource_root") != run.get("resource_root"):
            raise ControllerError("schema descriptor resource root differs from run")
        root = Path(run["resource_root"]).resolve(strict=True)
        if root != self.resource_root:
            raise ControllerError("schema descriptor selects a different immutable source root")
        bundle = SchemaBundle.load(root, verified_release_root=self.release_root)
        if (bundle.resource_inventory_sha256 != descriptor.get("resource_inventory_sha256") or
            bundle.schema_graph_sha256 != descriptor.get("schema_graph_sha256") or
            bundle.package_content_sha256 != descriptor.get("package_content_sha256")):
            raise ControllerError("schema bundle identity differs from allocated run")
        current = bundle.validation_descriptor(descriptor.get("required_validations", []))
        if current["entrypoint"] != descriptor.get("entrypoint") or current["runtime"] != descriptor.get("runtime"):
            raise ControllerError("schema validation endpoint or runtime changed after allocation")
        return bundle

    def register_schema_validation(self, task_id: str, *, run_id: str, purpose: str,
                                   schema_selector: str, input_path: Path,
                                   invitation_bytes: bytes, invocation_kind: str = "CLI",
                                   argv: list[str] | None = None) -> dict:
        """Validate exact stage bytes and publish a journal-registered receipt."""
        from .schema_validation import SchemaValidationFailure
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            root, run = self._run(directory, state, run_id)
            if run.get("operation_scope") not in {"STAGE", "ISSUE_CONTINUATION"} or state.get("active_run_id") != run["run_id"]:
                raise ControllerError("stage schema validation requires the active allocated role")
            if invocation_kind not in {"CLI", "API"}:
                raise ControllerError("unsupported schema validation invocation kind")
            bundle = self._schema_bundle_for_run(run)
            descriptor = run["offline_schema_validation"]
            required = {item["purpose"]: item for item in descriptor["required_validations"]}
            if purpose not in required or required[purpose]["schema_selector"] != schema_selector:
                raise ControllerError("schema purpose or selector is not in the frozen stage matrix")
            if purpose == "IMPLEMENTATION_RESULT" and run["stage"] != "ACCEPTANCE":
                raise ControllerError("implementation result validation is Acceptance-only")
            path = Path(input_path)
            if not path.is_absolute():
                path = directory / path
            raw = _read_regular(path, directory)
            relative = safe_relative_path(path.absolute().relative_to(directory.absolute()).as_posix())
            inv, capture_raw = self._verified_invitation(directory, run, invitation_bytes)
            publication = None
            if purpose == "CONTRACT":
                publication_current = None
                if run["stage"] == "PLAN":
                    publication_current = json.loads(_read_regular(directory / "plan-publication.json", directory))
                    expected_rel = publication_current.get("contract_path")
                    if not expected_rel:
                        raise ControllerError("PLAN has no current published contract input")
                else:
                    expected_rel = f"runs/{run['run_id']}/origin-contract.json"
                if relative != expected_rel:
                    raise ControllerError("CONTRACT receipt input must be the immutable run-origin contract snapshot")
                expected_raw = _read_regular(path, directory)
                if raw != expected_raw:
                    raise ControllerError("published contract bytes differ from preserved input bytes")
                if run["stage"] == "PLAN":
                    plan_path = directory / publication_current["plan_path"]
                    plan_raw = _read_regular(plan_path, directory)
                    publication_raw = _read_regular(plan_path.parent / "publication.json", directory)
                    publication_value = json.loads(publication_raw)
                    if (publication_value.get("plan_sha256") != _sha(plan_raw) or
                        publication_value.get("plan_contract_sha256") != _sha(raw) or
                        publication_value.get("plan_path") != publication_current["plan_path"] or
                        publication_value.get("contract_path") != relative or
                        state.get("plan_sha256") != _sha(plan_raw) or state.get("plan_contract_sha256") != _sha(raw)):
                        raise ControllerError("PLAN publication bytes differ from controller publication state")
                    publication = {"plan_sha256": _sha(plan_raw), "plan_contract_sha256": _sha(raw),
                                   "publication_sha256": _sha(publication_raw)}
                else:
                    effective_contract = run.get("contract_sha256") or run.get("plan_contract_sha256")
                    if not effective_contract or _sha(raw) != effective_contract:
                        raise ControllerError("pinned run contract differs from its preserved origin bytes")
            elif purpose == "IMPLEMENTATION_RESULT":
                if run["stage"] != "ACCEPTANCE":
                    raise ControllerError("IMPLEMENTATION_RESULT is Acceptance-only")
                implementation_run_id = state.get("last_valid_run_id")
                if not implementation_run_id:
                    raise ControllerError("accepted implementation result is unavailable")
                implementation_root, implementation_run = self._run(directory, state, implementation_run_id)
                if implementation_run.get("stage") != "IMPLEMENT":
                    raise ControllerError("last accepted result is not from IMPLEMENT")
                consumption = json.loads(_read_regular(implementation_root / "consumption.json", directory))
                result_rel = f"runs/{implementation_run_id}/submissions/{consumption['admission_sha256']}/candidate-result.json"
                accepted_raw = _read_regular(directory / result_rel, directory)
                if relative != result_rel or raw != accepted_raw:
                    raise ControllerError("IMPLEMENTATION_RESULT must be the currently accepted exact result bytes")
                try:
                    self._verify_consumed_run(directory, state, implementation_run_id)
                except WriterError as exc:
                    raise ControllerError(str(exc)) from exc
            elif purpose == "RESULT":
                if relative == f"runs/{run['run_id']}/consumption.json":
                    raise ControllerError("RESULT input cannot be a controller consumption record")
            if purpose == "CONTRACT":
                if run["stage"] != "PLAN":
                    expected_contract = _read_regular(root / "origin-contract.json", directory)
                    effective_contract = run.get("contract_sha256") or run.get("plan_contract_sha256")
                    if raw != expected_contract or not effective_contract or _sha(raw) != effective_contract:
                        raise ControllerError("CONTRACT input differs from preserved run-origin pin")
            try:
                validated = bundle.validate(schema_selector, raw)
                verdict, error = "VALID", None
            except SchemaValidationFailure as exc:
                verdict = "INVALID" if exc.category in {"INPUT", "INSTANCE"} else "BLOCKED"
                error = {"category": exc.category, "location": exc.location, "reason": exc.reason[:512]}
                validated = {"input_raw_sha256": _sha(raw)}
            context = {"task_id": task_id, "run_id": run["run_id"], "stage": run["stage"],
                       "role": run["role"], "invitation_nonce": run["invitation_nonce"],
                       "actor_id": inv["actor_id"], "platform_session_id": inv["platform_session_id"],
                       "invitation_sha256": _sha(invitation_bytes), "raw_capture_sha256": _sha(capture_raw)}
            event_id = str(uuid.uuid4())
            endpoint = descriptor["entrypoint"]
            receipt = {"receipt_format_version": "1", "api_version": SCHEMA_API_VERSION,
                "producer": "CONTROLLER", "context_kind": "STAGE",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "endpoint": {"entrypoint_path": endpoint["path"], "entrypoint_sha256": endpoint["sha256"],
                             "module_path": endpoint["module_path"], "module_sha256": endpoint["module_sha256"],
                             "invocation_kind": invocation_kind,
                             "argv": argv or [], "api_selector": schema_selector},
                "validation": {"purpose": purpose, "verdict": verdict, "error": error},
                "pins": {"release_version": run["release_version"], "release_sha256": run["release_sha256"],
                    "source_sha256": run["source_sha256"], "contract_sha256": run["contract_sha256"],
                    "plan_sha256": run["plan_sha256"], "plan_contract_sha256": run.get("plan_contract_sha256"),
                    "handoff_sha256": run["handoff_sha256"], "resource_root": run["resource_root"],
                    "resource_inventory_sha256": descriptor["resource_inventory_sha256"],
                    "schema_graph_sha256": descriptor["schema_graph_sha256"],
                    "package_content_sha256": descriptor["package_content_sha256"],
                    "publication": publication},
                "input": {"schema_selector": schema_selector, "path": relative, "bytes": len(raw),
                          "raw_sha256": _sha(raw), "canonical_sha256": None},
                "assurance": {"retrieval_policy": descriptor["retrieval_policy"],
                              "os_enforcement": "UNKNOWN", "io_observation": None},
                "registration": {"journal_path": "events.jsonl", "event_id": event_id},
                "context": context}
            receipt_raw = json.dumps(receipt, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            bundle.validate(SCHEMA_VALIDATION_SELECTOR, receipt_raw)
            digest = _sha(receipt_raw)
            receipt_rel = f"runs/{run['run_id']}/schema-validations/{digest}.json"
            _write_immutable_bytes(directory / receipt_rel, receipt_raw)
            Journal(directory / "events.jsonl").append("SCHEMA_VALIDATION_RECORDED", {
                "task_id": task_id, "context_kind": "STAGE", "run_id": run["run_id"],
                "purpose": purpose, "schema_selector": schema_selector, "input_path": relative,
                "input_raw_sha256": _sha(raw), "receipt_path": receipt_rel,
                "receipt_bytes": len(receipt_raw), "receipt_sha256": digest}, event_id=event_id)
            return {"receipt_path": receipt_rel, "receipt_sha256": digest, "event_id": event_id,
                    "verdict": verdict, "category": error.get("category") if error else None,
                    "location": error.get("location") if error else None,
                    "reason": error.get("reason") if error else None,
                    "input_path": relative, "input_bytes": len(raw),
                    "resource_inventory_sha256": descriptor["resource_inventory_sha256"],
                    "schema_graph_sha256": descriptor["schema_graph_sha256"],
                    "package_content_sha256": descriptor["package_content_sha256"],
                    "entrypoint": endpoint, "input_raw_sha256": validated.get("input_raw_sha256", _sha(raw))}

    def register_issue_schema_validation(self, task_id: str, *, issue_id: str, token: str,
                                         purpose: str, schema_selector: str, input_path: Path,
                                         invocation_kind: str = "CLI",
                                         argv: list[str] | None = None) -> dict:
        """Validate a high-review input against its originating run and invocation."""
        from .escalation import IssueLedger
        from .schema_validation import SchemaValidationFailure
        if invocation_kind not in {"CLI", "API"}:
            raise ControllerError("unsupported schema validation invocation kind")
        if purpose not in {"CONTRACT", "ANALYSIS"}:
            raise ControllerError("issue schema validation purpose is not in the frozen issue matrix")
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            ledger = IssueLedger(self.state_root / "issues")
            item = ledger.status(issue_id)
            if task_id not in item.get("tasks", {}) or item.get("state") != "REVIEW_INVOKED":
                raise ControllerError("issue schema validation requires its actual invoked reviewer")
            packet = item.get("packet", {})
            invocation = item.get("invocation", {})
            if packet.get("task_id") != task_id or not item.get("token") or item["token"] != token:
                raise ControllerError("issue dispatch token or task binding mismatch")
            run_id = packet.get("run_id")
            root, run = self._run(directory, state, run_id)
            if run.get("task_id") != task_id or packet.get("source_sha256") != run.get("source_sha256"):
                raise ControllerError("issue does not bind to the frozen originating run")
            effective_contract = run.get("contract_sha256") or run.get("plan_contract_sha256")
            if (not effective_contract or packet.get("contract_sha256") != effective_contract or
                task_id not in item.get("tasks", {}) or item["tasks"][task_id] != effective_contract):
                raise ControllerError("issue contract differs from the originating run")
            bundle = self._schema_bundle_for_run(run)
            descriptor = run["offline_schema_validation"]
            if purpose == "CONTRACT":
                matrix = next((entry for entry in descriptor["required_validations"]
                               if entry.get("purpose") == "CONTRACT"), None)
                if not matrix or schema_selector != matrix["schema_selector"]:
                    raise ControllerError("issue CONTRACT selector differs from originating run matrix")
                expected_rel = f"runs/{run_id}/origin-contract.json"
            else:
                if schema_selector != ISSUE_SCHEMA_VALIDATIONS["ANALYSIS"][0]:
                    raise ControllerError("issue ANALYSIS selector differs from the frozen issue matrix")
                expected_rel = None
            path = Path(input_path)
            if not path.is_absolute():
                path = directory / path
            raw = _read_regular(path, directory)
            try:
                relative = safe_relative_path(path.absolute().relative_to(directory.absolute()).as_posix())
            except ValueError as exc:
                raise ControllerError("issue schema input must be below its task evidence root") from exc
            if purpose == "CONTRACT" and relative != expected_rel:
                raise ControllerError("issue CONTRACT input must be the immutable originating-run contract")
            if purpose == "ANALYSIS":
                if relative.startswith("runs/") and relative.split("/")[1] != run_id:
                    raise ControllerError("issue ANALYSIS input must remain under its originating run")
            invocation_path = safe_relative_path(invocation.get("raw_path", ""))
            invocation_raw = _read_regular(directory / invocation_path, directory)
            if not invocation_raw or _sha(invocation_raw) != invocation.get("raw_sha256"):
                raise ControllerError("actual high-review invocation capture is missing or changed")
            try:
                capture = json.loads(invocation_raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ControllerError("actual high-review invocation capture is not structured JSON") from exc
            if (capture.get("capture_kind") != "INVITATION" or capture.get("issue_id") != issue_id or
                capture.get("token") != token or capture.get("agent_id") != invocation.get("agent_id") or
                capture.get("platform_session_id") != invocation.get("platform_session_id")):
                raise ControllerError("high-review invocation bytes do not identify the selected reviewer")
            try:
                parsed = json.loads(raw.decode("utf-8"))
                validated = bundle.validate(schema_selector, raw)
                verdict, error = "VALID", None
                if purpose == "ANALYSIS":
                    from .escalation import EscalationError, validate_high_review_analysis
                    try:
                        validate_high_review_analysis(parsed, effective_contract)
                    except EscalationError as exc:
                        verdict = "INVALID"
                        error = {"category": "SEMANTIC", "location": "<analysis>", "reason": str(exc)[:512]}
            except SchemaValidationFailure as exc:
                parsed = None
                verdict = "INVALID" if exc.category in {"INPUT", "INSTANCE"} else "BLOCKED"
                error = {"category": exc.category, "location": exc.location, "reason": exc.reason[:512]}
                validated = {"input_raw_sha256": _sha(raw)}
            except (ValueError, UnicodeDecodeError) as exc:
                parsed = None
                verdict = "INVALID"
                error = {"category": "INPUT", "location": "<root>", "reason": "input is not UTF-8 JSON"}
                validated = {"input_raw_sha256": _sha(raw)}
            canonical = _canonical_sha(parsed) if purpose == "ANALYSIS" and parsed is not None else None
            origin_contract_raw = _read_regular(root / "origin-contract.json", directory)
            if purpose == "CONTRACT" and (raw != origin_contract_raw or _sha(raw) != effective_contract):
                raise ControllerError("issue CONTRACT bytes differ from preserved originating-run pins")
            context = {"task_id": task_id, "originating_run_id": run_id, "issue_id": issue_id,
                       "dispatch_token": token, "reviewer_actor_id": invocation["agent_id"],
                       "platform_session_id": invocation["platform_session_id"],
                       "invocation_sha256": _canonical_sha(invocation),
                       "raw_transport_sha256": _sha(invocation_raw),
                       "packet_sha256": _canonical_sha(packet)}
            event_id = str(uuid.uuid4())
            endpoint = descriptor["entrypoint"]
            receipt = {"receipt_format_version": "1", "api_version": SCHEMA_API_VERSION,
                "producer": "CONTROLLER", "context_kind": "ISSUE",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "endpoint": {"entrypoint_path": endpoint["path"], "entrypoint_sha256": endpoint["sha256"],
                    "module_path": endpoint["module_path"], "module_sha256": endpoint["module_sha256"],
                    "invocation_kind": invocation_kind, "argv": argv or [], "api_selector": schema_selector},
                "validation": {"purpose": purpose, "verdict": verdict, "error": error},
                "pins": {"release_version": run["release_version"], "release_sha256": run["release_sha256"],
                    "source_sha256": run["source_sha256"], "contract_sha256": run.get("contract_sha256"),
                    "plan_sha256": run.get("plan_sha256"), "plan_contract_sha256": run.get("plan_contract_sha256"),
                    "handoff_sha256": run.get("handoff_sha256"), "resource_root": run["resource_root"],
                    "resource_inventory_sha256": descriptor["resource_inventory_sha256"],
                    "schema_graph_sha256": descriptor["schema_graph_sha256"],
                    "package_content_sha256": descriptor["package_content_sha256"], "publication": None},
                "input": {"schema_selector": schema_selector, "path": relative, "bytes": len(raw),
                    "raw_sha256": _sha(raw), "canonical_sha256": canonical},
                "assurance": {"retrieval_policy": descriptor["retrieval_policy"],
                    "os_enforcement": "UNKNOWN", "io_observation": None},
                "registration": {"journal_path": "events.jsonl", "event_id": event_id},
                "context": context}
            receipt_raw = json.dumps(receipt, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            bundle.validate(SCHEMA_VALIDATION_SELECTOR, receipt_raw)
            digest = _sha(receipt_raw)
            receipt_rel = f"runs/{run_id}/schema-validations/issues/{issue_id}/{digest}.json"
            _write_immutable_bytes(directory / receipt_rel, receipt_raw)
            Journal(directory / "events.jsonl").append("SCHEMA_VALIDATION_RECORDED", {
                "task_id": task_id, "context_kind": "ISSUE", "run_id": run_id, "issue_id": issue_id,
                "purpose": purpose, "schema_selector": schema_selector, "input_path": relative,
                "input_raw_sha256": _sha(raw), "receipt_path": receipt_rel,
                "receipt_bytes": len(receipt_raw), "receipt_sha256": digest}, event_id=event_id)
            return {"verdict": verdict, "category": error.get("category") if error else None,
                    "location": error.get("location") if error else None,
                    "reason": error.get("reason") if error else None, "schema_selector": schema_selector,
                    "input_path": relative, "input_bytes": len(raw), "input_raw_sha256": _sha(raw),
                    "resource_inventory_sha256": descriptor["resource_inventory_sha256"],
                    "schema_graph_sha256": descriptor["schema_graph_sha256"],
                    "package_content_sha256": descriptor["package_content_sha256"],
                    "entrypoint": endpoint, "receipt_path": receipt_rel,
                    "receipt_sha256": digest, "event_id": event_id}

    def _registered_issue_receipts(self, directory: Path, state: dict, issue_id: str,
                                   analysis: dict, *, analysis_path: str | None = None,
                                   analysis_raw: bytes | None = None,
                                   expected_refs: list[dict] | None = None) -> dict[str, dict]:
        """Select exact journal-bound origin CONTRACT and returned ANALYSIS receipts."""
        from .escalation import IssueLedger
        from .schema_validation import SchemaValidationFailure
        ledger = IssueLedger(self.state_root / "issues")
        item = ledger.status(issue_id)
        if state["task_id"] not in item.get("tasks", {}) or item.get("state") != "REVIEW_INVOKED":
            # Closure rechecks happen after REVIEW_INVOKED. The durable ledger keeps
            # the invocation and packet, so later states remain valid authorities.
            if not (expected_refs and item.get("invocation") and item.get("analysis") == analysis):
                raise ControllerError("issue receipts do not belong to an invoked high-review session")
        packet = item["packet"]
        run_id = packet["run_id"]
        root, run = self._run(directory, state, run_id)
        bundle = self._schema_bundle_for_run(run)
        descriptor = run["offline_schema_validation"]
        contract_matrix = next((entry for entry in descriptor["required_validations"]
                                if entry.get("purpose") == "CONTRACT"), None)
        if not contract_matrix:
            raise ControllerError("originating run has no frozen CONTRACT selector")
        inv = item["invocation"]
        context = {"task_id": state["task_id"], "originating_run_id": run_id, "issue_id": issue_id,
                   "dispatch_token": item["token"], "reviewer_actor_id": inv["agent_id"],
                   "platform_session_id": inv["platform_session_id"],
                   "invocation_sha256": _canonical_sha(inv)}
        raw_transport = _read_regular(directory / safe_relative_path(inv["raw_path"]), directory)
        if not raw_transport or _sha(raw_transport) != inv["raw_sha256"]:
            raise ControllerError("high-review invocation transport changed")
        context["raw_transport_sha256"] = _sha(raw_transport)
        context["packet_sha256"] = _canonical_sha(packet)
        accepted = {"CONTRACT": [], "ANALYSIS": []}
        expected_by_purpose = {ref.get("purpose"): ref for ref in (expected_refs or [])}
        if expected_refs is not None and (len(expected_refs) != 2 or
                set(expected_by_purpose) != {"CONTRACT", "ANALYSIS"}):
            raise ControllerError("consumed issue receipt references differ from the frozen purpose matrix")
        contract_path = f"runs/{run_id}/origin-contract.json"
        exact_analysis_sha = _sha(analysis_raw) if analysis_raw is not None else None
        records = Journal(directory / "events.jsonl").read()
        for record in records:
            facts = record.get("facts", {})
            if record.get("event_type") != "SCHEMA_VALIDATION_RECORDED":
                continue
            purpose_hint = facts.get("purpose")
            if expected_refs is not None:
                expected = expected_by_purpose.get(purpose_hint)
                if not expected or record.get("event_id") != expected.get("event_id"):
                    continue
                if (facts.get("context_kind") != "ISSUE" or facts.get("issue_id") != issue_id or
                    facts.get("receipt_path") != expected.get("path") or
                    facts.get("receipt_sha256") != expected.get("sha256")):
                    raise ControllerError("consumed issue receipt journal reference changed")
            else:
                if facts.get("context_kind") != "ISSUE" or facts.get("issue_id") != issue_id:
                    continue
                # Stale unconsumed receipts for an earlier input are diagnostic
                # history. They cannot poison a later exact revalidation.
                if purpose_hint == "CONTRACT":
                    if (facts.get("schema_selector") != contract_matrix["schema_selector"] or
                        facts.get("input_path") != contract_path):
                        continue
                elif purpose_hint == "ANALYSIS":
                    if facts.get("schema_selector") != ISSUE_SCHEMA_VALIDATIONS["ANALYSIS"][0]:
                        continue
                    if analysis_path is not None and facts.get("input_path") != analysis_path:
                        continue
                    if exact_analysis_sha is not None and facts.get("input_raw_sha256") != exact_analysis_sha:
                        continue
                else:
                    continue
            receipt_rel = safe_relative_path(facts.get("receipt_path", ""))
            receipt_raw = _read_regular(directory / receipt_rel, directory)
            if len(receipt_raw) != facts.get("receipt_bytes") or _sha(receipt_raw) != facts.get("receipt_sha256"):
                raise ControllerError("registered issue schema receipt bytes changed")
            try:
                receipt = json.loads(receipt_raw)
                bundle.validate(SCHEMA_VALIDATION_SELECTOR, receipt_raw)
            except (ValueError, SchemaValidationFailure) as exc:
                raise ControllerError("registered issue schema receipt is invalid") from exc
            registration = receipt["registration"]
            if registration.get("event_id") != record["event_id"] or registration.get("journal_path") != "events.jsonl":
                raise ControllerError("issue receipt journal identity mismatch")
            if receipt_rel != f"runs/{run_id}/schema-validations/issues/{issue_id}/{facts['receipt_sha256']}.json":
                raise ControllerError("issue receipt is outside its controller-owned storage path")
            if (facts.get("run_id") != run_id or facts.get("purpose") != receipt["validation"]["purpose"] or
                facts.get("schema_selector") != receipt["input"]["schema_selector"] or
                facts.get("input_path") != receipt["input"]["path"] or
                facts.get("input_raw_sha256") != receipt["input"]["raw_sha256"]):
                raise ControllerError("issue receipt journal binding mismatch")
            purpose = receipt["validation"]["purpose"]
            if purpose not in accepted or receipt["context_kind"] != "ISSUE" or receipt["validation"]["verdict"] != "VALID":
                continue
            if (receipt["endpoint"]["entrypoint_path"] != descriptor["entrypoint"]["path"] or
                receipt["endpoint"]["entrypoint_sha256"] != descriptor["entrypoint"]["sha256"] or
                receipt["endpoint"]["module_path"] != descriptor["entrypoint"]["module_path"] or
                receipt["endpoint"]["module_sha256"] != descriptor["entrypoint"]["module_sha256"]):
                raise ControllerError("issue receipt endpoint differs from immutable originating run")
            if any(receipt["context"].get(key) != value for key, value in context.items()):
                raise ControllerError("issue receipt context differs from the actual reviewer invocation")
            pins = receipt["pins"]
            expected_pins = {"release_version": run["release_version"], "release_sha256": run["release_sha256"],
                "source_sha256": run["source_sha256"], "contract_sha256": run.get("contract_sha256"),
                "plan_sha256": run.get("plan_sha256"), "plan_contract_sha256": run.get("plan_contract_sha256"),
                "handoff_sha256": run.get("handoff_sha256"), "resource_root": run["resource_root"],
                "resource_inventory_sha256": descriptor["resource_inventory_sha256"],
                "schema_graph_sha256": descriptor["schema_graph_sha256"],
                "package_content_sha256": descriptor["package_content_sha256"]}
            if any(pins.get(key) != value for key, value in expected_pins.items()):
                raise ControllerError("issue receipt pins differ from immutable originating run")
            if purpose == "CONTRACT":
                if (receipt["input"]["schema_selector"] != contract_matrix["schema_selector"] or
                    receipt["input"]["path"] != contract_path or
                    receipt["input"]["canonical_sha256"] is not None):
                    raise ControllerError("issue CONTRACT receipt does not select the originating contract")
            else:
                if receipt["input"]["schema_selector"] != ISSUE_SCHEMA_VALIDATIONS["ANALYSIS"][0]:
                    raise ControllerError("issue ANALYSIS receipt selector mismatch")
                if analysis_path is not None and receipt["input"]["path"] != analysis_path:
                    continue
                if analysis_raw is not None and (receipt["input"]["bytes"] != len(analysis_raw) or
                    receipt["input"]["raw_sha256"] != _sha(analysis_raw)):
                    continue
            if expected_refs is not None:
                expected = next((ref for ref in expected_refs if ref.get("purpose") == purpose), None)
                if not expected or expected.get("path") != receipt_rel or expected.get("sha256") != facts["receipt_sha256"] or expected.get("event_id") != record["event_id"]:
                    continue
            raw = _read_regular(directory / safe_relative_path(receipt["input"]["path"]), directory)
            if len(raw) != receipt["input"]["bytes"] or _sha(raw) != receipt["input"]["raw_sha256"]:
                raise ControllerError(f"registered issue {purpose} input bytes changed")
            if purpose == "CONTRACT":
                expected_contract = _read_regular(root / "origin-contract.json", directory)
                effective = run.get("contract_sha256") or run.get("plan_contract_sha256")
                if raw != expected_contract or _sha(raw) != effective:
                    raise ControllerError("registered issue CONTRACT no longer matches preserved origin bytes")
            else:
                try:
                    candidate = json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError) as exc:
                    raise ControllerError("registered issue ANALYSIS is no longer JSON") from exc
                if candidate != analysis or receipt["input"]["canonical_sha256"] != _canonical_sha(candidate):
                    continue
            accepted[purpose].append({"path": receipt_rel, "sha256": facts["receipt_sha256"],
                "event_id": record["event_id"], "receipt": receipt, "raw": raw})
        selected = {}
        for purpose in ("CONTRACT", "ANALYSIS"):
            if expected_refs is not None:
                ref = next((value for value in expected_refs if value.get("purpose") == purpose), None)
                accepted[purpose] = [candidate for candidate in accepted[purpose]
                    if ref and candidate["path"] == ref.get("path") and candidate["sha256"] == ref.get("sha256") and candidate["event_id"] == ref.get("event_id")]
                if len(accepted[purpose]) != 1:
                    raise ControllerError(f"missing or changed consumed issue {purpose} schema receipt")
                selected[purpose] = accepted[purpose][0]
            else:
                if not accepted[purpose]:
                    raise ControllerError(f"missing pre-existing issue {purpose} schema receipt")
                # Journal order is the controller's registration order. A
                # later exact unconsumed receipt supersedes earlier repeats.
                selected[purpose] = accepted[purpose][-1]
        return selected

    def _verify_issue_receipts(self, directory: Path, state: dict, refs: list[dict]) -> None:
        from .escalation import IssueLedger
        by_issue: dict[str, list[dict]] = {}
        for ref in refs:
            by_issue.setdefault(ref["issue_id"], []).append(ref)
        for issue_id, issue_refs in by_issue.items():
            item = IssueLedger(self.state_root / "issues").status(issue_id)
            analysis = item.get("analysis")
            if not isinstance(analysis, dict):
                raise ControllerError("accepted issue schema receipts have no durable returned analysis")
            expected = [{key: ref[key] for key in ("purpose", "path", "sha256", "event_id")} for ref in issue_refs]
            self._registered_issue_receipts(directory, state, issue_id, analysis,
                expected_refs=expected)

    def _registered_stage_receipts(self, directory: Path, state: dict, run: dict,
                                   invitation_bytes: bytes | None = None,
                                   expected_refs: list[dict] | None = None) -> dict[str, dict]:
        """Recheck journal-bound receipts for one allocated native role."""
        from .schema_validation import SchemaValidationFailure
        root, _ = self._run(directory, state, run["run_id"])
        bundle = self._schema_bundle_for_run(run)
        descriptor = run["offline_schema_validation"]
        expected_by_purpose = {item["purpose"]: item for item in (expected_refs or [])}
        required_purposes = {item["purpose"] for item in descriptor["required_validations"]}
        if expected_refs is not None and (len(expected_refs) != len(required_purposes) or
                                          set(expected_by_purpose) != required_purposes):
            raise ControllerError("consumed schema receipt references differ from the frozen purpose matrix")
        journal = Journal(directory / "events.jsonl")
        records = journal.read()
        accepted: dict[str, list[dict]] = {item["purpose"]: []
                                           for item in descriptor["required_validations"]}
        for record in records:
            facts = record.get("facts", {})
            if record.get("event_type") != "SCHEMA_VALIDATION_RECORDED" or facts.get("run_id") != run["run_id"]:
                continue
            receipt_rel = safe_relative_path(facts.get("receipt_path", ""))
            receipt_raw = _read_regular(directory / receipt_rel, directory)
            if len(receipt_raw) != facts.get("receipt_bytes") or _sha(receipt_raw) != facts.get("receipt_sha256"):
                raise ControllerError("registered schema receipt bytes changed")
            try:
                receipt = json.loads(receipt_raw)
                bundle.validate(SCHEMA_VALIDATION_SELECTOR, receipt_raw)
            except (ValueError, SchemaValidationFailure) as exc:
                raise ControllerError("registered schema receipt is invalid") from exc
            registration = receipt.get("registration", {})
            if registration.get("event_id") != record["event_id"] or registration.get("journal_path") != "events.jsonl":
                raise ControllerError("schema receipt journal identity mismatch")
            if (facts.get("purpose") != receipt["validation"]["purpose"] or
                facts.get("schema_selector") != receipt["input"]["schema_selector"] or
                facts.get("input_path") != receipt["input"]["path"] or
                facts.get("input_raw_sha256") != receipt["input"]["raw_sha256"]):
                raise ControllerError("schema receipt journal binding mismatch")
            if receipt["context_kind"] != "STAGE" or receipt["validation"]["verdict"] != "VALID":
                continue
            if receipt["endpoint"]["entrypoint_path"] != descriptor["entrypoint"]["path"] or receipt["endpoint"]["entrypoint_sha256"] != descriptor["entrypoint"]["sha256"] or receipt["endpoint"]["module_path"] != descriptor["entrypoint"]["module_path"] or receipt["endpoint"]["module_sha256"] != descriptor["entrypoint"]["module_sha256"]:
                raise ControllerError("schema receipt endpoint differs from immutable run descriptor")
            context = receipt["context"]
            for key, expected in (("task_id", state["task_id"]), ("run_id", run["run_id"]),
                                  ("stage", run["stage"]), ("role", run["role"]),
                                  ("invitation_nonce", run["invitation_nonce"])):
                if context.get(key) != expected:
                    raise ControllerError("schema receipt belongs to a different allocated role")
            if invitation_bytes is not None:
                inv, capture_raw = self._verified_invitation(directory, run, invitation_bytes)
                expected_context = {"actor_id": inv["actor_id"], "platform_session_id": inv["platform_session_id"],
                                    "invitation_sha256": _sha(invitation_bytes),
                                    "raw_capture_sha256": _sha(capture_raw)}
                if any(context.get(key) != value for key, value in expected_context.items()):
                    raise ControllerError("schema receipt native invitation identity changed")
            pins = receipt["pins"]
            expected_pins = {"release_version": run["release_version"], "release_sha256": run["release_sha256"],
                "source_sha256": run["source_sha256"], "contract_sha256": run["contract_sha256"],
                "plan_sha256": run["plan_sha256"], "plan_contract_sha256": run.get("plan_contract_sha256"),
                "handoff_sha256": run["handoff_sha256"], "resource_root": run["resource_root"],
                "resource_inventory_sha256": descriptor["resource_inventory_sha256"],
                "schema_graph_sha256": descriptor["schema_graph_sha256"],
                "package_content_sha256": descriptor["package_content_sha256"]}
            if any(pins.get(key) != value for key, value in expected_pins.items()):
                raise ControllerError("schema receipt frozen pins differ from allocated run")
            if run["stage"] == "PLAN" and receipt["validation"]["purpose"] == "CONTRACT":
                publication = pins.get("publication")
                input_rel = receipt["input"]["path"]
                input_path = directory / safe_relative_path(input_rel)
                publication_path = input_path.parent / "publication.json"
                publication_raw = _read_regular(publication_path, directory)
                publication_value = json.loads(publication_raw)
                plan_raw = _read_regular(input_path.parent / "plan.md", directory)
                origin_contract = _read_regular(input_path, directory)
                if (not isinstance(publication, dict) or
                    publication.get("plan_sha256") != _sha(plan_raw) or
                    publication.get("plan_contract_sha256") != _sha(origin_contract) or
                    publication.get("publication_sha256") != _sha(publication_raw) or
                    publication_value.get("plan_sha256") != _sha(plan_raw) or
                    publication_value.get("plan_contract_sha256") != _sha(origin_contract) or
                    publication_value.get("contract_path") != input_rel):
                    raise ControllerError("PLAN schema receipt publication pins differ from preserved controller bytes")
            purpose = receipt["validation"]["purpose"]
            if purpose in accepted:
                accepted[purpose].append({"path": receipt_rel, "sha256": facts["receipt_sha256"],
                                          "event_id": record["event_id"], "receipt": receipt})
        selected = {}
        for item in descriptor["required_validations"]:
            purpose = item["purpose"]
            candidates = [value for value in accepted[purpose]
                          if value["receipt"]["input"]["schema_selector"] == item["schema_selector"]]
            if purpose == "CONTRACT":
                if run["stage"] == "PLAN" and expected_refs is None:
                    current = json.loads(_read_regular(directory / "plan-publication.json", directory))
                    candidates = [value for value in candidates
                                  if value["receipt"]["input"]["path"] == current.get("contract_path") and
                                     current.get("plan_sha256") == state.get("plan_sha256") and
                                     current.get("plan_contract_sha256") == state.get("plan_contract_sha256")]
                elif run["stage"] != "PLAN":
                    expected_path = f"runs/{run['run_id']}/origin-contract.json"
                    candidates = [value for value in candidates if value["receipt"]["input"]["path"] == expected_path]
            if purpose == "IMPLEMENTATION_RESULT":
                own_consumption_path = root / "consumption.json"
                own_consumption = json.loads(_read_regular(own_consumption_path, directory)) if own_consumption_path.exists() else {}
                implementation_run_id = own_consumption.get("accepted_implementation_run_id") or state.get("last_valid_run_id")
                if implementation_run_id:
                    impl_root, _ = self._run(directory, state, implementation_run_id)
                    consumed = json.loads(_read_regular(impl_root / "consumption.json", directory))
                    expected_path = f"runs/{implementation_run_id}/submissions/{consumed['admission_sha256']}/candidate-result.json"
                    candidates = [value for value in candidates
                                  if value["receipt"]["input"]["path"] == expected_path]
            if purpose == "RESULT":
                # RESULT is selected at admission by exact result bytes below.
                pass
            if expected_refs is not None:
                ref = expected_by_purpose.get(purpose)
                if not ref:
                    raise ControllerError("consumed schema receipt reference is missing a required purpose")
                candidates = [value for value in candidates if value["path"] == ref.get("path") and
                              value["sha256"] == ref.get("sha256") and value["event_id"] == ref.get("event_id")]
            if purpose != "RESULT" and not candidates:
                raise ControllerError(f"missing pre-existing {purpose} schema receipt")
            if purpose == "RESULT" and not candidates:
                raise ControllerError("missing pre-existing RESULT schema receipt")
            if purpose == "RESULT":
                selected[purpose] = candidates
            else:
                chosen = candidates[-1]
                raw = _read_regular(directory / safe_relative_path(chosen["receipt"]["input"]["path"]), directory)
                identity = chosen["receipt"]["input"]
                if len(raw) != identity["bytes"] or _sha(raw) != identity["raw_sha256"]:
                    raise ControllerError(f"pre-existing {purpose} schema receipt input changed")
                if purpose == "CONTRACT":
                    if run["stage"] == "PLAN":
                        input_path = directory / safe_relative_path(identity["path"])
                        publication_raw = _read_regular(input_path.parent / "publication.json", directory)
                        publication = json.loads(publication_raw)
                        plan_raw = _read_regular(input_path.parent / "plan.md", directory)
                        receipt_publication = chosen["receipt"]["pins"].get("publication")
                        if (publication.get("contract_path") != identity["path"] or
                            publication.get("plan_sha256") != _sha(plan_raw) or
                            publication.get("plan_contract_sha256") != _sha(raw) or
                            not isinstance(receipt_publication, dict) or
                            receipt_publication.get("plan_sha256") != _sha(plan_raw) or
                            receipt_publication.get("plan_contract_sha256") != _sha(raw) or
                            receipt_publication.get("publication_sha256") != _sha(publication_raw)):
                            raise ControllerError("registered PLAN contract receipt publication bytes changed")
                    else:
                        expected_contract = _read_regular(root / "origin-contract.json", directory)
                        effective_contract = run.get("contract_sha256") or run.get("plan_contract_sha256")
                        if raw != expected_contract or not effective_contract or _sha(raw) != effective_contract:
                            raise ControllerError("registered CONTRACT receipt no longer matches preserved run-origin pin")
                chosen["raw"] = raw
                selected[purpose] = [chosen]
        return selected

    def _stage_receipts_for_admission(self, directory: Path, state: dict, run: dict,
                                      invitation_bytes: bytes, result_bytes: bytes,
                                      expected_refs: list[dict] | None = None) -> list[dict]:
        receipts = self._registered_stage_receipts(directory, state, run, invitation_bytes, expected_refs)
        result_candidates = []
        for item in receipts["RESULT"]:
            identity = item["receipt"]["input"]
            if identity["raw_sha256"] != _sha(result_bytes) or identity["bytes"] != len(result_bytes):
                continue
            try:
                candidate_raw = _read_regular(directory / safe_relative_path(identity["path"]), directory)
            except (OSError, ControllerError):
                continue
            if candidate_raw == result_bytes:
                item["raw"] = candidate_raw
                result_candidates.append(item)
        if expected_refs is not None:
            expected_result = next((item for item in expected_refs if item.get("purpose") == "RESULT"), None)
            result_candidates = [item for item in result_candidates if expected_result and
                                 item["path"] == expected_result["path"] and
                                 item["sha256"] == expected_result["sha256"] and
                                 item["event_id"] == expected_result["event_id"]]
        if len(result_candidates) != 1:
            if not result_candidates:
                raise ControllerError("submitted result has no pre-existing exact RESULT receipt")
            # Repeated validation of identical bytes remains one semantic input;
            # consume the last controller-registered exact receipt.
        result_ref = result_candidates[-1]
        refs = []
        for purpose in sorted(receipts):
            values = [result_ref] if purpose == "RESULT" else receipts[purpose]
            if len(values) != 1:
                raise ControllerError(f"missing or ambiguous pre-existing {purpose} schema receipt")
            ref = {key: values[0][key] for key in ("path", "sha256", "event_id")}
            refs.append({"purpose": purpose, **ref})
        return refs

    @staticmethod
    def _publication_facts(directory: Path, run_id: str) -> dict:
        publications = [record["facts"] for record in Journal(directory / "events.jsonl").read()
                        if record.get("event_type") == "PLAN_PUBLISHED" and
                        record.get("facts", {}).get("run_id") == run_id]
        if not publications:
            raise ControllerError("Plan publication has no controller journal record")
        return publications[-1]

    @staticmethod
    def _published_plan_paths(directory: Path, plan_sha: str, contract_sha: str,
                              *, preferred_run_id: str | None = None) -> dict[str, str]:
        records = [record["facts"] for record in Journal(directory / "events.jsonl").read()
                   if record.get("event_type") == "PLAN_PUBLISHED"]
        matches = [facts for facts in records
                   if facts.get("plan_sha256") == plan_sha and
                      facts.get("plan_contract_sha256") == contract_sha and
                      (preferred_run_id is None or facts.get("run_id") == preferred_run_id)]
        if not matches:
            raise ControllerError("pinned Plan evidence has no exact controller publication")
        facts = matches[-1]
        run_id = facts.get("run_id")
        publication_dir = f"runs/{run_id}/publications/{plan_sha}_{contract_sha}"
        expected = {"plan_sha256": plan_sha, "plan_contract_sha256": contract_sha,
                    "plan_path": publication_dir + "/plan.md",
                    "contract_path": publication_dir + "/contract.json"}
        publication_raw = _read_regular(directory / (publication_dir + "/publication.json"), directory)
        try:
            publication = json.loads(publication_raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ControllerError("pinned Plan publication is malformed") from exc
        plan_raw = _read_regular(directory / expected["plan_path"], directory)
        contract_raw = _read_regular(directory / expected["contract_path"], directory)
        if (publication != expected or facts.get("plan_path") != expected["plan_path"] or
            facts.get("contract_path") != expected["contract_path"] or
            facts.get("publication_sha256") != _sha(publication_raw) or
            _sha(plan_raw) != plan_sha or _sha(contract_raw) != contract_sha):
            raise ControllerError("pinned Plan publication bytes differ from its controller record")
        return expected

    def _verify_current_plan_publication(self, directory: Path, state: dict) -> dict:
        publications = [record["facts"] for record in Journal(directory / "events.jsonl").read()
                        if record.get("event_type") == "PLAN_PUBLISHED"]
        if not publications:
            raise ControllerError("current Plan has no controller publication record")
        facts = publications[-1]
        run_id = facts.get("run_id")
        if not isinstance(run_id, str):
            raise ControllerError("current Plan publication run identity is malformed")
        _, publication_run = self._run(directory, state, run_id)
        if publication_run.get("stage") != "PLAN":
            raise ControllerError("current Plan publication was not produced by a Planner run")
        expected_directory = f"runs/{run_id}/publications/{facts.get('plan_sha256')}_{facts.get('plan_contract_sha256')}"
        expected = {"plan_sha256": facts.get("plan_sha256"),
                    "plan_contract_sha256": facts.get("plan_contract_sha256"),
                    "plan_path": expected_directory + "/plan.md",
                    "contract_path": expected_directory + "/contract.json"}
        current_raw = _read_regular(directory / "plan-publication.json", directory)
        publication_raw = _read_regular(directory / (expected_directory + "/publication.json"), directory)
        try:
            current = json.loads(current_raw)
            recorded = json.loads(publication_raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ControllerError("current Plan publication pointer is malformed") from exc
        if (facts.get("plan_sha256") != state.get("plan_sha256") or
            facts.get("plan_contract_sha256") != state.get("plan_contract_sha256") or
            current != expected or recorded != expected or current_raw != publication_raw or
            facts.get("publication_sha256") != _sha(publication_raw)):
            raise ControllerError("current Plan pointer differs from the latest controller publication")
        plan_raw = _read_regular(directory / expected["plan_path"], directory)
        contract_raw = _read_regular(directory / expected["contract_path"], directory)
        if (_sha(plan_raw) != state.get("plan_sha256") or
            _sha(contract_raw) != state.get("plan_contract_sha256") or
            _read_regular(directory / "plan.md", directory) != plan_raw or
            _read_regular(directory / "plan-contract.json", directory) != contract_raw):
            raise ControllerError("current canonical Plan files differ from the latest controller publication")
        return facts

    def _publication_alias_snapshots(self, directory: Path, run: dict, result: dict) -> list[dict]:
        aliases = {"plan.md": "plan", "plan-contract.json": "contract"}
        manifests = [manifest for manifest in result["evidence_manifests"]
                     if manifest.get("path") in aliases]
        snapshots = []
        if not manifests:
            return snapshots
        root = directory / "runs" / run["run_id"]
        if run["stage"] == "PLAN":
            plan_sha = result["plan_sha256"]
            contract_sha = result["plan_contract_sha256"]
            sources = self._published_plan_paths(directory, plan_sha, contract_sha,
                                                 preferred_run_id=run["run_id"])
            sources = {"plan": sources["plan_path"], "contract": sources["contract_path"]}
        elif run["stage"] == "PLAN_REVIEW":
            sources = {"plan": f"runs/{run['run_id']}/origin-plan.md",
                       "contract": f"runs/{run['run_id']}/origin-contract.json"}
            for kind, source in sources.items():
                raw = _read_regular(directory / source, directory)
                expected_sha = run.get("plan_sha256") if kind == "plan" else run.get("plan_contract_sha256")
                if not expected_sha or _sha(raw) != expected_sha:
                    raise ControllerError("Plan Review origin snapshot differs from its immutable run pins")
        else:
            sources = {"plan": f"runs/{run['run_id']}/origin-plan.md"}
            publication = self._published_plan_paths(directory, result["plan_sha256"],
                                                       result["plan_contract_sha256"])
            sources["contract"] = publication["contract_path"]
            plan_raw = _read_regular(directory / sources["plan"], directory)
            if not run.get("plan_sha256") or _sha(plan_raw) != run["plan_sha256"]:
                raise ControllerError("role origin Plan snapshot differs from its immutable run pin")
        for manifest in manifests:
            source = sources[aliases[manifest["path"]]]
            raw = _read_regular(directory / source, directory)
            if not raw or len(raw) != manifest["bytes"] or _sha(raw) != manifest["sha256"]:
                raise ControllerError("published evidence differs from its immutable origin snapshot")
            snapshots.append({"evidence_id": manifest["evidence_id"], "path": manifest["path"],
                "snapshot_path": source, "snapshot_bytes": len(raw), "snapshot_sha256": _sha(raw)})
        return snapshots

    def _evidence(self, directory: Path, run: dict, result: dict, *, state: dict | None = None,
                  evidence_alias_snapshots: list[dict] | None = None) -> set[str]:
        verified = set()
        aliases = {"plan.md", "plan-contract.json"}
        expected_snapshots = self._publication_alias_snapshots(directory, run, result)
        if evidence_alias_snapshots is not None and evidence_alias_snapshots != expected_snapshots:
            raise ControllerError("consumed publication evidence snapshot binding changed")
        snapshot_by_id = {item["evidence_id"]: item for item in expected_snapshots}
        current_aliases = {}
        for manifest in result["evidence_manifests"]:
            for key in ("task_id", "run_id", "stage", "role", "source_sha256"):
                if manifest[key] != run[key]:
                    raise ControllerError("evidence identity differs from run")
            if manifest["contract_sha256"] != run["contract_sha256"]:
                raise ControllerError("evidence contract binding mismatch")
            if manifest["evidence_id"] in verified:
                raise ControllerError("duplicate evidence ID")
            payload = None
            try:
                payload = _read_regular(directory / safe_relative_path(manifest["path"]), directory)
            except (OSError, ControllerError):
                if manifest["path"] not in aliases:
                    raise
            if payload is None or not payload or len(payload) != manifest["bytes"] or _sha(payload) != manifest["sha256"]:
                if manifest["path"] not in aliases or state is None or run["stage"] not in {"PLAN", "PLAN_REVIEW"}:
                    raise ControllerError("evidence bytes/hash mismatch")
                payload = None
                if manifest["path"] not in current_aliases:
                    try:
                        current_aliases[manifest["path"]] = _read_regular(directory / manifest["path"], directory)
                    except (OSError, ControllerError):
                        current_aliases[manifest["path"]] = None
                current = current_aliases[manifest["path"]]
                if current is not None and len(current) == manifest["bytes"] and _sha(current) == manifest["sha256"]:
                    payload = current
                else:
                    if state.get("plan_revisions", 0) <= 0:
                        raise ControllerError("evidence bytes/hash mismatch")
                    self._verify_current_plan_publication(directory, state)
                    pinned = snapshot_by_id.get(manifest["evidence_id"])
                    if (not pinned or pinned["path"] != manifest["path"] or
                        pinned["snapshot_bytes"] != manifest["bytes"] or
                        pinned["snapshot_sha256"] != manifest["sha256"]):
                        raise ControllerError("superseded publication evidence has no exact origin snapshot")
                    payload = _read_regular(directory / safe_relative_path(pinned["snapshot_path"]), directory)
            if not payload or len(payload) != manifest["bytes"] or _sha(payload) != manifest["sha256"]:
                raise ControllerError("evidence bytes/hash mismatch")
            verified.add(manifest["evidence_id"])
        if set(result["evidence_ids"]) != verified:
            raise ControllerError("evidence IDs differ from verified files")
        return verified

    def record_result(self, task_id: str, result_bytes: bytes, *, invitation_bytes: bytes,
                      completion_bytes: bytes, run_id: str | None = None, **untrusted) -> str:
        if untrusted:
            raise ControllerError("caller evidence sets and gate declarations are not authority")
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            root, run = self._run(directory, state, run_id)
            before_state_sha = _sha(validate_compact_state(state))
            accepted_implementation_run_id = state.get("last_valid_run_id") if run["stage"] == "ACCEPTANCE" else None
            consume = root / "consumption.json"
            admission_sha = _sha(result_bytes + invitation_bytes + completion_bytes)
            if consume.exists():
                prior = json.loads(_read_regular(consume, directory))
                if prior["admission_sha256"] != admission_sha:
                    raise ControllerError("run already consumed with different input")
                self._replay_state(state, prior)
                self._verify_consumed_run(directory, prior["state"], run["run_id"])
                self._verify_accepted(prior["state"])
                if prior["route"] == "DONE": self._verify_accepted_content(directory, prior["state"])
                # Recover only the exact pre-publication state, never an older run.
                if before_state_sha != _sha(validate_compact_state(prior["state"])):
                    _json_atomic(directory / "state.json", prior["state"])
                if prior["route"] == "DONE": self._closure(directory, prior["state"])
                return prior["route"]
            if state["phase"] == "STATE_RECONCILIATION_REQUIRED":
                raise ControllerError("rejected admission requires trusted reconciliation")
            if state["active_run_id"] != run["run_id"]:
                raise ControllerError("result is not the active allocated run")
            if run.get("operation_scope") in {"STAGE", "ISSUE_CONTINUATION"}:
                schema_receipt_refs = self._stage_receipts_for_admission(
                    directory, state, run, invitation_bytes, result_bytes)
            else:
                raise ControllerError("result admission requires a fixed schema receipt context")
            attempt = root / "submissions" / admission_sha
            attempt.mkdir(parents=True, exist_ok=True)
            for name, raw in (("candidate-result.json", result_bytes), ("invitation.json", invitation_bytes), ("completion.json", completion_bytes)):
                path = attempt / name
                if path.exists() and _read_regular(path, directory) != raw:
                    raise ControllerError("candidate input conflict")
                path.write_bytes(raw)
            try:
                result = _validate(result_bytes, "result.schema.json")
                for path, digest in run["validation_sources"].items():
                    if _sha(_read_regular(Path(path))) != digest:
                        raise ControllerError("controller validation source pin changed")
                inv, comp = self._provenance(directory, run, result_bytes, invitation_bytes, completion_bytes)
                if run["stage"] == "IMPLEMENT":
                    actors = state.setdefault("implementer_actor_ids", [])
                    if inv["actor_id"] not in actors: actors.append(inv["actor_id"])
                if run["stage"] == "PLAN":
                    actors = state.setdefault("planner_actor_ids", [])
                    if inv["actor_id"] not in actors: actors.append(inv["actor_id"])
                for key in ("task_id", "run_id", "stage", "role", "source_sha256"):
                    if result[key] != run[key]:
                        raise ControllerError("result identity differs from immutable run")
                for key in ("plan_sha256", "handoff_sha256", "plan_contract_sha256"):
                    expected = state[key] if run["stage"] in {"PLAN", "HANDOFF"} else run[key]
                    if result[key] != expected:
                        raise ControllerError("result Plan/Handoff pin mismatch")
                if run["stage"] == "PLAN_REVIEW" and inv["actor_id"] in state.get("planner_actor_ids", []):
                    raise ControllerError("Plan Review must be independent of Planner")
                if run["stage"] == "ACCEPTANCE" and inv["actor_id"] in state.get("implementer_actor_ids", []):
                    raise ControllerError("Acceptance must be independent of Implementer")
                analysis = result.get("analysis")
                if not isinstance(analysis, dict) or not all(isinstance(analysis.get(k), list) for k in ("facts", "inferences", "unknowns", "evidence")) or not isinstance(analysis.get("confidence"), str):
                    raise ControllerError("v4.6 role result lacks structured evidence and uncertainty fields")
                convergence = result["convergence"]
                if result["needs_human"] and result["candidate_fact"] == "PASS":
                    raise ControllerError("a role cannot mark a task complete while asking you to decide")
                verified = self._evidence(directory, run, result, state=state)
                evidence_alias_snapshots = self._publication_alias_snapshots(directory, run, result)
                Writers(self, directory, state, root, run).validate(result)
                pre = json.loads(_read_regular(root / "pre-snapshot.json", directory))
                if snapshot_digest(pre) != run["source_sha256"]:
                    raise ControllerError("frozen pre-snapshot digest mismatch")
                post = self._snapshot()
                _json_atomic(attempt / "post-snapshot.json", post, immutable=True)
                for key in ("repository", "worktree", "head", "branch", "index_sha256"):
                    if pre[key] != post[key]:
                        raise ControllerError("repository Git identity changed during role")
                allowed = run.get("continuation_permission", {}).get("allowed_paths", state["allowed_paths"]) if run["stage"] == "IMPLEMENT" else []
                violations = compare(pre, post, allowed)
                if violations:
                    raise ControllerError("role changed protected product paths: " + ", ".join(violations[:10]))
                if run["stage"] == "ACCEPTANCE": self._verify_accepted(state)
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
                    if run["stage"] == "PLAN" and not state["plan_sha256"]:
                        raise ControllerError("Planner did not publish a Plan")
                    if run["stage"] == "HANDOFF" and not state["handoff_sha256"]:
                        raise ControllerError("Compiler did not freeze Handoff")
            except (ContractError, ControllerError, WriterError, OSError, ValueError) as exc:
                _json_atomic(attempt / "validation.json", {"verdict": "INVALID", "reason": str(exc)}, immutable=True)
                state["phase"] = "STATE_RECONCILIATION_REQUIRED"; state["next_stage"] = None
                state["reconciliation_reason"] = str(exc)
                _json_atomic(directory / "state.json", state)
                Journal(directory / "events.jsonl").append("RESULT_REJECTED", {"run_id": run["run_id"], "reason": str(exc)})
                raise ControllerError(str(exc)) from exc
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
            if run["stage"] == "IMPLEMENT":
                state["convergence"] = result["convergence"]
            state["last_handoff_summary"] = result["handoff_summary"]
            if result["needs_human"]:
                state["human_decisions"] = result["human_decisions"]
            state["active_run_id"] = None; state["last_valid_run_id"] = run["run_id"]
            state["runtime_fact"] = {"outcome": comp["outcome"], "process_exit": None}
            state["candidate_fact"] = result["candidate_fact"]; state["validation_fact"] = "VALID"
            if (self.state_root / "issues").exists() and run["stage"] == "IMPLEMENT":
                from .escalation import IssueLedger
                permission = run.get("continuation_permission")
                evidence = None
                if permission:
                    matches = [m for m in result["evidence_manifests"] if m["observation"] == permission["success_criterion"]]
                    evidence = {"condition": permission["success_criterion"], "verified_files": [{k: m[k] for k in ("path", "bytes", "sha256")} for m in matches]}
                IssueLedger(self.state_root / "issues").finish_task_run(task_id, passed, run_id=run["run_id"], evidence=evidence)
                if self._pending(task_id):
                    state["phase"] = "BLOCKED"; state["next_stage"] = None
                    state["statuses"]["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
                    route = "WAIT_HUMAN"
            if run["stage"] == "IMPLEMENT" and not passed and result["candidate_fact"] in {"PARTIAL", "FAIL", "BLOCKED"} and not self._pending(task_id):
                from .escalation import IssueLedger
                packet = self._issue_packet(state, run, result)
                issue_id = IssueLedger(self.state_root / "issues").open(packet)
                state["active_issue_id"] = issue_id
                state["phase"] = "BLOCKED"; state["next_stage"] = None
                state["statuses"]["IMPLEMENTATION_STATUS"] = "ESCALATED"
                state["statuses"]["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
            if run["stage"] == "IMPLEMENT":
                self._write_progress(directory, state, route=route, result=result)
            _json_atomic(attempt / "validation.json", {"verdict": "VALID", "runtime": comp["outcome"], "route": route}, immutable=True)
            _json_atomic(root / "consumption.json", {"admission_sha256": admission_sha, "route": route,
                "before_state_sha256": before_state_sha,
                "schema_validation_receipts": schema_receipt_refs,
                "evidence_alias_snapshots": evidence_alias_snapshots,
                "accepted_implementation_run_id": accepted_implementation_run_id,
                "post_snapshot_sha256": _sha(_read_regular(attempt / "post-snapshot.json", directory)),
                "state": state}, immutable=True)
            _json_atomic(directory / "state.json", state)
            Journal(directory / "events.jsonl").append("RESULT_ACCEPTED", {"run_id": run["run_id"], "route": route})
            if route == "DONE": self._closure(directory, state)
            return route

    @staticmethod
    def content_sha256(value):
        # Parent may commit an independently accepted tree. Compare actual
        # product bytes/modes/paths rather than the changed Git bookkeeping.
        entries = [{k:e[k] for k in ("path", "kind", "mode", "bytes", "sha256") if k in e}
                   for e in value["entries"] if e.get("gating", True)]
        return _sha(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode())

    def record_parent_gate(self, task_id, receipt_bytes):
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            before_state_sha = _sha(validate_compact_state(state))
            receipt = _validate(receipt_bytes, "run.schema.json#post_check")
            digest = _sha(receipt_bytes)
            canonical = directory / "post-checks" / receipt["gate_id"] / "consumption.json"
            if canonical.exists():
                previous = json.loads(_read_regular(canonical, directory))
                if previous["receipt_sha256"] != digest:
                    raise ControllerError("post-check already consumed with different bytes")
                self._replay_state(state, previous)
                self._verify_parent_files(directory, receipt)
                self._verify_accepted(previous["state"])
                if previous["route"] in {"DONE", "DONE_WITH_WAIVER"}: self._verify_accepted_content(directory, previous["state"])
                if before_state_sha != _sha(validate_compact_state(previous["state"])):
                    _json_atomic(directory / "state.json", previous["state"])
                if previous["route"] in {"DONE", "DONE_WITH_WAIVER"}: self._closure(directory, previous["state"])
                return previous["route"]
            if self._pending(task_id): raise ControllerError("unresolved STOP prevents post-check closure")
            run_id = state.get("acceptance_run_id") or state.get("completion_run_id")
            if not run_id or state["statuses"]["INDEPENDENT_ACCEPTANCE_STATUS"] not in {"PASS", "NOT_REQUIRED"}:
                raise ControllerError("post-check needs a completed task and a resolved Acceptance policy")
            root, run = self._run(directory, state, run_id)
            gate = next((g for g in state["required_gates"] if g["gate_id"] == receipt["gate_id"]), None)
            if not gate or gate["owner"] not in {"PARENT", "HUMAN"} or gate["phase"] != "POST_CHECK":
                raise ControllerError("parent receipt gate is not frozen PARENT POST_CHECK")
            if gate["owner"] == "HUMAN" and receipt["verdict"] != "OBSERVED":
                raise ControllerError("human observation must remain OBSERVED; it cannot be promoted to PASS")
            if gate["owner"] == "PARENT" and receipt["verdict"] == "OBSERVED":
                raise ControllerError("OBSERVED is reserved for explicitly human-owned evidence")
            for key, expected in (("task_id", task_id), ("run_id", run["run_id"]),
                                  ("contract_sha256", state["contract_sha256"]), ("source_sha256", run["source_sha256"])):
                if receipt[key] != expected: raise ControllerError("parent receipt identity binding mismatch")
            current = self._snapshot()
            accepted = json.loads(_read_regular(root / "consumption.json", directory))
            post = json.loads(_read_regular(root / "submissions" / accepted["admission_sha256"] / "post-snapshot.json", directory))
            content = self.content_sha256(current)
            if content != self.content_sha256(post) or content != receipt["current_content_sha256"]:
                raise ControllerError("parent post-check changed accepted product content")
            raw = _read_regular(directory / safe_relative_path(receipt["raw_path"]), directory)
            if not raw or _sha(raw) != receipt["raw_sha256"]:
                raise ControllerError("actual parent observation missing or changed")
            for artifact in receipt["artifacts"]:
                payload = _read_regular(directory / safe_relative_path(artifact["path"]), directory)
                if len(payload) != artifact["bytes"] or _sha(payload) != artifact["sha256"]:
                    raise ControllerError("parent artifact bytes/hash mismatch")
            self._verify_accepted(state)
            if receipt["verdict"] == "PASS":
                # All originals are retained, and later closure rechecks them.
                state["accepted_gates"][gate["gate_id"]] = {"run_id":run["run_id"],"stage":"POST_CHECK",
                    "evidence_id":gate["gate_id"],"manifest":receipt["artifacts"][0],"artifacts":receipt["artifacts"] + [{"path":receipt["raw_path"],"bytes":len(raw),"sha256":receipt["raw_sha256"]}]}
            elif receipt["verdict"] == "OBSERVED":
                state.setdefault("human_observations", {})[gate["gate_id"]] = {
                    "run_id": run["run_id"], "receipt_sha256": digest,
                    "observation": receipt["observation"],
                    "raw_path": receipt["raw_path"], "raw_sha256": receipt["raw_sha256"],
                    "artifacts": receipt["artifacts"]}
            needed = {g["gate_id"] for g in state["required_gates"] if g["required"] and g["closure_gate"] != "NON_GATING"}
            covered = set(state["accepted_gates"]) | set(state.get("waived_gates", {}))
            complete = needed.issubset(covered)
            route = ("DONE_WITH_WAIVER" if state.get("waived_gates") else "DONE") if complete else "WAIT_EVIDENCE"
            if complete:
                state["phase"] = "DONE"; state["statuses"]["REQUIRED_VERIFICATION_STATUS"] = "WAIVED" if state.get("waived_gates") else "PASS"
                state["statuses"]["TASK_CLOSURE_STATUS"] = "DONE"
            elif receipt["verdict"] != "PASS":
                state["statuses"]["REQUIRED_VERIFICATION_STATUS"] = "INCOMPLETE" if receipt["verdict"] == "OBSERVED" else receipt["verdict"]
            # Keep the exact submitted bytes: the observation digest identifies
            # the user's receipt, not a re-serialized JSON representation.
            receipt_path = canonical.parent / "receipt.json"
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fd = os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o400)
            except FileExistsError:
                if _read_regular(receipt_path, directory) != receipt_bytes:
                    raise ControllerError("post-check receipt bytes conflict with existing evidence")
            else:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(receipt_bytes); stream.flush(); os.fsync(stream.fileno())
            _json_atomic(canonical, {"receipt_sha256":digest,"route":route,
                "before_state_sha256":before_state_sha,"state":state}, immutable=True)
            _json_atomic(directory / "state.json", state)
            if complete: self._closure(directory, state)
            return route

    def waive_gate(self, task_id: str, decision_bytes: bytes) -> str:
        """Record a user's decision separately from observations and verified PASS."""
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            decision = _validate(decision_bytes, "waiver.schema.json")
            if decision["task_id"] != task_id or decision["contract_sha256"] != state.get("contract_sha256"):
                raise ControllerError("waiver does not match this task's frozen Plan")
            if state.get("active_run_id") or state["statuses"]["IMPLEMENTATION_STATUS"] != "COMPLETE":
                raise ControllerError("a waiver can be recorded only after implementation is finished")
            if state["statuses"]["INDEPENDENT_ACCEPTANCE_STATUS"] not in {"PASS", "NOT_REQUIRED"}:
                raise ControllerError("a waiver cannot replace required independent Acceptance")
            gate = next((g for g in state.get("required_gates", []) if g["gate_id"] == decision["gate_id"]), None)
            if not gate or not gate["required"] or gate["closure_gate"] == "NON_GATING":
                raise ControllerError("only an unmet required closure gate can be waived")
            if decision["gate_id"] in state.get("accepted_gates", {}):
                raise ControllerError("a passed gate does not need a waiver")
            observation = state.get("human_observations", {}).get(decision["gate_id"])
            if observation and decision["observation_sha256"] != observation["receipt_sha256"]:
                raise ControllerError("waiver must cite the exact recorded human observation")
            if not observation and decision["observation_sha256"] is not None:
                raise ControllerError("waiver cites a human observation that is not recorded")
            digest = _sha(decision_bytes)
            relative = f"waivers/{digest}.json"
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and _read_regular(path, directory) != decision_bytes:
                raise ControllerError("waiver digest conflicts with existing bytes")
            if not path.exists():
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(decision_bytes); stream.flush(); os.fsync(stream.fileno())
            state.setdefault("waived_gates", {})[decision["gate_id"]] = {
                "decision_sha256": digest, "path": relative, "reason": decision["reason"],
                "observation_sha256": decision["observation_sha256"]}
            needed = {g["gate_id"] for g in state["required_gates"]
                      if g["required"] and g["closure_gate"] != "NON_GATING"}
            covered = set(state.get("accepted_gates", {})) | set(state["waived_gates"])
            if needed.issubset(covered):
                state["phase"] = "DONE"; state["next_stage"] = None
                state["statuses"].update(PRIMARY_OUTCOME_STATUS="ACHIEVED", CORE_ACCEPTANCE_STATUS="PASS",
                    REQUIRED_VERIFICATION_STATUS="WAIVED" if state["waived_gates"] else "PASS",
                    TASK_CLOSURE_STATUS="DONE")
                route = "DONE_WITH_WAIVER" if state["waived_gates"] else "DONE"
            else:
                state["statuses"]["REQUIRED_VERIFICATION_STATUS"] = "INCOMPLETE"
                state["statuses"]["TASK_CLOSURE_STATUS"] = "PENDING_REQUIRED_VERIFICATION"
                route = "WAIT_EVIDENCE"
            _json_atomic(directory / "state.json", state)
            Journal(directory / "events.jsonl").append("USER_GATE_WAIVED", {
                "gate_id": decision["gate_id"], "decision_sha256": digest, "route": route})
            if route in {"DONE", "DONE_WITH_WAIVER"}:
                self._closure(directory, state)
            return route

    def _pending(self, task_id):
        if not (self.state_root / "issues").exists(): return []
        from .escalation import IssueLedger
        return IssueLedger(self.state_root / "issues").pending_for_task(task_id)

    @staticmethod
    def _verify_routing_files(directory, decision):
        for key in ("raw_path", "raw_sha256"):
            if not isinstance(decision.get(key), str) or not decision[key]:
                raise ControllerError("routing observation requires " + key)
        for name in ("evidence", "review") if decision["action"] == "REPLAN" else ("evidence",):
            manifest = decision.get(name)
            if (not isinstance(manifest, dict) or not isinstance(manifest.get("path"), str) or
                type(manifest.get("bytes")) is not int or manifest["bytes"] < 1 or
                not isinstance(manifest.get("sha256"), str)):
                raise ControllerError("routing " + name + " requires an actual file manifest")
        if decision["action"] == "REPLAN" and (not isinstance(decision["review"].get("actor_id"), str) or not decision["review"]["actor_id"].strip()):
            raise ControllerError("replan review requires an independent actor identity")
        raw = _read_regular(directory / safe_relative_path(decision["raw_path"]), directory)
        body = {k:v for k,v in decision.items() if k not in {"raw_path", "raw_sha256"}}
        if not raw or _sha(raw) != decision["raw_sha256"] or json.loads(raw) != body:
            raise ControllerError("trusted routing observation missing, changed, or differently bound")
        manifest = decision["evidence"]
        evidence = _read_regular(directory / safe_relative_path(manifest["path"]), directory)
        if not evidence or len(evidence) != manifest["bytes"] or _sha(evidence) != manifest["sha256"]:
            raise ControllerError("routing evidence bytes/hash mismatch")
        if decision["action"] == "REPLAN":
            review = decision["review"]
            observed = _read_regular(directory / safe_relative_path(review["path"]), directory)
            if not observed or len(observed) != review["bytes"] or _sha(observed) != review["sha256"]:
                raise ControllerError("reviewed replan decision evidence changed")
            content = json.loads(observed)
            reviewed = {k:v for k,v in body.items() if k != "review"}
            if content != {"source":"TRUSTED_OPERATOR", "actor_id":review["actor_id"],
                           "verdict":"PASS", "decision_sha256":_sha(validate_compact_state(reviewed))}:
                raise ControllerError("review is not bound to the exact replan decision")

    def reconcile(self, task_id, decision_bytes, *, authority, operation):
        """Import one trusted, file-backed bounded return; never launch a role."""
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            before = _sha(validate_compact_state(state))
            decision = json.loads(decision_bytes)
            required = {"source", "task_id", "run_id", "contract_sha256", "source_sha256", "action",
                        "authority", "reason", "failed_condition", "evidence", "raw_path", "raw_sha256",
                        "permitted_action", "allowed_paths", "success_criterion", "stop_condition"}
            if not isinstance(decision, dict) or set(decision) != required | ({"review"} if operation == "REPLAN" else set()):
                raise ControllerError("routing decision requires the exact trusted envelope")
            if decision["source"] != "TRUSTED_OPERATOR" or decision["authority"] != authority or decision["action"] != operation:
                raise ControllerError("routing decision authority/action mismatch")
            for key in ("authority", "reason", "failed_condition", "permitted_action", "success_criterion", "stop_condition"):
                if not isinstance(decision[key], str) or not decision[key].strip():
                    raise ControllerError("routing decision requires nonempty " + key)
            if operation not in {"REPAIR", "REPLAN", "ABANDON"}:
                raise ControllerError("unsupported supervised reconciliation operation")
            self._verify_routing_files(directory, decision)
            digest = _sha(decision_bytes)
            record = directory / "routing-decisions" / digest / "consumption.json"
            if record.exists():
                prior = json.loads(_read_regular(record, directory))
                self._replay_state(state, prior)
                self._verify_accepted(state)
                if before != _sha(validate_compact_state(prior["state"])):
                    _json_atomic(directory / "state.json", prior["state"])
                return prior["route"]
            if self._pending(task_id):
                raise ControllerError("unresolved/exhausted issue requires human resolution; routing cannot reset its ledger")
            if state.get("active_run_id") or state["phase"] != "BLOCKED" or not state.get("last_valid_run_id"):
                raise ControllerError("routing return requires the current accepted failed run")
            root, run = self._run(directory, state, state["last_valid_run_id"])
            for key, expected in (("task_id",task_id), ("run_id",run["run_id"]),
                                  ("source_sha256",run["source_sha256"]), ("contract_sha256",state["contract_sha256"])):
                if decision[key] != expected:
                    raise ControllerError("routing decision current-run binding mismatch")
            consumption = json.loads(_read_regular(root / "consumption.json", directory))
            result = _validate(_read_regular(root / "submissions" / consumption["admission_sha256"] / "candidate-result.json", directory), "result.schema.json")
            self._verify_consumed_run(directory, state, run["run_id"])
            self._verify_accepted(state)
            if state["runtime_fact"]["outcome"] != "COMPLETED" or result["candidate_fact"] not in {"FAIL", "REVISION_REQUIRED"}:
                raise ControllerError("unknown/runtime failure cannot authorize a product repair or replan")
            if decision["evidence"] not in result["evidence_manifests"] or decision["evidence"]["observation"] != decision["failed_condition"]:
                raise ControllerError("decision must cite the accepted failed-condition observation")
            if not isinstance(decision["allowed_paths"], list):
                raise ControllerError("routing decision paths must be a list")
            for path in decision["allowed_paths"]:
                safe_relative_path(path)
                if not any(path_is_within_scope(path, scope) for scope in state["allowed_paths"]):
                    raise ControllerError("routing return expands frozen write scope")
            if operation == "REPAIR":
                if run["stage"] != "ACCEPTANCE" or state.get("repair_authorizations", 0):
                    raise ControllerError("only one known Acceptance defect repair is authorized; issue/STOP required")
                if not decision["allowed_paths"]:
                    raise ControllerError("bounded repair requires an exact write scope")
                state["repair_authorizations"] = 1
                state["bounded_repair"] = {"decision_sha256":digest,
                    "decision_path":str((record.parent / "decision.json").relative_to(directory))}
                route = "IMPLEMENT"
            elif operation == "REPLAN":
                if state["plan_revisions"] >= 2:
                    raise ControllerError("reviewed Plan revision limit exhausted; WAIT_HUMAN")
                if decision["review"]["actor_id"] in state.get("planner_actor_ids", []) + state.get("implementer_actor_ids", []):
                    raise ControllerError("replan decision review must be independent")
                state["plan_revisions"] += 1
                if state["handoff_sha256"]:
                    archived = directory / "handoffs" / (state["handoff_sha256"] + ".json")
                    archived.parent.mkdir(exist_ok=True)
                    raw = _read_regular(directory / "handoff.json", directory)
                    if _sha(raw) != state["handoff_sha256"]:
                        raise ControllerError("frozen Handoff changed before replan")
                    if archived.exists() and _read_regular(archived, directory) != raw:
                        raise ControllerError("historical Handoff conflicts")
                    archived.write_bytes(raw); (directory / "handoff.json").unlink()
                state.update(plan_sha256=None, plan_contract_sha256=None, contract_sha256=None, handoff_sha256=None)
                state.pop("reviewed_plan_sha256", None); state.pop("acceptance_run_id", None)
                state.pop("bounded_repair", None)
                route = "PLAN"
            else:
                route = "WAIT_HUMAN"
            if route != "WAIT_HUMAN":
                state["accepted_gates"] = {k:v for k,v in state["accepted_gates"].items()
                    if operation == "REPAIR" and v["stage"] not in {"IMPLEMENT", "ACCEPTANCE", "POST_CHECK"}}
                state.update(phase="IN_PROGRESS", next_stage=route)
                state["statuses"]["TASK_CLOSURE_STATUS"] = "IN_PROGRESS"
            _json_atomic(record.parent / "decision.json", decision, immutable=True)
            _json_atomic(record, {"before_state_sha256":before, "route":route, "state":state}, immutable=True)
            _json_atomic(directory / "state.json", state)
            Journal(directory / "events.jsonl").append("TRUSTED_ROUTING_RETURN", {"decision_sha256":digest, "route":route})
            return route

    def open_issue(self, task_id, packet):
        from .escalation import IssueLedger
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            if packet.get("task_id") != task_id or packet.get("contract_sha256") != state["contract_sha256"]:
                raise ControllerError("issue task/contract mismatch")
            identity = IssueLedger(self.state_root / "issues").open(packet)
            state["phase"] = "BLOCKED"; state["next_stage"] = None
            state["statuses"]["IMPLEMENTATION_STATUS"] = "ESCALATED"
            state["statuses"]["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
            _json_atomic(directory / "state.json", state)
            return identity

    def authorize_continuation(self, task_id, issue_id):
        from .escalation import IssueLedger
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            ledger = IssueLedger(self.state_root / "issues")
            if task_id not in ledger.status(issue_id)["tasks"]:
                raise ControllerError("issue belongs to another task")
            permission = ledger.authorize(issue_id, contract_sha256=state["contract_sha256"], allowed_paths=state["allowed_paths"])
            # A stopped worker may have returned or been interrupted. Preserve
            # its facts; a continuation always obtains a fresh run identity.
            if state.get("active_run_id"):
                root, run = self._run(directory, state)
                _json_atomic(root / "stopped.json", {"issue_id": issue_id, "run_id": run["run_id"], "fact": "STOPPED_BY_ISSUE"}, immutable=True)
            state["active_run_id"] = None; state["next_stage"] = "IMPLEMENT"; state["phase"] = "IN_PROGRESS"
            state["statuses"]["IMPLEMENTATION_STATUS"] = "IN_PROGRESS"
            state["statuses"]["TASK_CLOSURE_STATUS"] = "IN_PROGRESS"
            _json_atomic(directory / "state.json", state)
            return permission

    def return_high_review(self, task_id, issue_id, token, analysis, completion, *,
                           analysis_raw: bytes, analysis_path: Path):
        """Import review and reuse the Plan's authorization for one in-scope action."""
        from .escalation import IssueLedger
        if not isinstance(analysis_raw, bytes) or analysis_path is None:
            raise ControllerError("high-review return requires exact analysis bytes and task-relative file path")
        with task_lock(self.state_root, task_id):
            directory, state = self._load(task_id)
            ledger = IssueLedger(self.state_root / "issues")
            item = ledger.status(issue_id)
            if task_id not in item["tasks"]:
                raise ControllerError("issue belongs to another task")
            path = Path(analysis_path)
            if not path.is_absolute():
                path = directory / path
            try:
                relative_analysis_path = safe_relative_path(path.absolute().relative_to(directory.absolute()).as_posix())
            except ValueError as exc:
                raise ControllerError("high-review analysis must remain below its task evidence root") from exc
            selected_raw = _read_regular(path, directory)
            if selected_raw != analysis_raw:
                raise ControllerError("high-review analysis file changed across the controller boundary")
            try:
                file_analysis = json.loads(selected_raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                raise ControllerError("high-review analysis file is not UTF-8 JSON") from exc
            if (_canonical_sha(file_analysis) != _canonical_sha(analysis) or
                not isinstance(analysis, dict)):
                raise ControllerError("high-review analysis value does not match the exact input file")
            actor = completion.get("actor_id") or completion.get("agent_id")
            if actor in state.get("planner_actor_ids", []) + state.get("implementer_actor_ids", []):
                raise ControllerError("high-reasoning review must be independent of all artifact authors")
            selected_receipts = self._registered_issue_receipts(directory, state, issue_id, analysis,
                analysis_path=relative_analysis_path, analysis_raw=analysis_raw)
            receipt_refs = [{"issue_id": issue_id, "purpose": purpose, "path": selected_receipts[purpose]["path"],
                "sha256": selected_receipts[purpose]["sha256"], "event_id": selected_receipts[purpose]["event_id"]}
                for purpose in ("CONTRACT", "ANALYSIS")]
            ledger.returned(issue_id, token, analysis, completion)
            Journal(directory / "events.jsonl").append("HIGH_REVIEW_SCHEMA_VALIDATION_ACCEPTED", {
                "task_id": task_id, "issue_id": issue_id, "originating_run_id": item["packet"]["run_id"],
                "receipt_refs": receipt_refs})
            route = analysis.get("route")
            if route in {"IMPLEMENTER_FIX", "TARGETED_DIAGNOSTIC"}:
                try:
                    permission = ledger.authorize(issue_id, contract_sha256=state["contract_sha256"],
                                                  allowed_paths=state["allowed_paths"])
                except Exception as exc:
                    state["phase"] = "BLOCKED"; state["next_stage"] = None
                    state["statuses"]["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
                    state["human_action_reason"] = "The suggested action is outside the reviewed write scope."
                    _json_atomic(directory / "state.json", state)
                    return {"issue_id": issue_id, "route": "WAIT_HUMAN",
                            "message": "建議的修正超出原本核准的範圍，需要你先決定是否重新規劃。"}
                if state.get("active_run_id"):
                    root, run = self._run(directory, state)
                    _json_atomic(root / "stopped.json", {"issue_id": issue_id, "run_id": run["run_id"],
                        "fact": "STOPPED_BY_ISSUE"}, immutable=True)
                state["active_run_id"] = None; state["next_stage"] = "IMPLEMENT"; state["phase"] = "IN_PROGRESS"
                state["statuses"]["IMPLEMENTATION_STATUS"] = "IN_PROGRESS"
                state["statuses"]["TASK_CLOSURE_STATUS"] = "IN_PROGRESS"
                state.pop("human_decisions", None)
                _json_atomic(directory / "state.json", state)
                return {"issue_id": issue_id, "route": "IMPLEMENT",
                        "authorization": "REUSED_WITHIN_REVIEWED_SCOPE", "permission": permission,
                        "message": "已確認這一步仍在你原本核准的範圍內，將直接交給實作者處理，不需要你重複授權。"}
            state["active_run_id"] = None; state["next_stage"] = None; state["phase"] = "BLOCKED"
            state["statuses"]["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
            _json_atomic(directory / "state.json", state)
            return {"issue_id": issue_id, "route": "WAIT_HUMAN",
                    "message": "目前需要你決定是否調整原計畫，或處理計畫以外的阻礙。"}

    def _verify_accepted(self, state):
        directory = self.state_root / state["task_id"]
        issue_receipt_refs = []
        for record in Journal(directory / "events.jsonl").read():
            if record.get("event_type") == "HIGH_REVIEW_SCHEMA_VALIDATION_ACCEPTED":
                issue_receipt_refs.extend(record.get("facts", {}).get("receipt_refs", []))
        if issue_receipt_refs:
            self._verify_issue_receipts(directory, state, issue_receipt_refs)
        journal_records = Journal(directory / "events.jsonl").read()
        # Allocations which were stopped before a role result was accepted are
        # legitimate unconsumed history (for example a replan or issue stop).
        # Audit every accepted lineage, and every run with a consumption record;
        # RESULT_ACCEPTED journal facts keep a deleted consumption file visible.
        runs = {record.get("facts", {}).get("run_id") for record in journal_records
                if record.get("event_type") == "RESULT_ACCEPTED"}
        runs.discard(None)
        runs.update(fact["run_id"] for fact in state["accepted_gates"].values())
        runs.update(run_id for run_id in state.get("run_ids", [])
                    if (directory / "runs" / run_id / "consumption.json").exists())
        if state.get("last_valid_run_id"):
            runs.add(state["last_valid_run_id"])
        if state.get("acceptance_run_id"):
            runs.add(state["acceptance_run_id"])
        if state.get("completion_run_id"):
            runs.add(state["completion_run_id"])
        for run_id in runs:
            if run_id != state.get("active_run_id"):
                self._verify_consumed_run(directory, state, run_id)
        for fact in state["accepted_gates"].values():
            for manifest in fact.get("artifacts", [fact["manifest"]]):
                raw = _read_regular(directory / safe_relative_path(manifest["path"]), directory)
                if len(raw) != manifest["bytes"] or _sha(raw) != manifest["sha256"]:
                    raise ControllerError("previously accepted evidence bytes changed; closure refused")
        for gate_id, observation in state.get("human_observations", {}).items():
            receipt_raw = _read_regular(directory / "post-checks" / gate_id / "receipt.json", directory)
            if _sha(receipt_raw) != observation["receipt_sha256"]:
                raise ControllerError("human observation receipt changed after capture")
            receipt = _validate(receipt_raw, "run.schema.json#post_check")
            if receipt["verdict"] != "OBSERVED":
                raise ControllerError("human observation was promoted after capture")
            self._verify_parent_files(directory, receipt)
        for gate_id, waiver in state.get("waived_gates", {}).items():
            waiver_raw = _read_regular(directory / safe_relative_path(waiver["path"]), directory)
            if _sha(waiver_raw) != waiver["decision_sha256"]:
                raise ControllerError("user waiver decision changed after recording")
            decision = _validate(waiver_raw, "waiver.schema.json")
            if decision["gate_id"] != gate_id or decision["task_id"] != state["task_id"]:
                raise ControllerError("user waiver decision is bound to a different gate or task")
        if state["statuses"]["TASK_CLOSURE_STATUS"] == "DONE":
            needed = {g["gate_id"] for g in state.get("required_gates", [])
                      if g["required"] and g["closure_gate"] != "NON_GATING"}
            if not needed.issubset(set(state.get("accepted_gates", {})) | set(state.get("waived_gates", {}))):
                raise ControllerError("DONE is missing a verified or explicitly waived required gate")
            if state.get("waived_gates") and state["statuses"]["REQUIRED_VERIFICATION_STATUS"] != "WAIVED":
                raise ControllerError("waived requirements must remain visible in the verification status")

    @staticmethod
    def _replay_state(state, consumption):
        current = _sha(validate_compact_state(state))
        accepted = _sha(validate_compact_state(consumption["state"]))
        if current not in {accepted, consumption.get("before_state_sha256")}:
            raise ControllerError("consumed decision is not the current state; historical route cannot be replayed")

    def _verify_consumed_run(self, directory, state, run_id):
        root, run = self._run(directory, state, run_id)
        consumption = json.loads(_read_regular(root / "consumption.json", directory))
        attempt = root / "submissions" / consumption["admission_sha256"]
        raw = _read_regular(attempt / "candidate-result.json", directory)
        invitation = _read_regular(attempt / "invitation.json", directory)
        completion = _read_regular(attempt / "completion.json", directory)
        if _sha(raw + invitation + completion) != consumption["admission_sha256"]:
            raise ControllerError("accepted admission originals changed")
        refs = self._stage_receipts_for_admission(directory, state, run, invitation, raw,
                                                  consumption.get("schema_validation_receipts"))
        if refs != consumption.get("schema_validation_receipts"):
            raise ControllerError("consumed schema receipt references changed")
        if _sha(_read_regular(attempt / "post-snapshot.json", directory)) != consumption.get("post_snapshot_sha256"):
            raise ControllerError("accepted product snapshot bytes changed")
        result = _validate(raw, "result.schema.json")
        self._provenance(directory, run, raw, invitation, completion)
        self._evidence(directory, run, result, state=state,
                       evidence_alias_snapshots=consumption.get("evidence_alias_snapshots", []))
        Writers(self, directory, state, root, run).validate(result)

    @staticmethod
    def _verify_parent_files(directory, receipt):
        raw = _read_regular(directory / safe_relative_path(receipt["raw_path"]), directory)
        if not raw or _sha(raw) != receipt["raw_sha256"]:
            raise ControllerError("actual parent observation missing or changed")
        for manifest in receipt["artifacts"]:
            raw = _read_regular(directory / safe_relative_path(manifest["path"]), directory)
            if len(raw) != manifest["bytes"] or _sha(raw) != manifest["sha256"]:
                raise ControllerError("parent artifact bytes/hash mismatch")

    def _verify_accepted_content(self, directory, state):
        run_id = state.get("acceptance_run_id") or state.get("completion_run_id")
        if not run_id:
            raise ControllerError("accepted content has no trusted completion run")
        root, _ = self._run(directory, state, run_id)
        consumption = json.loads(_read_regular(root / "consumption.json", directory))
        post = json.loads(_read_regular(root / "submissions" / consumption["admission_sha256"] / "post-snapshot.json", directory))
        if self.content_sha256(self._snapshot()) != self.content_sha256(post):
            raise ControllerError("current product content differs from accepted content; closure refused")

    def _closure(self, directory, state):
        self._verify_accepted(state)
        self._verify_accepted_content(directory, state)
        _json_atomic(directory / "closure.json", {"task_id": state["task_id"], "statuses": state["statuses"],
            "plan_sha256": state["plan_sha256"], "handoff_sha256": state["handoff_sha256"],
            "accepted_gates": state["accepted_gates"], "acceptance_run_id": state.get("acceptance_run_id"),
            "completion_run_id": state.get("completion_run_id"),
            "human_observations": state.get("human_observations", {}),
            "waived_gates": state.get("waived_gates", {})}, immutable=True)

    @staticmethod
    def _issue_packet(state: dict, run: dict, result: dict) -> dict:
        manifests = {item["evidence_id"]:item for item in result["evidence_manifests"]}
        failures = []
        for gate in result["gate_results"]:
            if gate["verdict"] not in {"FAIL", "BLOCKED"}:
                continue
            manifest = manifests.get(gate.get("evidence_manifest"))
            observation = manifest.get("observation") if manifest else None
            failures.append(f"{gate['gate_id']}: {observation or gate['verdict']}")
        convergence = result["convergence"]
        failed_condition = "；".join(failures) or result["handoff_summary"] or result["candidate_fact"]
        gates = sorted(g["gate_id"] for g in state.get("required_gates", [])
                       if g["required"] and g["phase"] == "IMPLEMENT")
        attempt_count = convergence["meaningful_attempts"]
        attempts = [f"本次實作階段回報 {attempt_count}/3 次有效嘗試；最後發現：{convergence['last_attempt']}."]
        question = (result["human_decisions"][0]["question"] if result["human_decisions"] else
                    "請判斷能否在原計畫範圍內用一個明確步驟排除這個問題。")
        facts = result["analysis"]["facts"] or [f"The Implementer returned {result['candidate_fact']} for run {run['run_id']}."]
        evidence = result["analysis"]["evidence"] or [
            "Controller-verified evidence IDs: " + (", ".join(result["evidence_ids"]) or "none; inspect the bound run record.")]
        return {"task_id":state["task_id"],"run_id":run["run_id"],
            "source_sha256":run["source_sha256"],"goal":state["goal"],
            "failed_condition":failed_condition,
            "capability_boundary":"IMPLEMENT; approved paths=" + ",".join(state["allowed_paths"]) +
                "; required implementation gates=" + ",".join(gates),
            "contract_sha256":state["contract_sha256"],
            "facts":facts,"hypotheses":result["analysis"]["inferences"],
            "evidence":evidence,
            "attempts":attempts,"last_learning":convergence["last_attempt"],
            "impact":result["handoff_summary"],"question":question,
            "owner":"HIGH_REASONING_REVIEWER",
            "success_criterion":"Required implementation checks pass with verified evidence.",
            "stop_condition":"Stop if the next action changes approved scope or fails its focused check."}

    @staticmethod
    def _write_progress(directory: Path, state: dict, *, route: str, result: dict) -> None:
        convergence = state.get("convergence", {})
        statuses = state["statuses"]
        route_text = {
            "ACCEPTANCE":"交給獨立驗收檢查結果。", "DONE":"已完成所有適用檢查。",
            "WAIT_EVIDENCE":"實作已完成；仍缺少必要檢查證據。",
            "WAIT_HUMAN":"已停止實作並保留目前發現，等待一次高階審查或你需要做的決定。",
            "IMPLEMENT":"依核准範圍繼續實作。"}.get(route, f"下一個流程：{route}。")
        status_words = {"ACHIEVED":"已達成","COMPLETE":"已完成","PASS":"已通過",
            "NOT_REQUIRED":"不適用","WAIVED":"已明確略過","NOT_RUN":"尚未執行",
            "NOT_STARTED":"尚未開始","PENDING":"待確認","INCOMPLETE":"尚未完成",
            "BLOCKED":"受阻","ESCALATED":"已交由高階審查","FAIL":"未通過",
            "IN_PROGRESS":"進行中","HIGH_REASONING_REVIEW_REQUIRED":"需要高階審查",
            "READY_FOR_INDEPENDENT_ACCEPTANCE":"等待獨立驗收","PENDING_REQUIRED_VERIFICATION":"等待必要檢查",
            "FIX_REQUIRED":"需要修正","ACCEPTANCE_BLOCKED":"驗收受阻","REPLAN_REQUIRED":"需要重新規劃",
            "IMPLEMENTATION_BLOCKED":"實作受阻","DONE":"已結案","UNKNOWN":"尚未確認"}
        question = "；".join(item["question"] for item in state.get("human_decisions", []))
        if not question and state.get("active_issue_id"):
            question = "問題已整理成高階審查資料；只有建議超出原核准範圍或檢查失敗時，才需要你決定。"
        elif not question and route == "WAIT_EVIDENCE":
            question = "目前不需要改變計畫；請依狀態補上缺少的檢查證據。"
        elif not question:
            question = "否。"
        lines = ["# 目前進度", "", f"**要完成什麼：** {state['goal']}", "",
            f"**目前卡在哪：** {state.get('last_handoff_summary') if route in {'WAIT_HUMAN','WAIT_EVIDENCE'} else '目前沒有已知阻礙。'}", "",
            f"**已做的有效嘗試：** {convergence.get('meaningful_attempts',0)}/3（連續無新進展：{convergence.get('consecutive_no_progress',0)}/2）", "",
            f"**最後一次學到什麼：** {convergence.get('last_attempt','目前沒有實作嘗試紀錄。')}", "",
            f"**現在有更接近成功嗎：** {'有新證據或已驗證的進展。' if convergence.get('information_gain') else '最後一次嘗試沒有帶來新證據。'}", "",
            f"**下一步與停止條件：** {route_text} 若超出核准範圍或下一項檢查失敗，就停止並交還問題。", "",
            f"**需要你決定嗎：** {question}", "",
            f"**實作狀態：** {status_words.get(statuses['IMPLEMENTATION_STATUS'],statuses['IMPLEMENTATION_STATUS'])}",
            f"**核心結果檢查：** {status_words.get(statuses['CORE_ACCEPTANCE_STATUS'],statuses['CORE_ACCEPTANCE_STATUS'])}",
            f"**必要驗證：** {status_words.get(statuses['REQUIRED_VERIFICATION_STATUS'],statuses['REQUIRED_VERIFICATION_STATUS'])}",
            f"**獨立驗收：** {status_words.get(statuses['INDEPENDENT_ACCEPTANCE_STATUS'],statuses['INDEPENDENT_ACCEPTANCE_STATUS'])}",
            f"**整體結案：** {status_words.get(statuses['TASK_CLOSURE_STATUS'],statuses['TASK_CLOSURE_STATUS'])}", ""]
        path = directory / "progress.md"
        fd, temp = tempfile.mkstemp(prefix="progress-", dir=directory)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as stream:
                stream.write("\n".join(lines)); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp,path)
        finally:
            Path(temp).unlink(missing_ok=True)

    def _advance(self, state: dict, run: dict, invitation: dict, result: dict, passed: bool) -> str:
        stage = run["stage"]; statuses = state["statuses"]
        if result["needs_human"]:
            state["phase"] = "BLOCKED"; state["next_stage"] = None
            statuses["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
            state["human_decisions"] = result["human_decisions"]
            return "WAIT_HUMAN"
        state.pop("human_decisions", None)
        convergence = result["convergence"]
        if stage == "IMPLEMENT" and result["candidate_fact"] != "PASS" and (
            convergence["consecutive_no_progress"] >= 2 or
            convergence["meaningful_attempts"] >= 3 or convergence["stuck"]
        ):
            state["phase"] = "BLOCKED"; state["next_stage"] = None
            statuses["IMPLEMENTATION_STATUS"] = "ESCALATED"
            statuses["TASK_CLOSURE_STATUS"] = "HIGH_REASONING_REVIEW_REQUIRED"
            state["human_decisions"] = [{"id":"convergence-stop",
                "question":"實作者已連續卡住，是否交由高階審查分析一次？",
                "options":["交給高階審查","我來決定下一步"],
                "recommendation":"交給高階審查，先找出一個安全且有限的下一步。"}]
            return "WAIT_HUMAN"
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
        for gate in result["gate_results"]:
            if gate["verdict"] == "PASS":
                manifest = next(m for m in result["evidence_manifests"] if m["evidence_id"] == gate["evidence_manifest"])
                state["accepted_gates"][gate["gate_id"]] = {"run_id": run["run_id"], "evidence_id": gate["evidence_manifest"], "stage": stage, "manifest": manifest}
        if stage == "PLAN":
            state["planner_actor_id"] = invitation["actor_id"]
            workflow = state["workflow_policy"]
            if workflow["plan_review_required"]:
                route = "PLAN_REVIEW"
            else:
                state["reviewed_plan_sha256"] = state["plan_sha256"]
                route = "HANDOFF" if workflow["handoff_review_required"] else "IMPLEMENT"
                if route == "IMPLEMENT":
                    self._compile_handoff(self.state_root / state["task_id"], state)
        elif stage == "PLAN_REVIEW":
            state["reviewed_plan_sha256"] = state["plan_sha256"]
            route = "HANDOFF" if state["workflow_policy"]["handoff_review_required"] else "IMPLEMENT"
            if route == "IMPLEMENT":
                self._compile_handoff(self.state_root / state["task_id"], state)
        elif stage == "HANDOFF":
            route = "IMPLEMENT"
        elif stage == "IMPLEMENT":
            state.setdefault("implementer_actor_ids", []).append(invitation["actor_id"])
            statuses["IMPLEMENTATION_STATUS"] = "COMPLETE"
            workflow = state["workflow_policy"]
            acceptance_required = (state["task_class"] == "CRITICAL" or
                workflow["independent_acceptance_required"] or
                any(g["required"] and g["phase"] == "ACCEPTANCE" for g in state["required_gates"]))
            if acceptance_required:
                statuses["TASK_CLOSURE_STATUS"] = "READY_FOR_INDEPENDENT_ACCEPTANCE"; route = "ACCEPTANCE"
            else:
                state["completion_run_id"] = run["run_id"]
                state["core_acceptance_run_id"] = run["run_id"]
                statuses.update(PRIMARY_OUTCOME_STATUS="ACHIEVED", CORE_ACCEPTANCE_STATUS="PASS",
                                INDEPENDENT_ACCEPTANCE_STATUS="NOT_REQUIRED")
                needed = {g["gate_id"] for g in state["required_gates"] if g["required"] and g["closure_gate"] != "NON_GATING"}
                if not needed.issubset(state["accepted_gates"]):
                    statuses["REQUIRED_VERIFICATION_STATUS"] = "INCOMPLETE"
                    statuses["TASK_CLOSURE_STATUS"] = "PENDING_REQUIRED_VERIFICATION"
                    state["phase"] = "BLOCKED"; state["next_stage"] = None
                    return "WAIT_EVIDENCE"
                statuses.update(REQUIRED_VERIFICATION_STATUS="PASS", TASK_CLOSURE_STATUS="DONE")
                route = "DONE"
        else:
            state["acceptance_run_id"] = run["run_id"]
            statuses.update(PRIMARY_OUTCOME_STATUS="ACHIEVED", CORE_ACCEPTANCE_STATUS="PASS", INDEPENDENT_ACCEPTANCE_STATUS="PASS")
            self._verify_accepted(state)
            needed = {g["gate_id"] for g in state["required_gates"] if g["required"] and g["closure_gate"] != "NON_GATING"}
            if not needed.issubset(state["accepted_gates"]):
                statuses["INDEPENDENT_ACCEPTANCE_STATUS"] = "PASS"
                statuses["REQUIRED_VERIFICATION_STATUS"] = "INCOMPLETE"
                statuses["TASK_CLOSURE_STATUS"] = "PENDING_REQUIRED_VERIFICATION"
                state["next_stage"] = None; state["phase"] = "BLOCKED"
                return "WAIT_EVIDENCE"
            statuses.update(PRIMARY_OUTCOME_STATUS="ACHIEVED", CORE_ACCEPTANCE_STATUS="PASS",
                REQUIRED_VERIFICATION_STATUS="PASS", INDEPENDENT_ACCEPTANCE_STATUS="PASS", TASK_CLOSURE_STATUS="DONE")
            route = "DONE"
        state["next_stage"] = route if route != "DONE" else None
        state["phase"] = "DONE" if route == "DONE" else "IN_PROGRESS"
        return route
