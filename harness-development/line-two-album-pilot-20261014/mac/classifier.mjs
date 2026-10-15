import {createHash} from 'node:crypto';
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
const inside=(a,b,margin=0)=>a[0]>=b[0]+margin&&a[1]>=b[1]+margin
  &&a[0]+a[2]<=b[0]+b[2]-margin&&a[1]+a[3]<=b[1]+b[3]-margin;

const observationKeys=['frame','frame_id','session_id','group_key','surface','captured_at','provider','layout_key',
  'window_id','pid','width','height','mapping','cards','boundary','editable_focus','occlusion'];

export function createLiveClassifier({retain,frameSupport,analyzeCapture,groupKey,clock=()=>Date.now()}) {
  need(typeof retain==='function'&&typeof frameSupport==='function'&&typeof analyzeCapture==='function','CLASSIFIER_DEPENDENCY_REQUIRED');
  need(typeof groupKey==='string'&&groupKey,'CLASSIFIER_GROUP_REQUIRED');
  const cache=new Map();

  async function classify({capture,saved,frameId,sessionId,capturedAt,sourceBinding,capturedContext}) {
    need(capture?.screenshot instanceof Uint8Array&&typeof capture.state==='string','CLASSIFIER_CAPTURE_REQUIRED');
    need(hex64(frameId)&&sha256Hex(capture.screenshot)===frameId&&saved?.sha256===frameId,'CLASSIFIER_FRAME_HASH');
    need(typeof capturedAt==='string'&&Number.isFinite(Date.parse(capturedAt)),'CLASSIFIER_CAPTURE_TIME');
    const [width,height]=imageSize(capture.screenshot);
    const sourceAX=encoder.encode(capture.state);const sourceAXSha=sha256Hex(sourceAX);
    need(saved.ax&&saved.ax.bytes===sourceAX.byteLength&&saved.ax.sha256===sourceAXSha,'CLASSIFIER_AX_RETENTION');
    const analysis=await analyzeCapture({screenshot:capture.screenshot,axText:capture.state,frameId,sessionId,capturedAt,
      width,height,sourceAXSha256:sourceAXSha,sourceBinding,capturedContext,saved});
    need(analysis?.version===1&&analysis.frame_id===frameId&&analysis.session_id===sessionId
      &&analysis.source_sha256===frameId&&analysis.source_ax_sha256===sourceAXSha,'CLASSIFIER_SOURCE_BINDING');
    const keys=['version','frame_id','session_id','source_sha256','source_ax_sha256','surface','group_key','native',
      'layout','surface_structure','surface_bounds_px','occlusion','editable_focus','focus_evidence','ax','cards',
      'boundary','boundary_evidence','chooser_controls'];
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
      need(el&&Object.keys(el).sort().join(',')===['index','role','subrole','identifier','label','value','bounds_px','parent_index','enabled']
        .sort().join(',')&&Number.isInteger(el.index)&&el.index>=0&&typeof el.role==='string'
        &&typeof el.subrole==='string'&&typeof el.identifier==='string'&&typeof el.enabled==='boolean'
        &&(el.parent_index===null||Number.isInteger(el.parent_index)),'CLASSIFIER_AX_ELEMENT');
      rect(el.bounds_px,width,height,'CLASSIFIER_AX_ELEMENT_BOUNDS');
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
      need(Object.keys(proof).sort().join(',')==='version,frame_id,session_id,source,indicator_index,minimum,maximum,value'
        &&proof.source==='AX_SCROLLBAR'&&Number.isInteger(proof.indicator_index)
        &&Number.isFinite(proof.minimum)&&Number.isFinite(proof.maximum)&&Number.isFinite(proof.value)
        &&proof.maximum>proof.minimum,'CLASSIFIER_BOUNDARY_EVIDENCE');
      const indicator=axElements.find(e=>e.index===proof.indicator_index);
      need(indicator?.role==='scroll bar'&&indicator.value===proof.value
        &&boundary.top===(proof.value===proof.minimum)&&boundary.bottom===(proof.value===proof.maximum),
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
    const uncertainty=support.uncertaintyPx;
    const witnessCards=[];const cards=[];
    need(Array.isArray(analysis.cards),'CLASSIFIER_CARDS');
    const byIndex=new Map(axElements.map(e=>[e.index,e]));const seen=new Set();
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
      const expectedTitle=`${id.start_date.replaceAll('-','/')}～${id.end_date.slice(5).replaceAll('-','/')}`;
      need(candidate.title===expectedTitle&&typeof candidate.fully_visible==='boolean','CLASSIFIER_CARD_TITLE');
      rect(candidate.card_bounds,width,height,'CLASSIFIER_CARD_BOUNDS');
      rect(candidate.metadata_bounds,width,height,'CLASSIFIER_METADATA_BOUNDS');
      rect(candidate.safe_metadata_bounds,width,height,'CLASSIFIER_SAFE_METADATA_BOUNDS');
      rect(candidate.thumbnail_bounds,width,height,'CLASSIFIER_THUMBNAIL_BOUNDS');
      need(Array.isArray(candidate.neighbor_bounds),'CLASSIFIER_NEIGHBORS');
      for(const b of candidate.neighbor_bounds)rect(b,width,height,'CLASSIFIER_NEIGHBOR_BOUNDS');
      need(inside(candidate.metadata_bounds,candidate.card_bounds)&&inside(candidate.thumbnail_bounds,candidate.card_bounds)
        &&inside(candidate.safe_metadata_bounds,candidate.metadata_bounds,uncertainty),'CLASSIFIER_CARD_CROSS_PAIR');
      const cardNode=byIndex.get(candidate.card_ax_index),thumbNode=byIndex.get(candidate.thumbnail_ax_index);
      need(cardNode&&['row','group','cell'].includes(cardNode.role)&&cardNode.bounds_px.join(',')===candidate.card_bounds.join(',')
        &&thumbNode?.role==='image'&&thumbNode.bounds_px.join(',')===candidate.thumbnail_bounds.join(','),
        'CLASSIFIER_AX_CARD_BINDING');
      const titleMatches=ocr.cua.filter(o=>completeDateTitle(o.text)?.start_date===id.start_date
        &&completeDateTitle(o.text)?.end_date===id.end_date&&o.candidate_count===1&&o.confidence>=0.5
        &&inside(o.bounds,candidate.metadata_bounds));
      const countMatches=ocr.cua.filter(o=>new RegExp(`(?<![0-9])${id.expected_images}(?![0-9])`).test(o.text)
        &&o.candidate_count===1&&o.confidence>=0.5&&inside(o.bounds,candidate.metadata_bounds));
      need(titleMatches.length===1&&countMatches.length===1&&titleMatches[0]!==countMatches[0],
        'CLASSIFIER_OCR_CARD_BINDING');
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
      screenshot_sha256:frameId,cards:witnessCards,boundary:{top:boundary.top,bottom:boundary.bottom,evidence:boundaryRef},
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
    need(Object.keys(observation).sort().join(',')===observationKeys.slice().sort().join(','),
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

  return Object.freeze({classify,classifyChooser,cache});
}
