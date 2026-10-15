// Load in the real hosted cua_repl kernel. Construction never acquires LINE.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFile} from 'node:child_process';
import {createHash,randomUUID} from 'node:crypto';
import {createNavigationObserver,createAlbumSupportCallbacks} from '../../scripts/line_backup_cua_adapter.mjs';
import {runTwoAlbumPilot} from './two_album_entry.mjs';
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
const inside=(a,b,m=0)=>a[0]>=b[0]+m&&a[1]>=b[1]+m&&a[0]+a[2]<=b[0]+b[2]-m&&a[1]+a[3]<=b[1]+b[3]-m;

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
  async function bindLiveAuthority(){
    need(SOURCE_ROOT===projectRoot,'REVIEWED_SOURCE_INSTALLATION_REQUIRED');
    const raw=await fs.readFile(path.join(projectRoot,authorization));
    const grant=JSON.parse(raw);need(grant.owner===owner,'PROJECT_OWNER_MISMATCH');grantDigest=hash(raw);
    await cli('native_authorize');return grant;
  }
  const analyzer=createLiveAnalyzer({runProcess,binary:producerPath,repoRoot:projectRoot,retain,
    groupKey:config.group_key,groupTitle:config.group_name,authorization,
    grantSha256:()=>authority.grantSha256,owner});
  // The producer and analyzer obtain the digest at use time, after genuine admission.
  const nativeAnalyzer=analyzer;
  const menuGeometry=new Map();let classifier;
  const producer=createProducerHook({io,runProcess,repoRoot:projectRoot,authorization,authority,retain,
    binary:{absolutePath:producerPath},geometryProvider:async({pairFrameId})=>{
      const g=menuGeometry.get(pairFrameId);need(g,'MENU_GEOMETRY_NOT_OBSERVED');return g;
    }});
  classifier=createLiveClassifier({retain,analyzeCapture:nativeAnalyzer.analyzeCapture,
    analyzeVisualCardDiagnostic:nativeAnalyzer.analyzeVisualCardDiagnostic,groupKey:config.group_key,
    frameSupport:producer.frameSupport});
  const cached=frame=>{const c=classifier.cache.get(frame.frame_id);need(c?.observation,'FRESH_CLASSIFIER_FRAME_REQUIRED');return c;};
  function ellipsis(frame){
    const c=cached(frame),ctx=nativeAnalyzer.contexts.get(frame.frame_id)?.sourceBinding.after.value;
    const dots=ctx?.visual?.ellipsisComponents;need(Array.isArray(dots),'ACTUAL_PIXEL_DOTS_REQUIRED');
    const matches=[];
    for(const button of c.axSnapshot.elements.filter(e=>e.role==='button'&&e.enabled)){
      const ds=dots.filter(d=>inside([d.x,d.y,1,1],button.bounds_px)).sort((a,b)=>a.y-b.y);
      if(ds.length!==3)continue;const d0=ds[1].y-ds[0].y,d1=ds[2].y-ds[1].y;
      if(d0>0&&Math.abs(d0-d1)<=1&&Math.max(...ds.map(d=>d.x))-Math.min(...ds.map(d=>d.x))<=1)
        matches.push({point:[Math.round(ds[1].x),Math.round(ds[1].y)],frameId:frame.frame_id,role:'button',
          bounds_px:button.bounds_px,dot_spacing:(d0+d1)/2});
    }
    need(matches.length===1,'ELLIPSIS_PIXEL_AX_AMBIGUOUS');return matches[0];
  }
  async function menuLocator(frame,{phase}){
    const c=cached(frame);if(phase==='TRIGGER')return ellipsis(frame);
    need(phase==='ROW','MENU_PHASE_UNKNOWN');
    const rows=c.axSnapshot.elements.filter(e=>e.role==='menu item'&&e.enabled).sort((a,b)=>a.bounds_px[1]-b.bounds_px[1]);
    const selected=rows.filter(e=>['儲存全部','Save All'].includes(e.label));need(selected.length===1&&rows.length>1,'OBSERVED_SAVE_ALL_REQUIRED');
    const row=selected[0],u=c.observation.mapping.uncertainty,m=u+4,b=row.bounds_px;
    const safe=[b[0]+m,b[1]+m,b[2]-2*m,b[3]-2*m];need(safe[2]>=16&&safe[3]>=16,'MENU_ROW_SAFE_MARGIN');
    const x=Math.min(...rows.map(e=>e.bounds_px[0])),y=Math.min(...rows.map(e=>e.bounds_px[1]));
    const bounds=[x,y,Math.max(...rows.map(e=>e.bounds_px[0]+e.bounds_px[2]))-x,Math.max(...rows.map(e=>e.bounds_px[1]+e.bounds_px[3]))-y];
    const trigger=ellipsis(frame),a=c.analysis,n=a.native;
    const result={frameId:frame.frame_id,layoutKey:frame.layout_key,label:row.label,save_all:center(safe),
      menuBounds:bounds,addressableBounds:a.surface_bounds_px,safeBounds:safe,ellipsisBounds:trigger.bounds_px,
      saveAllBounds:b,menu_order:rows.map(e=>e.label),item_spacing:rows[1].bounds_px[1]-rows[0].bounds_px[1]};
    menuGeometry.set(frame.frame_id,{pid:n.pid,windowId:n.window_id,displayId:n.display_id,layoutKey:frame.layout_key,
      uncertaintyPx:u,cuaBounds:n.cua_capture_bounds_points,menuBounds:bounds,addressableBounds:a.surface_bounds_px});return result;
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
    need(a&&b&&after.cards.length===1&&JSON.stringify(after.cards[0].fingerprint)===JSON.stringify(prepared.fingerprint),'DETAIL_LINEAGE_IDENTITY');
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
    cli,retain,classifier,producer:{...producer,...supportCallbacks},menuLocator,chooser,navigation,windowLineage,privateEvidence,clock:()=>performance.now(),
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
        const observer=createVisualDiagnosticObserver({app,retain,beforeCapture:runtime.beforeCapture,
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
    runPilot:async()=>{await bindLiveAuthority();return runTwoAlbumPilot(runtime);}});
}
