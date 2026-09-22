# Mobile Capture & Beta Readiness V1

## Scope shipped

- Phone-first responsive layout below 820 px.
- Bottom navigation with mobile safe-area spacing.
- Larger touch targets and single-column scan/review flow.
- Mobile-friendly session history, comparison, capture guidance and result tabs.
- Installable PWA metadata and home-screen identity.
- Minimal service worker for app-shell fallback.
- Mobile capture hints that distinguish Phone RGB from the external-device UV workflow.

## Scientific/product boundary

- Browser lighting, sharpness and stability checks remain advisory.
- Phone RGB uses the device camera only when browser permissions and secure-context requirements are satisfied.
- UV fluorescence capture still requires a supported external UV device or an uploaded UV fluorescence image.
- A normal phone or laptop RGB camera is not treated as a UV camera.
- Analysis and longitudinal eligibility continue to be decided by the existing backend validators and version-safe comparison rules.

## Local mobile testing note

A phone can preview the responsive UI when the development server is reachable on the local network. However, browser camera APIs generally require HTTPS on non-localhost origins. For a real phone-camera beta test, use an HTTPS deployment or trusted development tunnel.

## Deferred deliberately

Richer device/capture provenance (camera vs upload, normalized device/browser class, source dimensions) should be added as an explicit scan-schema/API revision. V1 does not silently modify stored measurement contracts.
