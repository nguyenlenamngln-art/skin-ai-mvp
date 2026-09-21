# Scan Session V1

## Goal
Turn individual scans into a guided visit-level workflow while preserving existing modality and longitudinal safety rules.

## UV session workflow
A UV session is ordered and fixed:

1. Forehead
2. Left cheek
3. Right cheek
4. Nose
5. Chin

The backend owns the expected next region. A client cannot skip ahead or write a capture into the wrong region slot.

## RGB session workflow
Phone RGB remains a one-step `full_face` session in V1 because the current RGB engine measures a full frontal face. Regional RGB close-up sessions are intentionally deferred until a region-specific RGB measurement model exists.

## Persistence
Each session stores:
- session id
- subject id
- modality
- ordered region plan
- session version
- in-progress / complete state
- capture timestamp per region
- scan id per region

Each successful session scan is also stamped with `scan_session_id`, `scan_session_version`, and its session position.

## Rejection behavior
UV input-validation failures and poor RGB captures happen before session advancement. A rejected capture does not create a session item, so the user remains on the same required region for a retake.

## UI
The New Scan screen adds a Guided Session panel with:
- Start session
- ordered progress steps
- explicit current/next region
- automatic profile/region locking while a session is active
- persistence across browser refresh through the session id
- completion summary with per-region signal values

## Boundaries
- Session membership does not make scans clinically comparable by itself. Existing subject/region, model-version, validator, and capture-quality rules still control longitudinal deltas.
- UV input validation still checks compatibility with the supported UVFD-like close-up profile; passing the gate does not independently prove UV illumination.
- This is a local research-beta workflow, not user authentication or a medical diagnostic session.
