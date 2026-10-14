PUBLIC REVIEW COPY — revision03 of a separately versioned PRIVATE candidate. This is a mechanical redaction/projection, not an unchanged revision01/revision02 private artifact. Those originals and the alias mapping remain preserved. Hidden root/group/fingerprint/config/state/evidence bindings are PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED; public JSON is not native schema/admission evidence.

Private candidate bindings: 940bd61bdecd136fa60e7d165b309ca24d4500edffee1b0f75281ec57c7484a5 (Plan); d8c21890706c981d4605b9d416cd1964b646e98ea9ef42a29895287df75a47ac (Contract).

Stable private historical references: VERIFIED_ALBUM_01=OPAQUE_FP_6b27490d9210bc6a0c7a9bf9049a5c0a2d901061d77a24e8697ec29a28ac11a0, VERIFIED_ALBUM_02=OPAQUE_FP_0a26366c9663e2bb14ee8d4a4a55d4404a8b30fc3d7c4af4838a2e5a2354e2a8. No raw fingerprints are published.

PUBLIC_PLAN_SHA256=90856548355809187e4b96d089f392ae2ba31326bbdf0b1d3a2b8f058d0ea64b
PUBLIC_CONTRACT_SHA256=dc8d5cb92cd0d752edfdcab3ab2db387568165d011affa8414d0d0e1c8dafd47

# PRIVATE revision03 — executable-scope design review packet

ROLE=SOL_XHIGH_PLANNER_ONLY
REVIEW_RESPONSE=CHANGES_ADDRESSED_FOR_REVIEW
PR_NUMBER=9
PRIVATE_PLAN_SHA256=940bd61bdecd136fa60e7d165b309ca24d4500edffee1b0f75281ec57c7484a5
PRIVATE_CONTRACT_SHA256=d8c21890706c981d4605b9d416cd1964b646e98ea9ef42a29895287df75a47ac

Original revision01 and existing revision02/mapping are preserved. This is a new candidate; no original frozen semantics/bytes were relabeled. Public copies are a mechanical redaction of this revision with explicit private-binding projections. No native receipt, Task, Issue, implementation, GUI consent or product PASS.

Selected CAP1_SEQUENTIAL. Existing API check actually exercised TWO distinct cap1 transactions with SAME workflow owner/session, A/B independent run/batch/action/lease/destination, finalize/read-back/CLOSED lease, stop/release, fresh next begin, old-intent refusal and third-scope quota refusal. Same owner W avoids revision02's unnecessary owner/session split. Current production still refuses new scope at cli.py:127–128 and150–152; lawful grant/source/menu/ledger adoption is proposed, not implemented. See Plan §2 exactly two-option comparison and contract for literal scope.

Current historical runs both have batch_id=null and remain duplicate barriers/immutable. Store counts all non-null batch intents across lifecycles; count is currently0. No offset, entitlement reset or quota algorithm change is proposed. New independent eligibility/grant is unresolved and cannot be inferred from that zero.

Minimum proposed changes: cli/service/store/adapter, five affected existing test files, one private bounded orchestration entry reusing existing supported bridge/retention. No config, schema, observations, Coordinator, Swift/Harness, ML08 or PR8 changes. Existing Coordinator remains a complete-catalog algorithm and is not the selected bounded entry.

B03=BLOCKED; hosted retries/native duplicate delivery UNKNOWN. B05=BLOCKED; manual review/native mapping unresolved. NATIVE_ADMISSION=NOT_GRANTED; GUI_CONSENT=NOT_GRANTED. The Chief GitHub comment is design review evidence only. The CUA documentation-only call selected an unavailable browser; it returned App signatures without acquiring LINE or reading its screen. It establishes API shape, not current permissions/producer/bridge/delivery.

## Actual focused checks

Python existing: 11/12 pass, one failure retained: loaded-intent test fixture CLI subprocess drops dependency PYTHONPATH and reports missing jsonschema. No package install/source/test fix. Direct existing Service probe separately proves loaded-intent refusal/resume zero calls. Node existing12/12 pass; misleading old 'only two clicks and timer' test actually asserts inter-click SCK capture/guard. That PASS is current behavior evidence, not accepted no-I/O compatibility.

Bounded fixture probe: two same-owner independent cap1 full filesystem/finalize/stop/release transitions, no replay, aggregate third-lifecycle refusal and exact global23 pool across A9+navigation1+four reserved scrolls+B9 including UNKNOWN/owner/run changes pass. Current missing-ledger reinitialization is a CONFIRMED GAP. Six synthetic scroll checks pass; current prepend/non-adjacent/AX-displacement gap is confirmed. Initial private probe import-path error was preserved and corrected only in the private probe. Prior revision02's unchanged-image scroll fixture failure remains historical; nothing was overwritten to hide it.

Static candidate checks separately pass exact receipt3 keys/event order against receipt2, cap1/23 slots, bounded-not-complete discovery, c6 zero retries and hard blockers. This is specification consistency only. No proposed slot/manifest/grant/receipt3 implementation was tested. These checks establish existing API facts and necessary design delta only. Fresh LINE E2E, GUI/menu calibration, A transaction, C1 scroll, B transaction and independent acceptance all NOT_RUN.

## Exact current local bindings

Aggregate Store.sources SHA256: cf5a67a959039f5e18c98c86df1337ba594c2b59c809110ab6f97c09fe0faf9e (ordered path + NUL + exact bytes + NUL). Hashing source does not independently establish hidden source provenance. Full affected code/interface excerpts follow, with exact original line anchors and excerpt SHA. Reviewer may inspect these public excerpts, not claim a remote rehash of full Mac-only files.

