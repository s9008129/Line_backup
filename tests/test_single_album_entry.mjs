import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {
  createHumanInputCoordinator,
  createHumanInputRequest,
  createHumanInputResult,
  runHumanAssistedSingleAlbumPilot,
  runSingleAlbumPilot,
  validateHumanInputRequest,
  validateHumanInputResult,
} from '../harness-development/line-two-album-pilot-20261014/two_album_entry.mjs';
import {
  humanDestinationForConfig,
  requiresChooserBaseline,
  readHumanOwnerResponse,
  publishJSONValue,
  createHumanAssistedAdapter,
} from '../harness-development/line-two-album-pilot-20261014/mac_runtime.mjs';

function runtimeWithUsedLifecycle(){
  const operations=[];
  const runtime={profile:'LINE_TWO_ALBUM_PILOT/1',owner:'owner-1',authorization:'grant.json',
    one56Fingerprint:{start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56},
    decoder:{path:'/decoder',sha256:'a'.repeat(64)},
    cli:async(operation)=>{
      operations.push(operation);
      if(operation==='inspect'&&operations.length===1)return {receipt_token:'token-1'};
      if(operation==='inspect')return {receipt_token:'token-2',gui_ledger_status:{
        status:'INITIALIZED',workflow_phase:'A',lifecycle_count:1,failure_latched:false,reserved_entry_count:0}};
      throw new Error('unexpected operation '+operation);
    },
    assertLineAlreadyRunning:async()=>{},getApp:async()=>({}),retain:async()=>{},
    producer:{captureMenuSupport:async()=>{},guardMenu:async()=>{}},menuLocator:async()=>{},chooser:{},navigation:{},
    privateEvidence:{leaseCloseReference:async()=>{},retainC1:async()=>{},retainFailure:async()=>{},retainDiscovery:async()=>{}},
    beforeCapture:async()=>{},afterCapture:async()=>{},windowLineage:async()=>{},clock:()=>0,
  };
  runtime.cli.bridge=async operation=>{operations.push(operation);return {};};
  return {runtime,operations};
}

test('single route refuses a used lifecycle before GUI, batch, C1, B, or initialization operations',async()=>{
  const {runtime,operations}=runtimeWithUsedLifecycle();
  await assert.rejects(runSingleAlbumPilot(runtime),error=>error?.message==='ONE56_LEDGER_NOT_FRESH');
  assert.deepEqual(operations,['inspect','inspect']);
  assert.equal(operations.some(op=>['gui_initialize','begin','gui_phase'].includes(op)),false);
});

test('single route requires the exact 56-photo target before execution',async()=>{
  const {runtime,operations}=runtimeWithUsedLifecycle();
  runtime.one56Fingerprint.expected_images=65;
  await assert.rejects(runSingleAlbumPilot(runtime),error=>error?.message==='ONE56_FINGERPRINT_REQUIRED');
  assert.deepEqual(operations,[]);
});

const humanHash='a'.repeat(64);
const humanSource='b'.repeat(64);
const humanFingerprint={start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56};
const humanBinding={
  task_id:'task-one56-a',grant_sha256:humanHash,observer_session_id:'deepseek-session-a',
  source_sha256:humanSource,destination:'/Users/owner/Downloads/A56',
};
const humanRef=name=>({path:`harness-development/line-two-album-pilot-20261014/private/evidence/${name}.json`,
  bytes:1,sha256:humanHash});
const humanClock=(()=>{let tick=0;return()=>new Date(Date.UTC(2026,9,18,0,0,0,tick++*1000)).toISOString();})();
const humanOperator=(outcome='HUMAN_REPORTED_RETURNED')=>({
  status:'OPERATOR_REPORTED',outcome,reported_at:humanClock(),statement:'Owner completed the bound action.',
  raw_response_ref:humanRef('operator-'+outcome.toLowerCase()),
});
const humanObserved=(facts,status='OBSERVED')=>({status,facts,
  observed_at:status==='OBSERVED'?humanClock():null,
  raw_evidence_refs:[humanRef('observed-'+status.toLowerCase()+'-'+Object.keys(facts).join('-'))]});

function humanRequestInput(overrides={}){
  return {task_id:humanBinding.task_id,grant_sha256:humanBinding.grant_sha256,
    observer_session_id:humanBinding.observer_session_id,source_sha256:humanBinding.source_sha256,
    run_id:'run-a56',action_id:null,request_stage:'CARD',fingerprint:humanFingerprint,
    destination:humanBinding.destination,reservation_ids:['reservation-1'],
    raw_evidence_refs:[humanRef('request-evidence')],...overrides};
}

