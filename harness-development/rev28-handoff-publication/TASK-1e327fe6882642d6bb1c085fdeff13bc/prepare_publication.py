"""Prepare this documentation-only publication; never operate LINE or stage Git."""
import hashlib
import json
import pathlib
import re
import subprocess
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[3]
T = pathlib.Path(__file__).resolve().parent
P = ROOT / 'harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b'
C = P / 'bounded-correction-01'
RELEASE = pathlib.Path('/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, data):
    path = T / name
    assert not path.exists(), 'No overwrite: ' + name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def validate(schema_name, data):
    from referencing import Registry, Resource
    from jsonschema import Draft202012Validator
    def refuse(uri):
        raise RuntimeError('No remote schema retrieval: ' + uri)
    schemas = [json.loads(p.read_text()) for p in sorted((RELEASE / 'schemas/v3').glob('*.schema.json'))]
    registry = Registry(retrieve=refuse).with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
    schema = json.loads((RELEASE / 'schemas/v3' / schema_name).read_text())
    Draft202012Validator(schema, registry=registry).validate(data)

def main():
    assert ROOT == pathlib.Path('/Users/hsiaojohnny/Documents/ChatGPT/Line_backup')
    source = json.loads((C / 'final-source-manifest.json').read_text())
    rows = source['all_source_and_tests']
    assert len(rows) == 117
    for row in rows:
        f = ROOT / row['path']
        assert not f.is_symlink() and f.stat().st_size == row['bytes'] and digest(f) == row['sha256'], row['path']
    base = json.loads((T / 'preservation-baseline.json').read_text())
    for row in base['files']:
        f = ROOT / row['path']
        assert f.stat().st_size == row['bytes'] and digest(f) == row['sha256'], row['path']
    write('source-preservation-check.json', {'verdict':'PASS','source_test_files':117,'baseline_files':len(base['files']),'source_manifest_sha256':digest(C/'final-source-manifest.json'),'all_source_and_tests':rows,'baseline_sha256':digest(T/'preservation-baseline.json'),'note':'Actual byte checks, no product test rerun or LINE interaction; not whole-workspace or OS enforcement.'})

    document = ROOT / '20261009_handoff.md'
    body = document.read_text()
    assert body.startswith('```text\n你是接手此專案的 agent。')
    required = ['所有相簿','不需要人工介入','OCR','Computer Use','macOS','182 張','明確授權','Best Practices','canDispatch=false','NOT_ACHIEVED','77,918','318','沒有建立它','不宣稱已包含於同一個commit']
    for phrase in required:
        assert phrase in body, phrase
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', body)
    for link in links:
        assert not link.startswith(('http:','https:','file:')), link
        assert (ROOT / link).is_file(), link
    anchors = [P/'plan-03.md',P/'plan-contract-02.json',P/'project-binding-report.schema.json',P/'plan-review-02.result.json',C/'acceptance.result.json',C/'root-final.result.json',C/'final-source-manifest.json',C/'final-preservation-verification.json',C/'admission-order-deviation.json',ROOT/'config/line_backup_config.json',ROOT/'state/backup_state.json',ROOT/'20261006_issue_harness_offline_schema_resolution.md']
    for f in anchors:
        assert digest(f) in body, str(f)
    assert (P/'plan-contract-02.json').read_bytes() == (P/'handoff.json').read_bytes()
    write('document-check.json', {'verdict':'PASS','document':str(document.relative_to(ROOT)),'bytes':document.stat().st_size,'sha256':digest(document),'local_links_verified':links,'anchors_verified':[{'path':str(f.relative_to(ROOT)),'sha256':digest(f)} for f in anchors],'user_requirements_verified':required,'review':'Root documentation review; prior independent product A1 retained, no new independent review claimed.'})

    p_names = ['continuation-completed-20261009.md','progress.md','plan-03.md','plan-contract-02.json','handoff.json','project-binding-report.schema.json','plan-review-02.result.json','user-consent-20261006.json','user-pause-20261006.json','resume-admission-20261009.json','acceptance-01.result.json','root-acceptance-blocked.result.json','evidence-join-gap-reproduction.json','candidate-02-swift-full.json','candidate-02-swift-full.log','candidate-02-swift-legacy.json','candidate-02-swift-legacy.log','candidate-02-cli-build.json','candidate-02-cli-build.log','retained-packet-compatibility.json']
    c_names = ['result.md','root-final.result.json','acceptance.result.json','acceptance-archive-validation.json','final-source-manifest.json','delivery-receipt.json','user-grant.json','supplemental-convergence.json','admission-order-deviation.json','python-focused.json','python-focused.log','swift-focused.json','swift-focused.log','actual-cli-summary.json','actual-project57.stdout','actual-project182.stdout','retained-contradiction-refusal.stdout','retained-other-target-contradiction-refusal.stdout','full-swift-compatibility-join.json','final-isolation-verification.json','final-preservation-verification.json','implement-gates.json','implementation-note.md']
    t_names = ['publication-context.json','plan.md','plan-contract.json','handoff.json','planner.result.json','user-next-task-decisions.json','commit-message.txt','progress.md','source-preservation-check.json','document-check.json','schema-check.json','publication-files.json','prepare_publication.py']
    selected = ['20261009_handoff.md'] + [str((P/n).relative_to(ROOT)) for n in p_names] + [str((C/n).relative_to(ROOT)) for n in c_names] + [str((T/n).relative_to(ROOT)) for n in t_names]
    selected = sorted(selected)
    assert len(selected) == len(set(selected))
    for name in selected:
        f = ROOT / name
        if f.exists():
            assert not f.is_symlink() and f.is_file()
            f.read_text()
            assert f.stat().st_size < 300000, name
    write('publication-files.json', {'literal_paths':selected,'scope':'Documentation + selected text evidence only; no local product source/config/state/photos/binaries/fixtures. Post-publication receipts excluded.'})

    gates = []
    for gate_id, role in [('DOC','OUTCOME'),('PRESERVE','MUST_NOT_BREAK'),('GIT','OUTCOME')]:
        gates.append({'gate_id':gate_id,'required':True,'owner':'ROLE','phase':'IMPLEMENT','evidence_source':'ROLE_OBSERVATION','goal_criticality':'CORE','evidence_role':role,'closure_gate':'HARD_CLEAN','reuse':'NEVER'})
    contract = {'format_version':'3','task_id':T.name,'goal':'Publish exact detailed LINE tool handoff, confirmed182 and actual-test authority, retained final text evidence; normal commit/push only.','task_class':'QUICK','allowed_paths':['20261009_handoff.md',str(T.relative_to(ROOT))]+[n for n in selected if not n.startswith(str(T.relative_to(ROOT))) and n!='20261009_handoff.md'],'required_evidence':['DOC','PRESERVE','GIT'],'gate_specs':gates,'capability_policy':{'network':'PROXY_ALLOWLIST','browser':False,'destinations':['https://github.com/s9008129/Line_backup.git']},'retry_policy':{'transient_read_only_retries':2,'delays_seconds':[10,30]},'resource_policy':{'prompt_bytes':65536,'state_bytes':524288,'inspect_bytes':16384,'log_bytes':134217728},'workflow_policy':{'plan_review_required':False,'independent_acceptance_required':False,'max_parallel_read_only_helpers':0,'max_parallel_writers':0,'handoff_review_required':False}}
    validate('task.schema.json', contract)
    write('plan-contract.json', contract)
    (T/'handoff.json').write_bytes((T/'plan-contract.json').read_bytes())
    assert (T/'handoff.json').read_bytes() == (T/'plan-contract.json').read_bytes()
    planner = {'result_format_version':'3','task_id':T.name,'run_id':str(uuid.uuid4()),'role':'PLANNER','stage':'PLAN','candidate_fact':'PASS','validation_fact':'VALID','routing_fact':'HANDOFF','statuses':{'PRIMARY_OUTCOME_STATUS':'NOT_ACHIEVED','IMPLEMENTATION_STATUS':'NOT_STARTED','CORE_ACCEPTANCE_STATUS':'NOT_RUN','REQUIRED_VERIFICATION_STATUS':'NOT_RUN','INDEPENDENT_ACCEPTANCE_STATUS':'NOT_REQUIRED','TASK_CLOSURE_STATUS':'IN_PROGRESS'},'gate_results':[],'evidence_ids':[],'plan_sha256':digest(T/'plan.md'),'handoff_sha256':digest(T/'handoff.json'),'plan_contract_sha256':digest(T/'plan-contract.json'),'source_sha256':source['source_sha256'],'evidence_manifests':[],'analysis':{'facts':['User requested dated handoff and git add/commit/push.','Latest user explicitly authorized182 album click and actual testing; documentation records it.','Only documentation publication paths are editable; selected prior text evidence is immutable.'],'inferences':['QUICK serial documentation-only route is sufficient.'],'unknowns':['Controller admission and OS sandbox/network enforcement are unavailable/unknown.','Commit/push outcomes remain to be observed.'],'evidence':['plan.md','user-next-task-decisions.json','publication-files.json'],'confidence':'High for documented scope; publication remains future gate.'},'handoff_summary':'Write and check full handoff; literal stage, commit, normal push and verify remote identity. No product edits or LINE actions in this unit.','needs_human':False,'human_decisions':[],'convergence':{'meaningful_attempts':0,'consecutive_no_progress':0,'last_attempt':'Plan and exact scope prepared; implementation publication pending.','information_gain':True,'stuck':False},'writer_receipts':[]}
    validate('result.schema.json', planner)
    write('planner.result.json', planner)
    write('schema-check.json', {'verdict':'PASS','schema_root':str(RELEASE/'schemas/v3'),'validated':['plan-contract.json','planner.result.json'],'handoff_byte_identical':True,'network_schema_resolution':False,'method':'Complete pinned offline referencing.Registry; unknown retrieval raises error. Standalone role validation, not controller admission.'})
    for name in selected:
        assert (ROOT/name).is_file(), name
    print(json.dumps({'verdict':'PASS','literal_publication_paths':len(selected),'document_bytes':document.stat().st_size,'source_test_files':117},ensure_ascii=False))

if __name__ == '__main__':
    main()