| Path | Bytes | SHA256 |
|---|---:|---|
| src/line_backup_acceptance/__init__.py | 85 | 5ae55afa11a74a856393b707db26b37202ad66d2142d1b56e02720f1a235a53b |
| src/line_backup_acceptance/__main__.py | 48 | 935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d |
| src/line_backup_acceptance/authority.py | 9441 | 7805ec0c53bca8991c3cc727339df4242d1e45a114b407913a2b0780614b6e7e |
| src/line_backup_acceptance/cli.py | 5587 | 832896eda31583199b192a0df51b921257fb7875835b1b502e476f9f1383d82f |
| src/line_backup_acceptance/common.py | 35808 | 2737d5c2febeeaf248b2d81e2e112ce0e99d48640e946bfa6dd8e71b5a2cf127 |
| src/line_backup_acceptance/project_binding.py | 27866 | f8894652fc9070416df5544b9573c26cee440300ca8a14f201f654f3886874f8 |
| src/line_backup_acceptance/status.py | 7937 | 1c8c27edf204d9243e8773cd830e16566269fb3814faa332dd8237c71587180e |
| src/line_backup_acceptance/transaction.py | 42494 | 0dd44fec005c70d6bb19436ed899e6c95d7b4d232dd83baa056732f4213a9da9 |
| src/line_backup_acceptance/verifier.py | 25377 | a07ffe450284ade34fce27f646bd4a0c37baccb65de5660e77aea3faf48b23b6 |
| src/line_backup_batch/__init__.py | 77 | ae2e6f7132820073b853877b5fbae4cbef55f9dcada8a6ceba0608d5e043fb83 |
| src/line_backup_batch/__main__.py | 47 | 79ee6f134c5c5193377cf9b189cbdcc3e2095e49ba9cec310114441c15a917c4 |
| src/line_backup_batch/cli.py | 19613 | f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6 |
| src/line_backup_batch/content.py | 4943 | 45837c8a84c22564efb668001fa0c7e9d443bec0b6fd3d9340e87bb6b7921205 |
| src/line_backup_batch/coordinator.py | 2552 | 285d0411d62f21133075e7bf203eca2376170b36faaf25a74edff0bb59060b8f |
| src/line_backup_batch/image_decode.swift | 4120 | 238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b |
| src/line_backup_batch/observations.py | 48734 | db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587 |
| src/line_backup_batch/schema.py | 2623 | d400cb0e5cdee4a0f0ce555e3222a590093c2dcaae9f10f464e205b9d1da3302 |
| src/line_backup_batch/service.py | 45295 | 54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6 |
| src/line_backup_batch/state_v3.schema.json | 33379 | d30ff068623f7dc6c9988387935beabbd5347e4b3a5e2c3a784daf8197db2a37 |
| src/line_backup_batch/store.py | 24794 | f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc |
| scripts/line_backup_cua_adapter.mjs | 44833 | d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f |
| config/line_backup_config.json | 384 | <PRIVATE_CONFIG_SHA256_NOT_EXTERNALLY_VERIFIED> |
| state/backup_state.json | 252115 | <PRIVATE_STATE_SHA256_NOT_EXTERNALLY_VERIFIED> |
| state/run_log.md | 14736 | <PRIVATE_RUN_LOG_SHA256_NOT_EXTERNALLY_VERIFIED> |
| tests/test_batch_authority.py | 14930 | e7adfff030b5105cf342b8f0bc1af72014eb6ab449e1ed600600423450f358e5 |
| tests/test_batch_lifecycle.py | 2256 | aeeedbf61bf29a80ee6529628223dce4c1c01783f6da6c64b01e81242f11011b |
| tests/test_batch_observations.py | 18502 | 92defeef97b5d27c79c83ad3c9fdbb4c26ddbef55f0f0eb4f6fe4f2b898fb222 |
| tests/test_cua_adapter.mjs | 18529 | 0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd |
| tests/test_batch_coordinator.py | 20939 | 7374c6e253dd059767614581b0bdc39d0063f234b99c8339ed2d5c6f7f86b4c5 |

## Source/interface proof

### begin needs clear lifecycle

src/line_backup_batch/service.py:59–72; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=438d65fbe363ff5e89252775a957bd4844431be4fe03c7f19aeb8119a9f8bb05.

```python
    def begin(self,expected,mode,limit):
        require(mode in ('catalog_only','backup_batch') and integer(limit),'INVALID_BATCH_SCOPE')
        require(limit==0 if mode=='catalog_only' else limit>0,'INVALID_BATCH_SCOPE')
        batch_id='BATCH-'+uuid.uuid4().hex
        def acquire(cfg,s):
            require(s['active_batch'] is None and s['active_writer_id'] is None and s['context_lock'] is None,'BATCH_BUSY')
            require(all(r['workflow_outcome']=='VERIFIED' or (r['workflow_outcome']=='SAFE_ABORT' and r['intent'] is None
                and r['manual_reconciliation_required'] is False) for r in s['runs']),'UNRESOLVED_HISTORY')
            s['active_batch']=dict(batch_id=batch_id,owner_execution_id=self.owner,group_key=cfg['group_key'],mode=mode,
                phase='CATALOG',policy_version=POLICY,config_sha256=expected['config_sha256'],source_sha256=expected['source_sha256'],
                created_at=utc_now(),authorized_new_download_limit=limit,configured_new_download_limit=cfg['max_albums_per_run'],
                new_transactions_reserved=0,manifest_reference=None,next_index=0,current_album_run_id=None,stop_reason=None)
            return dict(batch_id=batch_id,status='BATCH_OWNED')
        return self.store._update(expected,acquire,operation='begin')
```

### prepare min-cap and fresh target

src/line_backup_batch/service.py:119–128; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=576c4f23131e8756e464615c4d20b40250ece1d4f3bed57c62c2885ef0db0184.

```python
            b=self.batch(snap['state']);m=self.manifest(b,reader,snap['config'])
            require(b['mode']=='backup_batch' and b['phase'] in ('ADMITTED','RUNNING'),'CATALOG_DISPATCH_REFUSED')
            require(b['current_album_run_id'] is None,'ALBUM_BUSY')
            index=b['next_index'];require(index<len(m['identities']),'MANIFEST_END')
            target=m['identities'][index];decision=self.eligible(snap['state'],target)
            click=None
            if decision=='PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION':
                require(b['new_transactions_reserved']<min(b['authorized_new_download_limit'],b['configured_new_download_limit']),'LIMIT_REACHED')
                click=card_target(reader,observation,snap['config'],target,m['session_id'])
            else:require(decision=='SKIP_VERIFIED',decision)
```

### intent once, retry false and quota

src/line_backup_batch/service.py:272–289; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=235359cf704e897bc9cd982e90812e243cf60e346cdea1e0c386f0bb4020871a.

