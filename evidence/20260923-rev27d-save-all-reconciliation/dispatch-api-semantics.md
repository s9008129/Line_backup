# Dispatch API semantics — the actual Save-All click path (read from the installed implementation)

Round: Rev27d `ZERO_GUI_SAVE_ALL_DISPATCH_RECONCILIATION`. All sources below were read read-only from the installed bundles on this machine.

## 1. The implementation chain (JS layer — source-verifiable)

Binding used by the live session: the CU REPL computer binding `lineApp.click([320,135], {mouseButton:'left', clickCount:1})`.

1. **`create_tinysky_alt.js`** — `/Applications/ChatGPT.app/Contents/Resources/cua_node/lib/node_modules/@oai/cua/dist/lib/js/oai_js_cua/src/tinysky_alt/create_tinysky_alt.js` (sha256 `d8c19eb3a82cfbd84ddc32625c05901fd3c7ad654db92e617ba1ab3bb16fdab4`):

   ```js
   click:(e,o)=>t.click(Object.assign(Object.assign(Object.assign({app:i},
     Array.isArray(e)?{x:e[0],y:e[1]}:{element_index:e}),
     void 0===(o?.mouseButton)?{}:{mouse_button:o.mouseButton}),
     void 0===(o?.clickCount)?{}:{click_count:o.clickCount}))
   ```

   → array form `[x,y]` becomes `x:e[0], y:e[1]`; **no coordinate conversion anywhere in this wrapper.**

2. **`targets/mac/click.js`** — `@oai/sky/dist/project/cua/sky_js/src/targets/mac/click.js` (sha256 `020901282209d67583ba6316f0a09bc00a694fd394d705105821d047b22da0a4`): `client.click({app, clickCount, elementIndex, mouseButton, x, y})` — pass-through.

3. **`targets/mac/client.js`** — `@oai/sky/dist/project/cua/sky_js/src/targets/mac/client.js` (sha256 `b5addc3c85ff0124095042832bca0fe1a271d119925459df7bd284dcab1931ab`):

   ```js
   click(e,t={}){ const r = e.clickCount??1, o = e.mouseButton??"left";
     return this.performAction(e.app, {click:{at:h({elementIndex:e.elementIndex,x:e.x,y:e.y}),
       clickCount:r, mouseButton:g(o)}}, t) }
   ```

   with `h(e) = e.elementIndex==null ? {coordinate:{_0:[Number(e.x),Number(e.y)]}} : {elementID:{_0:String(e.elementIndex)}}`, and `performAction` → IPC request type `"ComputerUseIPCAppPerformActionRequest"` with payload `{app, action:{click:{at:{coordinate:{_0:[x,y]}}, clickCount, mouseButton}}}`.

   → the IPC carries the **raw pair** `[320,135]` as `coordinate`. No scaling, no offset, no desktop mapping.

## 2. Documented coordinate semantics (types shipped with the same package)

- `@oai/sky .../types/window/Click.d.ts` (sha256 `89ca15e99d87a8587b42d2d94ef69ef098e96006876ec38fb41fcd6e0b4bfdc4`):
  - `x?: number;` — “**X coordinate in the app-window screenshot.**”
  - `y?: number;` — “**Y coordinate in the app-window screenshot.**”
  - Function doc: “Click either an indexed element from the latest app state or **a coordinate in the app window**.”
- `@oai/sky .../types/window2/Click.d.ts` (sha256 `3820ce4debf5d5f731ea5259f731b5bd74d9999fd59b95b3a1e24922d0e9d57c`): `x` — “**Window-relative X coordinate.**”
- For completeness, the full-desktop variant (not the binding used here) documents “coordinates are window-relative when provided” / “X coordinate on the desktop **or** within the target window” — i.e., in the family of APIs, coordinates are explicitly window-relative unless a desktop mode is chosen.

**JS-layer conclusion [VERIFIED]:** the click API accepts coordinates in the **app-window screenshot space, which is window-relative**. For an app binding the origin is the bound app window's top-left.

## 3. The native layer (not source-auditable) and how it is pinned

The coordinate pair travels by IPC to the native `SkyComputerUseService` (`/Users/hsiaojohnny/.codex/computer-use/Codex Computer Use.app/Contents/MacOS/SkyComputerUseService`, version 26.913.1001067; the service process observed in the logs: pid 47469, `com.openai.sky.CUAService`). The service is a **compiled binary** — its translation cannot be read as source. It is instead pinned **empirically**, by two independent physical measurements per dispatch:

1. **The harness's own software cursor.** After the Save All click, the harness overlay window `Software Cursor` (owner `ChatGPT Computer Use`, layer 102) has bounds pt (468,101,126×126) → **center (531,164) pt = px (1062,328)** — exactly the reconstructed physical point from the dispatching args under the documented window-local semantics ([320,135] + window origin [211,29]). The overlay window did not exist in the pre-click window lists; no pointer action occurred after 11:29:18, so it reflects the Save All click position.
2. **The rendered cursor glyph, cross-calibrated on two dispatches.** Bright-outline isolation in the post-click frames (identical method, both clicks): ellipsis click (point px (1030,158)) → glyph centroid (1032.6,161.4) px; Save All click (point px (1062,328)) → glyph centroid (1064.4,331.2) px. Both = **point + (≈+2.5,+3.3) px**, matching within 0.2 px across two independent clicks — the glyph is rendered at a fixed offset from the physical point, so the Save All physical point is the reconstructed (1062,328) px given the ellipsis point is semantically pinned (it opened the popup).
3. **Semantic pin for the ellipsis dispatch.** The ellipsis click at window-local [304,50] opened the menu; any non-window-local interpretation (screen-global (304,50) pt → window-local (93,21) title bar; other origins) would have missed the control and produced no menu. Hence the same translation was demonstrably in force through the identical call path one dispatch earlier.

**Falsified alternatives for the Save All dispatch:** screen-global (predicts px (640,270)), scale-2 (predicts px (1702,598)), origin [0,29] (px (640,328)), origin [−1,35] (px (638,318)), no-translation (px (640,270)) — all ≥420 px away in x from the measured cursor artifacts.

## 4. Conclusion

- Click API coordinate space actually consumed: **window-local points (app-window screenshot space)**; native translation by the bound window origin (211,29) at scale 1, pinned by two physical anchors and one semantic anchor.
- The one physical click point of the Save All dispatch is reconstructed as **screen (531,164) pt = frame px (1062,328)**.
- Residual (disclosed): the native translation is proven empirically, not by source audit. No evidence supports any mapping other than the one above.
