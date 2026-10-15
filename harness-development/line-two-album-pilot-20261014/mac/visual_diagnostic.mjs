import {createHash, randomUUID} from 'node:crypto';
import {normalizeScreenshotBytes} from '../../../scripts/line_backup_cua_adapter.mjs';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};

/** Observe one authentic hosted CUA frame and return evidence only. The app is
 * held in a closure; this module exposes no action, navigation, or cache API. */
export function createVisualDiagnosticObserver({app,retain,readClock,beforeCapture,capturePair,afterCapture,analyze,sessionId}) {
  need(app&&typeof app.getAXStateAndScreenshot==='function','VISUAL_DIAGNOSTIC_CUA_REQUIRED');
  for(const [fn,name] of [[retain,'retain'],[readClock,'readClock'],[beforeCapture,'beforeCapture'],[capturePair,'capturePair'],
      [afterCapture,'afterCapture'],[analyze,'analyze']])need(typeof fn==='function',`VISUAL_DIAGNOSTIC_${name.toUpperCase()}_REQUIRED`);
  need(typeof sessionId==='string'&&sessionId,'VISUAL_DIAGNOSTIC_SESSION_REQUIRED');
  let used=false;
  return Object.freeze({observe:async()=>{
    need(!used,'VISUAL_DIAGNOSTIC_ALREADY_USED');used=true;
    const startedAt=new Date().toISOString();
    let before=null,capture=null,saved=null,frameId=null,pairEvidence=null;
    try {
      const clockWitnessId=randomUUID();
      const clockBeforeCUA=await readClock({sessionId,witnessId:clockWitnessId});
      before=await beforeCapture({sessionId});
      const requestStartedAtUtc=new Date().toISOString();
      const requestStart=process.hrtime.bigint();
      const raw=await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
      const requestEnd=process.hrtime.bigint();
      const requestEndedAtUtc=new Date().toISOString();
      need(requestEnd>=requestStart&&typeof raw?.state==='string','VISUAL_DIAGNOSTIC_CUA_CAPTURE');
      const screenshot=normalizeScreenshotBytes(raw.screenshot);
      need(screenshot.byteLength>0,'VISUAL_DIAGNOSTIC_CUA_BYTES');
      capture=Object.freeze({...raw,screenshot});frameId=hash(screenshot);
      const startNs=requestStart.toString(),endNs=requestEnd.toString();
      const monotonicInterval=Object.freeze({start_ns:startNs,end_ns:endNs,
        duration_ns:(requestEnd-requestStart).toString()});
      saved=await retain({screenshot,ax:capture.state,frameId,sessionId,capturedAt:requestStartedAtUtc,
        requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
      need(saved?.sha256===frameId&&saved.bytes===screenshot.byteLength&&saved.ax?.sha256===hash(new TextEncoder().encode(capture.state)),
        'VISUAL_DIAGNOSTIC_CUA_RETENTION');
      // Real independent SCK capture occurs before Native AFTER and remains
      // bound to this original CUA request start.
      pairEvidence=await capturePair({capture,saved,frameId,sessionId,before,
        requestStartedAtUtc,requestEndedAtUtc,requestStartMonotonicNanoseconds:startNs,
        requestEndMonotonicNanoseconds:endNs,clockBeforeCUA,clockWitnessId});
      const after=await afterCapture({capture,saved,frameId,sessionId,before,
        capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
      return await analyze({capture,saved,frameId,sessionId,capturedAt:requestStartedAtUtc,
        requestStartedAtUtc,requestEndedAtUtc,monotonicInterval,sourceBinding:{before,after},pairEvidence,
        requestStartMonotonicNanoseconds:startNs});
    } catch(error) {
      const failure={kind:'VISUAL_CARD_DIAGNOSTIC_FAILURE',evidence_only:true,actionable:false,session_id:sessionId,
        frame_id:frameId,started_at:startedAt,completed_at:new Date().toISOString(),
        capture_status:pairEvidence?'CAPTURED':'FAILED',analysis_status:'NOT_RUN',action_eligibility:'INELIGIBLE',
        frame:saved??null,capture_pair_receipt:pairEvidence?.reference??null,
        native_before:before?.reference??null,error:{code:error.code??null,message:String(error.message??error)}};
      try{await retain({artifact:failure,kind:'visual-card-diagnostic-failure',frameId:frameId??hash(Buffer.from(randomUUID()))});}
      catch(retentionError){error.diagnosticRetentionError=String(retentionError.message??retentionError);}
      throw error;
    }
  }});
}