```python
        def intent(cfg,s):
            b,r=self.run(s);require(r['phase']=='SAVE_ALL_CALIBRATION' and r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            require(b['new_transactions_reserved']<min(b['authorized_new_download_limit'],b['configured_new_download_limit']),'LIMIT_REACHED')
            require(content.inventory(self.store.root,r['destination'])==[],'DESTINATION_NONEMPTY')
            previous=strict_json(r['checkpoint']['evidence'].encode(),'INVALID_CALIBRATION_RECORD')
            require(previous['closure']['layout_key']==fresh['layout_key'] and previous['closure']['pid']==fresh['pid']
                and previous['closure']['window_id']==fresh['window_id'],'CALIBRATION_LAYOUT_DRIFT')
            cal=previous['calibration'];action='ACTION-'+uuid.uuid4().hex
            r['intent']=dict(action_id=action,committed_at=utc_now(),owner_execution_id=self.owner,group_key=cfg['group_key'],
                fingerprint=r['fingerprint'],destination=r['destination'],calibration=cal,save_all_retry_allowed=False,
                dispatch_outcome='NOT_ATTEMPTED',trigger_outcome='NOT_APPLICABLE')
            r['intent_state']='INTENT_COMMITTED';b['new_transactions_reserved']+=1
            self.event(r,'SAVE_ALL_INTENT_COMMITTED',dict(fresh=fresh,action_id=action))
            return dict(status='ORIGINAL_INTENT_COMMITTED',run_id=r['run_id'],action_id=action,owner=self.owner,
                fingerprint=r['fingerprint'],destination=r['destination'],frame_id=fresh['frame_id'],session_id=m['session_id'],
                ellipsis=cal['ellipsis'],save_all=cal['save_all_point'],dispatch_authorized=not self.store.fixture,
                fixture=self.store.fixture)
        result=self.store._update(expected,intent,operation='intent');result['new_intent']=True
```

### VERIFIED owner/context release

src/line_backup_batch/service.py:524–531; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=aa97a49278a9ad6b0a4b48130a74668236387c2fcaaf4f619331f5e00da1ff92.

```python
            current['verification']=verification;current['workflow_outcome']='VERIFIED';current['stop_reason']='COMPLETED'
            event=dict(phase='VERIFIED',at=utc_now(),evidence=reference)
            current['events'].append(event);current['phase']='VERIFIED';current['checkpoint']=event
            s['verified_albums'].append(dict(group_key=current['group_key'],fingerprint=current['fingerprint'],
                verified_run_id=current['run_id'],destinations=[current['destination']],source_kind='filesystem_verification',evidence=reference))
            s['active_writer_id']=None;s['context_lock']=None;b['current_album_run_id']=None;b['next_index']+=1
            return dict(status='VERIFIED',run_id=current['run_id'],fingerprint=current['fingerprint'],verification_reference=vref)
        outcome=self.store._update(expected,finish,operation='finalize')
```

### lease CLOSED after readback

src/line_backup_batch/service.py:534–548; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=899683f6715be025a409aa15f25f66705953611d321e9ab4109a36b17d735cf9.

```python
        try:
            post=content.inventory(self.store.root,r['destination'])
            require(post==verification['inventory'],'FINALIZE_READBACK_UNCERTAIN')
        except Exception as exc:
            failure=getattr(exc,'code',None) or str(exc)
            self.publish('finalize-drift-'+r['run_id']+'.json',dict(version='line-backup-finalize-drift-1',run_id=r['run_id'],
                state_committed=True,state_revision=outcome['receipt']['revision'],
                pre_inventory_sha256=sha(json_bytes(verification['inventory'])),post_inventory_sha256=None,
                at=utc_now(),failure=failure))
            self.publish('lease-close-'+r['run_id']+'.json',dict(version='line-backup-lease-close-1',run_id=r['run_id'],
                state='UNVERIFIED',state_revision=outcome['receipt']['revision'],at=utc_now()))
            raise AcceptanceError('FINALIZE_READBACK_UNCERTAIN',str(exc),4) from exc
        self.publish('lease-close-'+r['run_id']+'.json',dict(version='line-backup-lease-close-1',run_id=r['run_id'],
            state='CLOSED',post_inventory_sha256=sha(json_bytes(post)),state_revision=outcome['receipt']['revision'],at=utc_now()))
        return outcome
```

### stop empty lifecycle and release barrier

src/line_backup_batch/service.py:550–561; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=933cfb0c4c9b326cfd0cc29fc5840d4403dfd8f3a0ac544168c0926af0744c41.

```python
    def stop(self,expected,reason):
        def stop(cfg,s):
            b=self.batch(s)
            if b['current_album_run_id'] is not None:
                _,r=self.run(s);r['workflow_outcome']='SAFE_ABORT';r['stop_reason']=reason
                r['manual_reconciliation_required']=r['intent'] is not None
                r['reconciliation_reason']='Stopped with non-retryable intent; reconcile only.' if r['intent'] else None
                self.event(r,'SAFE_ABORT',dict(reason=reason))
                s['active_writer_id']=None;s['context_lock']=None;b['current_album_run_id']=None
            b['phase']='STOPPED';b['stop_reason']=reason
            return dict(status='STOPPED',reason=reason,replay_allowed=False)
        return self.store._update(expected,stop,operation='stop')
```

### release then next lifecycle

src/line_backup_batch/service.py:593–603; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=84c985349a08beb15921db1c573843e8f095b4d04a704d59e0b0aea591baa68c.

```python
    def release(self,expected):
        def release(cfg,s):
            b=s['active_batch']
            require(b is not None and b['owner_execution_id']==self.owner and b['phase'] in ('STOPPED','COMPLETED'),
                'TERMINAL_BATCH_REQUIRED')
            require(b['current_album_run_id'] is None and s['active_writer_id'] is None and s['context_lock'] is None,'ALBUM_BUSY')
            require(all(run_barrier_ok(r) for r in s['runs']),'UNRESOLVED_BARRIER')
            result=dict(status='BATCH_RELEASED',batch_id=b['batch_id'],prior_phase=b['phase'],stop_reason=b['stop_reason'])
            s['active_batch']=None
            return result
        return self.store._update(expected,release,operation='release')
```

### first current new-scope entry blocker

src/line_backup_batch/cli.py:115–130; full source SHA256=f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6; exact excerpt SHA256=84ca1bcf35dbb8e597c255a96cbaa489f9434156b398490c7481405ace06e876.

