import test from 'node:test';
import assert from 'node:assert/strict';
import {buildMenuEnvelope} from '../harness-development/line-two-album-pilot-20261014/mac/analyzer.mjs';
import {locateSaveAllRow} from '../harness-development/line-two-album-pilot-20261014/mac_runtime.mjs';

// Real measured evidence (probe 22-probe3, LINE detail window 654x1286 px at backing scale 2):
// the layer-101 popup and its 儲存全部 label extend past the hosted CUA crop, so only the
// intersection of popup ∩ crop ∩ label is addressable.
const WIDTH=654,HEIGHT=1286;
const POPUP_SCK=[1282,196,274,334];
const POPUP_CUA=[566,104,274,334];
const LABEL_SCK=[1333.685927,349.871193,110.101982,30.257612];
const LABEL_CUA=[617.685927,257.871193,110.101982,30.257612];
const SAFE=[617.685927,257.871193,36.314073,30.257612];
const ERODED=[623.685927,263.871193,24.314073,18.257612];
const SAVE_ALL_ROW={text:'儲存全部',bounds:LABEL_SCK,confidence:1,candidate_count:1};
const TITLE_ROW={text:'2024/05/27~05/31',bounds:[30,178,380,44],confidence:.5,candidate_count:1};
const COUNT_ROW={text:'56張照片',bounds:[30,242,102,26],confidence:1,candidate_count:1};

function facts(overrides={}) {
  return {...{
    kind:'MENU_FRAME_FACTS',version:1,evidence_only:true,admissible_to_ordinary_classifier:false,
    frame_id:'a'.repeat(64),session_id:'execution',source_sha256:'a'.repeat(64),source_ax_sha256:'b'.repeat(64),
    native:{bundle_id:'jp.naver.line.mac',pid:2,window_id:7,display_id:1,
      cua_capture_bounds_points:[358,46,327,643]},
    process_start:[1,0],layer_identity:{owner_pid:2,window_id:9,layer:101,above_window_id:7},
    popup:{window_number:9,layer:101,bounds_pt:[641,98,137,167],bounds_px:POPUP_SCK,above_window_id:7},
    mapping:{kind:'SCK_TO_CUA_LOCAL',crop_px:[0,0,WIDTH,HEIGHT],display_pt:[0,0,1147,745],backing_scale:2,
      cua_offset_px:[-716,-92],cua_scale:[2,2],
      inverse:'cua_px = sck_px * cua_scale / backing_scale + cua_offset_px'},
    uncertainty_px:2,
    layout:{line_version:'9.4.0',language:'zh-Hant',window_class:'AXStandardWindow',native_scale:2},
    surface_structure:[{role:'window',subrole:'AXStandardWindow',identifier:''}],
    ocr:[TITLE_ROW,COUNT_ROW],
    detail_fingerprint:{start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56},
    detail_window_id:7,list_window_id:107},...overrides};
}
const code=error=>error?.code??error?.message;
// The intersection is the same real geometry the Python calibrate contract accepts with its 1e-6
// drift tolerance; binary floating point alone makes the last components differ by 7.1e-15.
const close=(actual,expected,tolerance=1e-9)=>{
  assert.equal(actual.length,expected.length);
  actual.forEach((value,index)=>assert.ok(Math.abs(value-expected[index])<=tolerance,
    `${value} vs ${expected[index]}`));
};

test('real popup/label geometry outside the hosted CUA crop yields the proven intersection',()=>{
  const envelope=buildMenuEnvelope({menuFrame:facts(),sckRows:[SAVE_ALL_ROW],cuaRows:[],width:WIDTH,height:HEIGHT});
  close(envelope.safe_bounds_px,SAFE);
  close(envelope.eroded_bounds_px,ERODED);
  assert.deepEqual(envelope.popup.cua_bounds_px,POPUP_CUA);
  assert.deepEqual(envelope.save_all.cua_label_bounds_px,LABEL_CUA);
  assert.equal(envelope.uncertainty_px,2);
  const row=locateSaveAllRow({envelope,width:WIDTH,height:HEIGHT});
  assert.deepEqual(row.save_all,[635,272]);
  close(row.safeBounds,SAFE);
  assert.deepEqual(row.menuBounds,POPUP_CUA);
  assert.equal(row.dismiss_point[0]>POPUP_CUA[0],false);
  assert.deepEqual(row.dismiss_point,[220,200]);
  assert.equal(row.label,'儲存全部');
});

test('a popup that never reaches the crop is refused instead of clicked',()=>{
  const offscreen=facts({popup:{window_number:9,layer:101,bounds_pt:[641,98,137,167],
    bounds_px:[-2000,196,274,334],above_window_id:7}});
  assert.throws(()=>buildMenuEnvelope({menuFrame:offscreen,sckRows:[SAVE_ALL_ROW],cuaRows:[],width:WIDTH,height:HEIGHT}),
    error=>code(error)==='MENU_ENVELOPE_POPUP_OFFSCREEN');
});

test('a save all label that mostly misses the crop is refused instead of clicked',()=>{
  const outside=facts();
  assert.throws(()=>buildMenuEnvelope({menuFrame:outside,
    sckRows:[{...SAVE_ALL_ROW,bounds:[2200,349.871193,110.101982,30.257612]}],cuaRows:[],
    width:WIDTH,height:HEIGHT}),error=>code(error)==='MENU_ENVELOPE_ROW_OFFSCREEN');
});

test('a duplicated save all row in the fresh SCK OCR is refused',()=>{
  assert.throws(()=>buildMenuEnvelope({menuFrame:facts(),
    sckRows:[SAVE_ALL_ROW,{...SAVE_ALL_ROW,bounds:[1333.685927,400.0,110.101982,30.257612]}],cuaRows:[],
    width:WIDTH,height:HEIGHT}),error=>code(error)==='MENU_SAVE_ALL_ROW_NOT_UNIQUE');
});

test('a hosted CUA row that disagrees with the SCK row refuses as a space conflict',()=>{
  assert.throws(()=>buildMenuEnvelope({menuFrame:facts(),sckRows:[SAVE_ALL_ROW],
    cuaRows:[{text:'儲存全部',bounds:[640.0,257.871193,110.101982,30.257612],confidence:1,candidate_count:1}],
    width:WIDTH,height:HEIGHT}),error=>code(error)==='MENU_ENVELOPE_ROW_SPACE_CONFLICT');
  const mirrored=buildMenuEnvelope({menuFrame:facts(),sckRows:[SAVE_ALL_ROW],
    cuaRows:[{text:'儲存全部',bounds:[618.0,257.871193,110.101982,30.257612],confidence:1,candidate_count:1}],
    width:WIDTH,height:HEIGHT});
  close(mirrored.safe_bounds_px,SAFE);
});

test('a menu frame facts record of the wrong kind is refused before any geometry',()=>{
  assert.throws(()=>buildMenuEnvelope({menuFrame:{...facts(),admissible_to_ordinary_classifier:true},
    sckRows:[SAVE_ALL_ROW],cuaRows:[],width:WIDTH,height:HEIGHT}),
    error=>code(error)==='MENU_ENVELOPE_FACTS_REQUIRED');
});
