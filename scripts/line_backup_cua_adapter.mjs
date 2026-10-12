// Load only inside the documented cua_repl kernel with a genuine App object.
// Ordinary Node tests supply external fake I/O; no CUA SDK or GUI synthesis here.
import {createHash, randomUUID} from 'node:crypto';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requireFact = (ok, code) => {if (!ok) throw new Error(code);};
const point = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const hex64 = v => typeof v === 'string' && /^[0-9a-f]{64}$/.test(v);
const typeFinite = v => typeof v === 'number' && Number.isFinite(v);
const typedArrayPrototype = Object.getPrototypeOf(Uint8Array.prototype);
const typedArrayTag = Object.getOwnPropertyDescriptor(typedArrayPrototype, Symbol.toStringTag)?.get;
const typedArrayBuffer = Object.getOwnPropertyDescriptor(typedArrayPrototype, 'buffer')?.get;
const typedArrayByteOffset = Object.getOwnPropertyDescriptor(typedArrayPrototype, 'byteOffset')?.get;
const typedArrayByteLength = Object.getOwnPropertyDescriptor(typedArrayPrototype, 'byteLength')?.get;
const arrayBufferByteLength = Object.getOwnPropertyDescriptor(ArrayBuffer.prototype, 'byteLength')?.get;

export function normalizeScreenshotBytes(value) {
  requireFact(ArrayBuffer.isView(value), 'CAPTURE_BYTES_INVALID');
  let tag, buffer, byteOffset, byteLength, backingLength;
  try {
    tag = Reflect.apply(typedArrayTag, value, []);
    buffer = Reflect.apply(typedArrayBuffer, value, []);
    byteOffset = Reflect.apply(typedArrayByteOffset, value, []);
    byteLength = Reflect.apply(typedArrayByteLength, value, []);
    backingLength = Reflect.apply(arrayBufferByteLength, buffer, []);
  } catch {
    throw new Error('CAPTURE_BYTES_INVALID');
  }
  requireFact(tag === 'Uint8Array' && Number.isSafeInteger(byteOffset) && byteOffset >= 0
    && Number.isSafeInteger(byteLength) && byteLength > 0 && byteLength <= 16 * 1024 * 1024
    && Number.isSafeInteger(backingLength) && byteOffset + byteLength <= backingLength,
  'CAPTURE_BYTES_INVALID');
  const copy = new Uint8Array(byteLength);
  copy.set(new Uint8Array(buffer, byteOffset, byteLength));
  return copy;
}

function verifyFrameReference(saved, frameId, byteLength) {
  requireFact(saved && typeof saved.path === 'string' && saved.path.startsWith('harness-development/')
    && Number.isInteger(saved.bytes) && saved.bytes === byteLength && saved.sha256 === frameId
    && saved.ax && typeof saved.ax.path === 'string' && saved.ax.path.startsWith('harness-development/')
    && Number.isInteger(saved.ax.bytes) && saved.ax.bytes > 0 && hex64(saved.ax.sha256),
  'CUA_FRAME_REFERENCE_REQUIRED');
}


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
}

export function createAlbumSupportCallbacks({invokeProducer}) {
  requireFact(typeof invokeProducer === 'function','PRODUCER_BRIDGE_REQUIRED');
  async function captureMenuSupport({action, pairFrameId, sessionId, requestedAt, cuaFrame, cuaCapturedAt}) {
    requireFact(hex64(pairFrameId) && cuaFrame && hex64(cuaFrame.sha256) && cuaFrame.sha256 === pairFrameId
      && typeof cuaFrame.path === 'string' && cuaFrame.path.startsWith('harness-development/') && Number.isInteger(cuaFrame.bytes),
      'CUA_FRAME_REFERENCE_REQUIRED');
    const support = await invokeProducer({mode:'capture',action,pairFrameId,sessionId,requestedAt,cuaFrame,cuaCapturedAt});
    requireFact(support?.provider === 'SCREEN_CAPTURE_KIT' && support?.pairFrameId === pairFrameId
      && hex64(support?.popupFrameId) && support.popupFrameId !== pairFrameId && support?.sessionId === sessionId
      && typeof support?.reference?.path === 'string' && support.reference.path.startsWith('harness-development/')
      && Number.isInteger(support.reference.bytes) && support.reference.bytes > 0 && hex64(support.reference.sha256)
      && typeFinite(support.uncertaintyPx) && support.uncertaintyPx >= 2
      && typeFinite(support.safeMarginPx) && support.safeMarginPx >= support.uncertaintyPx + 4
      && Array.isArray(support.intersectionPx) && support.intersectionPx.length === 4
      && support.intersectionPx[2] >= 16 && support.intersectionPx[3] >= 16,
      'SCK_SUPPORT_REQUIRED');
    return support;
  }
  async function guardMenu({action, support, pairFrameId, sessionId}) {
    requireFact(support?.reference && hex64(support.popupFrameId),'SCK_SUPPORT_REQUIRED');
    const guard = await invokeProducer({mode:'guard',support:support.reference,pairFrameId,popupFrameId:support.popupFrameId,
      saveAllPoint:action.save_all,uncertaintyPx:support.uncertaintyPx,sessionId});
    requireFact(guard?.verdict === 'PASS' && guard?.provider === 'SCREEN_CAPTURE_KIT'
      && guard?.pairFrameId === pairFrameId && guard?.popupFrameId === support.popupFrameId
      && guard?.supportSha256 === support.reference.sha256
      && point(guard?.actionPoint) && guard.actionPoint[0] === action.save_all[0] && guard.actionPoint[1] === action.save_all[1],
      'SCK_MENU_GUARD_REFUSED');
    return guard;
  }
  return Object.freeze({captureMenuSupport,guardMenu});
}

