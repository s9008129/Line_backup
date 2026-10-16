// Real before/CUA/after observations only. Missing full-card geometry refuses.
import {createHash} from 'node:crypto';
import path from 'node:path';
const hash=b=>createHash('sha256').update(b).digest('hex');
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
const shape=b=>[b.x,b.y,b.width,b.height];
const inside=(a,b)=>a[0]>=b[0]&&a[1]>=b[1]&&a[0]+a[2]<=b[0]+b[2]&&a[1]+a[3]<=b[1]+b[3];
const intersects=(a,b)=>a[0]<b[0]+b[2]&&b[0]<a[0]+a[2]&&a[1]<b[1]+b[3]&&b[1]<a[1]+a[3];
const role=v=>({'AXWindow':'window','AXSheet':'sheet','AXDialog':'dialog','AXRow':'row','AXGroup':'group',
  'AXCell':'cell','AXImage':'image','AXStaticText':'static text','AXTextField':'text field','AXButton':'button',
  'AXScrollBar':'scroll bar','AXScrollArea':'scroll area','AXMenu':'menu','AXMenuItem':'menu item'}[v]??String(v??'').replace(/^AX/,'').toLowerCase());

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
  const m=/^(\d{4})\/(\d{2})\/(\d{2})\s*[~～〜]\s*(\d{2})\/(\d{2})$/.exec(text);
  if(!m)return null;
  const start=`${m[1]}-${m[2]}-${m[3]}`;let year=Number(m[1]);
  if(`${m[4]}-${m[5]}`<`${m[2]}-${m[3]}`)year++;
  const end=`${year}-${m[4]}-${m[5]}`;
  for(const s of [start,end])if(new Date(s+'T00:00:00Z').toISOString().slice(0,10)!==s)return null;
  return {start_date:start,end_date:end};
}

