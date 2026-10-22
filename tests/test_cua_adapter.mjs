import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {deflateSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import {createHostedSession,createAlbumSupportCallbacks,createNavigationObserver,normalizeScreenshotBytes}
  from '../scripts/line_backup_cua_adapter.mjs';

function fixture(options={}) {
  const calls=[],ledger=[];let now=0,clicks=0,intents=0,captureIndex=0,surface=options.initialSurface??'ALBUM_DETAIL',downloadStarted=false,reservationSeq=0;
  const app={
    async getAXStateAndScreenshot(){calls.push('capture');const frame=options.scrollFrames?.[captureIndex++];
      return frame?{state:frame.axRaw,screenshot:frame.screenshot}:{state:'fixture AX',
        screenshot:options.screenshot??new Uint8Array([1,2,3])};},
    async getAXState(){calls.push('ax');return 'fixture AX';},
    async click(p){calls.push(['click',p]);clicks++;if(clicks===options.throwAt)throw new Error('external click error');
      if(clicks===1)surface='ALBUM_DETAIL';else if(clicks===2)surface='FOLDER_CHOOSER';else downloadStarted=true;},
    async pressKey(k){calls.push(['key',k]);},async setValue(i,s){calls.push(['setValue',i,s]);},async scroll(){calls.push('scroll');}
  };
  const session=createHostedSession({app,sessionId:'execution',clock:()=>now,wait:async ms=>{calls.push(['timer',ms]);now+=options.timerDuration??ms;},
    retain:async o=>{calls.push('retain');const ref={path:`harness-development/${o.kind??'frame'}-${o.frameId.slice(0,12)}.json`,
      bytes:o.screenshot?o.screenshot.byteLength:160,sha256:o.frameId};
      if(o.screenshot){const ax=Buffer.from(o.ax);ref.ax={path:`harness-development/ax-${o.frameId.slice(0,12)}.txt`,
        bytes:ax.byteLength,sha256:createHash('sha256').update(ax).digest('hex')};}
      return ref;},
    classify:async o=>{calls.push('classify');options.onClassify?.(o);return {frame_id:o.frameId,session_id:o.sessionId,surface,download_started:downloadStarted,
      captured_at:o.capturedAt,...options.scrollFrames?.[captureIndex-1]?.observation};},
    bridge:async (operation,payload)=>{
      calls.push(['bridge',operation]);
      if(operation==='gui_reserve'){
        if(options.ledgerExhausted)return {reservation:null};
        ledger.push({op:operation,data:payload.data});
        return {reservation:{id:`res-${payload.data.kind}-${++reservationSeq}`,kind:payload.data.kind,count:payload.data.count}};
      }
      if(operation==='gui_consume'){ledger.push({op:operation,data:payload.data});
        return {reservation:{id:payload.data.reservation_id,state:'CONSUMED'}};}
      if(operation==='dispatch')return {result:{status:'DOWNLOAD_STARTED'}};
      intents++;
      if(options.loaded || intents>1)throw new Error('LOADED_INTENT_NO_PERMISSION');
      return {new_intent:true,receipt_token:'opaque-token',result:{status:'ORIGINAL_INTENT_COMMITTED',dispatch_authorized:options.dispatchAuthorized??true,
        fixture:options.fixture??false,frame_id:payload.data.fresh.frame_id,
        session_id:'execution',run_id:'run',owner:'execution',action_id:'action',destination:'/fixture/new',ellipsis:[100,10],save_all:[100,50]}};
    }});
  const dispatch=(permit,overrides={})=>session.originalAtomicDispatch(permit,{captureMenuSupport:async ({pairFrameId,sessionId})=>{
      calls.push('sck-capture');return {provider:'SCREEN_CAPTURE_KIT',pairFrameId,popupFrameId:overrides.popupFrameId??'b'.repeat(64),sessionId,
        reference:{path:'harness-development/support.json',bytes:40,sha256:'a'.repeat(64)},
        uncertaintyPx:2,safeMarginPx:6,intersectionPx:[100,50,40,30]};},
    guardMenu:async ({action,support,pairFrameId,sessionId})=>{calls.push('sck-guard');
      return {verdict:options.guardVerdict??'PASS',provider:'SCREEN_CAPTURE_KIT',pairFrameId,
        popupFrameId:overrides.guardPopupFrameId??support.popupFrameId,
        supportSha256:support.reference.sha256,actionPoint:overrides.guardActionPoint??action.save_all};}});
  return {session,calls,ledger,dispatch,advance:n=>{now+=n;},getClicks:()=>clicks};
}

test('byte normalizer accepts foreign Uint8Array and honors byteOffset for Buffer views',()=>{
  const foreign=runInNewContext('new Uint8Array([9,1,2,3,8]).subarray(1,4)');
  assert.equal(foreign instanceof Uint8Array,false);
  const copied=normalizeScreenshotBytes(foreign);
  assert.deepEqual([...copied],[1,2,3]);
  assert.notEqual(copied.buffer,foreign.buffer);
  const source=Buffer.from([9,4,5,6,8]).subarray(1,4);
  const bufferCopy=normalizeScreenshotBytes(source);
  assert.deepEqual([...bufferCopy],[4,5,6]);
  assert.equal(createHash('sha256').update(bufferCopy).digest('hex'),
    createHash('sha256').update(Buffer.from([4,5,6])).digest('hex'));
});

test('byte normalizer rejects non-byte views, DataView, empty and oversized inputs',()=>{
  for(const value of [new Uint16Array([1]),new DataView(new ArrayBuffer(1)),new Uint8Array(),
    new Uint8Array(16*1024*1024+1),{buffer:new ArrayBuffer(1),byteOffset:0,byteLength:1}])
    assert.throws(()=>normalizeScreenshotBytes(value),/CAPTURE_BYTES_INVALID/);
});

test('session capture hashes and retains the copied cross-realm bytes with the request interval',async()=>{
  const foreign=runInNewContext('new Uint8Array([7,1,2,3,9]).subarray(1,4)');
  let classified;
  const f=fixture({screenshot:foreign,onClassify:value=>{classified=value;}});
  const observation=await f.session.observe();
  const expected=createHash('sha256').update(Buffer.from([1,2,3])).digest('hex');
  assert.equal(observation.frame_id,expected);
  assert.deepEqual([...classified.capture.screenshot],[1,2,3]);
  assert.notEqual(classified.capture.screenshot.buffer,foreign.buffer);
  assert.equal(classified.saved.bytes,3);
  assert.equal(classified.saved.sha256,expected);
  assert.equal(classified.requestStartedAtUtc,classified.capturedAt);
  assert.equal(classified.monotonicInterval.duration_ms,
    classified.monotonicInterval.end_ms-classified.monotonicInterval.start_ms);
  assert.ok(Date.parse(classified.requestEndedAtUtc)>=Date.parse(classified.requestStartedAtUtc));
});

test('navigation observer uses the same copied-byte and request-time boundary',async()=>{
  const foreign=runInNewContext('new Uint8Array([8,2,4,6,9]).subarray(1,4)');
  let classified;
  const nav=createNavigationObserver({
    app:{async getAXStateAndScreenshot(){return {state:'navigation AX',screenshot:foreign};},
      async getAXState(){return 'navigation AX';},async click(){},async pressKey(){},async setValue(){},async scroll(){}},
    bridge:async()=>({}),
    retain:async value=>{const ax=Buffer.from(value.ax);return {path:'harness-development/frame.bin',
      bytes:value.screenshot.byteLength,sha256:createHash('sha256').update(value.screenshot).digest('hex'),
      ax:{path:'harness-development/ax.txt',bytes:ax.byteLength,sha256:createHash('sha256').update(ax).digest('hex')}};},
    classify:async value=>{classified=value;return {frame_id:value.frameId,session_id:value.sessionId};},
    sessionId:'navigation',clock:()=>1
  });
  const observation=await nav.observe();
  assert.equal(observation.frame_id,createHash('sha256').update(Buffer.from([2,4,6])).digest('hex'));
  assert.deepEqual([...classified.capture.screenshot],[2,4,6]);
  assert.equal(classified.monotonicInterval.start_ms,1);
  assert.equal(classified.monotonicInterval.end_ms,1);
});

test('original pair contains only two clicks and timer; one-shot cannot replay',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const before=f.calls.length;await f.dispatch(permit);
  assert.deepEqual(f.calls.slice(before,before+8),[['bridge','gui_reserve'],['click',[100,10]],['timer',1200],'sck-capture','sck-guard',['click',[100,50]],['bridge','gui_consume'],'ax']);
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);assert.equal(f.getClicks(),2);
});
test('loaded JSON cannot mint a dispatch or chooser capability',async()=>{
  const f=fixture({loaded:true});const observation=await f.session.observe();
  await assert.rejects(f.session.originalIntent({receiptToken:'old',freshObservation:observation}),/LOADED_INTENT/);
  await assert.rejects(f.session.originalAtomicDispatch({new_intent:true}),/NO_ORIGINAL_PERMISSION/);
  await assert.rejects(f.session.exactChooser({dispatch:{action:{},chooser:{}}}),/NO_ORIGINAL_CHOOSER_PERMISSION/);
  assert.equal(f.getClicks(),0);
});
test('fixture authority cannot mint a live app dispatch token',async()=>{
  const f=fixture({fixture:true,dispatchAuthorized:false});const observation=await f.session.observe();
  await assert.rejects(f.session.originalIntent({receiptToken:'opaque',freshObservation:observation}),/LIVE_DISPATCH_AUTHORITY_REQUIRED/);
  assert.equal(f.getClicks(),0);
});
test('ellipse error never invokes SaveAll; all tokens stay consumed',async()=>{
  const f=fixture({throwAt:1});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit),/external click/);
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);
  assert.equal(f.getClicks(),1);assert(!f.session.trace().some(t=>t.event==='SAVE_ALL_INVOCATION'));
});
test('SaveAll error is attempted once and prohibits replay',async()=>{
  const f=fixture({throwAt:2});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit),/external click/);
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);
  assert.equal(f.getClicks(),2);
});
test('expired capture and expired second-click boundary both stop',async()=>{
  const stale=fixture();const o=await stale.session.observe();stale.advance(5001);
  await assert.rejects(stale.session.originalIntent({receiptToken:'opaque',freshObservation:o}),/FRESH_CAPTURE_REQUIRED/);
  const f=fixture({timerDuration:5100});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit),/PERMIT_EXPIRED_BEFORE_(?:MENU_CAPTURE|SAVE_ALL)/);assert.equal(f.getClicks(),1);
});
test('correct chooser path and fresh control confirmed exactly once',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const dispatch=await f.dispatch(permit);
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
  const dispatch=await f.dispatch(permit);
  await assert.rejects(f.session.exactChooser({dispatch,locatePathField:async o=>({index:7,frameId:o.frame_id,role:'text field'}),
    validatePath:async()=>false,validateLeaf:async()=>true,locateConfirm:async o=>({point:[1,1],frameId:o.frame_id,role:'button'})}),/FULL_PATH_NOT_CONFIRMED/);
  assert.equal(f.getClicks(),2);assert(!f.calls.some(c=>Array.isArray(c)&&c[0]==='key'&&c[1]==='Return'));
});
test('a stale field index is refused before typing',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  const dispatch=await f.dispatch(permit);
  await assert.rejects(f.session.exactChooser({dispatch,locatePathField:async()=>({index:7,frameId:'old',role:'text field'}),
    validatePath:async()=>true,validateLeaf:async()=>true,locateConfirm:async()=>({})}),/PATH_FIELD_UNKNOWN/);
  assert(!f.calls.some(c=>Array.isArray(c)&&c[0]==='setValue'));
});
test('native scroll is limited to one quarter viewport per invocation',async()=>{
  // Synthetic data only: the same rendered list moves upward by 50 px in a 200 px viewport.
  const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
  const crc32=bytes=>{let crc=0xffffffff;for(const byte of bytes){crc^=byte;
    for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;};
  const chunk=(type,data)=>{const name=Buffer.from(type),length=Buffer.alloc(4),crc=Buffer.alloc(4);
    length.writeUInt32BE(data.length);crc.writeUInt32BE(crc32(Buffer.concat([name,data])));
    return Buffer.concat([length,name,data,crc]);};
  const frame=(offset,capturedAt)=>{
    const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(200,0);ihdr.writeUInt32BE(200,4);ihdr[8]=8;ihdr[9]=2;
    const rows=[];
    for(let y=0;y<200;y++){
      const row=Buffer.alloc(601,255);row[0]=0;const sourceY=y+offset,localY=sourceY%80;
      for(let x=10;x<190&&sourceY<240&&localY<70;x++){
        const metadata=x>=20&&((x<120&&localY>=42&&localY<50)||(x<40&&localY>=55&&localY<63));
        const shade=metadata?0:50+Math.floor(sourceY/80)*50;
        row[1+x*3]=shade;row[2+x*3]=shade;row[3+x*3]=shade;
      }
      rows.push(row);
    }
    const screenshot=new Uint8Array(Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),
      chunk('IHDR',ihdr),chunk('IDAT',deflateSync(Buffer.concat(rows))),chunk('IEND',Buffer.alloc(0))]));
    const cards=[0,1,2].map(i=>({fingerprint:{start_date:`2024-0${i+1}-01`,end_date:`2024-0${i+1}-02`,expected_images:i+2},
      card_bounds:[10,i*80-offset,180,70],metadata_bounds:[[20,i*80-offset+42,100,8],[20,i*80-offset+55,20,8]],
      fully_visible:i*80-offset>=0&&i*80-offset+70<=200}));
    const axCards=cards.filter(card=>card.fully_visible).map(card=>({...card.fingerprint,
      bounds:card.card_bounds,metadata_bounds:card.metadata_bounds}));
    const axRaw=JSON.stringify({synthetic:true,role:'AXList',viewport:[0,0,200,200],pid:7,window_id:1,
      group_key:'fixture-group',scroll_offset:offset,captured_at:capturedAt,rows:cards});
    return {screenshot,axRaw,observation:{provider:'HOSTED_CUA',group_key:'fixture-group',pid:7,window_id:1,
      process_instance:JSON.stringify(['jp.naver.line.mac',7,1,0]),layout_key:'fixture-layout',width:200,height:200,
      native_scale:1,captured_at:capturedAt,viewport_bounds:[0,0,200,200],mapping:{uncertainty:2},
      cards:cards.filter(card=>card.fully_visible),
      parsed_ax:{raw_sha256:digest(Buffer.from(axRaw)),scroll_offset:offset,cards:axCards}}};
  };
  const f=fixture({initialSurface:'ALBUMS',scrollFrames:[frame(0,'2026-10-17T00:00:00.000Z'),
    frame(50,'2026-10-17T00:00:00.010Z')]});const observation=await f.session.observe();
  await assert.rejects(f.session.boundedScroll(observation,[100,100],'down',0.251),/SCROLL_POLICY/);
  assert(!f.calls.includes('scroll'));
  await f.session.boundedScroll(observation,[100,100],'down',0.25);
  assert.equal(f.calls.filter(c=>c==='scroll').length,1);
  const reservations=f.ledger.filter(e=>e.op==='gui_reserve').map(e=>e.data.kind);
  assert.deepEqual(reservations,['scroll']);
  const scrollAt=f.calls.indexOf('scroll'),consumeAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_consume');
  const reserveAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_reserve');
  assert(reserveAt<scrollAt&&scrollAt<consumeAt);
});

