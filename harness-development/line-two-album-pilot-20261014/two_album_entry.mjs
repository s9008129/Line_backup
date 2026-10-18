// Bounded LINE two-album entry. Runtime bindings (root, grant, owner, destination,
// decoder, producer and retained-evidence writers) are injected by admitted host code.
import {createHostedSession, createNavigationObserver} from '../../scripts/line_backup_cua_adapter.mjs';
import {createHash,randomUUID} from 'node:crypto';
import path from 'node:path';

const requireFact=(ok,code)=>{if(!ok)throw new Error(code);};
const PROJECT_PROFILE='LINE_TWO_ALBUM_PILOT/1';
const hasRecord=o=>o&&typeof o==='object'&&(o.batch_record??o.record);
const fingerprintKey=value=>JSON.stringify([value?.start_date,value?.end_date,value?.expected_images]);

export async function runOneScrollProbe(runtime) {
  requireFact(runtime&&runtime.profile===PROJECT_PROFILE&&typeof runtime.cli==='function'
    &&typeof runtime.assertLineAlreadyRunning==='function'&&typeof runtime.getApp==='function'
    &&typeof runtime.retain==='function'&&typeof runtime.classifyScrollWitness==='function'
    &&typeof runtime.decodeRetainedImage==='function'&&runtime.navigation
    &&typeof runtime.beforeCapture==='function'&&typeof runtime.afterCapture==='function'
    &&typeof runtime.windowLineage==='function'&&typeof runtime.clock==='function'
    &&typeof runtime.privateEvidence?.retainDiscovery==='function','ONE_SCROLL_RUNTIME_REQUIRED');
  const owner=runtime.owner;
  requireFact(typeof owner==='string'&&owner,'ONE_SCROLL_OWNER_REQUIRED');
  let token=null;
  const cli=async(operation,data=null,publicRead=false)=>{
    const payload=data===null?null:(publicRead?{data}:{expected_token:token,data});
    const response=await runtime.cli(operation,{authorization:publicRead?null:runtime.authorization,payload});
    if(typeof response?.receipt_token==='string')token=response.receipt_token;
    return response;
  };
  const inspected=await cli('inspect',null,true);
  requireFact(typeof inspected?.receipt_token==='string','ONE_SCROLL_INSPECTION_REQUIRED');
  token=inspected.receipt_token;
  const readLedgerStatus=async()=>{
    const authority=await cli('inspect',{include_gui_ledger_status:true});
    const status=authority?.gui_ledger_status;
    requireFact(status&&typeof status.task_id==='string'&&status.task_id
      &&typeof status.source_sha256==='string'&&/^[0-9a-f]{64}$/.test(status.source_sha256)&&status.owner===owner,
      'ONE_SCROLL_LEDGER_AUTHORITY_MISMATCH');
    return status;
  };
  let ledger=await readLedgerStatus();
  if(ledger.status==='NOT_INITIALIZED'){
    const initialized=await cli('gui_initialize',{confirm_initialization:true});
    requireFact(initialized?.status==='PROJECT_LEDGER_INITIALIZED','ONE_SCROLL_LEDGER_INITIALIZATION_FAILED');
    ledger=await readLedgerStatus();
  }
  requireFact(ledger.status==='INITIALIZED'&&ledger.workflow_phase==='A'&&!ledger.failure_latched
    &&ledger.scroll_1_used===false&&ledger.reserved_entry_count===0,'ONE_SCROLL_LEDGER_NOT_CONTINUABLE');
  const bridge=async(operation,request={})=>{
    if(operation==='gui_observe')return runtime.cli(operation,{authorization:runtime.authorization,
      payload:{data:request.data}});
    return runtime.cli.bridge(operation,request);
  };
  await bridge('gui_observe',{data:{kind:'app',album:'A',checkpoint:'ONE_SCROLL_APP_ACQUISITION'}});
  await runtime.assertLineAlreadyRunning();
  const app=await runtime.getApp('jp.naver.line.mac');
  requireFact(app&&typeof app.scroll==='function','ONE_SCROLL_LINE_APP_REQUIRED');
  const observer=createNavigationObserver({app,bridge,retain:runtime.retain,classify:runtime.classifyScrollWitness,
    requireV3:true,beforeCapture:runtime.beforeCapture,afterCapture:runtime.afterCapture,
    resolveWindowLineage:runtime.windowLineage,checkpointPrefix:'A_DISCOVERY',sessionId:owner,
    clock:runtime.clock,decodeRetainedImage:runtime.decodeRetainedImage});
  try {
    const before=await observer.observe('PAIR-A-DISCOVERY_SCROLL_1_BEFORE');
    requireFact(before.surface==='ALBUMS'&&before.group_key&&before.scroll_witness?.actionable===false
      &&before.scroll_witness?.evidence_only===true&&before.scroll_witness?.rows?.length>0,
      'ONE_SCROLL_BEFORE_WITNESS_REQUIRED');
    const target=await runtime.navigation.scrollTarget(before);
    const after=await observer.boundedScroll(before,target,'down',0.25,'SCROLL_1',{mode:'ONE_SCROLL_PROBE'});
    requireFact(after?.surface==='ALBUMS'&&observer.movementEvidence().length===1,
      'ONE_SCROLL_MOVEMENT_NOT_VERIFIED');
    await runtime.privateEvidence.retainDiscovery({kind:'ONE_SCROLL_PROBE',evidence_only:true,actionable:false,
      owner,slot:'SCROLL_1',before_frame:before.frame,after_frame:after.frame,
      movement:observer.movementEvidence()[0]});
    return {status:'SCROLL_MOVEMENT_ONLY',evidence_only:true,actionable:false,slot:'SCROLL_1',
      before_frame:before.frame,after_frame:after.frame,movement:observer.movementEvidence()[0].movement};
  } finally {observer.close();}
}

