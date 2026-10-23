// Continuation runner for the reviewed two-album live workflow.
// Load it only in the documented persistent CUA kernel and pass a genuine App object.
// It does not import a GUI SDK or synthesize screenshots; all input goes through the adapter.
import {createHash, randomUUID} from 'node:crypto';
import path from 'node:path';
import {createLiveClassifier} from './live_classifier.mjs';
import {createChooserLocators} from './chooser_locators.mjs';

const REL='harness-development/line-v3-live-e2e-20261010';
const CON=`${REL}/continuations/live-grounding-03`;
const decoderPath=`${REL}/bin/image_decode`;
const decoderSha256='1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf';
const contractPath=`${CON}/plan-contract.json`;
const contractSha256='d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219';
const encoder=new TextEncoder();
const decoder=new TextDecoder();
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const isHash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(ok,code)=>{if(!ok)fail(code);};
const nowISO=()=>new Date().toISOString();
const safeRel=value=>typeof value==='string'&&value.startsWith(`${REL}/`)
  &&!value.split('/').some(part=>part==='.'||part==='..');
const refShape=value=>value&&Object.keys(value).sort().join(',')==='bytes,path,sha256'
  &&safeRel(value.path)&&Number.isInteger(value.bytes)&&value.bytes>0&&isHash(value.sha256);

