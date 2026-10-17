import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {deflateSync} from 'node:zlib';
import {createLiveAnalyzer} from '../harness-development/line-two-album-pilot-20261014/mac/analyzer.mjs';
import {createLiveClassifier} from '../harness-development/line-two-album-pilot-20261014/mac/classifier.mjs';

const target={start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56};
const canonical='Canonical group';
const alias='Owner-confirmed display alias';
const ref=(name,hash)=>({path:`harness-development/test/${name}.json`,bytes:1,sha256:hash.repeat(64)});
function native({frameId,at,kind='list',ocr=null,focused=3766,includeList=true,group=canonical,scrollValue='225',min=0,max=300}={}){
  const start={bundleID:'jp.naver.line.mac',pid:25266,startTimeSeconds:100,startTimeMicroseconds:5,appVersion:'test'};
  const win=(number,nodeID)=>({windowNumber:number,cgWindowNumber:number,cgOwnerPID:25266,nodeID,
    framePt:{x:358,y:46,width:327,height:643},cgFramePt:{x:358,y:46,width:327,height:643},displayIDs:[1],
    role:'AXWindow',subrole:'AXStandardWindow'});
  const nodes=[];
  if(kind==='list'){
    nodes.push({id:'list-window',parentID:null,role:'AXWindow',framePt:{x:358,y:46,width:327,height:643},offscreen:false,
      children:['group','tab','list','scroll']});
    nodes.push({id:'group',parentID:'list-window',role:'AXStaticText',title:group,framePt:{x:365,y:90,width:150,height:20},offscreen:false,children:[]});
    nodes.push({id:'tab',parentID:'list-window',role:'AXButton',title:'相簿',framePt:{x:365,y:120,width:40,height:18},offscreen:false,enabled:true,children:[]});
    nodes.push({id:'list',parentID:'list-window',role:'AXList',framePt:{x:358,y:149,width:327,height:540},offscreen:false,children:['row']});
    nodes.push({id:'row',parentID:'list',role:'AXRow',framePt:{x:358,y:149,width:327,height:540},offscreen:false,children:[]});
    nodes.push({id:'scroll',parentID:'list-window',role:'AXScrollBar',value:scrollValue,minimumValue:min,maximumValue:max,
      framePt:{x:672,y:149,width:13,height:540},offscreen:false,children:[]});
  } else {
    nodes.push({id:'detail-window',parentID:null,role:'AXWindow',framePt:{x:358,y:46,width:327,height:643},offscreen:false,children:['detail-scroll']});
    nodes.push({id:'detail-scroll',parentID:'detail-window',role:'AXScrollBar',value:'225',minimumValue:null,maximumValue:null,
      framePt:{x:672,y:149,width:13,height:540},offscreen:false,children:[]});
  }
  const windows=kind==='list'?[win(3766,'list-window')]:[
    ...(includeList?[win(3766,'list-window')]:[]),win(5798,'detail-window')];
  const current=windows.find(w=>w.windowNumber===focused)??windows.at(-1);
  const visualItems=ocr??(kind==='list'?[
    {text:group,confidence:.9,candidateCount:1,bounds:{x:14,y:88,width:200,height:24}},
    {text:'相簿',confidence:.9,candidateCount:1,bounds:{x:18,y:145,width:60,height:20}},
    {text:'2024/05/27~05/31',confidence:.95,candidateCount:1,bounds:{x:31,y:1136,width:258,height:30}},
    {text:'56',confidence:.95,candidateCount:1,bounds:{x:31,y:1174,width:50,height:24}}
  ]:[
    {text:'2024/05/27~05/31',confidence:.95,candidateCount:1,bounds:{x:30,y:120,width:280,height:32}},
    {text:'56張照片',confidence:.95,candidateCount:1,bounds:{x:30,y:165,width:140,height:30}}
  ]);
  const value={schemaVersion:1,complete:true,truncated:false,target:start,observedAtUnixMilliseconds:at,
    focusedWindowID:focused,windows,onScreenWindows:[...windows].sort((a,b)=>(a.windowNumber===focused?-1:0)
      -(b.windowNumber===focused?-1:0)).map((w,i)=>({windowNumber:w.windowNumber,ownerPID:25266,
      alpha:1,isOnScreen:true,boundsPt:{x:w.framePt.x,y:w.framePt.y,width:w.framePt.width,height:w.framePt.height},
      orderFrontToBack:i})),displays:[{displayID:1,backingScale:2,boundsPt:{x:0,y:0,width:1000,height:1000}}],nodes,
    visual:{sourceSHA256:frameId,width:654,height:1286,ocr:visualItems,ellipsisComponents:[]}};
  return value;
}
function analyzer({groupTitleAliases=[]}={}){
  return createLiveAnalyzer({runProcess:async()=>{throw new Error('not used');},binary:'native',repoRoot:'/project',
    retain:async({artifact,kind,frameId})=>({path:`harness-development/test/${kind}-${frameId.slice(0,8)}.json`,
      bytes:JSON.stringify(artifact).length,sha256:'a'.repeat(64)}),groupKey:'stable-group',groupTitle:canonical,
    groupTitleAliases,authorization:'bundle/project-grant.json',grantSha256:'b'.repeat(64),owner:'owner'});
}
function tinyPNG(){
  const crc32=b=>{let c=0xffffffff;for(const x of b){c^=x;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;};
  const chunk=(type,data)=>{const name=Buffer.from(type),len=Buffer.alloc(4),crc=Buffer.alloc(4);len.writeUInt32BE(data.length);
    crc.writeUInt32BE(crc32(Buffer.concat([name,data])));return Buffer.concat([len,name,data,crc]);};
  const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(10,0);ihdr.writeUInt32BE(10,4);ihdr[8]=8;ihdr[9]=2;
  const rows=Buffer.concat(Array.from({length:10},()=>Buffer.from([0,...Array(30).fill(100)])));
  return new Uint8Array(Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ihdr),
    chunk('IDAT',deflateSync(rows)),chunk('IEND',Buffer.alloc(0))]));
}
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function capture(analyzerInstance,{frameId,kind='list',at=10000,beforeValue=null,afterValue=null,includeList=true,ocr=null,
  group=canonical,scrollValue='225',min=0,max=300,scrollWitness=false}={}){
  const sessionId='session';const before=beforeValue??native({frameId,at:at-10,kind,includeList,ocr,group,scrollValue,min,max});
  const after=afterValue??native({frameId,at:at+10,kind,includeList,ocr,group,scrollValue,min,max});
  const nativeRef=ref('native-context','c');
  const args={frameId,sessionId,capturedAt:new Date(at).toISOString(),width:654,height:1286,
    sourceAXSha256:'d'.repeat(64),sourceBinding:{before:{value:before},after:{value:after,reference:nativeRef}}};
  return scrollWitness?analyzerInstance.analyzeScrollWitness(args):analyzerInstance.analyzeCapture(args);
}

test('real-shape detail grid is recognized only through same-process list-to-new-window lineage and literal count',async()=>{
  const a=analyzer();
  const list=await capture(a,{frameId:'1'.repeat(64),kind:'list'});
  assert.equal(list.surface,'ALBUMS');
  assert.equal(list.cards.length,1);
  assert.deepEqual(list.cards[0].fingerprint,target);
  const before=native({frameId:'2'.repeat(64),kind:'detail',at:19990,focused:5798});
  const after=native({frameId:'2'.repeat(64),kind:'detail',at:20010,focused:5798});
  const detail=await capture(a,{frameId:'2'.repeat(64),kind:'detail',at:20000,beforeValue:before,afterValue:after});
  assert.equal(detail.surface,'ALBUM_DETAIL');
  assert.deepEqual(detail.cards,[]);
  assert.equal(detail.detail_identity.kind,'ALBUM_DETAIL_GRID');
  assert.deepEqual(detail.detail_identity.fingerprint,target);
  assert.equal(detail.detail_identity.list_frame_id,list.frame_id);
  assert.equal(detail.detail_identity.list_window_id,3766);
  assert.equal(detail.detail_identity.detail_window_id,5798);
  assert.equal(detail.detail_identity.pid,25266);
  assert.equal(detail.detail_identity.photo_count.text,'56張照片');
});

