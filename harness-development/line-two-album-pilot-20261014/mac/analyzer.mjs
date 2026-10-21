// Real before/CUA/after observations only. Missing full-card geometry refuses.
import {createHash} from 'node:crypto';
import path from 'node:path';
const hash=b=>createHash('sha256').update(b).digest('hex');
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
const shape=b=>[b.x,b.y,b.width,b.height];
const inside=(a,b)=>a[0]>=b[0]&&a[1]>=b[1]&&a[0]+a[2]<=b[0]+b[2]&&a[1]+a[3]<=b[1]+b[3];
const intersects=(a,b)=>a[0]<b[0]+b[2]&&b[0]<a[0]+a[2]&&a[1]<b[1]+b[3]&&b[1]<a[1]+a[3];
const intersection=(a,b)=>{const x=Math.max(a[0],b[0]),y=Math.max(a[1],b[1]);
  const r=Math.min(a[0]+a[2],b[0]+b[2]),bottom=Math.min(a[1]+a[3],b[1]+b[3]);
  return [x,y,r-x,bottom-y];};
const erode=(r,m)=>[r[0]+m,r[1]+m,r[2]-2*m,r[3]-2*m];
const role=v=>({'AXWindow':'window','AXSheet':'sheet','AXDialog':'dialog','AXRow':'row','AXGroup':'group',
  'AXCell':'cell','AXImage':'image','AXStaticText':'static text','AXTextField':'text field','AXButton':'button',
  'AXScrollBar':'scroll bar','AXScrollArea':'scroll area','AXMenu':'menu','AXMenuItem':'menu item'}[v]??String(v??'').replace(/^AX/,'').toLowerCase());
const ONE56={start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56};
const A45={start_date:'2024-04-22',end_date:'2024-04-26',expected_images:45};
const B78={start_date:'2024-04-21',end_date:'2024-04-21',expected_images:78};
const NAME_ONLY_TARGETS=[ONE56,A45,B78];
const isNameOnlyTarget=id=>NAME_ONLY_TARGETS.some(target=>target.start_date===id.start_date
  &&target.end_date===id.end_date&&target.expected_images===id.expected_images);

export function verifyNativePair(before,after) {
  for(const value of [before,after])need(value?.schemaVersion===1&&value.complete===true&&value.truncated===false,
    'NATIVE_CONTEXT_INCOMPLETE');
  const identity=v=>JSON.stringify([v.target?.bundleID,v.target?.pid,v.target?.startTimeSeconds,v.target?.startTimeMicroseconds]);
  need(before.target?.bundleID==='jp.naver.line.mac'&&identity(before)===identity(after),'PROCESS_INSTANCE_DRIFT');
  need(Number.isInteger(after.target.pid)&&after.target.pid>0&&Number.isInteger(after.target.startTimeSeconds)
    &&after.target.startTimeSeconds>0,'PROCESS_INSTANCE_REQUIRED');
  return after.target;
}

export function completeDateTitle(text) {
  const m=/^(\d{4})\/(\d{1,2})\/(\d{1,2})(?:\s*[~～〜]\s*(\d{1,2})\/(\d{1,2}))?$/.exec(text);
  if(!m)return null;
  const year=Number(m[1]),month=Number(m[2]),day=Number(m[3]);
  const valid=(y,mo,d)=>Number.isInteger(y)&&Number.isInteger(mo)&&Number.isInteger(d)
    &&y>=1&&mo>=1&&mo<=12&&d>=1&&d<=31
    &&new Date(Date.UTC(y,mo-1,d)).toISOString().slice(0,10)===`${String(y).padStart(4,'0')}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  if(!valid(year,month,day))return null;
  let endYear=year,endMonth=month,endDay=day;
  if(m[4]!==undefined){
    endMonth=Number(m[4]);endDay=Number(m[5]);
    endYear=year+((endMonth<month||(endMonth===month&&endDay<day))?1:0);
    if(!valid(endYear,endMonth,endDay))return null;
  }
  const iso=(y,mo,d)=>`${String(y).padStart(4,'0')}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  const start=iso(year,month,day);
  const end=iso(endYear,endMonth,endDay);
  return {start_date:start,end_date:end};
}

/** Assemble the retained menu calibration envelope from one menu-open frame's facts plus the
 *  fresh full-display SCK OCR of that same frame.
 *
 *  The authoritative 「儲存全部」 row is the unique SCK OCR row in display-global pixels: the
 *  hosted CUA crop is the input target, and the LINE popup is a separate raised window that may
 *  extend outside that crop. The clickable area is therefore proven, not assumed: the raw popup
 *  and label rectangles may cross the crop edge, but their intersection *with the crop* must be
 *  at least 16x16 px, `safe_bounds_px` must equal popup ∩ crop ∩ label, and the eroded interior
 *  (uncertainty + 4 px) must still be at least 16x16 px inside the crop. Anything else refuses.
 */
