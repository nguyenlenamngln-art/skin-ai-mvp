# Profiles + Structured Regions + Longitudinal Dashboard V1

## Product goal
Move from free-text scan labels to explicit local subject profiles and standardized scan regions so longitudinal comparisons cannot silently mix different people or anatomical sites.

## What changed
- Added persistent local subject profiles in SQLite.
- Added structured region vocabulary with modality-aware options.
- Added `GET/POST /v1/subjects` and `GET /v1/regions`.
- Both RGB and UV uploads can now carry `subject_id` + `region_code`.
- New scans store structured tracking metadata and a deterministic tracking-series key.
- RGB reference selection now requires the same subject + region + RGB engine version + eligible capture.
- UV comparison still requires compatible UV analysis/model/validator metadata and now also requires structured subject + region identity.
- Unassigned/legacy scans remain readable but are excluded from new structured longitudinal trends.
- Added a tracking-context UI above scan capture.
- Added Overview dashboard filters for subject, region, and modality.
- Added History filters using the same tracking context.
- Added grouped series summaries for comparable scans.

## Structured regions in V1
RGB:
- Full face
- Forehead
- Left cheek
- Right cheek
- Nose
- Chin
- Jawline

UV:
- Forehead
- Left cheek
- Right cheek
- Nose
- Chin
- Jawline
- Other facial area
- Other body area

## Integrity rules
A scan can still be saved for analysis without a structured profile/region, but it does not enter longitudinal profile trends.

RGB comparison requires:
1. same structured subject + region,
2. same RGB engine version,
3. good/eligible capture quality.

UV comparison requires:
1. same structured subject + region,
2. same UV analysis version,
3. same model signature,
4. same validator version/profile,
5. valid UV longitudinal eligibility.

Legacy scans are not automatically assigned to a profile or region.

## Scope and limitations
- Profiles are local product records, not authenticated accounts.
- Region is user-selected; the software does not verify anatomical site from image content.
- No clinical/diagnostic claims are introduced.
- Existing research-proxy limitations for RGB and UV measurements remain unchanged.