function humanHarness({unknownStage=null,unknownObservationStage=null,operatorErrorStage=null}={}){
  const calls={reserve:[],read:[],published:[],consumed:[],latched:[],evidence:[],transaction:[],
    finalize:[],cli:[],gui:0};
  const reservations=new Map();let nextReservation=0,nextId=0;
  const humanInput={
    reserve:async spec=>{
      const id=`reservation-${++nextReservation}`;calls.reserve.push({...spec,id});
      reservations.set(id,{id,state:'RESERVED',kind:spec.kind,count:spec.count,run_id:spec.run_id,
        slots:[...spec.slots]});return {id};
    },
    readReservation:async id=>{calls.read.push(id);return structuredClone(reservations.get(id));},
    publish:async artifact=>{calls.published.push(artifact);
      return humanRef(artifact.kind+'-'+(artifact.request_id??artifact.result_id));},
    awaitOperatorReport:async ({request})=>{calls.evidence.push('operator-'+request.request_stage);
      if(operatorErrorStage===request.request_stage)throw Error('operator channel unavailable');
      return humanOperator(unknownStage===request.request_stage?'UNKNOWN':'HUMAN_REPORTED_RETURNED');},
    consumeReservation:async value=>{calls.consumed.push(value);
      const reservation=reservations.get(value.reservation_id);if(reservation)reservation.state='CONSUMED';},
    persistLatch:async latch=>{calls.latched.push(latch);return humanRef('latch-'+latch.request_id);},
  };
  const observation=(stage,facts)=>{calls.evidence.push(stage);
    return humanObserved(facts,unknownObservationStage===stage?'UNKNOWN':'OBSERVED');};
  const evidence={
    readiness:async()=>observation('readiness',{album_a_eligible:true}),
    card:async()=>observation('card',{album_detail_observed:true}),
    calibration:async()=>observation('calibration',{menu_closed:true,no_activation:true}),
    preIntent:async()=>observation('preIntent',{album_detail_observed:true}),
    saveAll:async()=>observation('saveAll',{folder_chooser_observed:true}),
    chooserPath:async()=>observation('chooserPath',{full_path_exact:true,empty_target:true,same_window_lineage:true}),
    chooserConfirm:async()=>observation('chooserConfirm',{download_started:true}),
    recordFailure:async failure=>{calls.evidence.push('failure-'+failure.stage);
      return humanRef('failure-'+failure.stage);},
  };
  let stopped=false;
  const transaction={
    begin:async value=>{calls.transaction.push('begin');assert.equal(value.binding.task_id,humanBinding.task_id);
      return {status:'BATCH_OWNED',batch_id:'batch-a56'};},
    admit:async()=>{calls.transaction.push('admit');return {status:'ADMITTED_BOUNDED_CANDIDATE'};},
    prepare:async()=>{calls.transaction.push('prepare');return {status:'ALBUM_OPEN_READY',run_id:'run-a56',
      project_album_slot:'A',destination:humanBinding.destination,fingerprint:humanFingerprint};},
    commitCalibration:async()=>{calls.transaction.push('commitCalibration');return {status:'CALIBRATED',run_id:'run-a56'};},
    commitIntent:async()=>{calls.transaction.push('commitIntent');return {status:'ORIGINAL_INTENT_COMMITTED',run_id:'run-a56',
      action_id:'action-a56',destination:humanBinding.destination,fingerprint:humanFingerprint,
      raw_evidence_refs:[humanRef('intent')]};},
    readIntent:async()=>{calls.transaction.push('readIntent');return {status:'ORIGINAL_INTENT_COMMITTED',run_id:'run-a56',
      action_id:'action-a56',destination:humanBinding.destination,fingerprint:humanFingerprint,durable:true,
      raw_evidence_refs:[humanRef('intent-readback')]};},
    recordDispatch:async value=>{calls.transaction.push('recordDispatch');calls.dispatch=value;
      return {status:'DOWNLOAD_STARTED',run_id:'run-a56',action_id:'action-a56'};},
    finalize:async value=>{calls.transaction.push('finalize');calls.finalize.push(value);
      return {status:'VERIFIED',run_id:'run-a56',files_verified:56,expected_images:56};},
    readVerified:async()=>{calls.transaction.push('readVerified');return {status:'VERIFIED',run_id:'run-a56',
      files_verified:56,expected_images:56,result:{status:'VERIFIED'}};},
    stop:async()=>{calls.transaction.push('stop');stopped=true;return {status:'STOPPED'};},
    release:async()=>{calls.transaction.push('release');return {status:'BATCH_RELEASED'};},
  };
  let inspectCalls=0;
  const runtime={
    profile:'LINE_TWO_ALBUM_PILOT/1',owner:'owner-1',authorization:'grant.json',decoder:{path:'/decoder',sha256:'c'.repeat(64)},
    one56Fingerprint:{...humanFingerprint},
    cli:async(operation,args)=>{calls.cli.push({operation,args});inspectCalls+=1;
      if(inspectCalls===1)return {receipt_token:'token-1'};
      return {receipt_token:'token-2',gui_ledger_status:{status:'INITIALIZED',workflow_phase:'A',lifecycle_count:0,
        failure_latched:false,reserved_entry_count:0,task_id:humanBinding.task_id,source_sha256:humanBinding.source_sha256,
        owner:'owner-1'}};},
    getApp:async()=>{calls.gui+=1;throw Error('human route must not acquire LINE GUI');},
  };
  return {runtime,calls,humanInput,transaction,evidence,reservations,
    options:{binding:{...humanBinding},humanInput,transaction,evidence,clock:humanClock,
      idFactory:()=>`id-${++nextId}`},get stopped(){return stopped;}};
}

