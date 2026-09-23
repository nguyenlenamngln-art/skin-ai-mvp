# RGB V1.5.7 — Researcher Dashboard & Study Access Control

Status: engineering access-control and study-management milestone.

Production RGB measurement remains **V1.5.2** under **Capture Protocol V1.4**. V1.5.7 does not alter redness/pigmentation thresholds, anatomical masking, regional trend gates, or result calculations.

## Purpose

V1.5.6 created pseudonymous study/session structure but did not provide a private researcher view or a real tester access boundary. V1.5.7 separates the system into three contexts:

1. **Public/non-study app** — ordinary study records are excluded from subject, scan, session and trend listings.
2. **Tester Study Mode** — a tester signs in with an assigned tester ID plus access code and receives an HttpOnly signed study cookie. Tester-scoped data views expose only that tester's study records.
3. **Researcher Dashboard** — `/researcher.html` authenticates with the server-side `SKIN_AI_RESEARCHER_KEY`, exchanges it for an HttpOnly researcher cookie, and exposes cohort/participant study views.

## Researcher workflow

- Open `/researcher.html`.
- Enter the researcher key configured in the deployment environment.
- Create a pseudonymous tester (automatic `P001`, `P002`, ... or an allowed explicit code).
- The server returns a one-time access code. Share tester ID + access code privately with that participant.
- Review participant/session/capture counts and measurement stability summaries.
- Open a participant to review RGB overlays and capture-level metrics.
- Rotate a tester's access code when required; old signed tester sessions fail subsequent access checks.
- Export the V1.5.4-compatible JSON manifest.

## Tester workflow

- Enable Tester Study Mode.
- Enter the assigned tester ID and access code.
- A successful login creates an HttpOnly study cookie; the access code is not stored in localStorage.
- The app locks the capture context to Phone RGB / full face and starts a guided study session.
- Refresh/history reads are redirected to tester-scoped endpoints so only that participant's study data is returned.
- The V1.5.5 result experience remains unchanged for the actual analysis result.

## Access-control behavior

Study profiles use the existing `STUDY-<tester_id>` tracking identity so V1.5.6 manifests remain compatible. A new `study_participants` table stores tester ID, linked subject ID, access-code hash, activation state and timestamps. Raw tester access codes are never stored.

The researcher key is configured only through the deployment environment as `SKIN_AI_RESEARCHER_KEY`. It is not committed to the repository. Researcher login creates an HttpOnly, SameSite=Strict cookie. The dashboard JavaScript does not place the researcher key in localStorage.

Individual study scans, sessions and media are blocked unless the requester has either the matching tester cookie or a researcher cookie. Public study lists exclude study participants and study scans.

This is a substantial improvement over V1.5.6, but it remains an engineering beta access layer rather than a full regulated identity/consent platform. Formal research governance, consent requirements, retention policies and jurisdiction-specific privacy obligations must be handled separately when applicable.

## Dashboard metrics

The initial researcher dashboard intentionally reports descriptive engineering statistics only:

- participants
- sessions
- captures
- trend-eligible captures
- mean capture-quality score
- redness coefficient of variation (when at least two eligible captures exist)
- pigmentation coefficient of variation (when at least two eligible captures exist)
- capture-level redness/pigmentation/texture/quality/confidence/anatomical support

These metrics are not diagnostic or clinical validation thresholds. Full mask-IoU V1.5.4 analysis remains available through the exported manifest/offline validation harness.

## Deployment requirement

Set a strong random `SKIN_AI_RESEARCHER_KEY` before using V1.5.7. Production HTTPS should keep `SKIN_AI_COOKIE_SECURE=1` (the default). `SKIN_AI_COOKIE_SECURE=0` is intended only for local HTTP tests.
