// Load only inside the documented cua_repl kernel with a genuine App object.
// Ordinary Node tests supply external fake I/O; no CUA SDK or GUI synthesis here.
import {createHash, randomUUID} from 'node:crypto';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requireFact = (ok, code) => {if (!ok) throw new Error(code);};
const point = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);

export function createHostedSession({app, bridge, retain, classify, sessionId = randomUUID(),
    clock = () => performance.now(), wait = ms => new Promise(r => setTimeout(r,ms)), menuWaitMs = 1200}) {
  requireFact(app && ['getAXStateAndScreenshot','getAXState','click','pressKey','setValue','scroll'].every(k => typeof app[k] === 'function'), 'DOCUMENTED_APP_REQUIRED');
  requireFact(typeof bridge === 'function' && typeof retain === 'function' && typeof classify === 'function','HOST_BRIDGE_REQUIRED');
  requireFact(Number.isInteger(menuWaitMs) && menuWaitMs >= 800 && menuWaitMs <= 1500,'MENU_WAIT_OUTSIDE_POLICY');
  let latest = null, stopped = false, confirming = new Set();
  const permits = new WeakMap(), choosers = new WeakMap(), trace = [];
  const record = (event, extra={}) => trace.push(Object.freeze({event, at:clock(), ...extra}));
  function fresh(frameId) {
    requireFact(!stopped && latest && latest.frameId === frameId && clock() >= latest.at && clock()-latest.at <= 2000,'FRESH_CAPTURE_REQUIRED');
  }
  async function observe() {
    requireFact(!stopped,'SESSION_STOPPED');
    const start = clock();
    const capture = await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
    requireFact(capture.screenshot instanceof Uint8Array && typeof capture.state === 'string','CAPTURE_INCOMPLETE');
    const frameId = sha(capture.screenshot);
    const saved = await retain({screenshot:capture.screenshot,ax:capture.state,frameId,sessionId});
    const observation = await classify({capture,saved,frameId,sessionId});
    requireFact(observation.frame_id === frameId && observation.session_id === sessionId,'CLASSIFIER_FRAME_MISMATCH');
    // Timestamp starts before capture, never renewed by slow classification/persistence.
    latest = Object.freeze({frameId,at:start,observation});
    return observation;
  }
  async function openAlbum(prepared) {
    fresh(prepared.frame_id);requireFact(point(prepared.click),'INVALID_CARD_POINT');
    record('ALBUM_OPEN_INVOCATION',{runId:prepared.run_id});
    latest = null;
    try {await app.click(prepared.click); await app.getAXState({emit:false});}
    catch(e) {stopped=true;throw e;}
    return observe();
  }
  async function originalIntent({receiptToken,freshObservation}) {
    fresh(freshObservation.frame_id);
    const committed = await bridge('intent',{expected_token:receiptToken,data:{fresh:freshObservation}});
    requireFact(committed.new_intent === true && committed.result?.status === 'ORIGINAL_INTENT_COMMITTED','NEW_INTENT_REQUIRED');
    fresh(freshObservation.frame_id);
    requireFact(committed.result.frame_id === latest.frameId && committed.result.session_id === sessionId,
      'INTENT_FRAME_MISMATCH');
    const token = Object.freeze({});
    permits.set(token,Object.freeze({result:committed.result,receiptToken:committed.receipt_token,
      frameId:latest.frameId,issuedAt:clock(),deadline:latest.at+2000}));
    return token;
  }
  async function originalAtomicDispatch(token) {
    const permit=permits.get(token);requireFact(permit,'NO_ORIGINAL_PERMISSION');
    // Consume before the first call. Throw/timeout/crash never leaves a reusable token.
    permits.delete(token);
    fresh(permit.frameId);
    const action=permit.result;
    requireFact(point(action.ellipsis) && point(action.save_all),'INVALID_MENU_POINTS');
    requireFact(clock()-permit.issuedAt<=2000,'PERMIT_EXPIRED');
    record('ELLIPSIS_INVOCATION',{actionId:action.action_id});
    latest=null;
    try {
      await app.click(action.ellipsis);
      record('ELLIPSIS_RETURNED');
      await wait(menuWaitMs);
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_SAVE_ALL');
      record('SAVE_ALL_INVOCATION',{actionId:action.action_id});
      await app.click(action.save_all);
      record('SAVE_ALL_RETURNED');
    } catch(error) {
      stopped=true;record('DISPATCH_UNCERTAIN',{message:String(error)});throw error;
    }
    // No observe, persistence, bridge call, keyboard or app switch between the two clicks.
    await app.getAXState({emit:false});
    const chooser=await observe();
    requireFact(chooser.surface==='FOLDER_CHOOSER','CHOOSER_NOT_CONFIRMED');
    const dispatch=Object.freeze({action,receiptToken:permit.receiptToken,chooser,trace:[...trace]});
    choosers.set(dispatch,true);
    return dispatch;
  }
  async function exactChooser({dispatch,locatePathField,validatePath,validateLeaf,locateConfirm}) {
    requireFact(choosers.has(dispatch),'NO_ORIGINAL_CHOOSER_PERMISSION');
    const {action,chooser}=dispatch;
    fresh(chooser.frame_id);requireFact(chooser.surface==='FOLDER_CHOOSER','CHOOSER_NOT_CONFIRMED');
    requireFact(!confirming.has(action.action_id),'CONFIRMATION_ALREADY_ATTEMPTED');
    requireFact([locatePathField,validatePath,validateLeaf,locateConfirm].every(f => typeof f==='function'),'CHOOSER_LOCATORS_REQUIRED');
    // One Go-to-Folder navigation, then a newly observed actual text field.
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
    return observe();
  }
  async function boundedScroll(observation,target,direction,distance) {
    fresh(observation.frame_id);requireFact(observation.surface==='ALBUMS','SCROLL_SURFACE_UNKNOWN');
    requireFact(point(target) && ['up','down'].includes(direction) && Number.isFinite(distance) && distance>0 && distance<=1,'SCROLL_POLICY');
    latest=null;record('ONE_SCROLL');
    try {await app.scroll(target,direction,distance);await app.getAXState({emit:false});}
    catch(e) {stopped=true;throw e;}
    return observe();
  }
  function ceaseInput() {stopped=true;latest=null;record('CEASE_INPUT');}
  return Object.freeze({sessionId,observe,openAlbum,originalIntent,originalAtomicDispatch,exactChooser,boundedScroll,
    ceaseInput,trace:()=>[...trace]});
}