```python
def authorize(root,path,fixture,operation):
    grant=load_input(root,path)
    expected_keys=GRANT_V1_KEYS if fixture else GRANT_V2_KEYS
    expected_version='line-batch-execution-grant-1' if fixture else 'line-batch-execution-grant-2'
    require(isinstance(grant,dict) and set(grant)==expected_keys and grant['grant_version']==expected_version,'INVALID_GRANT')
    require(isinstance(grant.get('operations'),list),'GRANT_OPERATIONS')
    require(grant['project_root']==root and grant['fixture'] is fixture and operation in grant['operations'],'GRANT_SCOPE')
    require(isinstance(grant['task_id'],str) and grant['task_id'].startswith('TASK-')
        and isinstance(grant['owner'],str) and grant['owner'] and isinstance(grant['artifact_dir'],str),
        'GRANT_SCOPE')
    if fixture:
        require(grant['artifact_dir']=='harness-development/evidence','GRANT_SCOPE')
    else:
        require(grant['artifact_dir']==CONTINUATION,'GRANT_SCOPE')
    require(isinstance(grant['operations'],list) and len(grant['operations'])==len(set(grant['operations']))
        and set(grant['operations'])<=OPERATIONS and 'mutate' not in grant['operations'],'GRANT_OPERATIONS')
```

### pinned grant binding

src/line_backup_batch/cli.py:149–152; full source SHA256=f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6; exact excerpt SHA256=d7f37f30f19e973d743d1fafac5fe77573403d15938768700a1601636b113f47.

```python
            from .observations import artifact
            require(grant['contract_path']==CONTRACT_PATH and grant['contract_sha256']==CONTRACT_SHA256
                and grant['native_binary_sha256']==NATIVE_BINARY_SHA256 and grant['gui_ledger']==GUI_LEDGER_PATH,
                'GRANT_LIVE_BINDING_REQUIRED')
```

### cross-lifecycle intent count

src/line_backup_batch/store.py:129–140; full source SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc; exact excerpt SHA256=5253063a321341129ac1e3e0df8b7a4ff7993066d664fa2b3bf217998acede4c.

```python
def enforce_grant_quota(grant,operation,state):
    """Conservatively count persisted original intents across separate lifecycle batches."""
    used=sum(1 for item in state['runs'] if item.get('batch_id') is not None and item.get('intent') is not None)
    allowance=min(grant['album_quota'],grant['save_all_dispatch_limit'],grant['chooser_confirmation_limit'])
    if operation=='begin':
        batch=state['active_batch']
        require(batch is not None and batch.get('owner_execution_id')==grant['owner']
            and batch.get('authorized_new_download_limit',0)<=grant['lifecycle_album_limit']
            and batch.get('authorized_new_download_limit',0)<=max(0,allowance-used),'GRANT_ALBUM_QUOTA')
    if operation=='intent':
        require(used<=allowance,'GRANT_DISPATCH_QUOTA')
    return used
```

### CAS and operation-scoped authority

src/line_backup_batch/store.py:203–218; full source SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc; exact excerpt SHA256=a42cec880d68d532ea32c1bd92798f7302c159fd6e175fb8dac1fc9299931bf9.

```python
    def _update(self,expected,transform,*,operation=None,migration=False,snapshot_path=None,fault=None):
        """Internal operation-scoped commit primitive; public callers use Service transitions."""
        grant=None
        require(operation in TRANSITION_FIELDS,'OPERATION_REQUIRED')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            require(migration==(operation=='migrate'),'OPERATION_MISMATCH')
            grant=authorize(self.root,self.authorization_path,False,operation)
        with self.guard() as (r,parent,check_lock,lock_identity):
            cfg,before,actual,raw,_=self.load(r)
            require(actual==expected,'STALE_CAS')
            require(before['schema_version']==(2 if migration else 3),'STATE_VERSION_READ_ONLY')
            if grant is not None:
                grant_raw,_=r.read(self.authorization_path,'GRANT_DRIFT')
                require(strict_json(grant_raw,'INVALID_GRANT')==grant,'GRANT_DRIFT')
```

### fsync atomic replacement exact readback

src/line_backup_batch/store.py:260–277; full source SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc; exact excerpt SHA256=cc4419a8d8d856beef28aedd7a86ca1aac4a12b1f832292b0091159af7f783ff.

```python
                owner=self._temp_owner(fd)
                self._write(fd,body);os.fsync(fd)
                if fault=='BEFORE_REPLACE':raise AcceptanceError('WRITE_BEFORE_REPLACE','fixture fault',4)
                check_lock()
                require(ProjectReader.ident(os.stat('backup_state.json',dir_fd=parent,follow_symlinks=False))==tuple(actual['state_identity']),
                    'STATE_INODE_DRIFT')
                self._require_temp_owner(parent,temporary,owner)
                os.replace(temporary,'backup_state.json',src_dir_fd=parent,dst_dir_fd=parent);replaced=True
                os.fsync(parent)
                if fault=='AFTER_REPLACE':raise AcceptanceError('READBACK_UNCERTAIN','fixture fault',4)
                check_lock()
                back=ProjectReader(self.root)
                try:
                    written,_=back.read(STATE)
                    require(written==body,'READBACK_UNCERTAIN')
                    _,_,receipt,_,_=self.load(back)
                finally:back.close()
                return dict(receipt=receipt,result=result,lock_identity=lock_identity,new_intent=False)
```

### missing-ledger initialization gap

src/line_backup_batch/store.py:353–361; full source SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc; exact excerpt SHA256=d5e112ef4b23eb025e58f1329db0a22a387f69c6a8bc506c301508f713580592.

```python
    def _ledger_open(self,r,grant):
        path=self.ledger_path(grant);cap=grant['reversible_gui_invocation_limit']
        ledger=self._ledger_read(r,path)
        if ledger is None:
            ledger=dict(version=GUI_LEDGER_VERSION,task_id=grant['task_id'],cap=cap,entries=[])
        require(isinstance(ledger,dict) and set(ledger)=={'version','task_id','cap','entries'}
            and ledger['version']==GUI_LEDGER_VERSION and isinstance(ledger['entries'],list)
            and ledger['task_id']==grant['task_id'] and ledger['cap']==cap,'GUI_LEDGER_DRIFT')
        return path,ledger,cap
```

### global all-entry sum no refund

src/line_backup_batch/store.py:375–402; full source SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc; exact excerpt SHA256=f8e01c74bb846124f3472ca0ea122212894a48fafba7fc92d66707f45e762509.