test('human-assisted A-only route issues five ordered requests and never acquires GUI',async()=>{
  const h=humanHarness();
  const result=await runHumanAssistedSingleAlbumPilot(h.runtime,h.options);
  assert.equal(result.status,'ONE_ALBUM_VERIFIED');
  assert.equal(result.execution_mode,'HUMAN_ASSISTED');
  assert.equal(result.albumB,'NOT_STARTED');assert.equal(result.c1,'NOT_STARTED');
  assert.equal(result.live_e2e,'NOT_CLAIMED');assert.equal(result.physical_exactly_once,'UNKNOWN');
  assert.deepEqual(h.calls.reserve.map(item=>item.stage),['CARD','CALIBRATION','SAVE_ALL','CHOOSER_PATH']);
  const inspections=h.calls.cli.filter(item=>item.operation==='inspect');
  assert.equal(inspections.length>=2,true);
  assert.deepEqual(inspections.map(item=>item.args.authorization),
    [null,h.runtime.authorization]);
  assert.equal(h.calls.reserve.every(item=>item.owner===h.runtime.owner),true);
  const requests=h.calls.published.filter(item=>item.kind==='human-input-request-1');
  const results=h.calls.published.filter(item=>item.kind==='human-input-result-1');
  assert.deepEqual(requests.map(item=>item.request_stage),
    ['CARD','CALIBRATION','SAVE_ALL','CHOOSER_PATH','CHOOSER_CONFIRM']);
  assert.equal(results.length,5);
  assert.equal(requests.every(item=>item.version===1&&item.kind==='human-input-request-1'&&item.input_actor==='OWNER_HUMAN'
    &&item.execution_mode==='HUMAN_ASSISTED'&&item.task_id===humanBinding.task_id
    &&item.grant_sha256===humanBinding.grant_sha256&&item.source_sha256===humanBinding.source_sha256
    &&item.observer_session_id===humanBinding.observer_session_id&&item.run_id==='run-a56'
    &&item.destination===humanBinding.destination&&JSON.stringify(item.fingerprint)===JSON.stringify(humanFingerprint)
    &&item.reservation_ids.length===1&&item.issued_at&&item.raw_evidence_refs.length>0),true);
  assert.equal(results.every(item=>item.version===1&&item.kind==='human-input-result-1'&&item.outcome==='HUMAN_REPORTED_RETURNED'),true);
  assert.equal(requests.filter(item=>item.request_stage==='SAVE_ALL').length,1);
  assert.equal(requests.filter(item=>['SAVE_ALL','CHOOSER_PATH','CHOOSER_CONFIRM'].includes(item.request_stage))
    .every(item=>item.action_id==='action-a56'),true);
  assert.equal(requests[3].reservation_ids[0],requests[4].reservation_ids[0]);
  for(let index=0;index<requests.length;index+=1){
    assert.equal(results[index].request_id,requests[index].request_id);
    for(const field of ['task_id','grant_sha256','execution_mode','input_actor','observer_session_id','source_sha256',
      'run_id','action_id','request_stage','destination'])assert.equal(results[index][field],requests[index][field]);
    assert.deepEqual(results[index].fingerprint,requests[index].fingerprint);
    assert.deepEqual(results[index].reservation_ids,requests[index].reservation_ids);
  }
  assert.equal(h.calls.reserve.length,4);assert.equal(h.calls.consumed.length,4);assert.equal(h.calls.read.length,5);
  assert.equal(h.calls.consumed.every(item=>item.execution_mode==='HUMAN_ASSISTED'
    &&item.input_actor==='OWNER_HUMAN'&&item.observer_session_id===humanBinding.observer_session_id
    &&item.request_ref?.sha256===humanHash&&item.result_ref?.sha256===humanHash
    &&item.request_id&&item.result_id&&item.evidence_refs.length===2),true);
  assert.equal(h.calls.finalize.length,1);
  assert.equal(h.calls.finalize[0].decoder,h.runtime.decoder);
  assert.equal(h.calls.finalize[0].requests,undefined);
  assert.match(h.calls.dispatch.chooser_readback.reference.path,/HUMAN_CHOOSER_RESERVATION_READBACK/);
  assert.equal(h.calls.dispatch.chooser_path.result.request_stage,'CHOOSER_PATH');
  assert.equal(h.calls.dispatch.chooser_confirm.result.request_stage,'CHOOSER_CONFIRM');
  assert.deepEqual(h.calls.evidence,['readiness','operator-CARD','card','operator-CALIBRATION','calibration',
    'preIntent','operator-SAVE_ALL','saveAll','operator-CHOOSER_PATH','chooserPath','operator-CHOOSER_CONFIRM','chooserConfirm']);
  assert.equal(h.calls.gui,0);assert.equal(h.calls.cli.length,2);assert.equal(h.stopped,true);
});

