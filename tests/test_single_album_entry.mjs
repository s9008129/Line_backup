import test from 'node:test';
import assert from 'node:assert/strict';
import {runSingleAlbumPilot} from '../harness-development/line-two-album-pilot-20261014/two_album_entry.mjs';

function runtimeWithUsedLifecycle(){
  const operations=[];
  const runtime={profile:'LINE_TWO_ALBUM_PILOT/1',owner:'owner-1',authorization:'grant.json',
    one56Fingerprint:{start_date:'2024-05-27',end_date:'2024-05-31',expected_images:56},
    decoder:{path:'/decoder',sha256:'a'.repeat(64)},
    cli:async(operation)=>{
      operations.push(operation);
      if(operation==='inspect'&&operations.length===1)return {receipt_token:'token-1'};
      if(operation==='inspect')return {receipt_token:'token-2',gui_ledger_status:{
        status:'INITIALIZED',workflow_phase:'A',lifecycle_count:1,failure_latched:false,reserved_entry_count:0}};
      throw new Error('unexpected operation '+operation);
    },
    assertLineAlreadyRunning:async()=>{},getApp:async()=>({}),retain:async()=>{},
    producer:{captureMenuSupport:async()=>{},guardMenu:async()=>{}},menuLocator:async()=>{},chooser:{},navigation:{},
    privateEvidence:{leaseCloseReference:async()=>{},retainC1:async()=>{},retainFailure:async()=>{},retainDiscovery:async()=>{}},
    beforeCapture:async()=>{},afterCapture:async()=>{},windowLineage:async()=>{},clock:()=>0,
  };
  runtime.cli.bridge=async operation=>{operations.push(operation);return {};};
  return {runtime,operations};
}

test('single route refuses a used lifecycle before GUI, batch, C1, B, or initialization operations',async()=>{
  const {runtime,operations}=runtimeWithUsedLifecycle();
  await assert.rejects(runSingleAlbumPilot(runtime),error=>error?.message==='ONE56_LEDGER_NOT_FRESH');
  assert.deepEqual(operations,['inspect','inspect']);
  assert.equal(operations.some(op=>['gui_initialize','begin','gui_phase'].includes(op)),false);
});

test('single route requires the exact 56-photo target before execution',async()=>{
  const {runtime,operations}=runtimeWithUsedLifecycle();
  runtime.one56Fingerprint.expected_images=65;
  await assert.rejects(runSingleAlbumPilot(runtime),error=>error?.message==='ONE56_FINGERPRINT_REQUIRED');
  assert.deepEqual(operations,[]);
});