test('SCK pair and popup frames stay distinct and guard binds both ids',async()=>{
  const invokeProducer=async req=>req.mode==='capture'
    ?{provider:'SCREEN_CAPTURE_KIT',pairFrameId:req.pairFrameId,popupFrameId:'b'.repeat(64),sessionId:req.sessionId,
      reference:{path:'harness-development/support.json',bytes:40,sha256:'a'.repeat(64)},
      uncertaintyPx:2,safeMarginPx:6,intersectionPx:[100,50,40,30]}
    :{verdict:'PASS',provider:'SCREEN_CAPTURE_KIT',pairFrameId:req.pairFrameId,popupFrameId:req.popupFrameId,
      supportSha256:req.support.sha256,actionPoint:req.saveAllPoint};
  const callbacks=createAlbumSupportCallbacks({invokeProducer});
  const action={save_all:[100,50]},pairFrameId='c'.repeat(64);
  const support=await callbacks.captureMenuSupport({action,pairFrameId,sessionId:'execution',requestedAt:0,
    cuaFrame:{path:'harness-development/pair.png',bytes:3,sha256:pairFrameId},cuaCapturedAt:'2026-10-10T00:00:00.000Z'});
  assert.notEqual(support.popupFrameId,support.pairFrameId);
  const guard=await callbacks.guardMenu({action,support,pairFrameId,sessionId:'execution'});
  assert.equal(guard.verdict,'PASS');assert.equal(guard.supportSha256,support.reference.sha256);
  assert.deepEqual(guard.actionPoint,action.save_all);
});