export function createHostedSession({app, bridge, retain, classify, classifyChooser = null, requireV2 = false,
    chooser = null, sessionId = randomUUID(),
    clock = () => performance.now(), wait = ms => new Promise(r => setTimeout(r,ms)), menuWaitMs = 1200}) {
  requireFact(app && ['getAXStateAndScreenshot','getAXState','click','pressKey','setValue','scroll'].every(k => typeof app[k] === 'function'), 'DOCUMENTED_APP_REQUIRED');
  requireFact(typeof bridge === 'function' && typeof retain === 'function' && typeof classify === 'function','HOST_BRIDGE_REQUIRED');
  requireFact(Number.isInteger(menuWaitMs) && menuWaitMs >= 800 && menuWaitMs <= 1500,'MENU_WAIT_OUTSIDE_POLICY');
  if (requireV2) requireFact(typeof classifyChooser === 'function' && chooser
    && ['locatePathField','validatePath','validateLeaf','locateConfirm','refreshBaseline','observeDownload']
      .every(k=>typeof chooser[k]==='function'),
    'V2_CHOOSER_DEPENDENCIES_REQUIRED');
  let latest = null, stopped = false, confirming = new Set();
  const permits = new WeakMap(), choosers = new WeakMap(), trace = [];
  const record = (event, extra={}) => trace.push(Object.freeze({event, at:clock(), wallAt:new Date().toISOString(), ...extra}));
  function fresh(frameId) {
    requireFact(!stopped && latest && latest.frameId === frameId && clock() >= latest.at && clock()-latest.at <= 5000,'FRESH_CAPTURE_REQUIRED');
  }
  async function reserveGui(kind,count,runId) {
    requireFact(!stopped,'SESSION_STOPPED');
    requireFact(Number.isInteger(count) && count > 0,'GUI_LEDGER_COUNT');
    const response = await bridge('gui_reserve',{data:{kind,count,run_id:runId,owner:sessionId}});
    const reservation = response?.reservation;
    requireFact(reservation && typeof reservation.id === 'string' && reservation.kind === kind
      && reservation.count === count,'GUI_LEDGER_RESERVE_REFUSED');
    latest = null;
    return Object.freeze({id:reservation.id,kind,count});
  }
  async function consumeGui(reservation,outcome) {
    const response = await bridge('gui_consume',{data:{reservation_id:reservation.id,outcome}});
    requireFact(response?.reservation?.id === reservation.id && response.reservation.state === 'CONSUMED',
      'GUI_LEDGER_CONSUME_REFUSED');
  }
  async function observe() {
    requireFact(!stopped,'SESSION_STOPPED');
    const requestStartedAtMonotonic = clock();
    const requestStartedAtUtc = new Date().toISOString();
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
    const observation = await classify({capture,saved,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    requireFact(observation.frame_id === frameId && observation.session_id === sessionId,'CLASSIFIER_FRAME_MISMATCH');
    // The capture interval starts before CUA and never renews during persistence/OCR.
    latest = Object.freeze({frameId,at:requestStartedAtMonotonic,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval,observation,saved,capture});
    return observation;
  }
  async function makeChooserPhase(phase, dispatchInfo, previous=null) {
    requireFact(typeof classifyChooser==='function' && latest,'CHOOSER_CLASSIFIER_REQUIRED');
    const envelope=await classifyChooser({phase,dispatch:dispatchInfo,previous:previous?.envelope??null,
      capture:latest.capture,saved:latest.saved,observation:latest.observation,frameId:latest.frameId,
      sessionId,capturedAt:latest.capturedAt});
    requireFact(envelope?.version===1 && envelope.phase===phase && envelope.frame?.frame_id===latest.frameId
      && envelope.frame?.session_id===sessionId,'CHOOSER_PHASE_FRAME_MISMATCH');
    const reference=await retain({artifact:envelope,kind:`chooser-phase-${phase.toLowerCase()}`,
      frameId:latest.frameId,sessionId});
    requireFact(reference && typeof reference.path==='string' && reference.path.startsWith('harness-development/')
      && Number.isInteger(reference.bytes) && reference.bytes>0 && hex64(reference.sha256),'CHOOSER_PHASE_RETAIN_REQUIRED');
    return Object.freeze({phase,envelope,reference});
  }
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
    }
  }
  async function calibrateMenu({detail,runId,locateMenu,captureMenuSupport,guardMenu}) {
    fresh(detail.frame_id);
    requireFact(detail.surface==='ALBUM_DETAIL'&&typeof locateMenu==='function'
      &&typeof captureMenuSupport==='function'&&typeof guardMenu==='function','MENU_CALIBRATION_DEPENDENCIES');
    const reservation=await reserveGui('menu_calibration',2,runId);
    const started=clock();const wallStarted=new Date().toISOString();let uncertain=false;
    try {
      const trigger=await locateMenu(detail,{phase:'TRIGGER'});
      requireFact(point(trigger?.point)&&trigger.frameId===detail.frame_id&&trigger.role==='button'
        &&trigger.point.every(Number.isInteger)&&Array.isArray(trigger.bounds_px)
        &&Number.isFinite(trigger.dot_spacing)&&trigger.dot_spacing>0,'MENU_TRIGGER_UNKNOWN');
      latest=null;record('MENU_OPEN_INVOCATION',{runId});await app.click(trigger.point);await app.getAXState({emit:false});
      record('MENU_OPEN_RETURNED');await wait(menuWaitMs);
      const openFrame=await observe();
      requireFact(openFrame.surface==='ALBUM_DETAIL'&&openFrame.session_id===sessionId,'MENU_OPEN_CONTEXT_DRIFT');
      const row=await locateMenu(openFrame,{phase:'ROW'});
      requireFact(point(row?.save_all)&&row.save_all.every(Number.isInteger)
        &&row.frameId===openFrame.frame_id&&row.layoutKey===openFrame.layout_key
        &&Array.isArray(row.menuBounds)&&Array.isArray(row.addressableBounds)&&Array.isArray(row.safeBounds)
        &&Array.isArray(row.ellipsisBounds)&&(row.label==='儲存全部'||row.label==='Save All'),'MENU_ROW_UNKNOWN');
      const action={run_id:runId,action_id:`CAL-${sessionId}-${openFrame.frame_id.slice(0,12)}`,
        owner:sessionId,save_all:row.save_all};
      const support=await captureMenuSupport({action,pairFrameId:openFrame.frame_id,sessionId,requestedAt:clock(),
        cuaFrame:latest.saved,cuaCapturedAt:openFrame.captured_at,geometry:row});
      const guard=await guardMenu({action,support,pairFrameId:openFrame.frame_id,sessionId});
      requireFact(guard.verdict==='PASS'&&guard.pairFrameId===openFrame.frame_id
        &&guard.actionPoint[0]===row.save_all[0]&&guard.actionPoint[1]===row.save_all[1],'MENU_GUARD_REFUSED');
      record('MENU_SUPPORT_GUARD_PASS',{support:support.reference,guard});
      latest=null;record('MENU_CLOSE_INVOCATION');await app.pressKey('Escape');await app.getAXState({emit:false});
      record('MENU_CLOSE_RETURNED');const closure=await observe();
      requireFact(closure.surface==='ALBUM_DETAIL'&&closure.session_id===sessionId&&closure.group_key===detail.group_key
        &&closure.pid===detail.pid&&closure.window_id===detail.window_id&&closure.layout_key===detail.layout_key
        &&closure.cards.length===1&&detail.cards.length===1
        &&JSON.stringify(closure.cards[0].fingerprint)===JSON.stringify(detail.cards[0].fingerprint),
        'MENU_CLOSURE_CONTEXT_DRIFT');
      await consumeGui(reservation,'RETURNED');
      const closedAt=new Date().toISOString();
      const calibration={observed_at:wallStarted,screenshot_width:detail.width,screenshot_height:detail.height,
        ellipsis:trigger.point,dot_spacing:trigger.dot_spacing,save_all_point:row.save_all,confidence:'HIGH',
        evidence:support.reference.sha256};
      const menu={label:row.label,frame_id:detail.frame_id,layout_key:detail.layout_key,
        evidence:support.reference,safe_bounds:row.safeBounds,ellipsis_bounds:trigger.bounds_px,
        closure_trace:['OPEN_MENU','OBSERVE_SAVE_ALL','CLOSE_WITHOUT_COMMAND','DETAIL_MATCH']};
      const claim={version:1,kind:'menu-calibration',run_id:runId,session_id:sessionId,
        detail,menu_frame:openFrame,trigger,label:row.label,
        support:support.reference,guard,save_all:row.save_all,safe_bounds:row.safeBounds,
        opened_at:wallStarted,closed_at:closedAt,latency_ms:clock()-started,reservation_id:reservation.id,
        reservation_state:'CONSUMED'};
      const reference=await retain({artifact:claim,kind:'menu-calibration',frameId:detail.frame_id,sessionId});
      return {detail,calibration,menu:{...menu,evidence:reference},closure,claim:reference};
    } catch(error) {
      uncertain=true;stopped=true;latest=null;record('MENU_CALIBRATION_UNCERTAIN',{message:String(error)});throw error;
    } finally {
      if(!uncertain) { /* successful reservation was consumed above */ }
    }
  }
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
    const action=permit.result;
    requireFact(point(action.ellipsis) && point(action.save_all),'INVALID_MENU_POINTS');
    requireFact(clock()-permit.issuedAt<=2000,'PERMIT_EXPIRED');
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
    // No observe, persistence, bridge call, keyboard or app switch between the two clicks.
    await app.getAXState({emit:false});
    const chooser=await observe();
    requireFact(chooser.surface==='FOLDER_CHOOSER','CHOOSER_NOT_CONFIRMED');
    const dispatchInfo=Object.freeze({run_id:action.run_id,action_id:action.action_id,session_id:sessionId,
      owner:action.owner,destination:action.destination,original_frame_id:permit.frameId,
      original_context:permit.originalContext});
    let appeared=null;
    if (typeof classifyChooser==='function') {
      appeared=await makeChooserPhase('APPEARED',dispatchInfo);
      record('CHOOSER_APPEARED',{frameId:chooser.frame_id});
    }
    const dispatch=Object.freeze({action,receiptToken:permit.receiptToken,chooser,pairFrameId:permit.frameId,
      popupFrameId:support.popupFrameId,support:support.reference,guard,
      menuSupport:trace.findLast(t=>t.event==='SCK_MENU_GUARD_PASS'),reservation,dispatchInfo,appeared,
      trace:[...trace]});
    choosers.set(dispatch,true);
    return dispatch;
  }
  async function exactChooser({dispatch,locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload,
      destinationBaseline}) {
    requireFact(choosers.has(dispatch),'NO_ORIGINAL_CHOOSER_PERMISSION');
    const {action,chooser}=dispatch;
    fresh(chooser.frame_id);requireFact(chooser.surface==='FOLDER_CHOOSER','CHOOSER_NOT_CONFIRMED');
    requireFact(!confirming.has(action.action_id),'CONFIRMATION_ALREADY_ATTEMPTED');
    if (requireV2 || typeof classifyChooser==='function') {
      const deps={...chooser,locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload,
        destinationBaseline};
      return exactChooserV2({dispatch,...deps});
    }
    requireFact([locatePathField,validatePath,validateLeaf,locateConfirm].every(f => typeof f==='function'),'CHOOSER_LOCATORS_REQUIRED');
    // One Go-to-Folder navigation, then a newly observed actual text field.
    const reservation = await reserveGui('chooser_inputs',4,action.run_id);
    latest=null;await app.pressKey('super+shift+g');await app.getAXState({emit:false});
    const dialog=await observe();const field=await locatePathField(dialog);
    requireFact(Number.isInteger(field?.index) && field.index>=0 && field.frameId===dialog.frame_id && field.role==='text field','PATH_FIELD_UNKNOWN');
    fresh(dialog.frame_id);latest=null;await app.setValue(field.index,action.destination);await app.getAXState({emit:false});
    const filled=await observe();requireFact(await validatePath(filled,action.destination),'FULL_PATH_NOT_CONFIRMED');
    fresh(filled.frame_id);latest=null;await app.pressKey('Return');await app.getAXState({emit:false});
    const leaf=await observe();requireFact(await validateLeaf(leaf,action.destination),'DESTINATION_LEAF_MISMATCH');
    const confirmation=await locateConfirm(leaf);
    requireFact(point(confirmation?.point) && confirmation.frameId===leaf.frame_id && confirmation.role==='button','CONFIRM_CONTROL_UNKNOWN');fresh(leaf.frame_id);
    confirming.add(action.action_id);latest=null;record('CONFIRM_INVOCATION',{actionId:action.action_id});
    choosers.delete(dispatch);
    try {await app.click(confirmation.point);await app.getAXState({emit:false});}
    catch(e) {stopped=true;record('CONFIRM_UNCERTAIN');throw e;}
    await consumeGui(reservation,'RETURNED');
    const afterConfirm=await observe();
    if (afterConfirm.download_started!==true) {stopped=true;record('DOWNLOAD_START_UNKNOWN');throw new Error('DOWNLOAD_START_UNKNOWN');}
    // Stop LINE input before the receipt is sealed: the retained receipt must
    // carry the full dispatch event order and nothing may touch LINE after it.
    stopped=true;latest=null;record('CEASE_INPUT_AFTER_DOWNLOAD_START');
    const evidence={run_id:action.run_id,action_id:action.action_id,execution_id:action.owner,observed_at:new Date().toISOString(),
      save_all_click_count:1,save_all_invocation_attempted:true,failure_boundary:'NONE',folder_chooser_appeared:true,
      download_started:true,provenance:'HOSTED_CUA_AND_SCREEN_CAPTURE_KIT'};
    const chooserEvidence={action_id:action.action_id,session_id:sessionId,destination:action.destination,
      full_path:action.destination,leaf:action.destination.split('/').at(-1),confirmation_attempts:1,frame_id:chooser.frame_id,
      confirmation_frame_id:afterConfirm.frame_id,confirmation_attempted:true};
    const dispatchEventNames=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
      'SAVE_ALL_RETURNED','CONFIRM_INVOCATION','CEASE_INPUT_AFTER_DOWNLOAD_START'];
    try {
      const start=trace.findIndex(t=>t.event==='ELLIPSIS_INVOCATION');
      requireFact(start>=0,'DISPATCH_TRACE_ORDER');
      const dispatchEvents=trace.slice(start).filter(t=>dispatchEventNames.includes(t.event));
      requireFact(dispatchEvents.map(t=>t.event).join(',')===dispatchEventNames.join(','),'DISPATCH_TRACE_ORDER');
      const receipt={version:'cua-dispatch-receipt-1',run_id:action.run_id,action_id:action.action_id,execution_id:action.owner,
        session_id:sessionId,pair_frame_id:dispatch.pairFrameId,popup_frame_id:dispatch.popupFrameId,support:dispatch.support,
        guard:dispatch.guard,
        reservations:[{kind:dispatch.reservation.kind,count:dispatch.reservation.count,reservation_id:dispatch.reservation.id,state:'CONSUMED'},
          {kind:reservation.kind,count:reservation.count,reservation_id:reservation.id,state:'CONSUMED'}],
        events:dispatchEvents.map(t=>({event:t.event,at:t.at})),chooser:chooserEvidence,download_started:true,
        save_all_click_count:1,cease_input:true};
      const savedReceipt=await retain({receipt,kind:'cua-dispatch-receipt-1',frameId:dispatch.pairFrameId,sessionId});
      requireFact(savedReceipt && typeof savedReceipt.path==='string' && savedReceipt.path.startsWith('harness-development/')
        && Number.isInteger(savedReceipt.bytes) && savedReceipt.bytes>0 && hex64(savedReceipt.sha256),'RETAINED_RECEIPT_REQUIRED');
      const recorded=await bridge('dispatch',{expected_token:dispatch.receiptToken,
        data:{evidence,chooser:chooserEvidence,download_started:true,receipt:savedReceipt}});
      requireFact(recorded?.result?.status==='DOWNLOAD_STARTED','DISPATCH_READBACK_REQUIRED');
    } catch(e) {stopped=true;record('DISPATCH_RECORD_UNCERTAIN',{message:String(e)});throw e;}
    return afterConfirm;
  }
  async function exactChooserV2({dispatch,locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload,
      destinationBaseline}) {
    const {action,chooser,dispatchInfo}=dispatch;
    requireFact(dispatch.appeared?.phase==='APPEARED' && dispatchInfo?.action_id===action.action_id,
      'CHOOSER_APPEARED_PROOF_REQUIRED');
    requireFact([locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload]
      .every(f=>typeof f==='function')
      &&destinationBaseline&&destinationBaseline.reference,
      'CHOOSER_LOCATORS_REQUIRED');
    const reservation=await reserveGui('chooser_inputs',4,action.run_id);
    const phases=[dispatch.appeared];let prior=dispatch.appeared;
    try {
      latest=null;await app.pressKey('super+shift+g');await app.getAXState({emit:false});
      const goObservation=await observe();
      const go=await makeChooserPhase('GO_TO_FOLDER',dispatchInfo,prior);phases.push(go);prior=go;
      record('GO_TO_FOLDER',{frameId:goObservation.frame_id});
      const field=await locatePathField(go.envelope);
      requireFact(Number.isInteger(field?.index) && field.index>=0 && field.frameId===goObservation.frame_id
        && field.role==='text field' && field.subrole==='PathTextField','PATH_FIELD_UNKNOWN');

      fresh(goObservation.frame_id);latest=null;await app.setValue(field.index,action.destination);await app.getAXState({emit:false});
      const filledObservation=await observe();
      const filled=await makeChooserPhase('PATH_FILLED',dispatchInfo,prior);phases.push(filled);prior=filled;
      record('PATH_FILLED',{frameId:filledObservation.frame_id});
      requireFact(await validatePath(filled.envelope,action.destination),'FULL_PATH_NOT_CONFIRMED');

      fresh(filledObservation.frame_id);latest=null;await app.pressKey('Return');await app.getAXState({emit:false});
      const selectedObservation=await observe();
      const selected=await makeChooserPhase('DESTINATION_SELECTED',dispatchInfo,prior);phases.push(selected);prior=selected;
      record('DESTINATION_SELECTED',{frameId:selectedObservation.frame_id});
      requireFact(await validateLeaf(selected.envelope,action.destination),'DESTINATION_LEAF_MISMATCH');
      const confirmation=await locateConfirm(selected.envelope);
      requireFact(point(confirmation?.point) && confirmation.frameId===selectedObservation.frame_id
        && confirmation.role==='button' && confirmation.enabled===true,'CONFIRM_CONTROL_UNKNOWN');
      fresh(selectedObservation.frame_id);

      destinationBaseline=await refreshBaseline({action,frameId:selectedObservation.frame_id,previous:destinationBaseline});
      requireFact(destinationBaseline?.reference&&destinationBaseline?.artifact?.inventory?.length===0
        &&destinationBaseline?.identity,'DESTINATION_NOT_EMPTY_BEFORE_CONFIRM');

      confirming.add(action.action_id);latest=null;record('CONFIRM_INVOCATION',{actionId:action.action_id,point:[...confirmation.point]});
      choosers.delete(dispatch);
      try {await app.click(confirmation.point);await app.getAXState({emit:false});}
      catch(error) {stopped=true;record('CONFIRM_UNCERTAIN');throw error;}
      await consumeGui(reservation,'RETURNED');
      const afterConfirm=await observe();
      const attempted=await makeChooserPhase('CONFIRM_ATTEMPTED',dispatchInfo,prior);phases.push(attempted);
      record('CONFIRM_ATTEMPTED',{frameId:afterConfirm.frame_id});
      stopped=true;latest=null;

      const confirmationInvokedAt=trace.findLast(t=>t.event==='CONFIRM_INVOCATION')?.wallAt;
      requireFact(typeof confirmationInvokedAt==='string' && typeof observeDownload==='function',
        'DOWNLOAD_OBSERVER_REQUIRED');
      const download=await observeDownload({action,dispatch,confirmation:selected.envelope.frame,
        attempted:attempted.envelope.frame,confirmationInvokedAt,destinationBaseline});
      requireFact(download?.evidence?.source_kind==='FILESYSTEM_DELTA' && download?.evidence?.before_inventory?.length===0
        && Array.isArray(download?.evidence?.after_inventory) && download.evidence.after_inventory.length>0
        && download.evidence.run_id===action.run_id && download.evidence.action_id===action.action_id
        && download.evidence.execution_id===action.owner && download.evidence.session_id===sessionId
        && download.evidence.destination===action.destination
        && download.evidence.baseline?.path===destinationBaseline.reference.path
        && download.evidence.baseline?.sha256===destinationBaseline.reference.sha256
        && download.evidence.confirmation_frame_id===selected.envelope.frame.frame_id
        && download.evidence.confirmation_invoked_at===confirmationInvokedAt,
        'DOWNLOAD_START_UNKNOWN');
      const downloadRef=download.reference??await retain({artifact:download.evidence,kind:'download-start',
        frameId:selected.envelope.frame.frame_id,sessionId});
      requireFact(downloadRef && typeof downloadRef.path==='string' && downloadRef.path.startsWith('harness-development/')
        && Number.isInteger(downloadRef.bytes) && downloadRef.bytes>0 && hex64(downloadRef.sha256),'DOWNLOAD_EVIDENCE_RETAIN_REQUIRED');
      record('DOWNLOAD_EVIDENCE_OBSERVED',{at:download.evidence.observed_at,reference:downloadRef});
      record('CEASE_INPUT_AFTER_DOWNLOAD_START');

      const evidence={run_id:action.run_id,action_id:action.action_id,execution_id:action.owner,
        observed_at:download.evidence.observed_at,save_all_click_count:1,save_all_invocation_attempted:true,
        failure_boundary:'NONE',folder_chooser_appeared:true,download_started:true,
        provenance:'HOSTED_CUA_SCREEN_CAPTURE_KIT_AND_FILESYSTEM_DELTA'};
      const chooserEvidence={action_id:action.action_id,session_id:sessionId,destination:action.destination,
        full_path:action.destination,leaf:action.destination.split('/').at(-1),confirmation_attempts:1,
        frame_id:dispatch.appeared.envelope.frame.frame_id,
        confirmation_frame_id:selected.envelope.frame.frame_id,confirmation_attempted:true};
      const expectedEvents=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
        'SAVE_ALL_RETURNED','CHOOSER_APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED',
        'CONFIRM_INVOCATION','CONFIRM_ATTEMPTED','DOWNLOAD_EVIDENCE_OBSERVED','CEASE_INPUT_AFTER_DOWNLOAD_START'];
      const start=trace.findIndex(t=>t.event==='ELLIPSIS_INVOCATION');
      requireFact(start>=0,'DISPATCH_TRACE_ORDER');
      const dispatchEvents=trace.slice(start).filter(t=>expectedEvents.includes(t.event));
      requireFact(dispatchEvents.map(t=>t.event).join(',')===expectedEvents.join(','),'DISPATCH_TRACE_ORDER');
      const receipt={version:'cua-dispatch-receipt-2',run_id:action.run_id,action_id:action.action_id,
        execution_id:action.owner,session_id:sessionId,pair_frame_id:dispatch.pairFrameId,
        popup_frame_id:dispatch.popupFrameId,support:dispatch.support,guard:dispatch.guard,
        reservations:[{kind:dispatch.reservation.kind,count:dispatch.reservation.count,
          reservation_id:dispatch.reservation.id,state:'CONSUMED'},{kind:reservation.kind,count:reservation.count,
          reservation_id:reservation.id,state:'CONSUMED'}],
        events:dispatchEvents.map(t=>({event:t.event,at:t.event==='DOWNLOAD_EVIDENCE_OBSERVED'
          ?download.evidence.observed_at:t.event==='CONFIRM_INVOCATION'?t.wallAt:t.wallAt})),
        chooser:chooserEvidence,chooser_phases:phases.map(p=>p.reference),
        confirmation_frame:selected.envelope.frame.frame,confirmation_point:[...confirmation.point],download_evidence:downloadRef,
        save_all_click_count:1,cease_input:true};
      const savedReceipt=await retain({receipt,kind:'cua-dispatch-receipt-2',frameId:dispatch.pairFrameId,sessionId});
      requireFact(savedReceipt && typeof savedReceipt.path==='string' && savedReceipt.path.startsWith('harness-development/')
        && Number.isInteger(savedReceipt.bytes) && savedReceipt.bytes>0 && hex64(savedReceipt.sha256),
        'RETAINED_RECEIPT_REQUIRED');
      const recorded=await bridge('dispatch',{expected_token:dispatch.receiptToken,
        data:{evidence,chooser:chooserEvidence,download_started:true,receipt:savedReceipt}});
      requireFact(recorded?.result?.status==='DOWNLOAD_STARTED','DISPATCH_READBACK_REQUIRED');
      return afterConfirm;
    } catch(error) {
      stopped=true;latest=null;record('DISPATCH_RECORD_UNCERTAIN',{message:String(error)});throw error;
    }
  }
  async function boundedScroll(observation,target,direction,distance) {
    fresh(observation.frame_id);requireFact(observation.surface==='ALBUMS','SCROLL_SURFACE_UNKNOWN');
    requireFact(point(target) && ['up','down'].includes(direction) && Number.isFinite(distance) && distance>0 && distance<=0.25,'SCROLL_POLICY');
    const reservation = await reserveGui('scroll',1,null);
    latest=null;record('ONE_SCROLL');
    try {await app.scroll(target,direction,distance);await app.getAXState({emit:false});}
    catch(e) {stopped=true;throw e;}
    await consumeGui(reservation,'RETURNED');
    try {
      const after=await observe();
      const progress=verifyAlbumScroll(observation,after);
      record('SCROLL_VERIFIED_NEW_CARD',progress);
      return after;
    } catch(error) {
      stopped=true;latest=null;record('SCROLL_UNVERIFIED',{message:String(error)});
      throw error;
    }
  }
  function ceaseInput() {stopped=true;latest=null;record('CEASE_INPUT');}
  return Object.freeze({sessionId,observe,openAlbum,originalIntent,originalAtomicDispatch,exactChooser,boundedScroll,
    calibrateMenu,ceaseInput,trace:()=>[...trace]});
}