export function buildMenuEnvelope({menuFrame,sckRows,cuaRows,width,height}){
  need(menuFrame?.kind==='MENU_FRAME_FACTS'&&menuFrame.version===1&&menuFrame.evidence_only===true
    &&menuFrame.admissible_to_ordinary_classifier===false,'MENU_ENVELOPE_FACTS_REQUIRED');
  const mapping=menuFrame.mapping,popup=menuFrame.popup;
  need(mapping?.kind==='SCK_TO_CUA_LOCAL'&&Array.isArray(mapping.crop_px)
    &&JSON.stringify(mapping.crop_px)===JSON.stringify([0,0,width,height])
    &&Number.isFinite(mapping.backing_scale)&&mapping.backing_scale>0
    &&Array.isArray(mapping.cua_scale)&&mapping.cua_scale.length===2
    &&mapping.cua_scale.every(v=>Number.isFinite(v)&&v>0)
    &&Array.isArray(mapping.cua_offset_px)&&mapping.cua_offset_px.length===2
    &&mapping.cua_offset_px.every(Number.isFinite),'MENU_ENVELOPE_MAPPING');
  need(popup&&Number.isInteger(popup.window_number)&&popup.window_number>0
    &&Number.isInteger(popup.layer)&&popup.layer>0&&popup.above_window_id===menuFrame.native?.window_id
    &&Array.isArray(popup.bounds_px)&&popup.bounds_px.length===4&&popup.bounds_px.every(Number.isFinite)
    &&popup.bounds_px[2]>0&&popup.bounds_px[3]>0,'MENU_ENVELOPE_POPUP_BOUNDS');
  need(Number.isFinite(menuFrame.uncertainty_px)&&menuFrame.uncertainty_px>=2,'MENU_ENVELOPE_UNCERTAINTY');
  const crop=[0,0,width,height];
  const toCuaLocal=b=>[b[0]*mapping.cua_scale[0]/mapping.backing_scale+mapping.cua_offset_px[0],
    b[1]*mapping.cua_scale[1]/mapping.backing_scale+mapping.cua_offset_px[1],
    b[2]*mapping.cua_scale[0]/mapping.backing_scale,b[3]*mapping.cua_scale[1]/mapping.backing_scale];
  const popupCua=toCuaLocal(popup.bounds_px);
  need(popupCua.every(Number.isFinite)&&popupCua[2]>0&&popupCua[3]>0,'MENU_ENVELOPE_POPUP_BOUNDS');
  const popupIntersect=intersection(crop,popupCua);
  need(popupIntersect[2]>=16&&popupIntersect[3]>=16,'MENU_ENVELOPE_POPUP_OFFSCREEN');
  const rows=(Array.isArray(sckRows)?sckRows:[]).filter(o=>o&&['儲存全部','Save All'].includes(o.text)
    &&Number.isFinite(o.confidence)&&o.confidence>=.5&&o.candidate_count===1)
    .sort((a,b)=>a.bounds[1]-b.bounds[1]);
  need(rows.length===1,'MENU_SAVE_ALL_ROW_NOT_UNIQUE');
  const label=rows[0].bounds;
  need(Array.isArray(label)&&label.length===4&&label.every(Number.isFinite)&&label[2]>0&&label[3]>0,
    'MENU_ENVELOPE_ROW_BOUNDS');
  const labelCua=toCuaLocal(label);
  need(labelCua.every(Number.isFinite)&&labelCua[2]>0&&labelCua[3]>0,'MENU_ENVELOPE_ROW_BOUNDS');
  // If a future capture composites the popup into the crop as well, both spaces must agree.
  const mirrored=(Array.isArray(cuaRows)?cuaRows:[]).filter(o=>o&&['儲存全部','Save All'].includes(o.text)
    &&Number.isFinite(o.confidence)&&o.confidence>=.5&&o.candidate_count===1);
  if(mirrored.length>0)
    need(mirrored.length===1&&Array.isArray(mirrored[0].bounds)&&mirrored[0].bounds.length===4
      &&Math.max(...mirrored[0].bounds.map((v,i)=>Math.abs(v-labelCua[i])))<=2,
      'MENU_ENVELOPE_ROW_SPACE_CONFLICT');
  const labelIntersect=intersection(crop,labelCua);
  need(labelIntersect[2]>=16&&labelIntersect[3]>=16,'MENU_ENVELOPE_ROW_OFFSCREEN');
  const safe=intersection(popupIntersect,labelIntersect);
  need(safe[2]>=16&&safe[3]>=16,'MENU_SAFE_INTERSECTION');
  need(inside(safe,crop),'MENU_SAFE_INSIDE_CROP');
  const eroded=erode(safe,menuFrame.uncertainty_px+4);
  need(eroded[2]>=16&&eroded[3]>=16&&inside(eroded,crop),'MENU_SAFE_UNKNOWN');
  return {evidence_only:true,admissible_to_ordinary_classifier:false,
    frame_id:menuFrame.frame_id,session_id:menuFrame.session_id,source_sha256:menuFrame.source_sha256,
    source_ax_sha256:menuFrame.source_ax_sha256,native:menuFrame.native,process_start:menuFrame.process_start,
    layer_identity:menuFrame.layer_identity,
    popup:{...popup,cua_bounds_px:popupCua},
    save_all:{text:rows[0].text,label_bounds_px:label,cua_label_bounds_px:labelCua},
    mapping, safe_bounds_px:safe, eroded_bounds_px:eroded, uncertainty_px:menuFrame.uncertainty_px,
    ocr:menuFrame.ocr, detail_fingerprint:menuFrame.detail_fingerprint,
    detail_window_id:menuFrame.detail_window_id, list_window_id:menuFrame.list_window_id};
}