async function runAlbumWorkflow(runtime,{singleAlbum=false}={}) {
  requireFact(runtime&&runtime.profile===PROJECT_PROFILE,'PROJECT_PROFILE_REQUIRED');
  requireFact(typeof runtime.cli==='function'&&typeof runtime.assertLineAlreadyRunning==='function'
    &&typeof runtime.getApp==='function'&&typeof runtime.retain==='function'
    &&runtime.producer&&typeof runtime.producer.captureMenuSupport==='function'
    &&typeof runtime.producer.guardMenu==='function'&&runtime.menuLocator
    &&runtime.chooser&&runtime.navigation&&runtime.privateEvidence
    &&typeof runtime.privateEvidence.leaseCloseReference==='function'
    &&typeof runtime.privateEvidence.retainC1==='function'
    &&typeof runtime.privateEvidence.retainFailure==='function'
    &&typeof runtime.privateEvidence.retainDiscovery==='function'
    &&typeof runtime.beforeCapture==='function'&&typeof runtime.afterCapture==='function'
    &&typeof runtime.windowLineage==='function'&&typeof runtime.clock==='function',
    'ADMITTED_RUNTIME_DEPENDENCIES_REQUIRED');
  const owner=runtime.owner;
  requireFact(typeof owner==='string'&&owner&&runtime.decoder&&typeof runtime.decoder.path==='string'
    &&/^[0-9a-f]{64}$/.test(runtime.decoder.sha256),'PROJECT_OWNER_OR_DECODER_REQUIRED');
  const tokenState={value:null};
  const cli=async(operation,data=null,publicRead=false)=>{
    const payload=data===null?null:(publicRead?{data}:{expected_token:tokenState.value,data});
    const response=await runtime.cli(operation,{authorization:publicRead?null:runtime.authorization,payload});
    if(typeof response?.receipt_token==='string')tokenState.value=response.receipt_token;
    return response;
  };
  const needToken=()=>{requireFact(typeof tokenState.value==='string','RECEIPT_TOKEN_UNAVAILABLE');return tokenState.value;};
  const rawBridge=runtime.cli.bridge;
  requireFact(typeof rawBridge==='function','SUPPORTED_CLI_BRIDGE_REQUIRED');
  const bridge=async(operation,request={})=>{
    if(operation==='gui_observe')return runtime.cli(operation,{authorization:runtime.authorization,
      payload:{data:request.data}});
    const isState=operation==='intent'||operation==='dispatch';
    const response=await rawBridge.call(runtime.cli,operation,isState?{...request,expected_token:request.expected_token??needToken()}:request);
    if(typeof response?.receipt_token==='string')tokenState.value=response.receipt_token;
    return response;
  };

  // A runtime grant must pass the CLI's independent Owner, external review, runtime
  // closure and live-readiness checks before this entry touches LINE or its ledger.
  const inspected=await cli('inspect',null,true);
  requireFact(inspected?.receipt_token,'PROJECT_INSPECTION_REQUIRED');
  tokenState.value=inspected.receipt_token;
  if(singleAlbum){
    const ledgerResponse=await cli('inspect',{include_gui_ledger_status:true});
    const ledger=ledgerResponse?.gui_ledger_status;
    requireFact(ledger?.status==='INITIALIZED'&&ledger.workflow_phase==='A'
      &&ledger.lifecycle_count===0&&ledger.failure_latched===false
      &&ledger.reserved_entry_count===0,'ONE56_LEDGER_NOT_FRESH');
  } else await cli('gui_initialize',{confirm_initialization:true});
  await bridge('gui_observe',{data:{kind:'app',album:'A',checkpoint:'APP_ACQUISITION'}});
  await runtime.assertLineAlreadyRunning();
  const app=await runtime.getApp('jp.naver.line.mac');
  requireFact(app,'LINE_APP_UNAVAILABLE');
  const sessionId=owner;
  const classifier=runtime.classifier;
  requireFact(classifier&&typeof classifier.classify==='function'&&classifier.cache instanceof Map
    &&typeof classifier.classifyChooser==='function','GROUNDED_LIVE_CLASSIFIER_REQUIRED');
  const classify=async(args)=>{
    const base=await classifier.classify(args),cached=classifier.cache.get(args.frameId);
    requireFact(cached?.observation===base&&cached.analysis&&cached.axSnapshot&&cached.geometryRef,
      'CLASSIFIER_CACHE_BINDING_REQUIRED');
    const analysis=cached.analysis,layout=analysis.layout;
    requireFact(Array.isArray(analysis.surface_bounds_px)&&layout&&Number.isFinite(layout.native_scale)
      &&Array.isArray(analysis.cards)&&Array.isArray(cached.axSnapshot.elements),'CLASSIFIER_GEOMETRY_REQUIRED');
    const axCards=analysis.cards.map(card=>{
      const ax=cached.axSnapshot.elements.find(element=>element.index===card.card_ax_index);
      requireFact(ax?.bounds_px?.length===4,'CLASSIFIER_AX_CARD_BINDING');
      return {...card.fingerprint,bounds:ax.bounds_px};
    });
    const parsed_ax={raw_sha256:createHash('sha256').update(args.capture.state).digest('hex'),cards:axCards,
      scroll_offset:analysis.boundary_evidence?.value};
    return {...base,batch_record:base,viewport_bounds:analysis.surface_bounds_px,
      native_scale:layout.native_scale,layout_signature:layout,parsed_ax,
      adapter_evidence:{geometry:cached.geometryRef,ax:cached.axRef,boundary:analysis.boundary_evidence}};
  };
  const makeSession=projectAlbumSlot=>createHostedSession({app,bridge,retain:runtime.retain,classify,
    collectMenuEnvelope:classifier.collectMenuEnvelope,
    classifyChooser:classifier.classifyChooser,requireV2:true,requireV3:true,chooser:runtime.chooser,
    beforeCapture:runtime.beforeCapture,afterCapture:runtime.afterCapture,resolveWindowLineage:runtime.windowLineage,
    projectAlbumSlot,sessionId,clock:runtime.clock,
    menuWaitMs:1200,wait:runtime.wait});
  const stripAdapterEvidence=observation=>{
    const {batch_record,viewport_bounds,native_scale,layout_signature,parsed_ax,adapter_evidence,project_album_slot,...record}=observation;
    return batch_record??record;
  };
  let activeSession=null,activeNavigation=null,activeLifecycle=null,totalScrolls=0;
  const runAlbum=async({ordinal,workflowLink,allowedCandidates=null})=>{
    activeLifecycle={ordinal,begun:false,intentStarted:false,finalized:false,released:false};
    const begun=await cli('begin',{mode:'backup_batch',limit:1});
    requireFact(begun?.result?.status==='BATCH_OWNED','BATCH_BEGIN_REFUSED');
    activeLifecycle.begun=true;
    const session=makeSession(ordinal===1?'A':'B');
    activeSession=session;
    const albumSlot=ordinal===1?'A':'B';
    let list=await session.observe(`PAIR-${albumSlot}-LIST_GROUNDING`);
    requireFact(list.surface==='ALBUMS'&&list.group_key&&hasRecord(list),'ALBUM_LIST_UNGROUNDED');
    let record=stripAdapterEvidence(list.batch_record??list.record);
    let full=list.cards.filter(card=>card?.fully_visible===true).map(card=>card.fingerprint);
    let candidates=(allowedCandidates??full).filter(fp=>full.some(item=>fingerprintKey(item)===fingerprintKey(fp)));
    let admitted=null;
    const discovered=[];
    const maxDiscovery=singleAlbum?0:(ordinal===1?3:0);
    let discovery=null;
    if(maxDiscovery){
      discovery=createNavigationObserver({app,bridge,retain:runtime.retain,classify,
        beforeCapture:runtime.beforeCapture,afterCapture:runtime.afterCapture,resolveWindowLineage:runtime.windowLineage,
        checkpointPrefix:'A_DISCOVERY',requireV3:true,sessionId,clock:runtime.clock});
      activeNavigation=discovery;
    }
    while(!admitted){
      for(const target of candidates){
        try {
          const link=workflowLink?{...workflowLink,b_target:target}:null;
          admitted=await cli('admit',{record,target,session:sessionId,workflow_link:link});
          if(admitted?.result?.status==='ADMITTED_BOUNDED_CANDIDATE')break;
          admitted=null;
        } catch(error) {
          if(error?.code==='BOUNDED_TARGET_INELIGIBLE')continue;
          throw error;
        }
      }
      if(admitted||totalScrolls>=maxDiscovery||totalScrolls>=3)break;
      const nav=discovery;requireFact(nav,'A_DISCOVERY_OBSERVER_REQUIRED');
      try {
        const freshList=await nav.observe(`PAIR-A-DISCOVERY_SCROLL_${totalScrolls+1}_BEFORE`);
        requireFact(freshList.surface==='ALBUMS'&&freshList.session_id===list.session_id
          &&freshList.group_key===list.group_key&&freshList.pid===list.pid&&freshList.window_id===list.window_id
          &&freshList.layout_key===list.layout_key,'A_DISCOVERY_LIST_IDENTITY');
        const scrollSlot=`SCROLL_${totalScrolls+1}`;
        const after=await nav.boundedScroll(freshList,await runtime.navigation.scrollTarget(freshList),'down',0.25,scrollSlot);
        totalScrolls++;
        const proofs=nav.scrollEvidence();
        discovered.push(proofs.at(-1));
        list=after;record=stripAdapterEvidence(list.batch_record??list.record);
        full=list.cards.filter(card=>card?.fully_visible===true).map(card=>card.fingerprint);
        candidates=full;
      } catch(error){throw error;}
    }
    discovery?.close();if(activeNavigation===discovery)activeNavigation=null;
    requireFact(admitted,'NO_ELIGIBLE_TARGET');
    if(discovered.length)await runtime.privateEvidence.retainDiscovery({kind:'A_PRE_DISCOVERY',owner,
      scrolls:discovered,selected:admitted.result?.fingerprint??null});
    const freshList=await session.observe(`PAIR-${albumSlot}-PREPARED_LIST`);
    requireFact(freshList.surface==='ALBUMS'&&freshList.session_id===list.session_id
      &&freshList.group_key===list.group_key&&freshList.pid===list.pid&&freshList.window_id===list.window_id
      &&freshList.layout_key===list.layout_key&&freshList.cards.filter(card=>card?.fully_visible===true)
        .some(card=>fingerprintKey(card.fingerprint)===fingerprintKey(admitted.result?.identity??admitted.result?.fingerprint)),
      'ADMITTED_CARD_NOT_FRESHLY_VISIBLE');
    list=freshList;record=stripAdapterEvidence(freshList.batch_record??freshList.record);
    const preparedResponse=await cli('prepare',{observation:record});
    const prepared=preparedResponse?.result;
    requireFact(prepared?.status==='ALBUM_OPEN_READY'&&prepared.project_album_slot===(ordinal===1?'A':'B'),
      'BOUNDED_PREPARE_REFUSED');
    const detail=await session.openAlbum(prepared);
    const calibrated=await session.calibrateMenu({detail,runId:prepared.run_id,
      locateMenu:runtime.menuLocator,captureMenuSupport:runtime.producer.captureMenuSupport,
      guardMenu:runtime.producer.guardMenu});
    const calibrationResponse=await cli('calibrate',{detail:stripAdapterEvidence(calibrated.detail),calibration:calibrated.calibration,
      menu:calibrated.menu,closure:stripAdapterEvidence(calibrated.closure)});
    requireFact(calibrationResponse?.result?.status==='CALIBRATED','MENU_CALIBRATION_REFUSED');
    const fresh=await session.observe(`PAIR-${albumSlot}-PRE_INTENT_DETAIL`);
    requireFact(fresh.surface==='ALBUM_DETAIL'&&fresh.session_id===detail.session_id
      &&fresh.group_key===detail.group_key&&fresh.pid===detail.pid,'FRESH_DETAIL_REQUIRED');
    activeLifecycle.intentStarted=true;
    const permit=await session.originalIntent({receiptToken:needToken(),freshObservation:stripAdapterEvidence(fresh)});
    const dispatch=await session.originalAtomicDispatch(permit);
    await session.exactChooser({dispatch,...runtime.chooser});
    const finalized=await cli('finalize',{decoder:runtime.decoder.path,decoder_sha256:runtime.decoder.sha256});
    requireFact(finalized?.result?.status==='VERIFIED','ALBUM_VERIFICATION_REQUIRED');
    activeLifecycle.finalized=true;
    const runId=finalized.result.run_id;
    await cli('stop',{reason:'VERIFIED_SINGLE_CANDIDATE_LIFECYCLE'});
    const released=await cli('release',{});
    requireFact(released?.result?.status==='BATCH_RELEASED','ALBUM_RELEASE_REQUIRED');
    activeLifecycle.released=true;
    session.ceaseInput();
    activeSession=null;activeLifecycle=null;
    return {runId,batchId:begun.result.batch_id,fingerprint:prepared.fingerprint,record,list,sessionId,leaseClose:
      await runtime.privateEvidence.leaseCloseReference(runId)};
  };

  try {
  const a=await runAlbum({ordinal:1,workflowLink:null,
    allowedCandidates:singleAlbum?[{...runtime.one56Fingerprint}]:null});
  if(singleAlbum)return {status:'ONE_ALBUM_VERIFIED',profile:PROJECT_PROFILE,albumA:a.runId,
    fingerprint:a.fingerprint,live_e2e:'NOT_CLAIMED'};
  await cli('gui_phase',{phase:'C1',a_run_id:a.runId});
  const navigation=createNavigationObserver({app,bridge,retain:runtime.retain,classify,
    beforeCapture:runtime.beforeCapture,afterCapture:runtime.afterCapture,resolveWindowLineage:runtime.windowLineage,
    requireV3:true,sessionId,clock:runtime.clock});
  activeNavigation=navigation;
  let afterScroll;
  try {
    const detail=await navigation.observe('PAIR-C1-DETAIL');
    requireFact(detail.surface==='ALBUM_DETAIL','C1_DETAIL_REQUIRED');
    const albums=await navigation.returnToAlbums(detail,runtime.navigation.locateBack,a.list);
    const scrollTarget=await runtime.navigation.scrollTarget(albums);
    requireFact(totalScrolls<4,'PROJECT_SCROLL_BUDGET_EXHAUSTED');
    afterScroll=await navigation.boundedScroll(albums,scrollTarget,'down',0.25,`SCROLL_${totalScrolls+1}`);
    totalScrolls++;
  } catch(error) {navigation.close();throw error;}
  let proofs=navigation.scrollEvidence();
  requireFact(afterScroll?.surface==='ALBUMS'&&proofs.length>=1,'C1_BOUNDED_SCROLL_REQUIRED');
  let candidateSet=proofs.at(-1).new_candidates;
  let inspectedB=await cli('inspect',{candidates:candidateSet},true);
  let eligibleCandidates=inspectedB?.eligible_candidates??[];
  while(!eligibleCandidates.length&&totalScrolls<4){
    const nextTarget=await runtime.navigation.scrollTarget(afterScroll);
    afterScroll=await navigation.boundedScroll(afterScroll,nextTarget,'down',0.25,`SCROLL_${totalScrolls+1}`);
    totalScrolls++;proofs=navigation.scrollEvidence();candidateSet=proofs.at(-1).new_candidates;
    inspectedB=await cli('inspect',{candidates:candidateSet},true);
    eligibleCandidates=inspectedB?.eligible_candidates??[];
  }
  navigation.close();activeNavigation=null;
  requireFact(eligibleCandidates.length>0,'NO_ELIGIBLE_TARGET_B');
  candidateSet=eligibleCandidates;
  const c1={kind:'LINE_TWO_ALBUM_C1',status:'PASS',a_run_id:a.runId,group_key:a.list.group_key,
    verified_scroll_count:proofs.length,scrolls:proofs,new_candidates:proofs.at(-1).new_candidates};
  const c1Reference=await runtime.privateEvidence.retainC1(c1);
  await cli('gui_phase',{phase:'C1',a_run_id:a.runId,c1_evidence:c1Reference});
  const workflowLink={a_run_id:a.runId,a_fingerprint:a.fingerprint,lease_close:a.leaseClose,
    c1_evidence:c1Reference,released_batch_id:a.batchId,
    workflow_owner:owner,scroll_count:proofs.length,b_target:null};
  activeNavigation=null;
  const b=await runAlbum({ordinal:2,workflowLink,allowedCandidates:candidateSet});
  await cli('gui_phase',{phase:'DONE',a_run_id:a.runId});
  return {status:'TWO_BOUNDED_ALBUMS_VERIFIED',profile:PROJECT_PROFILE,albumA:a.runId,albumB:b.runId,
    c1:c1Reference,live_e2e:'NOT_CLAIMED'};
  } catch(originalError) {
    const cleanup={profile:PROJECT_PROFILE,owner,error:{name:originalError?.name??'Error',message:String(originalError),code:originalError?.code??null},
      actions:[]};
    try {activeSession?.ceaseInput();cleanup.actions.push({action:'CEASE_SESSION_INPUT',status:'PASS'});}
    catch(error){cleanup.actions.push({action:'CEASE_SESSION_INPUT',status:'UNKNOWN',error:String(error)});}
    try {activeNavigation?.close();cleanup.actions.push({action:'CLOSE_NAVIGATION',status:'PASS'});}
    catch(error){cleanup.actions.push({action:'CLOSE_NAVIGATION',status:'UNKNOWN',error:String(error)});}
    if(activeLifecycle?.begun&&!activeLifecycle.released){
      try {await cli('stop',{reason:'PILOT_FAILURE_LATCHED'});cleanup.actions.push({action:'STOP_ACTIVE_LIFECYCLE',status:'PASS'});}
      catch(error){cleanup.actions.push({action:'STOP_ACTIVE_LIFECYCLE',status:'UNKNOWN',error:String(error)});}
      if(!activeLifecycle.intentStarted||activeLifecycle.finalized){
        try {await cli('release',{});cleanup.actions.push({action:'RELEASE_SAFE_LIFECYCLE',status:'PASS'});}
        catch(error){cleanup.actions.push({action:'RELEASE_SAFE_LIFECYCLE',status:'UNKNOWN',error:String(error)});}
      } else cleanup.actions.push({action:'RELEASE_ACTIVE_INTENT',status:'NOT_ATTEMPTED_UNRESOLVED_INTENT'});
    }
    if(!singleAlbum||activeLifecycle?.begun){
      try {await cli('gui_phase',{phase:'FAILED'});cleanup.actions.push({action:'LATCH_FAILURE',status:'PASS'});}
      catch(error){cleanup.actions.push({action:'LATCH_FAILURE',status:'UNKNOWN',error:String(error)});}
    }
    try {await runtime.privateEvidence.retainFailure(cleanup);}
    catch(error){cleanup.actions.push({action:'RETAIN_FAILURE',status:'UNKNOWN',error:String(error)});}
    originalError.cleanup=cleanup;
    throw originalError;
  }
}

