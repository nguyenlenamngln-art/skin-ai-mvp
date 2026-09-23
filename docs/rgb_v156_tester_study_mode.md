# RGB V1.5.6 — Tester Study Mode

## Scope

V1.5.6 adds a lightweight study workflow for collecting repeat RGB captures from external testers while keeping the production measurement pipeline frozen.

Unchanged:

- RGB measurement engine: V1.5.2
- Capture Protocol: V1.4
- redness/pigmentation thresholds
- V1.5.1 regional trend gate
- V1.5.2 anatomical mask stabilization
- V1.5.3 real-image validation
- V1.5.4 repeatability criteria
- V1.5.5 tester result presentation

## Tester workflow

A tester enables **Tester Study Mode**, enters an assigned pseudonymous code such as `P001`, reads and acknowledges the study notice, and starts a study session.

The UI then:

1. forces Phone RGB mode;
2. creates or reuses a pseudonymous profile named `STUDY-<tester code>`;
3. fixes the tracking region to `full_face`;
4. starts the existing guided RGB session workflow;
5. attaches the server-generated guided-session ID to the saved scan automatically;
6. shows the V1.5.5 result experience after a successful capture;
7. allows the tester to start another study session for a repeat capture.

Each Phone RGB guided session contains one full-face capture, so repeated study sessions become independent session IDs for V1.5.4 repeatability analysis.

## Privacy and identifier rules

The study UI asks for a pseudonymous tester code only. The accepted format is 2–32 characters using letters, numbers, hyphens, or underscores.

The interface explicitly tells testers not to enter names, email addresses, phone numbers, or other identifying information in the tester-code field.

V1.5.6 does **not** add production-grade authentication or a research-consent management system. The notice acknowledgment is stored locally in the browser to streamline the engineering beta workflow. It should not be treated as a substitute for formal informed consent or ethics-review requirements where those apply.

Original images remain stored by the existing product scan store because V1.5.4 repeatability validation requires access to the saved RGB captures.

## Automatic V1.5.4 manifest export

Study captures reuse existing server-side metadata rather than creating a second scan database:

- `tracking_subject_name` → participant ID (`STUDY-P001` becomes `P001`)
- `scan_session_id` → V1.5.4 session ID
- scan ID → capture ID
- saved `original.jpg` path → manifest image path
- RGB engine/capture protocol/quality fields → validation metadata

Export a V1.5.4-compatible JSON manifest from a deployment database with:

```bash
PYTHONPATH=src python -m skin_ai.study_mode_v156 \
  --db data/product/skin_ai.db \
  --output data/interim/rgb_v156_study_manifest.json
```

The resulting `captures` list can be converted directly to the V1.5.4 manifest fields `path`, `participant_id`, `session_id`, `capture_id`, and optional `device_id` (currently `null`).

## Suggested tester protocol

For a lightweight engineering repeatability study:

- assign each tester a pseudonymous code (`P001`, `P002`, ...);
- collect at least 3 captures per tester;
- spread captures across at least 2 study sessions;
- prefer original phone captures rather than screenshots;
- ask testers to follow the same frontal-light/distance guidance shown by the app;
- deliberately allow small realistic variation between sessions so repeatability is actually tested.

A single tester can still contribute useful within-person repeatability data, but V1.5.4 continues to prevent a multi-user cohort pass until its cohort-completeness criteria are met.

Research/wellness use only; no diagnostic claims.
