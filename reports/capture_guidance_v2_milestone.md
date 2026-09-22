# Capture Guidance V2

## Goal
Improve repeatability before a scan reaches the existing RGB/UV backend quality gates.

## Added
- browser camera workflow via `getUserMedia`
- region-aware positioning overlay during guided sessions
- live browser estimates for lighting, sharpness and motion/stability
- preflight checks for uploaded or camera-captured images
- minimum-resolution, exposure/clipping and sharpness guidance
- explicit `Retake` vs `Analyze anyway` choice for advisory preflight warnings
- existing server-side RGB quality gate and UV input validator remain authoritative

## Measurement boundary
- Lighting is estimated from image luminance and clipping.
- Sharpness is estimated from local luminance gradients.
- Stability is estimated from frame-to-frame luminance change while the live camera is open.
- Position and distance are visual guidance only in V2; the browser does not provide reliable physical distance measurement here.
- Passing browser guidance does not guarantee a valid scan.
- Passing the UV input validator does not independently prove UV illumination.

## Product behavior
The browser can warn before submission, but the user can choose `Analyze anyway`. Rejected server-side captures are still not persisted or allowed into longitudinal trends.

## Intended use
Research/wellness longitudinal tracking only. No diagnostic claims.