export async function runTwoAlbumPilot(runtime) {
  return runAlbumWorkflow(runtime,{singleAlbum:false});
}

export async function runSingleAlbumPilot(runtime) {
  requireFact(runtime&&runtime.one56Fingerprint
    &&fingerprintKey(runtime.one56Fingerprint)===fingerprintKey({start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56}),
    'ONE56_FINGERPRINT_REQUIRED');
  return runAlbumWorkflow(runtime,{singleAlbum:true});
}

// HUMAN_ASSISTED_ONE56/1_A_ONLY. These helpers are deliberately separate from the
// AUTO workflow above: they never create a hosted input session, classify a frame,
// click a card/menu, dispatch Save All, enter a chooser path, or confirm a chooser.
export const HUMAN_INPUT_STAGES=Object.freeze(['CARD','CALIBRATION','SAVE_ALL','CHOOSER_PATH','CHOOSER_CONFIRM']);
const HUMAN_REQUEST_KIND='human-input-request-1';
const HUMAN_RESULT_KIND='human-input-result-1';
const HUMAN_EXECUTION_MODE='HUMAN_ASSISTED';
const HUMAN_INPUT_ACTOR='OWNER_HUMAN';
const HUMAN_REQUEST_KEYS=Object.freeze(['version','kind','task_id','grant_sha256','execution_mode',
  'input_actor','observer_session_id','source_sha256','run_id','action_id','request_stage','fingerprint',
  'destination','reservation_ids','request_id','issued_at','instruction','raw_evidence_refs']);
