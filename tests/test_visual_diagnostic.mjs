import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createProducerHook} from '../harness-development/line-two-album-pilot-20261014/mac/producer.mjs';
import {createLiveClassifier} from '../harness-development/line-two-album-pilot-20261014/mac/classifier.mjs';
import {createVisualDiagnosticObserver} from '../harness-development/line-two-album-pilot-20261014/mac/visual_diagnostic.mjs';

const root='/project';
const hash=value=>createHash('sha256').update(value).digest('hex');
function png(width=40,height=30){
  const value=Buffer.alloc(24);value.set([137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82],0);
  value.writeUInt32BE(width,16);value.writeUInt32BE(height,20);return new Uint8Array(value);
}
function ref(path,bytes){return {path,bytes:bytes.byteLength,sha256:hash(bytes)};}

function harness({analysisDelayMs=0,mutatePair=value=>value,artifactFault=null}={}){
  const files=new Map(),retained=[];let captureCalls=0,analysisCalls=0;
  const store=(path,bytes)=>{const value=new Uint8Array(bytes);files.set(path,value);return ref(path,value);};
  const io={readFile:async absolute=>{const value=files.get(absolute.slice(root.length+1));assert(value);return value;},
    mkdirp:async()=>{}};
  const retain=async value=>{
    if(value.screenshot){
      const frame=store(`harness-development/line-two-album-pilot-20261014/private/evidence/cua-frames/${value.frameId}.png`,value.screenshot);
      const ax=store(`harness-development/line-two-album-pilot-20261014/private/evidence/cua-ax/${value.frameId}.bin`,new TextEncoder().encode(value.ax));
      return {...frame,ax};
    }
    const raw=new TextEncoder().encode(JSON.stringify(value.artifact));
    retained.push(value.artifact);
    return store(`harness-development/line-two-album-pilot-20261014/private/evidence/${value.kind}/${hash(raw)}.json`,raw);
  };
  const pairFor=argv=>{
    const arg=name=>argv[argv.indexOf(name)+1];
    const framePath=arg('--cua-frame'),frameId=arg('--cua-frame-id');
    const sckBytes=new Uint8Array([1,2,3,4,5,6]);
    const sck=store(`harness-development/line-two-album-pilot-20261014/private/evidence/visual-diagnostic/test/sck.png`,sckBytes);
    if(artifactFault==='corrupt')files.set(sck.path,new Uint8Array([9,8,7]));
    if(artifactFault==='missing')files.delete(sck.path);
    const start=arg('--cua-request-started-at'),end=arg('--cua-request-ended-at');
    const startMono=arg('--cua-request-start-monotonic-ns'),endMono=arg('--cua-request-end-monotonic-ns');
    const sckStart=new Date(Date.parse(end)+100).toISOString(),sckEnd=new Date(Date.parse(start)+3000).toISOString();
    const pair={version:1,kind:'VISUAL_CARD_DIAGNOSTIC',sessionID:arg('--session-id'),cuaFrameID:frameId,
      cuaFrame:{path:framePath,bytes:files.get(framePath)?.byteLength,sha256:frameId},
      cuaRequestStartedAt:start,cuaRequestEndedAt:end,
      cuaRequestStartMonotonicNanoseconds:startMono,cuaRequestEndMonotonicNanoseconds:endMono,
      sckFrameID:sck.sha256,sckFrame:sck,sckRequestStartedAt:sckStart,sckRequestEndedAt:sckEnd,
      sckRequestStartMonotonicNanoseconds:(BigInt(endMono)+100_000_000n).toString(),
      sckRequestEndMonotonicNanoseconds:(BigInt(startMono)+3_000_000_000n).toString(),
      nativeInventoryStartedAt:new Date(Date.parse(end)+10).toISOString(),
      nativeInventoryEndedAt:new Date(Date.parse(end)+20).toISOString(),
      nativeInventoryStartMonotonicNanoseconds:(BigInt(endMono)+10_000_000n).toString(),
      nativeInventoryEndMonotonicNanoseconds:(BigInt(endMono)+20_000_000n).toString(),
      windowScreenAssociationStatus:'PROVISIONAL',
      bundleID:'jp.naver.line.mac',pid:41,processStartTimeSeconds:100,processStartTimeMicroseconds:0,
      windowID:7,displayID:1,widthPixels:2000,heightPixels:1600,nativeScale:2,pointPixelScale:2,
      cuaBoundsPoints:[0,0,1000,800],sckWindowBoundsPoints:[0,0,1000,800],displayBoundsPoints:[0,0,1000,800],
      captureRecord:{}};
    return mutatePair({version:1,kind:'VISUAL_CARD_DIAGNOSTIC',evidenceOnly:true,actionable:false,pair});
  };
  const runProcess=async argv=>{
    const command=argv[1];
    if(command==='visual-diagnostic-capture'){captureCalls++;return {status:0,stdout:JSON.stringify(pairFor(argv)),stderr:''};}
    if(command==='visual-diagnostic-analyze'){
      analysisCalls++;if(analysisDelayMs)await new Promise(resolve=>setTimeout(resolve,analysisDelayMs));
      const pairSHA=argv[argv.indexOf('--capture-receipt-sha256')+1];
      return {status:0,stdout:JSON.stringify({version:1,kind:'VISUAL_CARD_DIAGNOSTIC',evidenceOnly:true,
        actionable:false,capturePairSHA256:pairSHA,status:'INSUFFICIENT',reason:'insufficientUniqueAnchors',
        anchors:[],cuaOCR:[],sckOCR:[]}),stderr:''};
    }
    throw new Error(`unexpected command ${command}`);
  };
  const producer=createProducerHook({io,runProcess,repoRoot:root,authorization:'grant.json',authority:{grantSha256:'a'.repeat(64)},
    binary:{absolutePath:'/rev28ctl'},geometryProvider:async()=>{throw Error('production frame-support must not run');},retain});
  return {producer,retain,files,retained,get captureCalls(){return captureCalls;},get analysisCalls(){return analysisCalls;}};
}

