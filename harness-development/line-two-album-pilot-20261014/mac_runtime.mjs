// Load in the real hosted cua_repl kernel. Construction never acquires LINE.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFile} from 'node:child_process';
import {createHash,randomUUID} from 'node:crypto';
import {createNavigationObserver,createAlbumSupportCallbacks} from '../../scripts/line_backup_cua_adapter.mjs';
import {runTwoAlbumPilot,runSingleAlbumPilot,runOneScrollProbe} from './two_album_entry.mjs';
import {createLiveAnalyzer,verifyNativePair} from './mac/analyzer.mjs';
import {createLiveClassifier} from './mac/classifier.mjs';
import {createChooserLocators} from './mac/chooser.mjs';
import {createProducerHook,createDownloadObserver} from './mac/producer.mjs';
import {createVisualDiagnosticObserver} from './mac/visual_diagnostic.mjs';

const BASE='harness-development/line-two-album-pilot-20261014';
const PRIVATE=BASE+'/private';
const SOURCE_ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const DECODER_SHA='1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf';
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
const center=b=>[Math.trunc(b[0]+b[2]/2),Math.trunc(b[1]+b[3]/2)];

// MENU56 pure locator helpers: fresh-frame structural checks only, no fabricated AX roles.
const ELLIPSIS={maxArea:16,maxSide:5,stackX:1,stackGap:1.5,pad:4,minSafe:3,minInterior:16};
const intersectsRect=(a,b)=>a[0]<b[0]+b[2]&&b[0]<a[0]+a[2]&&a[1]<b[1]+b[3]&&b[1]<a[1]+a[3];
const insideRect=(a,b)=>a[0]>=b[0]&&a[1]>=b[1]&&a[0]+a[2]<=b[0]+b[2]&&a[1]+a[3]<=b[1]+b[3];
const containsPoint=(p,b,m=0)=>p[0]>=b[0]-m&&p[1]>=b[1]-m&&p[0]<=b[0]+b[2]+m&&p[1]<=b[1]+b[3]+m;
const erodeRect=(r,margin)=>[r[0]+margin,r[1]+margin,r[2]-2*margin,r[3]-2*margin];
const centerOf=r=>[Math.trunc(r[0]+r[2]/2),Math.trunc(r[1]+r[3]/2)];

/** Pixel-structural album ellipsis locator. Dots come only from fresh detected components. */
export function locateAlbumEllipsis({visual,width,height,uncertaintyPx}){
  need(visual?.sourceSHA256&&visual.width===width&&visual.height===height,'ELLIPSIS_VISUAL_SOURCE_REQUIRED');
  const dots=visual.ellipsisComponents;
  need(Array.isArray(dots)&&dots.length>=3,'ACTUAL_PIXEL_DOTS_REQUIRED');
  for(const d of dots)need(Number.isFinite(d?.x)&&Number.isFinite(d?.y)&&Number.isInteger(d.area)
    &&Number.isInteger(d.width)&&Number.isInteger(d.height)&&d.area>0&&d.area<=ELLIPSIS.maxArea
    &&d.width<=ELLIPSIS.maxSide&&d.height<=ELLIPSIS.maxSide,'ELLIPSIS_COMPONENT_UNSUPPORTED');
  const sorted=[...dots].sort((a,b)=>a.y===b.y?a.x-b.x:a.y-b.y);
  const triples=[];
  for(let i=0;i+2<sorted.length;i+=1)triples.push([sorted[i],sorted[i+1],sorted[i+2]]);
  const eligible=[];
  for(const triple of triples){
    const [a,b,c]=triple;
    const maxX=Math.max(a.x,b.x,c.x),minX=Math.min(a.x,b.x,c.x);
    const g0=b.y-a.y,g1=c.y-b.y;
    if(!(g0>0&&Math.abs(g0-g1)<=ELLIPSIS.stackGap))continue;
    if(maxX-minX>ELLIPSIS.stackX)continue;
    const point=[Math.round(b.x),Math.round(b.y)];
    if(!insideRect([0,0,width,height],[0,0,width,height]))continue;
    if(!(point[0]>=0&&point[1]>=0&&point[0]<width&&point[1]<height))continue;
    if(!(point[1]<=0.09*height&&point[0]>=0.75*width))continue;
    eligible.push({triple,point,gap:(g0+g1)/2});
  }
  need(eligible.length===1,'ELLIPSIS_PIXEL_STRUCTURE_AMBIGUOUS');
  const chosen=eligible[0];
  const xs=chosen.triple.map(d=>d.x),ys=chosen.triple.map(d=>d.y);
  const raw=[Math.min(...xs)-ELLIPSIS.pad,Math.min(...ys)-ELLIPSIS.pad,
    Math.max(...xs)-Math.min(...xs)+2*ELLIPSIS.pad,Math.max(...ys)-Math.min(...ys)+2*ELLIPSIS.pad];
  const safe=[Math.max(0,raw[0]),Math.max(0,raw[1]),
    Math.min(width,raw[0]+raw[2])-Math.max(0,raw[0]),Math.min(height,raw[1]+raw[3])-Math.max(0,raw[1])];
  need(safe[2]>ELLIPSIS.minSafe&&safe[3]>ELLIPSIS.minSafe
    &&containsPoint(chosen.point,safe,0.5),'ELLIPSIS_SAFE_INTERIOR');
  const u=Number.isFinite(uncertaintyPx)?uncertaintyPx:2;
  const interior=erodeRect(safe,u+4);
  need(interior[2]>=ELLIPSIS.minInterior&&interior[3]>=ELLIPSIS.minInterior
    &&insideRect(interior,[0,0,width,height]),'ELLIPSIS_INTERIOR_UNPROVEN');
  return {point:chosen.point,bounds_px:safe,interior_bounds_px:interior,dot_spacing:chosen.gap,
    component_count:dots.length,evidence_kind:'PIXEL_STRUCTURE',uncertainty_px:u};
}