```python
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            path,ledger,cap=self._ledger_open(r,grant)
            used=sum(entry['count'] for entry in ledger['entries'])
            require(used+count<=cap,'GUI_LEDGER_EXHAUSTED')
            entry=dict(seq=len(ledger['entries'])+1,id=uuid.uuid4().hex,kind=kind,count=count,run_id=run_id,
                owner=owner,at=utc_now(),state='RESERVED',outcome=None,consumed_at=None)
            ledger['entries'].append(entry)
            self._ledger_write(r,path,ledger)
            return dict(reservation=dict(id=entry['id'],kind=kind,count=count),used=used+count,cap=cap)

    def consume_gui(self,grant,data):
        """Mark one reservation consumed; a consumed or unknown reservation never refunds."""
        reservation_id=data.get('reservation_id');outcome=data.get('outcome')
        require(isinstance(reservation_id,str) and reservation_id,'GUI_LEDGER_RESERVATION')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            live=authorize(self.root,self.authorization_path,False,'gui_consume')
            require(live==grant,'GRANT_DRIFT')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            path,ledger,cap=self._ledger_open(r,grant)
            entry=next((item for item in ledger['entries'] if item['id']==reservation_id),None)
            require(entry is not None and entry['owner']==grant['owner'],'GUI_LEDGER_UNKNOWN_RESERVATION')
            require(entry['state']=='RESERVED','GUI_LEDGER_STATE')
            entry['state']='CONSUMED';entry['consumed_at']=utc_now()
            entry['outcome']=json.dumps(outcome,ensure_ascii=False,sort_keys=True) if outcome is not None else None
```

### current complete catalog requirement

src/line_backup_batch/observations.py:609–636; full source SHA256=db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587; exact excerpt SHA256=566345a17f4015ad49ec9e80dc65578157829cc320c81921d29087ca90d1c6f8.

```python
def catalog(reader,records,cfg,session,*,now=None):
    require(isinstance(records,list) and records,'EMPTY_CATALOG')
    identities=[];prior=None;context=None;seen_dates={}
    for i,record in enumerate(records):
        frame(reader,record,cfg,session=session,now=now,max_age=600)
        require(record['surface']=='ALBUMS' and record['cards'],'CATALOG_SURFACE')
        current=(record['session_id'],record['group_key'],record['pid'],record['window_id'],record['layout_key'])
        require(context is None or context==current,'COLLECTION_IDENTITY_DRIFT');context=current
        keys=[tuple(c['fingerprint'].values()) for c in record['cards']]
        if prior is not None:
            require(keys!=prior,'NO_COLLECTION_PROGRESS')
            require(any(prior[-k:]==keys[:k] for k in range(1,min(len(prior),len(keys))+1)),
                'COLLECTION_COVERAGE_GAP')
        for c in record['cards']:
            identity=c['fingerprint'];datekey=(identity['start_date'],identity['end_date'])
            if identity in identities:
                require(prior is not None and tuple(identity.values()) in prior,'REAPPEARED_AMBIGUOUS_IDENTITY')
            require(datekey not in seen_dates or seen_dates[datekey]==identity,'ALBUM_COUNT_DRIFT')
            seen_dates[datekey]=identity
            if identity not in identities:identities.append(identity)
        boundary=record['boundary']
        require(isinstance(boundary,dict) and set(boundary)=={'top','bottom','evidence'},'BOUNDARY_UNKNOWN')
        require(type(boundary['top']) is bool and type(boundary['bottom']) is bool,'BOUNDARY_UNKNOWN')
        artifact(reader,boundary['evidence'])
        if i==0:require(boundary['top'],'TOP_NOT_PROVEN')
        if i==len(records)-1:require(boundary['bottom'],'BOTTOM_NOT_PROVEN')
        prior=keys
    return identities
```

### actual retained frame grounding

src/line_backup_batch/observations.py:359–381; full source SHA256=db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587; exact excerpt SHA256=73962c51fb894507cd7dca684ffdb5e68a9a8e04ec4f401c482771d4f8b6a333.

```python
    required={'frame','frame_id','session_id','group_key','surface','captured_at','provider','layout_key',
        'window_id','pid','width','height','mapping','cards','boundary','editable_focus','occlusion'}
    require(isinstance(record,dict) and set(record)==required,'INVALID_OBSERVATION')
    require(record['session_id']==session and record['group_key']==cfg['group_key'],'CONTEXT_MISMATCH')
    require(record['provider']=='HOSTED_CUA' and record['surface'] in ('ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER'),'SURFACE_MISMATCH')
    focus_ok=record['editable_focus']=='NONE' or (allow_high_editable and record['editable_focus']=='HIGH_EDITABLE')
    require(record['occlusion']=='CLEAR' and focus_ok,'INPUT_SAFETY_UNKNOWN')
    require(integer(record['pid'],1) and integer(record['window_id'],1) and isinstance(record['layout_key'],str) and record['layout_key'],'WINDOW_IDENTITY')
    instant=dt.datetime.fromisoformat(record['captured_at'].replace('Z','+00:00'))
    require(instant.tzinfo is not None,'INVALID_CAPTURE_TIME')
    age=(dt.datetime.now(dt.timezone.utc) if now is None else now)-instant
    require(age.total_seconds()>=0 and (max_age is None or age.total_seconds()<=max_age),'STALE_OBSERVATION')
    raw=artifact(reader,record['frame']);require(record['frame_id']==sha(raw),'FRAME_ID_MISMATCH')
    size=image_size(raw);require(size==(record['width'],record['height']),'FRAME_DIMENSIONS_MISMATCH')
    mapping=record['mapping']
    require(isinstance(mapping,dict) and set(mapping)=={'space','uncertainty','evidence','frame_id','layout_key','sck_support'},'MAPPING_UNKNOWN')
    require(mapping['space']=='CUA_CAPTURE_PIXELS' and mapping['frame_id']==record['frame_id'] and mapping['layout_key']==record['layout_key'],'MAPPING_MISMATCH')
    require(type(mapping['uncertainty']) in (int,float) and math.isfinite(mapping['uncertainty']) and mapping['uncertainty']>=2,'MAPPING_UNKNOWN')
    artifact(reader,mapping['evidence'])
    support=_support(reader,mapping['sck_support'],record,cfg,now=(dt.datetime.now(dt.timezone.utc) if now is None else now),max_age=max_age)
    require(mapping['uncertainty']>=support['sidecar']['uncertainty_px'],'MAPPING_UNCERTAINTY_UNDERSTATED')
    fixture_root=Path(reader.root).is_relative_to(Path(__file__).resolve().parents[2]/'harness-development') and '/fixtures/' in reader.root
    if not fixture_root:_grounding_evidence(reader,mapping['evidence'],record,support)
```

### current same-window assumption requires actual detail lineage

