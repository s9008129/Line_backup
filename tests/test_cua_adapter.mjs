import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {deflateSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import {createHostedSession,createAlbumSupportCallbacks,createNavigationObserver,normalizeScreenshotBytes,verifyAlbumScroll}
  from '../scripts/line_backup_cua_adapter.mjs';
import {runTwoAlbumPilot} from '../harness-development/line-two-album-pilot-20261014/two_album_entry.mjs';

const digest=value=>createHash('sha256').update(value).digest('hex');
function png(width,height,shade,nonce=0){
  const crc32=buffer=>{let c=0xffffffff;for(const byte of buffer){c^=byte;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;};
  const chunk=(type,data)=>{const name=Buffer.from(type),length=Buffer.alloc(4),crc=Buffer.alloc(4);length.writeUInt32BE(data.length);
    crc.writeUInt32BE(crc32(Buffer.concat([name,data])));return Buffer.concat([length,name,data,crc]);};
  const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(width,0);ihdr.writeUInt32BE(height,4);ihdr[8]=8;ihdr[9]=2;
  const rows=[];for(let y=0;y<height;y++){const row=Buffer.alloc(1+width*3);for(let x=0;x<width;x++){
    row[1+x*3]=y===0&&x===0?nonce:shade;row[2+x*3]=y;row[3+x*3]=x;}rows.push(row);}
  return new Uint8Array(Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ihdr),
    chunk('IDAT',deflateSync(Buffer.concat(rows))),chunk('IEND',Buffer.alloc(0))]));
}

function scrollObservation(bytes,cards,rawAx,offset){
  const frame_id=digest(bytes),axHash=digest(Buffer.from(rawAx));
  return {surface:'ALBUMS',session_id:'scroll-session',group_key:'group',provider:'HOSTED_CUA',pid:9,window_id:3,
    layout_key:'layout',width:100,height:100,native_scale:2,frame_id,viewport_bounds:[0,0,100,100],viewport_visual_delta:1,
    mapping:{uncertainty:2},cards:cards.map(([fp,y])=>({fingerprint:fp,fully_visible:true,card_bounds:[0,y,80,20]})),
    parsed_ax:{raw_sha256:axHash,scroll_offset:offset,cards:cards.map(([fp,y])=>({start_date:fp.start_date,
      end_date:fp.end_date,expected_images:fp.expected_images,bounds:[0,y,80,20]}))},
    proof:{frame_id,axHash,rawAx,bytes}};
}

function retainedProof(observation){
  const saved={sha256:observation.frame_id,ax:{sha256:observation.proof.axHash}};
  return {frameId:observation.frame_id,saved,screenshot:observation.proof.bytes,axRaw:observation.proof.rawAx};
}

