# Image Retention Fix

`createRetain` now validates screenshot bytes before creating the retained path. The supported subset is PNG with 8-bit RGB or RGBA pixels, noninterlaced, using only IHDR, contiguous IDAT chunks, and IEND. The suffix is `.png` only after validation. JPEG is explicitly unsupported; unsupported PNG variants, unknown bytes, and malformed/truncated data fail before `mkdirp` or `writeFile` runs. This conservative subset is not evidence that the CUA App screenshot bridge emits PNG; its real byte format remains unverified.

PNG validation checks the exact signature, first and unique IHDR, supported dimensions, bit depth and color types, chunk bounds/names/CRC-32, only the supported chunk set, contiguous IDAT chunks, a final IEND with no trailing bytes, bounded zlib inflation with complete compressed-input consumption, expected scanline byte count, and valid filter-byte values. Interlaced PNG, indexed/palette PNG, metadata-bearing variants, and other bit depths/color types are unsupported. This is a bounded structural/deflate check, not a claim that native ImageIO or a live producer decoded the image.

After validation the existing retention behavior remains: paths stay under the same task evidence directory and kind, frame-ID prefix/counter/random suffix remain, bytes are written unchanged, and the readback byte count and SHA-256 must match. Screenshot evidence keeps its frame hash; AX text, receipts, and other artifacts continue using `.bin`.

The offline check executes the literal `createRetain` function from the candidate `live_runner.mjs` source, with pure dependencies and an in-memory `io` implementation. Fourteen cases cover generated RGB/RGBA PNGs, JPEG including the previously accepted malformed-Huffman entropy fixture, corrupt/truncated/unsupported PNGs, unknown bytes, zlib trailing input, frame-ID refusal, readback mismatch, byte/hash preservation, and `.bin` retention for AX/non-image evidence. No App object, CUA call, LINE session, grant, runtime binding, screenshot, or AX capture is used.

The validator is a strict supported-format gate, not a claim that a live producer emitted these bytes or that a native decoder accepted them. Runtime decode, native frame correlation, screenshot producer format, and retained producer provenance remain unverified pending authorized session evidence.

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES — isolated candidate only |
| `SOURCE_VALIDATED` | PARTIAL — literal production function passed 14 offline cases; source-to-CUA format binding unknown |
| `OFFLINE_BUILD_PASS` | NO — the sole authorized Swift build failed before tests |
| `RUNTIME_BOUND` | NO |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |
