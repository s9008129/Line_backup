import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createLiveClassifier,sha256Hex} from '../live_classifier.mjs';
import {createChooserLocators} from '../chooser_locators.mjs';

const jsonBytes=value=>new TextEncoder().encode(JSON.stringify(value));
const ref=(path,raw)=>({path,bytes:raw.byteLength,sha256:sha256Hex(raw)});

function fixture({mutateAnalysis=()=>{}}={}) {
  const retained=new Map();let counter=0;
  const retain=async ({artifact,kind,frameId})=>{
    const raw=jsonBytes(artifact);const result=ref(`harness-development/test/${kind}-${++counter}.json`,raw);
    retained.set(result.path,raw);return result;
  };
  const frameSupport=async args=>{
    const supportRef={path:'harness-development/test/support.json',bytes:20,sha256:'a'.repeat(64)};
    const ocr={version:1,cua_frame_id:args.frameId,sck_frame_sha256:'c'.repeat(64),cua:[],sck:[]};
    const ocrRaw=jsonBytes(ocr);const ocrRef=ref('harness-development/test/ocr.json',ocrRaw);retained.set(ocrRef.path,ocrRaw);
    const manifest={pairFrameId:args.frameId,surface:args.surface,layoutKey:args.layoutKey,sckFrameId:'c'.repeat(64),
      geometryEvidence:args.geometryRef,support:supportRef,ocr:ocrRef};
    const manifestRaw=jsonBytes(manifest);const manifestReference=ref('harness-development/test/manifest.json',manifestRaw);
    retained.set(manifestReference.path,manifestRaw);
    return {provider:'SCREEN_CAPTURE_KIT',surface:args.surface,pairFrameId:args.frameId,sessionId:args.sessionId,
      uncertaintyPx:2,safeMarginPx:8,reference:supportRef,manifestReference,
      readRef:async value=>retained.get(value.path)};
  };
  const analyzeCapture=async args=>{
    const data={version:1,frame_id:args.frameId,session_id:args.sessionId,source_sha256:args.frameId,
      source_ax_sha256:args.sourceAXSha256,surface:'ALBUM_DETAIL',group_key:'group:fixture',
      native:{bundle_id:'jp.naver.line.mac',pid:42,window_id:8,display_id:2,cua_capture_bounds_points:[0,0,100,100]},
      layout:{line_version:'1.2',language:'en',window_class:'LINEWindow',native_scale:2},surface_structure:[
        {role:'window',subrole:'AXWindow',identifier:'line-window'}],surface_bounds_px:[0,0,args.width,args.height],
      occlusion:'CLEAR',editable_focus:'NONE',focus_evidence:{version:1,frame_id:args.frameId,session_id:args.sessionId,
        kind:'NONE',focused_index:null},ax:{version:1,focused_index:null,elements:[{index:0,role:'window',subrole:'AXWindow',
          identifier:'line-window',label:'LINE',value:null,bounds_px:[0,0,args.width,args.height],parent_index:null,enabled:true}]},
      cards:[],boundary:{top:false,bottom:false},boundary_evidence:{version:1,frame_id:args.frameId,
        session_id:args.sessionId,source:'NOT_APPLICABLE'},
      chooser_controls:{root_index:null,path_field_index:null,confirm_button_index:null,selected_leaf_index:null}};
    mutateAnalysis(data);return data;
  };
  const classifier=createLiveClassifier({retain,frameSupport,analyzeCapture,groupKey:'group:fixture'});
  const screenshot=new Uint8Array(24);screenshot.set([137,80,78,71,13,10,26,10]);
  const view=new DataView(screenshot.buffer);view.setUint32(16,128);view.setUint32(20,128);
  const frameId=sha256Hex(screenshot),state='{}',stateBytes=new TextEncoder().encode(state);
  return {classifier,frameId,screenshot,state,stateRef:{path:'harness-development/test/frame.ax',bytes:stateBytes.byteLength,
    sha256:sha256Hex(stateBytes)}};
}

test('classifier returns exactly the frozen 17-key frame with captured-source bindings',async()=>{
  const f=fixture();
  const observation=await f.classifier.classify({capture:{screenshot:f.screenshot,state:f.state},saved:{path:'harness-development/test/frame.png',
    bytes:f.screenshot.byteLength,sha256:f.frameId,ax:f.stateRef},frameId:f.frameId,sessionId:'session-1',
    capturedAt:'2026-10-10T12:00:00.000Z'});
  assert.equal(Object.keys(observation).length,17);
  assert.equal(observation.frame_id,f.frameId);
  assert.equal(observation.mapping.space,'CUA_CAPTURE_PIXELS');
  assert.equal(observation.mapping.sck_support.path,'harness-development/test/support.json');
});

test('classifier rejects an analyzer result from another screenshot',async()=>{
  const f=fixture({mutateAnalysis:data=>{data.source_sha256='0'.repeat(64);}});
  await assert.rejects(f.classifier.classify({capture:{screenshot:f.screenshot,state:f.state},saved:{path:'harness-development/test/frame.png',
    bytes:f.screenshot.byteLength,sha256:f.frameId,ax:f.stateRef},frameId:f.frameId,sessionId:'session-1',
    capturedAt:'2026-10-10T12:00:00.000Z'}),/CLASSIFIER_SOURCE_BINDING/);
});

test('chooser locators only resolve a typed focused path field and enabled confirm control',()=>{
  const locators=createChooserLocators();
  const go={version:1,phase:'GO_TO_FOLDER',frame:{frame_id:'a'.repeat(64)},control:{path_field_index:4,
    path_field_role:'text field',path_field_subrole:'PathTextField',path_field_identifier:'path',
    path_field_bounds_px:[2,3,40,12],path_field_enabled:true,focused:true}};
  assert.equal(locators.locatePathField(go).index,4);
  const filled={version:1,phase:'PATH_FILLED',frame:{frame_id:'b'.repeat(64)},control:{path_field_index:4,
    path_field_role:'text field',path_field_subrole:'PathTextField',path_field_identifier:'path',
    path_field_bounds_px:[2,3,40,12],path_field_enabled:true,
    value:'/tmp/album',focused:true}};
  assert.equal(locators.validatePath(filled,'/tmp/album'),true);
  const selected={version:1,phase:'DESTINATION_SELECTED',frame:{frame_id:'c'.repeat(64)},control:{path_field_index:4,
    path_field_identifier:'path',path_field_role:'text field',path_field_subrole:'PathTextField',path_field_enabled:true,value:'/tmp/album',
    selected_leaf:'album',selected_leaf_index:6,selected_leaf_identifier:'album-row',
    selected_leaf_bounds_px:[2,30,40,12],selected_leaf_ocr:{text:'album',bounds:[3,31,24,8]},
    confirm_index:5,confirm_role:'button',confirm_identifier:'open',confirm_bounds_px:[80,40,20,10],
    confirm_enabled:true,confirm_point:[90,45]}};
  assert.equal(locators.validateLeaf(selected,'/tmp/album'),true);
  assert.deepEqual(locators.locateConfirm(selected).point,[90,45]);
  assert.throws(()=>locators.locatePathField({...go,control:{...go.control,path_field_subrole:'AXTextField'}}),
    /PATH_FIELD_UNKNOWN/);
});