const HUMAN_RESULT_KEYS=Object.freeze(['version','kind','task_id','grant_sha256','execution_mode',
  'input_actor','observer_session_id','source_sha256','run_id','action_id','request_stage','fingerprint',
  'destination','reservation_ids','request_id','result_id','recorded_at','operator_reported','observed',
  'outcome','raw_evidence_refs']);
const HUMAN_STAGE_INSTRUCTIONS=Object.freeze({
  CARD:'Open only the bound A56 album card; do not use Save All in this step.',
  CALIBRATION:'Open the album menu, verify the Save All row is present, then close the menu without choosing Save All.',
  SAVE_ALL:'Use Save All exactly once. If the result is uncertain, stop; never repeat it.',
  CHOOSER_PATH:'Enter the exact bound destination in LINE\'s folder chooser and return to the chooser; do not confirm yet.',
  CHOOSER_CONFIRM:'Confirm the exact empty destination once. If confirmation is uncertain, stop; never repeat it.'
});
const HUMAN_STAGE_RESERVATIONS=Object.freeze({
  CARD:{kind:'album_open',count:1,slots:['A.CARD']},
  CALIBRATION:{kind:'menu_calibration',count:2,slots:['A.CAL_OPEN','A.CAL_DISMISS']},
  SAVE_ALL:{kind:'dispatch_inputs',count:2,slots:['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']},
  CHOOSER_PATH:{kind:'chooser_inputs',count:4,
    slots:['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM']},
  CHOOSER_CONFIRM:{kind:'chooser_inputs',count:4,
    slots:['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM']}
});
const HUMAN_A56_FINGERPRINT=Object.freeze({start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56});
const HUMAN_PRIVATE_PREFIX='harness-development/';
const humanNeed=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
const humanClone=value=>value===undefined?undefined:JSON.parse(JSON.stringify(value));
const humanFreeze=value=>{
  if(value&&typeof value==='object'&&!Object.isFrozen(value)){
    for(const child of Object.values(value))humanFreeze(child);Object.freeze(value);
  }
  return value;
};
const humanKeys=value=>value&&typeof value==='object'&&!Array.isArray(value)
  ?Object.keys(value).sort().join(',') : '';
const humanISO=value=>typeof value==='string'&&Number.isFinite(Date.parse(value));
const humanHash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const humanCanonicalDestination=value=>typeof value==='string'&&path.isAbsolute(value)
  &&path.normalize(value)===value&&value===value.normalize('NFC')&&(value==='/'||!value.endsWith('/'));
const humanEvidenceRef=value=>humanKeys(value)==='bytes,path,sha256'
  &&typeof value.path==='string'&&value.path.startsWith(HUMAN_PRIVATE_PREFIX)
  &&value.path.split('/').includes('private')&&!value.path.split('/').includes('..')
  &&Number.isInteger(value.bytes)&&value.bytes>0&&humanHash(value.sha256);
const humanSameRef=(left,right)=>humanEvidenceRef(left)&&humanEvidenceRef(right)
  &&left.path===right.path&&left.bytes===right.bytes&&left.sha256===right.sha256;
const humanRefKey=ref=>ref.path+'|'+ref.bytes+'|'+ref.sha256;
const humanRefs=value=>Array.isArray(value)&&value.length>0&&value.every(humanEvidenceRef)
  &&new Set(value.map(humanRefKey)).size===value.length;
const humanUniqueRefs=values=>{
  const seen=new Set(),result=[];
  for(const ref of values.flat())if(humanEvidenceRef(ref)){
    const key=humanRefKey(ref);
    if(!seen.has(key)){seen.add(key);result.push(humanClone(ref));}
  }
  return result;
};
const humanCompleteRefs=(actual,expected)=>{
  const wanted=humanUniqueRefs([expected]);
  return humanRefs(actual)&&actual.length===wanted.length
    &&wanted.every(ref=>actual.some(candidate=>humanSameRef(candidate,ref)));
};

export function humanInputIssuanceKey(request){
  return [request?.task_id,request?.grant_sha256,request?.run_id,
    request?.action_id??'null',request?.request_stage].join('|');
}

function humanValidateFingerprint(value){
  humanNeed(humanKeys(value)==='end_date,expected_images,start_date'
    &&fingerprintKey(value)===fingerprintKey(HUMAN_A56_FINGERPRINT),'HUMAN_INPUT_FINGERPRINT');
}

function humanValidateAction(stage,actionId){
  humanNeed(HUMAN_INPUT_STAGES.includes(stage),'HUMAN_INPUT_STAGE_REQUIRED');
  if(stage==='CARD'||stage==='CALIBRATION')
    humanNeed(actionId===null,'HUMAN_INPUT_ACTION_BINDING');
  else humanNeed(typeof actionId==='string'&&actionId,'HUMAN_INPUT_ACTION_BINDING');
}

function humanValidateBinding(value){
  humanNeed(typeof value.task_id==='string'&&value.task_id
    &&humanHash(value.grant_sha256)&&humanHash(value.source_sha256)
    &&typeof value.observer_session_id==='string'&&value.observer_session_id
    &&humanCanonicalDestination(value.destination)
    &&typeof value.run_id==='string'&&value.run_id,'HUMAN_INPUT_BINDING_REQUIRED');
  humanValidateFingerprint(value.fingerprint);
  humanValidateAction(value.request_stage,value.action_id);
}

