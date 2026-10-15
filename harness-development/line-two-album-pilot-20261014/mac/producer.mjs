// Existing native producer and filesystem observer algorithms, scoped to this pilot.
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
const CON='harness-development/line-two-album-pilot-20261014/private';
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const isHash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
const fail=code=>{throw Object.assign(Error(code),{code});};
const decoder=new TextDecoder();
const nowISO=()=>new Date().toISOString();
const canonical=value=>Array.isArray(value)?`[${value.map(canonical).join(',')}]`
  :value&&typeof value==='object'?`{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`
  :JSON.stringify(value);
const refShape=v=>v&&Object.keys(v).sort().join(',')==='bytes,path,sha256'
  &&v.path.startsWith(CON+'/')&&!v.path.split('/').some(p=>p==='.'||p==='..')
  &&Number.isInteger(v.bytes)&&v.bytes>0&&isHash(v.sha256);
async function readVerified(io,root,ref,code='ARTIFACT_DRIFT'){
  need(refShape(ref),code);const raw=await io.readFile(path.join(root,ref.path));
  need(raw.byteLength===ref.bytes&&raw.byteLength<=16*1024*1024&&sha256(raw)===ref.sha256,code);return raw;
}
export function createProducerHook({io,runProcess,repoRoot,authorization,authority,binary,geometryProvider,retain}) {
  need(typeof geometryProvider==='function','LIVE_GEOMETRY_PROVIDER_REQUIRED');
  const run=async (args,code) => {
    const env={};
    const result=await runProcess([binary.absolutePath,...args],{cwd:repoRoot,env});
    if(result?.status!==0)throw Object.assign(new Error(String(result?.stderr??'').trim()),{code});
    try{return JSON.parse(result.stdout);}catch{fail('PRODUCER_RECEIPT_UNPARSEABLE');}
  };
  async function readVisualDiagnosticClock({sessionId,witnessId}) {
    need(typeof sessionId==='string'&&sessionId&&typeof witnessId==='string'
      &&/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(witnessId),
      'VISUAL_DIAGNOSTIC_CLOCK_BINDING');
    const result=await run(['visual-diagnostic-clock','--session-id',sessionId,'--witness-id',witnessId],
      'VISUAL_DIAGNOSTIC_CLOCK_UNAVAILABLE');
    const witness=result?.witness;
    need(witness?.version===1&&witness.sessionID===sessionId&&witness.witnessID===witnessId
      &&witness.domain==='mach_continuous_time'&&/^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(witness.bootSessionUUID)
      &&Number.isInteger(witness.timebaseNumerator)&&witness.timebaseNumerator>0
      &&Number.isInteger(witness.timebaseDenominator)&&witness.timebaseDenominator>0
      &&typeof witness.continuousNanoseconds==='string'&&/^(0|[1-9][0-9]*)$/.test(witness.continuousNanoseconds)
      &&Number.isFinite(Date.parse(witness.sampledAtUTC)), 'VISUAL_DIAGNOSTIC_CLOCK_WITNESS');
    return witness;
  }
  async function readRef(ref) {
    const raw=await readVerified(io,repoRoot,ref,'SCK_ARTIFACT_DRIFT');
    return raw;
  }
  async function captureVisualDiagnostic({capture,saved,frameId,sessionId,requestStartedAtUtc,
      requestEndedAtUtc,requestStartMonotonicNanoseconds,requestEndMonotonicNanoseconds,before,
      clockBeforeCUA,clockWitnessId}) {
    need(typeof retain==='function','VISUAL_DIAGNOSTIC_RETENTION_REQUIRED');
    const decimalNs=value=>typeof value==='string'&&/^(0|[1-9][0-9]*)$/.test(value);
    const startMono=decimalNs(requestStartMonotonicNanoseconds)?BigInt(requestStartMonotonicNanoseconds):-1n;
    const endMono=decimalNs(requestEndMonotonicNanoseconds)?BigInt(requestEndMonotonicNanoseconds):-1n;
    need(capture?.screenshot instanceof Uint8Array&&saved?.sha256===frameId
      &&sha256(capture.screenshot)===frameId&&startMono>=0n&&endMono>=startMono
      &&endMono-startMono<=30_000_000_000n&&Number.isFinite(Date.parse(requestStartedAtUtc))
      &&Number.isFinite(Date.parse(requestEndedAtUtc))&&Date.parse(requestEndedAtUtc)>=Date.parse(requestStartedAtUtc),
      'VISUAL_DIAGNOSTIC_CUA_BINDING');
    need(before?.value?.target?.bundleID==='jp.naver.line.mac'&&before.value.complete===true
      &&before.value.truncated===false&&Number.isInteger(before.value.target.pid)
      &&Number.isInteger(before.value.target.startTimeSeconds)
      &&Number.isInteger(before.value.target.startTimeMicroseconds),
      'VISUAL_DIAGNOSTIC_NATIVE_BEFORE');
    need(clockBeforeCUA?.sessionID===sessionId&&clockBeforeCUA?.witnessID===clockWitnessId
      &&clockBeforeCUA?.domain==='mach_continuous_time'
      &&/^(0|[1-9][0-9]*)$/.test(clockBeforeCUA.continuousNanoseconds)
      &&Number.isInteger(clockBeforeCUA.timebaseNumerator)&&clockBeforeCUA.timebaseNumerator>0
      &&Number.isInteger(clockBeforeCUA.timebaseDenominator)&&clockBeforeCUA.timebaseDenominator>0,
      'VISUAL_DIAGNOSTIC_CLOCK_BINDING');
    const pid=before.value.target.pid;
    const focusedID=before.value.focusedWindowID;
    const windows=before.value.windows.filter(w=>w.windowNumber===focusedID&&w.nodeID!==null);
    need(windows.length===1&&Array.isArray(windows[0].displayIDs)&&windows[0].displayIDs.length===1
      &&windows[0].framePt,'VISUAL_DIAGNOSTIC_WINDOW_IDENTITY');
    const w=windows[0],bounds=[w.framePt.x,w.framePt.y,w.framePt.width,w.framePt.height];
    const preDispatchMono=process.hrtime.bigint();
    need(preDispatchMono>=startMono&&preDispatchMono-startMono<=5_000_000_000n
      &&Date.now()>=Date.parse(requestStartedAtUtc)
      &&Date.now()-Date.parse(requestStartedAtUtc)<=5000,'VISUAL_DIAGNOSTIC_CAPTURE_DEADLINE');
    const output=`${CON}/evidence/visual-diagnostic/${sessionId}/${frameId.slice(0,16)}-${randomUUID()}`;
    await io.mkdirp(path.join(repoRoot,output));
    const result=await run(['visual-diagnostic-capture','--project-root',repoRoot,
      '--grant',authorization,'--grant-sha256',authority.grantSha256,'--output',output,
      '--session-id',sessionId,'--cua-frame',saved.path,'--cua-frame-id',frameId,
      '--cua-request-started-at',requestStartedAtUtc,'--cua-request-ended-at',requestEndedAtUtc,
      '--cua-request-start-monotonic-ns',String(requestStartMonotonicNanoseconds),
      '--cua-request-end-monotonic-ns',String(requestEndMonotonicNanoseconds),
      '--clock-witness-id',clockWitnessId,'--continuous-clock-before-cua-json',JSON.stringify(clockBeforeCUA),
      '--pid',String(pid),'--process-start-seconds',String(before.value.target.startTimeSeconds),
      '--process-start-microseconds',String(before.value.target.startTimeMicroseconds),
      '--window-id',String(focusedID),'--display-id',String(w.displayIDs[0]),'--cua-bounds',bounds.join(',')],
      'VISUAL_DIAGNOSTIC_CAPTURE_REFUSED');
    const receipt=result;
    need(receipt.version===2&&receipt.kind==='VISUAL_CARD_DIAGNOSTIC'&&receipt.evidenceOnly===true
      &&receipt.actionable===false&&receipt.pair?.sessionID===sessionId&&receipt.pair.cuaFrameID===frameId,
      'VISUAL_DIAGNOSTIC_CAPTURE_RECEIPT');
    const pair=receipt.pair;
    need(refShape(pair.cuaFrame)&&pair.cuaFrame.sha256===frameId&&refShape(pair.sckFrame)
      &&pair.sckFrame.sha256===pair.sckFrameID&&pair.sckFrameID!==frameId
      &&pair.cuaRequestStartedAt===requestStartedAtUtc&&pair.cuaRequestEndedAt===requestEndedAtUtc
      &&pair.cuaRequestStartMonotonicNanoseconds===requestStartMonotonicNanoseconds
      &&pair.cuaRequestEndMonotonicNanoseconds===requestEndMonotonicNanoseconds
      &&pair.continuousClockWitnessID===clockWitnessId
      &&canonical(pair.continuousClockBeforeCUA)===canonical(clockBeforeCUA)
      &&pair.continuousClockAfterSCK?.sessionID===sessionId
      &&pair.continuousClockAfterSCK?.witnessID===clockWitnessId
      &&pair.continuousClockAfterSCK?.domain==='mach_continuous_time'
      &&pair.continuousClockAfterSCK?.bootSessionUUID===clockBeforeCUA.bootSessionUUID
      &&pair.continuousClockAfterSCK?.timebaseNumerator===clockBeforeCUA.timebaseNumerator
      &&pair.continuousClockAfterSCK?.timebaseDenominator===clockBeforeCUA.timebaseDenominator
      &&/^(0|[1-9][0-9]*)$/.test(pair.continuousClockAfterSCK?.continuousNanoseconds)
      &&BigInt(pair.continuousClockAfterSCK.continuousNanoseconds)>=BigInt(clockBeforeCUA.continuousNanoseconds)
      &&BigInt(pair.continuousClockAfterSCK.continuousNanoseconds)-BigInt(clockBeforeCUA.continuousNanoseconds)<=5_000_000_000n
      &&Date.parse(pair.sckRequestEndedAt)>=Date.parse(requestStartedAtUtc)
      &&Date.parse(pair.sckRequestEndedAt)-Date.parse(pair.cuaRequestStartedAt)<=5000,
      'VISUAL_DIAGNOSTIC_CAPTURE_PAIR');
    await readRef(pair.cuaFrame);await readRef(pair.sckFrame);
    const reference=await retain({artifact:receipt,kind:'visual-diagnostic-capture-receipt',frameId,sessionId});
    return {pair,reference,readRef};
  }
  async function analyzeVisualDiagnostic({pairEvidence,frameId,sessionId}) {
    const pair=pairEvidence?.pair;
    need(pair&&pair.kind==='VISUAL_CARD_DIAGNOSTIC'&&pair.sessionID===sessionId
      &&pair.cuaFrameID===frameId&&pair.cuaFrame?.sha256===frameId&&pair.sckFrame?.sha256===pair.sckFrameID,
      'VISUAL_DIAGNOSTIC_ANALYSIS_PAIR');
    const cuaRaw=await readRef(pair.cuaFrame),sckRaw=await readRef(pair.sckFrame);
    need(sha256(cuaRaw)===frameId&&sha256(sckRaw)===pair.sckFrameID&&pair.sckFrameID!==frameId,
      'VISUAL_DIAGNOSTIC_ANALYSIS_SOURCE_HASH');
    const captureReceipt=pairEvidence.reference;
    need(refShape(captureReceipt),'VISUAL_DIAGNOSTIC_TYPED_RECEIPT_REQUIRED');
    const receiptBytes=await readRef(captureReceipt);
    let decodedReceipt;try{decodedReceipt=JSON.parse(decoder.decode(receiptBytes));}catch{fail('VISUAL_DIAGNOSTIC_TYPED_RECEIPT_INVALID');}
    need(decodedReceipt.version===2&&decodedReceipt.kind==='VISUAL_CARD_DIAGNOSTIC'
      &&decodedReceipt.evidenceOnly===true&&decodedReceipt.actionable===false
      &&canonical(decodedReceipt.pair)===canonical(pair),'VISUAL_DIAGNOSTIC_RECEIPT_PAIR_MISMATCH');
    const pairSHA=captureReceipt.sha256;
    const result=await run(['visual-diagnostic-analyze','--project-root',repoRoot,
      '--capture-receipt',captureReceipt.path,'--capture-receipt-sha256',captureReceipt.sha256],
      'VISUAL_DIAGNOSTIC_PIXEL_ANALYSIS_REFUSED');
    need(result.version===1&&result.kind==='VISUAL_CARD_DIAGNOSTIC'&&result.evidenceOnly===true
      &&result.actionable===false&&result.capturePairSHA256===pairSHA
      &&['COMPLETE','INSUFFICIENT'].includes(result.status)&&Array.isArray(result.anchors)
      &&Array.isArray(result.cuaOCR)&&Array.isArray(result.sckOCR),'VISUAL_DIAGNOSTIC_PIXEL_ANALYSIS_SHAPE');
    if(result.status==='COMPLETE')need(result.anchors.length>=3&&Number.isFinite(result.uncertaintyPixels)
      &&Number.isFinite(result.maximumResidualPixels),'VISUAL_DIAGNOSTIC_PIXEL_ANCHORS');
    const reference=await retain({artifact:result,kind:'visual-diagnostic-pixel-analysis',frameId,sessionId});
    return {analysis:result,reference};
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
    const receipt=await run(['album-support','--project-root',repoRoot,'--grant',authorization,
      '--grant-sha256',authority.grantSha256,'--output',output,'--bundle-id','jp.naver.line.mac',
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
    const result=await run(['album-support-guard','--project-root',repoRoot,'--grant',authorization,
      '--grant-sha256',authority.grantSha256,'--support',support.path,
      '--support-sha256',support.sha256,'--pair-frame-id',pairFrameId,'--session-id',sessionId,
      '--pid',String(g.pid),'--window-id',String(g.windowId),'--layout-key',g.layoutKey,
      '--save-all-point',saveAllPoint.join(','),'--uncertainty-px',String(uncertaintyPx)],'MENU_GUARD_REFUSED');
    need(result.verdict==='PASS'&&result.pairFrameId===pairFrameId&&result.popupFrameId===popupFrameId
      &&result.supportSha256===support.sha256,'MENU_GUARD_REFUSED');
    return result;
  }
  const invokeProducer=request=>request.mode==='capture'?captureMenuSupport(request)
    :request.mode==='guard'?guardMenu(request):Promise.reject(Object.assign(new Error('PRODUCER_MODE_UNKNOWN'),{code:'PRODUCER_MODE_UNKNOWN'}));
  return Object.freeze({frameSupport,captureMenuSupport,guardMenu,readVisualDiagnosticClock,captureVisualDiagnostic,
    analyzeVisualDiagnostic,invokeProducer,readRef});
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