test('human route rejects wrong actor, session, mode, destination, fingerprint and reservation bindings',async()=>{
  const request=createHumanInputRequest(humanRequestInput({request_id:'request-a',issued_at:humanClock()}));
  const mutations=[
    value=>{value.input_actor='AUTO_CUA';},
    value=>{value.execution_mode='AUTO';},
    value=>{value.observer_session_id='';},
    value=>{value.destination='Downloads/B65';},
    value=>{value.destination='/Users/owner/Downloads/../B65';},
    value=>{value.destination='/Users/owner/Downloads/A56/';},
    value=>{value.fingerprint={...value.fingerprint,expected_images:0};},
    value=>{value.fingerprint={...value.fingerprint,expected_images:65};},
    value=>{value.reservation_ids=['reservation-1','reservation-2'];},
  ];
  for(const mutate of mutations){
    const value=structuredClone(request);mutate(value);
    assert.throws(()=>validateHumanInputRequest(value),/HUMAN_INPUT_/);
  }
  const result=createHumanInputResult(request,{operator_reported:humanOperator(),observed:humanObserved({album_detail_observed:true}),
    recorded_at:humanClock(),result_id:'result-a'});
  for(const mutate of [value=>{value.observer_session_id='other-session';},value=>{value.destination='/Users/owner/Downloads/B65';},
    value=>{value.fingerprint={...value.fingerprint,expected_images:65};},value=>{value.reservation_ids=['reservation-2'];}]){
    const value=structuredClone(result);mutate(value);
    assert.throws(()=>validateHumanInputResult(request,value),/HUMAN_INPUT_RESULT_BINDING/);
  }
  const fabricated=structuredClone(result);fabricated.observed.facts.precision_px=1;
  assert.throws(()=>validateHumanInputResult(request,fabricated),/HUMAN_INPUT_FABRICATED_CLAIM/);
  const fabricatedValue=structuredClone(result);fabricatedValue.observed.facts.result='CUA_RETURNED';
  assert.throws(()=>validateHumanInputResult(request,fabricatedValue),/HUMAN_INPUT_FABRICATED_CLAIM/);
  const fabricatedOnce=structuredClone(result);fabricatedOnce.observed.facts.exactly_once=true;
  assert.throws(()=>validateHumanInputResult(request,fabricatedOnce),/HUMAN_INPUT_FABRICATED_CLAIM/);
});

test('human route refuses a destination mismatch at durable prepare before any request',async()=>{
  const h=humanHarness();
  h.transaction.prepare=async()=>({status:'ALBUM_OPEN_READY',run_id:'run-a56',project_album_slot:'A',
    destination:'/Users/owner/Downloads/B65',fingerprint:humanFingerprint});
  await assert.rejects(()=>runHumanAssistedSingleAlbumPilot(h.runtime,h.options),/HUMAN_PREPARE_REFUSED/);
  assert.equal(h.calls.published.length,0);assert.equal(h.calls.gui,0);
});