function fixture(options={}) {
  const calls=[],ledger=[];let now=0,clicks=0,intents=0,captures=0,surface=options.initialSurface??'ALBUM_DETAIL',downloadStarted=false,reservationSeq=0;
  const app={
    async getAXStateAndScreenshot(){calls.push('capture');captures++;return {state:'fixture AX',
      screenshot:options.screenshot??new Uint8Array([1,2,3,captures])};},
    async getAXState(){calls.push('ax');return 'fixture AX';},
    async click(p){calls.push(['click',p]);clicks++;if(clicks===options.throwAt)throw new Error('external click error');
      if(clicks===1)surface='ALBUM_DETAIL';else if(clicks===2)surface='FOLDER_CHOOSER';else downloadStarted=true;},
    async pressKey(k){calls.push(['key',k]);},async setValue(i,s){calls.push(['setValue',i,s]);},async scroll(){calls.push('scroll');}
  };
  const session=createHostedSession({app,sessionId:'execution',requireV3:options.requireV3??false,clock:()=>now,wait:async ms=>{calls.push(['timer',ms]);now+=options.timerDuration??ms;},
    resolveWindowLineage:async ({after})=>after.window_lineage,
    retain:async o=>{calls.push('retain');const ref={path:`harness-development/${o.kind??'frame'}-${o.frameId.slice(0,12)}.json`,
      bytes:o.screenshot?o.screenshot.byteLength:160,sha256:o.frameId};
      if(o.screenshot){const ax=Buffer.from(o.ax);ref.ax={path:`harness-development/ax-${o.frameId.slice(0,12)}.txt`,
        bytes:ax.byteLength,sha256:createHash('sha256').update(ax).digest('hex')};}
      return ref;},
    classify:async o=>{calls.push('classify');options.onClassify?.(o,surface);return {frame_id:o.frameId,session_id:o.sessionId,surface,download_started:downloadStarted,
      group_key:'fixture-group',pid:7,window_id:surface==='ALBUM_DETAIL'&&options.relatedWindow?2:1,
      cards:surface==='ALBUM_DETAIL'?options.detailCards??[]:options.listCards??[],
      window_lineage:surface==='ALBUM_DETAIL'?options.windowLineage?.(o):null,layout_key:'fixture-layout',captured_at:o.capturedAt};},
    bridge:async (operation,payload)=>{
      calls.push(['bridge',operation]);
      if(operation==='gui_observe')return {status:'PROJECT_OBSERVATION_RESERVED'};
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
  const f=fixture({initialSurface:'ALBUMS'});const observation=await f.session.observe();
  await assert.rejects(f.session.boundedScroll(observation,[100,100],'down',0.251),/SCROLL_POLICY/);
  assert(!f.calls.includes('scroll'));
  await assert.rejects(f.session.boundedScroll(observation,[100,100],'down',0.25),/SCROLL_CONTEXT_DRIFT/);
  assert.equal(f.calls.filter(c=>c==='scroll').length,1);
  const reservations=f.ledger.filter(e=>e.op==='gui_reserve').map(e=>e.data.kind);
  assert.deepEqual(reservations,['scroll']);
  const scrollAt=f.calls.indexOf('scroll'),consumeAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_consume');
  const reserveAt=f.calls.findIndex(c=>Array.isArray(c)&&c[0]==='bridge'&&c[1]==='gui_reserve');
  assert(reserveAt<scrollAt&&scrollAt<consumeAt);
});

test('scroll proof compares retained viewport pixels, raw AX cards, movement and adjacent overlap',()=>{
  const a={start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2};
  const b={start_date:'2024-02-01',end_date:'2024-02-01',expected_images:3};
  const c={start_date:'2024-03-01',end_date:'2024-03-01',expected_images:4};
  const beforeAx='raw AX before',afterAx='raw AX after';
  const before=scrollObservation(png(100,100,10),[[a,10],[b,50]],beforeAx,0);
  const after=scrollObservation(png(100,100,20),[[b,25],[c,70]],afterAx,15);
  const changed=verifyAlbumScroll(before,after,{before:retainedProof(before),after:retainedProof(after)});
  assert.equal(changed.overlap_count,1);assert.equal(changed.new_full_card_count,1);
  assert.ok(changed.changed_viewport_pixels>0);assert.deepEqual(changed.ax_offset,[0,15]);
  const reversed=scrollObservation(png(100,100,20),[[b,60],[c,80]],afterAx,15);
  assert.throws(()=>verifyAlbumScroll(before,reversed,{before:retainedProof(before),after:retainedProof(reversed)}),
    /SCROLL_SHARED_CARD_NOT_MOVED_UP/);
});

test('project album open accepts recorded related detail-window lineage',async()=>{
  const fp={start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2};
  let listFrameId=null;
  const f=fixture({initialSurface:'ALBUMS',requireV3:true,relatedWindow:true,
    detailCards:[{fingerprint:fp}],
    onClassify:(value,currentSurface)=>{if(currentSurface==='ALBUMS')listFrameId=value.frameId;},
    windowLineage:()=>({from_window_id:1,to_window_id:2,relationship:'ALBUM_CARD_OPEN_DETAIL',list_frame_id:listFrameId})});
  const list=await f.session.observe();listFrameId=list.frame_id;
  const detail=await f.session.openAlbum({run_id:'run-a',fingerprint:fp,frame_id:list.frame_id,click:[20,30],project_album_slot:'A'});
  assert.equal(detail.surface,'ALBUM_DETAIL');assert.equal(detail.window_id,2);
  assert.equal(detail.window_lineage.list_frame_id,list.frame_id);
});

test('wrong fresh detail identity stops after the reserved card click before calibration',async()=>{
  const f=fixture({initialSurface:'ALBUMS',requireV3:true,
    detailCards:[{fingerprint:{start_date:'2024-02-01',end_date:'2024-02-01',expected_images:3}}]});
  const list=await f.session.observe();
  await assert.rejects(f.session.openAlbum({run_id:'run-a',fingerprint:{start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2},
    frame_id:list.frame_id,click:[20,30],project_album_slot:'A'}),/PROJECT_DETAIL_IDENTITY_MISMATCH/);
  assert.equal(f.ledger.filter(entry=>entry.op==='gui_reserve').length,1);
  assert.equal(f.ledger.find(entry=>entry.op==='gui_reserve').data.kind,'album_open');
  assert.equal(f.calls.filter(entry=>Array.isArray(entry)&&entry[0]==='click').length,1);
});

test('slow menu locator burns calibration slots without clicking a stale detail frame',async()=>{
  const fp={start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2};
  const f=fixture({initialSurface:'ALBUMS',requireV3:true,detailCards:[{fingerprint:fp}]});
  const list=await f.session.observe();
  const detail=await f.session.openAlbum({run_id:'run-a',fingerprint:fp,frame_id:list.frame_id,click:[20,30],project_album_slot:'A'});
  const clicksBefore=f.calls.filter(entry=>Array.isArray(entry)&&entry[0]==='click').length;
  await assert.rejects(f.session.calibrateMenu({detail,runId:'run-a',locateMenu:async observation=>{
    f.advance(5001);return {point:[10,10],frameId:observation.frame_id,role:'button',bounds_px:[5,5,15,15],dot_spacing:5};
  },captureMenuSupport:async()=>{throw new Error('must not capture')},guardMenu:async()=>{throw new Error('must not guard');}}),
  /FRESH_CAPTURE_EXPIRED_AFTER_LOCATOR/);
  assert.equal(f.calls.filter(entry=>Array.isArray(entry)&&entry[0]==='click').length,clicksBefore);
  assert.deepEqual(f.ledger.find(entry=>entry.op==='gui_reserve').data.slots,['A.CARD']);
  assert.deepEqual(f.ledger.filter(entry=>entry.op==='gui_reserve')[1].data.slots,['A.CAL_OPEN','A.CAL_DISMISS']);
});

async function twoAlbumEntryProbe(preDiscoveryBudget){
  const calls=[],targets=Array.from({length:8},(_,index)=>({start_date:`2024-${String(index+1).padStart(2,'0')}-01`,
    end_date:`2024-${String(index+1).padStart(2,'0')}-01`,expected_images:index+2}));
  let appSurface='ALBUMS',selected=targets[0],lifecycle=0,scrollCount=0,captureNo=0,downloadStarted=false;
  const retainedArtifacts=[],scrollSlots=[],inspectionCandidates=[];
  const token=()=>`token-${calls.length}`;
  const ref=(kind,value)=>{const raw=Buffer.from(JSON.stringify(value));return {path:`harness-development/private/${kind}-${calls.length}.json`,
    bytes:raw.length,sha256:digest(raw)};};
  const app={
    async getAXStateAndScreenshot(){captureNo++;return {state:JSON.stringify({captureNo,appSurface}),
      screenshot:png(100,100,scrollCount?25+scrollCount:10,captureNo%255)};},
    async getAXState(){return JSON.stringify({captureNo,appSurface});},
    async click(point){calls.push(`click:${point.join(',')}`);
      if(point[0]===20){appSurface='ALBUM_DETAIL';downloadStarted=false;}
      else if(point[0]===50)appSurface='FOLDER_CHOOSER';
      else if(point[0]===70){appSurface='ALBUM_DETAIL';downloadStarted=true;}
      else if(point[0]===90)appSurface='ALBUMS';},
    async pressKey(){},async setValue(){},async scroll(){calls.push('scroll');scrollCount++;}
  };
  const card=(fp,y)=>({fingerprint:fp,fully_visible:true,card_bounds:[10,y,70,20],
    safe_metadata_bounds:[15,y+4,40,10],metadata_bounds:[15,y+4,40,10],neighbor_bounds:[]});
  const classifierCache=new Map();
  const classify=async ({capture,saved,frameId,sessionId,capturedAt})=>{
    const listCards=scrollCount===0?[card(targets[0],10),card(targets[1],60)]:
      [card(targets[scrollCount],10),card(targets[scrollCount+1],30),card(targets[scrollCount+2],50),card(targets[scrollCount+3],70)];
    const cards=appSurface==='ALBUMS'?listCards:[card(selected,35)];
    const parsedAx={scroll_offset:scrollCount*20,cards:cards.map(c=>({start_date:c.fingerprint.start_date,
      end_date:c.fingerprint.end_date,expected_images:c.fingerprint.expected_images,bounds:c.card_bounds}))};
    const base={frame:saved,frame_id:frameId,session_id:sessionId,group_key:'fixture-group',surface:appSurface,
      captured_at:capturedAt,provider:'HOSTED_CUA',layout_key:'fixture-layout',window_id:1,pid:7,width:100,height:100,
      mapping:{space:'CUA_CAPTURE_PIXELS',uncertainty:2,evidence:ref('grounding',{}),frame_id:frameId,
        layout_key:'fixture-layout',sck_support:ref('support',{})},cards,
      boundary:{top:false,bottom:false,evidence:ref('boundary',{})},editable_focus:'NONE',occlusion:'CLEAR'};
    classifierCache.set(frameId,{observation:base,analysis:{surface_bounds_px:[10,10,80,80],
      layout:{native_scale:2,line_version:'LINE 9',language:'en',window_class:'LINE_MAIN'},
      cards:cards.map((c,i)=>({...c,card_ax_index:i})),boundary_evidence:{value:scrollCount*20}},
      axSnapshot:{elements:cards.map((c,i)=>({index:i,bounds_px:c.card_bounds}))},
      geometryRef:ref('geometry',{}),axRef:ref('ax',{})});
    return base;
  };
  const retain=async value=>{
    if(value.receipt)retainedArtifacts.push({kind:value.kind,receipt:structuredClone(value.receipt)});
    if(value.artifact&&value.kind==='menu-calibration')retainedArtifacts.push({kind:value.kind,artifact:structuredClone(value.artifact)});
    if(value.screenshot){const ax=Buffer.from(value.ax);return {path:`harness-development/private/${value.frameId}.png`,
      bytes:value.screenshot.byteLength,sha256:value.frameId,ax:{path:`harness-development/private/${value.frameId}.ax`,
        bytes:ax.byteLength,sha256:digest(ax)}};}
    return ref(value.kind??'artifact',value.artifact??value.receipt??{});
  };
  const classifyChooser=async ({phase,dispatch,frameId,sessionId,capturedAt})=>({version:1,phase,
    frame:{frame_id:frameId,session_id:sessionId,captured_at:capturedAt,frame:{frame_id:frameId,captured_at:capturedAt}},
    ax_state:{path:'harness-development/private/ax.json'},sck_support:null,dispatch,
    control:{chooser_index:0,chooser_identifier:'chooser'}});
  const cli=async(operation,{payload=null}={})=>{
    const data=payload?.data??{};calls.push(operation);
    if(operation==='inspect'){inspectionCandidates.push(data.candidates??[]);return {receipt_token:token(),eligible_candidates:(data.candidates??[])
      .filter(target=>target.start_date===targets[preDiscoveryBudget===0?3:preDiscoveryBudget+4].start_date)};}
    if(operation==='begin')return {receipt_token:token(),result:{status:'BATCH_OWNED',batch_id:`batch-${++lifecycle}`}};
    if(operation==='admit'){
      if(lifecycle===1&&scrollCount<preDiscoveryBudget)throw Object.assign(new Error('candidate not yet eligible'),{code:'BOUNDED_TARGET_INELIGIBLE'});
      selected=data.target;return {receipt_token:token(),result:{status:'ADMITTED_BOUNDED_CANDIDATE',identity:data.target}};}
    if(operation==='prepare')return {receipt_token:token(),result:{status:'ALBUM_OPEN_READY',run_id:`run-${lifecycle}`,
      fingerprint:selected,click:[20,20],frame_id:data.observation.frame_id,session_id:'mock-owner',project_album_slot:lifecycle===1?'A':'B'}};
    if(operation==='calibrate')return {receipt_token:token(),result:{status:'CALIBRATED'}};
    if(operation==='finalize')return {receipt_token:token(),result:{status:'VERIFIED',run_id:`run-${lifecycle}`}};
    if(operation==='release')return {receipt_token:token(),result:{status:'BATCH_RELEASED'}};
    if(operation==='stop')return {receipt_token:token(),result:{status:'STOPPED'}};
    if(operation==='gui_phase')return {status:'PROJECT_WORKFLOW_PHASE'};
    if(operation==='gui_observe')return {status:'PROJECT_OBSERVATION_RESERVED'};
    return {receipt_token:token(),status:'MOCKED'};
  };
  cli.bridge=async(operation,request={})=>{
    calls.push(operation);
    if(operation==='gui_reserve'){
      if(request.data.kind==='scroll')scrollSlots.push(...request.data.slots);
      return {reservation:{id:`r-${calls.length}`,kind:request.data.kind,count:request.data.count}};}
    if(operation==='gui_consume')return {reservation:{id:request.data.reservation_id,state:'CONSUMED'}};
    if(operation==='intent')return {new_intent:true,receipt_token:token(),result:{status:'ORIGINAL_INTENT_COMMITTED',
      dispatch_authorized:true,fixture:false,frame_id:request.data.fresh.frame_id,session_id:'mock-owner',run_id:`run-${lifecycle}`,
      owner:'mock-owner',action_id:`action-${lifecycle}`,destination:'/fixture/new',ellipsis:[10,10],save_all:[50,40],
      project_album_slot:lifecycle===1?'A':'B',calibration_reference:ref('cal',{}),
      calibration_closure_reference:ref('closure',{}),applicability_reference:ref('applicability',{})}};
    if(operation==='dispatch')return {receipt_token:token(),result:{status:'DOWNLOAD_STARTED'}};
    throw new Error(`unexpected bridge ${operation}`);
  };
  const menuLocator=async(observation,{phase})=>phase==='TRIGGER'
    ?{point:[10,10],frameId:observation.frame_id,role:'button',bounds_px:[5,5,15,15],dot_spacing:5}
    :{save_all:[50,40],frameId:observation.frame_id,layoutKey:observation.layout_key,
      menuBounds:[0,0,100,100],addressableBounds:[0,0,100,100],safeBounds:[0,0,100,100],
      ellipsisBounds:[5,5,15,15],label:'Save All',menu_order:['Save All'],item_spacing:20,saveAllBounds:[40,30,30,20]};
  const chooser={locatePathField:async o=>({index:1,frameId:o.frame.frame_id,role:'text field',subrole:'PathTextField'}),
    validatePath:async()=>true,validateLeaf:async()=>true,
    locateConfirm:async o=>({point:[70,70],frameId:o.frame.frame_id,role:'button',enabled:true}),
    refreshBaseline:async()=>({reference:ref('baseline',{}),artifact:{inventory:[]},identity:{dev:1,ino:1}}),
    observeDownload:async({action,confirmation,confirmationInvokedAt,destinationBaseline})=>({reference:ref('download',{}),
      evidence:{source_kind:'FILESYSTEM_DELTA',before_inventory:[],after_inventory:[{name:'one.jpg'}],run_id:action.run_id,
        action_id:action.action_id,execution_id:action.owner,session_id:'mock-owner',destination:action.destination,
        baseline:destinationBaseline.reference,confirmation_frame_id:confirmation.frame_id,
        confirmation_invoked_at:confirmationInvokedAt,observed_at:new Date().toISOString()}}),
    destinationBaseline:{reference:ref('baseline',{}),artifact:{inventory:[]},identity:{dev:1,ino:1}}};
  const classifier={classify,classifyChooser,cache:classifierCache};
  const runtime={profile:'LINE_TWO_ALBUM_PILOT/1',owner:'mock-owner',authorization:'private/grant.json',cli,
    assertLineAlreadyRunning:async()=>calls.push('preflight-app'),getApp:async()=>app,retain,classifier,
    producer:{captureMenuSupport:async()=>({reference:ref('support',{}),provider:'SCREEN_CAPTURE_KIT',pairFrameId:'x'}),
      guardMenu:async({action,pairFrameId})=>({verdict:'PASS',pairFrameId,actionPoint:action.save_all})},
    menuLocator,chooser,decoder:{path:'/fixture/decoder',sha256:'a'.repeat(64)},wait:async ms=>calls.push(`wait:${ms}`),
    navigation:{locateBack:async o=>({frameId:o.frame_id,role:'button',point:[90,5]}),scrollTarget:async()=>[30,50]},
    beforeCapture:async()=>({pid:7,window_id:1}),afterCapture:async()=>({pid:7,window_id:1}),
    windowLineage:async()=>null,clock:()=>performance.now(),
    privateEvidence:{leaseCloseReference:async runId=>ref('lease-close',{runId}),retainC1:async evidence=>ref('c1',evidence),
      retainFailure:async evidence=>ref('failure',evidence),retainDiscovery:async evidence=>ref('discovery',evidence)}};
  const result=await runTwoAlbumPilot(runtime);
  assert.equal(result.status,'TWO_BOUNDED_ALBUMS_VERIFIED');
  const receipt3=retainedArtifacts.find(item=>item.kind==='cua-dispatch-receipt-3')?.receipt;
  const calibration2=retainedArtifacts.find(item=>item.kind==='menu-calibration')?.artifact;
  assert.equal(calibration2?.version,2);assert.equal(calibration2?.kind,'menu-calibration-no-io-pair');
  assert.equal(Object.hasOwn(calibration2?.detail??{},'viewport_bounds'),false);
  assert.equal(Object.hasOwn(calibration2?.detail??{},'batch_record'),false);
  assert.equal(Object.hasOwn(calibration2?.menu_frame??{},'viewport_bounds'),false);
  assert.equal(calibration2?.trigger?.role,'button');
  assert.deepEqual(calibration2?.trigger?.point,[10,10]);
  assert.deepEqual(calibration2?.trigger?.bounds_px,[5,5,15,15]);
  assert.equal(calibration2?.trigger?.dot_spacing,5);
  assert.equal(receipt3?.version,'cua-dispatch-receipt-3');
  assert.deepEqual(receipt3.events.map(event=>event.event),['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SAVE_ALL_INVOCATION',
    'SAVE_ALL_RETURNED','CHOOSER_APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_INVOCATION',
    'CONFIRM_ATTEMPTED','DOWNLOAD_EVIDENCE_OBSERVED','CEASE_INPUT_AFTER_DOWNLOAD_START']);
  assert.equal(Object.hasOwn(receipt3,'popup_frame_id'),false);assert.equal(Object.hasOwn(receipt3,'support'),false);
  assert.equal(Object.hasOwn(receipt3,'guard'),false);
  assert.ok(receipt3.calibration_reference&&receipt3.calibration_closure_reference&&receipt3.applicability_reference);
  const firstRelease=calls.indexOf('release'),c1Phase=calls.indexOf('gui_phase'),secondBegin=calls.lastIndexOf('begin');
  const scroll=calls.indexOf('scroll',c1Phase+1);
  assert.ok(firstRelease>=0&&c1Phase>firstRelease&&scroll>c1Phase&&secondBegin>scroll);
  assert.equal(calls.filter(call=>call==='begin').length,2);
  assert.ok(calls.includes('admit'));
  assert.equal(selected.start_date,targets[preDiscoveryBudget===0?3:preDiscoveryBudget+4].start_date);
  assert.equal(calls.filter(call=>typeof call==='string'&&call.startsWith('wait:1200')).length,4);
  assert.deepEqual(scrollSlots,targets.slice(0,preDiscoveryBudget+1).map((_,i)=>`SCROLL_${i+1}`));
  if(preDiscoveryBudget===0)assert.equal(inspectionCandidates.at(-1)[0].start_date,targets[2].start_date);
  return result;
}

test('two-album entry orders pre-discovery scroll, A release, C1 scroll, then B transaction',
  async()=>{await twoAlbumEntryProbe(1);});
test('two-album entry uses all three pre-discovery slots and one post-A slot',
  async()=>{await twoAlbumEntryProbe(3);});
test('two-album entry skips the first duplicate C1 candidate before admitting B',
  async()=>{await twoAlbumEntryProbe(0);});

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
