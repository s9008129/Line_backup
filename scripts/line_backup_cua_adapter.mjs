// Load only inside the documented cua_repl kernel with a genuine App object.
// Ordinary Node tests supply external fake I/O; no CUA SDK or GUI synthesis here.
import {createHash, randomUUID} from 'node:crypto';
import {inflateSync} from 'node:zlib';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requireFact = (ok, code) => {if (!ok) throw new Error(code);};
const point = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const inside = (a,b) => Array.isArray(a)&&Array.isArray(b)&&a.length===4&&b.length===4
  &&a[0]>=b[0]&&a[1]>=b[1]&&a[0]+a[2]<=b[0]+b[2]&&a[1]+a[3]<=b[1]+b[3];
const hex64 = v => typeof v === 'string' && /^[0-9a-f]{64}$/.test(v);
const typeFinite = v => typeof v === 'number' && Number.isFinite(v);
const typedArrayPrototype = Object.getPrototypeOf(Uint8Array.prototype);
const typedArrayTag = Object.getOwnPropertyDescriptor(typedArrayPrototype, Symbol.toStringTag)?.get;
const typedArrayBuffer = Object.getOwnPropertyDescriptor(typedArrayPrototype, 'buffer')?.get;
const typedArrayByteOffset = Object.getOwnPropertyDescriptor(typedArrayPrototype, 'byteOffset')?.get;
const typedArrayByteLength = Object.getOwnPropertyDescriptor(typedArrayPrototype, 'byteLength')?.get;
const arrayBufferByteLength = Object.getOwnPropertyDescriptor(ArrayBuffer.prototype, 'byteLength')?.get;
const retainedObservationProofs = new WeakMap();