/** Fresh SCK/OCR Save All row with the measured SCK->CUA transform, eroded interior and a verified title close. */
export function locateSaveAllRow({envelope,width,height}){
  const native=envelope?.native,popup=envelope?.popup,saveAll=envelope?.save_all,mapping=envelope?.mapping;
  need(native?.bundle_id==='jp.naver.line.mac'&&Number.isInteger(native.pid)&&Number.isInteger(native.window_id)
    &&Number.isInteger(native.display_id)&&Array.isArray(native.cua_capture_bounds_points)
    &&native.cua_capture_bounds_points.length===4,'MENU_ROW_NATIVE_IDENTITY');
  need(Array.isArray(native.cua_capture_bounds_points)&&native.cua_capture_bounds_points[2]>0
    &&native.cua_capture_bounds_points[3]>0,'MENU_ROW_WINDOW_BOUNDS');
  need(mapping?.kind==='SCK_TO_CUA_LOCAL'&&Number.isFinite(mapping.backing_scale)&&mapping.backing_scale>0
    &&Array.isArray(mapping.cua_scale)&&mapping.cua_scale.length===2&&mapping.cua_scale.every(v=>Number.isFinite(v)&&v>0)
    &&Array.isArray(mapping.cua_offset_px)&&mapping.cua_offset_px.length===2&&mapping.cua_offset_px.every(Number.isFinite)
    &&Number.isFinite(envelope.uncertainty_px)&&envelope.uncertainty_px>=2,'MENU_ROW_TRANSFORM');
  need(popup&&Number.isInteger(popup.window_number)&&popup.window_number!==native.window_id
    &&Number.isInteger(popup.layer)&&popup.layer>0&&Array.isArray(popup.bounds_px)&&popup.bounds_px.length===4
    &&popup.bounds_px.every(Number.isFinite)&&popup.bounds_px[2]>0&&popup.bounds_px[3]>0
    &&Array.isArray(popup.cua_bounds_px)&&popup.cua_bounds_px.length===4&&popup.cua_bounds_px[2]>0
    &&popup.cua_bounds_px[3]>0,'MENU_ROW_POPUP_IDENTITY');
  need(['儲存全部','Save All'].includes(saveAll?.text)&&Array.isArray(saveAll.label_bounds_px)
    &&saveAll.label_bounds_px.length===4&&saveAll.label_bounds_px.every(Number.isFinite)
    &&saveAll.label_bounds_px[2]>0&&saveAll.label_bounds_px[3]>0
    &&Array.isArray(saveAll.cua_label_bounds_px)&&saveAll.cua_label_bounds_px.length===4
    &&saveAll.cua_label_bounds_px[2]>0&&saveAll.cua_label_bounds_px[3]>0,
    'MENU_ROW_SAVE_ALL_OCR');
  const toCuaLocal=(x,y)=>[x*mapping.cua_scale[0]/mapping.backing_scale+mapping.cua_offset_px[0],
    y*mapping.cua_scale[1]/mapping.backing_scale+mapping.cua_offset_px[1]];
  const popupCua=[...toCuaLocal(popup.bounds_px[0],popup.bounds_px[1]),
    popup.bounds_px[2]*mapping.cua_scale[0]/mapping.backing_scale,
    popup.bounds_px[3]*mapping.cua_scale[1]/mapping.backing_scale];
  const rowCua=[...toCuaLocal(saveAll.label_bounds_px[0],saveAll.label_bounds_px[1]),
    saveAll.label_bounds_px[2]*mapping.cua_scale[0]/mapping.backing_scale,
    saveAll.label_bounds_px[3]*mapping.cua_scale[1]/mapping.backing_scale];
  const drift=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
  need(drift(popupCua,popup.cua_bounds_px)<=1&&drift(rowCua,saveAll.cua_label_bounds_px)<=1,
    'MENU_ROW_TRANSFORM_DRIFT');
  popupCua.splice(0,4,...popup.cua_bounds_px);
  rowCua.splice(0,4,...saveAll.cua_label_bounds_px);
  const crop=[0,0,width,height];
  const inCrop=[Math.max(crop[0],popupCua[0]),Math.max(crop[1],popupCua[1]),
    Math.min(crop[0]+crop[2],popupCua[0]+popupCua[2])-Math.max(crop[0],popupCua[0]),
    Math.min(crop[1]+crop[3],popupCua[1]+popupCua[3])-Math.max(crop[1],popupCua[1])];
  need(inCrop[2]>0&&inCrop[3]>0,'MENU_ROW_POPUP_NOT_VISIBLE');
  const band=[Math.max(inCrop[0],rowCua[0]),Math.max(inCrop[1],rowCua[1]),
    Math.min(inCrop[0]+inCrop[2],rowCua[0]+rowCua[2])-Math.max(inCrop[0],rowCua[0]),
    Math.min(inCrop[1]+inCrop[3],rowCua[1]+rowCua[3])-Math.max(inCrop[1],rowCua[1])];
  need(band[2]>=ELLIPSIS.minInterior&&band[3]>=ELLIPSIS.minInterior,'MENU_ROW_LABEL_INTERSECTION');
  const safe=[band[0],band[1],Math.min(rowCua[0]+rowCua[2],inCrop[0]+inCrop[2])-band[0],
    Math.min(rowCua[1]+rowCua[3],inCrop[1]+inCrop[3])-band[1]];
  need(insideRect(safe,crop)&&insideRect(safe,popupCua)&&insideRect(safe,rowCua),'MENU_ROW_SAFE_INSIDE_CROP');
  const margin=envelope.uncertainty_px+4;
  const eroded=erodeRect(safe,margin);
  need(eroded[2]>=ELLIPSIS.minInterior&&eroded[3]>=ELLIPSIS.minInterior&&insideRect(eroded,crop),
    'MENU_ROW_SAFE_UNKNOWN');
  const closeInterior=erodeRect(rowCua,margin);
  need(closeInterior[2]>=ELLIPSIS.minInterior&&closeInterior[3]>=ELLIPSIS.minInterior
    &&insideRect(closeInterior,crop)&&intersectsRect(closeInterior,eroded),'MENU_CLOSE_INTERIOR_UNPROVEN');
  return {frameId:envelope.frame_id,layoutKey:null,label:saveAll.text,save_all:centerOf(eroded),
    menuBounds:popupCua,addressableBounds:crop,safeBounds:safe,saveAllBounds:rowCua,
    dismiss_point:centerOf(closeInterior),dismiss_bounds_px:closeInterior,
    popup_window_id:popup.window_number,popup_layer:popup.layer,uncertaintyPx:envelope.uncertainty_px,
    evidence_kind:'FRESH_SCK_OCR_TRANSFORM',menu_order:[saveAll.text],item_spacing:rowCua[3]};
}

