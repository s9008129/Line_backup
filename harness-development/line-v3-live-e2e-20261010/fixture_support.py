"""External fixture I/O only. Never imports CUA or reads old photo pixels."""
import base64
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import uuid
import zlib
from line_backup_acceptance.common import json_bytes,utc_now
from line_backup_batch.store import Store
from line_backup_batch.service import Service
from line_backup_batch.schema import require

ROOT=Path(__file__).resolve().parents[2]
TASK=Path(__file__).resolve().parent
FIXTURES=TASK/'fixtures'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def token(receipt):return base64.b64encode(json_bytes(receipt)).decode()
def png(width=128,height=128,marker=0):
    def chunk(name,raw):return struct.pack('>I',len(raw))+name+raw+struct.pack('>I',zlib.crc32(name+raw)&0xffffffff)
    rows=b''.join(b'\0'+bytes([marker%256,60,120])*width for _ in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

class Fixture:
    def __init__(self,version=3,cap=2):
        self.temp=tempfile.TemporaryDirectory(dir=FIXTURES);self.root=Path(self.temp.name)
        self.artifacts='harness-development/evidence';self.owner='execution-'+uuid.uuid4().hex
        self.session=self.owner;self.serial=0
        for name in ('state','config','backups',self.artifacts): (self.root/name).mkdir(parents=True,exist_ok=True)
        (self.root/'state/.line-backup-state.lock').touch(mode=0o600)
        cfg=json.loads((TASK/'fixtures/config/source-config.json').read_bytes())
        cfg.update(group_name='FixtureGroup',group_key='line:jp.naver.line.mac:FixtureGroup',backup_root=str(self.root/'backups'),
            max_albums_per_run=cap,poll_interval_seconds=1,max_wait_seconds=3)
        self.cfg=cfg
        s=dict(schema_version=version,revision=0,current_run_id=None,active_writer_id=None,context_lock=None,runs=[],verified_albums=[])
        if version==3:s['active_batch']=None
        self.save(s)
        shutil.copytree(ROOT/'src/line_backup_acceptance',self.root/'src/line_backup_acceptance',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT/'src/line_backup_batch',self.root/'src/line_backup_batch',ignore=shutil.ignore_patterns('__pycache__'))
        (self.root/'scripts').mkdir();shutil.copyfile(ROOT/'scripts/line_backup_cua_adapter.mjs',self.root/'scripts/line_backup_cua_adapter.mjs')
        self.svc=Service(str(self.root),self.owner,self.artifacts)
        self.binding=json.loads((TASK/'evidence/decoder-binding.json').read_bytes())
    def close(self):self.temp.cleanup()
    def save(self,s):
        (self.root/'state/backup_state.json').write_bytes(json_bytes(s))
        (self.root/'config/line_backup_config.json').write_bytes(json_bytes(self.cfg))
        (self.root/'state/run_log.md').write_bytes(b'fixture only\n')
    def state(self):return json.loads((self.root/'state/backup_state.json').read_bytes())
    def receipt(self):return self.svc.store.snapshot()['receipt']
    def ref(self,name,raw):
        path=self.root/self.artifacts/name;path.write_bytes(raw)
        return dict(path=str(path.relative_to(self.root)),bytes=len(raw),sha256=sha(raw))
    def grant(self,operations):
        receipt=self.receipt()
        return dict(grant_version='line-batch-execution-grant-1',task_id='TASK-20261010-line-v3-live-e2e',
            project_root=str(self.root),fixture=True,artifact_dir=self.artifacts,owner=self.owner,operations=list(operations),
            config_sha256=receipt['config_sha256'],source_sha256=receipt['source_sha256'],album_quota=0,lifecycle_album_limit=0,
            save_all_dispatch_limit=0,chooser_confirmation_limit=0,reversible_gui_invocation_limit=0,
            authorization_evidence=None,acceptance_evidence=None,
            contract_sha256=None,native_binary_sha256=None,gui_ledger=None)
    def observation(self,identities,surface='ALBUMS',top=False,bottom=False):
        self.serial+=1
        raw=png(marker=self.serial);image=self.ref('frame-'+uuid.uuid4().hex+'.png',raw)
        proof=self.ref('proof-'+uuid.uuid4().hex+'.json',json_bytes(dict(fixture=True,frame_id=sha(raw),top=top,bottom=bottom)))
        sck_raw=png(marker=self.serial+80);sck_frame=self.ref('sck-frame-'+uuid.uuid4().hex+'.png',sck_raw)
        texts=[('anchor-left',10,10),('anchor-right',90,14),('anchor-low',20,100)]
        def ocr_items():
            return [dict(text=text,confidence=0.99,candidate_count=1,bounds=[x,y,8,8]) for text,x,y in texts]
        ocr=self.ref('sck-ocr-'+uuid.uuid4().hex+'.json',json_bytes(dict(version=1,cua_frame_id=sha(raw),
            sck_frame_sha256=sha(sck_raw),cua=ocr_items(),sck=ocr_items())))
        captured_at=dt.datetime.now(dt.timezone.utc).isoformat()
        bounds=[0,0,128,128]
        support_value=dict(version=1,provider='FIXTURE_ONLY',fixture=True,frame_id=sha(raw),session_id=self.session,
            pid=2,window_id=1,layout_key='fixture-128',captured_at=captured_at,sck_frame=sck_frame,ocr=ocr,
            native_binding=dict(bundle_id=self.cfg['app_identifier'],pid=2,window_id=1,display_id=1,
                cua_capture_bounds_points=bounds,sck_window_bounds_points=bounds,display_bounds_points=bounds,
                cua_size_px=[128,128],sck_size_px=[128,128]),uncertainty_px=2,safe_margin_px=6,
            interactive_intersection_px=[90,40,20,20])
        sck_support=self.ref('sck-support-'+uuid.uuid4().hex+'.json',json_bytes(support_value))
        cards=[]
        for i,identity in enumerate(identities):
            y=25+i*60
            cards.append(dict(fingerprint=identity,title=identity['start_date'].replace('-','/')+'～'+identity['end_date'][5:].replace('-','/'),
                metadata_bounds=[10,y+5,60,12],card_bounds=[0,y,100,30],fully_visible=True,
                safe_metadata_bounds=[12,y+7,56,8],neighbor_bounds=[]))
        return dict(frame=image,frame_id=sha(raw),session_id=self.session,group_key=self.cfg['group_key'],surface=surface,
            captured_at=captured_at,provider='HOSTED_CUA',layout_key='fixture-128',window_id=1,pid=2,
            width=128,height=128,mapping=dict(space='CUA_CAPTURE_PIXELS',uncertainty=2,evidence=proof,frame_id=sha(raw),
                layout_key='fixture-128',sck_support=sck_support),
            cards=cards,boundary=dict(top=top,bottom=bottom,evidence=proof),editable_focus='NONE',occlusion='CLEAR')
    def frames(self,identities):
        if len(identities)==1:return [self.observation(identities,top=True,bottom=True)]
        return [self.observation(identities[i:i+2],top=i==0,bottom=i==len(identities)-2) for i in range(len(identities)-1)]
    def start(self,identities,limit=2):
        receipt=self.svc.begin(self.receipt(),'backup_batch',limit)['receipt']
        return self.svc.admit(receipt,self.frames(identities),self.session)['receipt']
    def prepare(self,identity):return self.svc.prepare(self.receipt(),self.observation([identity]))
    def calibration(self,identity):
        detail=self.observation([identity],'ALBUM_DETAIL');closure=self.observation([identity],'ALBUM_DETAIL')
        cal=dict(observed_at=utc_now(),screenshot_width=128,screenshot_height=128,ellipsis=[115,15],dot_spacing=5,
            save_all_point=[100,50],confidence='HIGH',evidence='fixture actual external menu I/O')
        menu=dict(label='儲存全部',frame_id=detail['frame_id'],layout_key=detail['layout_key'],evidence=detail['mapping']['evidence'],
            safe_bounds=[90,40,20,20],ellipsis_bounds=[110,10,10,10],closure_trace=['OPEN_MENU','OBSERVE_SAVE_ALL','CLOSE_WITHOUT_COMMAND','DETAIL_MATCH'])
        return detail,cal,menu,closure
    def intent(self,identity):
        detail,cal,menu,closure=self.calibration(identity)
        receipt=self.svc.calibrate(self.receipt(),detail,cal,menu,closure)['receipt']
        return self.svc.intent(receipt,self.observation([identity],'ALBUM_DETAIL'))
    def cli(self,operation,data=None,expected=None,owner=None,grant_operations=None):
        grant=self.grant(grant_operations or [operation])
        grant['owner']=owner or self.owner
        g=self.ref('grant-'+uuid.uuid4().hex+'.json',json_bytes(grant))
        inp=self.ref('input-'+uuid.uuid4().hex+'.json',json_bytes(dict(expected_token=token(expected or self.receipt()),data=data or {})))
        argv=[sys.executable,'-B','-m','line_backup_batch',operation,'--project-root',str(self.root),
            '--authorization',g['path'],'--input',inp['path'],'--fixture']
        p=subprocess.run(argv,capture_output=True,env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1'},timeout=30)
        return p,argv
    def seed(self,identity):
        s=self.state();rid='seed-'+uuid.uuid4().hex
        destination=str(self.root/'backups'/self.cfg['group_name']/f"{identity['start_date']}_{identity['end_date']}_{identity['expected_images']}張")
        v=dict(observed_at=utc_now(),outcome='PASS',regular_files=identity['expected_images'],image_files=identity['expected_images'],subdirectories=[],
            total_bytes=3,extensions={'.png':identity['expected_images']},metadata_files=[],zero_byte_files=[],partial_temp_files=[],unrecognized_files=[],
            other_entries=[],stable_samples=3,inventory=[dict(relative_path='retained-fixture.png',size=3,mtime_ns=9223372036854775000,mime='image/png',
            sha256='0'*64,status='OK',type='regular',failure_class=None)],evidence='retained fixture proof; never decode on SKIP')
        record=dict(app_identifier=self.cfg['app_identifier'],group_key=self.cfg['group_key'],run_id=rid,fingerprint=identity,destination=destination,verification=v)
        ref=self.ref('seed-'+uuid.uuid4().hex+'.json',json_bytes(record));reference='fixture:'+ref['path']+':'+ref['sha256']
        event=dict(phase='VERIFIED',at=utc_now(),evidence=reference)
        run=dict(run_id=rid,mode='backup_one',group_key=self.cfg['group_key'],album_id=None,fingerprint=identity,observed_title=self.cfg['group_name'],
            title_confidence='HIGH',destination=destination,destination_initially_empty=True,phase='VERIFIED',checkpoint=event,events=[event],intent=None,
            recovery_used={},runtime_errors=[],verification=v,workflow_outcome='VERIFIED',stop_reason='COMPLETED',batch_id=None,intent_state='INTENT_NONE',
            manual_reconciliation_required=False,reconciliation_reason=None,contract_revision='1.0-rc2',dispatch_state='NOT_ATTEMPTED',dispatch_evidence=None,reconciliations=[])
        s['runs'].append(run);s['verified_albums'].append(dict(group_key=self.cfg['group_key'],fingerprint=identity,verified_run_id=rid,
            destinations=[destination],source_kind='filesystem_verification',evidence=reference));self.save(s)

def identity(count=2,day=1):return dict(start_date=f'2024-06-{day:02}',end_date=f'2024-06-{day:02}',expected_images=count)

class Provider:
    def __init__(self,f,identities):
        self.f=f;self.identities=identities;self.opens=[];self.dispatches=[];self.confirms=[];self.now=0
    def catalog(self):return self.f.frames(self.identities),self.f.session
    final_catalog=catalog
    def target(self):return self.identities[self.f.state()['active_batch']['next_index']]
    def observe_album(self):return self.f.observation([self.target()])
    def open_album(self,prepared):self.opens.append(prepared['fingerprint'])
    def calibrate(self):return self.f.calibration(self.target())
    def detail(self):return self.f.observation([self.target()],'ALBUM_DETAIL')
    def original_atomic_dispatch(self,committed):
        action=committed['result'];self.dispatches.append(action['action_id']);self.confirms.append(action['action_id'])
        for i in range(action['fingerprint']['expected_images']):
            (Path(action['destination'])/f'{i}.png').write_bytes(png(4,4,i))
        evidence=dict(run_id=action['run_id'],action_id=action['action_id'],execution_id=self.f.owner,observed_at=utc_now(),
            save_all_click_count=1,save_all_invocation_attempted=True,failure_boundary='NONE',folder_chooser_appeared=True,download_started=True,
            provenance='external fixture provider; no real GUI')
        chooser=dict(action_id=action['action_id'],session_id=self.f.owner,destination=action['destination'],full_path=action['destination'],
            leaf=Path(action['destination']).name,confirmation_attempts=1)
        return evidence,chooser
    def verification_io(self):
        def wait(seconds):self.now+=seconds
        return dict(clock=lambda:self.now,sleep=wait)