// A fresh object for post-VERIFIED navigation. It exposes no intent, menu, chooser,
// or dispatch capability and cannot revive a stopped transaction session.
export function createNavigationObserver({app,bridge,retain,classify,sessionId=randomUUID(),
    clock=()=>performance.now()}) {
  requireFact(app&&['getAXStateAndScreenshot','getAXState','click','pressKey','scroll'].every(k=>typeof app[k]==='function'),
    'DOCUMENTED_APP_REQUIRED');
  requireFact(typeof bridge==='function'&&typeof retain==='function'&&typeof classify==='function',
    'NAVIGATION_OBSERVER_DEPENDENCIES');
  let latest=null,closed=false;const trace=[];
  const record=(event,extra={})=>trace.push(Object.freeze({event,at:clock(),wallAt:new Date().toISOString(),...extra}));
  async function reserve(kind,count) {
    requireFact(!closed,'NAVIGATION_OBSERVER_CLOSED');
    const response=await bridge('gui_reserve',{data:{kind,count,run_id:null,owner:sessionId}});
    requireFact(response?.reservation?.kind===kind&&response.reservation.count===count,'GUI_LEDGER_RESERVE_REFUSED');
    latest=null;return response.reservation;
  }
  async function consume(reservation) {
    const response=await bridge('gui_consume',{data:{reservation_id:reservation.id,outcome:'RETURNED'}});
    requireFact(response?.reservation?.state==='CONSUMED','GUI_LEDGER_CONSUME_REFUSED');
  }
  async function observe() {
    requireFact(!closed,'NAVIGATION_OBSERVER_CLOSED');
    const started=clock(),requestStartedAtUtc=new Date().toISOString();
    const rawCapture=await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
    const ended=clock(),requestEndedAtUtc=new Date().toISOString();
    requireFact(Number.isFinite(started)&&Number.isFinite(ended)&&ended>=started&&typeof rawCapture?.state==='string',
      'CAPTURE_INCOMPLETE');
    const screenshot=normalizeScreenshotBytes(rawCapture.screenshot);
    const capture=Object.freeze({...rawCapture,screenshot});
    const frameId=sha(screenshot);
    const monotonicInterval=Object.freeze({start_ms:started,end_ms:ended,duration_ms:ended-started});
    const saved=await retain({screenshot,ax:capture.state,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    verifyFrameReference(saved,frameId,screenshot.byteLength);
    const observation=await classify({capture,saved,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    requireFact(observation.frame_id===frameId&&observation.session_id===sessionId,'CLASSIFIER_FRAME_MISMATCH');
    latest=Object.freeze({started,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,
      monotonicInterval,frameId,capture,saved,observation});return observation;
  }
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
}
