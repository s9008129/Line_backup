# CAL-1 — SIGABRT in the strict monitor (root cause, fix, verification)

Date: 2026-09-29 (offline; screen session LOCKED for the whole investigation)
Fingerprint: `STAGE=04 CHECK=CURRENT_COMPOSER_MONITOR_SIGABRT_TASK_DEALLOC (CAL-1)`
Status: RESOLVED (verified crash-free end-to-end).

## Symptom

`rev28ctl composer-calibrate --diagnose-only --timings 1` aborted (SIGABRT, exit 134)
~1.3–2.0 s after the item-04 panel dispatch, after items 00/02/03 had been written.
Deterministic across repeated runs; not present in the frozen W2 CI path
(`harness-calibrate`), which this driver does not call.

Crash (both `.ips` files in this directory):

```
freed pointer was not the last allocation
libswift_Concurrency: swift_Concurrency_fatalErrorv
  swift_task_dealloc + 124
  static PostconditionMonitor.run(bounds:sampler:monotonicNow:sleep:) + 68   PostconditionMonitor.swift:155:19
  closure #1 in ComposerCalibrationDriver.itemStrictMonitorTimings()         ComposerCalibration.swift:1169
  thunk for @escaping @isolated(any) @callee_guaranteed @async () -> (@out A)
  completeTaskWithClosure
```

`PostconditionMonitor.swift:155` is the `await sleep(...)` call inside `run`, i.e. the
call site of the *default-argument async closure* `sleep` declared in Rev28Core and
invoked from the rev28ctl client module.

`runtime/StackAllocator.h` (task-local stack allocator) fails this check only when the
slab allocator is enabled and the freed pointer is not the allocator's last allocation;
out-of-order frees degrade to `free()` only when the slab allocator is disabled.

## Root cause (upstream defect, external)

swiftlang/swift#92017 — "Default-argument async closure: copies disagree on context size,
linker mixes body and `Tu`" (open, filed 2026-09-07, Swift 6.3 / Xcode 27 era):

* a closure literal used as a **default argument** of a function in a library module is
  emitted as a weak (link-once) definition in both the defining module and every client
  module that references the default;
* in `-Onone` builds the two copies disagree on the **async context size** (library copy
  spills the error register at context offset 0x70 and its `Tu` records 128 bytes; the
  client copy allocates 112 bytes), so the spill lands one word past the allocation and
  overwrites the `previous` link of the following task allocation;
* the next `swift_task_dealloc` in the caller then aborts with exactly
  `freed pointer was not the last allocation` — the same stack shape as observed here.

The reporter's workaround: pass the closure explicitly at the call site (only one copy
exists). We reproduce all identifying features: library-defined default `sleep`
(Rev28Core), client-module invocation, `-Onone` build, the same frame chain, the same
runtime message. The upstream issue remains open; this is a workaround, not a fix of the
toolchain.

## Fix applied (branch-local, driver-side only)

`rev28/Sources/rev28ctl/ComposerCalibration.swift`: new file-private
`runCurrentComposerMonitor(bounds:sampler:)` that calls `PostconditionMonitor.run` with
`monotonicNow:` and `sleep:` passed **explicitly** from rev28ctl; all seven driver call
sites now use it. Semantics are unchanged (same closures, same defaults' behavior:
`max(0.001, seconds)` floor, `try?` around `Task.sleep`).

Deliberately not changed:
* `PostconditionMonitor.run`'s defaults and Rev28Core tests — `HarnessCalibration.swift`
  (frozen blob `c411011b1b44b1efb614e000f526b2118f45d120`, provenance PASS after the
  change) still uses the defaults; that path is bound by the W2 freeze and out of this
  task's scope. The landmine therefore remains reachable *only* from that frozen path.
* No Rev28Core source change, so the 168-test suite, matrix and replay expectations are
  untouched.

## Verification

* `--diagnose-only --timings 1` completes end-to-end, exit 0: diag6 (fix build) and diag7
  (clean build, telemetry fidelity fix). diag7 records preserved in
  `CAL1-diag7-COMPOSER-20260929-101022/` with the run's own `sha256sums.txt`
  (verified locally with `shasum -a 256 -c`).
* `xcrun swift test --package-path rev28` → 168/168 pass after the change.
* `python3 -B rev28/Tools/verify_pre_live_provenance.py` → PASS.
* Instrumented bisection runs (traces) located the crash to the monitor task suspended at
  `await sleep(...)` right after the panel dispatch; traces removed before commit.

## Locked-session environment (not a driver defect)

For the whole investigation the console session was locked
(`CGSessionScreenIsLocked=1`, frontmost `com.apple.loginwindow`). Direct probes (logs in
this directory) show the split that explains every remaining item-03/04 refusal:

* `CAL1-probe3-cg-sck-under-lock.log` — CG (`optionOnScreenOnly`) and SCK both list the
  harness windows including `rev28 harness chooser` shortly after `showPanel`; the
  window is present and frame-stable.
* `CAL1-probe4-ax-under-lock.log` — AX (`kAXWindowsAttribute` / `kAXChildrenAttribute`)
  returns `AXApplication`-role placeholder elements with `kAXErrorAttributeUnsupported`
  (-25205) for subrole/position/size. No `AXWindow` with a frame is exposed while
  locked, so `matchingAXWindow` cannot match and item 03 cannot locate the panel.

The official ≥20-timings run requires an unlocked session; the session gate
(`BLOCKED_SESSION_LOCKED`) and `--diagnose-only` (never claimable as PASS) already encode
that. The diagnostic verdict for a locked session is `DIAGNOSTIC_ONLY` with blocker
`ACTIVATION_REFUSED_DIAGNOSTIC_BYPASS`.