function humanRejectFabricatedClaims(value,path='result'){
  if(!value||typeof value!=='object')return;
  for(const [key,child] of Object.entries(value)){
    const normalized=key.toLowerCase().replace(/[^a-z]/g,'');
    const normalizedValue=typeof child==='string'?child.toLowerCase().replace(/[^a-z]/g,''):'';
    humanNeed(!/cuareturned|classifierpass|precision|exactlyonce/.test(normalized)
      &&!/^(cuareturned|classifierpass|precision|exactlyonce)$/.test(normalizedValue),
      `HUMAN_INPUT_FABRICATED_CLAIM:${path}.${key}`);
    humanRejectFabricatedClaims(child,`${path}.${key}`);
  }
}

export function validateHumanInputRequest(request){
  humanNeed(humanKeys(request)===HUMAN_REQUEST_KEYS.slice().sort().join(','),'HUMAN_INPUT_REQUEST_SHAPE');
  humanNeed(request.version===1&&request.kind===HUMAN_REQUEST_KIND
    &&request.execution_mode===HUMAN_EXECUTION_MODE&&request.input_actor===HUMAN_INPUT_ACTOR,
    'HUMAN_INPUT_REQUEST_IDENTITY');
  humanValidateBinding(request);
  humanNeed(typeof request.request_id==='string'&&request.request_id&&humanISO(request.issued_at),
    'HUMAN_INPUT_REQUEST_IDENTITY');
  const reservationCount=HUMAN_STAGE_RESERVATIONS[request.request_stage].count;
  humanNeed(Array.isArray(request.reservation_ids)
    &&request.reservation_ids.length>=1&&request.reservation_ids.length<=reservationCount
    &&request.reservation_ids.every(id=>typeof id==='string'&&id)
    &&new Set(request.reservation_ids).size===request.reservation_ids.length,'HUMAN_INPUT_RESERVATIONS');
  humanNeed(request.instruction===HUMAN_STAGE_INSTRUCTIONS[request.request_stage],'HUMAN_INPUT_INSTRUCTION');
  humanNeed(humanRefs(request.raw_evidence_refs),'HUMAN_INPUT_EVIDENCE');
  humanRejectFabricatedClaims(request);
  return true;
}

export function createHumanInputRequest(input={}){
  const request={
    version:1,kind:HUMAN_REQUEST_KIND,task_id:input.task_id,grant_sha256:input.grant_sha256,
    execution_mode:HUMAN_EXECUTION_MODE,input_actor:HUMAN_INPUT_ACTOR,
    observer_session_id:input.observer_session_id,source_sha256:input.source_sha256,
    run_id:input.run_id,action_id:input.action_id??null,request_stage:input.request_stage,
    fingerprint:humanClone(input.fingerprint),destination:input.destination,
    reservation_ids:humanClone(input.reservation_ids),request_id:input.request_id??randomUUID(),
    issued_at:input.issued_at??new Date().toISOString(),
    instruction:HUMAN_STAGE_INSTRUCTIONS[input.request_stage],
    raw_evidence_refs:humanClone(input.raw_evidence_refs)
  };
  validateHumanInputRequest(request);return humanFreeze(request);
}

function humanOperatorReport(value){
  humanNeed(humanKeys(value)==='outcome,raw_response_ref,reported_at,statement,status'
    &&value.status==='OPERATOR_REPORTED'
    &&['HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED'].includes(value.outcome)
    &&humanISO(value.reported_at)&&typeof value.statement==='string'&&value.statement
    &&humanEvidenceRef(value.raw_response_ref),'HUMAN_INPUT_OPERATOR_REPORT');
  return humanFreeze(humanClone(value));
}

function humanObservedReport(value){
  humanNeed(humanKeys(value)==='facts,observed_at,raw_evidence_refs,status'
    &&['OBSERVED','UNKNOWN'].includes(value.status)
    &&value.facts&&typeof value.facts==='object'&&!Array.isArray(value.facts)
    &&humanRefs(value.raw_evidence_refs)
    &&(value.status==='UNKNOWN'?value.observed_at===null:humanISO(value.observed_at)),
    'HUMAN_INPUT_OBSERVED');
  return humanFreeze(humanClone(value));
}

function humanCombinedOutcome(operator,observed){
  if(operator.outcome==='REFUSED')return 'REFUSED';
  if(operator.outcome==='UNKNOWN')return 'UNKNOWN';
  return observed.status==='OBSERVED'?'HUMAN_REPORTED_RETURNED':'UNKNOWN';
}

export function createHumanInputResult(request,input={}){
  validateHumanInputRequest(request);
  const operator=humanOperatorReport(input.operator_reported);
  const observed=humanObservedReport(input.observed);
  const outcome=input.outcome??humanCombinedOutcome(operator,observed);
  humanNeed(['HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED'].includes(outcome),'HUMAN_INPUT_OUTCOME');
  const result={
    version:1,kind:HUMAN_RESULT_KIND,task_id:request.task_id,grant_sha256:request.grant_sha256,
    execution_mode:request.execution_mode,input_actor:request.input_actor,
    observer_session_id:request.observer_session_id,source_sha256:request.source_sha256,
    run_id:request.run_id,action_id:request.action_id,request_stage:request.request_stage,
    fingerprint:humanClone(request.fingerprint),destination:request.destination,
    reservation_ids:humanClone(request.reservation_ids),request_id:request.request_id,
    result_id:input.result_id??randomUUID(),recorded_at:input.recorded_at??new Date().toISOString(),
    operator_reported:operator,observed,
    outcome,raw_evidence_refs:humanUniqueRefs([operator.raw_response_ref,observed.raw_evidence_refs])
  };
  validateHumanInputResult(request,result);return humanFreeze(result);
}

export function validateHumanInputResult(request,result){
  validateHumanInputRequest(request);
  humanNeed(humanKeys(result)===HUMAN_RESULT_KEYS.slice().sort().join(','),'HUMAN_INPUT_RESULT_SHAPE');
  humanNeed(result.version===1&&result.kind===HUMAN_RESULT_KIND
    &&result.execution_mode===HUMAN_EXECUTION_MODE&&result.input_actor===HUMAN_INPUT_ACTOR,
    'HUMAN_INPUT_RESULT_IDENTITY');
  for(const field of ['task_id','grant_sha256','observer_session_id','source_sha256','run_id',
    'action_id','request_stage','destination']){
    humanNeed(result[field]===request[field],'HUMAN_INPUT_RESULT_BINDING');
  }
  humanNeed(JSON.stringify(result.fingerprint)===JSON.stringify(request.fingerprint)
    &&JSON.stringify(result.reservation_ids)===JSON.stringify(request.reservation_ids)
    &&result.request_id===request.request_id,'HUMAN_INPUT_RESULT_BINDING');
  humanNeed(typeof result.result_id==='string'&&result.result_id&&humanISO(result.recorded_at)
    &&Date.parse(result.recorded_at)>=Date.parse(request.issued_at),'HUMAN_INPUT_RESULT_IDENTITY');
  const operator=humanOperatorReport(result.operator_reported),observed=humanObservedReport(result.observed);
  humanNeed(['HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED'].includes(result.outcome),'HUMAN_INPUT_OUTCOME');
  humanNeed(result.outcome===humanCombinedOutcome(operator,observed)
    ||result.outcome==='UNKNOWN'&&(operator.outcome==='UNKNOWN'||observed.status==='UNKNOWN'),
    'HUMAN_INPUT_OUTCOME');
  humanNeed(Date.parse(operator.reported_at)>=Date.parse(request.issued_at)
    &&(observed.status==='UNKNOWN'||Date.parse(observed.observed_at)>=Date.parse(request.issued_at)),
    'HUMAN_INPUT_TIME');
  humanNeed(humanCompleteRefs(result.raw_evidence_refs,
    [operator.raw_response_ref,...observed.raw_evidence_refs]),'HUMAN_INPUT_EVIDENCE');
  humanRejectFabricatedClaims(result);
  return true;
}