export function createLiveAnalyzer({runProcess,binary,repoRoot,retain,groupKey,groupTitle,authorization,grantSha256,owner}) {
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
      {visualCardDiagnostic=false,scrollWitness=false}={}) {
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
    for(const w of ordered.slice(0,at))need(w.alpha===0||(typeof w.alpha==='number'&&w.alpha>0
      &&w.isOnScreen===true&&w.boundsPt&&!intersects(shape(w.boundsPt),bounds)),'WINDOW_OCCLUDED');
    const all=new Map(value.nodes.map(n=>[n.id,n]));const selected=[];const visited=new Set();
    function visit(id){need(!visited.has(id),'AX_CYCLE');visited.add(id);const n=all.get(id);need(n,'AX_NODE_MISSING');
      selected.push(n);for(const child of n.children)visit(child);}
    visit(win.nodeID);
    const px=b=>[(b.x-bounds[0])*sx,(b.y-bounds[1])*sy,b.width*sx,b.height*sy];
    const visible=selected.filter(n=>n.framePt&&n.offscreen!==true&&inside(px(n.framePt),[0,0,width,height])
      &&n.framePt.width>0&&n.framePt.height>0);
    const nativeIDs=new Map(visible.map((n,index)=>[n.id,index]));
    const elements=visible.map((n,index)=>({index,role:role(n.role),subrole:n.subrole??'',identifier:n.identifier??'',
      label:n.title??n.description??'',value:n.value??null,bounds_px:px(n.framePt),
      parent_index:nativeIDs.get(n.parentID)??null,enabled:n.enabled===true}));
    const byID=new Map(elements.map(n=>[n.index,n]));
    const chooserRoot=elements.filter(e=>e.role==='sheet'||e.role==='dialog'||e.subrole==='AXDialog');
    need(chooserRoot.length<=1,'CHOOSER_ROOT_AMBIGUOUS');
    const group=ocr.filter(o=>o.text===groupTitle&&o.confidence>=.5&&o.candidate_count===1);
    const back=elements.filter(e=>e.role==='button'&&['返回','上一頁','Back'].includes(e.label));
    const surface=chooserRoot.length===1?'FOLDER_CHOOSER':back.length===1?'ALBUM_DETAIL':'ALBUMS';
    if(surface!=='FOLDER_CHOOSER'){
      need(group.length===1,'CANONICAL_GROUP_NOT_GROUNDED');
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
              &&inside(e.bounds_px,list.bounds_px));
            const corroborated=rows.filter(row=>{
              const titles=ocr.filter(o=>completeDateTitle(o.text)&&o.confidence>=.5&&o.candidate_count===1
                &&inside(o.bounds,row.bounds_px));
              const counts=ocr.filter(o=>/^\d+$/.test(o.text)&&o.confidence>=.5&&o.candidate_count===1
                &&inside(o.bounds,row.bounds_px));
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
    for(const e of elements)if(e.role==='scroll bar'&&typeof e.value==='string'&&/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(e.value))e.value=Number(e.value);
    const scroll=elements.filter(e=>e.role==='scroll bar'&&typeof e.value==='number');
    if(surface==='ALBUMS')need(scroll.length===1&&scroll[0].value>=0&&scroll[0].value<=1,'SCROLL_BOUNDARY_UNKNOWN');
    const cards=[];
    for(const node of (scrollWitness?[]:visible.filter(n=>surface!=='FOLDER_CHOOSER'
      &&['AXRow','AXGroup','AXCell'].includes(n.role)))) {
      const cardBounds=px(node.framePt);const titles=ocr.filter(o=>completeDateTitle(o.text)&&inside(o.bounds,cardBounds));
      if(titles.length!==1)continue;
      const descendants=new Set();function descend(id){for(const c of all.get(id)?.children??[]){descendants.add(c);descend(c);}}
      descend(node.id);
      const thumbnails=visible.filter(n=>descendants.has(n.id)&&n.role==='AXImage'&&n.framePt.width>0&&n.framePt.height>0);
      if(thumbnails.length!==1)continue; // A grid without a complete container is not one witnessed thumbnail.
      const thumbBounds=px(thumbnails[0].framePt);
      const title=titles[0];const counts=ocr.filter(o=>/^\d+$/.test(o.text)&&inside(o.bounds,cardBounds)
        &&o.bounds[1]>title.bounds[1]&&!inside(o.bounds,thumbBounds));
      if(counts.length!==1)continue;
      const id={...completeDateTitle(title.text),expected_images:Number(counts[0].text)};
      need(id.expected_images>0,'CARD_COUNT_INVALID');
      const metadata=[cardBounds[0],thumbBounds[1]+thumbBounds[3],cardBounds[2],
        cardBounds[1]+cardBounds[3]-thumbBounds[1]-thumbBounds[3]];
      need(metadata[3]>16&&inside(title.bounds,metadata)&&inside(counts[0].bounds,metadata),'FULL_CARD_METADATA_UNPROVEN');
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
      cards.push({fingerprint:id,title:`${id.start_date.replaceAll('-','/')}～${id.end_date.slice(5).replaceAll('-','/')}`,
        metadata_bounds:metadata,card_bounds:cardBounds,fully_visible:true,safe_metadata_bounds:safe,
        neighbor_bounds:[],thumbnail_bounds:thumbBounds,card_ax_index:nativeIDs.get(node.id),thumbnail_ax_index:nativeIDs.get(thumbnails[0].id)});
    }
    if(!scrollWitness){
      need(surface==='FOLDER_CHOOSER'||cards.length>0,'FULL_CARD_WITNESS_MISSING');
      if(surface==='ALBUM_DETAIL')need(cards.length===1,'DETAIL_IDENTITY_AMBIGUOUS');
    }
    cards.sort((a,b)=>a.card_bounds[1]-b.card_bounds[1]);
    for(const c of cards)c.neighbor_bounds=cards.filter(x=>x!==c).map(x=>x.card_bounds);
    if(!scrollWitness)need(new Set(cards.map(c=>JSON.stringify(c.fingerprint))).size===cards.length,
      'FULL_CARD_WITNESS_AMBIGUOUS');
    const focused=visible.filter(n=>n.focused===true);
    need(surface==='FOLDER_CHOOSER'||!focused.some(n=>n.role==='AXTextField'),'EDITABLE_FOCUS_CONFLICT');
    const focusedIndex=focused.length===1?nativeIDs.get(focused[0].id):null;
    if(scrollWitness){
      need(surface==='ALBUMS'&&focused.length===0,'SCROLL_FOCUS_NOT_CLEAR');
      const lists=visible.filter(n=>role(n.role)==='list');
      need(lists.length===1,'SCROLL_VIEWPORT_AMBIGUOUS');
      const viewport=px(lists[0].framePt);
      const indicators=elements.filter(e=>e.role==='scroll bar'&&typeof e.value==='number'&&e.value>=0&&e.value<=1);
      need(indicators.length===1,'SCROLL_BOUNDARY_UNKNOWN');
      const rows=[];
      for(const node of visible.filter(n=>role(n.role)==='row'&&n.parentID===lists[0].id)){
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
        indicator_index:indicators[0].index,minimum:0,maximum:1,value:indicators[0].value};
      const analysis={version:1,frame_id:frameId,session_id:sessionId,source_sha256:frameId,
        source_ax_sha256:sourceAXSha256,surface,group_key:groupKey,
        native:{bundle_id:value.target.bundleID,pid:value.target.pid,window_id:win.windowNumber,
          display_id:display[0].displayID,cua_capture_bounds_points:bounds},
        layout:{line_version:value.target.appVersion,language:'zh-Hant',window_class:win.subrole??win.role,native_scale:sx},
        surface_structure:structure,surface_bounds_px:[0,0,width,height],occlusion:'CLEAR',editable_focus:'NONE',
        focus_evidence:{version:1,frame_id:frameId,session_id:sessionId,kind:'NONE',focused_index:focusedIndex},
        ax:{version:1,focused_index:focusedIndex,elements},cards:[],
        boundary:{top:indicators[0].value===0,bottom:indicators[0].value===1},boundary_evidence:offset,
        chooser_controls:{root_index:null,path_field_index:null,confirm_button_index:null,selected_leaf_index:null},
        scroll_witness:{viewport_bounds:viewport,viewport_ax_index:nativeIDs.get(lists[0].id),rows,
          native_identity:{display_id:display[0].displayID,cua_capture_bounds_points:bounds},
          process_instance:[value.target.bundleID,value.target.pid,value.target.startTimeSeconds,
            value.target.startTimeMicroseconds],
          scroll_offset:{frame_id:frameId,session_id:sessionId,value:indicators[0].value}}};
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
      ax:{version:1,focused_index:focusedIndex,elements},cards,
      boundary:{top:surface==='ALBUMS'&&scroll[0].value===0,bottom:surface==='ALBUMS'&&scroll[0].value===1},
      boundary_evidence:surface==='ALBUMS'?{version:1,frame_id:frameId,session_id:sessionId,source:'AX_SCROLLBAR',indicator_index:scroll[0].index,
        minimum:0,maximum:1,value:scroll[0].value}:{version:1,frame_id:frameId,session_id:sessionId,source:'NOT_APPLICABLE'},
      chooser_controls:{root_index:chooserRoot[0]?.index??null,path_field_index:surface==='FOLDER_CHOOSER'?pathFields[0]?.index??null:null,
        confirm_button_index:surface==='FOLDER_CHOOSER'?confirms[0]?.index??null:null,
        selected_leaf_index:surface==='FOLDER_CHOOSER'&&leaves.length===1?leaves[0].index:null}};
    const ref=await retain({artifact:{sourceBinding,analysis,raw_ocr:ocr,projected_node_ids:elements.map(e=>e.index)},
      kind:'native-cua-correlation',frameId});
    contexts.set(frameId,{analysis,reference:ref,sourceBinding});return analysis;
  }
  const analyzeVisualCardDiagnostic=args=>analyzeCapture(args,{visualCardDiagnostic:true});
  const analyzeScrollWitness=args=>analyzeCapture(args,{scrollWitness:true});
  return Object.freeze({beforeCapture,afterCapture,analyzeCapture,analyzeVisualCardDiagnostic,analyzeScrollWitness,contexts,native});
}
