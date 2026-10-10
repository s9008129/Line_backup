import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createDownloadObserver,validateDownwardScroll} from '../live_runner.mjs';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const fp=(start,end,count)=>({start_date:start,end_date:end,expected_images:count});
const card=(fingerprint,y,fullyVisible=true)=>({fingerprint,card_bounds:[0,y,100,60],fully_visible:fullyVisible});
const context={surface:'ALBUMS',group_key:'group-1',session_id:'session-1',pid:10,window_id:20,layout_key:'layout-1'};

test('bounded downward scroll requires continuous context, moved full overlap and a new complete card',()=>{
  const shared=fp('2026-10-01','2026-10-02',3);
  const old=contextFrame([card(shared,100),card(fp('2026-09-28','2026-09-30',4),170)]);
  const next=contextFrame([card(shared,40),card(fp('2026-10-03','2026-10-04',2),110)]);
  const proof=validateDownwardScroll(old,next,0.25);
  assert.equal(proof.movedUp,true);
  assert.equal(proof.overlap.length,1);
  assert.equal(proof.newCandidates.length,1);
  assert.throws(()=>validateDownwardScroll(old,next,0.251),/SCROLL_EVIDENCE_CONTEXT/);
  assert.throws(()=>validateDownwardScroll(old,{...next,window_id:21},0.25),/SCROLL_CONTEXT_DRIFT/);
});

test('scroll evidence rejects duplicate fingerprints and unchanged or incomplete overlap',()=>{
  const a=fp('2026-10-01','2026-10-02',3),b=fp('2026-10-03','2026-10-04',2);
  const duplicate=contextFrame([card(a,100),card(a,170)]);
  assert.throws(()=>validateDownwardScroll(duplicate,contextFrame([card(a,30),card(b,90)]),0.25),
    /SCROLL_CARD_IDENTITY_AMBIGUOUS/);
  assert.throws(()=>validateDownwardScroll(contextFrame([card(a,100)]),contextFrame([card(a,100),card(b,160)]),0.25),
    /SCROLL_EFFECT_UNPROVEN/);
  assert.throws(()=>validateDownwardScroll(contextFrame([card(a,100,false)]),contextFrame([card(a,40,false),card(b,90)]),0.25),
    /SCROLL_COMPLETE_OVERLAP_MISSING/);
});

function contextFrame(cards) {return {...context,cards};}

function imageBytes() {
  const bytes=new Uint8Array(24);bytes.set([137,80,78,71,13,10,26,10]);
  bytes.set([73,72,68,82],12);return bytes;
}

function downloadFixture({writeUnknown=false}={}) {
  const files=new Map();let inode=100;const retained=[];
  const directory={dev:1n,ino:2n,mode:0o40755n,isDirectory:()=>true,isFile:()=>false,isSymbolicLink:()=>false};
  const io={
    async realpath(value){return value;},
    async readdir(){return [...files.keys()];},
    async readFile(value){const name=value.split('/').at(-1);const entry=files.get(name);if(!entry)throw new Error('ENOENT');return entry.bytes;},
    async lstat(value){
      if(value==='/leased/destination')return directory;
      const entry=files.get(value.split('/').at(-1));if(!entry)throw new Error('ENOENT');
      return {dev:1n,ino:BigInt(entry.inode),mode:0o100644n,size:BigInt(entry.bytes.byteLength),
        mtimeNs:entry.mtimeNs,isDirectory:()=>false,isFile:()=>true,isSymbolicLink:()=>false};
    }
  };
  const retain=async ({artifact,frameId})=>{
    const bytes=new TextEncoder().encode(JSON.stringify(artifact,(_key,value)=>typeof value==='bigint'?String(value):value));
    const reference={path:`harness-development/test/${retained.length}.json`,bytes:bytes.byteLength,sha256:sha(bytes)};
    retained.push({artifact,reference,frameId});return reference;
  };
  let observer;
  const wait=async()=>{
    const bytes=writeUnknown?new TextEncoder().encode('unknown'):imageBytes();
    files.set(writeUnknown?'unexpected.txt':'download.png',{bytes,inode:++inode,mtimeNs:BigInt(Date.now())*1000000n});
  };
  observer=createDownloadObserver({io,repoRoot:'/repo',retain,wait});
  return {observer,files,retained,io};
}

test('download-start evidence follows a fresh empty baseline and records exact file identity',async()=>{
  const f=downloadFixture();
  const action={run_id:'RUN-1',action_id:'ACT-1',owner:'OWNER-1',destination:'/leased/destination',frame_id:'a'.repeat(64)};
  const baseline=await f.observer.baseline({action,owner:action.owner,sessionId:'SESSION-1'});
  const confirmationInvokedAt=new Date().toISOString();
  const result=await f.observer.observe({action,dispatch:{dispatchInfo:{session_id:'SESSION-1'}},
    confirmation:{frame_id:'b'.repeat(64)},confirmationInvokedAt,destinationBaseline:baseline});
  assert.equal(result.evidence.before_inventory.length,0);
  assert.equal(result.evidence.after_inventory.length,1);
  assert.equal(result.evidence.after_inventory[0].name,'download.png');
  assert.equal(typeof result.evidence.after_inventory[0].mtime_ns,'bigint');
  assert.equal(result.evidence.baseline.sha256,baseline.reference.sha256);
});

test('download-start evidence rejects unknown files and a baseline captured after confirmation',async()=>{
  const action={run_id:'RUN-1',action_id:'ACT-1',owner:'OWNER-1',destination:'/leased/destination',frame_id:'a'.repeat(64)};
  const unknown=downloadFixture({writeUnknown:true});
  const baseline=await unknown.observer.baseline({action,owner:action.owner,sessionId:'SESSION-1'});
  await assert.rejects(unknown.observer.observe({action,dispatch:{dispatchInfo:{session_id:'SESSION-1'}},
    confirmation:{frame_id:'b'.repeat(64)},confirmationInvokedAt:new Date().toISOString(),destinationBaseline:baseline}),
    /DOWNLOAD_UNKNOWN_ENTRY/);

  const stale=downloadFixture();
  const lateBaseline=await stale.observer.baseline({action,owner:action.owner,sessionId:'SESSION-1'});
  const futureConfirmation=new Date(Date.now()-1000).toISOString();
  lateBaseline.artifact.captured_at=new Date(Date.now()+1000).toISOString();
  await assert.rejects(stale.observer.observe({action,dispatch:{dispatchInfo:{session_id:'SESSION-1'}},
    confirmation:{frame_id:'b'.repeat(64)},confirmationInvokedAt:futureConfirmation,destinationBaseline:lateBaseline}),
    /DOWNLOAD_BASELINE_STALE/);
});