scripts/line_backup_cua_adapter.mjs:194–214; full source SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f; exact excerpt SHA256=d0ba74bfa433e2be040c09db2dbd629a07e5d2c37f35f81168cb715d89918960.

```javascript
  async function openAlbum(prepared) {
    fresh(prepared.frame_id);requireFact(point(prepared.click),'INVALID_CARD_POINT');
    const before=latest.observation;
    requireFact(before?.surface==='ALBUMS','ALBUM_OPEN_SURFACE_UNKNOWN');
    const reservation = await reserveGui('album_open',1,prepared.run_id);
    record('ALBUM_OPEN_INVOCATION',{runId:prepared.run_id});
    latest = null;
    try {await app.click(prepared.click); await app.getAXState({emit:false});}
    catch(e) {stopped=true;throw e;}
    await consumeGui(reservation,'RETURNED');
    try {
      const after=await observe();
      requireFact(after.surface==='ALBUM_DETAIL' && after.frame_id!==before.frame_id
        && after.session_id===before.session_id && after.group_key===before.group_key
        && after.pid===before.pid && after.window_id===before.window_id,
        'ALBUM_OPEN_NOT_VERIFIED');
      record('ALBUM_DETAIL_OBSERVED',{frameId:after.frame_id});
      return after;
    } catch(error) {
      stopped=true;latest=null;record('ALBUM_OPEN_UNVERIFIED',{message:String(error)});
      throw error;
```

### current scroll comparison gaps

scripts/line_backup_cua_adapter.mjs:46–76; full source SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f; exact excerpt SHA256=a8cfb56b587370117b3504f4016c52e172203ea91553fd0629fd084eabba9b99.

```javascript
// This check runs on two *actual retained LINE observations* after one reserved
// native scroll. It does not dispatch GUI events and accepts no fixture-only PASS.
export function verifyAlbumScroll(before, after) {
  requireFact(before?.surface==='ALBUMS' && after?.surface==='ALBUMS'
    && before.session_id===after.session_id && before.group_key===after.group_key
    && before.pid===after.pid && before.window_id===after.window_id
    && before.layout_key===after.layout_key, 'SCROLL_CONTEXT_DRIFT');
  requireFact(hex64(before.frame_id) && hex64(after.frame_id)
    && before.frame_id!==after.frame_id, 'SCROLL_NO_VISUAL_CHANGE');
  requireFact(Array.isArray(before.cards) && Array.isArray(after.cards),
    'SCROLL_CARD_EVIDENCE_REQUIRED');
  const complete = observation => observation.cards.filter(card=>
    card?.fully_visible===true && typeof card?.fingerprint?.start_date==='string'
    && typeof card?.fingerprint?.end_date==='string'
    && Number.isInteger(card?.fingerprint?.expected_images)
    && card.fingerprint.expected_images>0
  ).map(card => JSON.stringify([card.fingerprint.start_date,
    card.fingerprint.end_date, card.fingerprint.expected_images]));
  const previous=complete(before), current=complete(after);
  requireFact(previous.length>0 && current.length>0
    && new Set(previous).size===previous.length
    && new Set(current).size===current.length, 'SCROLL_CARD_EVIDENCE_REQUIRED');
  const previousSet=new Set(previous);
  const shared=current.filter(id=>previousSet.has(id));
  const fresh=current.filter(id=>!previousSet.has(id));
  requireFact(shared.length>0, 'SCROLL_NO_CARD_OVERLAP');
  const indices=shared.map(id=>previous.indexOf(id));
  requireFact(indices.every((value,i)=>i===0||value>indices[i-1]),
    'SCROLL_CARD_ORDER_DRIFT');
  requireFact(fresh.length>0, 'SCROLL_NO_NEW_FULL_CARD');
  return Object.freeze({overlap_count:shared.length,new_full_card_count:fresh.length});
```

### actual capture and AX retention

scripts/line_backup_cua_adapter.mjs:152–178; full source SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f; exact excerpt SHA256=b25943ef527e23aa9af179f5554a632fc90b9642f52c41646a0e7548e59e0649.

```javascript
    const rawCapture = await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
    const requestEndedAtMonotonic = clock();
    const requestEndedAtUtc = new Date().toISOString();
    requireFact(Number.isFinite(requestStartedAtMonotonic) && Number.isFinite(requestEndedAtMonotonic)
      && requestEndedAtMonotonic >= requestStartedAtMonotonic && typeof rawCapture?.state === 'string',
    'CAPTURE_INCOMPLETE');
    const screenshot = normalizeScreenshotBytes(rawCapture.screenshot);
    const capture = Object.freeze({...rawCapture,screenshot});
    const frameId = sha(screenshot);
    const monotonicInterval = Object.freeze({start_ms:requestStartedAtMonotonic,end_ms:requestEndedAtMonotonic,
      duration_ms:requestEndedAtMonotonic-requestStartedAtMonotonic});
    const saved = await retain({screenshot,ax:capture.state,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    verifyFrameReference(saved,frameId,screenshot.byteLength);
    // The retained CUA frame is available to native-context/OCR readers here.
    // Keep capturedAt anchored to the original CUA request start; persistence
    // and OCR work must never make the frame appear newer.
    const afterContext = hasCaptureContextHooks ? await afterCapture({capture,saved,frameId,sessionId,
      sourceBinding:beforeContext,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval}) : null;
    const sourceBinding = hasCaptureContextHooks ? Object.freeze({before:beforeContext,after:afterContext}) : null;
    const capturedContext = sourceBinding;
    const observation = await classify({capture,saved,frameId,sessionId,sourceBinding,capturedContext,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    requireFact(observation.frame_id === frameId && observation.session_id === sessionId,'CLASSIFIER_FRAME_MISMATCH');
    // The capture interval starts before CUA and never renews during persistence/OCR.
    latest = Object.freeze({frameId,at:requestStartedAtMonotonic,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval,sourceBinding,capturedContext,observation,saved,capture});
```

### current no-replay memory permit

scripts/line_backup_cua_adapter.mjs:273–300; full source SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f; exact excerpt SHA256=3a689e751ff134695050698f2df94010db5d35c55dafd4590aa12e113d95a971.