export function createLiveAnalyzer({runProcess,binary,repoRoot,retain,groupKey,groupTitle,groupTitleAliases=[],authorization,grantSha256,owner}) {
  const contexts=new Map();
  async function native(image=null) {
    const argv=[binary,'native-context','--bundle-id','jp.naver.line.mac','--project-root',repoRoot,
      '--grant',authorization,'--grant-sha256',typeof grantSha256==='function'?grantSha256():grantSha256,'--session-id',owner];
    if(image)argv.push('--image',path.join(repoRoot,image.path),'--image-sha256',image.sha256);
    const result=await runProcess(argv,{timeoutMs:30000,cap:2*1024*1024});
    if(!(result.status===0&&!result.stop_reason&&result.reaped===true)) {
      const diagnostic={command:argv,phase:image?'AFTER_CUA_CAPTURE':'BEFORE_CUA_CAPTURE',process_result:result};
      let evidence;
      try {
        evidence=await retain({artifact:diagnostic,kind:'native-context-failure',
          frameId:hash(Buffer.from(JSON.stringify(diagnostic)))});
      } catch(error) {
        throw Object.assign(new Error('NATIVE_CONTEXT_FAILED; diagnostic retention failed: '+(error.code??error.message)),
          {code:'NATIVE_CONTEXT_FAILED',cause:error});
      }
      throw Object.assign(new Error('NATIVE_CONTEXT_FAILED; evidence='+evidence.path),
        {code:'NATIVE_CONTEXT_FAILED',evidence});
    }
    const value=JSON.parse(result.stdout);const frameId=image?.sha256??hash(Buffer.from(result.stdout));
    const ref=await retain({artifact:{value,process_receipt:result.receipt},kind:'native-context',frameId});
    return {value,reference:ref};
  }
  const beforeCapture=()=>native();
  const afterCapture=({saved})=>native(saved);
  async function analyzeCapture({frameId,sessionId,capturedAt,width,height,sourceAXSha256,sourceBinding},
      {visualCardDiagnostic=false,scrollWitness=false,menuCalibration=false}={}) {
    const before=sourceBinding?.before,after=sourceBinding?.after;
    const value=after?.value;verifyNativePair(before?.value,value);
    const visual=value.visual;
    need(visual?.sourceSHA256===frameId&&visual.width===width&&visual.height===height&&Array.isArray(visual.ocr),
      'NATIVE_VISUAL_SOURCE_MISMATCH');
    const started=Date.parse(capturedAt);
    need(before.value.observedAtUnixMilliseconds<=started&&value.observedAtUnixMilliseconds>=started,
      'NATIVE_CAPTURE_ORDER');
    const ocr=visual.ocr.map(o=>({text:o.text,confidence:o.confidence,bounds:shape(o.bounds),candidate_count:o.candidateCount}));
    // A native focused window identity, not a same-sized window guess.
    const matches=value.windows.filter(w=>w.windowNumber===value.focusedWindowID&&w.nodeID!==null);
    need(matches.length===1,'FOCUSED_WINDOW_AMBIGUOUS');const win=matches[0];
    need(win.cgWindowNumber===win.windowNumber&&win.cgOwnerPID===value.target.pid&&win.framePt&&win.cgFramePt
      &&shape(win.framePt).every((n,i)=>Math.abs(n-shape(win.cgFramePt)[i])<=1),'AX_CG_WINDOW_MISMATCH');
    const prior=before.value.windows.filter(w=>w.windowNumber===win.windowNumber);
    need(prior.length===1&&JSON.stringify(prior[0].framePt)===JSON.stringify(win.framePt),'WINDOW_GEOMETRY_DRIFT');
    const bounds=shape(win.framePt);const sx=width/bounds[2],sy=height/bounds[3];
    need(Math.abs(sx-sy)<=.01&&sx>0,'CUA_WINDOW_SCALE_MISMATCH');
    const display=value.displays.filter(d=>win.displayIDs.includes(d.displayID)&&inside(bounds,shape(d.boundsPt)));
    // CG mode ratio is not hosted image scale; downstream SCK validation remains authoritative.
    need(display.length===1&&Number.isFinite(display[0].backingScale)&&display[0].backingScale>0,
      'DISPLAY_GEOMETRY_AMBIGUOUS');
    const ordered=value.onScreenWindows;
    need(Array.isArray(ordered),'OCCLUSION_EVIDENCE_MISSING');
    const at=ordered.findIndex(w=>w.windowNumber===win.windowNumber&&w.ownerPID===value.target.pid);
    need(at>=0,'WINDOW_NOT_ON_SCREEN');
    let menuOverlay=null;
    if(menuCalibration){
      // The authorized menu popup is the one LINE-owned raised-layer window above the fresh
      // authenticated detail grid; it is expected to overlap that grid. Every other window above
      // the grid stays subject to the ordinary occlusion rule (transparent, or disjoint).
      const overlays=[];
      for(const w of ordered.slice(0,at)){
        const raised=w.ownerPID===value.target.pid&&Number.isInteger(w.cgLayer)&&w.cgLayer>0;
        if(raised){
          need(typeof w.alpha==='number'&&w.alpha>0&&w.isOnScreen===true&&w.boundsPt
            &&Number.isInteger(w.windowNumber)&&w.windowNumber>0&&w.windowNumber!==win.windowNumber,
            'MENU_OVERLAY_WINDOW_IDENTITY');
          overlays.push({window:shape(w.boundsPt),layer:w.cgLayer,windowNumber:w.windowNumber,
            owner_pid:w.ownerPID,below_window_id:value.focusedWindowID});
          continue;
        }
        need(w.alpha===0||(typeof w.alpha==='number'&&w.alpha>0&&w.isOnScreen===true&&w.boundsPt
          &&!intersects(shape(w.boundsPt),bounds)),'WINDOW_OCCLUDED');
      }
      need(overlays.length===1,'MENU_OVERLAY_NOT_OBSERVED');
      menuOverlay=overlays[0];
    }else{
      for(const w of ordered.slice(0,at))need(w.alpha===0||(typeof w.alpha==='number'&&w.alpha>0
        &&w.isOnScreen===true&&w.boundsPt&&!intersects(shape(w.boundsPt),bounds)),'WINDOW_OCCLUDED');
    }
    const all=new Map(value.nodes.map(n=>[n.id,n]));const selected=[];const visited=new Set();
    function visit(id){need(!visited.has(id),'AX_CYCLE');visited.add(id);const n=all.get(id);need(n,'AX_NODE_MISSING');
      selected.push(n);for(const child of n.children)visit(child);}
    visit(win.nodeID);
    const px=b=>[(b.x-bounds[0])*sx,(b.y-bounds[1])*sy,b.width*sx,b.height*sy];
    const listIDs=new Set(selected.filter(n=>role(n.role)==='list').map(n=>n.id));
    const visible=selected.filter(n=>n.framePt&&n.offscreen!==true&&n.framePt.width>0&&n.framePt.height>0
      &&(inside(px(n.framePt),[0,0,width,height])||(scrollWitness&&role(n.role)==='row'
        &&listIDs.has(n.parentID)&&intersects(px(n.framePt),[0,0,width,height]))));
    const nativeIDs=new Map(visible.map((n,index)=>[n.id,index]));
    const elements=visible.map((n,index)=>({index,role:role(n.role),subrole:n.subrole??'',identifier:n.identifier??'',
      label:n.title??n.description??'',value:n.value??null,bounds_px:px(n.framePt),
      parent_index:nativeIDs.get(n.parentID)??null,enabled:n.enabled===true,
      ...(role(n.role)==='scroll bar'?{minimum_value:n.minimumValue??null,maximum_value:n.maximumValue??null,
        native_node_id:n.id}: {})}));
    const byID=new Map(elements.map(n=>[n.index,n]));
    const chooserRoot=elements.filter(e=>e.role==='sheet'||e.role==='dialog'||e.subrole==='AXDialog');
    need(chooserRoot.length<=1,'CHOOSER_ROOT_AMBIGUOUS');
    const allowedGroupTitles=[groupTitle,...groupTitleAliases];
    const group=ocr.filter(o=>allowedGroupTitles.includes(o.text)&&o.confidence>=.5&&o.candidate_count===1);
    const back=elements.filter(e=>e.role==='button'&&['返回','上一頁','Back'].includes(e.label));
    let detailSeed=null;
    if(chooserRoot.length===0&&back.length===0){
      const dates=ocr.filter(o=>completeDateTitle(o.text)&&o.confidence>=.5&&o.candidate_count===1);
      const counts=ocr.filter(o=>/^\d+張照片$/.test(o.text)&&o.confidence>=.5&&o.candidate_count===1);
      const viewer=ocr.some(o=>/\(\s*\d+\s*\/\s*\d+\s*\)/.test(o.text));
      const prior=[...contexts.values()].findLast(c=>c.analysis.native.pid===value.target.pid
        &&c.analysis.group_key===groupKey&&c.analysis.surface==='ALBUMS');
      if(!viewer&&dates.length===1&&counts.length===1){
        const id={...completeDateTitle(dates[0].text),expected_images:Number(counts[0].text.match(/^\d+/)[0])};
        const listed=prior?.analysis.cards.filter(c=>JSON.stringify(c.fingerprint)===JSON.stringify(id))??[];
        const old=prior?.sourceBinding.after.value;
        const oldWindow=prior?.analysis.native.window_id;
        const newWindow=value.windows.some(w=>w.windowNumber===oldWindow)
          &&value.focusedWindowID===win.windowNumber&&oldWindow!==win.windowNumber;
        if(listed.length===1&&old&&newWindow&&old.target.pid===value.target.pid
          &&old.target.startTimeSeconds===value.target.startTimeSeconds
          &&old.target.startTimeMicroseconds===value.target.startTimeMicroseconds)
          detailSeed={fingerprint:id,title:dates[0],count:counts[0],prior};
      }
    }
    const surface=chooserRoot.length===1?'FOLDER_CHOOSER':back.length===1||detailSeed?'ALBUM_DETAIL':'ALBUMS';
    if(surface!=='FOLDER_CHOOSER'){
      if(surface==='ALBUMS'||!detailSeed)need(group.length===1,'CANONICAL_GROUP_NOT_GROUNDED');
      else if(group.length>0)need(group.length===1,'DETAIL_GROUP_TITLE_AMBIGUOUS');
      if(surface==='ALBUMS'){
        let grounded=ocr.some(o=>o.text==='相簿'&&o.confidence>=.5);
        if(!grounded){
          const exact=text=>ocr.filter(o=>o.text===text&&o.confidence>=.3&&o.candidate_count===1);
          const albums=exact('相簿'),siblings=exact('記事本');
          const lists=elements.filter(e=>e.role==='list');
          if(albums.length===1&&siblings.length===1&&lists.length===1){
            const album=albums[0],sibling=siblings[0],list=lists[0],groupBounds=group[0].bounds;
            const sameTabRow=Math.min(album.bounds[1]+album.bounds[3],sibling.bounds[1]+sibling.bounds[3])
              >Math.max(album.bounds[1],sibling.bounds[1]);
            const separated=album.bounds[0]+album.bounds[2]<=sibling.bounds[0]
              ||sibling.bounds[0]+sibling.bounds[2]<=album.bounds[0];
            const ordered=[album,sibling].every(o=>inside(o.bounds,[0,0,width,height])
              &&groupBounds[1]+groupBounds[3]<=o.bounds[1]
              &&o.bounds[1]+o.bounds[3]<=list.bounds_px[1]);
            const rows=elements.filter(e=>e.role==='row'&&e.parent_index===list.index
              &&(scrollWitness?intersects(e.bounds_px,list.bounds_px):inside(e.bounds_px,list.bounds_px)));
            const corroborated=rows.filter(row=>{
              const titles=ocr.filter(o=>completeDateTitle(o.text)&&o.confidence>=.5&&o.candidate_count===1
                &&inside(o.bounds,row.bounds_px)&&(!scrollWitness||inside(o.bounds,list.bounds_px)));
              const counts=ocr.filter(o=>/^\d+$/.test(o.text)&&o.confidence>=.5&&o.candidate_count===1
                &&inside(o.bounds,row.bounds_px)&&(!scrollWitness||inside(o.bounds,list.bounds_px)));
              return titles.length===1&&counts.length===1&&Number(counts[0].text)>0
                &&counts[0].bounds[1]>=titles[0].bounds[1]+titles[0].bounds[3];
            });
            grounded=sameTabRow&&separated&&ordered&&corroborated.length===1;
          }
        }
        need(grounded,'ALBUM_SURFACE_NOT_GROUNDED');
      }
    }else{
      const prior=[...contexts.values()].findLast(c=>c.analysis.native.pid===value.target.pid
        &&c.analysis.group_key===groupKey&&c.analysis.surface==='ALBUM_DETAIL');
      need(prior&&prior.sourceBinding.after.value.target.startTimeSeconds===value.target.startTimeSeconds
        &&prior.sourceBinding.after.value.target.startTimeMicroseconds===value.target.startTimeMicroseconds,
        'CHOOSER_ORIGINAL_GROUP_LINEAGE_REQUIRED');
    }
    // Evidence collection only: this shape is deliberately inadmissible to classify().
    if(visualCardDiagnostic) {
      need(surface==='ALBUMS','VISUAL_DIAGNOSTIC_ALBUM_LIST_REQUIRED');
      const focused=visible.filter(n=>n.focused===true);
      const diagnostic={kind:'VISUAL_CARD_DIAGNOSTIC',evidence_only:true,actionable:false,version:1,
        frame_id:frameId,session_id:sessionId,source_sha256:frameId,source_ax_sha256:sourceAXSha256,
        surface,group_key:groupKey,native:{bundle_id:value.target.bundleID,pid:value.target.pid,
          window_id:win.windowNumber,display_id:display[0].displayID,cua_capture_bounds_points:bounds},
        layout:{line_version:value.target.appVersion,language:'zh-Hant',window_class:win.subrole??win.role,native_scale:sx},
        surface_structure:elements.map(({role,subrole,identifier})=>({role,subrole,identifier})),
        surface_bounds_px:[0,0,width,height],occlusion:'CLEAR',
        ax:{version:1,focused_index:focused.length===1?nativeIDs.get(focused[0].id):null,elements},raw_ocr:ocr};
      const reference=await retain({artifact:{sourceBinding,analysis:diagnostic},
        kind:'visual-card-diagnostic-analysis',frameId});
      return {...diagnostic,reference};
    }
    // Menu calibration: one authorized LINE popup over the fresh authenticated detail grid.
    // This branch returns the *facts* of the menu-open frame only. The Save All row is never
    // taken from the hosted CUA crop: that crop is the input target, and the LINE popup is a
    // separate raised window that may lie partly outside it. The row comes from the fresh
    // full-display SCK OCR bound to this same frame by buildMenuEnvelope().
    if(menuCalibration){
      need(surface==='ALBUM_DETAIL'&&menuOverlay,'MENU_ENVELOPE_DETAIL_REQUIRED');
      // The menu envelope belongs to the same LINE process and the detail window itself: the
      // focused window must be the fresh detail grid, never the originating list window.
      need(detailSeed&&Number.isInteger(win.windowNumber)
        &&win.windowNumber!==detailSeed.prior.analysis.native.window_id,'MENU_ENVELOPE_WINDOW_MISMATCH');
      const menuPt=menuOverlay.window;
      need(inside(menuPt,shape(display[0].boundsPt)),'MENU_REGION_OUTSIDE_DISPLAY');
      const backing=display[0].backingScale;
      need(Number.isFinite(backing)&&backing>0,'MENU_DISPLAY_SCALE');
      const crop=[0,0,width,height];
      const displayPt=shape(display[0].boundsPt);
      const menuPx=[(menuPt[0]-displayPt[0])*backing,(menuPt[1]-displayPt[1])*backing,
        menuPt[2]*backing,menuPt[3]*backing];
      need(inside(menuPx,[0,0,displayPt[2]*backing,displayPt[3]*backing]),'MENU_REGION_OUTSIDE_FULL_DISPLAY');
      // Measured SCK -> hosted CUA transform. Raw OCR/popup evidence stays in SCK display pixels;
      // every crop/intersection bound derived from it is the hosted CUA-local geometry the click uses.
      const cua_scale=[width/bounds[2],height/bounds[3]];
      const cua_offset_px=[-bounds[0]*cua_scale[0],-bounds[1]*cua_scale[1]];
      const u=Number.isFinite(display[0].uncertaintyPixels)?display[0].uncertaintyPixels:2;
      return {kind:'MENU_FRAME_FACTS',version:1,evidence_only:true,admissible_to_ordinary_classifier:false,
        frame_id:frameId,session_id:sessionId,source_sha256:frameId,source_ax_sha256:sourceAXSha256,
        native:{bundle_id:value.target.bundleID,pid:value.target.pid,window_id:win.windowNumber,
          display_id:display[0].displayID,cua_capture_bounds_points:bounds},
        process_start:[value.target.startTimeSeconds,value.target.startTimeMicroseconds],
        layer_identity:{owner_pid:menuOverlay.owner_pid,window_id:menuOverlay.windowNumber,
          layer:menuOverlay.layer,above_window_id:menuOverlay.below_window_id},
        popup:{window_number:menuOverlay.windowNumber,layer:menuOverlay.layer,bounds_pt:menuPt,
          bounds_px:menuPx,above_window_id:win.windowNumber},
        mapping:{kind:'SCK_TO_CUA_LOCAL',crop_px:crop,display_pt:displayPt,backing_scale:backing,
          cua_offset_px,cua_scale,inverse:'cua_px = sck_px * cua_scale / backing_scale + cua_offset_px'},
        uncertainty_px:u,
        layout:{line_version:value.target.appVersion,language:'zh-Hant',window_class:win.subrole??win.role,
          native_scale:sx},
        surface_structure:elements.map(({role,subrole,identifier})=>({role,subrole,identifier})),
        ocr:ocr.map(o=>({text:o.text,confidence:o.confidence,bounds:o.bounds,candidate_count:o.candidate_count})),
        detail_fingerprint:detailSeed.fingerprint,
        detail_window_id:win.windowNumber,list_window_id:detailSeed.prior.analysis.native.window_id};
    }
    const scroll=elements.filter(e=>e.role==='scroll bar');
    if(surface==='ALBUMS'){
      need(scroll.length===1&&typeof scroll[0].value==='string'&&/^-?(?:\d+\.?\d*|\.\d+)$/.test(scroll[0].value)
        &&Number.isFinite(scroll[0].minimum_value)&&Number.isFinite(scroll[0].maximum_value)
        &&scroll[0].maximum_value>scroll[0].minimum_value,'SCROLL_BOUNDARY_UNKNOWN');
      const raw=Number(scroll[0].value);
      need(raw>=scroll[0].minimum_value&&raw<=scroll[0].maximum_value,'SCROLL_RANGE_INVALID');
    }
    const cards=[];let detailIdentity=null;
    if(surface==='ALBUM_DETAIL'&&detailSeed){
      const fingerprint=detailSeed.fingerprint;
      const lineage={version:1,kind:'ALBUM_DETAIL_GRID',frame_id:frameId,session_id:sessionId,
        fingerprint,list_frame_id:detailSeed.prior.analysis.frame_id,
        list_window_id:detailSeed.prior.analysis.native.window_id,detail_window_id:win.windowNumber,
        pid:value.target.pid,process_start:[value.target.startTimeSeconds,value.target.startTimeMicroseconds],
        list_native_ref:detailSeed.prior.reference,detail_source_ref:after.reference};
      const nativeLineageRef=await retain({artifact:lineage,kind:'detail-native-lineage',frameId,sessionId});
      detailIdentity={kind:'ALBUM_DETAIL_GRID',fingerprint,title:{text:detailSeed.title.text,bounds:detailSeed.title.bounds},
        photo_count:{text:detailSeed.count.text,bounds:detailSeed.count.bounds},group_key:groupKey,
        list_frame_id:lineage.list_frame_id,list_window_id:lineage.list_window_id,detail_window_id:lineage.detail_window_id,
        pid:lineage.pid,process_start:lineage.process_start,native_lineage_ref:nativeLineageRef};
    }
    for(const node of (scrollWitness||surface==='ALBUM_DETAIL'&&detailSeed?[]:visible.filter(n=>surface!=='FOLDER_CHOOSER'
      &&['AXRow','AXGroup','AXCell'].includes(n.role)))) {
      const cardBounds=px(node.framePt);const titles=ocr.filter(o=>completeDateTitle(o.text)&&inside(o.bounds,cardBounds));
      if(titles.length!==1)continue;
      const descendants=new Set();function descend(id){for(const c of all.get(id)?.children??[]){descendants.add(c);descend(c);}}
      descend(node.id);
      const thumbnails=visible.filter(n=>descendants.has(n.id)&&n.role==='AXImage'&&n.framePt.width>0&&n.framePt.height>0);
      const title=titles[0];const counts=ocr.filter(o=>/^\d+$/.test(o.text)&&inside(o.bounds,cardBounds)
        &&o.bounds[1]>title.bounds[1]);
      if(counts.length!==1)continue;
      const id={...completeDateTitle(title.text),expected_images:Number(counts[0].text)};
      need(id.expected_images>0,'CARD_COUNT_INVALID');
      if(thumbnails.length===0){
        const fullyVisible=inside(cardBounds,[0,0,width,height]);
        const unsafe=visible.some(n=>role(n.role)==='button'&&n.enabled&&intersects(title.bounds,px(n.framePt)));
        if(!isNameOnlyTarget(id)||!fullyVisible||node.role!=='AXRow'||title.confidence<.5||title.candidate_count!==1
          ||counts[0].confidence<.5||counts[0].candidate_count!==1||unsafe)continue;
        const x=Math.min(title.bounds[0],counts[0].bounds[0]),y=title.bounds[1];
        const right=Math.max(title.bounds[0]+title.bounds[2],counts[0].bounds[0]+counts[0].bounds[2]);
        const bottom=counts[0].bounds[1]+counts[0].bounds[3];
        const metadata=[x,y,right-x,bottom-y],margin=6;
        const safe=[title.bounds[0]+margin,title.bounds[1]+margin,title.bounds[2]-2*margin,title.bounds[3]-2*margin];
        if(safe[2]<8||safe[3]<8||!inside(title.bounds,cardBounds)||!inside(counts[0].bounds,cardBounds))continue;
        cards.push({fingerprint:id,title:title.text,
          metadata_bounds:metadata,card_bounds:cardBounds,fully_visible:fullyVisible,
          safe_metadata_bounds:safe,neighbor_bounds:[],thumbnail_bounds:null,card_ax_index:nativeIDs.get(node.id),
          thumbnail_ax_index:null});
        continue;
      }
      if(thumbnails.length!==1)continue; // A non-target card needs its existing full thumbnail witness.
      const thumbBounds=px(thumbnails[0].framePt);
      const thumbCounts=counts.filter(o=>!inside(o.bounds,thumbBounds));
      if(thumbCounts.length!==1)continue;
      const metadata=[cardBounds[0],thumbBounds[1]+thumbBounds[3],cardBounds[2],
        cardBounds[1]+cardBounds[3]-thumbBounds[1]-thumbBounds[3]];
      need(metadata[3]>16&&inside(title.bounds,metadata)&&inside(thumbCounts[0].bounds,metadata),'FULL_CARD_METADATA_UNPROVEN');
      // Conservative seed erosion; measured SCK uncertainty is checked later.
      const margin=2+4;let safe=[metadata[0]+margin,metadata[1]+margin,metadata[2]-2*margin,metadata[3]-2*margin];
      const controls=visible.filter(n=>descendants.has(n.id)&&n.role==='AXButton'&&intersects(px(n.framePt),metadata));
      for(const control of controls) {
        const b=px(control.framePt);if(!intersects(safe,b))continue;
        const options=[[safe[0],safe[1],b[0]-margin-safe[0],safe[3]],
          [b[0]+b[2]+margin,safe[1],safe[0]+safe[2]-b[0]-b[2]-margin,safe[3]],
          [safe[0],safe[1],safe[2],b[1]-margin-safe[1]],
          [safe[0],b[1]+b[3]+margin,safe[2],safe[1]+safe[3]-b[1]-b[3]-margin]]
          .filter(r=>r[2]>=16&&r[3]>=16&&inside(r,safe));
        need(options.length>0,'CARD_CONTROL_EXCLUSION_UNPROVEN');
        options.sort((a,b)=>b[2]*b[3]-a[2]*a[3]);safe=options[0];
      }
      need(safe[2]>=16&&safe[3]>=16&&!intersects(safe,thumbBounds),'CARD_SAFE_GEOMETRY');
      cards.push({fingerprint:id,title:title.text,
        metadata_bounds:metadata,card_bounds:cardBounds,fully_visible:true,safe_metadata_bounds:safe,
        neighbor_bounds:[],thumbnail_bounds:thumbBounds,card_ax_index:nativeIDs.get(node.id),thumbnail_ax_index:nativeIDs.get(thumbnails[0].id)});
    }
    if(!scrollWitness){
      need(surface==='FOLDER_CHOOSER'||(surface==='ALBUM_DETAIL'&&detailSeed&&detailIdentity)||cards.length>0,
        'FULL_CARD_WITNESS_MISSING');
      if(surface==='ALBUM_DETAIL'&&detailSeed)need(detailIdentity&&cards.length===0,'DETAIL_IDENTITY_AMBIGUOUS');
    }
    cards.sort((a,b)=>a.card_bounds[1]-b.card_bounds[1]);
    for(const c of cards)c.neighbor_bounds=cards.filter(x=>x!==c).map(x=>x.card_bounds);
    if(!scrollWitness)need(new Set(cards.map(c=>JSON.stringify(c.fingerprint))).size===cards.length,
      'FULL_CARD_WITNESS_AMBIGUOUS');
    const focused=visible.filter(n=>n.focused===true);
    need(surface==='FOLDER_CHOOSER'||!focused.some(n=>n.role==='AXTextField'),'EDITABLE_FOCUS_CONFLICT');
    const focusedIndex=focused.length===1?nativeIDs.get(focused[0].id):null;
    if(scrollWitness){
      const lists=visible.filter(n=>role(n.role)==='list');
      need(lists.length===1,'SCROLL_VIEWPORT_AMBIGUOUS');
      need(surface==='ALBUMS'&&(focused.length===0
        ||focused.length===1&&role(focused[0].role)==='list'&&focused[0].id===lists[0].id),
        'SCROLL_FOCUS_NOT_CLEAR');
      const viewport=px(lists[0].framePt);
      const indicators=scroll.filter(e=>typeof e.value==='string'&&/^-?(?:\d+\.?\d*|\.\d+)$/.test(e.value)
        &&Number.isFinite(Number(e.value))&&Number.isFinite(e.minimum_value)&&Number.isFinite(e.maximum_value)
        &&e.maximum_value>e.minimum_value&&Number(e.value)>=e.minimum_value&&Number(e.value)<=e.maximum_value);
      need(indicators.length===1,'SCROLL_BOUNDARY_UNKNOWN');
      const rows=[];
      for(const node of visible.filter(n=>role(n.role)==='row'&&n.parentID===lists[0].id
        &&lists[0].children.includes(n.id))){
        const rowBounds=px(node.framePt);
        if(!intersects(rowBounds,viewport))continue;
        const titles=ocr.filter(o=>completeDateTitle(o.text)&&o.confidence>=.5&&o.candidate_count===1
          &&inside(o.bounds,rowBounds));
        if(titles.length!==1)continue;
        const title=titles[0];
        const counts=ocr.filter(o=>/^\d+$/.test(o.text)&&o.confidence>=.5&&o.candidate_count===1
          &&inside(o.bounds,rowBounds)&&o.bounds[1]>=title.bounds[1]+title.bounds[3]);
        if(counts.length!==1||Number(counts[0].text)<=0
          ||!inside(titles[0].bounds,viewport)||!inside(counts[0].bounds,viewport))continue;
        const dates=completeDateTitle(title.text);
        rows.push({fingerprint:{...dates,expected_images:Number(counts[0].text)},row_bounds:rowBounds,
          fully_visible:inside(rowBounds,viewport),identity_visible:true,
          metadata_bounds:[titles[0].bounds,counts[0].bounds],row_ax_index:nativeIDs.get(node.id)});
      }
      need(rows.length>0&&new Set(rows.map(row=>JSON.stringify(row.fingerprint))).size===rows.length,
        'SCROLL_LIST_WITNESS_AMBIGUOUS');
      const structure=elements.filter(e=>!['row','static text','text','scroll bar'].includes(e.role))
        .map(({role,subrole,identifier})=>({role,subrole,identifier}));
      const offset={version:1,frame_id:frameId,session_id:sessionId,source:'AX_SCROLLBAR',
        indicator_index:indicators[0].index,minimum:0,maximum:1,
        value:(Number(indicators[0].value)-indicators[0].minimum_value)/(indicators[0].maximum_value-indicators[0].minimum_value),
        raw_value:indicators[0].value,ax_minimum:indicators[0].minimum_value,ax_maximum:indicators[0].maximum_value,
        indicator_native_id:indicators[0].native_node_id,native_context_ref:after.reference};
      const analysis={version:1,frame_id:frameId,session_id:sessionId,source_sha256:frameId,
        source_ax_sha256:sourceAXSha256,surface,group_key:groupKey,
        native:{bundle_id:value.target.bundleID,pid:value.target.pid,window_id:win.windowNumber,
          display_id:display[0].displayID,cua_capture_bounds_points:bounds},
        layout:{line_version:value.target.appVersion,language:'zh-Hant',window_class:win.subrole??win.role,native_scale:sx},
        surface_structure:structure,surface_bounds_px:[0,0,width,height],occlusion:'CLEAR',editable_focus:'NONE',
        focus_evidence:{version:1,frame_id:frameId,session_id:sessionId,kind:'NONE',focused_index:focusedIndex},
        ax:{version:1,focused_index:focusedIndex,elements},cards:[],detail_identity:null,
        boundary:{top:Number(indicators[0].value)===indicators[0].minimum_value,
          bottom:Number(indicators[0].value)===indicators[0].maximum_value},boundary_evidence:offset,
        chooser_controls:{root_index:null,path_field_index:null,confirm_button_index:null,selected_leaf_index:null},
        scroll_witness:{viewport_bounds:viewport,viewport_ax_index:nativeIDs.get(lists[0].id),rows,
          native_identity:{display_id:display[0].displayID,cua_capture_bounds_points:bounds},
          process_instance:[value.target.bundleID,value.target.pid,value.target.startTimeSeconds,
            value.target.startTimeMicroseconds],
          scroll_offset:{frame_id:frameId,session_id:sessionId,
            value:(Number(indicators[0].value)-indicators[0].minimum_value)/(indicators[0].maximum_value-indicators[0].minimum_value)}}};
      const reference=await retain({artifact:{sourceBinding,analysis,raw_ocr:ocr},
        kind:'scroll-list-witness',frameId});
      contexts.set(frameId,{analysis,reference,sourceBinding});return analysis;
    }
    const pathFields=elements.filter(e=>e.role==='text field'&&e.subrole==='PathTextField'&&e.enabled);
    const confirms=elements.filter(e=>e.role==='button'&&e.enabled&&['選擇','選擇檔案夾','選擇資料夾','Choose','Open','開啟'].includes(e.label));
    need(surface!=='FOLDER_CHOOSER'||pathFields.length<=1&&confirms.length<=1,'CHOOSER_CONTROLS_AMBIGUOUS');
    const leaf=pathFields[0]?.value?.split('/').at(-1);
    const leaves=elements.filter(e=>leaf&&['static text','text','button'].includes(e.role)&&[e.label,e.value].includes(leaf));
    const editable=surface==='FOLDER_CHOOSER'&&pathFields[0]?.index===focusedIndex;
    const structure=elements.map(({role,subrole,identifier})=>({role,subrole,identifier}));
    const analysis={version:1,frame_id:frameId,session_id:sessionId,source_sha256:frameId,source_ax_sha256:sourceAXSha256,
      surface,group_key:groupKey,native:{bundle_id:value.target.bundleID,pid:value.target.pid,
        window_id:win.windowNumber,display_id:display[0].displayID,cua_capture_bounds_points:bounds},
      layout:{line_version:value.target.appVersion,language:'zh-Hant',window_class:win.subrole??win.role,native_scale:sx},
      surface_structure:structure,surface_bounds_px:[0,0,width,height],occlusion:'CLEAR',editable_focus:editable?'HIGH_EDITABLE':'NONE',
      focus_evidence:editable?{version:1,frame_id:frameId,session_id:sessionId,kind:'HIGH_EDITABLE',focused_index:focusedIndex,
        element_identifier:pathFields[0].identifier}:{version:1,frame_id:frameId,session_id:sessionId,kind:'NONE',focused_index:focusedIndex},
      ax:{version:1,focused_index:focusedIndex,elements},cards,detail_identity:detailIdentity,
      boundary:{top:surface==='ALBUMS'&&Number(scroll[0].value)===scroll[0].minimum_value,
        bottom:surface==='ALBUMS'&&Number(scroll[0].value)===scroll[0].maximum_value},
      boundary_evidence:surface==='ALBUMS'?{version:1,frame_id:frameId,session_id:sessionId,source:'AX_SCROLLBAR',indicator_index:scroll[0].index,
        minimum:0,maximum:1,value:(Number(scroll[0].value)-scroll[0].minimum_value)/(scroll[0].maximum_value-scroll[0].minimum_value),
        raw_value:scroll[0].value,
        ax_minimum:scroll[0].minimum_value,ax_maximum:scroll[0].maximum_value,
        indicator_native_id:scroll[0].native_node_id,native_context_ref:after.reference}
        :{version:1,frame_id:frameId,session_id:sessionId,source:'NOT_APPLICABLE'},
      chooser_controls:{root_index:chooserRoot[0]?.index??null,path_field_index:surface==='FOLDER_CHOOSER'?pathFields[0]?.index??null:null,
        confirm_button_index:surface==='FOLDER_CHOOSER'?confirms[0]?.index??null:null,
        selected_leaf_index:surface==='FOLDER_CHOOSER'&&leaves.length===1?leaves[0].index:null}};
    const ref=await retain({artifact:{sourceBinding,analysis,raw_ocr:ocr,projected_node_ids:elements.map(e=>e.index)},
      kind:'native-cua-correlation',frameId});
    contexts.set(frameId,{analysis,reference:ref,sourceBinding});return analysis;
  }
  const analyzeVisualCardDiagnostic=args=>analyzeCapture(args,{visualCardDiagnostic:true});
  const analyzeMenuFrame=args=>analyzeCapture(args,{menuCalibration:true});
  const analyzeScrollWitness=args=>analyzeCapture(args,{scrollWitness:true});
  return Object.freeze({beforeCapture,afterCapture,analyzeCapture,analyzeVisualCardDiagnostic,analyzeScrollWitness,
    analyzeMenuFrame,buildMenuEnvelope,contexts,native});
}