test('analyzer refuses photo viewer, wrong or ambiguous title/count, foreign window, and missing list lineage',async()=>{
  const badCases=[
    {name:'viewer counter',ocr:[{text:'2024/05/27~05/31(1/56)',confidence:.95,candidateCount:1,bounds:{x:10,y:20,width:300,height:30}},
      {text:'photo 1',confidence:.95,candidateCount:1,bounds:{x:10,y:60,width:100,height:20}}]},
    {name:'wrong count',ocr:[{text:'2024/05/27~05/31',confidence:.95,candidateCount:1,bounds:{x:30,y:120,width:280,height:32}},
      {text:'65張照片',confidence:.95,candidateCount:1,bounds:{x:30,y:165,width:140,height:30}}]},
    {name:'ambiguous count',ocr:[{text:'2024/05/27~05/31',confidence:.95,candidateCount:1,bounds:{x:30,y:120,width:280,height:32}},
      {text:'56張照片',confidence:.95,candidateCount:1,bounds:{x:30,y:165,width:140,height:30}},
      {text:'56張照片',confidence:.95,candidateCount:1,bounds:{x:200,y:165,width:140,height:30}}]},
    {name:'missing old list window',includeList:false},
  ];
  for(const bad of badCases){
    const a=analyzer();await capture(a,{frameId:'3'.repeat(64),kind:'list'});
    await assert.rejects(()=>capture(a,{frameId:'4'.repeat(64),kind:'detail',at:20000,includeList:bad.includeList??true,
      ocr:bad.ocr}),undefined,bad.name);
  }
  const a=analyzer();await capture(a,{frameId:'9'.repeat(64),kind:'list'});
  const foreignBefore=native({frameId:'a'.repeat(64),at:29990,kind:'detail',focused:5798});
  const foreignAfter=native({frameId:'a'.repeat(64),at:30010,kind:'detail',focused:5798});
  foreignBefore.target.pid=99999;foreignAfter.target.pid=99999;
  await assert.rejects(()=>capture(a,{frameId:'a'.repeat(64),kind:'detail',at:30000,
    beforeValue:foreignBefore,afterValue:foreignAfter}),undefined,'foreign PID');
  const legacy=analyzer();await capture(legacy,{frameId:'d'.repeat(64),kind:'list'});
  const legacyBefore=native({frameId:'e'.repeat(64),at:39990,kind:'detail',focused:5798});
  const legacyAfter=native({frameId:'e'.repeat(64),at:40010,kind:'detail',focused:5798});
  for(const value of [legacyBefore,legacyAfter]){
    value.nodes.find(n=>n.id==='detail-window').children.push('back');
    value.nodes.push({id:'back',parentID:'detail-window',role:'AXButton',title:'Back',enabled:true,
      framePt:{x:360,y:80,width:40,height:20},offscreen:false,children:[]});
  }
  await assert.rejects(()=>capture(legacy,{frameId:'e'.repeat(64),kind:'detail',at:40000,
    beforeValue:legacyBefore,afterValue:legacyAfter}),/CANONICAL_GROUP_NOT_GROUNDED/,
    'legacy Back path still requires original group witness');
  for(const value of [legacyBefore,legacyAfter]){
    value.nodes.find(n=>n.id==='detail-window').children.push('back-2');
    value.nodes.push({id:'back-2',parentID:'detail-window',role:'AXButton',title:'Back',enabled:true,
      framePt:{x:405,y:80,width:40,height:20},offscreen:false,children:[]});
  }
  await assert.rejects(()=>capture(legacy,{frameId:'e'.repeat(64),kind:'detail',at:40000,
    beforeValue:legacyBefore,afterValue:legacyAfter}),/CANONICAL_GROUP_NOT_GROUNDED/,
    'multiple Back buttons cannot enter the no-Back detail-grid route');
});