```javascript
  async function originalIntent({receiptToken,freshObservation}) {
    fresh(freshObservation.frame_id);
    const committed = await bridge('intent',{expected_token:receiptToken,data:{fresh:freshObservation}});
    requireFact(committed.new_intent === true && committed.result?.status === 'ORIGINAL_INTENT_COMMITTED'
      && committed.result?.dispatch_authorized === true && committed.result?.fixture === false,
      'LIVE_DISPATCH_AUTHORITY_REQUIRED');
    fresh(freshObservation.frame_id);
    requireFact(committed.result.frame_id === latest.frameId && committed.result.session_id === sessionId,
      'INTENT_FRAME_MISMATCH');
    requireFact(latest.saved && typeof latest.saved.path === 'string' && Number.isInteger(latest.saved.bytes)
      && hex64(latest.saved.sha256) && latest.saved.sha256 === latest.frameId,'CUA_FRAME_REFERENCE_REQUIRED');
    requireFact(typeof latest.observation.captured_at === 'string','CUA_CAPTURE_TIME_REQUIRED');
    const token = Object.freeze({});
    permits.set(token,Object.freeze({result:committed.result,receiptToken:committed.receipt_token,
      frameId:latest.frameId,issuedAt:clock(),deadline:latest.at+5000,
      originalContext:Object.freeze({frame_id:latest.frameId,pid:latest.observation.pid,
        window_id:latest.observation.window_id,layout_key:latest.observation.layout_key}),
      cuaFrame:Object.freeze({path:latest.saved.path,bytes:latest.saved.bytes,sha256:latest.saved.sha256}),
      cuaCapturedAt:latest.observation.captured_at}));
    return token;
  }
  async function originalAtomicDispatch(token,{captureMenuSupport,guardMenu}={}) {
    const permit=permits.get(token);requireFact(permit,'NO_ORIGINAL_PERMISSION');
    // Consume before the first call. Throw/timeout/crash never leaves a reusable token.
    permits.delete(token);
    requireFact(typeof captureMenuSupport==='function' && typeof guardMenu==='function','MENU_GUARD_REQUIRED');
    if (requireV2) requireFact(typeof classifyChooser==='function' && chooser,'V2_CHOOSER_REQUIRED');
    fresh(permit.frameId);
```

### current in-pair SCK side effects

scripts/line_backup_cua_adapter.mjs:304–335; full source SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f; exact excerpt SHA256=429b66ae83ddc22e690192d697c77b86fc4045bf66cd06dc2dee15a02c6452b9.

```javascript
    const reservation = await reserveGui('dispatch_inputs',2,action.run_id);
    record('ELLIPSIS_INVOCATION',{actionId:action.action_id});
    latest=null;
    let support=null,guard=null;
    try {
      await app.click(action.ellipsis);
      record('ELLIPSIS_RETURNED');
      await wait(menuWaitMs);
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_MENU_CAPTURE');
      support=await captureMenuSupport(Object.freeze({action,pairFrameId:permit.frameId,sessionId,
        requestedAt:clock(),cuaFrame:permit.cuaFrame,cuaCapturedAt:permit.cuaCapturedAt}));
      requireFact(support?.provider==='SCREEN_CAPTURE_KIT' && support?.pairFrameId===permit.frameId
        && hex64(support?.popupFrameId) && support.popupFrameId!==permit.frameId && support?.sessionId===sessionId
        && typeof support?.reference?.path==='string' && support.reference.path.startsWith('harness-development/')
        && Number.isInteger(support.reference.bytes) && support.reference.bytes>0
        && hex64(support.reference.sha256),'SCK_SUPPORT_REQUIRED');
      guard=await guardMenu(Object.freeze({action,support,pairFrameId:permit.frameId,sessionId}));
      requireFact(guard?.verdict==='PASS' && guard?.provider==='SCREEN_CAPTURE_KIT'
        && guard?.pairFrameId===permit.frameId && guard?.popupFrameId===support.popupFrameId
        && guard?.supportSha256===support.reference.sha256
        && Array.isArray(guard?.actionPoint) && guard.actionPoint.length===2
        && guard.actionPoint[0]===action.save_all[0] && guard.actionPoint[1]===action.save_all[1],
        'SCK_MENU_GUARD_REFUSED');
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_SAVE_ALL');
      record('SCK_MENU_GUARD_PASS',{support:support.reference,guard});
      record('SAVE_ALL_INVOCATION',{actionId:action.action_id});
      await app.click(action.save_all);
      record('SAVE_ALL_RETURNED');
      await consumeGui(reservation,'RETURNED');
    } catch(error) {
      stopped=true;record('DISPATCH_UNCERTAIN',{message:String(error)});throw error;
    }
```

### current receipt2 exact event route

src/line_backup_batch/service.py:15–23; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=821f265770a7c81207bd318b9e5aa9ee02bc52597ca38c29489c122a2432b160.

```python
DISPATCH_RECEIPT_V1_KEYS={'version','run_id','action_id','execution_id','session_id','pair_frame_id','popup_frame_id',
    'support','guard','reservations','events','chooser','download_started','save_all_click_count','cease_input'}
DISPATCH_RECEIPT_V2_KEYS=(DISPATCH_RECEIPT_V1_KEYS-{'download_started'})|{'chooser_phases','confirmation_frame',
    'confirmation_point','download_evidence'}
DISPATCH_EVENT_ORDER_V1=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
    'SAVE_ALL_RETURNED','CONFIRM_INVOCATION','CEASE_INPUT_AFTER_DOWNLOAD_START']
DISPATCH_EVENT_ORDER_V2=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
    'SAVE_ALL_RETURNED','CHOOSER_APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED',
    'CONFIRM_INVOCATION','CONFIRM_ATTEMPTED','DOWNLOAD_EVIDENCE_OBSERVED','CEASE_INPUT_AFTER_DOWNLOAD_START']
```

### current receipt2 phase-age blocker

src/line_backup_batch/service.py:339–350; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=322b2ddeb79c253937d80d935c091c6aa27ce92df4d1a4da51be9d139ba8a771.

```python
                        event_time=phase_events[phase_event_names[index]]
                        try:
                            captured_time=dt.datetime.fromisoformat(envelope['frame']['captured_at'].replace('Z','+00:00'))
                        except (AttributeError,TypeError,ValueError):
                            raise AcceptanceError('CHOOSER_PHASE_TIME','chooser frame time is invalid',4)
                        require(captured_time.tzinfo is not None and event_time.tzinfo is not None
                            and captured_time<=event_time<=actual_now and (event_time-captured_time).total_seconds()<=5
                            and (actual_now-captured_time).total_seconds()<=5,
                            'CHOOSER_PHASE_STALE')
                        chooser_observation(reader,envelope,self.store.snapshot()['config'],session=receipt_data['session_id'],
                            owner=self.owner,run_id=receipt_data['run_id'],action_id=receipt_data['action_id'],
                            destination=receipt_data['chooser']['destination'],previous=previous,now=actual_now)
```

