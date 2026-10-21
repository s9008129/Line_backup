import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {completeDateTitle} from './analyzer.mjs';

const fail = code => { throw Object.assign(new Error(code), {code}); };
const need = (ok, code) => { if (!ok) fail(code); };
const encoder = new TextEncoder();
const hex64 = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
export const sha256Hex = bytes => createHash('sha256').update(bytes).digest('hex');
const shaJson = value => sha256Hex(encoder.encode(canonicalJSON(value)));
const canonicalJSON = value => {
  if (Array.isArray(value)) return `[${value.map(canonicalJSON).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${canonicalJSON(value[k])}`).join(',')}}`;
  return JSON.stringify(value);
};

function imageSize(raw) {
  if (raw.length >= 24 && raw[0]===137 && raw[1]===80 && raw[2]===78 && raw[3]===71) {
    const view=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);return [view.getUint32(16),view.getUint32(20)];
  }
  if (raw[0]!==255 || raw[1]!==216) fail('UNSUPPORTED_FRAME');
  let i=2;
  while(i+4<=raw.length) {
    if(raw[i]!==255)fail('INVALID_JPEG_FRAME');let marker=raw[i+1];i+=2;
    if(marker===0xd8 || marker===0xd9 || (marker>=0xd0&&marker<=0xd7))continue;
    const size=(raw[i]<<8)|raw[i+1];if(size<2||i+size>raw.length)fail('INVALID_JPEG_FRAME');
    if([0xc0,0xc1,0xc2].includes(marker))return [(raw[i+5]<<8)|raw[i+6],(raw[i+3]<<8)|raw[i+4]];
    i+=size;
  }
  fail('INVALID_FRAME_DIMENSIONS');
}

function ref(value, code) {
  need(value && typeof value.path==='string' && value.path.startsWith('harness-development/')
    && Number.isInteger(value.bytes) && value.bytes>0 && hex64(value.sha256),code);
  return {path:value.path,bytes:value.bytes,sha256:value.sha256};
}

function rect(value,width,height,code) {
  need(Array.isArray(value)&&value.length===4&&value.every(Number.isFinite),code);
  const [x,y,w,h]=value;need(w>0&&h>0&&x>=0&&y>=0&&x+w<=width&&y+h<=height,code);return value;
}
function nativeRowRect(value,code) {
  need(Array.isArray(value)&&value.length===4&&value.every(Number.isFinite)
    &&value[2]>0&&value[3]>0,code);
  return value;
}
const inside=(a,b,margin=0)=>a[0]>=b[0]+margin&&a[1]>=b[1]+margin
  &&a[0]+a[2]<=b[0]+b[2]-margin&&a[1]+a[3]<=b[1]+b[3]-margin;
const intersects=(a,b)=>a[0]<b[0]+b[2]&&b[0]<a[0]+a[2]&&a[1]<b[1]+b[3]&&b[1]<a[1]+a[3];
const erode=(r,margin)=>[r[0]+margin,r[1]+margin,r[2]-2*margin,r[3]-2*margin];

const observationKeys=['frame','frame_id','session_id','group_key','surface','captured_at','provider','layout_key',
  'window_id','pid','width','height','mapping','cards','boundary','editable_focus','occlusion'];
const ONE56={start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56};
const A45={start_date:'2024-04-22',end_date:'2024-04-26',expected_images:45};
const B78={start_date:'2024-04-21',end_date:'2024-04-21',expected_images:78};
const NAME_ONLY_TARGETS=[ONE56,A45,B78];
const isNameOnlyTarget=id=>NAME_ONLY_TARGETS.some(target=>target.start_date===id.start_date
  &&target.end_date===id.end_date&&target.expected_images===id.expected_images);

export function createLiveClassifier({retain,readRetained,frameSupport,analyzeCapture,analyzeScrollWitness,analyzeVisualCardDiagnostic,analyzeMenuFrame,buildMenuEnvelope,groupKey,clock=()=>Date.now()}) {
  need(typeof retain==='function'&&typeof frameSupport==='function'&&typeof analyzeCapture==='function','CLASSIFIER_DEPENDENCY_REQUIRED');
  const readBack=reference=>{need(typeof readRetained==='function','CLASSIFIER_READ_RETAINED_REQUIRED');return readRetained(reference);};
  need(typeof groupKey==='string'&&groupKey,'CLASSIFIER_GROUP_REQUIRED');
  const cache=new Map(),scrollCache=new Map(),menuEnvelopes=new Map();

  async function classify({capture,saved,frameId,sessionId,capturedAt,sourceBinding,capturedContext},{scrollWitness=false}={}) {
    need(capture?.screenshot instanceof Uint8Array&&typeof capture.state==='string','CLASSIFIER_CAPTURE_REQUIRED');
    need(hex64(frameId)&&sha256Hex(capture.screenshot)===frameId&&saved?.sha256===frameId,'CLASSIFIER_FRAME_HASH');
    need(typeof capturedAt==='string'&&Number.isFinite(Date.parse(capturedAt)),'CLASSIFIER_CAPTURE_TIME');
    const [width,height]=imageSize(capture.screenshot);
    const sourceAX=encoder.encode(capture.state);const sourceAXSha=sha256Hex(sourceAX);
    need(saved.ax&&saved.ax.bytes===sourceAX.byteLength&&saved.ax.sha256===sourceAXSha,'CLASSIFIER_AX_RETENTION');
    const analyzer=scrollWitness?analyzeScrollWitness:analyzeCapture;
    need(typeof analyzer==='function','SCROLL_WITNESS_ANALYZER_REQUIRED');
    const analysis=await analyzer({screenshot:capture.screenshot,axText:capture.state,frameId,sessionId,capturedAt,
      width,height,sourceAXSha256:sourceAXSha,sourceBinding,capturedContext,saved});
    need(analysis?.version===1&&analysis.frame_id===frameId&&analysis.session_id===sessionId
      &&analysis.source_sha256===frameId&&analysis.source_ax_sha256===sourceAXSha,'CLASSIFIER_SOURCE_BINDING');
    const keys=['version','frame_id','session_id','source_sha256','source_ax_sha256','surface','group_key','native',
      'layout','surface_structure','surface_bounds_px','occlusion','editable_focus','focus_evidence','ax','cards',
      'boundary','boundary_evidence','chooser_controls','detail_identity'];
    if(scrollWitness)keys.push('scroll_witness');
    need(Object.keys(analysis).sort().join(',')===keys.sort().join(','),'CLASSIFIER_ANALYSIS_SCHEMA');
    need(['ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER'].includes(analysis.surface)&&analysis.group_key===groupKey,
      'CLASSIFIER_CONTEXT');
    need(analysis.occlusion==='CLEAR','CLASSIFIER_OCCLUSION_UNKNOWN');
    const native=analysis.native;const nativeKeys=['bundle_id','pid','window_id','display_id','cua_capture_bounds_points'];
    need(native&&Object.keys(native).sort().join(',')===nativeKeys.sort().join(',')&&native.bundle_id==='jp.naver.line.mac'
      &&Number.isInteger(native.pid)&&native.pid>0&&Number.isInteger(native.window_id)&&native.window_id>0
      &&Number.isInteger(native.display_id)&&native.display_id>0,'CLASSIFIER_NATIVE_IDENTITY');
    need(Array.isArray(native.cua_capture_bounds_points)&&native.cua_capture_bounds_points.length===4
      &&native.cua_capture_bounds_points.every(Number.isFinite),'CLASSIFIER_NATIVE_BOUNDS');
    const layout=analysis.layout;const layoutKeys=['line_version','language','window_class','native_scale'];
    need(layout&&Object.keys(layout).sort().join(',')===layoutKeys.sort().join(',')
      &&['line_version','language','window_class'].every(k=>typeof layout[k]==='string'&&layout[k])
      &&Number.isFinite(layout.native_scale)&&layout.native_scale>0,'CLASSIFIER_LAYOUT');
    const ax=analysis.ax;const axKeys=['version','focused_index','elements'];
    need(ax&&Object.keys(ax).sort().join(',')===axKeys.sort().join(',')&&ax.version===1&&Array.isArray(ax.elements),
      'CLASSIFIER_AX_SCHEMA');
    const axElements=ax.elements;
    for(const el of axElements) {
      const baseKeys=['index','role','subrole','identifier','label','value','bounds_px','parent_index','enabled'];
      const rangeKeys=el?.role==='scroll bar'?['minimum_value','maximum_value','native_node_id']:[];
      need(el&&Object.keys(el).sort().join(',')===[...baseKeys,...rangeKeys].sort().join(',')&&Number.isInteger(el.index)&&el.index>=0&&typeof el.role==='string'
        &&typeof el.subrole==='string'&&typeof el.identifier==='string'&&typeof el.enabled==='boolean'
        &&(el.parent_index===null||Number.isInteger(el.parent_index)),'CLASSIFIER_AX_ELEMENT');
      if(el.role==='scroll bar')need((el.minimum_value===null&&el.maximum_value===null
        ||Number.isFinite(el.minimum_value)&&Number.isFinite(el.maximum_value)&&el.maximum_value>el.minimum_value)
        &&typeof el.native_node_id==='string','CLASSIFIER_AX_SCROLL_RANGE');
      if(scrollWitness&&el.role==='row')nativeRowRect(el.bounds_px,'CLASSIFIER_AX_ELEMENT_BOUNDS');
      else rect(el.bounds_px,width,height,'CLASSIFIER_AX_ELEMENT_BOUNDS');
    }
    need(new Set(axElements.map(e=>e.index)).size===axElements.length,'CLASSIFIER_AX_DUPLICATE_INDEX');
    const chooser=analysis.chooser_controls;
    const chooserKeys=['root_index','path_field_index','confirm_button_index','selected_leaf_index'];
    need(chooser&&Object.keys(chooser).sort().join(',')===chooserKeys.sort().join(',')
      &&chooserKeys.every(key=>chooser[key]===null||(Number.isInteger(chooser[key])&&chooser[key]>=0)),
      'CLASSIFIER_CHOOSER_CONTROLS');
    if(analysis.surface==='FOLDER_CHOOSER') {
      need(chooser.root_index!==null,
        'CLASSIFIER_CHOOSER_CONTROLS');
      const root=axElements.find(e=>e.index===chooser.root_index);
      const field=axElements.find(e=>e.index===chooser.path_field_index);
      const button=axElements.find(e=>e.index===chooser.confirm_button_index);
      need(root&&['window','sheet','dialog'].includes(root.role)&&(chooser.path_field_index===null||field?.role==='text field'&&field.subrole==='PathTextField')
        &&(chooser.confirm_button_index===null||button?.role==='button'),'CLASSIFIER_CHOOSER_CONTROLS');
      if(chooser.selected_leaf_index!==null) {
        const leaf=axElements.find(e=>e.index===chooser.selected_leaf_index);
        need(leaf&&['text','static text','button'].includes(leaf.role),'CLASSIFIER_CHOOSER_CONTROLS');
      }
    } else need(chooserKeys.every(key=>chooser[key]===null),'CLASSIFIER_CHOOSER_CONTROLS');
    need(Array.isArray(analysis.surface_structure)&&analysis.surface_structure.every(item=>item
      &&Object.keys(item).sort().join(',')==='identifier,role,subrole'&&typeof item.role==='string'
      &&typeof item.subrole==='string'&&typeof item.identifier==='string'),'CLASSIFIER_SURFACE_STRUCTURE');
    const structureSHA=shaJson(analysis.surface_structure);
    const signature={line_version:layout.line_version,language:layout.language,window_class:layout.window_class,
      frame_width_px:width,frame_height_px:height,native_scale:layout.native_scale,structure_sha256:structureSHA};
    const layoutKey=shaJson(signature);
    const axSnapshot={version:1,frame_id:frameId,session_id:sessionId,pid:native.pid,window_id:native.window_id,
      surface:analysis.surface,focused_index:ax.focused_index,elements:axElements};
    const axRef=ref(await retain({artifact:axSnapshot,kind:'grounded-ax',frameId,sessionId}),'GROUNDING_AX_RETAIN_REQUIRED');
    const boundary=analysis.boundary;
    need(boundary&&Object.keys(boundary).sort().join(',')==='bottom,top'&&typeof boundary.top==='boolean'
      &&typeof boundary.bottom==='boolean'&&analysis.boundary_evidence?.version===1
      &&analysis.boundary_evidence.frame_id===frameId&&analysis.boundary_evidence.session_id===sessionId,
      'CLASSIFIER_BOUNDARY_EVIDENCE');
    const boundaryRef=ref(await retain({artifact:analysis.boundary_evidence,kind:'boundary-evidence',frameId,sessionId}),
      'CLASSIFIER_BOUNDARY_RETAIN_REQUIRED');
    if(analysis.surface==='ALBUMS') {
      const proof=analysis.boundary_evidence;
      const actualKeys=Object.keys(proof).sort().join(',');
      const expectedKeys=['version','frame_id','session_id','source','indicator_index','minimum','maximum','value',
        'raw_value','ax_minimum','ax_maximum','indicator_native_id','native_context_ref'].sort().join(',');
      need(actualKeys===expectedKeys
        &&proof.source==='AX_SCROLLBAR'&&Number.isInteger(proof.indicator_index)
        &&Number.isFinite(proof.minimum)&&Number.isFinite(proof.maximum)&&Number.isFinite(proof.value)
        &&proof.maximum>proof.minimum&&Number.isFinite(proof.ax_minimum)&&Number.isFinite(proof.ax_maximum)
        &&proof.ax_maximum>proof.ax_minimum&&typeof proof.raw_value==='string'
        &&/^-?(?:\d+\.?\d*|\.\d+)$/.test(proof.raw_value)&&Number.isFinite(Number(proof.raw_value))
        &&Number(proof.raw_value)>=proof.ax_minimum&&Number(proof.raw_value)<=proof.ax_maximum
        &&typeof proof.indicator_native_id==='string'&&proof.native_context_ref?.sha256,'CLASSIFIER_BOUNDARY_EVIDENCE');
      const indicator=axElements.find(e=>e.index===proof.indicator_index);
      const nativeContext=sourceBinding?.after?.value;
      const nativeNode=nativeContext?.nodes?.filter(n=>n.id===proof.indicator_native_id)??[];
      const normalized=(Number(proof.raw_value)-proof.ax_minimum)/(proof.ax_maximum-proof.ax_minimum);
      need(indicator?.role==='scroll bar'&&indicator.value===proof.raw_value
        &&indicator.minimum_value===proof.ax_minimum&&indicator.maximum_value===proof.ax_maximum
        &&indicator.native_node_id===proof.indicator_native_id&&proof.value===normalized
        &&proof.native_context_ref?.path===sourceBinding?.after?.reference?.path
        &&proof.native_context_ref?.sha256===sourceBinding?.after?.reference?.sha256
        &&nativeNode.length===1&&nativeNode[0].value===proof.raw_value
        &&nativeNode[0].minimumValue===proof.ax_minimum&&nativeNode[0].maximumValue===proof.ax_maximum
        &&boundary.top===(Number(proof.raw_value)===proof.ax_minimum)
        &&boundary.bottom===(Number(proof.raw_value)===proof.ax_maximum),
        'CLASSIFIER_BOUNDARY_EVIDENCE');
    } else need(canonicalJSON(analysis.boundary_evidence)===canonicalJSON({version:1,frame_id:frameId,
      session_id:sessionId,source:'NOT_APPLICABLE'}),'CLASSIFIER_BOUNDARY_EVIDENCE');
    const focus=analysis.focus_evidence;
    if(analysis.editable_focus==='NONE') {
      need(canonicalJSON(focus)===canonicalJSON({version:1,frame_id:frameId,session_id:sessionId,kind:'NONE',
        focused_index:ax.focused_index}),'CLASSIFIER_FOCUS_EVIDENCE');
    } else if(analysis.editable_focus==='LOW_GHOST') {
      fail('CLASSIFIER_FOCUS_UNSUPPORTED');
    } else if(analysis.editable_focus==='HIGH_EDITABLE') {
      const focused=axElements.find(e=>e.index===ax.focused_index);
      need(analysis.surface==='FOLDER_CHOOSER'&&focused?.role==='text field'&&focused.subrole==='PathTextField'
        &&canonicalJSON(focus)===canonicalJSON({version:1,frame_id:frameId,session_id:sessionId,
          kind:'HIGH_EDITABLE',focused_index:focused.index,element_identifier:focused.identifier}),
        'CLASSIFIER_FOCUS_EVIDENCE');
    } else fail('CLASSIFIER_FOCUS_UNKNOWN');
    const focusRef=ref(await retain({artifact:focus,kind:'focus-evidence',frameId,sessionId}),
      'CLASSIFIER_FOCUS_RETAIN_REQUIRED');
    let detailIdentity=null;
    const geometry={version:1,frame_id:frameId,session_id:sessionId,surface:analysis.surface,pid:native.pid,
      window_id:native.window_id,layout_key:layoutKey,captured_at:capturedAt,
      cua_capture_bounds_points:native.cua_capture_bounds_points,
      surface_bounds_px:rect(analysis.surface_bounds_px,width,height,'CLASSIFIER_SURFACE_BOUNDS'),
      ax_state:axRef,layout_signature:signature,structure_sha256:structureSHA};
    const geometryRef=ref(await retain({artifact:geometry,kind:'frame-geometry',frameId,sessionId}),
      'CLASSIFIER_GEOMETRY_RETAIN_REQUIRED');
    const support=await frameSupport({frame:capture.screenshot,frameRef:saved,frameId,sessionId,capturedAt,
      surface:analysis.surface,layoutKey,native,geometryRef,width,height});
    need(support?.provider==='SCREEN_CAPTURE_KIT'&&support.surface===analysis.surface&&support.pairFrameId===frameId
      &&support.sessionId===sessionId&&Number.isFinite(support.uncertaintyPx)&&support.uncertaintyPx>=2
      &&Number.isFinite(support.safeMarginPx)&&support.safeMarginPx>=support.uncertaintyPx+4
      &&support.reference&&support.manifestReference,'NON_MENU_SCK_SUPPORT_REQUIRED');
    need(typeof support.readRef==='function','FRAME_SUPPORT_READER_REQUIRED');
    const manifestRaw=await support.readRef(support.manifestReference);
    const manifest=JSON.parse(new TextDecoder().decode(manifestRaw));
    need(manifest.pairFrameId===frameId&&manifest.surface===analysis.surface&&manifest.layoutKey===layoutKey
      &&manifest.geometryEvidence.path===geometryRef.path&&manifest.geometryEvidence.sha256===geometryRef.sha256
      &&manifest.support.path===support.reference.path&&manifest.support.sha256===support.reference.sha256,
      'FRAME_SUPPORT_MANIFEST_CROSS_PAIR');
    const ocrRaw=await support.readRef(manifest.ocr);const ocr=JSON.parse(new TextDecoder().decode(ocrRaw));
    need(ocr.cua_frame_id===frameId&&ocr.sck_frame_sha256===manifest.sckFrameId
      &&Array.isArray(ocr.cua),'FRAME_SUPPORT_OCR_BINDING');
    if(analysis.surface==='ALBUM_DETAIL'&&analysis.detail_identity){
      const d=analysis.detail_identity;
      need(d&&Object.keys(d).sort().join(',')===['detail_window_id','fingerprint','group_key','kind','list_frame_id',
        'list_window_id','native_lineage_ref','photo_count','pid','process_start','title'].sort().join(',')
        &&d.kind==='ALBUM_DETAIL_GRID'&&d.group_key===groupKey&&d.detail_window_id===native.window_id
        &&d.pid===native.pid&&Array.isArray(d.process_start)&&d.process_start.length===2
        &&d.fingerprint?.expected_images>0&&typeof d.title?.text==='string'
        &&typeof d.photo_count?.text==='string'&&d.native_lineage_ref?.sha256,'CLASSIFIER_DETAIL_IDENTITY');
      rect(d.title.bounds,width,height,'CLASSIFIER_DETAIL_TITLE_BOUNDS');
      rect(d.photo_count.bounds,width,height,'CLASSIFIER_DETAIL_COUNT_BOUNDS');
      const parsedTitle=completeDateTitle(d.title.text);
      need(parsedTitle?.start_date===d.fingerprint.start_date&&parsedTitle?.end_date===d.fingerprint.end_date
        &&d.photo_count.text===`${d.fingerprint.expected_images}張照片`,'CLASSIFIER_DETAIL_TEXT_IDENTITY');
      const unique=(items,predicate)=>items.filter(o=>predicate(o)&&o.candidate_count===1&&o.confidence>=.5);
      const sameTitle=o=>completeDateTitle(o.text)?.start_date===d.fingerprint.start_date
        &&completeDateTitle(o.text)?.end_date===d.fingerprint.end_date;
      const exactCua=(items,text,bounds)=>unique(items,o=>o.text===text&&o.bounds.join(',')===bounds.join(','));
      const cuaTitle=exactCua(ocr.cua,d.title.text,d.title.bounds);
      const cuaCount=exactCua(ocr.cua,d.photo_count.text,d.photo_count.bounds);
      const supportRaw=await support.readRef(manifest.support);
      const sidecar=JSON.parse(new TextDecoder().decode(supportRaw));
      const binding=sidecar.native_binding,display=manifest.displayBounds,sckWidth=manifest.imageWidthPx,sckHeight=manifest.imageHeightPx;
      need(Array.isArray(ocr.sck)&&binding&&Array.isArray(binding.cua_capture_bounds_points)
        &&Array.isArray(binding.display_bounds_points)&&Array.isArray(binding.cua_size_px)
        &&Array.isArray(binding.sck_size_px)&&binding.cua_size_px[0]===width&&binding.cua_size_px[1]===height
        &&canonicalJSON(binding.cua_capture_bounds_points)===canonicalJSON(native.cua_capture_bounds_points)
        &&Array.isArray(display)&&display.length===4&&binding.display_bounds_points.join(',')===display.join(',')
        &&binding.sck_size_px[0]===sckWidth&&binding.sck_size_px[1]===sckHeight
        &&Number.isFinite(display[2])&&display[2]>0&&Number.isFinite(display[3])&&display[3]>0
        &&Number.isInteger(sckWidth)&&sckWidth>0&&Number.isInteger(sckHeight)&&sckHeight>0
        &&cuaTitle.length===1&&cuaCount.length===1
        &&!ocr.cua.some(o=>/\(\s*\d+\s*\/\s*\d+\s*\)/.test(o.text)),
        'CLASSIFIER_DETAIL_OCR_BINDING');
      const cb=binding.cua_capture_bounds_points,db=binding.display_bounds_points;
      const scaleX=(cb[2]/width)*(sckWidth/db[2]),scaleY=(cb[3]/height)*(sckHeight/db[3]);
      const offsetX=(cb[0]-db[0])*(sckWidth/db[2]),offsetY=(cb[1]-db[1])*(sckHeight/db[3]);
      const mappedUnique=(items,predicate,cuaItem)=>unique(items,o=>predicate(o)&&Array.isArray(o.bounds)
        &&o.bounds.length===4&&o.bounds.every(Number.isFinite)
        &&Math.hypot(scaleX*(cuaItem.bounds[0]+cuaItem.bounds[2]/2)+offsetX-(o.bounds[0]+o.bounds[2]/2),
          scaleY*(cuaItem.bounds[1]+cuaItem.bounds[3]/2)+offsetY-(o.bounds[1]+o.bounds[3]/2))<=2);
      need(mappedUnique(ocr.sck,sameTitle,cuaTitle[0]).length===1
        &&mappedUnique(ocr.sck,o=>o.text===d.photo_count.text,cuaCount[0]).length===1,
        'CLASSIFIER_DETAIL_OCR_BINDING');
      detailIdentity=d;
    } else need(analysis.detail_identity===null,'CLASSIFIER_DETAIL_IDENTITY_UNEXPECTED');
    const uncertainty=support.uncertaintyPx;
    const byIndex=new Map(axElements.map(e=>[e.index,e]));
    if(scrollWitness){
      need(analysis.surface==='ALBUMS'&&analysis.cards.length===0,'SCROLL_WITNESS_SURFACE');
      const sw=analysis.scroll_witness;
      need(sw&&Object.keys(sw).sort().join(',')==='native_identity,process_instance,rows,scroll_offset,viewport_ax_index,viewport_bounds'
        &&Array.isArray(sw.process_instance)&&JSON.stringify(sw.process_instance)===JSON.stringify([
          native.bundle_id,native.pid,
          sourceBinding?.after?.value?.target?.startTimeSeconds,
          sourceBinding?.after?.value?.target?.startTimeMicroseconds])
        &&Number.isFinite(sw.process_instance[2])&&Number.isFinite(sw.process_instance[3])
        &&sw.native_identity&&Object.keys(sw.native_identity).sort().join(',')==='cua_capture_bounds_points,display_id'
        &&sw.native_identity.display_id===native.display_id
        &&canonicalJSON(sw.native_identity.cua_capture_bounds_points)===canonicalJSON(native.cua_capture_bounds_points),
        'SCROLL_WITNESS_PROCESS_BINDING');
      const viewport=rect(sw.viewport_bounds,width,height,'SCROLL_VIEWPORT_BOUNDS');
      const lists=axElements.filter(e=>e.role==='list');
      need(lists.length===1&&lists[0].index===sw.viewport_ax_index
        &&lists[0].bounds_px.join(',')===viewport.join(','),'SCROLL_VIEWPORT_AX_BINDING');
      const offset=sw.scroll_offset;
      need(offset&&Object.keys(offset).sort().join(',')==='frame_id,session_id,value'
        &&offset.frame_id===frameId&&offset.session_id===sessionId
        &&offset.value===analysis.boundary_evidence.value,'SCROLL_OFFSET_BINDING');
      need(Array.isArray(sw.rows)&&sw.rows.length>0,'SCROLL_LIST_WITNESS_REQUIRED');
      const scrollRows=[],rowSeen=new Set();
      for(const row of sw.rows){
        need(row&&Object.keys(row).sort().join(',')==='fingerprint,fully_visible,identity_visible,metadata_bounds,row_ax_index,row_bounds'
          &&row.identity_visible===true&&typeof row.fully_visible==='boolean','SCROLL_ROW_SCHEMA');
        const id=row.fingerprint;
        need(id&&Object.keys(id).sort().join(',')==='end_date,expected_images,start_date'
          &&/^\d{4}-\d{2}-\d{2}$/.test(id.start_date)&&/^\d{4}-\d{2}-\d{2}$/.test(id.end_date)
          &&Number.isInteger(id.expected_images)&&id.expected_images>0,'SCROLL_ROW_IDENTITY');
        const identity=JSON.stringify([id.start_date,id.end_date,id.expected_images]);
        need(!rowSeen.has(identity),'SCROLL_ROW_DUPLICATE');rowSeen.add(identity);
        nativeRowRect(row.row_bounds,'SCROLL_ROW_BOUNDS');
        need(intersects(row.row_bounds,[0,0,width,height]),'SCROLL_ROW_BOUNDS');
        need(intersects(row.row_bounds,viewport)&&row.fully_visible===inside(row.row_bounds,viewport),
          'SCROLL_ROW_VIEWPORT_BINDING');
        const node=byIndex.get(row.row_ax_index);
        need(node?.role==='row'&&node.parent_index===lists[0].index
          &&node.bounds_px.join(',')===row.row_bounds.join(','),'SCROLL_ROW_AX_BINDING');
        need(Array.isArray(row.metadata_bounds)&&row.metadata_bounds.length===2,
          'SCROLL_ROW_METADATA_BOUNDS');
        for(const b of row.metadata_bounds){rect(b,width,height,'SCROLL_ROW_METADATA_BOUNDS');
          need(inside(b,row.row_bounds)&&inside(b,viewport),'SCROLL_ROW_METADATA_CLIPPED');}
        const matchesIdentity=text=>{const parsed=completeDateTitle(text);
          return parsed?.start_date===id.start_date&&parsed?.end_date===id.end_date;};
        const channelMatches=(items)=>items.filter(item=>matchesIdentity(item.text)&&item.confidence>=.5
          &&item.candidate_count===1&&inside(item.bounds,row.row_bounds)&&inside(item.bounds,viewport));
        const countMatches=(items)=>items.filter(item=>item.text===String(id.expected_images)&&item.confidence>=.5
          &&item.candidate_count===1&&inside(item.bounds,row.row_bounds)&&inside(item.bounds,viewport));
        const uniqueSckText=(items,predicate)=>items.filter(item=>predicate(item.text)&&item.confidence>=.5
          &&item.candidate_count===1);
        need(channelMatches(ocr.cua).length===1&&countMatches(ocr.cua).length===1
          &&uniqueSckText(ocr.sck,matchesIdentity).length===1
          &&uniqueSckText(ocr.sck,text=>text===String(id.expected_images)).length===1,
          'SCROLL_ROW_OCR_CROSS_SOURCE');
        scrollRows.push({fingerprint:id,row_bounds:row.row_bounds,fully_visible:row.fully_visible,
          identity_visible:true,metadata_bounds:row.metadata_bounds,row_ax_index:row.row_ax_index});
      }
      need(scrollRows.length>0,'SCROLL_LIST_WITNESS_REQUIRED');
      const scrollClassifierEvidence={version:1,frame_id:frameId,session_id:sessionId,ax_state_sha256:axRef.sha256,
        screenshot_sha256:frameId,cards:[],detail_identity:null,boundary:{top:boundary.top,bottom:boundary.bottom,evidence:boundaryRef},
        structure_sha256:structureSHA,surface_structure:analysis.surface_structure,focus_evidence:focusRef};
      const scrollClassifierRef=ref(await retain({artifact:scrollClassifierEvidence,kind:'classifier-evidence',frameId,sessionId}),
        'CLASSIFIER_EVIDENCE_RETAIN_REQUIRED');
      const groundingRef=ref(await retain({artifact:{version:1,geometry:geometryRef,manifest:support.manifestReference,
        classifier:scrollClassifierRef},kind:'grounding-evidence',frameId,sessionId}),
        'GROUNDING_EVIDENCE_RETAIN_REQUIRED');
      const processInstance=JSON.stringify(sw.process_instance);
      const observation={frame:saved,frame_id:frameId,session_id:sessionId,group_key:groupKey,surface:'ALBUMS',
        captured_at:capturedAt,provider:'HOSTED_CUA',layout_key:layoutKey,window_id:native.window_id,pid:native.pid,
        process_instance:processInstance,width,height,native_scale:layout.native_scale,
        mapping:{space:'CUA_CAPTURE_PIXELS',uncertainty,evidence:groundingRef,frame_id:frameId,
          layout_key:layoutKey,sck_support:ref(support.reference,'SCK_SUPPORT_REFERENCE')},cards:[],
        viewport_bounds:viewport,scroll_witness:{evidence_only:true,actionable:false,rows:scrollRows,
          native_identity:sw.native_identity},
        parsed_ax:{raw_sha256:sourceAXSha,cards:scrollRows.map(row=>({ ...row.fingerprint,bounds:row.row_bounds})),
          scroll_offset:{frame_id:frameId,session_id:sessionId,value:offset.value}},
        boundary:{top:boundary.top,bottom:boundary.bottom,evidence:boundaryRef},editable_focus:'NONE',occlusion:'CLEAR'};
      scrollCache.set(frameId,{observation,analysis,axSnapshot,axRef,support,geometryRef,groundingRef,manifest,ocr});
      return observation;
    }
    const witnessCards=[];const cards=[];
    need(Array.isArray(analysis.cards),'CLASSIFIER_CARDS');
    const seen=new Set();
    for(const candidate of analysis.cards) {
      const cardKeys=['fingerprint','title','metadata_bounds','card_bounds','fully_visible','safe_metadata_bounds',
        'neighbor_bounds','thumbnail_bounds','card_ax_index','thumbnail_ax_index'];
      need(candidate&&Object.keys(candidate).sort().join(',')===cardKeys.sort().join(','),'CLASSIFIER_CARD_SCHEMA');
      const id=candidate.fingerprint;
      need(id&&Object.keys(id).sort().join(',')==='end_date,expected_images,start_date'
        &&/^\d{4}-\d{2}-\d{2}$/.test(id.start_date)&&/^\d{4}-\d{2}-\d{2}$/.test(id.end_date)
        &&Number.isInteger(id.expected_images)&&id.expected_images>0,'CLASSIFIER_CARD_IDENTITY');
      const identity=JSON.stringify([id.start_date,id.end_date,id.expected_images]);
      need(!seen.has(identity),'CLASSIFIER_CARD_AMBIGUOUS');seen.add(identity);
      const parsedCardTitle=completeDateTitle(candidate.title);
      need(parsedCardTitle?.start_date===id.start_date&&parsedCardTitle?.end_date===id.end_date
        &&typeof candidate.fully_visible==='boolean','CLASSIFIER_CARD_TITLE');
      rect(candidate.card_bounds,width,height,'CLASSIFIER_CARD_BOUNDS');
      rect(candidate.metadata_bounds,width,height,'CLASSIFIER_METADATA_BOUNDS');
      rect(candidate.safe_metadata_bounds,width,height,'CLASSIFIER_SAFE_METADATA_BOUNDS');
      const nameOnlyShape=candidate.thumbnail_bounds===null&&candidate.thumbnail_ax_index===null;
      const nameOnly=nameOnlyShape&&candidate.fully_visible===true&&isNameOnlyTarget(id);
      need(!nameOnlyShape||nameOnly,'CLASSIFIER_NAME_ONLY_WITNESS');
      if(!nameOnly)rect(candidate.thumbnail_bounds,width,height,'CLASSIFIER_THUMBNAIL_BOUNDS');
      need(Array.isArray(candidate.neighbor_bounds),'CLASSIFIER_NEIGHBORS');
      for(const b of candidate.neighbor_bounds)rect(b,width,height,'CLASSIFIER_NEIGHBOR_BOUNDS');
      need(inside(candidate.metadata_bounds,candidate.card_bounds)
        &&(nameOnly||inside(candidate.thumbnail_bounds,candidate.card_bounds))
        &&inside(candidate.safe_metadata_bounds,candidate.metadata_bounds,uncertainty),'CLASSIFIER_CARD_CROSS_PAIR');
      const cardNode=byIndex.get(candidate.card_ax_index),thumbNode=byIndex.get(candidate.thumbnail_ax_index);
      need(cardNode&&(nameOnly?cardNode.role==='row':['row','group','cell'].includes(cardNode.role))
        &&cardNode.bounds_px.join(',')===candidate.card_bounds.join(',')
        &&(nameOnly?thumbNode===undefined:thumbNode?.role==='image'
          &&thumbNode.bounds_px.join(',')===candidate.thumbnail_bounds.join(',')),'CLASSIFIER_AX_CARD_BINDING');
      const titleMatches=ocr.cua.filter(o=>completeDateTitle(o.text)?.start_date===id.start_date
        &&completeDateTitle(o.text)?.end_date===id.end_date&&o.candidate_count===1&&o.confidence>=0.5
        &&inside(o.bounds,candidate.metadata_bounds));
      const countMatches=ocr.cua.filter(o=>new RegExp(`(?<![0-9])${id.expected_images}(?![0-9])`).test(o.text)
        &&o.candidate_count===1&&o.confidence>=0.5&&inside(o.bounds,candidate.metadata_bounds));
      need(titleMatches.length===1&&countMatches.length===1&&titleMatches[0]!==countMatches[0],
        'CLASSIFIER_OCR_CARD_BINDING');
      need(!(nameOnly&&axElements.some(el=>el.role==='button'&&el.enabled
        &&intersects(el.bounds_px,titleMatches[0].bounds))),'CLASSIFIER_NAME_ONLY_TITLE_OCCLUDED');
      const titleOcr={text:titleMatches[0].text,bounds:titleMatches[0].bounds};
      const countOcr={text:countMatches[0].text,bounds:countMatches[0].bounds};
      for(const item of [titleOcr,countOcr])rect(item.bounds,width,height,'CLASSIFIER_OCR_BOUNDS');
      cards.push({fingerprint:id,title:candidate.title,metadata_bounds:candidate.metadata_bounds,
        card_bounds:candidate.card_bounds,fully_visible:candidate.fully_visible,
        safe_metadata_bounds:candidate.safe_metadata_bounds,neighbor_bounds:candidate.neighbor_bounds});
      witnessCards.push({fingerprint:id,title:candidate.title,card_bounds:candidate.card_bounds,
        metadata_bounds:candidate.metadata_bounds,safe_metadata_bounds:candidate.safe_metadata_bounds,
        neighbor_bounds:candidate.neighbor_bounds,thumbnail_bounds:candidate.thumbnail_bounds,
        title_ocr:titleOcr,count_ocr:countOcr,card_ax_index:candidate.card_ax_index,
        thumbnail_ax_index:candidate.thumbnail_ax_index});
    }
    const classifierEvidence={version:1,frame_id:frameId,session_id:sessionId,ax_state_sha256:axRef.sha256,
      screenshot_sha256:frameId,cards:witnessCards,detail_identity:detailIdentity,boundary:{top:boundary.top,bottom:boundary.bottom,evidence:boundaryRef},
      structure_sha256:structureSHA,surface_structure:analysis.surface_structure,focus_evidence:focusRef};
    const classifierRef=ref(await retain({artifact:classifierEvidence,kind:'classifier-evidence',frameId,sessionId}),
      'CLASSIFIER_EVIDENCE_RETAIN_REQUIRED');
    const grounding={version:1,geometry:geometryRef,manifest:support.manifestReference,classifier:classifierRef};
    const groundingRef=ref(await retain({artifact:grounding,kind:'grounding-evidence',frameId,sessionId}),
      'GROUNDING_EVIDENCE_RETAIN_REQUIRED');
    const observation={frame:saved,frame_id:frameId,session_id:sessionId,group_key:groupKey,surface:analysis.surface,
      captured_at:capturedAt,provider:'HOSTED_CUA',layout_key:layoutKey,window_id:native.window_id,pid:native.pid,
      width,height,mapping:{space:'CUA_CAPTURE_PIXELS',uncertainty,evidence:groundingRef,frame_id:frameId,
        layout_key:layoutKey,sck_support:ref(support.reference,'SCK_SUPPORT_REFERENCE')},cards,
      boundary:{top:boundary.top,bottom:boundary.bottom,evidence:boundaryRef},
      editable_focus:analysis.editable_focus,occlusion:analysis.occlusion};
    if(detailIdentity)observation.detail_identity=detailIdentity;
    const strictKeys=detailIdentity?[...observationKeys,'detail_identity']:observationKeys;
    need(Object.keys(observation).sort().join(',')===strictKeys.slice().sort().join(','),
      'STRICT_FRAME_SHAPE');
    cache.set(frameId,{observation,analysis,axSnapshot,axRef,support,geometryRef,groundingRef,manifest,ocr});
    return observation;
  }

  async function classifyChooser({phase,dispatch,previous,frameId,sessionId}) {
    const captured=cache.get(frameId);
    const allowedSurface=phase==='CONFIRM_ATTEMPTED'
      ?['FOLDER_CHOOSER','ALBUM_DETAIL'].includes(captured?.observation?.surface)
      :captured?.observation?.surface==='FOLDER_CHOOSER';
    need(captured&&captured.observation.session_id===sessionId&&allowedSurface,
      'CHOOSER_FRAME_NOT_GROUNDED');
    const frame=captured.observation;const ax=captured.axSnapshot;const byIndex=new Map(ax.elements.map(e=>[e.index,e]));
    const origin=dispatch?.original_context;
    need(dispatch&&Object.keys(dispatch).sort().join(',')===['action_id','destination','original_context',
      'original_frame_id','owner','run_id','session_id'].sort().join(',')
      &&dispatch.session_id===sessionId&&dispatch.original_frame_id===origin?.frame_id
      &&origin&&Object.keys(origin).sort().join(',')==='frame_id,layout_key,pid,window_id'
      &&origin.pid===frame.pid&&Number.isInteger(origin.window_id)&&typeof origin.layout_key==='string'
      &&origin.layout_key.length>0,'CHOOSER_ORIGIN_CONTEXT');
    let control;
    if(phase==='APPEARED') {
      const rootIndex=captured.analysis.chooser_controls?.root_index;const root=byIndex.get(rootIndex);
      need(root&&['window','sheet','dialog'].includes(root.role),'CHOOSER_ROOT_UNKNOWN');
      control={chooser_index:root.index,chooser_identifier:root.identifier};
    } else if(phase==='GO_TO_FOLDER'||phase==='PATH_FILLED') {
      const index=captured.analysis.chooser_controls?.path_field_index;const field=byIndex.get(index);
      need(field&&field.role==='text field'&&field.subrole==='PathTextField'&&field.enabled===true
        &&ax.focused_index===field.index,
        'PATH_FIELD_UNKNOWN');
      control={path_field_index:field.index,path_field_role:field.role,path_field_subrole:field.subrole,
        path_field_identifier:field.identifier,path_field_bounds_px:field.bounds_px,path_field_enabled:true,focused:true};
      if(phase==='PATH_FILLED') {
        need(field.value===dispatch.destination,'CHOOSER_PATH_VALUE');control.value=field.value;
      }
    } else if(phase==='DESTINATION_SELECTED') {
      const chooser=captured.analysis.chooser_controls;
      const field=byIndex.get(chooser?.path_field_index),button=byIndex.get(chooser?.confirm_button_index);
      need(field&&field.role==='text field'&&field.subrole==='PathTextField'&&field.enabled===true
        &&field.value===dispatch.destination
        &&button&&button.role==='button'&&button.enabled===true,'CHOOSER_DESTINATION_CONTROL');
      const confirmPoint=[Math.trunc(button.bounds_px[0]+button.bounds_px[2]/2),
        Math.trunc(button.bounds_px[1]+button.bounds_px[3]/2)];
      const leaf=dispatch.destination.split('/').at(-1);
      const leafIndex=chooser.selected_leaf_index;const leafElement=byIndex.get(leafIndex);
      need(leafElement&&['text','static text','button'].includes(leafElement.role)
        &&[leafElement.label,leafElement.value].includes(leaf),'CHOOSER_LEAF_NOT_OBSERVED');
      const leafOCR=captured.ocr.cua.filter(item=>item.text===leaf&&item.candidate_count===1&&item.confidence>=0.5
        &&inside(item.bounds,leafElement.bounds_px));
      need(leafOCR.length===1&&inside(button.bounds_px,captured.support.intersectionPx,frame.mapping.uncertainty),
        'CHOOSER_CONFIRM_UNSAFE');
      control={path_field_index:field.index,path_field_identifier:field.identifier,path_field_role:field.role,
        path_field_subrole:field.subrole,value:field.value,selected_leaf:leaf,selected_leaf_index:leafElement.index,
        selected_leaf_identifier:leafElement.identifier,selected_leaf_bounds_px:leafElement.bounds_px,
        selected_leaf_ocr:{text:leafOCR[0].text,bounds:leafOCR[0].bounds},
        confirm_index:button.index,confirm_role:button.role,confirm_identifier:button.identifier,
        confirm_bounds_px:button.bounds_px,confirm_enabled:true,confirm_point:confirmPoint};
    } else if(phase==='CONFIRM_ATTEMPTED') {
      need(previous?.phase==='DESTINATION_SELECTED','CHOOSER_CONFIRM_PHASE');
      control={confirmation_frame_id:previous.frame.frame_id,attempted:true,invocation_count:1};
    } else fail('CHOOSER_PHASE_UNKNOWN');
    return {version:1,phase,frame,ax_state:captured.axRef,sck_support:captured.observation.mapping.sck_support,
      dispatch,control};
  }

  // A separate collector, never a normal observation and never inserted into cache.
  async function collectVisualCardDiagnostic({capture,saved,frameId,sessionId,capturedAt,sourceBinding,capturedContext}) {
    const diagnosticId=hex64(frameId)?frameId:sha256Hex(encoder.encode(JSON.stringify({sessionId,capturedAt})));
    try {
      need(typeof analyzeVisualCardDiagnostic==='function','VISUAL_DIAGNOSTIC_ANALYZER_REQUIRED');
      need(capture?.screenshot instanceof Uint8Array&&typeof capture.state==='string','CLASSIFIER_CAPTURE_REQUIRED');
      need(hex64(frameId)&&sha256Hex(capture.screenshot)===frameId&&saved?.sha256===frameId
        &&saved.bytes===capture.screenshot.byteLength,'CLASSIFIER_FRAME_HASH');
      const frameRef=ref(saved,'VISUAL_DIAGNOSTIC_FRAME_REFERENCE');
      need(typeof capturedAt==='string'&&Number.isFinite(Date.parse(capturedAt)),'CLASSIFIER_CAPTURE_TIME');
      const [width,height]=imageSize(capture.screenshot);
      const sourceAX=encoder.encode(capture.state),sourceAXSha=sha256Hex(sourceAX);
      const sourceAXRef=ref(saved.ax,'CLASSIFIER_AX_RETENTION');
      need(sourceAXRef.bytes===sourceAX.byteLength&&sourceAXRef.sha256===sourceAXSha,'CLASSIFIER_AX_RETENTION');
      const analysis=await analyzeVisualCardDiagnostic({screenshot:capture.screenshot,axText:capture.state,
        frameId,sessionId,capturedAt,width,height,sourceAXSha256:sourceAXSha,sourceBinding,capturedContext,saved});
      const keys=['kind','evidence_only','actionable','version','frame_id','session_id','source_sha256',
        'source_ax_sha256','surface','group_key','native','layout','surface_structure','surface_bounds_px',
        'occlusion','ax','raw_ocr','reference'];
      need(analysis&&Object.keys(analysis).sort().join(',')===keys.sort().join(',')
        &&analysis.kind==='VISUAL_CARD_DIAGNOSTIC'&&analysis.evidence_only===true&&analysis.actionable===false
        &&analysis.version===1&&analysis.frame_id===frameId&&analysis.session_id===sessionId
        &&analysis.source_sha256===frameId&&analysis.source_ax_sha256===sourceAXSha&&analysis.group_key===groupKey
        &&analysis.surface==='ALBUMS'&&analysis.occlusion==='CLEAR','VISUAL_DIAGNOSTIC_SCHEMA');
      const analysisRef=ref(analysis.reference,'VISUAL_DIAGNOSTIC_ANALYSIS_REFERENCE');
      const native=analysis.native,layout=analysis.layout;
      need(native?.bundle_id==='jp.naver.line.mac'&&Number.isInteger(native.pid)&&native.pid>0
        &&Number.isInteger(native.window_id)&&native.window_id>0&&Number.isInteger(native.display_id)&&native.display_id>0
        &&Array.isArray(native.cua_capture_bounds_points)&&native.cua_capture_bounds_points.length===4
        &&native.cua_capture_bounds_points.every(Number.isFinite),'CLASSIFIER_NATIVE_IDENTITY');
      need(layout&&['line_version','language','window_class'].every(k=>typeof layout[k]==='string'&&layout[k])
        &&Number.isFinite(layout.native_scale)&&layout.native_scale>0,'CLASSIFIER_LAYOUT');
      need(analysis.ax?.version===1&&Array.isArray(analysis.ax.elements)
        &&Array.isArray(analysis.surface_structure)&&Array.isArray(analysis.raw_ocr),'VISUAL_DIAGNOSTIC_EVIDENCE');
      const structureSHA=shaJson(analysis.surface_structure);
      const signature={line_version:layout.line_version,language:layout.language,window_class:layout.window_class,
        frame_width_px:width,frame_height_px:height,native_scale:layout.native_scale,structure_sha256:structureSHA};
      const layoutKey=shaJson(signature);
      const axSnapshot={version:1,frame_id:frameId,session_id:sessionId,pid:native.pid,
        window_id:native.window_id,surface:analysis.surface,...analysis.ax};
      const axRef=ref(await retain({artifact:axSnapshot,kind:'visual-card-diagnostic-ax',frameId,sessionId}),
        'VISUAL_DIAGNOSTIC_AX_RETAIN_REQUIRED');
      const geometry={version:1,frame_id:frameId,session_id:sessionId,surface:analysis.surface,pid:native.pid,
        window_id:native.window_id,layout_key:layoutKey,captured_at:capturedAt,
        cua_capture_bounds_points:native.cua_capture_bounds_points,
        surface_bounds_px:rect(analysis.surface_bounds_px,width,height,'CLASSIFIER_SURFACE_BOUNDS'),
        ax_state:axRef,layout_signature:signature,structure_sha256:structureSHA};
      const geometryRef=ref(await retain({artifact:geometry,kind:'visual-card-diagnostic-geometry',frameId,sessionId}),
        'VISUAL_DIAGNOSTIC_GEOMETRY_RETAIN_REQUIRED');
      const support=await frameSupport({frame:capture.screenshot,frameRef,frameId,sessionId,capturedAt,
        surface:analysis.surface,layoutKey,native,geometryRef,width,height});
      need(support?.provider==='SCREEN_CAPTURE_KIT'&&support.surface===analysis.surface
        &&support.pairFrameId===frameId&&support.sessionId===sessionId
        &&Number.isFinite(support.uncertaintyPx)&&support.uncertaintyPx>=2
        &&Number.isFinite(support.safeMarginPx)&&support.safeMarginPx>=support.uncertaintyPx+4
        &&typeof support.readRef==='function','NON_MENU_SCK_SUPPORT_REQUIRED');
      const readVerified=async reference=>{
        ref(reference,'VISUAL_DIAGNOSTIC_SUPPORT_REFERENCE');
        const raw=await support.readRef(reference);
        need(raw.byteLength===reference.bytes&&sha256Hex(raw)===reference.sha256,'SCK_ARTIFACT_DRIFT');return raw;
      };
      await readVerified(support.reference);
      const manifest=JSON.parse(new TextDecoder().decode(await readVerified(support.manifestReference)));
      need(manifest.pairFrameId===frameId&&manifest.surface===analysis.surface&&manifest.layoutKey===layoutKey
        &&manifest.geometryEvidence?.path===geometryRef.path&&manifest.geometryEvidence.sha256===geometryRef.sha256
        &&manifest.support?.path===support.reference.path&&manifest.support.sha256===support.reference.sha256
        &&manifest.sckFrame?.sha256===manifest.sckFrameId,'FRAME_SUPPORT_MANIFEST_CROSS_PAIR');
      const sckRaw=await readVerified(manifest.sckFrame),ocrRaw=await readVerified(manifest.ocr);
      need([137,80,78,71,13,10,26,10].every((n,i)=>sckRaw[i]===n),'VISUAL_DIAGNOSTIC_SCK_PNG_REQUIRED');
      const sckOcr=JSON.parse(new TextDecoder().decode(ocrRaw));
      need(sckOcr.cua_frame_id===frameId&&sckOcr.sck_frame_sha256===manifest.sckFrameId
        &&Array.isArray(sckOcr.cua)&&Array.isArray(sckOcr.sck),'FRAME_SUPPORT_OCR_BINDING');
      const packet={kind:'VISUAL_CARD_DIAGNOSTIC',evidence_only:true,actionable:false,version:1,
        frame_id:frameId,session_id:sessionId,captured_at:capturedAt,group_key:groupKey,surface:analysis.surface,
        layout_key:layoutKey,cua_frame:frameRef,cua_ax:sourceAXRef,
        native_before:ref(sourceBinding?.before?.reference,'VISUAL_DIAGNOSTIC_NATIVE_REFERENCE'),
        native_after:ref(sourceBinding?.after?.reference,'VISUAL_DIAGNOSTIC_NATIVE_REFERENCE'),
        analysis:analysisRef,geometry:geometryRef,sck_frame:manifest.sckFrame,sck_ocr:manifest.ocr,
        support:support.reference,manifest:support.manifestReference};
      const packetRef=ref(await retain({artifact:packet,kind:'visual-card-diagnostic',frameId,sessionId}),
        'VISUAL_DIAGNOSTIC_RETAIN_REQUIRED');
      return {kind:packet.kind,evidence_only:true,actionable:false,frame_id:frameId,session_id:sessionId,reference:packetRef};
    } catch(error) {
      const failure={kind:'VISUAL_CARD_DIAGNOSTIC_FAILURE',frame_id:diagnosticId,session_id:sessionId,
        frame:saved??null,source_before:sourceBinding?.before?.reference??null,
        source_after:sourceBinding?.after?.reference??null,error:{code:error.code??null,message:String(error.message??error)}};
      try{await retain({artifact:failure,kind:'visual-card-diagnostic-failure',frameId:diagnosticId,sessionId});}
      catch(retentionError){error.diagnosticRetentionError=String(retentionError.message??retentionError);}
      throw error;
    }
  }

  async function completeVisualCardDiagnostic({capture,saved,frameId,sessionId,capturedAt,sourceBinding,pairEvidence,analyzePixels,
      requestStartMonotonicNanoseconds}) {
    const pair=pairEvidence?.pair;
    need(pair&&pair.kind==='VISUAL_CARD_DIAGNOSTIC'&&pair.sessionID===sessionId
      &&pair.cuaFrameID===frameId&&pair.cuaFrame?.sha256===frameId&&pair.sckFrame?.sha256===pair.sckFrameID,
      'VISUAL_DIAGNOSTIC_PAIR_REQUIRED');
    const before=sourceBinding?.before?.value,after=sourceBinding?.after?.value;
    need(before?.schemaVersion===1&&before.complete===true&&before.truncated===false
      &&after?.schemaVersion===1&&after.complete===true&&after.truncated===false,
      'VISUAL_DIAGNOSTIC_NATIVE_CONTEXT_REQUIRED');
    const processKey=v=>JSON.stringify([v.target?.bundleID,v.target?.pid,v.target?.startTimeSeconds,
      v.target?.startTimeMicroseconds]);
    need(processKey(before)===processKey(after)&&pair.bundleID===after.target.bundleID
      &&pair.pid===after.target.pid&&pair.processStartTimeSeconds===after.target.startTimeSeconds
      &&pair.processStartTimeMicroseconds===after.target.startTimeMicroseconds,
      'VISUAL_DIAGNOSTIC_PROCESS_INSTANCE_DRIFT');
    const beforeWindows=(before.windows??[]).filter(w=>w.windowNumber===pair.windowID);
    const afterWindows=(after.windows??[]).filter(w=>w.windowNumber===pair.windowID);
    const afterDisplays=(after.displays??[]).filter(d=>d.displayID===pair.displayID);
    const rectValues=r=>r&&[r.x,r.y,r.width,r.height];
    const sameRect=(a,b,tolerance=1)=>Array.isArray(a)&&Array.isArray(b)&&a.length===4&&b.length===4
      &&a.every((v,i)=>Number.isFinite(v)&&Number.isFinite(b[i])&&Math.abs(v-b[i])<=tolerance);
    need(before.focusedWindowID===pair.windowID&&after.focusedWindowID===pair.windowID
      &&beforeWindows.length===1&&afterWindows.length===1&&afterDisplays.length===1
      &&sameRect(rectValues(beforeWindows[0].framePt),pair.sckWindowBoundsPoints)
      &&sameRect(rectValues(afterWindows[0].framePt),pair.sckWindowBoundsPoints)
      &&sameRect(rectValues(afterDisplays[0].boundsPt),pair.displayBoundsPoints)
      &&Array.isArray(afterWindows[0].displayIDs)&&afterWindows[0].displayIDs.includes(pair.displayID),
      'VISUAL_DIAGNOSTIC_NATIVE_GEOMETRY_DRIFT');
    const [width,height]=imageSize(capture.screenshot);
    const sourceAX=encoder.encode(capture.state),sourceAXSha=sha256Hex(sourceAX);
    need(saved?.sha256===frameId&&sha256Hex(capture.screenshot)===frameId
      &&saved.ax?.sha256===sourceAXSha&&saved.ax.bytes===sourceAX.byteLength,
      'VISUAL_DIAGNOSTIC_RETAINED_CUA_INVALID');
    const nativeAnalysis=await analyzeVisualCardDiagnostic({screenshot:capture.screenshot,axText:capture.state,
      frameId,sessionId,capturedAt,width,height,sourceAXSha256:sourceAXSha,sourceBinding,capturedContext:sourceBinding,saved});
    need(nativeAnalysis?.kind==='VISUAL_CARD_DIAGNOSTIC'&&nativeAnalysis.evidence_only===true
      &&nativeAnalysis.actionable===false&&nativeAnalysis.frame_id===frameId&&nativeAnalysis.session_id===sessionId
      &&nativeAnalysis.native?.pid===pair.pid&&nativeAnalysis.native?.window_id===pair.windowID
      &&nativeAnalysis.native?.display_id===pair.displayID
      &&sameRect(nativeAnalysis.native?.cua_capture_bounds_points,pair.cuaBoundsPoints),
      'VISUAL_DIAGNOSTIC_NATIVE_ANALYSIS_BINDING');
    need(typeof analyzePixels==='function','VISUAL_DIAGNOSTIC_PIXEL_ANALYZER_REQUIRED');
    const pixel=await analyzePixels({pairEvidence,frameId,sessionId});
    need(typeof pairEvidence.readRef==='function','VISUAL_DIAGNOSTIC_READER_REQUIRED');
    for(const reference of [pairEvidence.reference,pair.cuaFrame,pair.sckFrame,saved.ax,sourceBinding.before.reference,
      sourceBinding.after.reference,nativeAnalysis.reference,pixel.reference]) {
      const bytes=await pairEvidence.readRef(reference);
      need(bytes?.byteLength===reference.bytes,'VISUAL_DIAGNOSTIC_PROVENANCE_REFERENCE');
    }
    const analysisStatus='INSUFFICIENT';
    const completedAt=new Date().toISOString();
    const completedMonoMs=performance.now();
    const completedScaledNs=completedMonoMs*1_000_000;
    need(Number.isFinite(completedMonoMs)&&completedMonoMs>=0&&Number.isFinite(completedScaledNs)
      &&completedScaledNs<=Number.MAX_SAFE_INTEGER-2,'VISUAL_DIAGNOSTIC_CLOCK_RANGE');
    const completedLower=BigInt(Math.max(0,Math.floor(completedScaledNs)-2));
    const completedUpper=BigInt(Math.ceil(completedScaledNs)+2);
    const processingStart=BigInt(requestStartMonotonicNanoseconds);
    need(typeof pair.cuaRequestEndMonotonicNanoseconds==='string'
      &&/^(0|[1-9][0-9]*)$/.test(pair.cuaRequestEndMonotonicNanoseconds),
    'VISUAL_DIAGNOSTIC_PROCESSING_CLOCK');
    const processingEnd=BigInt(pair.cuaRequestEndMonotonicNanoseconds);
    const processingDuration=completedUpper-processingStart;
    need(completedLower>=processingStart&&completedLower>=processingEnd&&processingDuration>=0n,
      'VISUAL_DIAGNOSTIC_PROCESSING_CLOCK');
    const packet={version:1,kind:'VISUAL_CARD_DIAGNOSTIC',evidence_only:true,actionable:false,
      CAPTURE_STATUS:'CAPTURED',ANALYSIS_STATUS:analysisStatus,ACTION_ELIGIBILITY:'INELIGIBLE',
      ACQUISITION_RELATIONSHIP:'INSUFFICIENT',
      session_id:sessionId,frame_id:frameId,captured_at:capturedAt,
      cua_request_started_at:pair.cuaRequestStartedAt,cua_request_ended_at:pair.cuaRequestEndedAt,
      cua_request_start_monotonic_nanoseconds:pair.cuaRequestStartMonotonicNanoseconds,
      cua_request_end_monotonic_nanoseconds:pair.cuaRequestEndMonotonicNanoseconds,
      sck_request_started_at:pair.sckRequestStartedAt,sck_request_ended_at:pair.sckRequestEndedAt,
      sck_request_start_monotonic_nanoseconds:pair.sckRequestStartMonotonicNanoseconds,
      sck_request_end_monotonic_nanoseconds:pair.sckRequestEndMonotonicNanoseconds,
      processing_completed_at:completedAt,processing_duration_nanoseconds:processingDuration.toString(),
      cua_frame:pair.cuaFrame,sck_frame:pair.sckFrame,capture_pair_receipt:pairEvidence.reference,
      native_before:ref(sourceBinding.before.reference,'VISUAL_DIAGNOSTIC_NATIVE_BEFORE_REF'),
      native_after:ref(sourceBinding.after.reference,'VISUAL_DIAGNOSTIC_NATIVE_AFTER_REF'),
      native_analysis:ref(nativeAnalysis.reference,'VISUAL_DIAGNOSTIC_NATIVE_ANALYSIS_REF'),
      pixel_analysis:ref(pixel.reference,'VISUAL_DIAGNOSTIC_PIXEL_ANALYSIS_REF'),
      analysis_reason:pixel.analysis.reason??null,
      pixel_alignment_status:pixel.analysis.status,
      visual_card_status:'INSUFFICIENT_NO_COMPLETE_CARD_WITNESS',
      acquisition_relationship_reason:'Pixel anchor alignment and matching Native AFTER geometry do not establish full screen continuity or a complete card/thumbnail/control witness.',
      geometry_time_semantics:'SCK capture record is capture-time provenance; Native AFTER AX is later context and is only a consistency check.'};
    const reference=ref(await retain({artifact:packet,kind:'visual-card-diagnostic-completion',frameId,sessionId}),
      'VISUAL_DIAGNOSTIC_COMPLETION_RETAIN_REQUIRED');
    return {kind:packet.kind,evidence_only:true,actionable:false,CAPTURE_STATUS:packet.CAPTURE_STATUS,
      ANALYSIS_STATUS:packet.ANALYSIS_STATUS,ACTION_ELIGIBILITY:packet.ACTION_ELIGIBILITY,
      ACQUISITION_RELATIONSHIP:packet.ACQUISITION_RELATIONSHIP,
      frame_id:frameId,session_id:sessionId,reference};
  }

  // Purpose-selected menu envelope: evidence-only, never an ordinary observation and never cache.
  // The hosted CUA crop is the input target, but the LINE popup is a separate raised window that
  // may lie partly outside that crop, so the Save All row is taken from the fresh full-display
  // SCK OCR of this same menu-open frame (frame-support), never from the hosted CUA crop OCR.
  async function collectMenuEnvelope({capture,saved,frameId,sessionId,capturedAt,sourceBinding,capturedContext}) {
    need(typeof analyzeMenuFrame==='function'&&typeof buildMenuEnvelope==='function','MENU_ENVELOPE_ANALYZER_REQUIRED');
    need(capture?.screenshot instanceof Uint8Array&&typeof capture.state==='string','CLASSIFIER_CAPTURE_REQUIRED');
    need(hex64(frameId)&&sha256Hex(capture.screenshot)===frameId&&saved?.sha256===frameId
      &&saved.bytes===capture.screenshot.byteLength,'CLASSIFIER_FRAME_HASH');
    need(typeof capturedAt==='string'&&Number.isFinite(Date.parse(capturedAt)),'CLASSIFIER_CAPTURE_TIME');
    const [width,height]=imageSize(capture.screenshot);
    const sourceAX=encoder.encode(capture.state),sourceAXSha=sha256Hex(sourceAX);
    need(saved.ax&&saved.ax.bytes===sourceAX.byteLength&&saved.ax.sha256===sourceAXSha,'CLASSIFIER_AX_RETAINED');
    const frameRef=ref(saved,'MENU_ENVELOPE_FRAME_REFERENCE');
    const facts=await analyzeMenuFrame({screenshot:capture.screenshot,axText:capture.state,frameId,sessionId,
      capturedAt,width,height,sourceAXSha256:sourceAXSha,sourceBinding,capturedContext,saved});
    need(facts?.kind==='MENU_FRAME_FACTS'&&facts.version===1&&facts.evidence_only===true
      &&facts.admissible_to_ordinary_classifier===false&&facts.frame_id===frameId&&facts.session_id===sessionId
      &&facts.source_sha256===frameId&&facts.source_ax_sha256===sourceAXSha,'MENU_ENVELOPE_FACTS');
    const native=facts.native,popup=facts.popup,layout=facts.layout;
    need(native?.bundle_id==='jp.naver.line.mac'&&Number.isInteger(native.pid)&&native.pid>0
      &&Number.isInteger(native.window_id)&&native.window_id>0&&Number.isInteger(native.display_id)
      &&native.display_id>0&&Array.isArray(native.cua_capture_bounds_points)
      &&native.cua_capture_bounds_points.length===4&&native.cua_capture_bounds_points.every(Number.isFinite),
      'MENU_ENVELOPE_NATIVE_IDENTITY');
    need(popup&&Number.isInteger(popup.window_number)&&popup.window_number>0&&popup.window_number!==native.window_id
      &&Number.isInteger(popup.layer)&&popup.layer>0&&popup.above_window_id===native.window_id
      &&Array.isArray(popup.bounds_px)&&popup.bounds_px.length===4&&popup.bounds_px.every(Number.isFinite)
      &&popup.bounds_px[2]>0&&popup.bounds_px[3]>0&&Array.isArray(popup.bounds_pt)
      &&popup.bounds_pt.length===4&&popup.bounds_pt.every(Number.isFinite),'MENU_ENVELOPE_POPUP');
    need(layout&&['line_version','language','window_class'].every(key=>typeof layout[key]==='string'&&layout[key])
      &&Number.isFinite(layout.native_scale)&&layout.native_scale>0,'MENU_ENVELOPE_LAYOUT');
    need(Array.isArray(facts.surface_structure)&&facts.surface_structure.length>0
      &&facts.surface_structure.every(item=>item&&typeof item.role==='string'&&typeof item.subrole==='string'
        &&typeof item.identifier==='string'),'MENU_ENVELOPE_STRUCTURE');
    // Same-capture geometry evidence: the only layout signature this frame can prove. It is
    // deliberately the menu frame's own signature, not the ordinary detail observation's key.
    const signature={line_version:layout.line_version,language:layout.language,window_class:layout.window_class,
      frame_width_px:width,frame_height_px:height,native_scale:layout.native_scale,
      structure_sha256:shaJson(facts.surface_structure)};
    const layoutKey=shaJson(signature);
    const geometry={version:1,frame_id:frameId,session_id:sessionId,surface:'ALBUM_DETAIL',pid:native.pid,
      window_id:native.window_id,layout_key:layoutKey,captured_at:capturedAt,
      cua_capture_bounds_points:native.cua_capture_bounds_points,surface_bounds_px:[0,0,width,height],
      ax_state:ref(saved.ax,'MENU_ENVELOPE_AX_REFERENCE'),layout_signature:signature,
      structure_sha256:signature.structure_sha256};
    const geometryRef=ref(await retain({artifact:geometry,kind:'menu-frame-geometry',frameId,sessionId}),
      'MENU_ENVELOPE_GEOMETRY_RETAIN_REQUIRED');
    const support=await frameSupport({frame:capture.screenshot,frameRef:saved,frameId,sessionId,capturedAt,
      surface:'ALBUM_DETAIL',layoutKey,native,geometryRef,width,height});
    need(support?.provider==='SCREEN_CAPTURE_KIT'&&support.surface==='ALBUM_DETAIL'&&support.pairFrameId===frameId
      &&support.sessionId===sessionId&&support.reference&&support.manifestReference
      &&Number.isFinite(support.uncertaintyPx)&&support.uncertaintyPx>=2
      &&Number.isFinite(support.safeMarginPx)&&support.safeMarginPx>=support.uncertaintyPx+4,
      'MENU_ENVELOPE_SUPPORT_REQUIRED');
    need(typeof support.readRef==='function','MENU_ENVELOPE_SUPPORT_READER_REQUIRED');
    const manifestRaw=await support.readRef(support.manifestReference);
    const manifest=JSON.parse(new TextDecoder().decode(manifestRaw));
    need(manifest.pairFrameId===frameId&&manifest.surface==='ALBUM_DETAIL'&&manifest.layoutKey===layoutKey
      &&manifest.geometryEvidence.path===geometryRef.path&&manifest.geometryEvidence.sha256===geometryRef.sha256
      &&manifest.support?.path===support.reference.path&&manifest.support?.sha256===support.reference.sha256
      &&manifest.ocr&&manifest.sckFrame,'MENU_ENVELOPE_SUPPORT_MANIFEST');
    const ocrRaw=await support.readRef(manifest.ocr);
    const ocr=JSON.parse(new TextDecoder().decode(ocrRaw));
    need(ocr.cua_frame_id===frameId&&ocr.sck_frame_sha256===manifest.sckFrameId
      &&Array.isArray(ocr.cua)&&Array.isArray(ocr.sck),'MENU_ENVELOPE_OCR_BINDING');
    const inner=buildMenuEnvelope({menuFrame:facts,sckRows:ocr.sck,cuaRows:ocr.cua,width,height});
    const reference=ref(await retain({artifact:{sourceBinding,menuEnvelope:inner},
      kind:'menu-calibration-envelope',frameId,sessionId}),'MENU_ENVELOPE_RETAIN_REQUIRED');
    const retainedBytes=await readBack(reference);
    need(retainedBytes instanceof Uint8Array&&retainedBytes.byteLength===reference.bytes
      &&sha256Hex(retainedBytes)===reference.sha256,'MENU_ENVELOPE_ARTIFACT_DRIFT');
    menuEnvelopes.set(frameId,{envelope:inner,reference,frameRef,layoutKey});
    return {kind:'MENU_CALIBRATION_ENVELOPE',evidence_only:true,admissible_to_ordinary_classifier:false,
      frame_id:frameId,session_id:sessionId,captured_at:capturedAt,popup_window_id:popup.window_number,
      layer:popup.layer,save_all:inner.save_all.text,safe_bounds_px:inner.safe_bounds_px,
      eroded_bounds_px:inner.eroded_bounds_px,uncertainty_px:inner.uncertainty_px,reference};
  }

  return Object.freeze({classify,classifyScrollWitness:args=>classify(args,{scrollWitness:true}),classifyChooser,
    collectVisualCardDiagnostic,completeVisualCardDiagnostic,cache,scrollCache,menuEnvelopes});
}