test('SCK capture refuses a popup frame equal to the pair frame',async()=>{
  let guardCalls=0;
  const callbacks=createAlbumSupportCallbacks({invokeProducer:async req=>{if(req.mode==='guard'){guardCalls++;return {};}
    return {provider:'SCREEN_CAPTURE_KIT',pairFrameId:req.pairFrameId,popupFrameId:req.pairFrameId,sessionId:req.sessionId,
      reference:{path:'harness-development/support.json',bytes:40,sha256:'a'.repeat(64)},
      uncertaintyPx:2,safeMarginPx:6,intersectionPx:[100,50,40,30]};}});
  await assert.rejects(callbacks.captureMenuSupport({action:{save_all:[100,50]},pairFrameId:'c'.repeat(64),sessionId:'execution',
    requestedAt:0,cuaFrame:{path:'harness-development/pair.png',bytes:3,sha256:'c'.repeat(64)},cuaCapturedAt:'2026-10-10T00:00:00.000Z'}),
    /SCK_SUPPORT_REQUIRED/);
  assert.equal(guardCalls,0);
});

test('popup frame equal to the pair frame refuses before SaveAll',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit,{popupFrameId:observation.frame_id}),/SCK_SUPPORT_REQUIRED/);
  assert.equal(f.getClicks(),1);assert(!f.session.trace().some(t=>t.event==='SAVE_ALL_INVOCATION'));
});