function nativeContext(){
  const window={windowNumber:7,nodeID:'window',framePt:{x:0,y:0,width:1000,height:800},displayIDs:[1]};
  return {schemaVersion:1,complete:true,truncated:false,target:{bundleID:'jp.naver.line.mac',pid:41,
    startTimeSeconds:100,startTimeMicroseconds:0},focusedWindowID:7,windows:[window],
    displays:[{displayID:1,boundsPt:{x:0,y:0,width:1000,height:800}}]};
}

test('capture-first path retains the original CUA interval, then SCK, Native AFTER and offline completion',async()=>{
  const h=harness({analysisDelayMs:5100}),events=[],frame=png(),ax='hosted AX text',frameId=hash(frame);
  let before,originalRequestStart,flow={};
  const classifier=createLiveClassifier({retain:h.retain,frameSupport:async()=>{throw Error('normal frame support called');},
    analyzeCapture:async()=>{throw Error('normal classifier called');},analyzeVisualCardDiagnostic:async args=>{
      const value=nativeContext();
      return {kind:'VISUAL_CARD_DIAGNOSTIC',evidence_only:true,actionable:false,version:1,frame_id:args.frameId,
        session_id:args.sessionId,source_sha256:args.frameId,source_ax_sha256:args.sourceAXSha256,surface:'ALBUMS',
        group_key:'group',native:{bundle_id:'jp.naver.line.mac',pid:41,window_id:7,display_id:1,
          cua_capture_bounds_points:[0,0,1000,800]},layout:{line_version:'1',language:'zh-Hant',window_class:'window',native_scale:2},
        surface_structure:[],surface_bounds_px:[0,0,40,30],occlusion:'CLEAR',ax:{version:1,elements:[]},raw_ocr:[],
        reference:await h.retain({artifact:value,kind:'native-analysis',frameId:args.frameId,sessionId:args.sessionId})};
    },groupKey:'group'});
  const observer=createVisualDiagnosticObserver({app:{getAXStateAndScreenshot:async()=>{
      events.push('cua');return {state:ax,screenshot:frame};}},retain:h.retain,sessionId:'session',
    beforeCapture:async()=>{events.push('before');before=nativeContext();return {value:before,
      reference:await h.retain({artifact:before,kind:'native-before'})};},
    capturePair:async args=>{events.push('sck');originalRequestStart=args.requestStartedAtUtc;flow={...flow,...args,beforeBinding:args.before};
      flow.pairEvidence=await h.producer.captureVisualDiagnostic(args);return flow.pairEvidence;},
    afterCapture:async()=>{events.push('after');flow.after=nativeContext();return {value:flow.after,
      reference:await h.retain({artifact:flow.after,kind:'native-after'})};},
    analyze:args=>classifier.completeVisualCardDiagnostic({...args,analyzePixels:h.producer.analyzeVisualDiagnostic})});
  const output=await observer.observe();
  assert.deepEqual(events,['before','cua','sck','after']);
  assert.equal(h.captureCalls,1);assert.equal(h.analysisCalls,1);
  assert.equal(output.CAPTURE_STATUS,'CAPTURED');assert.equal(output.ANALYSIS_STATUS,'INSUFFICIENT');
  assert.equal(output.ACQUISITION_RELATIONSHIP,'INSUFFICIENT');assert.equal(output.ACTION_ELIGIBILITY,'INELIGIBLE');
  assert.equal(output.actionable,false);assert.equal(classifier.cache.size,0);
  const completed=h.retained.find(item=>item.kind==='VISUAL_CARD_DIAGNOSTIC'&&item.cua_request_started_at);
  assert.equal(completed.evidence_only,true);assert.equal(completed.actionable,false);
  assert.equal(completed.cua_request_started_at,originalRequestStart);
  assert.ok(Date.parse(completed.processing_completed_at)-Date.parse(completed.cua_request_started_at)>5000);
  assert.ok(BigInt(completed.processing_duration_nanoseconds)>0n);
  assert.ok(completed.capture_pair_receipt.sha256);
  assert.equal(completed.geometry_time_semantics,
    'SCK capture record is capture-time provenance; Native AFTER AX is later context and is only a consistency check.');

  const analysis=h.retained.find(item=>item.kind==='VISUAL_CARD_DIAGNOSTIC'&&item.cua_request_started_at===undefined);
  assert.ok(analysis);
  const driftCases=[
    ['PID',v=>{v.target.pid+=1;}],
    ['process start',v=>{v.target.startTimeSeconds+=1;}],
    ['focused window',v=>{v.focusedWindowID+=1;}],
    ['window geometry',v=>{v.windows[0].framePt.x+=5;}],
    ['display geometry',v=>{v.displays[0].boundsPt.width+=5;}],
  ];
  for(const [label,mutate] of driftCases){
    const after=nativeContext();mutate(after);
    await assert.rejects(()=>classifier.completeVisualCardDiagnostic({capture:flow.capture,saved:flow.saved,
      frameId,sessionId:'session',capturedAt:flow.requestStartedAtUtc,
      sourceBinding:{before:flow.beforeBinding,after:{value:after,
        reference:{path:'harness-development/native-after.json',bytes:1,sha256:'b'.repeat(64)}}},
      pairEvidence:flow.pairEvidence,requestStartMonotonicNanoseconds:flow.requestStartMonotonicNanoseconds,
      analyzePixels:h.producer.analyzeVisualDiagnostic}),/VISUAL_DIAGNOSTIC_(PROCESS_INSTANCE|NATIVE_GEOMETRY)_DRIFT/,
    `must reject ${label} drift`);
  }
  const crossPair={...flow.pairEvidence,pair:{...flow.pairEvidence.pair,sessionID:'other-session'}};
  await assert.rejects(()=>classifier.completeVisualCardDiagnostic({capture:flow.capture,saved:flow.saved,frameId,
    sessionId:'session',capturedAt:flow.requestStartedAtUtc,sourceBinding:{before:flow.beforeBinding,
      after:{value:flow.after,reference:{path:'harness-development/native-after.json',
      bytes:1,sha256:'b'.repeat(64)} }},pairEvidence:crossPair,requestStartMonotonicNanoseconds:flow.requestStartMonotonicNanoseconds,
    analyzePixels:h.producer.analyzeVisualDiagnostic}),/VISUAL_DIAGNOSTIC_PAIR_REQUIRED/);
  const swappedReceipt=await h.retain({artifact:{...flow.pairEvidence,actionable:false,
    pair:{...flow.pairEvidence.pair,sessionID:'other-session'}},kind:'swapped-capture-receipt'});
  await assert.rejects(()=>h.producer.analyzeVisualDiagnostic({pairEvidence:{...flow.pairEvidence,reference:swappedReceipt},
    frameId,sessionId:'session'}),/VISUAL_DIAGNOSTIC_RECEIPT_PAIR_MISMATCH/);
  const sckRef=flow.pairEvidence.pair.sckFrame;
  const originalSck=h.files.get(sckRef.path);
  h.files.set(sckRef.path,new Uint8Array([9,8,7]));
  await assert.rejects(()=>h.producer.readRef(sckRef),/SCK_ARTIFACT_DRIFT/);
  h.files.set(sckRef.path,originalSck);h.files.delete(sckRef.path);
  await assert.rejects(()=>h.producer.readRef(sckRef));
});

