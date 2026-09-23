from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

STUDY_MODE_VERSION = "1.5.6"
STUDY_NOTICE_VERSION = "1.0"
STUDY_SUBJECT_PREFIX = "study_"
_STUDY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$")
_ACCESS_TOKEN = re.compile(r"^[A-Fa-f0-9]{32,128}$")
_DEVICE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,47}$")


def clean_study_id(value: str | None, field: str) -> str:
    text = str(value or "").strip()
    if not _STUDY_ID.fullmatch(text):
        raise ValueError(
            f"{field} must be 2–32 characters using only letters, numbers, '-' or '_'. "
            "Use a pseudonymous study code, not a name or email address."
        )
    return text


def clean_device_id(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if not _DEVICE_ID.fullmatch(text):
        raise ValueError("device_id must be at most 48 characters using letters, numbers, '.', '-' or '_'.")
    return text


def study_access_hash(token: str | None) -> str:
    text = str(token or "").strip()
    if not _ACCESS_TOKEN.fullmatch(text):
        raise ValueError("Study access token is missing or invalid.")
    return hashlib.sha256(f"skin-ai-study-v156|{text}".encode("utf-8")).hexdigest()


def study_subject_id(tester_id: str) -> str:
    clean = clean_study_id(tester_id, "tester_id")
    digest = hashlib.sha256(f"skin-ai-study-subject-v156|{clean.lower()}".encode("utf-8")).hexdigest()[:16]
    return f"{STUDY_SUBJECT_PREFIX}{digest}"


def is_study_subject(subject_id: str | None) -> bool:
    return str(subject_id or "").startswith(STUDY_SUBJECT_PREFIX)


def stamp_study_metadata(
    metrics: dict[str, Any],
    *,
    tester_id: str,
    session_id: str,
    access_token: str,
    acknowledged: bool,
    acknowledged_at: str | None,
    device_id: str | None,
    capture_id: str,
) -> dict[str, Any]:
    if not acknowledged:
        raise ValueError("Study notice acknowledgment is required before a study capture can be saved.")
    tester = clean_study_id(tester_id, "tester_id")
    session = clean_study_id(session_id, "session_id")
    device = clean_device_id(device_id)
    access_hash = study_access_hash(access_token)
    metrics.update(
        {
            "study_mode": True,
            "study_mode_version": STUDY_MODE_VERSION,
            "study_notice_version": STUDY_NOTICE_VERSION,
            "study_notice_acknowledged": True,
            "study_notice_acknowledged_at": str(acknowledged_at or "")[:64] or None,
            "study_tester_id": tester,
            "study_session_id": session,
            "study_device_id": device,
            "study_capture_id": capture_id,
            "study_access_key_hash": access_hash,
        }
    )
    return metrics


def is_study_scan(scan: dict[str, Any]) -> bool:
    return bool((scan.get("metrics") or {}).get("study_mode"))


def study_scan_matches_access(scan: dict[str, Any], access_hash: str) -> bool:
    metrics = scan.get("metrics") or {}
    return bool(metrics.get("study_mode") and metrics.get("study_access_key_hash") == access_hash)


def study_manifest_record(scan: dict[str, Any]) -> dict[str, Any] | None:
    metrics = scan.get("metrics") or {}
    if not metrics.get("study_mode"):
        return None
    media_dir = scan.get("media_dir")
    path = str(Path(media_dir) / "original.jpg") if media_dir else None
    return {
        "path": path,
        "participant_id": metrics.get("study_tester_id"),
        "session_id": metrics.get("study_session_id"),
        "capture_id": metrics.get("study_capture_id") or scan.get("id"),
        "device_id": metrics.get("study_device_id"),
        "created_at": scan.get("created_at"),
        "rgb_engine_version": metrics.get("rgb_engine_version"),
        "capture_protocol_version": metrics.get("capture_protocol_version"),
        "capture_quality": metrics.get("capture_quality"),
        "longitudinal_eligible": metrics.get("longitudinal_eligible"),
    }


def build_study_manifest(scans: Iterable[dict[str, Any]]) -> dict[str, Any]:
    captures = [row for scan in scans if (row := study_manifest_record(scan)) is not None]
    captures.sort(key=lambda row: str(row.get("created_at") or ""))
    participants = {row["participant_id"] for row in captures if row.get("participant_id")}
    sessions = {(row["participant_id"], row["session_id"]) for row in captures if row.get("participant_id") and row.get("session_id")}
    return {
        "study_mode_version": STUDY_MODE_VERSION,
        "capture_count": len(captures),
        "participant_count": len(participants),
        "session_count": len(sessions),
        "captures": captures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export RGB V1.5.6 study captures as a V1.5.4-compatible manifest")
    parser.add_argument("--db", type=Path, required=True, help="Path to the Skin AI SQLite database")
    parser.add_argument("--output", type=Path, required=True, help="JSON manifest output path")
    args = parser.parse_args()

    from skin_ai.store import ProductStore

    store = ProductStore(args.db)
    report = build_study_manifest(store.list_scans(limit=100000, modality="rgb"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["capture_count"])


if __name__ == "__main__":
    main()
