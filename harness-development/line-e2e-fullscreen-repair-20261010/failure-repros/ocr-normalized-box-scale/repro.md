# Failure reproduction: Vision normalized coordinates were scaled twice

## Symptom

On the saved 2294×1490 full-display frame, the menu occupies SCK bounds x=640, y=107, w=137, h=167 points. With the menu ROI starting at display pixel y=190, v1 reported the `儲存全部` text at y=248.99 px. That placed its first row only 59 px below the ROI origin, inconsistent with the visible menu's row spacing and the saved full-display pixels.

## Root cause

`VisionRegions.swift` receives normalized Vision boxes for an enlarged crop. It used `roiOrigin + normalized * originalCropDimension / processingScale`. The original crop dimension was already in source pixels, so dividing by scale compressed the offset from the ROI origin by that factor. The same error affected x/y and width/height in boxes and quads.

## Exact reproduction

Input frame SHA-256: `685a142c7cf0868a4215097651ca099b7741762c11f833ecbfa66dfcf6adf86c`.

```text
candidate/v1/bin/vision-regions --input evidence/e01-detail-menu-01.png --output evidence/e01-detail-menu-01-ocr.json --roi album-detail-menu,1250,190,340,370 --scale 3
candidate/v2/bin/vision-regions --input evidence/e01-detail-menu-01.png --output evidence/e01-detail-menu-01-v2-ocr.json --roi album-detail-menu,1250,190,340,370 --scale 3
candidate/v2/bin/vision-regions --input evidence/e01-detail-menu-01.png --output evidence/e01-detail-menu-01-v2-ocr-2x.json --roi albumdetailmenu2x,1250,190,340,370 --scale 2
```

For v1, the `儲存全部` source bbox y was 248.99 px. For corrected v2, the same pixels place it at 366.97 px with scale 3 and 368.00 px with the frozen 2× profile. Its row center is about y=381.5 px, between `修改相簿名稱` and `刪除相簿` as shown in the source image.

## Fix and checks

Candidate v2 converts normalized coordinates through enlarged dimensions and divides once: `normalized * enlargedDimension / processingScale`. The old candidate and outputs remain unchanged. Build `build/attempt-06.json` passes. `candidate/v2/test_geometry.py` passes seven cases covering correct point/margin, scale regression, wrong image hash, excessive anchor residual, size mismatch, small popup/window overlap, and wrong row order.

This replay uses the old diagnostic frame to prove the conversion fix; it does not replace the required new live E01 frame. No Save All action or state/destination mutation occurred during reproduction or repair.