### current receipt2 popup/guard demands

src/line_backup_batch/service.py:378–400; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=922500a4e07f60fefbf4354ec3b21a037046446feb0a4b6cc0767eca030821e5.

```python
                require(receipt_data['run_id'] and receipt_data['action_id'] and receipt_data['execution_id']==self.owner
                    and receipt_data['session_id'],'RECEIPT_IDENTITY')
                support=strict_json(artifact(reader,receipt_data['support']),'INVALID_SCK_SUPPORT')
                require(support.get('frame_id')==receipt_data['pair_frame_id']
                    and support.get('session_id')==receipt_data['session_id'],'RECEIPT_SUPPORT_BINDING')
                popup_raw=artifact(reader,support.get('sck_frame'))
                require(sha(popup_raw)==receipt_data['popup_frame_id']
                    and receipt_data['popup_frame_id']!=receipt_data['pair_frame_id'],'RECEIPT_POPUP_BINDING')
                guard=receipt_data['guard']
                require(isinstance(guard,dict) and guard.get('verdict')=='PASS' and guard.get('provider')=='SCREEN_CAPTURE_KIT'
                    and guard.get('pairFrameId')==receipt_data['pair_frame_id']
                    and guard.get('popupFrameId')==receipt_data['popup_frame_id']
                    and guard.get('supportSha256')==receipt_data['support']['sha256'],'RECEIPT_GUARD_UNPROVEN')
                events=receipt_data['events']
                allowed_event_shapes=({'event'},{'event','at'}) if version=='cua-dispatch-receipt-1' else ({'event','at'},)
                require(isinstance(events,list) and all(isinstance(item,dict) and set(item) in allowed_event_shapes
                    and isinstance(item.get('event'),str) for item in events),'RECEIPT_EVENTS')
                names=[item['event'] for item in events]
                expected_names=event_order
                if version=='cua-dispatch-receipt-1':
                    require(set(names)<=set(event_order)|{'ALBUM_OPEN_INVOCATION'},'RECEIPT_EVENTS')
                    names=[name for name in names if name!='ALBUM_OPEN_INVOCATION']
                require(names==expected_names,'RECEIPT_EVENT_ORDER')
```

### owner/session equality can stay

src/line_backup_batch/service.py:423–430; full source SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6; exact excerpt SHA256=c77980df847814e2e94d1fdc04054cc0151a1d73c459a43d7606ffc65e1b3343.

```python
            b,r=self.run(s);require(r['intent'] is not None and r['dispatch_evidence'] is None,'DISPATCH_ALREADY_RECORDED')
            d=copy.deepcopy(evidence)
            require(d['run_id']==r['run_id'] and d['action_id']==r['intent']['action_id'] and d['execution_id']==self.owner,'DISPATCH_IDENTITY')
            if receipt_data is not None:
                require(receipt_data['run_id']==r['run_id'] and receipt_data['action_id']==r['intent']['action_id']
                    and receipt_data['execution_id']==self.owner and receipt_data['session_id']==b['owner_execution_id'],'RECEIPT_IDENTITY')
                require(json_bytes(receipt_data['chooser'])==json_bytes(chooser),'RECEIPT_CHOOSER_MISMATCH')
                point=receipt_data['guard']['actionPoint']
```

### navigation-only return and scroll

scripts/line_backup_cua_adapter.mjs:598–631; full source SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f; exact excerpt SHA256=1c1ef4c5dc9bc9068707740ca832fa4cd8af16ff2dac732045daba9a31d729a2.

```javascript
  function fresh(frameId) {
    requireFact(latest&&latest.frameId===frameId&&clock()>=latest.started&&clock()-latest.started<=5000,
      'FRESH_CAPTURE_REQUIRED');
  }
  async function returnToAlbums(fromObservation,locateBack) {
    fresh(fromObservation.frame_id);requireFact(typeof locateBack==='function','BACK_LOCATOR_REQUIRED');
    const control=await locateBack(fromObservation);
    requireFact(control?.frameId===fromObservation.frame_id&&control.role==='button'
      &&point(control.point),'BACK_CONTROL_UNKNOWN');
    const reservation=await reserve('return_navigation',1);record('RETURN_NAVIGATION_INVOCATION');
    try {await app.click(control.point);await app.getAXState({emit:false});}
    catch(error) {closed=true;record('RETURN_NAVIGATION_UNCERTAIN');throw error;}
    await consume(reservation);record('RETURN_NAVIGATION_RETURNED');
    const albums=await observe();requireFact(albums.surface==='ALBUMS','RETURN_TO_ALBUMS_FAILED');return albums;
  }
  async function boundedScroll(before,target,direction,distance) {
    fresh(before.frame_id);requireFact(before.surface==='ALBUMS'&&['up','down'].includes(direction)
      &&point(target)&&Number.isFinite(distance)&&distance>0&&distance<=0.25,'SCROLL_POLICY');
    const reservation=await reserve('scroll',1);record('SCROLL_INVOCATION',{direction,distance});
    try {await app.scroll(target,direction,distance);await app.getAXState({emit:false});}
    catch(error) {closed=true;record('SCROLL_UNCERTAIN');throw error;}
    await consume(reservation);record('SCROLL_RETURNED');
    try {
      const after=await observe();
      const progress=verifyAlbumScroll(before,after);
      record('SCROLL_VERIFIED_NEW_CARD',progress);
      return after;
    } catch(error) {
      closed=true;latest=null;record('SCROLL_UNVERIFIED',{message:String(error)});
      throw error;
    }
  }
  function close() {closed=true;latest=null;record('NAVIGATION_OBSERVER_CLOSED');}
  return Object.freeze({sessionId,observe,returnToAlbums,boundedScroll,close,trace:()=>[...trace]});
```

## Re-review boundary

Assess the selected model, four-path delta/private entry, global durable slot/capture counter plan, genuinely adjacent real image/AX scroll proof, scoped calibrated receipt semantics and unchanged hard entry barriers. If approved, actual implementation/source/config/producer/contract bytes and focused checks still require independent confirmation before live admission. No further code/governance or live work starts this turn. Return to Chief Reviewer on the exact new PR9 HEAD. NEXT_ACTION=RETURN_UPDATED_PR9_TO_CHATGPT.
