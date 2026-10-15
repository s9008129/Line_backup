import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const binary=process.env.REV28CTL;
const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)));

function invoke(args) {
  return spawnSync(binary,args,{cwd:root,encoding:'utf8',timeout:10_000,
    env:{PATH:'/usr/bin:/bin:/usr/sbin:/sbin'}});
}

function sample(sessionID,witnessID) {
  const run=invoke(['visual-diagnostic-clock','--session-id',sessionID,'--witness-id',witnessID]);
  assert.equal(run.error,undefined,run.error?.message);
  assert.equal(run.status,0,run.stderr);
  return JSON.parse(run.stdout).witness;
}

function check(before,after,sessionID,witnessID) {
  return invoke(['visual-diagnostic-clock-check','--session-id',sessionID,'--witness-id',witnessID,
    '--before-json',JSON.stringify(before),'--after-json',JSON.stringify(after)]);
}

function rejected(before,after,sessionID,witnessID,reason) {
  const result=check(before,after,sessionID,witnessID);
  assert.equal(result.error,undefined,result.error?.message);
  assert.equal(result.status,77,result.stderr);
  assert.match(result.stderr,/visual-diagnostic-clock-check refused/);
  console.log(`clock_negative_${reason}=${result.stderr.trim()}`);
}

test('real native clock-only cross-process bracket accepts one boot/domain and rejects offsets',
  {skip:!binary&&'set REV28CTL to the built rev28ctl executable'},async()=>{
    const sessionID=`clock-test-${randomUUID()}`,witnessID=randomUUID();
    const before=sample(sessionID,witnessID),after=sample(sessionID,witnessID);
    assert.equal(before.domain,'mach_continuous_time');
    assert.equal(before.sessionID,sessionID);assert.equal(before.witnessID,witnessID);
    assert.equal(after.bootSessionUUID,before.bootSessionUUID);
    assert.equal(after.timebaseNumerator,before.timebaseNumerator);
    assert.equal(after.timebaseDenominator,before.timebaseDenominator);
    assert.ok(BigInt(after.continuousNanoseconds)>=BigInt(before.continuousNanoseconds));
    const positive=check(before,after,sessionID,witnessID);
    assert.equal(positive.error,undefined,positive.error?.message);
    assert.equal(positive.status,0,positive.stderr);
    const passed=JSON.parse(positive.stdout);
    assert.equal(passed.status,'PASS');
    assert.ok(passed.elapsedNanoseconds<=5_000_000_000);
    console.log(`clock_positive=${JSON.stringify({runtime:process.version,before,after,check:passed})}`);

    const otherDomain={...after,domain:'mach_absolute_time'};
    rejected(before,otherDomain,sessionID,witnessID,'domain');
    const otherTimebase={...after,timebaseNumerator:after.timebaseNumerator+1};
    rejected(before,otherTimebase,sessionID,witnessID,'timebase');
    const reversed={...after,continuousNanoseconds:String(BigInt(before.continuousNanoseconds)-1n)};
    rejected(before,reversed,sessionID,witnessID,'reversed');
    const offset={...after,continuousNanoseconds:String(BigInt(before.continuousNanoseconds)+5_000_000_001n)};
    rejected(before,offset,sessionID,witnessID,'synthetic_offset');
    const unbound={...after,witnessID:randomUUID()};
    rejected(before,unbound,sessionID,witnessID,'witness_id');
    const otherBoot={...after,bootSessionUUID:randomUUID()};
    rejected(before,otherBoot,sessionID,witnessID,'boot');
    const otherSession={...after,sessionID:`other-${sessionID}`};
    rejected(before,otherSession,sessionID,witnessID,'session');

    await new Promise(resolve=>setTimeout(resolve,5_100));
    const stale=sample(sessionID,witnessID);
    rejected(before,stale,sessionID,witnessID,'real_elapsed_over_5s');
    console.log(`clock_stale=${JSON.stringify({before,stale,observedNanoseconds:
      (BigInt(stale.continuousNanoseconds)-BigInt(before.continuousNanoseconds)).toString()})}`);
  });