test('human coordinator rejects duplicate requests/results and latches unknown without replay',async()=>{
  const requests=[];
  const coordinator=createHumanInputCoordinator({clock:humanClock,onIssue:async request=>{requests.push(request);
    return humanRef('request-'+request.request_id);},onResult:async result=>humanRef('result-'+result.result_id),
    onLatch:async()=>humanRef('latch')});
  const input=humanRequestInput({issued_at:humanClock()});
  const first=await coordinator.issue(input);
  await assert.rejects(()=>coordinator.issue(input),/HUMAN_INPUT_REQUEST_DUPLICATE/);
  await assert.rejects(()=>coordinator.issue({...input,request_stage:'CALIBRATION',request_id:first.request.request_id}),
    /HUMAN_INPUT_REQUEST_DUPLICATE/);
  const result=createHumanInputResult(first.request,{operator_reported:humanOperator(),observed:humanObserved({album_detail_observed:true}),
    recorded_at:humanClock(),result_id:'result-duplicate'});
  await coordinator.consume(result);
  await assert.rejects(()=>coordinator.consume(result),/HUMAN_INPUT_RESULT_DUPLICATE/);
  const unknownCoordinator=createHumanInputCoordinator({clock:humanClock,
    onIssue:async request=>humanRef('request-'+request.request_id),
    onResult:async result=>humanRef('result-'+result.result_id),
    onLatch:async()=>humanRef('unknown-latch')});
  const unknownRequest=(await unknownCoordinator.issue({...input,issued_at:humanClock()})).request;
  const unknown=createHumanInputResult(unknownRequest,{operator_reported:humanOperator('UNKNOWN'),
    observed:humanObserved({},'UNKNOWN'),recorded_at:humanClock(),result_id:'result-unknown'});
  await unknownCoordinator.consume(unknown);
  assert.equal(unknownCoordinator.latched?.request_id,unknownRequest.request_id);
  await assert.rejects(()=>unknownCoordinator.issue({...input,issued_at:humanClock()}),/HUMAN_INPUT_UNKNOWN_LATCHED/);
});

test('human route stops at UNKNOWN Save All without chooser replay or B',async()=>{
  const h=humanHarness({unknownStage:'SAVE_ALL'});
  await assert.rejects(()=>runHumanAssistedSingleAlbumPilot(h.runtime,h.options),error=>error?.code==='HUMAN_INPUT_UNKNOWN_LATCHED');
  assert.equal(h.calls.published.filter(item=>item.kind==='human-input-request-1').some(item=>item.request_stage==='CHOOSER_PATH'),false);
  assert.equal(h.calls.published.filter(item=>item.kind==='human-input-request-1').some(item=>item.request_stage==='CHOOSER_CONFIRM'),false);
  assert.equal(h.calls.evidence.includes('chooserPath'),false);assert.equal(h.calls.evidence.includes('chooserConfirm'),false);
  assert.equal(h.calls.latched.length,1);assert.equal(h.calls.consumed.at(-1).outcome,'UNKNOWN');
  assert.equal(h.calls.consumed.at(-1).request_ref?.sha256,humanHash);
  assert.equal(h.calls.consumed.at(-1).result_ref?.sha256,humanHash);
  assert.equal(h.calls.finalize.length,0);assert.equal(h.calls.transaction.includes('stop'),true);
  assert.equal(h.calls.gui,0);
});

test('human route stops at UNKNOWN chooser path before confirmation',async()=>{
  const h=humanHarness({unknownStage:'CHOOSER_PATH'});
  await assert.rejects(()=>runHumanAssistedSingleAlbumPilot(h.runtime,h.options),
    error=>error?.code==='HUMAN_INPUT_UNKNOWN_LATCHED');
  assert.equal(h.calls.published.filter(item=>item.kind==='human-input-request-1')
    .some(item=>item.request_stage==='CHOOSER_CONFIRM'),false);
  assert.equal(h.calls.evidence.includes('chooserConfirm'),false);
  assert.equal(h.calls.consumed.length,3);assert.equal(h.calls.latched.length,1);
  assert.equal(h.calls.transaction.includes('stop'),true);assert.equal(h.calls.gui,0);
});