const inside=(a,b,m=0)=>a[0]>=b[0]+m&&a[1]>=b[1]+m&&a[0]+a[2]<=b[0]+b[2]-m&&a[1]+a[3]<=b[1]+b[3]-m;
const intersects=(a,b)=>a[0]<b[0]+b[2]&&b[0]<a[0]+a[2]&&a[1]<b[1]+b[3]&&b[1]<a[1]+a[3];

function evidenceJSON(value){
  const marker='__PILOT_INT_'+randomUUID().replaceAll('-','')+'_';
  return JSON.stringify(value,(_k,v)=>typeof v==='bigint'?marker+v:v,2)
    .replace(new RegExp('"'+marker+'(-?\\d+)"','g'),'$1')+'\n';
}

async function realDirectory(absolute){
  need(path.isAbsolute(absolute)&&path.normalize(absolute)===absolute,'CANONICAL_PROJECT_ROOT_REQUIRED');
  let current=path.parse(absolute).root;
  for(const part of absolute.split(path.sep).filter(Boolean)){
    current=path.join(current,part);const st=await fs.lstat(current);
    need(st.isDirectory()&&!st.isSymbolicLink(),'NON_SYMLINK_DIRECTORY_REQUIRED');
  }
}

/** Exact, read-only component assembly; live admission remains in the existing CLI. */
export async function createMacRuntime({cua,projectRoot,pythonPath,dependencyPath,producerPath,decoderPath,
    owner,authorization=PRIVATE+'/project-grant.json',buildRecordPath}){
  need(cua?.computer?.target==='mac'&&typeof cua.getApp==='function'&&typeof cua.listApps==='function','REAL_HOSTED_MAC_REQUIRED');
  await realDirectory(projectRoot);
  need(typeof owner==='string'&&owner&&path.isAbsolute(pythonPath)&&path.isAbsolute(producerPath)
    &&path.isAbsolute(decoderPath)&&path.isAbsolute(dependencyPath),'PINNED_RUNTIME_PATHS_REQUIRED');
  need(authorization.startsWith(PRIVATE+'/')&&!authorization.split('/').includes('..'),'PROJECT_GRANT_PATH_REQUIRED');
  const config=JSON.parse(await fs.readFile(path.join(projectRoot,'config/line_backup_config.json'),'utf8'));
  need(config.app_identifier==='jp.naver.line.mac'&&config.max_albums_per_run===1,'PRODUCTION_CAP1_REQUIRED');
  need(hash(await fs.readFile(decoderPath))===DECODER_SHA,'DECODER_DRIFT');
  const build=JSON.parse(await fs.readFile(buildRecordPath,'utf8'));
  need(build.exit_code===0&&build.binary_sha256===hash(await fs.readFile(producerPath)),'BUILT_PRODUCER_REQUIRED');
  for(const [relative,digest] of Object.entries(build.sources))
    need(hash(await fs.readFile(path.join(SOURCE_ROOT,relative)))===digest,'NATIVE_SOURCE_BUILD_DRIFT');
  const rawCaptures=new Map();
  const io={readFile:fs.readFile,open:fs.open,readdir:fs.readdir,lstat:fs.lstat,realpath:fs.realpath,
    mkdirp:async absolute=>{
      const relative=path.relative(projectRoot,absolute);
      need(relative.startsWith(PRIVATE+'/')&&!relative.split(path.sep).includes('..'),'PRIVATE_WRITE_SCOPE');
      let current=projectRoot;
      for(const part of relative.split(path.sep)){
        current=path.join(current,part);
        try{await fs.mkdir(current,{mode:0o700});}catch(e){if(e.code!=='EEXIST')throw e;}
        const st=await fs.lstat(current);need(st.isDirectory()&&!st.isSymbolicLink(),'PRIVATE_DIRECTORY_IDENTITY');
      }
    },
    writeFile:async(absolute,raw)=>{
      need(path.relative(projectRoot,absolute).startsWith(PRIVATE+'/'),'PRIVATE_WRITE_SCOPE');
      const h=await fs.open(absolute,'wx',0o600);try{await h.writeFile(raw);await h.sync();}finally{await h.close();}
      need(hash(await fs.readFile(absolute))===hash(raw),'PRIVATE_READBACK');
    }};
  async function publish(raw,kind,frameId,suffix='bin'){
    need(raw.byteLength>0&&raw.byteLength<=16*1024*1024&&/^[0-9a-f]{64}$/.test(frameId),'RETAIN_BYTES_REQUIRED');
    const rel=PRIVATE+'/evidence/'+kind.replace(/[^a-z0-9-]/gi,'-')+'/'+frameId.slice(0,16)+'-'+randomUUID()+'.'+suffix;
    await io.mkdirp(path.dirname(path.join(projectRoot,rel)));await io.writeFile(path.join(projectRoot,rel),raw);
    return {path:rel,bytes:raw.byteLength,sha256:hash(raw)};
  }
  async function retain(p){
    if(p.receipt)return publish(Buffer.from(evidenceJSON(p.receipt)),'dispatch-receipt',p.frameId);
    if(p.artifact!==undefined)return publish(Buffer.from(evidenceJSON(p.artifact)),p.kind,p.frameId);
    need(p.screenshot instanceof Uint8Array&&typeof p.ax==='string'&&hash(p.screenshot)===p.frameId,'GENUINE_RETAINED_CAPTURE_REQUIRED');
    const pngSignature=[0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a];
    const isPng=p.screenshot.byteLength>=pngSignature.length
      &&pngSignature.every((byte,index)=>p.screenshot[index]===byte);
    const isJpeg=p.screenshot.byteLength>=3&&p.screenshot[0]===0xff
      &&p.screenshot[1]===0xd8&&p.screenshot[2]===0xff;
    need(isPng||isJpeg,'RETAIN_SCREENSHOT_FORMAT_UNSUPPORTED');
    const frame=await publish(p.screenshot,'cua-frames',p.frameId,isPng?'png':'jpg'),ax=await publish(Buffer.from(p.ax),'cua-ax',p.frameId);
    rawCaptures.set(p.frameId,{ax:p.ax,frame,axReference:ax});return {...frame,ax};
  }
  async function runProcess(argv,{timeoutMs=30000,cap=8*1024*1024}={}){
    need([producerPath,pythonPath].includes(argv[0]),'PINNED_EXECUTABLE_REQUIRED');
    return new Promise((resolve,reject)=>execFile(argv[0],argv.slice(1),{
      cwd:projectRoot,timeout:timeoutMs,maxBuffer:cap,
      env:{PATH:'/usr/bin:/bin:/usr/sbin:/sbin',PYTHONDONTWRITEBYTECODE:'1',PYTHONNOUSERSITE:'1',
        PYTHONPATH:path.join(SOURCE_ROOT,'src')+':'+dependencyPath}},(error,stdout,stderr)=>{
      if(error&&(error.killed||error.code==='ENOENT'))return reject(Object.assign(error,{code:'PROCESS_UNKNOWN_NO_REPLAY'}));
      resolve({status:error?error.code:0,stdout,stderr,reaped:true,stop_reason:null});
    }));
  }
  async function cli(operation,{authorization:grant=authorization,payload=null}={}){
    const argv=[pythonPath,'-B','-m','line_backup_batch.cli',operation,'--project-root',projectRoot];
    if(grant!==null)argv.push('--authorization',grant);
    if(payload!==null){
      const input=PRIVATE+'/inputs/'+randomUUID()+'.json';await io.mkdirp(path.join(projectRoot,PRIVATE+'/inputs'));
      await io.writeFile(path.join(projectRoot,input),Buffer.from(evidenceJSON(payload)));argv.push('--input',input);
    }
    const r=await runProcess(argv,{timeoutMs:operation==='finalize'?650000:30000});
    if(r.status!==0){let e;try{e=JSON.parse(r.stderr);}catch{e={code:'CLI_REFUSED',message:r.stderr};}
      throw Object.assign(Error(e.message),{code:e.code});}
    const response=JSON.parse(r.stdout);
    if(operation==='prepare'&&response.result?.status==='ALBUM_OPEN_READY'){
      chooser.destinationBaseline=await download.baseline({action:{...response.result,owner},owner,sessionId:owner,
        frameId:response.result.frame_id});
    }
    return response;
  }
  cli.bridge=(operation,{expected_token=null,data={}}={})=>cli(operation,{payload:expected_token===null?{data}:{expected_token,data}});
  // Read the real grant lazily: preparation must never invent live authority.
  const authority={get grantSha256(){need(grantDigest,'LIVE_GRANT_NOT_BOUND');return grantDigest;}};
  let grantDigest=null;
  const groupTitleAliases=[];
  async function bindLiveAuthority(){
    need(SOURCE_ROOT===projectRoot,'REVIEWED_SOURCE_INSTALLATION_REQUIRED');
    const raw=await fs.readFile(path.join(projectRoot,authorization));
    const grant=JSON.parse(raw);need(grant.owner===owner,'PROJECT_OWNER_MISMATCH');grantDigest=hash(raw);
    const authorized=await cli('native_authorize');
    if(grant.single_album_route===true){need(typeof authorized.display_title_alias==='string'
      &&authorized.display_title_alias&&authorized.display_title_alias!==config.group_name,'PROJECT_DISPLAY_TITLE_ALIAS_REQUIRED');
      groupTitleAliases.splice(0,groupTitleAliases.length,authorized.display_title_alias);}
    return grant;
  }
  const analyzer=createLiveAnalyzer({runProcess,binary:producerPath,repoRoot:projectRoot,retain,
    groupKey:config.group_key,groupTitle:config.group_name,groupTitleAliases,authorization,
    grantSha256:()=>authority.grantSha256,owner});
  // The producer and analyzer obtain the digest at use time, after genuine admission.
  const nativeAnalyzer=analyzer;
  const menuGeometry=new Map(),closureContext=new Map();let classifier;
  const producer=createProducerHook({io,runProcess,repoRoot:projectRoot,authorization,authority,retain,
    binary:{absolutePath:producerPath},geometryProvider:async({pairFrameId})=>{
      const g=menuGeometry.get(pairFrameId);need(g,'MENU_GEOMETRY_NOT_OBSERVED');return g;
    }});
  classifier=createLiveClassifier({retain,readRetained,analyzeCapture:nativeAnalyzer.analyzeCapture,
    analyzeScrollWitness:nativeAnalyzer.analyzeScrollWitness,
    analyzeVisualCardDiagnostic:nativeAnalyzer.analyzeVisualCardDiagnostic,
    analyzeMenuEnvelope:nativeAnalyzer.analyzeMenuEnvelope,groupKey:config.group_key,
    frameSupport:producer.frameSupport});
  async function decodeRetainedImage({bytes,sourceSha256}){
    need(bytes instanceof Uint8Array&&hash(bytes)===sourceSha256,'SCROLL_IMAGE_SOURCE_HASH');
    if(bytes[0]===137&&bytes[1]===80&&bytes[2]===78&&bytes[3]===71)
      return {sourceSha256,png:new Uint8Array(bytes),pngSha256:hash(bytes)};
    need(bytes[0]===255&&bytes[1]===216&&bytes[2]===255,'SCROLL_IMAGE_FORMAT_UNSUPPORTED');
    const relativeDirectory=PRIVATE+'/tmp/scroll-decode-'+randomUUID();
    const directory=path.join(projectRoot,relativeDirectory);
    await io.mkdirp(directory);
    const input=path.join(directory,'retained.jpg'),output=path.join(directory,'decoded.png');
    try{
      await fs.writeFile(input,bytes,{flag:'wx',mode:0o600});
      await new Promise((resolve,reject)=>execFile('/usr/bin/sips',['-s','format','png',input,'--out',output],
        {timeout:30000,maxBuffer:1024*1024,env:{PATH:'/usr/bin:/bin:/usr/sbin:/sbin'}},error=>error?reject(error):resolve()));
      const outputStat=await fs.stat(output);
      need(outputStat.size>0&&outputStat.size<=16*1024*1024,'SCROLL_IMAGE_DECODE_SIZE');
      const original=await fs.readFile(input),png=await fs.readFile(output);
      need(hash(original)===sourceSha256&&png.byteLength===outputStat.size
        &&png[0]===137&&png[1]===80&&png[2]===78&&png[3]===71,'SCROLL_IMAGE_DECODE_INVALID');
      return {sourceSha256,png:new Uint8Array(png),pngSha256:hash(png)};
    }finally{await fs.rm(directory,{recursive:true,force:true});}
  }
  const cached=frame=>{const c=classifier.cache.get(frame.frame_id);need(c?.observation,'FRESH_CLASSIFIER_FRAME_REQUIRED');return c;};
  const readRetained=async reference=>{
    const absolute=path.resolve(projectRoot,reference.path);
    need(path.relative(projectRoot,absolute).startsWith('harness-development/'),'RETAINED_READ_SCOPE');
    return new Uint8Array(await fs.readFile(absolute));
  };
  function menuTrigger(frame){
    const c=cached(frame),ctx=nativeAnalyzer.contexts.get(frame.frame_id)?.sourceBinding.after.value;
    need(ctx?.visual&&ctx.visual.sourceSHA256===frame.frame_id,'FRESH_VISUAL_SOURCE_REQUIRED');
    const geometry=locateAlbumEllipsis({visual:ctx.visual,width:c.observation.width,height:c.observation.height,
      uncertaintyPx:c.observation.mapping.uncertainty});
    return {frameId:frame.frame_id,layoutKey:frame.layout_key,point:geometry.point,bounds_px:geometry.bounds_px,
      interior_bounds_px:geometry.interior_bounds_px,dot_spacing:geometry.dot_spacing,
      evidence_kind:geometry.evidence_kind,component_count:geometry.component_count,uncertaintyPx:geometry.uncertainty_px};
  }
  function menuClosure({frame,detail,envelope}){
    need(frame?.frame_id&&detail?.window_id===frame.window_id&&frame.surface==='ALBUM_DETAIL','MENU_CLOSURE_FRAME');
    const ctx=nativeAnalyzer.contexts.get(frame.frame_id)?.sourceBinding.after.value;
    need(ctx?.visual?.sourceSHA256===frame.frame_id,'MENU_CLOSURE_VISUAL_SOURCE');
    const target=ctx.target;
    need(target?.pid===frame.pid&&target.startTimeSeconds===envelope.process_start[0]
      &&target.startTimeMicroseconds===envelope.process_start[1],'MENU_CLOSURE_PROCESS_INSTANCE_DRIFT');
    const popupOpen=[...ctx.onScreenWindows].some(w=>w.windowNumber===envelope.popup.window_number
      &&w.ownerPID===target.pid&&(w.cgLayer??0)===(envelope.popup.layer??null));
    need(popupOpen===false,'MENU_CLOSURE_POPUP_STILL_PRESENT');
    const rows=[...ctx.visual.ocr].filter(o=>['儲存全部','Save All'].includes(o.text)
      &&o.confidence>=.5&&o.candidateCount===1);
    need(rows.length===0,'MENU_CLOSURE_ROW_STILL_PRESENT');
    return {native_popup_absent:true,row_absent:true,process_instance:[target.startTimeSeconds,target.startTimeMicroseconds],
      detail_window_id:frame.window_id,popup_window_id:envelope.popup.window_number,
      popup_layer:envelope.popup.layer,evidence_kind:'NATIVE_WINDOW_ABSENCE_AND_FRESH_OCR'};
  }
  async function menuLocator(frame,{phase,detail}={}){
    if(phase==='TRIGGER')return menuTrigger(frame);
    if(phase==='CLOSURE'){
      need(detail?.window_id,'MENU_CLOSURE_DETAIL_REQUIRED');
      const bound=closureContext.get(detail.frame_id);
      need(bound?.envelope,'MENU_CLOSURE_ENVELOPE_REQUIRED');
      return menuClosure({frame,detail,envelope:bound.envelope});
    }
    need(phase==='ROW','MENU_PHASE_UNKNOWN');
    const record=classifier.menuEnvelopes.get(frame.frame_id);
    need(record?.envelope,'FRESH_MENU_ENVELOPE_REQUIRED');
    const envelope=record.envelope,c=cached(frame);
    need(envelope.session_id===frame.session_id&&envelope.native.window_id===frame.window_id
      &&envelope.detail_window_id===frame.window_id,'MENU_ENVELOPE_FRAME_BINDING');
    const row=locateSaveAllRow({envelope,width:c.observation.width,height:c.observation.height});
    row.layoutKey=frame.layout_key;
    need(row.frameId===frame.frame_id,'MENU_ROW_FRAME_BINDING');
    menuGeometry.set(frame.frame_id,{pid:envelope.native.pid,windowId:envelope.native.window_id,
      displayId:envelope.native.display_id,layoutKey:frame.layout_key,uncertaintyPx:row.uncertaintyPx,
      cuaBounds:envelope.native.cua_capture_bounds_points,menuBounds:row.menuBounds,
      addressableBounds:row.addressableBounds});
    // The closure check reads the fresh post-close frame against the detail frame that opened
    // this menu, so the calibration context is keyed by that fresh detail frame id.
    closureContext.set(detail.frame_id,{envelope,detail,menu_frame_id:frame.frame_id});
    return row;
  }
  const baseChooser=createChooserLocators(),download=createDownloadObserver({io,repoRoot:projectRoot,retain});
  const chooser={...baseChooser,
    locatePathField(envelope){
      const bound=baseChooser.locatePathField(envelope),raw=rawCaptures.get(envelope.frame.frame_id);
      need(raw,'HOSTED_CHOOSER_AX_REQUIRED');
      const matches=raw.ax.split('\n').map(line=>/^\s*(\d+)\s+(?:文字欄位|text field|TextField).*\(settable\)/i.exec(line)).filter(Boolean);
      need(matches.length===1,'HOSTED_SETTABLE_PATH_INDEX_AMBIGUOUS');
      return {...bound,index:Number(matches[0][1])};
    },
    refreshBaseline:args=>download.baseline({action:{...args.action,frame_id:args.frameId},owner,sessionId:owner,frameId:args.frameId}),
    observeDownload:args=>download.observe(args)};
  const navigation={
    locateBack:async frame=>{
      const c=cached(frame),buttons=c.axSnapshot.elements.filter(e=>e.role==='button'&&e.enabled&&['返回','上一頁','Back'].includes(e.label));
      need(buttons.length===1,'BACK_CONTROL_AMBIGUOUS');return {frameId:frame.frame_id,role:'button',point:center(buttons[0].bounds_px)};
    },
    scrollTarget:async frame=>{
      const scroll=classifier.scrollCache.get(frame.frame_id);
      if(scroll){
        const w=scroll.analysis.scroll_witness,viewport=w.viewport_bounds,elements=scroll.axSnapshot.elements;
        need(frame.surface==='ALBUMS'&&frame.occlusion==='CLEAR'&&frame.editable_focus==='NONE'
          &&frame.window_id===scroll.analysis.native.window_id&&frame.pid===scroll.analysis.native.pid
          &&frame.group_key===scroll.analysis.group_key,
          'SCROLL_VIEWPORT_CONTEXT');
        const lists=elements.filter(e=>e.role==='list'&&e.index===w.viewport_ax_index
          &&JSON.stringify(e.bounds_px)===JSON.stringify(viewport));
        need(lists.length===1&&viewport[2]>=64&&viewport[3]>=64
          &&w.rows.length>0&&w.rows.every(row=>row.identity_visible===true)
          &&Number.isFinite(frame.mapping?.uncertainty)&&frame.mapping.uncertainty<=2,
          'SCROLL_VIEWPORT_UNSAFE');
        const margin=frame.mapping.uncertainty+4;
        const safe=[viewport[0]+margin,viewport[1]+margin,viewport[2]-2*margin,viewport[3]-2*margin];
        need(safe[2]>=32&&safe[3]>=32,'SCROLL_VIEWPORT_SAFE_AREA');
        const target=center(safe),targetRect=[target[0]-2,target[1]-2,4,4];
        const controls=elements.filter(e=>['button','text field'].includes(e.role)&&e.enabled);
        need(!controls.some(e=>intersects(targetRect,e.bounds_px)),'SCROLL_TARGET_CONTROL_OVERLAP');
        return target;
      }
      const c=cached(frame);need(frame.surface==='ALBUMS'&&frame.occlusion==='CLEAR'&&frame.editable_focus==='NONE','SCROLL_SURFACE_UNSAFE');
      const areas=c.axSnapshot.elements.filter(e=>e.role==='scroll area'&&frame.cards.every(card=>inside(card.metadata_bounds,e.bounds_px)));
      need(areas.length===1,'ACTUAL_SCROLL_VIEWPORT_REQUIRED');return center(areas[0].bounds_px);
    }};
  async function windowLineage({kind,before,after,prepared,from,to,expectedList}){
    if(kind==='DETAIL_RETURN_TO_LIST'){
      need(to.window_id===expectedList.window_id,'RETURN_WINDOW_LINEAGE_UNPROVEN');return null;
    }
    need(kind==='ALBUM_CARD_OPEN_DETAIL','WINDOW_LINEAGE_KIND');
    const a=nativeAnalyzer.contexts.get(before.frame_id),b=nativeAnalyzer.contexts.get(after.frame_id);
    need(a&&b&&after.detail_identity?.kind==='ALBUM_DETAIL_GRID'
      &&JSON.stringify(after.detail_identity.fingerprint)===JSON.stringify(prepared.fingerprint)
      &&after.detail_identity.list_frame_id===before.frame_id&&after.detail_identity.list_window_id===before.window_id
      &&after.detail_identity.detail_window_id===after.window_id&&after.detail_identity.pid===after.pid,
      'DETAIL_LINEAGE_IDENTITY');
    verifyNativePair(a.sourceBinding.after.value,b.sourceBinding.after.value);
    const old=a.sourceBinding.after.value,newer=b.sourceBinding.after.value;
    need(!old.windows.some(w=>w.windowNumber===after.window_id)&&newer.windows.some(w=>w.windowNumber===before.window_id)
      &&newer.focusedWindowID===after.window_id,'NEW_DETAIL_WINDOW_NOT_PROVEN');
    const proof={relationship:kind,from_window_id:before.window_id,to_window_id:after.window_id,list_frame_id:before.frame_id,
      before:a.reference,after:b.reference};await retain({artifact:proof,kind:'window-lineage',frameId:after.frame_id});return proof;
  }
  const privateEvidence={
    leaseCloseReference:async runId=>{
      need(/^[A-Za-z0-9_-]+$/.test(runId),'RUN_ID_SCOPE');const rel=PRIVATE+'/lease-close-'+runId+'.json';
      const raw=await fs.readFile(path.join(projectRoot,rel)),value=JSON.parse(raw);
      need(value.run_id===runId&&value.state==='CLOSED','VERIFIED_LEASE_CLOSE_REQUIRED');return {path:rel,bytes:raw.length,sha256:hash(raw)};
    },
    retainC1:value=>retain({artifact:value,kind:'c1',frameId:hash(Buffer.from(evidenceJSON(value)))}),
    retainDiscovery:value=>retain({artifact:value,kind:'discovery',frameId:hash(Buffer.from(evidenceJSON(value)))}),
    retainFailure:value=>retain({artifact:value,kind:'failure',frameId:hash(Buffer.from(evidenceJSON(value)))})};
  async function assertLineAlreadyRunning(){
    const apps=await cua.listApps({emit:false});need(apps.filter(a=>a.id==='jp.naver.line.mac'&&a.isRunning===true).length===1,'OWNER_MUST_START_LINE');
  }
  const supportCallbacks=createAlbumSupportCallbacks({invokeProducer:producer.invokeProducer});
  let visualCardDiagnosticUsed=false;
  const runtime={profile:'LINE_TWO_ALBUM_PILOT/1',owner,authorization,decoder:{path:decoderPath,sha256:DECODER_SHA},
    one56Fingerprint:{start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56},
    cli,retain,classifier,classifyScrollWitness:classifier.classifyScrollWitness,decodeRetainedImage,
    producer:{...producer,...supportCallbacks},menuLocator,chooser,navigation,windowLineage,privateEvidence,clock:()=>performance.now(),
    beforeCapture:nativeAnalyzer.beforeCapture,afterCapture:nativeAnalyzer.afterCapture,assertLineAlreadyRunning,
    getApp:async id=>{await bindLiveAuthority();await assertLineAlreadyRunning();need(id==='jp.naver.line.mac','LINE_SCOPE');return cua.getApp(id);}};
  return Object.freeze({runtime,
    readOnlyPreflight:async()=>{
      const native=await runProcess([producerPath,'runtime-preflight']);need(native.status===0,'NATIVE_PREFLIGHT_FAILED');
      return {native:JSON.parse(native.stdout),sourceRoot:SOURCE_ROOT,projectRoot,
        sourceInstalled:SOURCE_ROOT===projectRoot,grantPresent:await fs.stat(path.join(projectRoot,authorization)).then(()=>true,()=>false),
        callbacks:['cli.bridge','retain','classifier.classify','classifier.classifyChooser','producer.frameSupport',
          'producer.captureMenuSupport','producer.guardMenu','chooser','navigation','windowLineage','beforeCapture','afterCapture','privateEvidence'],
        guiInputs:0,lineAcquired:false,ledgerInitialized:false};
    },
    observeG1:async()=>{
      await bindLiveAuthority();await assertLineAlreadyRunning();const app=await runtime.getApp('jp.naver.line.mac');
      const observer=createNavigationObserver({app,bridge:cli.bridge,retain,classify:classifier.classify,
        beforeCapture:runtime.beforeCapture,afterCapture:runtime.afterCapture,sessionId:owner});
      try{return await observer.observe('G1_READ_ONLY');}finally{observer.close();}
    },
    observeVisualCardDiagnostic:async()=>{
      need(!visualCardDiagnosticUsed,'VISUAL_DIAGNOSTIC_ALREADY_USED');visualCardDiagnosticUsed=true;
      try {
        const grant=await bindLiveAuthority();
        need(Array.isArray(grant.operations)&&grant.operations.length===1
          &&grant.operations[0]==='gui_observe','VISUAL_DIAGNOSTIC_GRANT_SCOPE');
        await assertLineAlreadyRunning();
        const app=await cua.getApp('jp.naver.line.mac');
        const observer=createVisualDiagnosticObserver({app,retain,readClock:producer.readVisualDiagnosticClock,
          beforeCapture:runtime.beforeCapture,
          capturePair:producer.captureVisualDiagnostic,afterCapture:runtime.afterCapture,
          analyze:args=>classifier.completeVisualCardDiagnostic({...args,
            analyzePixels:producer.analyzeVisualDiagnostic}),sessionId:owner});
        return await observer.observe();
      } catch(error) {
        const evidence={kind:'VISUAL_CARD_DIAGNOSTIC_FAILURE',session_id:owner,
          error:{code:error.code??null,message:String(error.message??error)}};
        try{await retain({artifact:evidence,kind:'visual-card-diagnostic-failure',
          frameId:hash(Buffer.from(evidenceJSON(evidence)))});}
        catch(retentionError){error.diagnosticRetentionError=String(retentionError.message??retentionError);}
        throw error;
      }
    },
    runOneScrollProbe:async()=>{await bindLiveAuthority();return runOneScrollProbe(runtime);},
    runPilot:async()=>{await bindLiveAuthority();return runTwoAlbumPilot(runtime);},
    runSingleAlbumPilot:async()=>{await bindLiveAuthority();return runSingleAlbumPilot(runtime);}});
}
