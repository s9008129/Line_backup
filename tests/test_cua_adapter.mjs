import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {deflateSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import {createHostedSession,createAlbumSupportCallbacks,createNavigationObserver,normalizeScreenshotBytes,verifyAlbumScroll,verifyScrollMovement}
  from '../scripts/line_backup_cua_adapter.mjs';
import {runTwoAlbumPilot,runOneScrollProbe} from '../harness-development/line-two-album-pilot-20261014/two_album_entry.mjs';
import {createLiveClassifier} from '../harness-development/line-two-album-pilot-20261014/mac/classifier.mjs';
import {createLiveAnalyzer} from '../harness-development/line-two-album-pilot-20261014/mac/analyzer.mjs';

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

function scrollClassifierFixture({mutateAnalysis=()=>{}}={}){
  const screenshot=png(100,100,12),frameId=digest(screenshot),sessionId='classifier-scroll';
  const axText='offline source AX';const axBytes=Buffer.from(axText);
  const reference=(name,body)=>({path:`harness-development/offline-${name}.json`,bytes:Buffer.byteLength(body),sha256:digest(Buffer.from(body))});
  const artifacts=[];const retain=async({artifact,kind})=>{
    const body=JSON.stringify(artifact);artifacts.push({kind,artifact});return reference(kind,body);
  };
  const nativeRef=reference('native',JSON.stringify({value:{target:{bundleID:'jp.naver.line.mac',pid:42,startTimeSeconds:1,
    startTimeMicroseconds:2},nodes:[{id:'scroll',value:'0',minimumValue:0,maximumValue:1}]}}));
  const sourceBinding={after:{reference:nativeRef,value:{target:{bundleID:'jp.naver.line.mac',pid:42,startTimeSeconds:1,
    startTimeMicroseconds:2},nodes:[{id:'scroll',value:'0',minimumValue:0,maximumValue:1}]}}};
  const analyzeScrollWitness=async args=>{
    const title={text:'2026/01/01～01/02',confidence:.9,candidate_count:1,bounds:[10,30,40,10]};
    const count={text:'4',confidence:.9,candidate_count:1,bounds:[10,44,12,10]};
    const elements=[
      {index:0,role:'list',subrole:'',identifier:'albums',label:'',value:null,bounds_px:[0,0,100,100],parent_index:null,enabled:false},
      {index:1,role:'row',subrole:'',identifier:'album-row',label:'',value:null,bounds_px:[0,20,100,40],parent_index:0,enabled:false},
      {index:2,role:'scroll bar',subrole:'',identifier:'albums-scroll',label:'',value:'0',bounds_px:[95,0,5,100],
        parent_index:0,enabled:false,minimum_value:0,maximum_value:1,native_node_id:'scroll'}];
    const analysis={version:1,frame_id:args.frameId,session_id:args.sessionId,source_sha256:args.frameId,
      source_ax_sha256:args.sourceAXSha256,surface:'ALBUMS',group_key:'group',
      native:{bundle_id:'jp.naver.line.mac',pid:42,window_id:7,display_id:1,cua_capture_bounds_points:[0,0,100,100]},
      layout:{line_version:'1',language:'zh-Hant',window_class:'window',native_scale:1},
      surface_structure:[{role:'list',subrole:'',identifier:'albums'}],surface_bounds_px:[0,0,100,100],
      occlusion:'CLEAR',editable_focus:'NONE',focus_evidence:{version:1,frame_id:args.frameId,session_id:args.sessionId,
        kind:'NONE',focused_index:null},ax:{version:1,focused_index:null,elements},cards:[],
      boundary:{top:true,bottom:false},boundary_evidence:{version:1,frame_id:args.frameId,session_id:args.sessionId,
        source:'AX_SCROLLBAR',indicator_index:2,minimum:0,maximum:1,value:0,raw_value:'0',ax_minimum:0,ax_maximum:1,
        indicator_native_id:'scroll',native_context_ref:nativeRef},detail_identity:null,
      chooser_controls:{root_index:null,path_field_index:null,confirm_button_index:null,selected_leaf_index:null},
      scroll_witness:{viewport_bounds:[0,0,100,100],viewport_ax_index:0,
        native_identity:{display_id:1,cua_capture_bounds_points:[0,0,100,100]},
        process_instance:['jp.naver.line.mac',42,1,2],scroll_offset:{frame_id:args.frameId,session_id:args.sessionId,value:0},
        rows:[{fingerprint:{start_date:'2026-01-01',end_date:'2026-01-02',expected_images:4},
          row_bounds:[0,20,100,40],fully_visible:true,identity_visible:true,
          metadata_bounds:[[10,30,40,10],[10,44,12,10]],row_ax_index:1}]}};
    mutateAnalysis(analysis);return analysis;
  };
  const supportRef=reference('sck-support','offline-support');
  const ocrBody=JSON.stringify({cua_frame_id:frameId,sck_frame_sha256:'a'.repeat(64),cua:[
    {text:'2026/01/01～01/02',confidence:.9,candidate_count:1,bounds:[10,30,40,10]},
    {text:'4',confidence:.9,candidate_count:1,bounds:[10,44,12,10]}],sck:[
    {text:'2026/01/01～01/02',confidence:.9,candidate_count:1,bounds:[300,200,40,10]},
    {text:'4',confidence:.9,candidate_count:1,bounds:[300,220,10,10]}]});
  const ocrRef=reference('sck-ocr',ocrBody);
  const sckFrameRef=reference('sck-frame','offline-sck-frame');
  const manifestRef=reference('sck-manifest','placeholder');
  const manifest={pairFrameId:frameId,surface:'ALBUMS',layoutKey:null,geometryEvidence:null,
    support:{path:supportRef.path,sha256:supportRef.sha256},sckFrameId:'a'.repeat(64),sckFrame:sckFrameRef,ocr:ocrRef};
  const frameSupport=async({layoutKey,geometryRef})=>{
    manifest.layoutKey=layoutKey;manifest.geometryEvidence={path:geometryRef.path,sha256:geometryRef.sha256};
    const body=JSON.stringify(manifest),actualManifestRef={...manifestRef,bytes:Buffer.byteLength(body),sha256:digest(Buffer.from(body))};
    return {provider:'SCREEN_CAPTURE_KIT',surface:'ALBUMS',pairFrameId:frameId,sessionId,
      uncertaintyPx:2,safeMarginPx:6,reference:supportRef,manifestReference:actualManifestRef,
      readRef:async ref=>new Uint8Array(Buffer.from(ref.path===actualManifestRef.path?body:ocrBody))};
  };
  const classifier=createLiveClassifier({retain,frameSupport,analyzeCapture:async()=>{throw new Error('normal classifier not selected');},
    analyzeScrollWitness,groupKey:'group'});
  return {classifier,artifacts,screenshot,frameId,sessionId,axText,axBytes,sourceBinding};
}

function syntheticPartialRowSource({rowParent='list',rowY=-32,rowWidth=327,rowHeight=366,titleY=115,countY=140,
  includeRowInList=true,extraList=false,sourceHashMismatch=false}={}){
  const width=654,height=1286,sessionId='synthetic-partial-row',screenshot=png(width,height,17),frameId=digest(screenshot);
  const capturedAt='2026-10-16T00:00:00.000Z';
  const target={bundleID:'jp.naver.line.mac',pid:42,startTimeSeconds:1,startTimeMicroseconds:2,appVersion:'synthetic'};
  const mkValue=observedAtUnixMilliseconds=>({schemaVersion:1,complete:true,truncated:false,target,
    observedAtUnixMilliseconds,focusedWindowID:7,windows:[{windowNumber:7,cgWindowNumber:7,cgOwnerPID:42,
      nodeID:'window',framePt:{x:0,y:0,width:327,height:643},cgFramePt:{x:0,y:0,width:327,height:643},
      displayIDs:[1],role:'AXWindow',subrole:'AXStandardWindow'}],
    displays:[{displayID:1,backingScale:2,boundsPt:{x:0,y:0,width:327,height:643}}],
    onScreenWindows:[{windowNumber:7,ownerPID:42,alpha:1,isOnScreen:true,boundsPt:{x:0,y:0,width:327,height:643}}],
    nodes:[
      {id:'window',parentID:null,role:'AXWindow',subrole:'AXStandardWindow',framePt:{x:0,y:0,width:327,height:643},
        offscreen:false,focused:false,children:['group','albums','list','scroll',...(extraList?['list2']:[])]},
      {id:'group',parentID:'window',role:'AXStaticText',title:'Synthetic group',framePt:{x:10,y:20,width:120,height:20},
        offscreen:false,focused:false,children:[]},
      {id:'albums',parentID:'window',role:'AXButton',title:'相簿',framePt:{x:10,y:80,width:50,height:15},
        offscreen:false,focused:false,children:[]},
      {id:'list',parentID:'window',role:'AXList',framePt:{x:0,y:103,width:327,height:540},
        offscreen:false,focused:false,children:includeRowInList?['row']:[]},
      {id:'row',parentID:rowParent,role:'AXRow',framePt:{x:0,y:rowY,width:rowWidth,height:rowHeight},
        offscreen:false,focused:false,children:[]},
      {id:'scroll',parentID:'window',role:'AXScrollBar',value:'0',minimumValue:0,maximumValue:1,
        framePt:{x:313,y:103,width:14,height:540},
        offscreen:false,focused:false,children:[]},
      ...(extraList?[{id:'list2',parentID:'window',role:'AXList',framePt:{x:0,y:103,width:327,height:540},
        offscreen:false,focused:false,children:[]}]:[])
    ],visual:{sourceSHA256:sourceHashMismatch?'f'.repeat(64):frameId,width,height,ocr:[
      {text:'Synthetic group',confidence:.9,candidateCount:1,bounds:{x:20,y:40,width:120,height:20}},
      {text:'相簿',confidence:.4,candidateCount:1,bounds:{x:20,y:160,width:40,height:20}},
      {text:'記事本',confidence:.4,candidateCount:1,bounds:{x:120,y:160,width:50,height:20}},
      {text:'2026/01/01～01/02',confidence:.9,candidateCount:1,bounds:{x:20,y:titleY*2,width:240,height:24}},
      {text:'4',confidence:.9,candidateCount:1,bounds:{x:20,y:countY*2,width:20,height:24}}
    ]}});
  const after=mkValue(Date.parse(capturedAt)+1000),before=mkValue(Date.parse(capturedAt)-1000);
  const nativeRef={path:'harness-development/synthetic-native.json',bytes:1,sha256:'b'.repeat(64)};
  const sourceBinding={before:{value:before},after:{value:after,reference:nativeRef}};
  const analyzer=createLiveAnalyzer({runProcess:async()=>{throw new Error('native process forbidden in unit test');},
    binary:'synthetic',repoRoot:'/synthetic',retain:async()=>({path:'harness-development/synthetic.json',bytes:1,sha256:'b'.repeat(64)}),
    groupKey:'synthetic-group',groupTitle:'Synthetic group',authorization:'synthetic',grantSha256:'c'.repeat(64),owner:'synthetic'});
  return {analyzer,sourceBinding,frameId,sessionId,capturedAt,width,height,after,screenshot,
    state:'synthetic AX snapshot',visualOCR:after.visual.ocr.map(o=>({text:o.text,confidence:o.confidence,
      candidate_count:o.candidateCount,bounds:[o.bounds.x,o.bounds.y,o.bounds.width,o.bounds.height]}))};
}

function translateSyntheticRowAndVisibleOCR(source,points=135){
  const after=source.sourceBinding.after.value,list=after.nodes.find(node=>node.role==='AXList');
  const nodes=new Map(after.nodes.map(node=>[node.id,node]));
  const visit=id=>{const node=nodes.get(id);if(!node)return;node.framePt.y-=points;
    for(const child of node.children??[])visit(child);};
  for(const id of list.children)if(nodes.get(id)?.role==='AXRow')visit(id);
  for(const item of after.visual.ocr)if(item.bounds.y>=206)item.bounds.y-=points*2;
  source.visualOCR=after.visual.ocr.map(o=>({text:o.text,confidence:o.confidence,candidate_count:o.candidateCount,
    bounds:[o.bounds.x,o.bounds.y,o.bounds.width,o.bounds.height]}));
  return source;
}

function syntheticAnalyzerClassifier(source,{mutateAnalysis=()=>{}}={}){
  const artifacts=[];
  const ref=(name,body)=>({path:`harness-development/synthetic-${name}.json`,bytes:Buffer.byteLength(body),sha256:digest(Buffer.from(body))});
  const retain=async({artifact,kind})=>{const body=JSON.stringify(artifact);artifacts.push({kind,artifact});return ref(kind,body);};
  const ocrBody=JSON.stringify({cua_frame_id:source.frameId,sck_frame_sha256:'e'.repeat(64),cua:source.visualOCR,
    sck:source.visualOCR.map(item=>({...item,bounds:[400,300,Math.max(1,item.bounds[2]),Math.max(1,item.bounds[3])]}))});
  const ocrRef=ref('sck-ocr',ocrBody),supportRef=ref('sck-support','synthetic support');
  let manifestBody='',manifestRef;
  const frameSupport=async({frameId,sessionId,surface,layoutKey,geometryRef,width,height})=>{
    const manifest={pairFrameId:frameId,surface,layoutKey,geometryEvidence:{path:geometryRef.path,sha256:geometryRef.sha256},
      support:{path:supportRef.path,sha256:supportRef.sha256},sckFrameId:'e'.repeat(64),
      sckFrame:ref('sck-frame','synthetic pixels'),ocr:ocrRef};
    manifestBody=JSON.stringify(manifest);manifestRef=ref('manifest',manifestBody);
    return {provider:'SCREEN_CAPTURE_KIT',surface,pairFrameId:frameId,sessionId,uncertaintyPx:2,safeMarginPx:6,
      reference:supportRef,manifestReference:manifestRef,
      readRef:async target=>new Uint8Array(Buffer.from(target.path===manifestRef.path?manifestBody:ocrBody))};
  };
  const analyzeScrollWitness=async args=>{const analysis=await source.analyzer.analyzeScrollWitness(args);
    mutateAnalysis(analysis);return analysis;};
  const classifier=createLiveClassifier({retain,frameSupport,analyzeCapture:source.analyzer.analyzeCapture,
    analyzeScrollWitness,groupKey:'synthetic-group'});
  return {classifier,artifacts,retain};
}

test('actual analyzer accepts only the exact focused album-list viewport for scroll evidence',async()=>{
  const focusedList=syntheticPartialRowSource({rowY:103,titleY:428,countY:446});
  focusedList.sourceBinding.after.value.nodes.find(node=>node.id==='list').focused=true;
  const focusedArgs={frameId:focusedList.frameId,sessionId:focusedList.sessionId,capturedAt:focusedList.capturedAt,
    width:focusedList.width,height:focusedList.height,sourceAXSha256:digest(Buffer.from(focusedList.state)),
    sourceBinding:focusedList.sourceBinding};
  const focusedAnalysis=await focusedList.analyzer.analyzeScrollWitness(focusedArgs);
  const listIndex=focusedAnalysis.scroll_witness.viewport_ax_index;
  assert.equal(focusedAnalysis.ax.focused_index,listIndex);
  assert.equal(focusedAnalysis.focus_evidence.focused_index,listIndex);
  assert.equal(focusedAnalysis.editable_focus,'NONE');
  const focusedHarness=syntheticAnalyzerClassifier(focusedList),focusedSaved={path:'harness-development/synthetic-focused-frame.png',
    bytes:focusedList.screenshot.byteLength,sha256:focusedList.frameId,ax:{path:'harness-development/synthetic-focused-ax.txt',
      bytes:Buffer.byteLength(focusedList.state),sha256:digest(Buffer.from(focusedList.state))}};
  const focusedClassified=await focusedHarness.classifier.classifyScrollWitness({capture:{screenshot:focusedList.screenshot,
    state:focusedList.state},saved:focusedSaved,frameId:focusedList.frameId,sessionId:focusedList.sessionId,
    capturedAt:focusedList.capturedAt,sourceBinding:focusedList.sourceBinding});
  assert.ok(focusedClassified);
  const retainedFocus=focusedHarness.artifacts.find(item=>item.kind==='focus-evidence').artifact;
  assert.equal(retainedFocus.focused_index,listIndex);
  assert.equal(retainedFocus.kind,'NONE');

  for(const [mutate,code] of [
    [source=>{source.sourceBinding.after.value.nodes.find(node=>node.id==='list').focused=false;
      source.sourceBinding.after.value.nodes.find(node=>node.id==='window').children.push('other');
      source.sourceBinding.after.value.nodes.push({id:'other',parentID:'window',role:'AXButton',focused:true,
        framePt:{x:1,y:1,width:10,height:10},offscreen:false,children:[]});},/SCROLL_FOCUS_NOT_CLEAR/],
    [source=>{source.sourceBinding.after.value.nodes.find(node=>node.id==='list').focused=true;
      source.sourceBinding.after.value.nodes.find(node=>node.id==='window').children.push('other');
      source.sourceBinding.after.value.nodes.push({id:'other',parentID:'window',role:'AXButton',focused:true,
        framePt:{x:1,y:1,width:10,height:10},offscreen:false,children:[]});},/SCROLL_FOCUS_NOT_CLEAR/],
    [source=>{source.sourceBinding.after.value.nodes.find(node=>node.id==='list').focused=true;
      source.sourceBinding.after.value.nodes.find(node=>node.id==='window').children.push('list2');
      source.sourceBinding.after.value.nodes.push({id:'list2',parentID:'window',role:'AXList',focused:false,
        framePt:{x:0,y:103,width:327,height:540},offscreen:false,children:[]});},/ALBUM_SURFACE_NOT_GROUNDED|SCROLL_VIEWPORT_AMBIGUOUS/],
    [source=>{source.sourceBinding.after.value.nodes=source.sourceBinding.after.value.nodes.filter(node=>node.id!=='list');},
      /AX_NODE_MISSING/]
  ]) {
    const bad=syntheticPartialRowSource({rowY:103,titleY:428,countY:446});mutate(bad);
    await assert.rejects(()=>bad.analyzer.analyzeScrollWitness({frameId:bad.frameId,sessionId:bad.sessionId,
      capturedAt:bad.capturedAt,width:bad.width,height:bad.height,sourceAXSha256:digest(Buffer.from(bad.state)),
      sourceBinding:bad.sourceBinding}),code);
  }
});

test('actual analyzer and shared classifier preserve partial AXRow only for scroll evidence',async()=>{
  const focused=syntheticPartialRowSource();
  focused.after.nodes.find(node=>node.id==='window').children.push('edit');
  focused.after.nodes.push({id:'edit',parentID:'window',role:'AXTextField',subrole:'AXTextField',focused:true,
    enabled:true,framePt:{x:10,y:20,width:80,height:20},offscreen:false,children:[]});
  await assert.rejects(()=>focused.analyzer.analyzeScrollWitness({frameId:focused.frameId,sessionId:focused.sessionId,
    capturedAt:focused.capturedAt,width:focused.width,height:focused.height,
    sourceAXSha256:digest(Buffer.from(focused.state)),sourceBinding:focused.sourceBinding}),/EDITABLE_FOCUS_CONFLICT/);

  const source=syntheticPartialRowSource({rowY:103,titleY:428,countY:446});
  const args={frameId:source.frameId,sessionId:source.sessionId,capturedAt:source.capturedAt,width:source.width,
    height:source.height,sourceAXSha256:digest(Buffer.from(source.state)),sourceBinding:source.sourceBinding};
  const baseline=await source.analyzer.analyzeScrollWitness(args);
  assert.equal(baseline.scroll_witness.rows.length,1);
  assert.equal(baseline.scroll_witness.rows[0].fully_visible,true);
  const rowOnly=syntheticPartialRowSource({rowY:103,titleY:428,countY:446});
  rowOnly.sourceBinding.after.value.nodes.find(node=>node.role==='AXRow').framePt.y-=135;
  await assert.rejects(()=>rowOnly.analyzer.analyzeScrollWitness({frameId:rowOnly.frameId,
    sessionId:rowOnly.sessionId,capturedAt:rowOnly.capturedAt,width:rowOnly.width,height:rowOnly.height,
    sourceAXSha256:digest(Buffer.from(rowOnly.state)),sourceBinding:rowOnly.sourceBinding}),/ALBUM_SURFACE_NOT_GROUNDED/);
  translateSyntheticRowAndVisibleOCR(source);
  const analysis=await source.analyzer.analyzeScrollWitness(args);
  assert.equal(analysis.scroll_witness.rows.length,1);
  assert.equal(analysis.scroll_witness.rows[0].fully_visible,false);
  assert.deepEqual(analysis.scroll_witness.rows[0].row_bounds,[0,-64,654,732]);
  assert.deepEqual(analysis.scroll_witness.rows[0].metadata_bounds,[[20,586,240,24],[20,622,20,24]]);

  const harness=syntheticAnalyzerClassifier(source),saved={path:'harness-development/synthetic-frame.png',
    bytes:source.screenshot.byteLength,sha256:source.frameId,ax:{path:'harness-development/synthetic-ax.txt',
      bytes:Buffer.byteLength(source.state),sha256:digest(Buffer.from(source.state))}};
  const classified=await harness.classifier.classifyScrollWitness({capture:{screenshot:source.screenshot,state:source.state},
    saved,frameId:source.frameId,sessionId:source.sessionId,capturedAt:source.capturedAt,sourceBinding:source.sourceBinding});
  assert.equal(classified.scroll_witness.rows.length,1);
  assert.equal(classified.scroll_witness.rows[0].fully_visible,false);
  assert.equal(classified.cards.length,0);

  const mismatch=syntheticAnalyzerClassifier(source,{mutateAnalysis:analysis=>{
    analysis.scroll_witness.rows[0].row_bounds[0]+=1;
  }});
  await assert.rejects(()=>mismatch.classifier.classifyScrollWitness({capture:{screenshot:source.screenshot,state:source.state},
    saved,frameId:source.frameId,sessionId:source.sessionId,capturedAt:source.capturedAt,sourceBinding:source.sourceBinding}),
  /SCROLL_ROW_AX_BINDING/);

  await assert.rejects(()=>harness.classifier.classify({capture:{screenshot:source.screenshot,state:source.state},
    saved,frameId:source.frameId,sessionId:source.sessionId,capturedAt:source.capturedAt,
    sourceBinding:source.sourceBinding}),/ALBUM_SURFACE_NOT_GROUNDED/);
  await assert.rejects(()=>source.analyzer.analyzeCapture({...args,sourceBinding:source.sourceBinding}),
    /ALBUM_SURFACE_NOT_GROUNDED/);

  for(const [options,code] of [
    [{rowY:-400},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{rowY:-270},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{rowParent:'window'},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{includeRowInList:false},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{extraList:true},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{rowWidth:0},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{rowHeight:0},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{titleY:5},/ALBUM_SURFACE_NOT_GROUNDED/],
    [{countY:650},/ALBUM_SURFACE_NOT_GROUNDED/]
  ]) {
    const bad=syntheticPartialRowSource(options);
    await assert.rejects(()=>bad.analyzer.analyzeScrollWitness({frameId:bad.frameId,sessionId:bad.sessionId,
      capturedAt:bad.capturedAt,width:bad.width,height:bad.height,sourceAXSha256:digest(Buffer.from(bad.state)),
      sourceBinding:bad.sourceBinding}),code);
  }
  const wrongSource=syntheticPartialRowSource({sourceHashMismatch:true});
  await assert.rejects(()=>wrongSource.analyzer.analyzeScrollWitness({frameId:wrongSource.frameId,
    sessionId:wrongSource.sessionId,capturedAt:wrongSource.capturedAt,width:wrongSource.width,height:wrongSource.height,
    sourceAXSha256:digest(Buffer.from(wrongSource.state)),sourceBinding:wrongSource.sourceBinding}),
  /NATIVE_VISUAL_SOURCE_MISMATCH/);
  const completeRowNoImage=syntheticPartialRowSource({rowY:103});
  await assert.rejects(()=>completeRowNoImage.analyzer.analyzeCapture({frameId:completeRowNoImage.frameId,
    sessionId:completeRowNoImage.sessionId,capturedAt:completeRowNoImage.capturedAt,width:completeRowNoImage.width,
    height:completeRowNoImage.height,sourceAXSha256:digest(Buffer.from(completeRowNoImage.state)),
    sourceBinding:completeRowNoImage.sourceBinding}),/FULL_CARD_WITNESS_MISSING/);
});

function fixture(options={}) {
  const calls=[],ledger=[];let now=0,clicks=0,intents=0,captures=0,surface=options.initialSurface??'ALBUM_DETAIL',downloadStarted=false,reservationSeq=0,lastListFrameId=null;
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
    classify:async o=>{calls.push('classify');options.onClassify?.(o,surface);
      if(surface==='ALBUMS')lastListFrameId=o.frameId;
      const cards=surface==='ALBUM_DETAIL'?options.detailCards??[]:options.listCards??[];
      const detail_identity=surface==='ALBUM_DETAIL'&&cards.length===1?{kind:'ALBUM_DETAIL_GRID',fingerprint:cards[0].fingerprint,
        list_frame_id:lastListFrameId,list_window_id:1,detail_window_id:options.relatedWindow?2:1,pid:7}:null;
      return {frame_id:o.frameId,session_id:o.sessionId,surface,download_started:downloadStarted,
      group_key:'fixture-group',pid:7,window_id:surface==='ALBUM_DETAIL'&&options.relatedWindow?2:1,
      cards,detail_identity,
      window_lineage:surface==='ALBUM_DETAIL'?options.windowLineage?.(o):null,layout_key:'fixture-layout',captured_at:o.capturedAt};},
    bridge:async (operation,payload)=>{
      calls.push(['bridge',operation]);
      if(operation==='gui_observe'){calls.push(['observation-checkpoint',payload.data.checkpoint]);return {status:'PROJECT_OBSERVATION_RESERVED'};}
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

test('project observation retry keeps the same explicit logical checkpoint',async()=>{
  const f=fixture({requireV3:true});
  await f.session.observe('PAIR-A-LIST_GROUNDING');
  await f.session.observe('PAIR-A-LIST_GROUNDING');
  await f.session.observe('PAIR-A-PREPARED_LIST');
  const checkpoints=f.calls.filter(entry=>Array.isArray(entry)&&entry[0]==='observation-checkpoint')
    .map(entry=>entry[1]);
  assert.deepEqual(checkpoints,['PAIR-A-LIST_GROUNDING','PAIR-A-LIST_GROUNDING','PAIR-A-PREPARED_LIST']);
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

test('one-scroll movement proof requires retained pixel change, stable source identity, AX displacement and offset',async()=>{
  const rawBefore='before scroll AX',rawAfter='after scroll AX';
  const beforeBytes=png(100,100,10),afterBytes=png(100,100,20);
  const beforeId=digest(beforeBytes),afterId=digest(afterBytes);
  const make=(bytes,frameId,rawAx,capturedAt,y,offset)=>({surface:'ALBUMS',session_id:'s',group_key:'g',
    provider:'HOSTED_CUA',pid:9,process_instance:JSON.stringify(['jp.naver.line.mac',9,1,2]),window_id:3,
    layout_key:'l',width:100,height:100,native_scale:2,frame_id:frameId,captured_at:capturedAt,
    viewport_bounds:[0,0,100,100],native_identity:{display_id:1,cua_capture_bounds_points:[10,20,100,100]},
    mapping:{uncertainty:2},scroll_witness:{actionable:false,evidence_only:true,
      native_identity:{display_id:1,cua_capture_bounds_points:[10,20,100,100]},rows:[{fingerprint:{start_date:'2026-01-01',
        end_date:'2026-01-02',expected_images:4},identity_visible:true,row_bounds:[0,y,80,40],
        metadata_bounds:[[2,y+2,20,10],[2,y+15,10,10]]}]},
    parsed_ax:{raw_sha256:digest(Buffer.from(rawAx)),scroll_offset:{frame_id:frameId,session_id:'s',value:offset}}});
  const before=make(beforeBytes,beforeId,rawBefore,'2026-10-16T00:00:00.000Z',30,0);
  const after=make(afterBytes,afterId,rawAfter,'2026-10-16T00:00:01.000Z',10,0.2);
  const saved=(id,raw)=>({sha256:id,ax:{sha256:digest(Buffer.from(raw))}});
  const proof={before:{frameId:beforeId,saved:saved(beforeId,rawBefore),screenshot:beforeBytes,axRaw:rawBefore},
    after:{frameId:afterId,saved:saved(afterId,rawAfter),screenshot:afterBytes,axRaw:rawAfter}};
  const result=await verifyScrollMovement(before,after,proof);
  assert.equal(result.kind,'SCROLL_MOVEMENT_ONLY');assert.equal(result.actionable,false);
  assert.equal(result.changed_viewport_pixels,9999);assert.deepEqual(result.displacement_px,[-20]);
  assert.deepEqual(result.scroll_offset,[0,0.2]);
  const unanchored={...after,scroll_witness:{...after.scroll_witness,rows:after.scroll_witness.rows.map(row=>({...row,
    metadata_bounds:before.scroll_witness.rows[0].metadata_bounds.map(bounds=>[...bounds])}))}};
  await assert.rejects(()=>verifyScrollMovement(before,unanchored,proof),/SCROLL_OCR_MOVEMENT_INCONSISTENT/);
  for(const [mutateBefore,mutateAfter,code] of [
    [null,o=>{o.scroll_witness.native_identity.display_id=2;},/SCROLL_DISPLAY_ORIGIN_DRIFT/],
    [o=>{o.process_instance='["jp.naver.line.mac",9,null,null]';},
      o=>{o.process_instance='["jp.naver.line.mac",9,null,null]';},/SCROLL_PROCESS_IDENTITY/],
    [null,o=>{o.captured_at=before.captured_at;},/SCROLL_CAPTURE_TIME_ORDER/],
    [null,o=>{o.window_id=4;},/SCROLL_CONTEXT_DRIFT/],
    [null,o=>{o.process_instance=JSON.stringify(['jp.naver.line.mac',10,1,2]);},/SCROLL_CONTEXT_DRIFT/]]) {
    const prior={...before,scroll_witness:{...before.scroll_witness,
      native_identity:{...before.scroll_witness.native_identity}}};
    const changed={...after,scroll_witness:{...after.scroll_witness,
      native_identity:{...after.scroll_witness.native_identity}}};
    mutateBefore?.(prior);mutateAfter(changed);
    await assert.rejects(()=>verifyScrollMovement(prior,changed,proof),code);
  }
});

test('one-scroll probe rejects undecodable retained JPEG before ledger reservation or native input',async()=>{
  const calls=[];let scrolls=0,clicks=0;
  const bytes=new Uint8Array([255,216,255,0]);
  const observer=createNavigationObserver({app:{
    async getAXStateAndScreenshot(){return {state:'retained AX',screenshot:bytes};},
    async getAXState(){return 'retained AX';},async click(){clicks++;},async pressKey(){},async scroll(){scrolls++;}},
    bridge:async(operation)=>{calls.push(operation);if(operation==='gui_observe')return {status:'PROJECT_OBSERVATION_RESERVED'};
      throw new Error('Unexpected authorization operation: '+operation);},
    retain:async({screenshot,ax})=>({path:'harness-development/offline-frame',bytes:screenshot.byteLength,
      sha256:digest(screenshot),ax:{path:'harness-development/offline-ax',bytes:Buffer.byteLength(ax),sha256:digest(Buffer.from(ax))}}),
    classify:async({frameId,sessionId})=>({frame_id:frameId,session_id:sessionId,surface:'ALBUMS',
      viewport_bounds:[0,0,100,100],mapping:{uncertainty:2},
      scroll_witness:{evidence_only:true,actionable:false,rows:[{identity_visible:true}]}}),
    requireV3:true,resolveWindowLineage:async()=>null,checkpointPrefix:'A_DISCOVERY',sessionId:'offline',clock:()=>1,
    decodeRetainedImage:async()=>{throw new Error('SCROLL_JPEG_DECODE_INVALID');}});
  try {
    const before=await observer.observe('ONE_SCROLL_BEFORE');
    await assert.rejects(()=>observer.boundedScroll(before,[50,50],'down',0.25,'SCROLL_1',{mode:'ONE_SCROLL_PROBE'}),
      /SCROLL_JPEG_DECODE_INVALID/);
    assert.deepEqual(calls,['gui_observe']);assert.equal(scrolls,0);assert.equal(clicks,0);
    assert.equal(observer.movementEvidence().length,0);
  } finally {observer.close();}
});

test('one-scroll probe rejects a point outside the mapped safe viewport before decoder, reservation, or input',async()=>{
  const calls=[];let scrolls=0,decodes=0;
  const bytes=png(100,100,12);
  const observer=createNavigationObserver({app:{
    async getAXStateAndScreenshot(){return {state:'retained AX',screenshot:bytes};},
    async getAXState(){return 'retained AX';},async click(){},async pressKey(){},async scroll(){scrolls++;}},
    bridge:async(operation)=>{calls.push(operation);if(operation==='gui_observe')return {status:'PROJECT_OBSERVATION_RESERVED'};
      throw new Error('Unexpected authorization operation: '+operation);},
    retain:async({screenshot,ax})=>({path:'harness-development/offline-frame',bytes:screenshot.byteLength,
      sha256:digest(screenshot),ax:{path:'harness-development/offline-ax',bytes:Buffer.byteLength(ax),sha256:digest(Buffer.from(ax))}}),
    classify:async({frameId,sessionId})=>({frame_id:frameId,session_id:sessionId,surface:'ALBUMS',
      viewport_bounds:[0,0,100,100],mapping:{uncertainty:2},
      scroll_witness:{evidence_only:true,actionable:false,rows:[{identity_visible:true}]}}),
    requireV3:true,resolveWindowLineage:async()=>null,checkpointPrefix:'A_DISCOVERY',sessionId:'offline',clock:()=>1,
    decodeRetainedImage:async({bytes,sourceSha256})=>{decodes++;return {sourceSha256,png:bytes,pngSha256:sourceSha256};}});
  try {
    const before=await observer.observe('PAIR-A-DISCOVERY_SCROLL_1_BEFORE');
    await assert.rejects(()=>observer.boundedScroll(before,[1,1],'down',0.25,'SCROLL_1',{mode:'ONE_SCROLL_PROBE'}),
      /ONE_SCROLL_TARGET_OUTSIDE_SAFE_VIEWPORT/);
    assert.deepEqual(calls,['gui_observe']);assert.equal(decodes,0);assert.equal(scrolls,0);
  } finally {observer.close();}
});

test('shared live classifier returns a source-bound list viewport witness with native geometry',async()=>{
  const f=scrollClassifierFixture();
  const saved={path:'harness-development/offline-frame',bytes:f.screenshot.byteLength,sha256:f.frameId,
    ax:{path:'harness-development/offline-ax',bytes:f.axBytes.byteLength,sha256:digest(f.axBytes)}};
  const observation=await f.classifier.classifyScrollWitness({capture:{screenshot:f.screenshot,state:f.axText},saved,
    frameId:f.frameId,sessionId:f.sessionId,capturedAt:'2026-10-16T00:00:00.000Z',sourceBinding:f.sourceBinding});
  assert.equal(observation.surface,'ALBUMS');assert.equal(observation.cards.length,0);
  assert.equal(observation.scroll_witness.actionable,false);assert.equal(observation.scroll_witness.rows.length,1);
  const geometry=f.artifacts.find(item=>item.kind==='frame-geometry')?.artifact;
  assert.deepEqual(Object.keys(geometry).sort(),['ax_state','captured_at','cua_capture_bounds_points','frame_id','layout_key',
    'layout_signature','pid','session_id','structure_sha256','surface','surface_bounds_px','version','window_id'].sort());
  assert.deepEqual(Object.keys(geometry.layout_signature).sort(),['frame_width_px','frame_height_px','language',
    'line_version','native_scale','structure_sha256','window_class'].sort());
  assert.ok(f.artifacts.some(item=>item.kind==='grounding-evidence'));
});

test('shared live classifier rejects wrong group, duplicate row identity, and ungrounded viewport',async()=>{
  for(const [mutate,code] of [
    [analysis=>{analysis.group_key='other';},/CLASSIFIER_CONTEXT/],
    [analysis=>{analysis.scroll_witness.rows.push({...analysis.scroll_witness.rows[0]});},/SCROLL_ROW_DUPLICATE/],
    [analysis=>{analysis.scroll_witness.viewport_bounds=[5,0,95,100];},/SCROLL_VIEWPORT_AX_BINDING/],
    [analysis=>{analysis.native.pid=43;},/SCROLL_WITNESS_PROCESS_BINDING/]]) {
    const f=scrollClassifierFixture({mutateAnalysis:mutate});
    const saved={path:'harness-development/offline-frame',bytes:f.screenshot.byteLength,sha256:f.frameId,
      ax:{path:'harness-development/offline-ax',bytes:f.axBytes.byteLength,sha256:digest(f.axBytes)}};
    await assert.rejects(()=>f.classifier.classifyScrollWitness({capture:{screenshot:f.screenshot,state:f.axText},saved,
      frameId:f.frameId,sessionId:f.sessionId,capturedAt:'2026-10-16T00:00:00.000Z',sourceBinding:f.sourceBinding}),code);
  }
});

function oneScrollRuntimeFixture({denyReservation=false,mappingUncertainty=2,targetPoint=[50,50],ledgerStatus='INITIALIZED'}={}){
  const calls=[],reservations=[];let scrolls=0,captures=0,currentLedgerStatus=ledgerStatus;
  const app={async getAXStateAndScreenshot(){captures++;return {state:`AX ${captures}`,
    screenshot:png(100,100,captures===1?10:20,captures)};},async getAXState(){return 'AX'},
    async click(){calls.push('click');},async pressKey(){calls.push('pressKey');},async scroll(target,direction,distance){
      calls.push(['scroll',target,direction,distance]);scrolls++;}};
  const cli=async(operation,request={})=>{
    calls.push([operation,request.payload?.data?.checkpoint??null]);
    if(operation==='inspect'&&!request.payload?.data?.include_gui_ledger_status)
      return {receipt_token:'offline-token'};
    if(operation==='inspect')return {gui_ledger_status:{status:currentLedgerStatus,task_id:'offline-owner',owner:'offline-owner',
      source_sha256:'a'.repeat(64),workflow_phase:'A',failure_latched:false,scroll_1_used:false,reserved_entry_count:0}};
    if(operation==='gui_observe')return {status:'PROJECT_OBSERVATION_RESERVED'};
    if(operation==='gui_initialize'){currentLedgerStatus='INITIALIZED';return {status:'PROJECT_LEDGER_INITIALIZED'};}
    throw new Error(`Unexpected direct CLI operation: ${operation}`);
  };
  cli.bridge=async(operation,{data}={})=>{
    calls.push([operation,data]);
    if(operation==='gui_reserve'){
      if(denyReservation)throw new Error('GUI_LEDGER_RESERVE_REFUSED');
      reservations.push(data);return {reservation:{id:'offline-scroll-reservation',kind:data.kind,count:data.count}};
    }
    if(operation==='gui_consume')return {reservation:{id:data.reservation_id,state:'CONSUMED'}};
    throw new Error(`Unexpected bridge operation: ${operation}`);
  };
  const runtime={profile:'LINE_TWO_ALBUM_PILOT/1',owner:'offline-owner',authorization:'private/project-grant.json',cli,
    assertLineAlreadyRunning:async()=>{calls.push('line-preflight');},getApp:async()=>{calls.push('get-app');return app;},
    retain:async({screenshot,ax})=>({path:'harness-development/offline-frame',bytes:screenshot.byteLength,
      sha256:digest(screenshot),ax:{path:'harness-development/offline-ax',bytes:Buffer.byteLength(ax),sha256:digest(Buffer.from(ax))}}),
    classifyScrollWitness:async({capture,saved,frameId,sessionId,capturedAt})=>{
      const moved=scrolls>0,y=moved?10:30,offset=moved?.2:0;
      return {frame:saved,frame_id:frameId,session_id:sessionId,group_key:'group',surface:'ALBUMS',captured_at:capturedAt,
        provider:'HOSTED_CUA',layout_key:'layout',window_id:7,pid:42,process_instance:JSON.stringify(['jp.naver.line.mac',42,1,2]),
        width:100,height:100,native_scale:1,viewport_bounds:[0,0,100,100],mapping:{uncertainty:mappingUncertainty},cards:[],
        boundary:{top:offset===0,bottom:false},editable_focus:'NONE',occlusion:'CLEAR',
        scroll_witness:{evidence_only:true,actionable:false,native_identity:{display_id:1,cua_capture_bounds_points:[0,0,100,100]},
          rows:[{fingerprint:{start_date:'2026-01-01',end_date:'2026-01-02',expected_images:4},identity_visible:true,
            fully_visible:true,row_bounds:[0,y,90,50],metadata_bounds:[[10,y+5,30,10],[10,y+20,10,10]]}]},
        parsed_ax:{scroll_offset:{frame_id:frameId,session_id:sessionId,value:offset}}};},
    decodeRetainedImage:async()=>{throw new Error('PNG should decode locally');},navigation:{scrollTarget:async()=>targetPoint},
    beforeCapture:async()=>null,afterCapture:async()=>null,windowLineage:async()=>null,clock:()=>10,
    privateEvidence:{retainDiscovery:async value=>{calls.push(['retainDiscovery',value]);return {path:'retained'};}}};
  return {runtime,calls,reservations,get scrolls(){return scrolls;}};
}

test('one-scroll entry executes only one reserved SCROLL_1 input and records movement-only evidence',async()=>{
  const f=oneScrollRuntimeFixture();
  const result=await runOneScrollProbe(f.runtime);
  assert.equal(result.status,'SCROLL_MOVEMENT_ONLY');assert.equal(result.actionable,false);
  assert.equal(f.scrolls,1);assert.equal(f.reservations.length,1);
  assert.deepEqual(f.reservations[0].slots,['SCROLL_1']);assert.equal(f.reservations[0].kind,'scroll');
  assert.equal(f.calls.filter(item=>item==='click'||item==='pressKey').length,0);
  assert.equal(f.calls.some(item=>Array.isArray(item)&&item[0]==='gui_initialize'),false);
  assert.equal(f.calls.filter(item=>Array.isArray(item)&&item[0]==='retainDiscovery').length,1);
  assert.equal(f.calls.some(item=>Array.isArray(item)&&['dispatch','album_begin','album_admit','intent','finalize'].includes(item[0])),false);
});

test('one-scroll entry initializes only an authenticated absent ledger',async()=>{
  const f=oneScrollRuntimeFixture({ledgerStatus:'NOT_INITIALIZED'});
  const result=await runOneScrollProbe(f.runtime);
  assert.equal(result.status,'SCROLL_MOVEMENT_ONLY');
  assert.equal(f.calls.filter(item=>Array.isArray(item)&&item[0]==='gui_initialize').length,1);
  assert.equal(f.calls.filter(item=>Array.isArray(item)&&item[0]==='inspect'
    &&item[1]===null).length>=3,true);
});

test('one-scroll entry rejects incompatible initialized ledger before app acquisition',async()=>{
  for(const status of ['CLOSED_NO_REPLAY','SCROLL_USED','OTHER_RESERVED','FAILURE_LATCHED','WRONG_PHASE']){
    const f=oneScrollRuntimeFixture();
    const original=f.runtime.cli;
    f.runtime.cli=async(operation,request={})=>{
      if(operation==='inspect'&&request.payload?.data?.include_gui_ledger_status){
        const response=await original(operation,request),ledger=response.gui_ledger_status;
        if(status==='CLOSED_NO_REPLAY')ledger.status='CLOSED_NO_REPLAY';
        if(status==='SCROLL_USED')ledger.scroll_1_used=true;
        if(status==='OTHER_RESERVED')ledger.reserved_entry_count=1;
        if(status==='FAILURE_LATCHED')ledger.failure_latched=true;
        if(status==='WRONG_PHASE')ledger.workflow_phase='B';
        return response;
      }
      return original(operation,request);
    };
    f.runtime.cli.bridge=original.bridge;
    await assert.rejects(()=>runOneScrollProbe(f.runtime),/ONE_SCROLL_LEDGER_(AUTHORITY_MISMATCH|NOT_CONTINUABLE)/);
    assert.equal(f.calls.some(item=>item==='line-preflight'),false);
    assert.equal(f.calls.some(item=>Array.isArray(item)&&item[0]==='gui_initialize'),false);
    assert.equal(f.calls.some(item=>Array.isArray(item)&&item[0]==='gui_observe'),false);
    assert.equal(f.calls.includes('get-app'),false);
    assert.equal(f.scrolls,0);
  }
});

test('one-scroll entry stops on missing durable reservation with zero native input',async()=>{
  const f=oneScrollRuntimeFixture({denyReservation:true});
  await assert.rejects(()=>runOneScrollProbe(f.runtime),/GUI_LEDGER_RESERVE_REFUSED/);
  assert.equal(f.scrolls,0);assert.equal(f.reservations.length,0);
  assert.equal(f.calls.filter(item=>item==='click'||item==='pressKey').length,0);
});

test('one-scroll entry rejects source mapping above the existing two-pixel limit before reservation',async()=>{
  const f=oneScrollRuntimeFixture({mappingUncertainty:2.01});
  await assert.rejects(()=>runOneScrollProbe(f.runtime),/ONE_SCROLL_VIEWPORT_GEOMETRY/);
  assert.equal(f.scrolls,0);assert.equal(f.reservations.length,0);
});

test('project album open accepts recorded related detail-window lineage',async()=>{
  const fp={start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2};
  let listFrameId=null;
  const f=fixture({initialSurface:'ALBUMS',requireV3:true,relatedWindow:true,
    detailCards:[{fingerprint:fp}],
    onClassify:(value,currentSurface)=>{if(currentSurface==='ALBUMS')listFrameId=value.frameId;},
    windowLineage:()=>({from_window_id:1,to_window_id:2,relationship:'ALBUM_CARD_OPEN_DETAIL',list_frame_id:listFrameId})});
  const list=await f.session.observe('PAIR-A-LIST_GROUNDING');listFrameId=list.frame_id;
  const detail=await f.session.openAlbum({run_id:'run-a',fingerprint:fp,frame_id:list.frame_id,click:[20,30],project_album_slot:'A'});
  assert.equal(detail.surface,'ALBUM_DETAIL');assert.equal(detail.window_id,2);
  assert.equal(detail.detail_identity.list_frame_id,list.frame_id);
});

test('wrong fresh detail identity stops after the reserved card click before calibration',async()=>{
  const f=fixture({initialSurface:'ALBUMS',requireV3:true,
    detailCards:[{fingerprint:{start_date:'2024-02-01',end_date:'2024-02-01',expected_images:3}}]});
  const list=await f.session.observe('PAIR-A-LIST_GROUNDING');
  await assert.rejects(f.session.openAlbum({run_id:'run-a',fingerprint:{start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2},
    frame_id:list.frame_id,click:[20,30],project_album_slot:'A'}),/PROJECT_DETAIL_IDENTITY_MISMATCH/);
  assert.equal(f.ledger.filter(entry=>entry.op==='gui_reserve').length,1);
  assert.equal(f.ledger.find(entry=>entry.op==='gui_reserve').data.kind,'album_open');
  assert.equal(f.calls.filter(entry=>Array.isArray(entry)&&entry[0]==='click').length,1);
});

test('slow menu locator burns calibration slots without clicking a stale detail frame',async()=>{
  const fp={start_date:'2024-01-01',end_date:'2024-01-01',expected_images:2};
  const f=fixture({initialSurface:'ALBUMS',requireV3:true,detailCards:[{fingerprint:fp}]});
  const list=await f.session.observe('PAIR-A-LIST_GROUNDING');
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
  let appSurface='ALBUMS',selected=targets[0],lifecycle=0,scrollCount=0,captureNo=0,downloadStarted=false,lastListFrameId=null;
  const retainedArtifacts=[],scrollSlots=[],inspectionCandidates=[],observationCheckpoints=[];
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
    if(appSurface==='ALBUMS')lastListFrameId=frameId;
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
    if(appSurface==='ALBUM_DETAIL')base.detail_identity={kind:'ALBUM_DETAIL_GRID',fingerprint:selected,
      list_frame_id:lastListFrameId,list_window_id:1,detail_window_id:1,pid:7};
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
    if(operation==='gui_observe'){if(data.kind==='paired')observationCheckpoints.push(data.checkpoint);
      return {status:'PROJECT_OBSERVATION_RESERVED'};}
    return {receipt_token:token(),status:'MOCKED'};
  };
  cli.bridge=async(operation,request={})=>{
    calls.push(operation);
    if(operation==='gui_observe')observationCheckpoints.push(request.data.checkpoint);
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
  assert.ok(observationCheckpoints.includes('PAIR-A-LIST_GROUNDING'));
  assert.ok(observationCheckpoints.includes('PAIR-A-PRE_INTENT_DETAIL'));
  assert.ok(observationCheckpoints.includes('PAIR-C1-RETURN_LIST'));
  assert.ok(observationCheckpoints.includes('PAIR-B-CHOOSER_CONFIRM_ATTEMPTED'));
  assert.ok(observationCheckpoints.every(checkpoint=>checkpoint.startsWith('PAIR-')));
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
