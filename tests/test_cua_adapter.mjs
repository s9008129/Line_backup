import test from 'node:test';
import assert from 'node:assert/strict';
import {createHostedSession} from '../scripts/line_backup_cua_adapter.mjs';

function fixture(options={}) {
  const calls=[];let now=0,clicks=0,intents=0,surface='ALBUM_DETAIL';
  const app={
    async getAXStateAndScreenshot(){calls.push('capture');return {state:'fixture AX',screenshot:new Uint8Array([1,2,3])};},
    async getAXState(){calls.push('ax');return 'fixture AX';},
    async click(p){calls.push(['click',p]);clicks++;if(clicks===options.throwAt)throw new Error('external click error');surface='FOLDER_CHOOSER';},
    async pressKey(k){calls.push(['key',k]);},async setValue(i,s){calls.push(['setValue',i,s]);},async scroll(){calls.push('scroll');}
  };
  const session=createHostedSession({app,sessionId:'execution',clock:()=>now,wait:async ms=>{calls.push(['timer',ms]);now+=options.timerDuration??ms;},
    retain:async o=>{calls.push('retain');return o;},classify:async o=>{calls.push('classify');return {frame_id:o.frameId,session_id:o.sessionId,surface};},
    bridge:async (operation,payload)=>{
      calls.push(['bridge',operation]);intents++;
      if(options.loaded || intents>1)throw new Error('LOADED_INTENT_NO_PERMISSION');
      return {new_intent:true,receipt_token:'opaque-token',result:{status:'ORIGINAL_INTENT_COMMITTED',frame_id:payload.data.fresh.frame_id,
        session_id:'execution',run_id:'run',owner:'execution',action_id:'action',destination:'/fixture/new',ellipsis:[100,10],save_all:[100,50]}};
    }});
  return {session,calls,advance:n=>{now+=n;},getClicks:()=>clicks};
}

test('original pair contains only two clicks and timer; one-shot cannot replay',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const before=f.calls.length;await f.session.originalAtomicDispatch(permit);
  assert.deepEqual(f.calls.slice(before,before+3),[['click',[100,10]],['timer',1200],['click',[100,50]]]);
  assert.equal(f.calls[before+3],'ax');
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);assert.equal(f.getClicks(),2);
});
test('loaded JSON cannot mint a dispatch or chooser capability',async()=>{
  const f=fixture({loaded:true});const observation=await f.session.observe();
  await assert.rejects(f.session.originalIntent({receiptToken:'old',freshObservation:observation}),/LOADED_INTENT/);
  await assert.rejects(f.session.originalAtomicDispatch({new_intent:true}),/NO_ORIGINAL_PERMISSION/);
  await assert.rejects(f.session.exactChooser({dispatch:{action:{},chooser:{}}}),/NO_ORIGINAL_CHOOSER_PERMISSION/);
  assert.equal(f.getClicks(),0);
});
test('ellipse error never invokes SaveAll; all tokens stay consumed',async()=>{
  const f=fixture({throwAt:1});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.session.originalAtomicDispatch(permit),/external click/);
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);
  assert.equal(f.getClicks(),1);assert(!f.session.trace().some(t=>t.event==='SAVE_ALL_INVOCATION'));
});
test('SaveAll error is attempted once and prohibits replay',async()=>{
  const f=fixture({throwAt:2});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.session.originalAtomicDispatch(permit),/external click/);
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);
  assert.equal(f.getClicks(),2);
});
test('expired capture and expired second-click boundary both stop',async()=>{
  const stale=fixture();const o=await stale.session.observe();stale.advance(2001);
  await assert.rejects(stale.session.originalIntent({receiptToken:'opaque',freshObservation:o}),/FRESH_CAPTURE_REQUIRED/);
  const f=fixture({timerDuration:2500});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.session.originalAtomicDispatch(permit),/PERMIT_EXPIRED_BEFORE_SAVE_ALL/);assert.equal(f.getClicks(),1);
});
test('correct chooser path and fresh control confirmed exactly once',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const dispatch=await f.session.originalAtomicDispatch(permit);
  const options={dispatch,locatePathField:async o=>({index:7,frameId:o.frame_id,role:'text field'}),
    validatePath:async (o,p)=>p==='/fixture/new',validateLeaf:async(o,p)=>p.endsWith('/new'),
    locateConfirm:async o=>({point:[120,80],frameId:o.frame_id,role:'button'})};
  await f.session.exactChooser(options);
  assert.equal(f.getClicks(),3);assert(f.calls.some(c=>Array.isArray(c)&&c[0]==='setValue'&&c[2]==='/fixture/new'));
  await assert.rejects(f.session.exactChooser(options),/NO_ORIGINAL_CHOOSER_PERMISSION/);
  assert.equal(f.getClicks(),3);
});
test('wrong full path refuses navigation/confirmation',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const dispatch=await f.session.originalAtomicDispatch(permit);
  await assert.rejects(f.session.exactChooser({dispatch,locatePathField:async o=>({index:7,frameId:o.frame_id,role:'text field'}),
    validatePath:async()=>false,validateLeaf:async()=>true,locateConfirm:async o=>({point:[1,1],frameId:o.frame_id,role:'button'})}),/FULL_PATH_NOT_CONFIRMED/);
  assert.equal(f.getClicks(),2);assert(!f.calls.some(c=>Array.isArray(c)&&c[0]==='key'&&c[1]==='Return'));
});
test('a stale field index is refused before typing',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const dispatch=await f.session.originalAtomicDispatch(permit);
  await assert.rejects(f.session.exactChooser({dispatch,locatePathField:async()=>({index:7,frameId:'old',role:'text field'}),
    validatePath:async()=>true,validateLeaf:async()=>true,locateConfirm:async()=>({})}),/PATH_FIELD_UNKNOWN/);
  assert(!f.calls.some(c=>Array.isArray(c)&&c[0]==='setValue'));
});