test('human route latches a missing Save All side effect before chooser',async()=>{
  const h=humanHarness({unknownObservationStage:'saveAll'});
  await assert.rejects(()=>runHumanAssistedSingleAlbumPilot(h.runtime,h.options),
    error=>error?.code==='HUMAN_INPUT_UNKNOWN_LATCHED');
  assert.equal(h.calls.published.filter(item=>item.kind==='human-input-request-1')
    .some(item=>item.request_stage==='CHOOSER_PATH'),false);
  assert.equal(h.calls.evidence.includes('chooserPath'),false);
  assert.equal(h.calls.latched.length,1);assert.equal(h.calls.consumed.at(-1).outcome,'UNKNOWN');
  assert.equal(h.calls.finalize.length,0);assert.equal(h.calls.transaction.includes('stop'),true);
  assert.equal(h.calls.gui,0);
});

test('unknown chooser-path operator channel leaves the quartet reserved and never confirms',async()=>{
  const h=humanHarness({operatorErrorStage:'CHOOSER_PATH'});
  await assert.rejects(()=>runHumanAssistedSingleAlbumPilot(h.runtime,h.options),
    error=>error?.code==='HUMAN_INPUT_UNKNOWN_LATCHED');
  assert.equal(h.calls.published.filter(item=>item.kind==='human-input-request-1')
    .some(item=>item.request_stage==='CHOOSER_CONFIRM'),false);
  assert.equal(h.calls.evidence.includes('chooserConfirm'),false);
  assert.equal(h.calls.consumed.length,3);assert.equal(h.calls.latched.length,1);
  assert.equal([...h.reservations.values()].at(-1).state,'RESERVED');
  assert.equal(h.calls.transaction.includes('stop'),true);assert.equal(h.calls.gui,0);
});

const ROOT='/Users/example/Line_backup';
const GROUP='owner-group';
const DESTINATION=humanDestinationForConfig({projectRoot:ROOT,groupName:GROUP});

function retained(kind,sequence) {
  return {path:`harness-development/line-two-album-pilot-20261014/private/evidence/${kind}/${sequence}.json`,
    bytes:16,sha256:'a'.repeat(64)};
}

function createFakeAdapter(overrides={}) {
  let sequence=0;
  const calls=[],writes=[];
  const retainJSON=overrides.retainJSON??(async(_value,kind)=>retained(kind,++sequence));
  const retainRaw=overrides.retainRaw??(async(raw,kind)=>({
    ...retained(kind,++sequence),bytes:raw.byteLength,
    sha256:createHash('sha256').update(raw).digest('hex'),
  }));
  const writePrivateJSON=overrides.writePrivateJSON??(async(relative,value)=>{
    writes.push({relative,value});return retained('request',++sequence);
  });
  const readPrivateJSON=overrides.readPrivateJSON??(async()=>undefined);
  const readPrivateBytes=overrides.readPrivateBytes??(async(relative)=>{
    const value=await readPrivateJSON(relative);
    return value===undefined?undefined:new Uint8Array(Buffer.from(JSON.stringify(value)));
  });
  const humanCli=overrides.humanCli??(async(operation,data,options)=>{
    calls.push({operation,data,options});
    if(operation==='inspect')return {human_read:{id:'readback',kind:data.human_read.kind}};
    if(operation==='prepare')return {result:{status:'ALBUM_OPEN_READY',destination:DESTINATION,
      fingerprint:{start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56}}};
    return {result:{status:'OK'}};
  });
  const adapter=createHumanAssistedAdapter({humanCli,retainJSON,retainRaw,writePrivateJSON,
    readPrivateBytes,
    readRetained:overrides.readRetained,observeVisual:overrides.observeVisual,owner:'owner-1',destination:DESTINATION,
    humanOwnerTimeoutMs:overrides.humanOwnerTimeoutMs,
    now:overrides.now,nowMs:overrides.nowMs,sleep:overrides.sleep});
  return {adapter,calls,writes};
}

test('HUMAN adapter surface matches the coordinator contract',()=>{
  const {adapter}=createFakeAdapter();
  assert.equal(typeof runHumanAssistedSingleAlbumPilot,'function');
  assert.equal(typeof adapter.humanInput,'object');
  assert.equal(typeof adapter.transaction,'object');
  assert.equal(typeof adapter.evidence,'object');
  for(const method of ['reserve','readReservation','publish','awaitOperatorReport','consumeReservation','persistLatch'])
    assert.equal(typeof adapter.humanInput[method],'function');
  for(const method of ['begin','admit','prepare','commitCalibration','commitIntent','readIntent',
    'recordDispatch','finalize','readVerified','stop','release'])
    assert.equal(typeof adapter.transaction[method],'function');
  for(const method of ['readiness','card','calibration','preIntent','saveAll','chooserPath','chooserConfirm','recordFailure'])
    assert.equal(typeof adapter.evidence[method],'function');
});