test('producer refuses a mismatched native-context process schema before SCK dispatch',async()=>{
  const h=harness(),bytes=png(),frameId=hash(bytes),state='AX',axBytes=new TextEncoder().encode(state);
  const frame=ref('harness-development/line-two-album-pilot-20261014/private/evidence/cua-frames/frame.png',bytes);
  const saved={...frame,ax:ref('harness-development/line-two-album-pilot-20261014/private/evidence/cua-ax/frame.bin',axBytes)};
  h.files.set(frame.path,bytes);h.files.set(saved.ax.path,axBytes);
  await assert.rejects(h.producer.captureVisualDiagnostic({capture:{screenshot:bytes,state},saved,frameId,
    sessionId:'session',requestStartedAtUtc:new Date().toISOString(),requestEndedAtUtc:new Date().toISOString(),
    requestStartMonotonicNanoseconds:'100',requestEndMonotonicNanoseconds:'200',
    before:{value:{target:{bundleID:'jp.naver.line.mac',pid:41,startTimeSeconds:100,startTimeMicroseconds:0},
      complete:true,truncated:false,focusedWindowID:7,windows:[]}}}),/VISUAL_DIAGNOSTIC_WINDOW_IDENTITY/);
  assert.equal(h.captureCalls,0);
});

test('observer rejects non-byte screenshot input and never starts the SCK capture',async()=>{
  let sck=0;
  const observer=createVisualDiagnosticObserver({app:{getAXStateAndScreenshot:async()=>({state:'x',screenshot:[1,2,3]})},
    retain:async()=>{throw Error('must not retain invalid capture');},beforeCapture:async()=>({}),
    capturePair:async()=>{sck++;},afterCapture:async()=>({}),analyze:async()=>({}),sessionId:'session'});
  await assert.rejects(observer.observe());assert.equal(sck,0);
});

test('post-capture failure retains the original pair receipt and Native BEFORE reference',async()=>{
  const h=harness(),beforeRef={path:'harness-development/native-before.json',bytes:1,sha256:'a'.repeat(64)};
  const observer=createVisualDiagnosticObserver({app:{getAXStateAndScreenshot:async()=>({state:'AX',screenshot:png()})},
    retain:h.retain,sessionId:'session',beforeCapture:async()=>({value:nativeContext(),reference:beforeRef}),
    capturePair:async args=>h.producer.captureVisualDiagnostic(args),
    afterCapture:async()=>{throw Object.assign(Error('synthetic later-phase failure'),{code:'TEST_AFTER'});},
    analyze:async()=>{throw Error('analysis must not run');}});
  await assert.rejects(observer.observe(),/synthetic later-phase failure/);
  const failure=h.retained.find(item=>item.kind==='VISUAL_CARD_DIAGNOSTIC_FAILURE');
  assert.ok(failure.capture_pair_receipt?.sha256);assert.equal(failure.native_before,beforeRef);
  assert.equal(failure.capture_status,'CAPTURED');assert.equal(failure.analysis_status,'NOT_RUN');
});