function decodePngRgb(value) {
  const bytes=value instanceof Uint8Array?value:new Uint8Array(value);
  const signature=[137,80,78,71,13,10,26,10];
  requireFact(signature.every((n,i)=>bytes[i]===n),'SCROLL_PNG_REQUIRED');
  let offset=8,width=0,height=0,depth=0,color=0,interlace=0;const idat=[];
  while(offset+12<=bytes.length){
    const length=(bytes[offset]*0x1000000)+(bytes[offset+1]<<16)+(bytes[offset+2]<<8)+bytes[offset+3];
    const type=String.fromCharCode(...bytes.subarray(offset+4,offset+8));
    const start=offset+8,end=start+length;requireFact(end+4<=bytes.length,'SCROLL_PNG_INVALID');
    if(type==='IHDR'){width=(bytes[start]*0x1000000)+(bytes[start+1]<<16)+(bytes[start+2]<<8)+bytes[start+3];
      height=(bytes[start+4]*0x1000000)+(bytes[start+5]<<16)+(bytes[start+6]<<8)+bytes[start+7];
      depth=bytes[start+8];color=bytes[start+9];interlace=bytes[start+12];}
    else if(type==='IDAT')idat.push(bytes.subarray(start,end));
    else if(type==='IEND')break;
    offset=end+4;
  }
  requireFact(width>0&&height>0&&depth===8&&(color===2||color===6)&&interlace===0,'SCROLL_PNG_UNSUPPORTED');
  const channels=color===6?4:3,bpp=channels,rowBytes=width*channels;
  const packed=inflateSync(Buffer.concat(idat.map(chunk=>Buffer.from(chunk))));
  requireFact(packed.length===(rowBytes+1)*height,'SCROLL_PNG_INVALID');
  const raw=new Uint8Array(rowBytes*height),prior=new Uint8Array(rowBytes);
  const paeth=(a,b,c)=>{const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
  for(let y=0;y<height;y++){
    const filter=packed[y*(rowBytes+1)];const input=packed.subarray(y*(rowBytes+1)+1,(y+1)*(rowBytes+1));
    const row=raw.subarray(y*rowBytes,(y+1)*rowBytes);
    for(let x=0;x<rowBytes;x++){
      const a=x>=bpp?row[x-bpp]:0,b=prior[x],c=x>=bpp?prior[x-bpp]:0;
      const predictor=filter===0?0:filter===1?a:filter===2?b:filter===3?Math.floor((a+b)/2):filter===4?paeth(a,b,c):null;
      requireFact(predictor!==null,'SCROLL_PNG_FILTER');row[x]=(input[x]+predictor)&255;
    }
    prior.set(row);
  }
  return {width,height,channels,pixels:raw};
}

async function retainedRgb(bytes,reference,decodeRetainedImage) {
  const signature=[137,80,78,71,13,10,26,10];
  if(signature.every((n,i)=>bytes[i]===n))return decodePngRgb(bytes);
  requireFact(bytes[0]===0xff&&bytes[1]===0xd8&&bytes[2]===0xff,'SCROLL_IMAGE_FORMAT_UNSUPPORTED');
  requireFact(typeof decodeRetainedImage==='function','SCROLL_JPEG_DECODER_REQUIRED');
  const decoded=await decodeRetainedImage({bytes:new Uint8Array(bytes),sourceSha256:sha(bytes),reference});
  requireFact(decoded?.sourceSha256===sha(bytes)&&decoded.png instanceof Uint8Array
    &&decoded.pngSha256===sha(decoded.png),'SCROLL_JPEG_DECODE_BINDING');
  return decodePngRgb(decoded.png);
}

function compareRetainedViewport(before,after,proof) {
  requireFact(proof&&proof.before&&proof.after,'SCROLL_RETAINED_IMAGE_PROOF_REQUIRED');
  requireFact(proof.before.frameId===before.frame_id&&proof.after.frameId===after.frame_id
    &&proof.before.saved?.sha256===before.frame_id&&proof.after.saved?.sha256===after.frame_id
    &&proof.before.saved?.ax?.sha256===sha(new TextEncoder().encode(proof.before.axRaw))
    &&proof.after.saved?.ax?.sha256===sha(new TextEncoder().encode(proof.after.axRaw)),
    'SCROLL_RETAINED_FRAME_BINDING');
  const a=decodePngRgb(proof.before.screenshot),b=decodePngRgb(proof.after.screenshot);
  requireFact(a.width===b.width&&a.height===b.height&&a.width===before.width&&a.height===before.height,
    'SCROLL_IMAGE_DIMENSIONS');
  const rect=before.viewport_bounds;requireFact(Array.isArray(rect)&&rect.length===4
    &&rect.every(Number.isInteger)&&rect[0]>=0&&rect[1]>=0&&rect[2]>0&&rect[3]>0
    &&rect[0]+rect[2]<=a.width&&rect[1]+rect[3]<=a.height&&JSON.stringify(rect)===JSON.stringify(after.viewport_bounds),
    'SCROLL_VIEWPORT_GROUNDING');
  let changed=0;
  for(let y=rect[1];y<rect[1]+rect[3];y++)for(let x=rect[0];x<rect[0]+rect[2];x++){
    const i=(y*a.width+x)*a.channels,j=(y*b.width+x)*b.channels;
    if(a.pixels[i]!==b.pixels[j]||a.pixels[i+1]!==b.pixels[j+1]||a.pixels[i+2]!==b.pixels[j+2])changed++;
  }
  requireFact(changed>0,'SCROLL_NO_VIEWPORT_PIXEL_CHANGE');
  return changed;
}

async function compareRetainedViewportProbe(before,after,proof,decodeRetainedImage) {
  requireFact(proof&&proof.before&&proof.after,'SCROLL_RETAINED_IMAGE_PROOF_REQUIRED');
  requireFact(proof.before.frameId===before.frame_id&&proof.after.frameId===after.frame_id
    &&proof.before.saved?.sha256===before.frame_id&&proof.after.saved?.sha256===after.frame_id
    &&proof.before.saved?.ax?.sha256===sha(new TextEncoder().encode(proof.before.axRaw))
    &&proof.after.saved?.ax?.sha256===sha(new TextEncoder().encode(proof.after.axRaw)),
    'SCROLL_RETAINED_FRAME_BINDING');
  const a=await retainedRgb(proof.before.screenshot,proof.before.saved,decodeRetainedImage);
  const b=await retainedRgb(proof.after.screenshot,proof.after.saved,decodeRetainedImage);
  requireFact(a.width===b.width&&a.height===b.height&&a.width===before.width&&a.height===before.height,
    'SCROLL_IMAGE_DIMENSIONS');
  const rect=before.viewport_bounds;requireFact(Array.isArray(rect)&&rect.length===4
    &&rect.every(Number.isInteger)&&rect[0]>=0&&rect[1]>=0&&rect[2]>0&&rect[3]>0
    &&rect[0]+rect[2]<=a.width&&rect[1]+rect[3]<=a.height
    &&JSON.stringify(rect)===JSON.stringify(after.viewport_bounds),'SCROLL_VIEWPORT_GROUNDING');
  let changed=0;
  for(let y=rect[1];y<rect[1]+rect[3];y++)for(let x=rect[0];x<rect[0]+rect[2];x++){
    const i=(y*a.width+x)*a.channels,j=(y*b.width+x)*b.channels;
    if(a.pixels[i]!==b.pixels[j]||a.pixels[i+1]!==b.pixels[j+1]||a.pixels[i+2]!==b.pixels[j+2])changed++;
  }
  requireFact(changed>0,'SCROLL_NO_VIEWPORT_PIXEL_CHANGE');return changed;
}

export async function verifyScrollMovement(before,after,proof=null,{decodeRetainedImage=null}={}) {
  requireFact(before?.surface==='ALBUMS'&&after?.surface==='ALBUMS'
    &&before.session_id===after.session_id&&before.group_key===after.group_key
    &&before.provider==='HOSTED_CUA'&&after.provider==='HOSTED_CUA'
    &&before.pid===after.pid&&before.process_instance===after.process_instance
    &&before.window_id===after.window_id&&before.layout_key===after.layout_key
    &&before.width===after.width&&before.height===after.height
    &&Number.isFinite(before.native_scale)&&before.native_scale>0&&before.native_scale===after.native_scale,
    'SCROLL_CONTEXT_DRIFT');
  const processInstance=(()=>{try{return JSON.parse(before.process_instance);}catch{return null;}})();
  requireFact(Array.isArray(processInstance)&&processInstance.length===4
    &&processInstance[0]==='jp.naver.line.mac'&&processInstance[1]===before.pid
    &&Number.isFinite(processInstance[2])&&Number.isFinite(processInstance[3]),'SCROLL_PROCESS_IDENTITY');
  requireFact(before.scroll_witness?.native_identity?.display_id>0
    &&before.scroll_witness.native_identity.display_id===after.scroll_witness?.native_identity?.display_id
    &&Array.isArray(before.scroll_witness.native_identity.cua_capture_bounds_points)
    &&JSON.stringify(before.scroll_witness.native_identity.cua_capture_bounds_points)
      ===JSON.stringify(after.scroll_witness?.native_identity?.cua_capture_bounds_points),
    'SCROLL_DISPLAY_ORIGIN_DRIFT');
  const beforeTime=Date.parse(before.captured_at),afterTime=Date.parse(after.captured_at);
  requireFact(Number.isFinite(beforeTime)&&Number.isFinite(afterTime)&&afterTime>beforeTime,
    'SCROLL_CAPTURE_TIME_ORDER');
  requireFact(before.frame_id!==after.frame_id&&hex64(before.frame_id)&&hex64(after.frame_id),
    'SCROLL_NO_VISUAL_CHANGE');
  const retained=proof??{before:retainedObservationProofs.get(before),after:retainedObservationProofs.get(after)};
  const changedPixels=await compareRetainedViewportProbe(before,after,retained,decodeRetainedImage);
  const rows=observation=>observation.scroll_witness?.rows;
  const pre=rows(before),post=rows(after);
  requireFact(Array.isArray(pre)&&Array.isArray(post)&&pre.length>0&&post.length>0,
    'SCROLL_LIST_WITNESS_REQUIRED');
  const key=row=>JSON.stringify([row.fingerprint?.start_date,row.fingerprint?.end_date,row.fingerprint?.expected_images]);
  const preIds=pre.map(key),postIds=post.map(key);
  requireFact(preIds.every((id,i)=>id!==JSON.stringify([null,null,null])&&preIds.indexOf(id)===i)
    &&postIds.every((id,i)=>id!==JSON.stringify([null,null,null])&&postIds.indexOf(id)===i),
    'SCROLL_LIST_IDENTITY_AMBIGUOUS');
  const viewport=before.viewport_bounds;
  const shared=pre.filter(row=>postIds.includes(key(row))&&row.identity_visible===true
    &&Array.isArray(row.row_bounds)&&row.row_bounds.length===4);
  requireFact(shared.length>0,'SCROLL_NO_SHARED_VISIBLE_ROW');
  const uncertainty=(before.mapping?.uncertainty??Infinity)+(after.mapping?.uncertainty??Infinity);
  requireFact(Number.isFinite(uncertainty)&&uncertainty>=0,'SCROLL_MAPPING_UNCERTAINTY');
  const displacement=[];
  for(const prior of shared){
    const current=post.find(row=>key(row)===key(prior));
    requireFact(current?.identity_visible===true&&Array.isArray(current.row_bounds)
      &&Array.isArray(current.metadata_bounds)&&current.metadata_bounds.length===2,
      'SCROLL_SHARED_ROW_NOT_VISIBLE');
    for(const bound of current.metadata_bounds)requireFact(inside(bound,viewport),'SCROLL_SHARED_IDENTITY_CLIPPED');
    const dy=current.row_bounds[1]-prior.row_bounds[1];
    requireFact(dy < -uncertainty,'SCROLL_SHARED_ROW_NOT_MOVED_UP');displacement.push(dy);
    const metadataDy=[];
    for(let i=0;i<2;i++){
      const a=prior.metadata_bounds?.[i],b=current.metadata_bounds[i];
      requireFact(Array.isArray(a)&&a.length===4&&Array.isArray(b)&&b.length===4
        &&a.every(Number.isFinite)&&b.every(Number.isFinite),'SCROLL_OCR_MOVEMENT_ANCHOR_REQUIRED');
      const textDy=b[1]-a[1];
      requireFact(textDy < -uncertainty&&Math.abs(textDy-dy)<=uncertainty
        &&Math.abs(b[0]-a[0])<=uncertainty&&Math.abs(b[2]-a[2])<=uncertainty
        &&Math.abs(b[3]-a[3])<=uncertainty,'SCROLL_OCR_MOVEMENT_INCONSISTENT');
      metadataDy.push(textDy);
    }
    requireFact(Math.abs((current.metadata_bounds[1][1]-current.metadata_bounds[0][1])
      -(prior.metadata_bounds[1][1]-prior.metadata_bounds[0][1]))<=uncertainty,
      'SCROLL_OCR_RELATIVE_GEOMETRY_DRIFT');
  }
  const a=before.parsed_ax,b=after.parsed_ax;
  requireFact(a?.raw_sha256===sha(new TextEncoder().encode(retained.before.axRaw))
    &&b?.raw_sha256===sha(new TextEncoder().encode(retained.after.axRaw))
    &&a.scroll_offset?.frame_id===before.frame_id&&b.scroll_offset?.frame_id===after.frame_id,
    'SCROLL_AX_RAW_BINDING');
  requireFact(Number.isFinite(a.scroll_offset.value)&&Number.isFinite(b.scroll_offset.value)
    &&b.scroll_offset.value>a.scroll_offset.value,'SCROLL_AX_OFFSET_NOT_ADVANCED');
  return Object.freeze({kind:'SCROLL_MOVEMENT_ONLY',evidence_only:true,actionable:false,changed_viewport_pixels:changedPixels,
    shared_row_count:shared.length,displacement_px:displacement,scroll_offset:[a.scroll_offset.value,b.scroll_offset.value]});
}

export function normalizeScreenshotBytes(value) {
  requireFact(ArrayBuffer.isView(value), 'CAPTURE_BYTES_INVALID');
  let tag, buffer, byteOffset, byteLength, backingLength;
  try {
    tag = Reflect.apply(typedArrayTag, value, []);
    buffer = Reflect.apply(typedArrayBuffer, value, []);
    byteOffset = Reflect.apply(typedArrayByteOffset, value, []);
    byteLength = Reflect.apply(typedArrayByteLength, value, []);
    backingLength = Reflect.apply(arrayBufferByteLength, buffer, []);
  } catch {
    throw new Error('CAPTURE_BYTES_INVALID');
  }
  requireFact(tag === 'Uint8Array' && Number.isSafeInteger(byteOffset) && byteOffset >= 0
    && Number.isSafeInteger(byteLength) && byteLength > 0 && byteLength <= 16 * 1024 * 1024
    && Number.isSafeInteger(backingLength) && byteOffset + byteLength <= backingLength,
  'CAPTURE_BYTES_INVALID');
  const copy = new Uint8Array(byteLength);
  copy.set(new Uint8Array(buffer, byteOffset, byteLength));
  return copy;
}

function verifyFrameReference(saved, frameId, byteLength) {
  requireFact(saved && typeof saved.path === 'string' && saved.path.startsWith('harness-development/')
    && Number.isInteger(saved.bytes) && saved.bytes === byteLength && saved.sha256 === frameId
    && saved.ax && typeof saved.ax.path === 'string' && saved.ax.path.startsWith('harness-development/')
    && Number.isInteger(saved.ax.bytes) && saved.ax.bytes > 0 && hex64(saved.ax.sha256),
  'CUA_FRAME_REFERENCE_REQUIRED');
}


// This check runs on two *actual retained LINE observations* after one reserved
// native scroll. It does not dispatch GUI events and accepts no fixture-only PASS.
export function verifyAlbumScroll(before, after, proof=null) {
  requireFact(before?.surface==='ALBUMS' && after?.surface==='ALBUMS'
    && before.session_id===after.session_id && before.group_key===after.group_key
    && before.provider==='HOSTED_CUA' && after.provider==='HOSTED_CUA'
    && before.pid===after.pid && before.window_id===after.window_id
    && before.layout_key===after.layout_key && before.width===after.width && before.height===after.height
    && Number.isFinite(before.native_scale)&&before.native_scale>0&&before.native_scale===after.native_scale,
    'SCROLL_CONTEXT_DRIFT');
  requireFact(hex64(before.frame_id) && hex64(after.frame_id)
    && before.frame_id!==after.frame_id, 'SCROLL_NO_VISUAL_CHANGE');
  const retained=proof??{before:retainedObservationProofs.get(before),after:retainedObservationProofs.get(after)};
  const changedPixels=compareRetainedViewport(before,after,retained);
  requireFact(Array.isArray(before.cards) && Array.isArray(after.cards),
    'SCROLL_CARD_EVIDENCE_REQUIRED');
  const complete = observation => observation.cards.filter(card=>
    card?.fully_visible===true && typeof card?.fingerprint?.start_date==='string'
    && typeof card?.fingerprint?.end_date==='string'
    && Number.isInteger(card?.fingerprint?.expected_images)
    && card.fingerprint.expected_images>0
    && Array.isArray(card.card_bounds) && card.card_bounds.length===4
    && card.card_bounds.every(Number.isFinite)
  );
  const id=card=>JSON.stringify([card.fingerprint.start_date,card.fingerprint.end_date,card.fingerprint.expected_images]);
  const previous=complete(before), current=complete(after), previousIds=previous.map(id), currentIds=current.map(id);
  requireFact(previous.length>0 && current.length>0 && new Set(previousIds).size===previous.length
    && new Set(currentIds).size===current.length, 'SCROLL_CARD_EVIDENCE_REQUIRED');
  let overlap=0;
  for(let n=Math.min(previousIds.length,currentIds.length);n>0;n--){
    if(previousIds.slice(-n).join('|')===currentIds.slice(0,n).join('|')){overlap=n;break;}
  }
  requireFact(overlap>0,'SCROLL_NO_ADJACENT_SUFFIX_PREFIX');
  requireFact(current.length>overlap,'SCROLL_NO_NEW_FULL_CARD');
  const uncertainty=Math.max(before.mapping?.uncertainty??Infinity,after.mapping?.uncertainty??Infinity);
  requireFact(Number.isFinite(uncertainty)&&uncertainty>=0,'SCROLL_MAPPING_UNCERTAINTY');
  const displacement=[];
  for(let i=0;i<overlap;i++){
    const a=previous[previous.length-overlap+i],b=current[i];
    const dy=b.card_bounds[1]-a.card_bounds[1];
    requireFact(dy < -uncertainty,'SCROLL_SHARED_CARD_NOT_MOVED_UP');displacement.push(dy);
  }
  const axBefore=before.parsed_ax,axAfter=after.parsed_ax;
  requireFact(axBefore&&axAfter&&Array.isArray(axBefore.cards)&&Array.isArray(axAfter.cards),
    'SCROLL_AX_CARDS_REQUIRED');
  const axIds=ax=>ax.cards.map(card=>JSON.stringify([card.start_date,card.end_date,card.expected_images]));
  const bx=axIds(axBefore),ax=axIds(axAfter);
  requireFact(axBefore.raw_sha256===sha(new TextEncoder().encode(retained.before.axRaw))
    &&axAfter.raw_sha256===sha(new TextEncoder().encode(retained.after.axRaw)),'SCROLL_AX_RAW_BINDING');
  requireFact(bx.length&&ax.length&&new Set(bx).size===bx.length&&new Set(ax).size===ax.length,
    'SCROLL_AX_CARDS_REQUIRED');
  requireFact(bx.slice(-overlap).join('|')===ax.slice(0,overlap).join('|')
    && bx.slice(-overlap).join('|')===previousIds.slice(-overlap).join('|'), 'SCROLL_AX_ORDER_DRIFT');
  const off0=axBefore.scroll_offset,off1=axAfter.scroll_offset;
  if(Number.isFinite(off0)&&Number.isFinite(off1))requireFact(off1>off0,'SCROLL_AX_OFFSET_CONTRADICTION');
  for(let i=0;i<overlap;i++)requireFact(Array.isArray(axBefore.cards[bx.length-overlap+i].bounds)
    &&Array.isArray(axAfter.cards[i].bounds),'SCROLL_AX_BOUNDS_REQUIRED');
  return Object.freeze({overlap_count:overlap,new_full_card_count:current.length-overlap,
    displacement_px:displacement,changed_viewport_pixels:changedPixels,
    ax_offset: Number.isFinite(off0)&&Number.isFinite(off1)?[off0,off1]:null});
}

export function createAlbumSupportCallbacks({invokeProducer}) {
  requireFact(typeof invokeProducer === 'function','PRODUCER_BRIDGE_REQUIRED');
  async function captureMenuSupport({action, pairFrameId, sessionId, requestedAt, cuaFrame, cuaCapturedAt}) {
    requireFact(hex64(pairFrameId) && cuaFrame && hex64(cuaFrame.sha256) && cuaFrame.sha256 === pairFrameId
      && typeof cuaFrame.path === 'string' && cuaFrame.path.startsWith('harness-development/') && Number.isInteger(cuaFrame.bytes),
      'CUA_FRAME_REFERENCE_REQUIRED');
    const support = await invokeProducer({mode:'capture',action,pairFrameId,sessionId,requestedAt,cuaFrame,cuaCapturedAt});
    requireFact(support?.provider === 'SCREEN_CAPTURE_KIT' && support?.pairFrameId === pairFrameId
      && hex64(support?.popupFrameId) && support.popupFrameId !== pairFrameId && support?.sessionId === sessionId
      && typeof support?.reference?.path === 'string' && support.reference.path.startsWith('harness-development/')
      && Number.isInteger(support.reference.bytes) && support.reference.bytes > 0 && hex64(support.reference.sha256)
      && typeFinite(support.uncertaintyPx) && support.uncertaintyPx >= 2
      && typeFinite(support.safeMarginPx) && support.safeMarginPx >= support.uncertaintyPx + 4
      && Array.isArray(support.intersectionPx) && support.intersectionPx.length === 4
      && support.intersectionPx[2] >= 16 && support.intersectionPx[3] >= 16,
      'SCK_SUPPORT_REQUIRED');
    return support;
  }
  async function guardMenu({action, support, pairFrameId, sessionId}) {
    requireFact(support?.reference && hex64(support.popupFrameId),'SCK_SUPPORT_REQUIRED');
    const guard = await invokeProducer({mode:'guard',support:support.reference,pairFrameId,popupFrameId:support.popupFrameId,
      saveAllPoint:action.save_all,uncertaintyPx:support.uncertaintyPx,sessionId});
    requireFact(guard?.verdict === 'PASS' && guard?.provider === 'SCREEN_CAPTURE_KIT'
      && guard?.pairFrameId === pairFrameId && guard?.popupFrameId === support.popupFrameId
      && guard?.supportSha256 === support.reference.sha256
      && point(guard?.actionPoint) && guard.actionPoint[0] === action.save_all[0] && guard.actionPoint[1] === action.save_all[1],
      'SCK_MENU_GUARD_REFUSED');
    return guard;
  }
  return Object.freeze({captureMenuSupport,guardMenu});
}

export function createHostedSession({app, bridge, retain, classify, collectMenuEnvelope = null, classifyChooser = null, requireV2 = false,
    requireV3 = false, chooser = null, beforeCapture = null, afterCapture = null,
    resolveWindowLineage = null, projectAlbumSlot=null, sessionId = randomUUID(),
    clock = () => performance.now(), wait = ms => new Promise(r => setTimeout(r,ms)), menuWaitMs = 1200}) {
  requireFact(app && ['getAXStateAndScreenshot','getAXState','click','pressKey','setValue','scroll'].every(k => typeof app[k] === 'function'), 'DOCUMENTED_APP_REQUIRED');
  requireFact(typeof bridge === 'function' && typeof retain === 'function' && typeof classify === 'function','HOST_BRIDGE_REQUIRED');
  const hasCaptureContextHooks = beforeCapture !== null || afterCapture !== null;
  requireFact(!hasCaptureContextHooks || (typeof beforeCapture === 'function' && typeof afterCapture === 'function'),
    'CAPTURE_CONTEXT_HOOKS_REQUIRED');
  if(requireV3)requireFact(typeof resolveWindowLineage==='function','PROJECT_WINDOW_LINEAGE_REQUIRED');
  requireFact(Number.isInteger(menuWaitMs) && menuWaitMs >= 800 && menuWaitMs <= 1500,'MENU_WAIT_OUTSIDE_POLICY');
  if (requireV2) requireFact(typeof classifyChooser === 'function' && chooser
    && ['locatePathField','validatePath','validateLeaf','locateConfirm','refreshBaseline','observeDownload']
      .every(k=>typeof chooser[k]==='function'),
    'V2_CHOOSER_DEPENDENCIES_REQUIRED');
  let latest = null, stopped = false, confirming = new Set(), activeProjectSlot=projectAlbumSlot;
  const permits = new WeakMap(), choosers = new WeakMap(), trace = [];
  const record = (event, extra={}) => trace.push(Object.freeze({event, at:clock(), wallAt:new Date().toISOString(), ...extra}));
  async function countObservation(kind,extra={}) {
    if(!requireV3)return;
    const checkpoint=kind==='paired'?extra.checkpoint:trace.at(-1)?.event??'INITIAL_CAPTURE';
    if(kind==='paired')requireFact(typeof checkpoint==='string'&&checkpoint.length>0,'PROJECT_CHECKPOINT_REQUIRED');
    const response=await bridge('gui_observe',{data:{kind,album:activeProjectSlot??'A',checkpoint,...extra}});
    requireFact(response?.status==='PROJECT_OBSERVATION_RESERVED','PROJECT_OBSERVATION_RESERVATION');
  }
  async function extraAX(){await countObservation('extra_ax');return app.getAXState({emit:false,disableDiffing:true});}
  function fresh(frameId) {
    requireFact(!stopped && latest && latest.frameId === frameId && clock() >= latest.at && clock()-latest.at <= 5000,'FRESH_CAPTURE_REQUIRED');
  }
  async function reserveGui(kind,count,runId,slots=null) {
    requireFact(!stopped,'SESSION_STOPPED');
    requireFact(Number.isInteger(count) && count > 0,'GUI_LEDGER_COUNT');
    const data={kind,count,run_id:runId,owner:sessionId};
    if(requireV3){requireFact(Array.isArray(slots)&&slots.length===count,'PROJECT_LEDGER_SLOT_REQUIRED');data.slots=slots;}
    const response = await bridge('gui_reserve',{data});
    const reservation = response?.reservation;
    requireFact(reservation && typeof reservation.id === 'string' && reservation.kind === kind
      && reservation.count === count,'GUI_LEDGER_RESERVE_REFUSED');
    latest = null;
    return Object.freeze({id:reservation.id,kind,count});
  }
  async function consumeGui(reservation,outcome) {
    const response = await bridge('gui_consume',{data:{reservation_id:reservation.id,outcome}});
    requireFact(response?.reservation?.id === reservation.id && response.reservation.state === 'CONSUMED',
      'GUI_LEDGER_CONSUME_REFUSED');
  }
  // Menu envelopes come only from the purpose-selected collector. They are never routed
  // through the ordinary classification wrapper, which binds to the ordinary frame cache.
  async function observe(checkpoint,{menuEnvelope=false}={}) {
    requireFact(!stopped,'SESSION_STOPPED');
    await countObservation('paired',{checkpoint});
    // Native context sampling happens outside the GUI capture call. The callback
    // receives no app handle, so it cannot interleave input into a GUI action.
    const beforeContext = hasCaptureContextHooks ? await beforeCapture({sessionId}) : null;
    const requestStartedAtMonotonic = clock();
    const requestStartedAtUtc = new Date().toISOString();
    const rawCapture = await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
    const requestEndedAtMonotonic = clock();
    const requestEndedAtUtc = new Date().toISOString();
    requireFact(Number.isFinite(requestStartedAtMonotonic) && Number.isFinite(requestEndedAtMonotonic)
      && requestEndedAtMonotonic >= requestStartedAtMonotonic && typeof rawCapture?.state === 'string',
    'CAPTURE_INCOMPLETE');
    const screenshot = normalizeScreenshotBytes(rawCapture.screenshot);
    const capture = Object.freeze({...rawCapture,screenshot});
    const frameId = sha(screenshot);
    const monotonicInterval = Object.freeze({start_ms:requestStartedAtMonotonic,end_ms:requestEndedAtMonotonic,
      duration_ms:requestEndedAtMonotonic-requestStartedAtMonotonic});
    const saved = await retain({screenshot,ax:capture.state,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    verifyFrameReference(saved,frameId,screenshot.byteLength);
    // The retained CUA frame is available to native-context/OCR readers here.
    // Keep capturedAt anchored to the original CUA request start; persistence
    // and OCR work must never make the frame appear newer.
    const afterContext = hasCaptureContextHooks ? await afterCapture({capture,saved,frameId,sessionId,
      sourceBinding:beforeContext,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval}) : null;
    const sourceBinding = hasCaptureContextHooks ? Object.freeze({before:beforeContext,after:afterContext}) : null;
    const capturedContext = sourceBinding;
    requireFact(!menuEnvelope||typeof collectMenuEnvelope==='function','MENU_ENVELOPE_COLLECTOR_REQUIRED');
    const observation = menuEnvelope
      ? await collectMenuEnvelope({capture,saved,frameId,sessionId,sourceBinding,capturedContext,
        capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval})
      : await classify({capture,saved,frameId,sessionId,sourceBinding,capturedContext,
        capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    requireFact(observation.frame_id === frameId && observation.session_id === sessionId,'CLASSIFIER_FRAME_MISMATCH');
    if(observation.parsed_ax)observation.parsed_ax={...observation.parsed_ax,raw_sha256:sha(new TextEncoder().encode(capture.state))};
    retainedObservationProofs.set(observation,{frameId,saved,screenshot:new Uint8Array(screenshot),axRaw:capture.state});
    // The capture interval starts before CUA and never renews during persistence/OCR.
    latest = Object.freeze({frameId,at:requestStartedAtMonotonic,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval,sourceBinding,capturedContext,observation,saved,capture});
    return observation;
  }
  async function makeChooserPhase(phase, dispatchInfo, previous=null) {
    requireFact(typeof classifyChooser==='function' && latest,'CHOOSER_CLASSIFIER_REQUIRED');
    const envelope=await classifyChooser({phase,dispatch:dispatchInfo,previous:previous?.envelope??null,
      capture:latest.capture,saved:latest.saved,observation:latest.observation,frameId:latest.frameId,
      sessionId,sourceBinding:latest.sourceBinding,capturedContext:latest.capturedContext,capturedAt:latest.capturedAt});
    requireFact(envelope?.version===1 && envelope.phase===phase && envelope.frame?.frame_id===latest.frameId
      && envelope.frame?.session_id===sessionId,'CHOOSER_PHASE_FRAME_MISMATCH');
    const reference=await retain({artifact:envelope,kind:`chooser-phase-${phase.toLowerCase()}`,
      frameId:latest.frameId,sessionId});
    requireFact(reference && typeof reference.path==='string' && reference.path.startsWith('harness-development/')
      && Number.isInteger(reference.bytes) && reference.bytes>0 && hex64(reference.sha256),'CHOOSER_PHASE_RETAIN_REQUIRED');
    return Object.freeze({phase,envelope,reference});
  }
  async function openAlbum(prepared) {
    fresh(prepared.frame_id);requireFact(point(prepared.click),'INVALID_CARD_POINT');
    const before=latest.observation,originAt=latest.at;
    activeProjectSlot=prepared.project_album_slot??activeProjectSlot;
    requireFact(before?.surface==='ALBUMS','ALBUM_OPEN_SURFACE_UNKNOWN');
    const reservation = await reserveGui('album_open',1,prepared.run_id,requireV3?[`${prepared.project_album_slot}.CARD`]:null);
    requireFact(clock()>=originAt&&clock()-originAt<=5000,'FRESH_CAPTURE_EXPIRED_AFTER_RESERVATION');
    record('ALBUM_OPEN_INVOCATION',{runId:prepared.run_id});
    latest = null;
    try {await app.click(prepared.click); await extraAX();}
    catch(e) {stopped=true;throw e;}
    await consumeGui(reservation,'RETURNED');
    try {
      const observedAfter=await observe(`PAIR-${activeProjectSlot}-DETAIL_OPEN`);
      const lineage=observedAfter.window_id===before.window_id?null:await resolveWindowLineage({kind:'ALBUM_CARD_OPEN_DETAIL',
        before,after:observedAfter,prepared});
      const {window_lineage:_lineageOnly,...after}=observedAfter;
      const related=after.window_id===before.window_id||(requireV3&&lineage?.from_window_id===before.window_id
        &&lineage?.to_window_id===after.window_id&&lineage?.relationship==='ALBUM_CARD_OPEN_DETAIL'
        &&lineage?.list_frame_id===before.frame_id);
      requireFact(after.surface==='ALBUM_DETAIL' && after.frame_id!==before.frame_id
        && after.session_id===before.session_id && after.group_key===before.group_key
        && after.pid===before.pid && related,
        'ALBUM_OPEN_NOT_VERIFIED');
      if(requireV3){
        const key=value=>JSON.stringify([value?.start_date,value?.end_date,value?.expected_images]);
        requireFact(after.detail_identity?.kind==='ALBUM_DETAIL_GRID'
          &&after.detail_identity.list_frame_id===before.frame_id
          &&after.detail_identity.list_window_id===before.window_id
          &&after.detail_identity.detail_window_id===after.window_id
          &&after.detail_identity.pid===after.pid
          &&key(after.detail_identity.fingerprint)===key(prepared.fingerprint),
          'PROJECT_DETAIL_IDENTITY_MISMATCH');
      }
      record('ALBUM_DETAIL_OBSERVED',{frameId:after.frame_id});
      if(requireV3){
        const detail=Object.freeze({...after,project_album_slot:activeProjectSlot});
        latest=Object.freeze({...latest,observation:detail});
        return detail;
      }
      return after;
    } catch(error) {
      stopped=true;latest=null;record('ALBUM_OPEN_UNVERIFIED',{message:String(error)});
      throw error;
    }
  }
  async function calibrateMenu({detail,runId,locateMenu,captureMenuSupport,guardMenu}) {
    fresh(detail.frame_id);
    requireFact(detail.surface==='ALBUM_DETAIL'&&typeof locateMenu==='function'
      &&typeof captureMenuSupport==='function'&&typeof guardMenu==='function','MENU_CALIBRATION_DEPENDENCIES');
    const detailStarted=latest.at;
    const reservation=await reserveGui('menu_calibration',2,runId,requireV3?[`${detail.project_album_slot}.CAL_OPEN`,`${detail.project_album_slot}.CAL_DISMISS`]:null);
    requireFact(clock()>=detailStarted&&clock()-detailStarted<=5000,'FRESH_CAPTURE_EXPIRED_AFTER_RESERVATION');
    const started=clock();const wallStarted=new Date().toISOString();let uncertain=false;
    try {
      const trigger=await locateMenu(detail,{phase:'TRIGGER'});
      requireFact(clock()>=detailStarted&&clock()-detailStarted<=5000,'FRESH_CAPTURE_EXPIRED_AFTER_LOCATOR');
      requireFact(point(trigger?.point)&&trigger.frameId===detail.frame_id
        &&trigger.evidence_kind==='PIXEL_STRUCTURE'&&trigger.component_count>=3
        &&trigger.point.every(Number.isInteger)&&Array.isArray(trigger.bounds_px)
        &&Array.isArray(trigger.interior_bounds_px)&&trigger.interior_bounds_px[2]>=16
        &&trigger.interior_bounds_px[3]>=16&&Number.isFinite(trigger.dot_spacing)&&trigger.dot_spacing>0,
        'MENU_TRIGGER_UNKNOWN');
      latest=null;record('MENU_OPEN_INVOCATION',{runId});await app.click(trigger.point);await extraAX();
      record('MENU_OPEN_RETURNED');await wait(menuWaitMs);
      const openFrame=await observe(`PAIR-${activeProjectSlot}-MENU_OPEN`,{menuEnvelope:true});
      requireFact(openFrame.kind==='MENU_CALIBRATION_ENVELOPE'&&openFrame.evidence_only===true
        &&openFrame.admissible_to_ordinary_classifier===false&&openFrame.session_id===sessionId,'MENU_OPEN_CONTEXT_DRIFT');
      const row=await locateMenu(openFrame,{phase:'ROW',detail});
      requireFact(point(row?.save_all)&&row.save_all.every(Number.isInteger)
        &&point(row?.dismiss_point)&&row.dismiss_point.every(Number.isInteger)
        &&row.frameId===openFrame.frame_id&&row.layoutKey===detail.layout_key
        &&Array.isArray(row.menuBounds)&&Array.isArray(row.addressableBounds)&&Array.isArray(row.safeBounds)
        &&Array.isArray(row.dismiss_bounds_px)&&row.evidence_kind==='FRESH_SCK_OCR_TRANSFORM'
        &&(row.label==='儲存全部'||row.label==='Save All'),'MENU_ROW_UNKNOWN');
      const action={run_id:runId,action_id:`CAL-${sessionId}-${openFrame.frame_id.slice(0,12)}`,
        owner:sessionId,save_all:row.save_all};
      await countObservation('popup');
      const support=await captureMenuSupport({action,pairFrameId:openFrame.frame_id,sessionId,requestedAt:clock(),
        cuaFrame:latest.saved,cuaCapturedAt:openFrame.captured_at,geometry:row});
      const guard=await guardMenu({action,support,pairFrameId:openFrame.frame_id,sessionId});
      requireFact(guard.verdict==='PASS'&&guard.pairFrameId===openFrame.frame_id
        &&guard.actionPoint[0]===row.save_all[0]&&guard.actionPoint[1]===row.save_all[1],'MENU_GUARD_REFUSED');
      record('MENU_SUPPORT_GUARD_PASS',{support:support.reference,guard});
      requireFact(clock()>=detailStarted&&clock()-detailStarted<=5000,'FRESH_CAPTURE_EXPIRED_BEFORE_CLOSE');
      fresh(openFrame.frame_id);
      latest=null;record('MENU_CLOSE_INVOCATION',{target:'TITLE_LABEL',point:row.dismiss_point});
      await app.click(row.dismiss_point);await extraAX();
      record('MENU_CLOSE_RETURNED');const closure=await observe(`PAIR-${activeProjectSlot}-MENU_CLOSURE`);
      const closureFacts=await locateMenu(closure,{phase:'CLOSURE',detail});
      requireFact(closureFacts?.native_popup_absent===true&&closureFacts.row_absent===true
        &&closureFacts.popup_window_id===row.popup_window_id&&closureFacts.detail_window_id===detail.window_id,
        'MENU_CLOSURE_POPUP_PRESENT');
      const closureFingerprint=closure.detail_identity?.fingerprint??closure.cards?.[0]?.fingerprint;
      const detailFingerprint=detail.detail_identity?.fingerprint??detail.cards?.[0]?.fingerprint;
      requireFact(closure.surface==='ALBUM_DETAIL'&&closure.session_id===sessionId&&closure.group_key===detail.group_key
        &&closure.pid===detail.pid&&closure.window_id===detail.window_id&&closure.layout_key===detail.layout_key
        &&JSON.stringify([closureFingerprint?.start_date,closureFingerprint?.end_date,closureFingerprint?.expected_images])
          ===JSON.stringify([detailFingerprint?.start_date,detailFingerprint?.end_date,detailFingerprint?.expected_images]),
        'MENU_CLOSURE_CONTEXT_DRIFT');
      await consumeGui(reservation,'RETURNED');
      const closedAt=new Date().toISOString();
      const calibration={observed_at:wallStarted,screenshot_width:detail.width,screenshot_height:detail.height,
        ellipsis:trigger.point,dot_spacing:trigger.dot_spacing,save_all_point:row.save_all,confidence:'HIGH',
        evidence:support.reference.sha256};
      const menu={label:row.label,frame_id:detail.frame_id,layout_key:detail.layout_key,
        evidence:support.reference,safe_bounds:row.safeBounds,ellipsis_bounds:trigger.bounds_px,
        closure_trace:['OPEN_MENU','OBSERVE_SAVE_ALL','CLOSE_WITHOUT_COMMAND','DETAIL_MATCH']};
      if(requireV3){
        const layout=detail.layout_signature??{};
        const applicability={kind:'LINE_MENU_APPLICABILITY',provider:'SCREEN_CAPTURE_KIT',
          line_version:layout.line_version??detail.line_version,language:layout.language??detail.language,
          window_class:layout.window_class??detail.window_class,layout_key:detail.layout_key,
          dimensions:[detail.width,detail.height],native_scale:layout.native_scale??detail.native_scale,
          menu_order:row.menu_order??row.menu_items?.map(item=>item.label)??[row.label],
          item_spacing:row.item_spacing??row.spacing,menu_bounds:row.menuBounds,
          addressable_bounds:row.addressableBounds,safe_bounds:row.safeBounds,
          ellipsis_bounds:trigger.bounds_px,ellipsis_point:trigger.point,dot_spacing:trigger.dot_spacing,
          save_all_bounds:row.saveAllBounds??row.safeBounds,save_all_point:row.save_all,
          support:support.reference,guard};
        requireFact(typeof applicability.line_version==='string'&&typeof applicability.language==='string'
          &&typeof applicability.window_class==='string'&&Number.isFinite(applicability.native_scale)
          &&Array.isArray(applicability.menu_order)&&Number.isFinite(applicability.item_spacing),
          'MENU_APPLICABILITY_INCOMPLETE');
        const applicabilityReference=await retain({artifact:applicability,kind:'menu-applicability',frameId:detail.frame_id,sessionId});
        const closureProof={kind:'LINE_MENU_CLOSURE',run_id:runId,frame_id:closure.frame_id,
          frame:latest.saved,ax:latest.saved.ax,menu_closed:true,no_activation:true,
          layout_key:closure.layout_key,popup_window_id:row.popup_window_id,popup_layer:row.popup_layer,
          native_popup_absent:closureFacts.native_popup_absent,row_absent:closureFacts.row_absent,
          closure_evidence_kind:closureFacts.evidence_kind,
          detail_fingerprint:detail.detail_identity?.fingerprint??detail.cards?.[0]?.fingerprint,
          closure_trace:menu.closure_trace};
        const closureReference=await retain({artifact:closureProof,kind:'menu-closure',frameId:closure.frame_id,sessionId});
        const claim={version:2,kind:'menu-calibration-no-io-pair',run_id:runId,session_id:sessionId,
          detail:detail.batch_record??detail,menu_frame:openFrame.batch_record??openFrame,trigger,label:row.label,support:support.reference,guard,
          calibration,closure_reference:closureReference,applicability_reference:applicabilityReference,
          reservation_id:reservation.id,reservation_ids:[reservation.id],reservation_state:'CONSUMED',
          opened_at:wallStarted,closed_at:closedAt};
        const reference=await retain({artifact:claim,kind:'menu-calibration',frameId:detail.frame_id,sessionId});
        return {detail,calibration,menu:{...menu,evidence:reference,closure_reference:closureReference,
          applicability_reference:applicabilityReference},closure,claim:reference};
      }
      const claim={version:1,kind:'menu-calibration',run_id:runId,session_id:sessionId,
        detail,menu_frame:openFrame,trigger,label:row.label,
        support:support.reference,guard,save_all:row.save_all,safe_bounds:row.safeBounds,
        opened_at:wallStarted,closed_at:closedAt,latency_ms:clock()-started,reservation_id:reservation.id,
        reservation_state:'CONSUMED'};
      const reference=await retain({artifact:claim,kind:'menu-calibration',frameId:detail.frame_id,sessionId});
      return {detail,calibration,menu:{...menu,evidence:reference},closure,claim:reference};
    } catch(error) {
      uncertain=true;stopped=true;latest=null;record('MENU_CALIBRATION_UNCERTAIN',{message:String(error)});throw error;
    } finally {
      if(!uncertain) { /* successful reservation was consumed above */ }
    }
  }
  async function originalIntent({receiptToken,freshObservation}) {
    fresh(freshObservation.frame_id);
    const committed = await bridge('intent',{expected_token:receiptToken,data:{fresh:freshObservation}});
    requireFact(committed.new_intent === true && committed.result?.status === 'ORIGINAL_INTENT_COMMITTED'
      && committed.result?.dispatch_authorized === true && committed.result?.fixture === false,
      'LIVE_DISPATCH_AUTHORITY_REQUIRED');
    fresh(freshObservation.frame_id);
    requireFact(committed.result.frame_id === latest.frameId && committed.result.session_id === sessionId,
      'INTENT_FRAME_MISMATCH');
    requireFact(latest.saved && typeof latest.saved.path === 'string' && Number.isInteger(latest.saved.bytes)
      && hex64(latest.saved.sha256) && latest.saved.sha256 === latest.frameId,'CUA_FRAME_REFERENCE_REQUIRED');
    requireFact(typeof latest.observation.captured_at === 'string','CUA_CAPTURE_TIME_REQUIRED');
    const token = Object.freeze({});
    permits.set(token,Object.freeze({result:committed.result,receiptToken:committed.receipt_token,
      frameId:latest.frameId,issuedAt:clock(),deadline:latest.at+5000,
      originalContext:Object.freeze({frame_id:latest.frameId,pid:latest.observation.pid,
        window_id:latest.observation.window_id,layout_key:latest.observation.layout_key}),
      cuaFrame:Object.freeze({path:latest.saved.path,bytes:latest.saved.bytes,sha256:latest.saved.sha256}),
      cuaCapturedAt:latest.observation.captured_at}));
    return token;
  }
  async function originalAtomicDispatch(token,{captureMenuSupport,guardMenu}={}) {
    const permit=permits.get(token);requireFact(permit,'NO_ORIGINAL_PERMISSION');
    // Consume before the first call. Throw/timeout/crash never leaves a reusable token.
    permits.delete(token);
    if(!requireV3)requireFact(typeof captureMenuSupport==='function' && typeof guardMenu==='function','MENU_GUARD_REQUIRED');
    if (requireV2) requireFact(typeof classifyChooser==='function' && chooser,'V2_CHOOSER_REQUIRED');
    fresh(permit.frameId);
    const action=permit.result;
    requireFact(point(action.ellipsis) && point(action.save_all),'INVALID_MENU_POINTS');
    requireFact(clock()-permit.issuedAt<=2000,'PERMIT_EXPIRED');
    const reservation = await reserveGui('dispatch_inputs',2,action.run_id,requireV3?
      [`${action.project_album_slot}.ATOMIC_ELLIPSIS`,`${action.project_album_slot}.SAVE_ALL`]:null);
    requireFact(clock()>=permit.issuedAt&&clock()<=permit.deadline,'PERMIT_EXPIRED_AFTER_RESERVATION');
    record('ELLIPSIS_INVOCATION',{actionId:action.action_id});
    latest=null;
    let support=null,guard=null;
    try {
      await app.click(action.ellipsis);
      record('ELLIPSIS_RETURNED');
      await wait(menuWaitMs);
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_MENU_CAPTURE');
      if(!requireV3){support=await captureMenuSupport(Object.freeze({action,pairFrameId:permit.frameId,sessionId,
        requestedAt:clock(),cuaFrame:permit.cuaFrame,cuaCapturedAt:permit.cuaCapturedAt}));
      requireFact(support?.provider==='SCREEN_CAPTURE_KIT' && support?.pairFrameId===permit.frameId
        && hex64(support?.popupFrameId) && support.popupFrameId!==permit.frameId && support?.sessionId===sessionId
        && typeof support?.reference?.path==='string' && support.reference.path.startsWith('harness-development/')
        && Number.isInteger(support.reference.bytes) && support.reference.bytes>0
        && hex64(support.reference.sha256),'SCK_SUPPORT_REQUIRED');
      guard=await guardMenu(Object.freeze({action,support,pairFrameId:permit.frameId,sessionId}));
      requireFact(guard?.verdict==='PASS' && guard?.provider==='SCREEN_CAPTURE_KIT'
        && guard?.pairFrameId===permit.frameId && guard?.popupFrameId===support.popupFrameId
        && guard?.supportSha256===support.reference.sha256
        && Array.isArray(guard?.actionPoint) && guard.actionPoint.length===2
        && guard.actionPoint[0]===action.save_all[0] && guard.actionPoint[1]===action.save_all[1],
        'SCK_MENU_GUARD_REFUSED');}
      if(!requireV3)record('SCK_MENU_GUARD_PASS',{popupFrameId:support.popupFrameId});
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_SAVE_ALL');
      record('SAVE_ALL_INVOCATION',{actionId:action.action_id});
      await app.click(action.save_all);
      record('SAVE_ALL_RETURNED');
      await consumeGui(reservation,'RETURNED');
    } catch(error) {
      stopped=true;record('DISPATCH_UNCERTAIN',{message:String(error)});throw error;
    }
    // No observe, persistence, bridge call, keyboard or app switch between the two clicks.
    await extraAX();
    const chooserObservation=await observe(`PAIR-${activeProjectSlot}-CHOOSER_APPEARED`);
    requireFact(chooserObservation.surface==='FOLDER_CHOOSER','CHOOSER_NOT_CONFIRMED');
    const dispatchInfo=Object.freeze({run_id:action.run_id,action_id:action.action_id,session_id:sessionId,
      owner:action.owner,destination:action.destination,original_frame_id:permit.frameId,
      original_context:permit.originalContext});
    let appeared=null;
    if (typeof classifyChooser==='function') {
      appeared=await makeChooserPhase('APPEARED',dispatchInfo);
      record('CHOOSER_APPEARED',{frameId:chooserObservation.frame_id});
    }
    const dispatch=Object.freeze({action,receiptToken:permit.receiptToken,chooser:chooserObservation,pairFrameId:permit.frameId,
      popupFrameId:support?.popupFrameId??null,support:support?.reference??null,guard,
      menuSupport:trace.findLast(t=>t.event==='SCK_MENU_GUARD_PASS'),reservation,dispatchInfo,appeared,
      trace:[...trace]});
    choosers.set(dispatch,true);
    return dispatch;
  }
  async function exactChooser({dispatch,locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload,
      destinationBaseline}) {
    requireFact(choosers.has(dispatch),'NO_ORIGINAL_CHOOSER_PERMISSION');
    const {action,chooser}=dispatch;
    fresh(chooser.frame_id);requireFact(chooser.surface==='FOLDER_CHOOSER','CHOOSER_NOT_CONFIRMED');
    requireFact(!confirming.has(action.action_id),'CONFIRMATION_ALREADY_ATTEMPTED');
    if (requireV2 || typeof classifyChooser==='function') {
      const deps={...chooser,locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload,
        destinationBaseline};
      return exactChooserV2({dispatch,...deps});
    }
    requireFact([locatePathField,validatePath,validateLeaf,locateConfirm].every(f => typeof f==='function'),'CHOOSER_LOCATORS_REQUIRED');
    // One Go-to-Folder navigation, then a newly observed actual text field.
    const reservation = await reserveGui('chooser_inputs',4,action.run_id);
    latest=null;await app.pressKey('super+shift+g');await extraAX();
    const dialog=await observe(`PAIR-${activeProjectSlot}-CHOOSER_GO_TO_FOLDER`);const field=await locatePathField(dialog);
    requireFact(Number.isInteger(field?.index) && field.index>=0 && field.frameId===dialog.frame_id && field.role==='text field','PATH_FIELD_UNKNOWN');
    fresh(dialog.frame_id);latest=null;await app.setValue(field.index,action.destination);await extraAX();
    const filled=await observe(`PAIR-${activeProjectSlot}-CHOOSER_PATH_FILLED`);requireFact(await validatePath(filled,action.destination),'FULL_PATH_NOT_CONFIRMED');
    fresh(filled.frame_id);latest=null;await app.pressKey('Return');await extraAX();
    const leaf=await observe(`PAIR-${activeProjectSlot}-CHOOSER_DESTINATION_SELECTED`);requireFact(await validateLeaf(leaf,action.destination),'DESTINATION_LEAF_MISMATCH');
    const confirmation=await locateConfirm(leaf);
    requireFact(point(confirmation?.point) && confirmation.frameId===leaf.frame_id && confirmation.role==='button','CONFIRM_CONTROL_UNKNOWN');fresh(leaf.frame_id);
    confirming.add(action.action_id);latest=null;record('CONFIRM_INVOCATION',{actionId:action.action_id});
    choosers.delete(dispatch);
    try {await app.click(confirmation.point);await extraAX();}
    catch(e) {stopped=true;record('CONFIRM_UNCERTAIN');throw e;}
    await consumeGui(reservation,'RETURNED');
    const afterConfirm=await observe(`PAIR-${activeProjectSlot}-CHOOSER_CONFIRM_ATTEMPTED`);
    if (afterConfirm.download_started!==true) {stopped=true;record('DOWNLOAD_START_UNKNOWN');throw new Error('DOWNLOAD_START_UNKNOWN');}
    // Stop LINE input before the receipt is sealed: the retained receipt must
    // carry the full dispatch event order and nothing may touch LINE after it.
    stopped=true;latest=null;record('CEASE_INPUT_AFTER_DOWNLOAD_START');
    const evidence={run_id:action.run_id,action_id:action.action_id,execution_id:action.owner,observed_at:new Date().toISOString(),
      save_all_click_count:1,save_all_invocation_attempted:true,failure_boundary:'NONE',folder_chooser_appeared:true,
      download_started:true,provenance:'HOSTED_CUA_AND_SCREEN_CAPTURE_KIT'};
    const chooserEvidence={action_id:action.action_id,session_id:sessionId,destination:action.destination,
      full_path:action.destination,leaf:action.destination.split('/').at(-1),confirmation_attempts:1,frame_id:chooser.frame_id,
      confirmation_frame_id:afterConfirm.frame_id,confirmation_attempted:true};
    const dispatchEventNames=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
      'SAVE_ALL_RETURNED','CONFIRM_INVOCATION','CEASE_INPUT_AFTER_DOWNLOAD_START'];
    try {
      const start=trace.findIndex(t=>t.event==='ELLIPSIS_INVOCATION');
      requireFact(start>=0,'DISPATCH_TRACE_ORDER');
      const dispatchEvents=trace.slice(start).filter(t=>dispatchEventNames.includes(t.event));
      requireFact(dispatchEvents.map(t=>t.event).join(',')===dispatchEventNames.join(','),'DISPATCH_TRACE_ORDER');
      const receipt={version:'cua-dispatch-receipt-1',run_id:action.run_id,action_id:action.action_id,execution_id:action.owner,
        session_id:sessionId,pair_frame_id:dispatch.pairFrameId,popup_frame_id:dispatch.popupFrameId,support:dispatch.support,
        guard:dispatch.guard,
        reservations:[{kind:dispatch.reservation.kind,count:dispatch.reservation.count,reservation_id:dispatch.reservation.id,state:'CONSUMED'},
          {kind:reservation.kind,count:reservation.count,reservation_id:reservation.id,state:'CONSUMED'}],
        events:dispatchEvents.map(t=>({event:t.event,at:t.at})),chooser:chooserEvidence,download_started:true,
        save_all_click_count:1,cease_input:true};
      const savedReceipt=await retain({receipt,kind:'cua-dispatch-receipt-1',frameId:dispatch.pairFrameId,sessionId});
      requireFact(savedReceipt && typeof savedReceipt.path==='string' && savedReceipt.path.startsWith('harness-development/')
        && Number.isInteger(savedReceipt.bytes) && savedReceipt.bytes>0 && hex64(savedReceipt.sha256),'RETAINED_RECEIPT_REQUIRED');
      const recorded=await bridge('dispatch',{expected_token:dispatch.receiptToken,
        data:{evidence,chooser:chooserEvidence,download_started:true,receipt:savedReceipt}});
      requireFact(recorded?.result?.status==='DOWNLOAD_STARTED','DISPATCH_READBACK_REQUIRED');
    } catch(e) {stopped=true;record('DISPATCH_RECORD_UNCERTAIN',{message:String(e)});throw e;}
    return afterConfirm;
  }
  async function exactChooserV2({dispatch,locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload,
      destinationBaseline}) {
    const {action,chooser,dispatchInfo}=dispatch;
    requireFact(dispatch.appeared?.phase==='APPEARED' && dispatchInfo?.action_id===action.action_id,
      'CHOOSER_APPEARED_PROOF_REQUIRED');
    requireFact([locatePathField,validatePath,validateLeaf,locateConfirm,refreshBaseline,observeDownload]
      .every(f=>typeof f==='function')
      &&destinationBaseline&&destinationBaseline.reference,
      'CHOOSER_LOCATORS_REQUIRED');
    const reservation=await reserveGui('chooser_inputs',4,action.run_id,requireV3?
      [`${action.project_album_slot}.GO_TO_FOLDER`,`${action.project_album_slot}.SET_PATH`,
        `${action.project_album_slot}.PATH_RETURN`,`${action.project_album_slot}.CHOOSER_CONFIRM`]:null);
    const phases=[dispatch.appeared];let prior=dispatch.appeared;
    try {
      latest=null;await app.pressKey('super+shift+g');await extraAX();
      const goObservation=await observe(`PAIR-${activeProjectSlot}-CHOOSER_GO_TO_FOLDER`);
      const go=await makeChooserPhase('GO_TO_FOLDER',dispatchInfo,prior);phases.push(go);prior=go;
      record('GO_TO_FOLDER',{frameId:goObservation.frame_id});
      const field=await locatePathField(go.envelope);
      requireFact(Number.isInteger(field?.index) && field.index>=0 && field.frameId===goObservation.frame_id
        && field.role==='text field' && field.subrole==='PathTextField','PATH_FIELD_UNKNOWN');

      fresh(goObservation.frame_id);latest=null;await app.setValue(field.index,action.destination);await extraAX();
      const filledObservation=await observe(`PAIR-${activeProjectSlot}-CHOOSER_PATH_FILLED`);
      const filled=await makeChooserPhase('PATH_FILLED',dispatchInfo,prior);phases.push(filled);prior=filled;
      record('PATH_FILLED',{frameId:filledObservation.frame_id});
      requireFact(await validatePath(filled.envelope,action.destination),'FULL_PATH_NOT_CONFIRMED');

      fresh(filledObservation.frame_id);latest=null;await app.pressKey('Return');await extraAX();
      const selectedObservation=await observe(`PAIR-${activeProjectSlot}-CHOOSER_DESTINATION_SELECTED`);
      const selected=await makeChooserPhase('DESTINATION_SELECTED',dispatchInfo,prior);phases.push(selected);prior=selected;
      record('DESTINATION_SELECTED',{frameId:selectedObservation.frame_id});
      requireFact(await validateLeaf(selected.envelope,action.destination),'DESTINATION_LEAF_MISMATCH');
      const confirmation=await locateConfirm(selected.envelope);
      requireFact(point(confirmation?.point) && confirmation.frameId===selectedObservation.frame_id
        && confirmation.role==='button' && confirmation.enabled===true,'CONFIRM_CONTROL_UNKNOWN');
      fresh(selectedObservation.frame_id);

      destinationBaseline=await refreshBaseline({action,frameId:selectedObservation.frame_id,previous:destinationBaseline});
      requireFact(destinationBaseline?.reference&&destinationBaseline?.artifact?.inventory?.length===0
        &&destinationBaseline?.identity,'DESTINATION_NOT_EMPTY_BEFORE_CONFIRM');

      confirming.add(action.action_id);latest=null;record('CONFIRM_INVOCATION',{actionId:action.action_id,point:[...confirmation.point]});
      choosers.delete(dispatch);
      try {await app.click(confirmation.point);await extraAX();}
      catch(error) {stopped=true;record('CONFIRM_UNCERTAIN');throw error;}
      await consumeGui(reservation,'RETURNED');
      const afterConfirm=await observe(`PAIR-${activeProjectSlot}-CHOOSER_CONFIRM_ATTEMPTED`);
      const attempted=await makeChooserPhase('CONFIRM_ATTEMPTED',dispatchInfo,prior);phases.push(attempted);
      record('CONFIRM_ATTEMPTED',{frameId:afterConfirm.frame_id});
      stopped=true;latest=null;

      const confirmationInvokedAt=trace.findLast(t=>t.event==='CONFIRM_INVOCATION')?.wallAt;
      requireFact(typeof confirmationInvokedAt==='string' && typeof observeDownload==='function',
        'DOWNLOAD_OBSERVER_REQUIRED');
      const download=await observeDownload({action,dispatch,confirmation:selected.envelope.frame,
        attempted:attempted.envelope.frame,confirmationInvokedAt,destinationBaseline});
      requireFact(download?.evidence?.source_kind==='FILESYSTEM_DELTA' && download?.evidence?.before_inventory?.length===0
        && Array.isArray(download?.evidence?.after_inventory) && download.evidence.after_inventory.length>0
        && download.evidence.run_id===action.run_id && download.evidence.action_id===action.action_id
        && download.evidence.execution_id===action.owner && download.evidence.session_id===sessionId
        && download.evidence.destination===action.destination
        && download.evidence.baseline?.path===destinationBaseline.reference.path
        && download.evidence.baseline?.sha256===destinationBaseline.reference.sha256
        && download.evidence.confirmation_frame_id===selected.envelope.frame.frame_id
        && download.evidence.confirmation_invoked_at===confirmationInvokedAt,
        'DOWNLOAD_START_UNKNOWN');
      const downloadRef=download.reference??await retain({artifact:download.evidence,kind:'download-start',
        frameId:selected.envelope.frame.frame_id,sessionId});
      requireFact(downloadRef && typeof downloadRef.path==='string' && downloadRef.path.startsWith('harness-development/')
        && Number.isInteger(downloadRef.bytes) && downloadRef.bytes>0 && hex64(downloadRef.sha256),'DOWNLOAD_EVIDENCE_RETAIN_REQUIRED');
      record('DOWNLOAD_EVIDENCE_OBSERVED',{at:download.evidence.observed_at,reference:downloadRef});
      record('CEASE_INPUT_AFTER_DOWNLOAD_START');

      const evidence={run_id:action.run_id,action_id:action.action_id,execution_id:action.owner,
        observed_at:download.evidence.observed_at,save_all_click_count:1,save_all_invocation_attempted:true,
        failure_boundary:'NONE',folder_chooser_appeared:true,download_started:true,
        provenance:'HOSTED_CUA_SCREEN_CAPTURE_KIT_AND_FILESYSTEM_DELTA'};
      const chooserEvidence={action_id:action.action_id,session_id:sessionId,destination:action.destination,
        full_path:action.destination,leaf:action.destination.split('/').at(-1),confirmation_attempts:1,
        frame_id:dispatch.appeared.envelope.frame.frame_id,
        confirmation_frame_id:selected.envelope.frame.frame_id,confirmation_attempted:true};
      const expectedEvents=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED',...(requireV3?[]:['SCK_MENU_GUARD_PASS']),'SAVE_ALL_INVOCATION',
        'SAVE_ALL_RETURNED','CHOOSER_APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED',
        'CONFIRM_INVOCATION','CONFIRM_ATTEMPTED','DOWNLOAD_EVIDENCE_OBSERVED','CEASE_INPUT_AFTER_DOWNLOAD_START'];
      const start=trace.findIndex(t=>t.event==='ELLIPSIS_INVOCATION');
      requireFact(start>=0,'DISPATCH_TRACE_ORDER');
      const dispatchEvents=trace.slice(start).filter(t=>expectedEvents.includes(t.event));
      requireFact(dispatchEvents.map(t=>t.event).join(',')===expectedEvents.join(','),'DISPATCH_TRACE_ORDER');
      const receipt={version:requireV3?'cua-dispatch-receipt-3':'cua-dispatch-receipt-2',run_id:action.run_id,action_id:action.action_id,
        execution_id:action.owner,session_id:sessionId,pair_frame_id:dispatch.pairFrameId,
        reservations:[{kind:dispatch.reservation.kind,count:dispatch.reservation.count,
          reservation_id:dispatch.reservation.id,state:'CONSUMED'},{kind:reservation.kind,count:reservation.count,
          reservation_id:reservation.id,state:'CONSUMED'}],
        events:dispatchEvents.map(t=>({event:t.event,at:t.event==='DOWNLOAD_EVIDENCE_OBSERVED'
          ?download.evidence.observed_at:t.event==='CONFIRM_INVOCATION'?t.wallAt:t.wallAt})),
        chooser:chooserEvidence,chooser_phases:phases.map(p=>p.reference),
        confirmation_frame:selected.envelope.frame.frame,confirmation_point:[...confirmation.point],download_evidence:downloadRef,
        save_all_click_count:1,cease_input:true};
      if(requireV3)Object.assign(receipt,{dispatch_policy:'LOGICAL_AT_MOST_ONCE_DURABLE_PRE_INPUT_RESERVATION_NO_REPLAY',
        calibration_reference:action.calibration_reference,calibration_closure_reference:action.calibration_closure_reference,
        applicability_reference:action.applicability_reference});
      else Object.assign(receipt,{popup_frame_id:dispatch.popupFrameId,support:dispatch.support,guard:dispatch.guard});
      const savedReceipt=await retain({receipt,kind:requireV3?'cua-dispatch-receipt-3':'cua-dispatch-receipt-2',frameId:dispatch.pairFrameId,sessionId});
      requireFact(savedReceipt && typeof savedReceipt.path==='string' && savedReceipt.path.startsWith('harness-development/')
        && Number.isInteger(savedReceipt.bytes) && savedReceipt.bytes>0 && hex64(savedReceipt.sha256),
        'RETAINED_RECEIPT_REQUIRED');
      const recorded=await bridge('dispatch',{expected_token:dispatch.receiptToken,
        data:{evidence,chooser:chooserEvidence,download_started:true,receipt:savedReceipt}});
      requireFact(recorded?.result?.status==='DOWNLOAD_STARTED','DISPATCH_READBACK_REQUIRED');
      return afterConfirm;
    } catch(error) {
      stopped=true;latest=null;record('DISPATCH_RECORD_UNCERTAIN',{message:String(error)});throw error;
    }
  }
  async function boundedScroll(observation,target,direction,distance,slot) {
    fresh(observation.frame_id);requireFact(observation.surface==='ALBUMS','SCROLL_SURFACE_UNKNOWN');
    requireFact(point(target) && ['up','down'].includes(direction) && Number.isFinite(distance) && distance>0 && distance<=0.25,'SCROLL_POLICY');
    if(requireV3)requireFact(activeProjectSlot==='A'&&['SCROLL_1','SCROLL_2','SCROLL_3'].includes(slot),
      'PROJECT_SESSION_SCROLL_UNSUPPORTED');
    const originAt=latest.at;
    const reservation = await reserveGui('scroll',1,null,requireV3?[slot]:null);
    requireFact(clock()>=originAt&&clock()-originAt<=5000,'FRESH_CAPTURE_EXPIRED_AFTER_RESERVATION');
    latest=null;record('ONE_SCROLL');
    try {await app.scroll(target,direction,distance);await extraAX();}
    catch(e) {stopped=true;throw e;}
    await consumeGui(reservation,'RETURNED');
    try {
      const after=await observe(`PAIR-A-DISCOVERY_${slot}_AFTER`);
      const progress=verifyAlbumScroll(observation,after);
      record('SCROLL_VERIFIED_NEW_CARD',progress);
      return after;
    } catch(error) {
      stopped=true;latest=null;record('SCROLL_UNVERIFIED',{message:String(error)});
      throw error;
    }
  }
  function ceaseInput() {stopped=true;latest=null;record('CEASE_INPUT');}
  return Object.freeze({sessionId,observe,openAlbum,originalIntent,originalAtomicDispatch,exactChooser,boundedScroll,
    calibrateMenu,ceaseInput,trace:()=>[...trace]});
}

// A fresh object for post-VERIFIED navigation. It exposes no intent, menu, chooser,
// or dispatch capability and cannot revive a stopped transaction session.
export function createNavigationObserver({app,bridge,retain,classify,requireV3=false,beforeCapture=null,afterCapture=null,
    resolveWindowLineage=null,checkpointPrefix='C1',sessionId=randomUUID(),
    clock=()=>performance.now(),decodeRetainedImage=null}) {
  requireFact(app&&['getAXStateAndScreenshot','getAXState','click','pressKey','scroll'].every(k=>typeof app[k]==='function'),
    'DOCUMENTED_APP_REQUIRED');
  requireFact(typeof bridge==='function'&&typeof retain==='function'&&typeof classify==='function',
    'NAVIGATION_OBSERVER_DEPENDENCIES');
  const hasCaptureContextHooks=beforeCapture!==null||afterCapture!==null;
  requireFact(!hasCaptureContextHooks||(typeof beforeCapture==='function'&&typeof afterCapture==='function'),
    'CAPTURE_CONTEXT_HOOKS_REQUIRED');
  if(requireV3)requireFact(typeof resolveWindowLineage==='function','PROJECT_WINDOW_LINEAGE_REQUIRED');
  let latest=null,closed=false;const trace=[],scrollProofs=[],movementProofs=[];
  const record=(event,extra={})=>trace.push(Object.freeze({event,at:clock(),wallAt:new Date().toISOString(),...extra}));
  async function countObservation(kind,extra={}) {
    if(!requireV3)return;
    const checkpoint=kind==='paired'?extra.checkpoint:trace.at(-1)?.event??'NAVIGATION_CAPTURE';
    if(kind==='paired')requireFact(typeof checkpoint==='string'&&checkpoint.length>0,'PROJECT_CHECKPOINT_REQUIRED');
    const response=await bridge('gui_observe',{data:{kind,album:'A',checkpoint,...extra}});
    requireFact(response?.status==='PROJECT_OBSERVATION_RESERVED','PROJECT_OBSERVATION_RESERVATION');
  }
  async function extraAX(){await countObservation('extra_ax');return app.getAXState({emit:false,disableDiffing:true});}
  async function reserve(kind,count,slots=null) {
    requireFact(!closed,'NAVIGATION_OBSERVER_CLOSED');
    const data={kind,count,run_id:null,owner:sessionId};if(requireV3){requireFact(Array.isArray(slots)&&slots.length===count,
      'PROJECT_LEDGER_SLOT_REQUIRED');data.slots=slots;}
    const response=await bridge('gui_reserve',{data});
    requireFact(response?.reservation?.kind===kind&&response.reservation.count===count,'GUI_LEDGER_RESERVE_REFUSED');
    latest=null;return response.reservation;
  }
  async function consume(reservation) {
    const response=await bridge('gui_consume',{data:{reservation_id:reservation.id,outcome:'RETURNED'}});
    requireFact(response?.reservation?.state==='CONSUMED','GUI_LEDGER_CONSUME_REFUSED');
  }
  async function observe(checkpoint) {
    requireFact(!closed,'NAVIGATION_OBSERVER_CLOSED');
    await countObservation('paired',{checkpoint});
    const beforeContext=hasCaptureContextHooks?await beforeCapture({sessionId}):null;
    const started=clock(),requestStartedAtUtc=new Date().toISOString();
    const rawCapture=await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
    const ended=clock(),requestEndedAtUtc=new Date().toISOString();
    requireFact(Number.isFinite(started)&&Number.isFinite(ended)&&ended>=started&&typeof rawCapture?.state==='string',
      'CAPTURE_INCOMPLETE');
    const screenshot=normalizeScreenshotBytes(rawCapture.screenshot);
    const capture=Object.freeze({...rawCapture,screenshot});
    const frameId=sha(screenshot);
    const monotonicInterval=Object.freeze({start_ms:started,end_ms:ended,duration_ms:ended-started});
    const saved=await retain({screenshot,ax:capture.state,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    verifyFrameReference(saved,frameId,screenshot.byteLength);
    const afterContext=hasCaptureContextHooks?await afterCapture({capture,saved,frameId,sessionId,
      sourceBinding:beforeContext,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval}):null;
    const sourceBinding=hasCaptureContextHooks?Object.freeze({before:beforeContext,after:afterContext}):null;
    const capturedContext=sourceBinding;
    const observation=await classify({capture,saved,frameId,sessionId,sourceBinding,capturedContext,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    requireFact(observation.frame_id===frameId&&observation.session_id===sessionId,'CLASSIFIER_FRAME_MISMATCH');
    if(observation.parsed_ax)observation.parsed_ax={...observation.parsed_ax,raw_sha256:sha(new TextEncoder().encode(capture.state))};
    retainedObservationProofs.set(observation,{frameId,saved,screenshot:new Uint8Array(screenshot),axRaw:capture.state});
    latest=Object.freeze({started,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,
      monotonicInterval,frameId,capture,saved,observation});return observation;
  }
  function fresh(frameId) {
    requireFact(latest&&latest.frameId===frameId&&clock()>=latest.started&&clock()-latest.started<=5000,
      'FRESH_CAPTURE_REQUIRED');
  }
  async function returnToAlbums(fromObservation,locateBack,expectedList=null) {
    fresh(fromObservation.frame_id);requireFact(typeof locateBack==='function','BACK_LOCATOR_REQUIRED');
    const originAt=latest.started;
    const control=await locateBack(fromObservation);
    requireFact(control?.frameId===fromObservation.frame_id&&control.role==='button'
      &&point(control.point),'BACK_CONTROL_UNKNOWN');
    const reservation=await reserve('return_navigation',1,requireV3?['RETURN_A_TO_LIST']:null);
    requireFact(clock()>=originAt&&clock()-originAt<=5000,'FRESH_CAPTURE_EXPIRED_AFTER_RESERVATION');record('RETURN_NAVIGATION_INVOCATION');
    try {await app.click(control.point);await extraAX();}
    catch(error) {closed=true;record('RETURN_NAVIGATION_UNCERTAIN');throw error;}
    await consume(reservation);record('RETURN_NAVIGATION_RETURNED');
    const observedAlbums=await observe('PAIR-C1-RETURN_LIST');requireFact(observedAlbums.surface==='ALBUMS','RETURN_TO_ALBUMS_FAILED');
    const lineage=observedAlbums.window_id===expectedList?.window_id?null:await resolveWindowLineage({
      kind:'DETAIL_RETURN_TO_LIST',from:fromObservation,to:observedAlbums,expectedList});
    const albums=lineage?{...observedAlbums,window_lineage:lineage}:observedAlbums;
    if(requireV3)requireFact(expectedList&&expectedList.surface==='ALBUMS'
      &&albums.session_id===expectedList.session_id&&albums.group_key===expectedList.group_key
      &&albums.pid===expectedList.pid&&albums.layout_key===expectedList.layout_key
      &&albums.width===expectedList.width&&albums.height===expectedList.height
      &&albums.native_scale===expectedList.native_scale
      &&(albums.window_id===expectedList.window_id||(lineage?.from_window_id===fromObservation.window_id
        &&lineage?.to_window_id===albums.window_id&&lineage?.relationship==='DETAIL_RETURN_TO_LIST'
        &&lineage?.list_window_id===expectedList.window_id&&lineage?.list_frame_id===expectedList.frame_id)),
      'RETURN_LIST_IDENTITY_DRIFT');
    return albums;
  }
  async function boundedScroll(before,target,direction,distance,slot,{mode='PILOT'}={}) {
    fresh(before.frame_id);requireFact(before.surface==='ALBUMS'&&['up','down'].includes(direction)
      &&point(target)&&Number.isFinite(distance)&&distance>0&&distance<=0.25,'SCROLL_POLICY');
    if(requireV3)requireFact(direction==='down'&&distance===0.25
      &&['SCROLL_1','SCROLL_2','SCROLL_3','SCROLL_4'].includes(slot),'PROJECT_SCROLL_SLOT');
    if(mode==='ONE_SCROLL_PROBE')requireFact(requireV3&&checkpointPrefix==='A_DISCOVERY'
      &&slot==='SCROLL_1'&&direction==='down'&&distance===0.25,'ONE_SCROLL_PROBE_SCOPE');
    else requireFact(mode==='PILOT','SCROLL_MODE');
    const originAt=latest.started;
    if(mode==='ONE_SCROLL_PROBE'){
      requireFact(before===latest.observation&&before.scroll_witness?.evidence_only===true
        &&before.scroll_witness?.actionable===false&&before.scroll_witness?.rows?.length>0,
        'ONE_SCROLL_SOURCE_FRAME_REQUIRED');
      const viewport=before.viewport_bounds,uncertainty=before.mapping?.uncertainty;
      requireFact(Array.isArray(viewport)&&viewport.length===4&&viewport.every(Number.isFinite)
        &&Number.isFinite(uncertainty)&&uncertainty>=0&&uncertainty<=2&&target.every(Number.isInteger),
        'ONE_SCROLL_VIEWPORT_GEOMETRY');
      const margin=uncertainty+4;
      requireFact(target[0]>=viewport[0]+margin&&target[1]>=viewport[1]+margin
        &&target[0]<=viewport[0]+viewport[2]-margin&&target[1]<=viewport[1]+viewport[3]-margin,
        'ONE_SCROLL_TARGET_OUTSIDE_SAFE_VIEWPORT');
      requireFact(typeof decodeRetainedImage==='function','SCROLL_JPEG_DECODER_REQUIRED');
      await retainedRgb(latest.capture.screenshot,latest.saved,decodeRetainedImage);
      requireFact(clock()>=originAt&&clock()-originAt<=5000,'FRESH_CAPTURE_EXPIRED_DURING_IMAGE_PREFLIGHT');
    }
    const reservation=await reserve('scroll',1,requireV3?[slot]:null);
    requireFact(clock()>=originAt&&clock()-originAt<=5000,'FRESH_CAPTURE_EXPIRED_AFTER_RESERVATION');record('SCROLL_INVOCATION',{direction,distance,slot});
    try {await app.scroll(target,direction,distance);await extraAX();}
    catch(error) {closed=true;record('SCROLL_UNCERTAIN');throw error;}
    await consume(reservation);record('SCROLL_RETURNED');
    try {
      const after=await observe(checkpointPrefix==='A_DISCOVERY'
        ?`PAIR-A-DISCOVERY_${slot}_AFTER`:`PAIR-C1-${slot}_AFTER`);
      const progress=mode==='ONE_SCROLL_PROBE'
        ?await verifyScrollMovement(before,after,null,{decodeRetainedImage})
        :verifyAlbumScroll(before,after);
      const pre=retainedObservationProofs.get(before),post=retainedObservationProofs.get(after);
      if(mode==='ONE_SCROLL_PROBE'){
        movementProofs.push({kind:'SCROLL_MOVEMENT_ONLY',evidence_only:true,actionable:false,slot,
          before_frame:pre.saved,after_frame:post.saved,before_ax:pre.saved.ax,after_ax:post.saved.ax,
          context:{session_id:before.session_id,group_key:before.group_key,provider:before.provider,
            pid:before.pid,process_instance:before.process_instance,list_window_id:before.window_id,
            layout_key:before.layout_key,width:before.width,height:before.height,native_scale:before.native_scale},
          movement:progress});
        record('SCROLL_MOVEMENT_ONLY',progress);return after;
      }
      const complete=observation=>observation.cards.filter(card=>card?.fully_visible===true);
      const beforeCards=complete(before),afterCards=complete(after),overlap=progress.overlap_count;
      const newCard=afterCards[overlap];
      requireFact(newCard?.fingerprint,'SCROLL_NEW_CARD_GROUNDING');
      scrollProofs.push({slot,before_frame:pre.saved,after_frame:post.saved,before_ax:pre.saved.ax,after_ax:post.saved.ax,
        overlap:'ORDERED_SUFFIX_PREFIX',overlap_count:overlap,new_candidate:newCard.fingerprint,
        new_candidates:afterCards.slice(overlap).map(card=>card.fingerprint),identity_continuity:true,
        context:{session_id:before.session_id,group_key:before.group_key,provider:before.provider,pid:before.pid,
          list_window_id:before.window_id,layout_key:before.layout_key,width:before.width,height:before.height,
          native_scale:before.native_scale},
        movement:'UPWARD_BEYOND_UNCERTAINTY'});
      record('SCROLL_VERIFIED_NEW_CARD',progress);
      return after;
    } catch(error) {
      closed=true;latest=null;record('SCROLL_UNVERIFIED',{message:String(error)});
      throw error;
    }
  }
  function close() {closed=true;latest=null;record('NAVIGATION_OBSERVER_CLOSED');}
  return Object.freeze({sessionId,observe,returnToAlbums,boundedScroll,close,trace:()=>[...trace],
    scrollEvidence:()=>scrollProofs.map(item=>({...item})),
    movementEvidence:()=>movementProofs.map(item=>({...item}))});
}