export function createHumanInputCoordinator({clock=()=>new Date().toISOString(),idFactory=randomUUID,
    onIssue,onResult,onLatch}={}){
  for(const [fn,name] of [[onIssue,'ISSUE'],[onResult,'RESULT'],[onLatch,'LATCH']])
    humanNeed(typeof fn==='function',`HUMAN_INPUT_${name}_PUBLICATION_REQUIRED`);
  const records=new Map(),requestIds=new Set(),resultIds=new Set();let latch=null;
  async function latchUnknown(requestOrId,{reason='HUMAN_INPUT_RESULT_UNKNOWN',recorded_at=clock()}={}){
    humanNeed(!latch,'HUMAN_INPUT_UNKNOWN_LATCHED');
    const record=typeof requestOrId==='string'
      ?[...records.values()].find(item=>item.request.request_id===requestOrId)
      :[...records.values()].find(item=>item.request.request_id===requestOrId?.request_id);
    humanNeed(record,'HUMAN_INPUT_REQUEST_UNKNOWN');
    const request=record.request;
    const value={version:1,kind:'human-input-unknown-latch-1',task_id:request.task_id,
      grant_sha256:request.grant_sha256,observer_session_id:request.observer_session_id,
      source_sha256:request.source_sha256,run_id:request.run_id,action_id:request.action_id,
      request_stage:request.request_stage,request_id:request.request_id,
      issuance_key:humanInputIssuanceKey(request),reason,recorded_at};
    latch=humanFreeze(value);record.latch=latch;
    const reference=await onLatch(humanClone(latch));
    humanNeed(humanEvidenceRef(reference),'HUMAN_INPUT_LATCH_REFERENCE');
    record.latchReference=reference;
    return {latch,reference};
  }
  async function issue(input={}){
    humanNeed(!latch,'HUMAN_INPUT_UNKNOWN_LATCHED');
    const request=createHumanInputRequest({...input,request_id:input.request_id??idFactory(),
      issued_at:input.issued_at??clock()});
    const key=humanInputIssuanceKey(request);
    humanNeed(!requestIds.has(request.request_id),'HUMAN_INPUT_REQUEST_DUPLICATE');
    humanNeed(!records.has(key),'HUMAN_INPUT_REQUEST_DUPLICATE');
    const record={request,reference:null,result:null,resultReference:null,latch:null,latchReference:null};
    records.set(key,record);requestIds.add(request.request_id);
    try {
      const reference=await onIssue(request);
      humanNeed(humanEvidenceRef(reference),'HUMAN_INPUT_REQUEST_REFERENCE');
      record.reference=reference;
    } catch(error) {
      record.issue_error=String(error?.message??error);
      try{await latchUnknown(request,{reason:'HUMAN_INPUT_REQUEST_PUBLICATION_UNKNOWN',
        recorded_at:request.issued_at});}
      catch(latchError){error.latch_error=String(latchError?.message??latchError);}
      throw error;
    }
    return record;
  }
  async function consume(result){
    humanNeed(!latch,'HUMAN_INPUT_UNKNOWN_LATCHED');
    const record=[...records.values()].find(item=>item.request.request_id===result?.request_id);
    humanNeed(record,'HUMAN_INPUT_REQUEST_UNKNOWN');
    humanNeed(record.result===null,'HUMAN_INPUT_RESULT_DUPLICATE');
    humanNeed(!resultIds.has(result?.result_id),'HUMAN_INPUT_RESULT_DUPLICATE');
    try {
      validateHumanInputResult(record.request,result);
      const reference=await onResult(result);
      humanNeed(humanEvidenceRef(reference),'HUMAN_INPUT_RESULT_REFERENCE');
      record.result=result;record.resultReference=reference;resultIds.add(result.result_id);
      let latchReference=null;
      if(result.outcome==='UNKNOWN')latchReference=(await latchUnknown(record.request,{
        reason:'HUMAN_INPUT_RESULT_UNKNOWN',recorded_at:result.recorded_at})).reference;
      return {request:record.request,result,requestReference:record.reference,resultReference:reference,
        latchReference};
    } catch(error) {
      if(!latch)try{await latchUnknown(record.request,{reason:'HUMAN_INPUT_RESULT_PUBLICATION_UNKNOWN',
        recorded_at:humanISO(result?.recorded_at)?result.recorded_at:clock()});}
      catch(latchError){error.latch_error=String(latchError?.message??latchError);}
      throw error;
    }
  }
  return Object.freeze({issue,consume,latchUnknown,
    get latched(){return latch;},
    assertReplayAllowed(){humanNeed(!latch,'HUMAN_INPUT_UNKNOWN_LATCHED');},
    snapshot:()=>humanFreeze([...records.values()].map(record=>({request:record.request,reference:record.reference,
      result:record.result,resultReference:record.resultReference,latch:record.latch,
      latchReference:record.latchReference})))});
}

function humanValidateBindingOptions(binding){
  humanNeed(humanKeys(binding)==='destination,grant_sha256,observer_session_id,source_sha256,task_id',
    'HUMAN_INPUT_BINDING_REQUIRED');
  humanNeed(typeof binding.task_id==='string'&&binding.task_id&&humanHash(binding.grant_sha256)
    &&humanHash(binding.source_sha256)&&typeof binding.observer_session_id==='string'
    &&binding.observer_session_id&&humanCanonicalDestination(binding.destination),
    'HUMAN_INPUT_BINDING_REQUIRED');
}

async function readHumanLedgerStatus(runtime,binding,owner){
  const token={value:null};
  const cli=async(operation,data=null,publicRead=false)=>{
    const payload=data===null?null:(publicRead?{data}:{expected_token:token.value,data});
    const response=await runtime.cli(operation,{authorization:publicRead?null:runtime.authorization,payload});
    if(typeof response?.receipt_token==='string')token.value=response.receipt_token;
    return response;
  };
  const inspected=await cli('inspect',null,true);
  humanNeed(typeof inspected?.receipt_token==='string','HUMAN_READINESS_INSPECTION_REQUIRED');
  token.value=inspected.receipt_token;
  const response=await cli('inspect',{include_gui_ledger_status:true});
  const ledger=response?.gui_ledger_status;
  humanNeed(ledger?.status==='INITIALIZED'&&ledger.workflow_phase==='A'&&ledger.lifecycle_count===0
    &&ledger.failure_latched===false&&ledger.reserved_entry_count===0,'HUMAN_READINESS_LEDGER_NOT_FRESH');
  humanNeed(ledger.task_id===binding.task_id&&ledger.source_sha256===binding.source_sha256
    &&ledger.owner===owner,'HUMAN_READINESS_AUTHORITY_MISMATCH');
  return {ledger,inspection:inspected};
}

