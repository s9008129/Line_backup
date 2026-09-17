# Vision OCR helper (frozen supplementary) — macOS native text recognition

Read-only helper used by the attempt-05 supplementary cross-check
(`evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json`). It reads an image file
and prints every `VNRecognizeTextRequest` observation. It sends no input, touches no UI,
and is NOT part of the official verification chain:

> Adopting this reader inside the official chain (the three v3 tools) is a semantic change:
> it requires a new plan revision + independent review + explicit owner decision. Until
> then every frozen verdict stands.

## Source

`vision_ocr.swift` — 1,070 bytes, SHA-256
`4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`
(identical to the /tmp copy used for the recorded readings).

The compiled binary used for the recorded readings (`/tmp/vision_ocr`, 67,192 bytes, SHA-256
`f54628e8f42fb65200bf98bf5cc6463937d28781c673c22e5ca8b9418ae3f6c9`) is a build artifact;
rebuild it from the source below. Binaries are not committed.

## Build

```
swiftc -O vision_ocr.swift -o /tmp/vision_ocr
```

Compiled with: Apple Swift 6.3.3 (swiftlang-6.3.3.1.3 clang-2100.1.1.101),
arm64-apple-macosx26.0. No third-party dependencies (Foundation + Vision + AppKit only).

## Invocation and output

```
/tmp/vision_ocr <image>
```

One line per observation on stdout:

```
px[x0,y0,x1,y1]\tconf=NN\tTEXT
```

`px` coordinates are top-left-origin pixels (y flipped from Vision's bottom-left
boundingBox). `conf` is the top candidate's confidence, two decimals. Exit codes:
`2` usage, `3` image load failure, `4` recognition failure, `0` OK (including "no text").

Settings: `recognitionLevel = .accurate`, `recognitionLanguages = ["zh-Hant", "en-US"]`,
`usesLanguageCorrection = false`.

## Recorded readings (attempt-05 cross-check)

| Input (SHA-256) | Vision reading | Frozen tesseract reading |
|---|---|---|
| post frame 327x643 (`4cb8a6b4…c6560b3`) | title `2024/05/13~05/17` conf 1.00; `57張照片` conf 1.00 | title readable; count read `75` -> verify exit 4 TARGET_MISMATCH |
| pre frame 327x643 (`3d926e7d…3f573d531`) | title conf 1.00; `57` conf 0.50; group name `旻議允禎…` conf 0.50 (1x misread) | `57` readable |
| s1 probe crop 327x643 (`aea53a0d…e30f5c3`) | title conf 1.00; `57` conf 1.00 | count read `27` -> locate exit 5 |
| s2 probe crop 654x1286 (`7b9d0a19…9c63721b`) | title conf 1.00; `57` conf 1.00; group name `旻謙允禎…` conf 1.00 (2x fixes it) | count read `5` -> locate exit 5 |

Raw stdout SHAs: post `5c86dda8…`, pre `07e3e156…`, s1 `561bb131…`, s2 `abf9d75e…`
(full transcripts are embedded line-by-line in the cross-check JSON; /tmp copies are
volatile and not committed).

## Limits (as recorded)

- The helper reads image files from any path; the frozen tesseract path cannot open files
  under /tmp in this environment (that is why the v3 tools pipe via stdin/stdout).
- Reading a value is not a verdict: thresholds/acceptance rules for any Vision-based
  reader must be defined by the new plan revision; do not loosen fail-closed rules ad hoc.
- The 1x frame reads the group-name character `謙` as `議` at conf 0.50 (2x corrects it);
  do not normalize merge the owner's `禎` (U+798E) with `楨` (U+6968) under any scheme.