test('retainJSON evidence path is readback reference JSON',async()=>{
  const reference=await publishJSONValue({kind:'request',request_id:'r1'},'request',{
    publish:async(raw,kind,frameId,suffix)=>({path:`private/${kind}/${frameId}.${suffix}`,
      bytes:raw.byteLength,sha256:frameId})});
  assert.match(reference.path,/\.json$/);
  assert.equal(reference.sha256.length,64);
});

test('human prepare skips AUTO chooser baseline and validates exact destination',async()=>{
  assert.equal(requiresChooserBaseline({result:{status:'ALBUM_OPEN_READY'}}),false);
  assert.equal(requiresChooserBaseline({result:{status:'ALBUM_OPEN_READY',frame_id:''}}),false);
  assert.equal(requiresChooserBaseline({result:{status:'ALBUM_OPEN_READY',frame_id:'a'.repeat(64)}}),true);
  const {adapter,calls}=createFakeAdapter();
  const prepared=await adapter.transaction.prepare({binding:{task_id:'t'},readiness:{},begin:{},admitted:{}});
  assert.equal(prepared.destination,DESTINATION);
  assert.deepEqual(calls.map(call=>call.operation),['prepare']);
});

test('reservation adapter accepts the store reservation envelope',async()=>{
  const {adapter,calls}=createFakeAdapter({humanCli:async(operation,data,options)=>{
    calls.push({operation,data,options});return {reservation:{id:'reservation-1',kind:'album_open',count:1}};
  }});
  assert.deepEqual(await adapter.humanInput.reserve({stage:'CARD',kind:'album_open',count:1,
    run_id:'run-1',owner:'owner-1',slots:['card']}),{id:'reservation-1'});
  assert.equal(calls[0].operation,'gui_reserve');
});

test('human calibration requires four distinct refs and sends the attestation',async()=>{
  const refs=[1,2,3,4].map(sequence=>retained('calibration',sequence));
  const {adapter,calls}=createFakeAdapter();
  const base={status:'OBSERVED',observed_at:'2026-10-18T00:00:00Z',raw_evidence_refs:refs};
  await assert.rejects(adapter.transaction.commitCalibration({binding:{observer_session_id:'session-1'},
    run_id:'run-1',request:{request_id:'request-1'},result:{result_id:'result-1'},
    evidence:{...base,raw_evidence_refs:[refs[0]]},request_ref:retained('request',9),
    result_ref:retained('result',9)}),error=>error.code==='HUMAN_CALIBRATION_REQUIRED');
  await adapter.transaction.commitCalibration({binding:{observer_session_id:'session-1'},
    run_id:'run-1',request:{request_id:'request-1'},result:{result_id:'result-1'},
    evidence:base,request_ref:retained('request',10),result_ref:retained('result',10)});
  const call=calls.at(-1);
  assert.equal(call.operation,'calibrate');
  assert.equal(call.data.calibration.kind,'human-menu-attestation-1');
  assert.equal(call.data.calibration.observer_session_id,'session-1');
  assert.deepEqual([call.data.calibration.detail_ref,call.data.calibration.menu_ref,
    call.data.calibration.closure_ref,call.data.calibration.attestation_ref],refs);
});

test('human dispatch adapter forwards the pre-confirm chooser readback reference',async()=>{
  const {adapter,calls}=createFakeAdapter();
  const chooser_readback={reference:retained('HUMAN_CHOOSER_RESERVATION_READBACK',1)};
  await adapter.transaction.recordDispatch({binding:{},run_id:'run-1',intent:{},intent_readback:{},
    save_all:{},chooser_path:{},chooser_confirm:{},chooser_readback});
  assert.equal(calls.at(-1).operation,'dispatch');
  assert.deepEqual(calls.at(-1).data.chooser_readback,chooser_readback);
});

test('human prepare rejects a destination outside the exact A56 path',async()=>{
  const {adapter}=createFakeAdapter({humanCli:async()=>({result:{status:'ALBUM_OPEN_READY',
    destination:'/wrong',fingerprint:{start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56}}})});
  await assert.rejects(adapter.transaction.prepare({binding:{},readiness:{},begin:{},admitted:{}}),
    error=>error.code==='HUMAN_DESTINATION_MISMATCH');
});