function humanStageObservation(stage,value,failureRef){
  humanNeed(HUMAN_INPUT_STAGES.includes(stage)||stage==='READINESS'||stage==='PRE_INTENT',
    'HUMAN_INPUT_STAGE_REQUIRED');
  const fresh=value&&typeof value==='object'&&!Array.isArray(value)
    &&['OBSERVED','UNKNOWN'].includes(value.status)
    &&value.facts&&typeof value.facts==='object'&&!Array.isArray(value.facts)
    &&humanRefs(value.raw_evidence_refs)
    &&(value.status==='UNKNOWN'||humanISO(value.observed_at));
  if(!fresh){
    humanNeed(humanEvidenceRef(failureRef),'HUMAN_INPUT_FAILURE_EVIDENCE');
    return humanFreeze({status:'UNKNOWN',observed_at:null,
      facts:{observation_status:'UNKNOWN',observation_error:'FRESH_STAGE_EVIDENCE_MISSING'},
      raw_evidence_refs:[humanClone(failureRef)]});
  }
  const facts=humanClone(value.facts),refs=humanClone(value.raw_evidence_refs);
  let conclusive=value.status==='OBSERVED';
  if(stage==='READINESS')conclusive=conclusive&&facts.album_a_eligible===true;
  if(stage==='CARD')conclusive=conclusive&&facts.album_detail_observed===true;
  if(stage==='CALIBRATION')conclusive=conclusive&&facts.menu_closed===true&&facts.no_activation===true;
  if(stage==='PRE_INTENT')conclusive=conclusive&&facts.album_detail_observed===true;
  if(stage==='SAVE_ALL')conclusive=conclusive&&facts.folder_chooser_observed===true;
  if(stage==='CHOOSER_PATH')conclusive=conclusive&&facts.full_path_exact===true
    &&facts.empty_target===true&&facts.same_window_lineage===true;
  if(stage==='CHOOSER_CONFIRM')conclusive=conclusive&&facts.download_started===true;
  return humanFreeze(conclusive
    ?{status:'OBSERVED',observed_at:value.observed_at,facts,raw_evidence_refs:refs}
    :{status:'UNKNOWN',observed_at:null,facts,raw_evidence_refs:refs});
}

function humanOperatorInput(value){
  const report=value?.operator_reported??value;
  humanNeed(report&&['HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED'].includes(report.outcome)
    &&humanISO(report.reported_at)&&typeof report.statement==='string'&&report.statement
    &&humanEvidenceRef(report.raw_response_ref),'HUMAN_INPUT_OPERATOR_REPORT');
  return {status:'OPERATOR_REPORTED',outcome:report.outcome,reported_at:report.reported_at,
    statement:report.statement,raw_response_ref:humanClone(report.raw_response_ref)};
}