function canonicalJSON(value) {
  if(Array.isArray(value))return `[${value.map(canonicalJSON).join(',')}]`;
  if(value&&typeof value==='object')return `{${Object.keys(value).sort()
    .map(key=>`${JSON.stringify(key)}:${canonicalJSON(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}

function evidenceJSON(value,space=0) {
  const marker=`__LINE_BACKUP_BIGINT_${randomUUID().replaceAll('-','')}_`;
  return JSON.stringify(value,(_key,item)=>typeof item==='bigint'?`${marker}${item}`:item,space)
    .replace(new RegExp(`"${marker}(-?\\d+)"`,'g'),'$1');
}

async function readBounded(io,file,cap=16*1024*1024) {
  need(typeof io?.open==='function','BOUNDED_FILE_READER_REQUIRED');
  const handle=await io.open(file,'r');
  try {
    const initial=await handle.stat();
    need(initial.isFile()&&Number.isSafeInteger(initial.size)&&initial.size>=0&&initial.size<=cap,
      'ARTIFACT_SIZE_LIMIT');
    const chunks=[];let total=0;
    while(total<=cap) {
      const buffer=new Uint8Array(Math.min(65536,cap+1-total));
      const {bytesRead}=await handle.read(buffer,0,buffer.byteLength,total);
      if(bytesRead===0)break;
      chunks.push(buffer.slice(0,bytesRead));total+=bytesRead;
    }
    need(total<=cap,'ARTIFACT_SIZE_LIMIT');
    const after=await handle.stat();
    need(after.isFile()&&after.size===initial.size&&total===initial.size,'ARTIFACT_CHANGED_DURING_READ');
    const raw=new Uint8Array(total);let offset=0;
    for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.byteLength;}
    return raw;
  } finally {await handle.close();}
}

async function readVerified(io,root,ref,code='ARTIFACT_DRIFT',cap=16*1024*1024) {
  need(refShape(ref),code);
  const raw=await readBounded(io,path.join(root,ref.path),cap);
  need(raw instanceof Uint8Array&&raw.byteLength===ref.bytes&&raw.byteLength<=cap&&sha256(raw)===ref.sha256,code);
  return raw;
}

async function runtimeGate({io,repoRoot,authorization,pythonBin}) {
  need(typeof authorization==='string'&&safeRel(authorization),'GRANT_PATH_UNSAFE');
  need(path.isAbsolute(pythonBin)&&typeof io.realpath==='function','PYTHON_RUNTIME_PREFLIGHT_UNAVAILABLE');
  const grantRaw=await readBounded(io,path.join(repoRoot,authorization));
  const grant=JSON.parse(decoder.decode(grantRaw));
  need(grant.grant_version==='line-batch-execution-grant-2'&&grant.fixture===false
    &&grant.project_root===repoRoot&&grant.artifact_dir===CON,'GRANT_V2_REQUIRED');
  need(grant.contract_path===contractPath&&grant.contract_sha256===contractSha256
    &&grant.native_binary_sha256===decoderSha256,'GRANT_CONTRACT_BINDING');
  const contractRaw=await readBounded(io,path.join(repoRoot,contractPath));
  need(sha256(contractRaw)===contractSha256,'GRANT_CONTRACT_DRIFT');
  const runtimeRaw=await readVerified(io,repoRoot,grant.runtime_binding,'RUNTIME_BINDING_DRIFT');
  const runtime=JSON.parse(decoder.decode(runtimeRaw));
  need(Object.keys(runtime).sort().join(',')==='contract_path,contract_sha256,files,memberships,project_root,source_sha256,task_id,version'
    &&runtime.version===1&&runtime.task_id===grant.task_id&&runtime.project_root===repoRoot
    &&runtime.contract_path===contractPath&&runtime.contract_sha256===contractSha256
    &&runtime.source_sha256===grant.source_sha256,
    'RUNTIME_BINDING_MISMATCH');
  const realPython=await io.realpath(pythonBin);
  need(path.isAbsolute(realPython)&&pythonBin===realPython,'PYTHON_RUNTIME_PATH_UNRESOLVED');
  const pythonEntry=runtime.files?.find(item=>item.path===realPython&&item.member_of?.includes('python_runtime'));
  need(pythonEntry&&Number.isInteger(pythonEntry.bytes)&&isHash(pythonEntry.sha256),'PYTHON_RUNTIME_NOT_BOUND');
  const pythonBytes=await readBounded(io,realPython);
  need(pythonBytes.byteLength===pythonEntry.bytes&&sha256(pythonBytes)===pythonEntry.sha256,
    'PYTHON_RUNTIME_DRIFT');
  const producer=grant.producer_binary;
  need(refShape(producer)&&producer.path===`${CON}/bin/rev28ctl`,'PRODUCER_BINARY_BINDING');
  const producerRaw=await readBounded(io,path.join(repoRoot,producer.path));
  need(producerRaw.byteLength===producer.bytes&&sha256(producerRaw)===producer.sha256,
    'PRODUCER_BINARY_DRIFT');
  const decoderRaw=await readBounded(io,path.join(repoRoot,decoderPath));
  need(sha256(decoderRaw)===decoderSha256,'DECODER_BINARY_DRIFT');
  const memberships=runtime.memberships;
  const membershipKeys=['product_sources_21','task_modules','swift_sources','package_manifest','python_runtime','producer_binary'];
  need(memberships&&Object.keys(memberships).sort().join(',')===membershipKeys.slice().sort().join(','),
    'RUNTIME_MEMBERSHIP_DRIFT');
  const products=memberships.product_sources_21;
  const expectedTaskModules=['scripts/line_backup_cua_adapter.mjs',`${CON}/live_runner.mjs`,
    `${CON}/live_classifier.mjs`,`${CON}/chooser_locators.mjs`].sort();
  need(Array.isArray(products)&&products.length===21&&new Set(products).size===21
    &&products.every(safeRepoPath)&&Array.isArray(memberships.task_modules)
    &&JSON.stringify(memberships.task_modules)===JSON.stringify(expectedTaskModules)
    &&JSON.stringify(memberships.package_manifest)===JSON.stringify(['rev28/Package.swift'])
    &&JSON.stringify(memberships.python_runtime)===JSON.stringify([realPython])
    &&JSON.stringify(memberships.producer_binary)===JSON.stringify([producer.path]),'RUNTIME_MEMBERSHIP_DRIFT');
  const runtimeFiles=runtime.files;
  need(Array.isArray(runtimeFiles)&&runtimeFiles.length>0,'RUNTIME_FILE_INVENTORY_REQUIRED');
  const boundPaths=new Set();
  const expectedMembers=new Map();
  for(const [group,paths] of Object.entries(memberships)) {
    need(Array.isArray(paths)&&new Set(paths).size===paths.length,'RUNTIME_MEMBERSHIP_DRIFT');
    for(const filePath of paths) {
      need(typeof filePath==='string'&&(path.isAbsolute(filePath)?filePath===realPython:safeRepoPath(filePath)),
        'RUNTIME_FILE_PATH_UNSAFE');
      if(!expectedMembers.has(filePath))expectedMembers.set(filePath,new Set());
      expectedMembers.get(filePath).add(group);
    }
  }
  need(runtimeFiles.length===expectedMembers.size,'RUNTIME_CLOSURE_INCOMPLETE');
  for(const entry of runtimeFiles) {
    need(entry&&Object.keys(entry).sort().join(',')==='bytes,member_of,path,sha256'
      &&typeof entry.path==='string'&&Number.isInteger(entry.bytes)&&entry.bytes>0
      &&isHash(entry.sha256)&&Array.isArray(entry.member_of)&&entry.member_of.length>0
      &&entry.member_of.every(value=>typeof value==='string'&&value.length>0)
      &&!boundPaths.has(entry.path)&&JSON.stringify(entry.member_of.slice().sort())
        ===JSON.stringify([...(expectedMembers.get(entry.path)??[])].sort()),'RUNTIME_FILE_ENTRY_INVALID');
    boundPaths.add(entry.path);
    const file=path.isAbsolute(entry.path)?entry.path:path.join(repoRoot,entry.path);
    if(!path.isAbsolute(entry.path))need(safeRepoPath(entry.path),'RUNTIME_FILE_PATH_UNSAFE');
    if(entry.path===realPython||entry.path===producer.path)continue;
    const bytes=await readBounded(io,file);
    need(bytes.byteLength===entry.bytes&&sha256(bytes)===entry.sha256,'RUNTIME_SOURCE_DRIFT');
  }
  for(const required of ['scripts/line_backup_cua_adapter.mjs',`${CON}/live_runner.mjs`,
      `${CON}/live_classifier.mjs`,`${CON}/chooser_locators.mjs`])
    need(boundPaths.has(required),'RUNTIME_SOURCE_NOT_BOUND');
  need(boundPaths.has(realPython),'PYTHON_RUNTIME_NOT_IN_CLOSURE');
  const producerEntry=runtimeFiles.find(item=>item.path===producer.path);
  need(producerEntry&&producerEntry.bytes===producer.bytes&&producerEntry.sha256===producer.sha256,
    'PRODUCER_NOT_IN_RUNTIME_CLOSURE');
  const swiftRoots=['rev28/Sources/Rev28Core','rev28/Sources/rev28ctl'];
  async function collectSwift(root) {
    const entries=await io.readdir(path.join(repoRoot,root),{withFileTypes:true});
    const paths=[];
    for(const item of entries) {
      const relative=`${root}/${item.name}`;
      if(item.isDirectory())paths.push(...await collectSwift(relative));
      else if(item.isFile()&&item.name.endsWith('.swift'))paths.push(relative);
    }
    return paths;
  }
  const currentSwift=[];
  for(const root of swiftRoots)currentSwift.push(...await collectSwift(root));
  currentSwift.sort();
  need(JSON.stringify(memberships.swift_sources)===JSON.stringify(currentSwift),'RUNTIME_SWIFT_INVENTORY_DRIFT');
  for(const required of currentSwift)
    need(boundPaths.has(required),'RUNTIME_SWIFT_INVENTORY_INCOMPLETE');
  need(boundPaths.has('rev28/Package.swift'),'RUNTIME_PACKAGE_NOT_BOUND');
  return Object.freeze({grant,grantSha256:sha256(grantRaw),runtime,runtimeSha256:sha256(runtimeRaw),
    producer:Object.freeze({...producer,absolutePath:path.join(repoRoot,producer.path)}),pythonPath:realPython});
}

function safeRepoPath(value) {
  return typeof value==='string'&&value.length>0&&!path.isAbsolute(value)
    &&!value.split('/').some(part=>!part||part==='.'||part==='..');
}

export function createCli({io,runProcess,repoRoot,pythonBin,authorization}) {
  need(typeof runProcess==='function'&&typeof io?.readFile==='function'&&typeof io?.writeFile==='function',
    'CLI_BRIDGE_REQUIRED');
  const state={lastToken:null};let gatePromise=null;let counter=0;
  const nonce=label=>`${label}-${Date.now().toString(36)}-${(++counter).toString(36)}-${randomUUID()}`;
  async function gate() {
    if(!gatePromise)gatePromise=runtimeGate({io,repoRoot,authorization,pythonBin});
    return gatePromise;
  }
  async function cli(operation,{authorization:callAuthorization=authorization,payload=null}={}) {
    await gate();
    const argv=[pythonBin,'-B','-m','line_backup_batch.cli',operation,'--project-root',repoRoot];
    if(callAuthorization!==null)argv.push('--authorization',callAuthorization);
    if(payload!==null) {
      need(typeof io.mkdirp==='function','CLI_INPUT_STORAGE_REQUIRED');
      const inputRel=`${CON}/inputs/${nonce(operation)}.json`;
      await io.mkdirp(path.join(repoRoot,`${CON}/inputs`));
      const raw=encoder.encode(evidenceJSON(payload));
      await io.writeFile(path.join(repoRoot,inputRel),raw);
      argv.push('--input',inputRel);
    }
    const env={PYTHONPATH:'src',PYTHONDONTWRITEBYTECODE:'1'};
    if(Object.hasOwn(process.env,'CI'))env.CI=process.env.CI;
    const result=await runProcess(argv,{cwd:repoRoot,env});
    if(result?.status!==0) {
      let code=result?.status===4?'CLI_REFUSED':'CLI_PROCESS_FAILURE';let message=String(result?.stderr??'').trim();
      try {const parsed=JSON.parse(result.stderr);code=parsed.code||code;message=parsed.message||message;} catch {}
      throw Object.assign(new Error(`${operation}: ${message}`),{code});
    }
    let parsed;try {parsed=JSON.parse(result.stdout);}catch{fail('CLI_STDOUT_UNPARSEABLE');}
    if(typeof parsed.receipt_token==='string')state.lastToken=parsed.receipt_token;
    return parsed;
  }
  async function bridge(operation,{expected_token=null,data={}}={}) {
    if(operation==='gui_reserve'||operation==='gui_consume') {
      const result=await cli(operation,{payload:expected_token===null?{data}:{expected_token,data}});
      return result;
    }
    if(operation==='intent') {
      const parsed=await cli(operation,{payload:{expected_token,data}});
      need(parsed.new_intent===true&&parsed.result?.status==='ORIGINAL_INTENT_COMMITTED','INTENT_SHAPE');
      return {new_intent:true,receipt_token:parsed.receipt_token,result:parsed.result};
    }
    if(operation==='dispatch') {
      const parsed=await cli(operation,{payload:{expected_token,data}});
      need(parsed.result&&typeof parsed.result.status==='string','DISPATCH_SHAPE');
      return {receipt_token:parsed.receipt_token,result:parsed.result};
    }
    fail('BRIDGE_OPERATION_UNKNOWN');
  }
  return Object.assign(cli,{bridge,state,preflight:gate});
}

export function createRetain({io,repoRoot}) {
  need(['readFile','writeFile','mkdirp'].every(key=>typeof io?.[key]==='function'),'RETAIN_STORAGE_REQUIRED');
  let counter=0;
  async function publish(raw,kind,frameId) {
    need(raw instanceof Uint8Array&&raw.byteLength>0&&raw.byteLength<=16*1024*1024
      &&isHash(frameId),'RETAIN_ARTIFACT_SHAPE');
    const safeKind=kind.replace(/[^a-z0-9-]/gi,'-').toLowerCase();
    const directory=`${CON}/evidence/${safeKind}`;await io.mkdirp(path.join(repoRoot,directory));
    const file=`${frameId.slice(0,16)}-${(++counter).toString(36)}-${randomUUID()}.bin`;
    const rel=`${directory}/${file}`;await io.writeFile(path.join(repoRoot,rel),raw);
    const readback=await io.readFile(path.join(repoRoot,rel));
    need(readback.byteLength===raw.byteLength&&sha256(readback)===sha256(raw),'RETAIN_READBACK');
    return {path:rel,bytes:raw.byteLength,sha256:sha256(raw)};
  }
  return async function retain(payload) {
    if(payload?.receipt) {
      need(payload.kind==='cua-dispatch-receipt-2'&&isHash(payload.frameId),'RETAIN_RECEIPT_SHAPE');
      const raw=encoder.encode(evidenceJSON(payload.receipt,2)+'\n');
      return publish(raw,'live-receipt',payload.frameId);
    }
    if(payload?.artifact!==undefined) {
      const raw=encoder.encode(evidenceJSON(payload.artifact,2)+'\n');
      return publish(raw,payload.kind,payload.frameId);
    }
    need(payload?.screenshot instanceof Uint8Array&&typeof payload.ax==='string'
      &&isHash(payload.frameId)&&sha256(payload.screenshot)===payload.frameId
      &&payload.screenshot.byteLength<=16*1024*1024,'RETAIN_FRAME_SHAPE');
    const screenshot=await publish(payload.screenshot,'live-frames',payload.frameId);
    const ax=await publish(encoder.encode(payload.ax),'live-ax',payload.frameId);
    return {...screenshot,ax};
  };
}

export function createProducerHook({io,runProcess,repoRoot,authorization,authority,binary,geometryProvider}) {
  need(typeof geometryProvider==='function','LIVE_GEOMETRY_PROVIDER_REQUIRED');
  const run=async (args,code) => {
    const env={};if(Object.hasOwn(process.env,'CI'))env.CI=process.env.CI;
    const result=await runProcess([binary.absolutePath,...args],{cwd:repoRoot,env});
    if(result?.status!==0)throw Object.assign(new Error(String(result?.stderr??'').trim()),{code});
    try{return JSON.parse(result.stdout);}catch{fail('PRODUCER_RECEIPT_UNPARSEABLE');}
  };
  async function readRef(ref) {
    const raw=await readVerified(io,repoRoot,ref,'SCK_ARTIFACT_DRIFT');
    return raw;
  }
  async function frameSupport({frame,frameRef,frameId,sessionId,capturedAt,surface,layoutKey,native,geometryRef}) {
    need(['ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER'].includes(surface)&&frame instanceof Uint8Array
      &&isHash(frameId)&&frameRef?.sha256===frameId&&native?.bundle_id==='jp.naver.line.mac'
      &&Number.isInteger(native.pid)&&Number.isInteger(native.window_id)&&Number.isInteger(native.display_id),
      'FRAME_SUPPORT_INPUT');
    const output=`${CON}/evidence/frame-support/${sessionId}/${frameId.slice(0,16)}-${randomUUID()}`;
    await io.mkdirp(path.join(repoRoot,output));
    const receipt=await run(['frame-support','--project-root',repoRoot,'--grant',authorization,
      '--grant-sha256',authority.grantSha256,'--output',output,'--bundle-id',native.bundle_id,
      '--pid',String(native.pid),'--window-id',String(native.window_id),'--display-id',String(native.display_id),
      '--session-id',sessionId,'--layout-key',layoutKey,'--surface',surface,'--pair-frame',frameRef.path,
      '--pair-frame-id',frameId,'--geometry-evidence',geometryRef.path,'--geometry-evidence-sha256',geometryRef.sha256,
      '--cua-captured-at',capturedAt,'--cua-bounds',native.cua_capture_bounds_points.join(',')],
      'NON_MENU_SCK_SUPPORT_REFUSED');
    need(receipt.provider==='SCREEN_CAPTURE_KIT'&&receipt.surface===surface&&receipt.pairFrameId===frameId
      &&receipt.sessionId===sessionId&&receipt.reference&&receipt.manifestReference
      &&Number.isFinite(receipt.uncertaintyPx)&&receipt.uncertaintyPx>=2
      &&Number.isFinite(receipt.safeMarginPx)&&receipt.safeMarginPx>=receipt.uncertaintyPx+4,
      'FRAME_SUPPORT_RECEIPT_SHAPE');
    await readRef(receipt.reference);await readRef(receipt.manifestReference);
    return {provider:receipt.provider,surface:receipt.surface,pairFrameId:receipt.pairFrameId,
      sessionId:receipt.sessionId,uncertaintyPx:receipt.uncertaintyPx,safeMarginPx:receipt.safeMarginPx,
      reference:receipt.reference,manifestReference:receipt.manifestReference,readRef};
  }
  const geometryBySupport=new Map();
  async function captureMenuSupport({action,pairFrameId,sessionId,requestedAt,cuaFrame,cuaCapturedAt}) {
    const g=await geometryProvider({action,pairFrameId,sessionId,requestedAt,cuaFrame,cuaCapturedAt});
    need(g&&Number.isInteger(g.pid)&&Number.isInteger(g.windowId)&&Number.isInteger(g.displayId)
      &&typeof g.layoutKey==='string'&&Number.isFinite(g.uncertaintyPx)&&g.uncertaintyPx>=2,'LIVE_MENU_GEOMETRY');
    need(refShape(cuaFrame)&&cuaFrame.sha256===pairFrameId,'CUA_FRAME_REFERENCE_REQUIRED');
    const output=`${CON}/evidence/menu-support/${sessionId}/${pairFrameId.slice(0,16)}-${randomUUID()}`;
    await io.mkdirp(path.join(repoRoot,output));
    const receipt=await run(['album-support','--project-root',repoRoot,'--output',output,'--bundle-id','jp.naver.line.mac',
      '--pid',String(g.pid),'--window-id',String(g.windowId),'--display-id',String(g.displayId),
      '--session-id',sessionId,'--layout-key',g.layoutKey,'--pair-frame',cuaFrame.path,'--pair-frame-id',pairFrameId,
      '--cua-captured-at',cuaCapturedAt,'--cua-bounds',g.cuaBounds.join(','),'--menu-bounds',g.menuBounds.join(','),
      '--addressable-bounds',g.addressableBounds.join(','),'--save-all-point',action.save_all.join(','),
      '--uncertainty-px',String(g.uncertaintyPx)],'MENU_SUPPORT_REFUSED');
    need(receipt.provider==='SCREEN_CAPTURE_KIT'&&receipt.pairFrameId===pairFrameId&&receipt.sessionId===sessionId
      &&isHash(receipt.popupFrameId)&&receipt.reference&&refShape(receipt.reference),'MENU_SUPPORT_RECEIPT');
    const sidecarRaw=await readVerified(io,repoRoot,receipt.reference,'MENU_SUPPORT_ARTIFACT_DRIFT');
    const sidecar=JSON.parse(decoder.decode(sidecarRaw));
    need(sidecar.frame_id===pairFrameId&&sidecar.session_id===sessionId&&refShape(sidecar.sck_frame),
      'MENU_SUPPORT_SIDECAR_BINDING');
    await readVerified(io,repoRoot,sidecar.sck_frame,'MENU_POPUP_ARTIFACT_DRIFT');
    geometryBySupport.set(receipt.reference.sha256,{...g,saveAll:[...action.save_all],popupFrameId:receipt.popupFrameId,
      uncertaintyPx:receipt.uncertaintyPx});
    return receipt;
  }
  async function guardMenu({support,pairFrameId,popupFrameId,saveAllPoint,uncertaintyPx,sessionId}) {
    const g=geometryBySupport.get(support?.sha256);
    need(g&&g.popupFrameId===popupFrameId&&g.uncertaintyPx===uncertaintyPx
      &&JSON.stringify(g.saveAll)===JSON.stringify(saveAllPoint),'MENU_SUPPORT_BINDING');
    const result=await run(['album-support-guard','--project-root',repoRoot,'--support',support.path,
      '--support-sha256',support.sha256,'--pair-frame-id',pairFrameId,'--session-id',sessionId,
      '--pid',String(g.pid),'--window-id',String(g.windowId),'--layout-key',g.layoutKey,
      '--save-all-point',saveAllPoint.join(','),'--uncertainty-px',String(uncertaintyPx)],'MENU_GUARD_REFUSED');
    need(result.verdict==='PASS'&&result.pairFrameId===pairFrameId&&result.popupFrameId===popupFrameId
      &&result.supportSha256===support.sha256,'MENU_GUARD_REFUSED');
    return result;
  }
  const invokeProducer=request=>request.mode==='capture'?captureMenuSupport(request)
    :request.mode==='guard'?guardMenu(request):Promise.reject(Object.assign(new Error('PRODUCER_MODE_UNKNOWN'),{code:'PRODUCER_MODE_UNKNOWN'}));
  return Object.freeze({frameSupport,captureMenuSupport,guardMenu,invokeProducer,readRef});
}

function identityKey(fp) {return JSON.stringify([fp?.start_date,fp?.end_date,fp?.expected_images]);}

export function validateDownwardScroll(before,after,distance) {
  need(before?.surface==='ALBUMS'&&after?.surface==='ALBUMS'&&distance>0&&distance<=0.25,
    'SCROLL_EVIDENCE_CONTEXT');
  for(const key of ['group_key','session_id','pid','window_id','layout_key'])
    need(before[key]===after[key],'SCROLL_CONTEXT_DRIFT');
  const old=before.cards??[],next=after.cards??[];
  const validCard=card=>card&&card.fingerprint&&/^\d{4}-\d{2}-\d{2}$/.test(card.fingerprint.start_date)
    &&/^\d{4}-\d{2}-\d{2}$/.test(card.fingerprint.end_date)
    &&Number.isInteger(card.fingerprint.expected_images)&&card.fingerprint.expected_images>0
    &&Array.isArray(card.card_bounds)&&card.card_bounds.length===4&&card.card_bounds.every(Number.isFinite)
    &&typeof card.fully_visible==='boolean';
  need(old.length>0&&next.length>0&&old.every(validCard)&&next.every(validCard),'SCROLL_CARD_EVIDENCE');
  const oldMap=new Map(old.map((card,index)=>[identityKey(card.fingerprint),{card,index}]));
  const newMap=new Map(next.map((card,index)=>[identityKey(card.fingerprint),{card,index}]));
  need(oldMap.size===old.length&&newMap.size===next.length,'SCROLL_CARD_IDENTITY_AMBIGUOUS');
  const overlap=[...oldMap.keys()].filter(key=>newMap.has(key));
  need(overlap.length>0,'SCROLL_OVERLAP_MISSING');
  const oldOrder=overlap.map(key=>oldMap.get(key).index),newOrder=overlap.map(key=>newMap.get(key).index);
  need(oldOrder.every((n,i)=>i===0||oldOrder[i-1]<n)&&newOrder.every((n,i)=>i===0||newOrder[i-1]<n),
    'SCROLL_OVERLAP_ORDER');
  const completeOverlap=overlap.filter(key=>oldMap.get(key).card.fully_visible===true
    &&newMap.get(key).card.fully_visible===true);
  need(completeOverlap.length>=1,'SCROLL_COMPLETE_OVERLAP_MISSING');
  const movedUp=completeOverlap.some(key=>newMap.get(key).card.card_bounds[1]<oldMap.get(key).card.card_bounds[1]-1);
  need(movedUp,'SCROLL_EFFECT_UNPROVEN');
  const newComplete=[...newMap.entries()].filter(([key,value])=>!oldMap.has(key)&&value.card.fully_visible===true);
  need(newComplete.length>0,'SCROLL_NEW_CANDIDATE_MISSING');
  return Object.freeze({overlap:overlap.map(key=>oldMap.get(key).card.fingerprint),
    newCandidates:newComplete.map(([,value])=>value.card.fingerprint),movedUp:true,distance});
}

export function createDownloadObserver({io,repoRoot,retain,clock=()=>Date.now(),wait=ms=>new Promise(resolve=>setTimeout(resolve,ms))}) {
  function recognizedImage(raw,extension) {
    if(extension==='.png')return raw.byteLength>=24&&raw[0]===137&&raw[1]===80&&raw[2]===78&&raw[3]===71
      &&raw[12]===73&&raw[13]===72&&raw[14]===68&&raw[15]===82;
    return (extension==='.jpg'||extension==='.jpeg')&&raw.byteLength>=4&&raw[0]===255&&raw[1]===216
      &&raw[raw.byteLength-2]===255&&raw[raw.byteLength-1]===217;
  }
  async function inventory(destination,identity) {
    const real=await io.realpath(destination);need(real===destination,'DOWNLOAD_DESTINATION_IDENTITY');
    const directoryStat=await io.lstat(destination,{bigint:true});
    need(directoryStat?.isDirectory===true||typeof directoryStat?.isDirectory==='function'&&directoryStat.isDirectory(),
      'DOWNLOAD_DESTINATION_NOT_DIRECTORY');
    need(!directoryStat.isSymbolicLink?.()&&Number(directoryStat.dev)===identity.device
      &&Number(directoryStat.ino)===identity.inode&&Number(directoryStat.mode)===identity.mode,
      'DOWNLOAD_DESTINATION_REPLACED');
    const dir=await io.readdir(destination);need(Array.isArray(dir),'DOWNLOAD_DIRECTORY_READ');
    const names=dir.map(item=>typeof item==='string'?item:item.name).sort();
    const files=[];
    for(const name of names) {
      need(name&&name!=='.'&&name!=='..'&&!name.includes('/'),'DOWNLOAD_FILENAME');
      const target=path.join(destination,name);const st=await io.lstat(target,{bigint:true});
      const extension=path.extname(name).toLowerCase();
      need(st?.isFile===true||typeof st?.isFile==='function'&&st.isFile(),'DOWNLOAD_NONREGULAR_ENTRY');
      need(!st.isSymbolicLink?.(),'DOWNLOAD_SYMLINK');
      const mtimeNs=typeof st.mtimeNs==='bigint'?st.mtimeNs:st.mtime_ns;
      const size=Number(st.size),inode=Number(st.ino);
      need((typeof mtimeNs==='bigint'&&mtimeNs>=0n)||Number.isSafeInteger(mtimeNs),
        'DOWNLOAD_STAT_INCOMPLETE');
      need(Number.isSafeInteger(size)&&size>0&&Number.isSafeInteger(inode),
        'DOWNLOAD_STAT_INCOMPLETE');
      const raw=await io.readFile(target);
      need(raw.byteLength===size,'DOWNLOAD_FILE_CHANGED');
      const recognized=recognizedImage(raw,extension);
      if(!recognized)return {files,names,unknown:name};
      files.push({name,bytes:raw.byteLength,mtime_ns:mtimeNs,inode,sha256:sha256(raw),recognized_image:true});
    }
    return {files,names,unknown:null,identity};
  }
  async function baseline({action,owner,sessionId,frameId=action.frame_id}) {
    const st=await io.lstat(action.destination,{bigint:true});const real=await io.realpath(action.destination);
    need(st?.isDirectory===true||typeof st?.isDirectory==='function'&&st.isDirectory(),'DOWNLOAD_DESTINATION_NOT_DIRECTORY');
    need(!st.isSymbolicLink?.()&&real===action.destination,'DOWNLOAD_DESTINATION_IDENTITY');
    const identity={device:Number(st.dev),inode:Number(st.ino),mode:Number(st.mode),realpath:real};
    const sample=await inventory(action.destination,identity);need(sample.names.length===0,'DESTINATION_NONEMPTY');
    const artifact={version:1,run_id:action.run_id,execution_id:owner,destination:action.destination,
      captured_at:nowISO(),destination_identity:identity,inventory:[]};
    const reference=await retain({artifact,kind:'download-baseline',frameId});
    return Object.freeze({reference,artifact,identity});
  }
  async function observe({action,dispatch,confirmation,confirmationInvokedAt,destinationBaseline}) {
    need(destinationBaseline?.reference&&destinationBaseline.identity,'DOWNLOAD_BASELINE_REQUIRED');
    const confirmedMs=Date.parse(confirmationInvokedAt);
    need(Number.isFinite(confirmedMs),'DOWNLOAD_CONFIRMATION_TIME');
    const baselineMs=Date.parse(destinationBaseline.artifact?.captured_at);
    need(Number.isFinite(baselineMs)&&baselineMs<=confirmedMs,'DOWNLOAD_BASELINE_STALE');
    let sampleCount=0,last=null;
    for(;;) {
      const elapsed=Math.max(0,Date.now()-confirmedMs);
      if(elapsed>30000)break;
      sampleCount+=1;last=await inventory(action.destination,destinationBaseline.identity);
      need(last.unknown===null,'DOWNLOAD_UNKNOWN_ENTRY');
      if(last.files.length>0) {
        const observedAt=nowISO();
        const evidence={version:1,source_kind:'FILESYSTEM_DELTA',run_id:action.run_id,action_id:action.action_id,
          execution_id:action.owner,session_id:dispatch.dispatchInfo.session_id,destination:action.destination,
          baseline:destinationBaseline.reference,confirmation_frame_id:confirmation.frame_id,
          confirmation_invoked_at:confirmationInvokedAt,observed_at:observedAt,
          destination_identity:destinationBaseline.identity,before_inventory:[],after_inventory:last.files,
          sampling:{sample_count:sampleCount,interval_ms:1000,elapsed_ms:Math.min(30000,Date.now()-confirmedMs)}};
        const reference=await retain({artifact:evidence,kind:'download-start',frameId:confirmation.frame_id});
        return {evidence,reference};
      }
      const remaining=30000-(Date.now()-confirmedMs);
      if(remaining<=0)break;
      await wait(Math.min(1000,remaining));
    }
    fail('DOWNLOAD_START_UNKNOWN');
  }
  return Object.freeze({baseline,observe});
}

function token(cli) {need(typeof cli.state.lastToken==='string','RECEIPT_TOKEN_UNAVAILABLE');return cli.state.lastToken;}

async function runLifecycle({context,live,afterFirstAlbum=false,limit=1}) {
  const {cli,session,owner,authorization,download}=context;const trace=[];
  const step=async(name,fn)=>{const started=nowISO();const value=await fn();trace.push({name,started_at:started,completed_at:nowISO()});return value;};
  const inspect=await step('inspect',()=>cli('inspect',{authorization:null}));
  need(inspect.state_facts?.active_batch===null&&inspect.state_facts?.active_writer_id===null,
    'PREEXISTING_OWNERSHIP');
  const begin=await step('begin',()=>cli('begin',{payload:{expected_token:inspect.receipt_token,
    data:{mode:'backup_batch',limit}}}));
  need(begin.result?.status==='BATCH_OWNED','BATCH_BEGIN_REFUSED');
  const catalog=await step('capture-full-catalog',()=>live.captureCatalog({session,afterFirstAlbum}));
  need(catalog&&Array.isArray(catalog.records)&&catalog.records.length>0,'CATALOG_RECORDS_REQUIRED');
  const admitted=await step('admit',()=>cli('admit',{payload:{expected_token:token(cli),
    data:{records:catalog.records,session:owner}}}));
  need(admitted.result?.status==='ADMITTED'&&Array.isArray(admitted.result.identities), 'CATALOG_ADMISSION_REFUSED');
  let prepared=null;
  for(let index=0;index<admitted.result.identities.length;index++) {
    const identity=admitted.result.identities[index];
    const observation=await step(`reacquire-candidate-${index+1}`,()=>live.prepareCandidates({session,
      records:catalog.records,identity,index,afterFirstAlbum}));
    need(observation&&observation.surface==='ALBUMS'&&observation.session_id===owner,
      'CANDIDATE_REACQUISITION_REQUIRED');
    const result=await step(`prepare-${index+1}`,()=>cli('prepare',{payload:{expected_token:token(cli),data:{observation}}}));
    if(result.result?.status==='ALBUM_OPEN_READY') {prepared=result.result;break;}
    need(result.result?.status==='SKIP_VERIFIED','PREPARE_UNEXPECTED');
  }
  need(prepared&&typeof prepared.run_id==='string'&&prepared.session_id===owner,'NO_ELIGIBLE_TARGET');
  const baseline=await step('destination-empty-baseline',()=>download.baseline({action:{...prepared,owner,
    action_id:`BASE-${prepared.run_id}`,frame_id:prepared.frame_id},owner,sessionId:owner}));
  const detail=await step('open-album-and-match',()=>session.openAlbum(prepared));
  need(detail.surface==='ALBUM_DETAIL'&&detail.cards?.length===1
    &&identityKey(detail.cards[0].fingerprint)===identityKey(prepared.fingerprint),'POST_OPEN_IDENTITY_MISMATCH');
  const calibration=await step('menu-open-capture-guard-close',()=>session.calibrateMenu({detail,runId:prepared.run_id,
    locateMenu:live.locateMenu,captureMenuSupport:context.supportCallbacks.captureMenuSupport,
    guardMenu:context.supportCallbacks.guardMenu}));
  await step('calibrate',()=>cli('calibrate',{payload:{expected_token:token(cli),data:calibration}}));
  const fresh=await step('fresh-detail',()=>live.captureFresh?live.captureFresh({session,detail}):session.observe());
  const permit=await step('commit-original-intent',()=>session.originalIntent({receiptToken:token(cli),freshObservation:fresh}));
  const dispatch=await step('single-guarded-dispatch',()=>session.originalAtomicDispatch(permit,context.supportCallbacks));
  const chooser=await step('typed-chooser-and-download-observation',()=>session.exactChooser({dispatch,
    ...context.chooser,destinationBaseline:baseline}));
  const finalized=await step('independent-content-verification-and-commit',()=>cli('finalize',{payload:{
    expected_token:token(cli),data:{decoder:path.join(context.repoRoot,decoderPath),decoder_sha256:decoderSha256}}}));
  need(finalized.result?.status==='VERIFIED','VERIFIED_READBACK_REQUIRED');
  const navigation=context.adapter.createNavigationObserver({app:context.app,bridge:cli.bridge,retain:context.retain,
    classify:context.classifier.classify,sessionId:owner});
  const afterConfirm=await step('fresh-post-transaction-observation',()=>navigation.observe());
  need(afterConfirm.surface==='ALBUM_DETAIL','POST_TRANSACTION_DETAIL_REQUIRED');
  const albums=await step('return-to-albums',()=>navigation.returnToAlbums(afterConfirm,live.locateBack));
  const finalRecords=await step('async-final-catalog',()=>live.finalRecords({observer:navigation,albums,
    admittedRecords:catalog.records,afterFirstAlbum}));
  need(Array.isArray(finalRecords)&&finalRecords.length>0,'FINAL_CATALOG_REQUIRED');
  const finished=await step('finish-catalog-drift-check',()=>cli('finish',{payload:{expected_token:token(cli),
    data:{records:finalRecords,session:owner}}}));
  const released=await step('release-owner',()=>cli('release',{payload:{expected_token:token(cli),data:{}}}));
  need(released.result?.status==='BATCH_RELEASED','OWNER_RELEASE_REQUIRED');
  return {owner,authorization,inspect,begin,catalog,admitted,prepared,baseline,detail,calibration,fresh,chooser,
    finalized,albums,finalRecords,finished,released,trace,navigation,session};
}

export async function buildLiveRunner({io,runProcess,repoRoot,pythonBin,adapterModule,app,live,
    grant1=`${CON}/live-grant-1.json`,grant2=`${CON}/live-grant-2.json`,clock=()=>Date.now(),wait}) {
  need(adapterModule&&typeof adapterModule.createHostedSession==='function'
    &&typeof adapterModule.createNavigationObserver==='function'
    &&typeof adapterModule.createAlbumSupportCallbacks==='function','ADAPTER_MODULE_REQUIRED');
  need(app&&typeof live?.analyzeCapture==='function'&&typeof live.captureCatalog==='function'
    &&typeof live.prepareCandidates==='function'&&typeof live.finalRecords==='function'
    &&typeof live.locateMenu==='function'&&typeof live.locateBack==='function'
    &&typeof live.producerGeometry==='function'&&typeof live.scrollTarget==='function',
    'LIVE_GROUNDED_DEPENDENCIES_REQUIRED');
  const cache=new Map();
  async function makeContext(authorization,afterFirstAlbum) {
    const cli=createCli({io,runProcess,repoRoot,pythonBin,authorization});
    const authority=await cli.preflight();const owner=authority.grant.owner;
    const retain=createRetain({io,repoRoot});
    const producer=createProducerHook({io,runProcess,repoRoot,authorization,authority,
      binary:authority.producer,geometryProvider:live.producerGeometry});
    const supportCallbacks=adapterModule.createAlbumSupportCallbacks({invokeProducer:producer.invokeProducer});
    const classifier=createLiveClassifier({retain,frameSupport:producer.frameSupport,
      analyzeCapture:live.analyzeCapture,groupKey:live.groupKey});
    const locators=createChooserLocators();
    const download=createDownloadObserver({io,repoRoot,retain,clock,wait});
    const chooser={...locators,
      refreshBaseline:args=>download.baseline({action:{...args.action,frame_id:args.frameId},
        owner:args.action.owner,sessionId:owner}),
      observeDownload:args=>download.observe(args)};
    const session=adapterModule.createHostedSession({app,bridge:cli.bridge,retain,classify:classifier.classify,
      classifyChooser:classifier.classifyChooser,requireV2:true,chooser,sessionId:owner,clock:()=>clock()});
    const context={io,runProcess,repoRoot,authorization,authority,owner,cli,retain,producer,supportCallbacks,
      classifier,chooser,download,session,adapter:adapterModule,app,afterFirstAlbum};
    cache.set(owner,context);return context;
  }
  const preflight=async()=>Promise.all([grant1,grant2].map(async authorization=>{
    const context=await makeContext(authorization,false);
    return {owner:context.owner,authorization,grantSha256:context.authority.grantSha256,
      runtimeSha256:context.authority.runtimeSha256};
  }));
  async function runTwoAlbumLifecycle() {
    const authorities=await preflight();
    need(authorities[0].owner!==authorities[1].owner,'GRANT_OWNERS_MUST_DIFFER');
    const firstContext=cache.get(authorities[0].owner);
    const first=await runLifecycle({context:firstContext,live,afterFirstAlbum:false,limit:1});
    const nav=first.navigation;
    need(typeof live.preparePostReleaseScroll==='function','POST_RELEASE_SCROLL_PREPARATION_REQUIRED');
    const before=await live.preparePostReleaseScroll({observer:nav,records:first.finalRecords});
    need(before?.surface==='ALBUMS','POST_RELEASE_SCROLL_START_UNKNOWN');
    const target=await live.scrollTarget(before);
    need(Array.isArray(target)&&target.length===2&&target.every(Number.isFinite),'SCROLL_TARGET_UNKNOWN');
    const distance=0.25;
    const after=await nav.boundedScroll(before,target,'down',distance);
    const scrollFact=validateDownwardScroll(before,after,distance);
    const scrollEvidence=await firstContext.retain({artifact:{version:1,kind:'post-first-release-scroll',owner:first.owner,
      before,action:{target,direction:'down',distance},after,scrollFact,trace:nav.trace()},
      kind:'post-first-release-scroll',frameId:after.frame_id});
    nav.close();
    const secondContext=cache.get(authorities[1].owner);
    need(secondContext,'SECOND_OWNER_CONTEXT_REQUIRED');
    const second=await runLifecycle({context:secondContext,live,afterFirstAlbum:true,limit:1});
    second.navigation.close();
    return {status:'IMPLEMENTED_TWO_LIFECYCLE_RUNNER',authorities,first,scroll:{before,after,scrollFact,evidence:scrollEvidence},second};
  }
  return Object.freeze({preflight,runTwoAlbumLifecycle,contexts:cache});
}