test('scroll offset normalization uses native AX min/max, preserves raw value, and rejects absent or invalid ranges',async()=>{
  const a=analyzer();
  const list=await capture(a,{frameId:'5'.repeat(64),scrollValue:'225',min:0,max:300});
  assert.equal(list.boundary_evidence.raw_value,'225');
  assert.equal(list.boundary_evidence.value,.75);
  assert.equal(list.boundary.top,false);assert.equal(list.boundary.bottom,false);
  for(const options of [{min:null,max:300},{min:300,max:0},{scrollValue:'NaN'},{scrollValue:''},{scrollValue:'   '},
    {scrollValue:'301'},{min:false,max:300}]){
    await assert.rejects(()=>capture(analyzer(),{frameId:'6'.repeat(64),...options}),/SCROLL_BOUNDARY_UNKNOWN|SCROLL_RANGE_INVALID/);
    await assert.rejects(()=>capture(analyzer(),{frameId:'b'.repeat(64),scrollWitness:true,...options}),/SCROLL_BOUNDARY_UNKNOWN|SCROLL_RANGE_INVALID/);
  }
  const witness=await capture(analyzer(),{frameId:'c'.repeat(64),scrollWitness:true,scrollValue:'225',min:0,max:300});
  assert.equal(witness.scroll_witness.scroll_offset.value,.75);
});

test('Owner title alias is exact and per-analyzer; no generic fuzzy candidate is accepted',async()=>{
  const a=analyzer({groupTitleAliases:[alias]});
  const list=await capture(a,{frameId:'7'.repeat(64),kind:'list',group:alias});
  assert.equal(list.surface,'ALBUMS');
  await assert.rejects(()=>capture(analyzer(),{frameId:'8'.repeat(64),kind:'list',group:alias}),/CANONICAL_GROUP_NOT_GROUNDED/);
});