export async function runHumanAssistedSingleAlbumPilot(runtime,options={}){
  requireFact(runtime&&runtime.profile===PROJECT_PROFILE,'PROJECT_PROFILE_REQUIRED');
  requireFact(typeof runtime.owner==='string'&&runtime.owner&&runtime.one56Fingerprint
    &&fingerprintKey(runtime.one56Fingerprint)===fingerprintKey(HUMAN_A56_FINGERPRINT),
    'HUMAN_ONE56_FINGERPRINT_REQUIRED');
  humanValidateBindingOptions(options.binding);
  const humanInput=options.humanInput??runtime.humanAssisted?.humanInput;
  const transaction=options.transaction??runtime.humanAssisted?.transaction;
  const evidence=options.evidence??runtime.humanAssisted?.evidence;
  for(const [name,value,methods] of [
    ['humanInput',humanInput,['reserve','readReservation','publish','awaitOperatorReport','consumeReservation','persistLatch']],
    ['transaction',transaction,['begin','admit','prepare','commitCalibration','commitIntent','readIntent',
      'recordDispatch','finalize','readVerified','stop','release']],
    ['evidence',evidence,['readiness','card','calibration','preIntent','saveAll','chooserPath','chooserConfirm','recordFailure']]
  ])for(const method of methods)humanNeed(typeof value?.[method]==='function',`HUMAN_${name.toUpperCase()}_${method.toUpperCase()}_REQUIRED`);
  const clock=options.clock??(()=>new Date().toISOString());
  const binding=humanFreeze(humanClone(options.binding));
  const fingerprint=humanClone(runtime.one56Fingerprint);
  let begun=false,stopped=false,runId=null;
  const chain=(...groups)=>humanUniqueRefs(groups);
  async function recordFailureEvidence(stage,error,context={}){
    const reference=await evidence.recordFailure({stage,binding,run_id:runId,
      error:{code:error?.code??null,message:String(error?.message??error)},
      request:context.request??null,request_reference:context.reference??null,observed_at:clock()});
    humanNeed(humanEvidenceRef(reference),'HUMAN_INPUT_FAILURE_REFERENCE');
    return reference;
  }
  async function freshStageObservation(stage,observe,context={}){
    let value,error;
    try{value=await observe();}catch(captureError){error=captureError;}
    if(error!==undefined){
      const reference=await recordFailureEvidence(stage,error,context);
      return humanStageObservation(stage,null,reference);
    }
    try{return humanStageObservation(stage,value,undefined);}
    catch(validationError){
      const reference=await recordFailureEvidence(stage,validationError,context);
      return humanStageObservation(stage,null,reference);
    }
  }
  const readiness=await readHumanLedgerStatus(runtime,binding,runtime.owner);
  const readinessEvidence=await freshStageObservation('READINESS',
    ()=>evidence.readiness({binding,ledger:readiness.ledger}));
  humanNeed(readinessEvidence.status==='OBSERVED','HUMAN_READINESS_EVIDENCE_UNKNOWN');
  const begin=await transaction.begin({binding,ledger:readiness.ledger,readiness:readinessEvidence});
  humanNeed(begin?.status==='BATCH_OWNED'&&typeof begin.batch_id==='string'&&begin.batch_id,
    'HUMAN_BEGIN_REFUSED');begun=true;
  try {
    const admitted=await transaction.admit({binding,readiness:readinessEvidence,begin});
    humanNeed(admitted?.status==='ADMITTED_BOUNDED_CANDIDATE','HUMAN_ADMIT_REFUSED');
    const prepared=await transaction.prepare({binding,readiness:readinessEvidence,begin,admitted});
    humanNeed(prepared?.status==='ALBUM_OPEN_READY'&&typeof prepared.run_id==='string'&&prepared.run_id
      &&prepared.project_album_slot==='A'&&prepared.destination===binding.destination
      &&fingerprintKey(prepared.fingerprint)===fingerprintKey(fingerprint),
      'HUMAN_PREPARE_REFUSED');
    runId=prepared.run_id;
    const coordinator=createHumanInputCoordinator({clock,idFactory:options.idFactory,
      onIssue:request=>humanInput.publish(request),onResult:result=>humanInput.publish(result),
      onLatch:latch=>humanInput.persistLatch(latch)});
    async function readStageReservation(stage,reservationId,code='HUMAN_RESERVATION_READBACK'){
      const spec=HUMAN_STAGE_RESERVATIONS[stage];
      const readback=await humanInput.readReservation(reservationId);
      humanNeed(readback?.id===reservationId&&readback.state==='RESERVED'&&readback.kind===spec.kind
        &&readback.count===spec.count&&readback.run_id===runId
        &&JSON.stringify(readback.slots)===JSON.stringify(spec.slots),code);
      return readback;
    }
    async function reserveStage(stage){
      const spec=HUMAN_STAGE_RESERVATIONS[stage];
      const reservation=await humanInput.reserve({stage,kind:spec.kind,count:spec.count,
        run_id:runId,owner:runtime.owner,slots:[...spec.slots]});
      humanNeed(typeof reservation?.id==='string'&&reservation.id,'HUMAN_RESERVATION_REFUSED');
      return readStageReservation(stage,reservation.id);
    }
    function consumeRecord({reservation,request,requestReference,result,resultReference,outcome}){
      const record={reservation_id:reservation.id,outcome,execution_mode:HUMAN_EXECUTION_MODE,
        input_actor:HUMAN_INPUT_ACTOR,observer_session_id:binding.observer_session_id,
        request_id:request.request_id,request_ref:requestReference};
      if(result)Object.assign(record,{result_id:result.result_id,result_ref:resultReference,
        evidence_refs:humanClone(result.raw_evidence_refs)});
      return record;
    }
    async function runStage({stage,actionId,reservation,preRefs,observe,consume=true}){
      const issued=await coordinator.issue({task_id:binding.task_id,grant_sha256:binding.grant_sha256,
        observer_session_id:binding.observer_session_id,source_sha256:binding.source_sha256,
        run_id:runId,action_id:actionId,request_stage:stage,fingerprint,destination:binding.destination,
        reservation_ids:[reservation.id],raw_evidence_refs:humanUniqueRefs([preRefs])});
      let operatorReport,observed;
      try {
        operatorReport=humanOperatorInput(await humanInput.awaitOperatorReport({request:issued.request,
          reference:issued.reference,stage,instruction:issued.request.instruction}));
      } catch(error) {
        try{await coordinator.latchUnknown(issued.request,{reason:'HUMAN_OPERATOR_RESULT_UNKNOWN'});}
        catch(latchError){error.latch_error=String(latchError?.message??latchError);}
        if(consume){
          try{await humanInput.consumeReservation(consumeRecord({reservation,request:issued.request,
            requestReference:issued.reference,outcome:'UNKNOWN'}));}
          catch(consumeError){error.reservation_error=String(consumeError?.message??consumeError);}
        }
        throw Object.assign(Error('HUMAN_INPUT_UNKNOWN_LATCHED'),{code:'HUMAN_INPUT_UNKNOWN_LATCHED',cause:error});
      }
      observed=await freshStageObservation(stage,
        ()=>observe({request:issued.request,reference:issued.reference}),
        {request:issued.request,reference:issued.reference});
      const result=createHumanInputResult(issued.request,{operator_reported:operatorReport,observed,
        recorded_at:clock(),result_id:options.idFactory?options.idFactory():randomUUID()});
      const consumed=await coordinator.consume(result);
      humanNeed(humanEvidenceRef(consumed.resultReference),'HUMAN_INPUT_RESULT_REFERENCE');
      if(consume)await humanInput.consumeReservation(consumeRecord({reservation,request:issued.request,
        requestReference:issued.reference,result,resultReference:consumed.resultReference,
        outcome:result.outcome}));
      if(result.outcome==='UNKNOWN')throw Object.assign(Error('HUMAN_INPUT_UNKNOWN_LATCHED'),
        {code:'HUMAN_INPUT_UNKNOWN_LATCHED'});
      if(result.outcome==='REFUSED')throw Object.assign(Error('HUMAN_INPUT_REFUSED'),{code:'HUMAN_INPUT_REFUSED'});
      return {request:issued.request,requestReference:issued.reference,result,
        resultReference:consumed.resultReference,reservation,observed};
    }
    const card=await runStage({stage:'CARD',actionId:null,reservation:await reserveStage('CARD'),
      preRefs:readinessEvidence.raw_evidence_refs,observe:context=>evidence.card({...context,binding,prepared})});
    const calibrationReservation=await reserveStage('CALIBRATION');
    const calibration=await runStage({stage:'CALIBRATION',actionId:null,reservation:calibrationReservation,
      preRefs:card.result.raw_evidence_refs,observe:context=>evidence.calibration({...context,binding,prepared,card})});
    const calibrationCommit=await transaction.commitCalibration({binding,run_id:runId,request:calibration.request,
      result:calibration.result,evidence:calibration.observed});
    humanNeed(calibrationCommit?.status==='CALIBRATED'&&calibrationCommit.run_id===runId,
      'HUMAN_CALIBRATION_COMMIT_REFUSED');
    const preIntentEvidence=await freshStageObservation('PRE_INTENT',
      ()=>evidence.preIntent({binding,run_id:runId,calibrationCommit}));
    humanNeed(preIntentEvidence.status==='OBSERVED','HUMAN_PRE_INTENT_EVIDENCE_UNKNOWN');
    const intent=await transaction.commitIntent({binding,run_id:runId,calibration:calibrationCommit,
      fresh_evidence:preIntentEvidence});
    humanNeed(intent?.status==='ORIGINAL_INTENT_COMMITTED'&&intent.run_id===runId
      &&typeof intent.action_id==='string'&&intent.action_id&&intent.destination===binding.destination
      &&fingerprintKey(intent.fingerprint)===fingerprintKey(fingerprint),'HUMAN_INTENT_COMMIT_REFUSED');
    const intentReadback=await transaction.readIntent({binding,run_id:runId,action_id:intent.action_id});
    humanNeed(intentReadback?.status==='ORIGINAL_INTENT_COMMITTED'&&intentReadback.run_id===runId
      &&intentReadback.action_id===intent.action_id&&intentReadback.destination===binding.destination
      &&fingerprintKey(intentReadback.fingerprint)===fingerprintKey(fingerprint)
      &&intentReadback.durable===true,'HUMAN_INTENT_READBACK_REQUIRED');
    const intentRefs=chain(intent.raw_evidence_refs??[],intentReadback.raw_evidence_refs??[],
      preIntentEvidence.raw_evidence_refs);
    const saveAllReservation=await reserveStage('SAVE_ALL');
    const saveAll=await runStage({stage:'SAVE_ALL',actionId:intent.action_id,reservation:saveAllReservation,
      preRefs:intentRefs,observe:context=>evidence.saveAll({...context,binding,run_id:runId,intent})});
    const chooserReservation=await reserveStage('CHOOSER_PATH');
    const chooserPath=await runStage({stage:'CHOOSER_PATH',actionId:intent.action_id,reservation:chooserReservation,
      preRefs:saveAll.result.raw_evidence_refs,consume:false,
      observe:context=>evidence.chooserPath({...context,binding,run_id:runId,intent,saveAll})});
    await readStageReservation('CHOOSER_CONFIRM',chooserReservation.id,'HUMAN_CHOOSER_RESERVATION_READBACK');
    const chooserConfirm=await runStage({stage:'CHOOSER_CONFIRM',actionId:intent.action_id,
      reservation:chooserReservation,preRefs:chooserPath.result.raw_evidence_refs,consume:true,
      observe:context=>evidence.chooserConfirm({...context,binding,run_id:runId,intent,saveAll,chooserPath})});
    const dispatch=await transaction.recordDispatch({binding,run_id:runId,intent,intent_readback:intentReadback,
      save_all:saveAll,chooser_path:chooserPath,chooser_confirm:chooserConfirm});
    humanNeed(dispatch?.status==='DOWNLOAD_STARTED'&&dispatch.run_id===runId
      &&dispatch.action_id===intent.action_id,'HUMAN_DISPATCH_RECORD_REFUSED');
    const finalized=await transaction.finalize({binding,run_id:runId,decoder:runtime.decoder,
      requests:{card,calibration,saveAll,chooserPath,chooserConfirm}});
    humanNeed(finalized?.status==='VERIFIED'&&finalized.run_id===runId
      &&finalized.files_verified===56&&finalized.expected_images===56,'HUMAN_VERIFICATION_REQUIRED');
    const verified=await transaction.readVerified({binding,run_id:runId});
    humanNeed(verified?.status==='VERIFIED'&&verified.run_id===runId
      &&verified.files_verified===56&&verified.expected_images===56,'HUMAN_VERIFIED_READBACK_REQUIRED');
    const stop=await transaction.stop({binding,run_id:runId,reason:'VERIFIED_HUMAN_ASSISTED_SINGLE_ALBUM'});
    humanNeed(stop?.status==='STOPPED','HUMAN_STOP_REFUSED');stopped=true;
    const released=await transaction.release({binding,run_id:runId});
    humanNeed(released?.status==='BATCH_RELEASED','HUMAN_RELEASE_REFUSED');
    return humanFreeze({status:'ONE_ALBUM_VERIFIED',profile:PROJECT_PROFILE,execution_mode:HUMAN_EXECUTION_MODE,
      albumA:runId,albumB:'NOT_STARTED',c1:'NOT_STARTED',live_e2e:'NOT_CLAIMED',
      physical_exactly_once:'UNKNOWN',requests:{CARD:card.requestReference,CALIBRATION:calibration.requestReference,
        SAVE_ALL:saveAll.requestReference,CHOOSER_PATH:chooserPath.requestReference,
        CHOOSER_CONFIRM:chooserConfirm.requestReference},verified:verified.result??verified});
  } catch(error) {
    if(begun&&!stopped){try{await transaction.stop({binding,run_id:runId,reason:'HUMAN_ASSISTED_FAILURE_LATCHED'});}
      catch(stopError){error.stop_error=String(stopError?.message??stopError);}}
    throw error;
  }
}