test('guard popup frame mismatch refuses before SaveAll',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit,{guardPopupFrameId:'d'.repeat(64)}),/SCK_MENU_GUARD_REFUSED/);
  assert.equal(f.getClicks(),1);
});

test('guard action point change refuses before SaveAll',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit,{guardActionPoint:[101,50]}),/SCK_MENU_GUARD_REFUSED/);
  assert.equal(f.getClicks(),1);
});

test('menu callbacks are required before the ellipsis click',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.session.originalAtomicDispatch(permit),/MENU_GUARD_REQUIRED/);
  assert.equal(f.getClicks(),0);
  assert(!f.calls.some(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_reserve'));
  await assert.rejects(f.session.originalAtomicDispatch(permit),/NO_ORIGINAL_PERMISSION/);
});

test('GUI ledger reserve precedes the ellipsis and consume follows SaveAll',async()=>{
  const f=fixture();const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await f.dispatch(permit);
  assert.deepEqual(f.calls.filter(c=>Array.isArray(c)&&c[0]==='bridge').map(c=>c[1]),['intent','gui_reserve','gui_consume']);
  assert.deepEqual(f.ledger,[{op:'gui_reserve',data:{kind:'dispatch_inputs',count:2,run_id:'run',owner:'execution'}},
    {op:'gui_consume',data:{reservation_id:'res-dispatch_inputs-1',outcome:'RETURNED'}}]);
  const reserveAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_reserve'),
    ellipsisAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='click'&&c[1][0]===100&&c[1][1]===10),
    saveAllAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='click'&&c[1][0]===100&&c[1][1]===50),
    consumeAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_consume');
  assert(reserveAt<ellipsisAt&&ellipsisAt<saveAllAt&&saveAllAt<consumeAt);
});

test('exhausted GUI ledger refuses the dispatch with zero clicks',async()=>{
  const f=fixture({ledgerExhausted:true});const observation=await f.session.observe();
  const permit=await f.session.originalIntent({receiptToken:'opaque',freshObservation:observation});
  await assert.rejects(f.dispatch(permit),/GUI_LEDGER_RESERVE_REFUSED/);
  assert.equal(f.getClicks(),0);assert(!f.session.trace().some(t=>t.event==='ELLIPSIS_INVOCATION'));
});