test('owner report timeout is coded and never synthesized',async()=>{
  let clock=0;
  const {adapter,writes}=createFakeAdapter({humanOwnerTimeoutMs:5,nowMs:()=>clock,
    sleep:async milliseconds=>{clock+=milliseconds;}});
  await assert.rejects(adapter.humanInput.awaitOperatorReport({request:{request_id:'req-timeout'}}),
    error=>error.code==='HUMAN_OPERATOR_REPORT_TIMEOUT');
  assert.equal(writes.length,1);
  assert.equal(writes[0].relative,
    'harness-development/line-two-album-pilot-20261014/private/human-input/requests/req-timeout.json');
});

test('wrong-request or malformed owner response is rejected',async()=>{
  assert.throws(()=>readHumanOwnerResponse({request_id:'other',outcome:'HUMAN_REPORTED_RETURNED',
    reported_at:'2026-10-18T00:00:00.000Z',statement:'returned'},{requestId:'expected'}),
  error=>error.code==='HUMAN_OPERATOR_REPORT_INVALID');
  const {adapter}=createFakeAdapter({readPrivateJSON:async()=>({request_id:'wrong',
    outcome:'HUMAN_REPORTED_RETURNED',reported_at:'2026-10-18T00:00:00.000Z',statement:'returned'})});
  await assert.rejects(adapter.humanInput.awaitOperatorReport({request:{request_id:'expected'}}),
    error=>error.code==='HUMAN_OPERATOR_REPORT_INVALID');
});

test('valid owner response is retained and returned as OPERATOR_REPORTED',async()=>{
  const report={request_id:'request-1',outcome:'HUMAN_REPORTED_RETURNED',
    reported_at:'2026-10-18T00:00:00.000Z',statement:'returned to album list'};
  const {adapter}=createFakeAdapter({readPrivateJSON:async()=>report});
  const result=await adapter.humanInput.awaitOperatorReport({request:{request_id:'request-1'}});
  assert.equal(result.status,'OPERATOR_REPORTED');
  assert.equal(result.outcome,'HUMAN_REPORTED_RETURNED');
  assert.match(result.raw_response_ref.path,/\.json$/);
});

test('read-only inspection uses human_read selectors and no mutations',async()=>{
  const {adapter,calls}=createFakeAdapter();
  await adapter.humanInput.readReservation('reservation-1');
  await adapter.transaction.readIntent({binding:{},run_id:'run-1',action_id:'action-1'});
  await adapter.transaction.readVerified({binding:{},run_id:'run-1'});
  assert.equal(calls.length,3);
  assert.deepEqual(calls.map(call=>call.operation),['inspect','inspect','inspect']);
  assert.deepEqual(calls.map(call=>call.options.publicRead),[true,true,true]);
  assert.deepEqual(calls.map(call=>call.data.human_read.kind),['reservation','intent','verified']);
});

test('missing visual capture or evidence returns UNKNOWN with a real failure ref',async()=>{
  const {adapter}=createFakeAdapter({observeVisual:async()=>({})});
  const observed=await adapter.evidence.card({binding:{},prepared:{}});
  assert.equal(observed.status,'UNKNOWN');
  assert.equal(observed.observed_at,null);
  assert.equal(observed.facts.observation_status,'UNKNOWN');
  assert.equal(observed.raw_evidence_refs.length,1);
  assert.match(observed.raw_evidence_refs[0].path,/\.json$/);
});

test('unproven visual facts cannot become OBSERVED',async()=>{
  const packet=Buffer.from(JSON.stringify({facts:{album_detail_observed:false}}));
  const reference={path:'harness-development/line-two-album-pilot-20261014/private/evidence/diagnostic.json',
    bytes:packet.byteLength,sha256:(await import('node:crypto')).createHash('sha256').update(packet).digest('hex')};
  const {adapter}=createFakeAdapter({observeVisual:async()=>({reference}),
    readRetained:async()=>new Uint8Array(packet)});
  const observed=await adapter.evidence.card({binding:{},prepared:{}});
  assert.equal(observed.status,'UNKNOWN');
  assert.equal(observed.raw_evidence_refs[0].sha256,reference.sha256);
});

test('destination helper is exact and rooted in the project',()=>{
  assert.equal(DESTINATION,path.join(ROOT,'backups',GROUP,'2024-05-27_2024-05-31_56張'));
  assert.throws(()=>humanDestinationForConfig({projectRoot:ROOT,groupName:'../escape'}),
    error=>error.code==='HUMAN_GROUP_NAME_REQUIRED');
});