test('classifier binds detail grid identity to CUA bounds and exact SCK text after loading frame OCR',async()=>{
  const screenshot=tinyPNG(),frameId=hash(screenshot),sessionId='classifier-detail';
  const state='detail AX snapshot';const stateBytes=Buffer.from(state);
  const ref=(name,body)=>({path:`harness-development/detail-${name}.json`,bytes:body.length,sha256:hash(Buffer.from(body))});
  const title={text:'2024/05/27~05/31',bounds:[1,1,8,3]};
  const count={text:'56張照片',bounds:[1,5,8,3]};
  const ocr={cua_frame_id:frameId,sck_frame_sha256:'e'.repeat(64),
    cua:[{...title,confidence:.95,candidate_count:1},{...count,confidence:.95,candidate_count:1}],
    sck:[{text:title.text,confidence:.95,candidate_count:1,bounds:[203,300.5,4,4]},
      {text:count.text,confidence:.95,candidate_count:1,bounds:[201,303.5,8,6]}]};
  let ocrBody=JSON.stringify(ocr),ocrRef=ref('ocr',ocrBody);
  const displayBounds=[0,0,1000,1000],cuaBounds=[200,300,10,10];
  const sidecar={native_binding:{cua_capture_bounds_points:cuaBounds,display_bounds_points:displayBounds,
    cua_size_px:[10,10],sck_size_px:[1000,1000]}};
  const supportBody=JSON.stringify(sidecar),supportRef=ref('support',supportBody);
  const manifestRef0=ref('manifest','');let manifestBody='',manifestRef;
  const artifacts=[];
  const retain=async({artifact,kind})=>{const body=JSON.stringify(artifact);artifacts.push({kind,artifact});return ref(kind,body);};
  const analysis={version:1,frame_id:frameId,session_id:sessionId,source_sha256:frameId,
    source_ax_sha256:hash(stateBytes),surface:'ALBUM_DETAIL',group_key:'stable-group',
    native:{bundle_id:'jp.naver.line.mac',pid:25266,window_id:5798,display_id:1,cua_capture_bounds_points:cuaBounds},
    layout:{line_version:'test',language:'zh-Hant',window_class:'AXStandardWindow',native_scale:2},
    surface_structure:[{role:'window',subrole:'AXStandardWindow',identifier:'detail'}],surface_bounds_px:[0,0,10,10],
    occlusion:'CLEAR',editable_focus:'NONE',focus_evidence:{version:1,frame_id:frameId,session_id:sessionId,
      kind:'NONE',focused_index:null},ax:{version:1,focused_index:null,elements:[]},cards:[],
    detail_identity:{kind:'ALBUM_DETAIL_GRID',fingerprint:target,title,photo_count:count,group_key:'stable-group',
      list_frame_id:'1'.repeat(64),list_window_id:3766,detail_window_id:5798,pid:25266,process_start:[100,5],
      native_lineage_ref:ref('lineage','lineage')},
    boundary:{top:false,bottom:false},boundary_evidence:{version:1,frame_id:frameId,session_id:sessionId,source:'NOT_APPLICABLE'},
    chooser_controls:{root_index:null,path_field_index:null,confirm_button_index:null,selected_leaf_index:null}};
  const frameSupport=async({layoutKey,geometryRef})=>{
    const manifest={pairFrameId:frameId,surface:'ALBUM_DETAIL',layoutKey,displayBounds,imageWidthPx:1000,imageHeightPx:1000,
      geometryEvidence:{path:geometryRef.path,sha256:geometryRef.sha256},
      support:{path:supportRef.path,sha256:supportRef.sha256},sckFrameId:ocr.sck_frame_sha256,ocr:ocrRef};
    manifestBody=JSON.stringify(manifest);manifestRef={...manifestRef0,bytes:manifestBody.length,sha256:hash(Buffer.from(manifestBody))};
    return {provider:'SCREEN_CAPTURE_KIT',surface:'ALBUM_DETAIL',pairFrameId:frameId,sessionId,uncertaintyPx:2,
      safeMarginPx:6,reference:supportRef,manifestReference:manifestRef,
      readRef:async item=>new Uint8Array(Buffer.from(item.path===manifestRef.path?manifestBody
        :item.path===supportRef.path?supportBody:ocrBody))};
  };
  const classifier=createLiveClassifier({retain,frameSupport,groupKey:'stable-group',
    analyzeCapture:async()=>analysis});
  const saved={path:'harness-development/detail-frame.png',bytes:screenshot.length,sha256:frameId,
    ax:{path:'harness-development/detail-ax.txt',bytes:stateBytes.length,sha256:hash(stateBytes)}};
  const observation=await classifier.classify({capture:{screenshot,state},saved,frameId,sessionId,
    capturedAt:'2026-10-17T00:00:00.000Z',sourceBinding:{}});
  assert.equal(observation.surface,'ALBUM_DETAIL');
  assert.deepEqual(observation.cards,[]);
  assert.deepEqual(observation.detail_identity.fingerprint,target);
  assert.ok(artifacts.some(item=>item.kind==='classifier-evidence'&&item.artifact.detail_identity));
  const offTarget=structuredClone(ocr);offTarget.sck[0].bounds=[500,700,80,30];
  ocrBody=JSON.stringify(offTarget);ocrRef=ref('ocr',ocrBody);
  const negative=createLiveClassifier({retain,frameSupport,groupKey:'stable-group',analyzeCapture:async()=>analysis});
  await assert.rejects(()=>negative.classify({capture:{screenshot,state},saved,frameId,sessionId,
    capturedAt:'2026-10-17T00:00:00.000Z',sourceBinding:{}}),/CLASSIFIER_DETAIL_OCR_BINDING/);
});
