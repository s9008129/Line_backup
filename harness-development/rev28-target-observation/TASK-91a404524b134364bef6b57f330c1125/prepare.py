import hashlib, json, os, stat, subprocess
from pathlib import Path
import jsonschema
from referencing import Registry, Resource

ROOT = Path('/Users/hsiaojohnny/Documents/ChatGPT/Line_backup')
REL = 'harness-development/rev28-target-observation/TASK-91a404524b134364bef6b57f330c1125'
T = ROOT / REL
OUTPUT = 'harness-development/native-diagnostics/TASK-91a404524b134364bef6b57f330c1125/attempt-01'
C = ROOT / 'harness-development/rev28-passive-collector/TASK-1b159aadafc64ef9a2371832f46237a1'
RELEASE = Path('/Users/hsiaojohnny/.codex/harness-releases/4.7.0/1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d')

def sha(b): return hashlib.sha256(b).hexdigest()
def entry(p):
    s = p.lstat()
    e = dict(path=str(p.relative_to(ROOT)), mode=stat.S_IMODE(s.st_mode))
    if stat.S_ISREG(s.st_mode):
        b = p.read_bytes(); e.update(kind='file', bytes=len(b), sha256=sha(b))
    elif stat.S_ISLNK(s.st_mode):
        b = os.readlink(p).encode(); e.update(kind='symlink', bytes=len(b), sha256=sha(b))
    else: e.update(kind='special', file_type=stat.S_IFMT(s.st_mode), device=s.st_rdev)
    return e

source = json.loads((C / 'evidence/candidate-02-source.json').read_bytes())
material = b''
for e in source['files']:
    b = (ROOT / e['path']).read_bytes()
    assert len(b) == e['bytes'] and sha(b) == e['sha256'], e['path']
    material += e['path'].encode() + b'\0' + b + b'\0'
assert sha(material) == 'ac48a44af0823b22d2e512945b1a6cc7b7bb870caab73202cabb199c77b7a04e'
binary = (ROOT / source['binary']['path']).resolve(strict=True)
binary.relative_to(ROOT)
assert sha(binary.read_bytes()) == 'b4fce6a1a53c57b542015636244c82aa1aec059eb4264fe947037a22ebf0168c'
critical = [entry(ROOT / p) for p in ['config/line_backup_config.json', 'state/backup_state.json', 'evidence/20260925-rev28-native-closed-loop/harness/frozen/capture-geometry-rulebook-v1.json']]
assert critical[0]['sha256'] == '5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362'
assert critical[1]['sha256'] == '1093dd3065f7ce80ce4cfcb97081cabbb9b4334a53eeb77d1233985e5432acb9'
assert not (ROOT / OUTPUT).exists()
entries = []
for parent, dirs, files in os.walk(ROOT, followlinks=False):
    if Path(parent) == ROOT: dirs[:] = [d for d in dirs if d != '.git']
    if Path(parent) == T: dirs[:] = []; continue
    for n in files + [d for d in dirs if (Path(parent) / d).is_symlink()]:
        entries.append(entry(Path(parent) / n))
baseline = dict(entries=sorted(entries, key=lambda e:e['path']), critical=critical,
    source=source, binary_realpath=str(binary), head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    index_sha256=sha((ROOT/'.git/index').read_bytes()), staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True))
assert not baseline['staged']
baseline_bytes = (json.dumps(baseline,ensure_ascii=False,indent=2)+'\n').encode()
if (T/'baseline.json').exists():
    assert (T/'baseline.json').read_bytes() == baseline_bytes, 'baseline cannot be rewritten'
else:
    (T/'baseline.json').write_bytes(baseline_bytes)
contract = json.loads((C/'plan-02-contract.json').read_bytes())
contract.update(task_id=T.name, goal='Obtain one externally anchored current LINE primary-window passive observation of user-selected 2024-05-06 through 2024-05-10 / 182 album in configured canonical group; no input, activation, backup, state/product/ledger mutation or changed capture scope. Original issue budgets retained; all calibration/occlusion/currentComposer/PhaseB certifications UNKNOWN.',
    allowed_paths=[REL, 'harness-development/native-diagnostics', 'harness-development/native-diagnostics/TASK-91a404524b134364bef6b57f330c1125', OUTPUT], required_evidence=['plan-review','exact-handoff','fresh-target-context','actual-one-passive-invocation','externally-anchored-packet-validation-or-typed-refusal','scope-external-preservation','independent-acceptance'])
contract['gate_specs'] = []
for gate, phase, role in [('P1_PLAN_REVIEW','PLAN','MUST_NOT_BREAK'),('I1_CONTEXT','IMPLEMENT','MUST_NOT_BREAK'),('I2_PACKET','IMPLEMENT','OUTCOME'),('I3_PRESERVATION','IMPLEMENT','MUST_NOT_BREAK'),('A1_ACCEPTANCE','ACCEPTANCE','OUTCOME')]:
    contract['gate_specs'].append(dict(gate_id=gate,required=True,owner='ROLE',phase=phase,evidence_source='ROLE_OBSERVATION',goal_criticality='CORE',evidence_role=role,closure_gate='HARD_CLEAN',reuse='NEVER'))
schema=json.loads((RELEASE/'schemas/v3/task.schema.json').read_bytes())
registry = Registry()
for path in (RELEASE/'schemas/v3').glob('*.schema.json'):
    document = json.loads(path.read_bytes())
    registry = registry.with_resource(document['$id'], Resource.from_contents(document))
jsonschema.Draft202012Validator(schema,registry=registry).validate(contract)
(T/'plan-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status='BASELINE_AND_CONTRACT_VALID',entries=len(entries),binary_realpath=str(binary),source_sha256=sha(material),critical=critical,plan_sha256=sha((T/'plan.md').read_bytes()),contract_sha256=sha((T/'plan-contract.json').read_bytes())),ensure_ascii=False))
