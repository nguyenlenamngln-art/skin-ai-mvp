from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

STUDY_MODE_VERSION = "1.5.6"
STUDY_NOTICE_VERSION = "1.0"
STUDY_PROFILE_PREFIX = "STUDY-"
_STUDY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$")


def clean_study_id(value: str | None, field: str = "tester_id") -> str:
    text = str(value or "").strip()
    if not _STUDY_ID.fullmatch(text):
        raise ValueError(
            f"{field} must be 2–32 characters using only letters, numbers, '-' or '_'. "
            "Use a pseudonymous study code, not a name or email address."
        )
    return text


def study_profile_name(tester_id: str) -> str:
    return f"{STUDY_PROFILE_PREFIX}{clean_study_id(tester_id)}"


def tester_id_from_metrics(metrics: dict[str, Any]) -> str | None:
    name = str(metrics.get("tracking_subject_name") or "")
    if not name.startswith(STUDY_PROFILE_PREFIX):
        return None
    tester_id = name[len(STUDY_PROFILE_PREFIX):]
    try:
        return clean_study_id(tester_id)
    except ValueError:
        return None


def is_study_scan(scan: dict[str, Any]) -> bool:
    metrics = scan.get("metrics") or {}
    return bool(tester_id_from_metrics(metrics) and metrics.get("scan_session_id"))


def study_manifest_record(scan: dict[str, Any]) -> dict[str, Any] | None:
    metrics = scan.get("metrics") or {}
    tester_id = tester_id_from_metrics(metrics)
    session_id = metrics.get("scan_session_id")
    if scan.get("modality") != "rgb" or not tester_id or not session_id:
        return None
    media_dir = scan.get("media_dir")
    path = str(Path(media_dir) / "original.jpg") if media_dir else None
    return {
        "path": path,
        "participant_id": tester_id,
        "session_id": str(session_id),
        "capture_id": scan.get("id"),
        "device_id": None,
        "created_at": scan.get("created_at"),
        "rgb_engine_version": metrics.get("rgb_engine_version"),
        "capture_protocol_version": metrics.get("capture_protocol_version"),
        "capture_quality": metrics.get("capture_quality"),
        "longitudinal_eligible": metrics.get("longitudinal_eligible"),
        "tracking_series_key": metrics.get("tracking_series_key"),
    }


def build_study_manifest(scans: Iterable[dict[str, Any]]) -> dict[str, Any]:
    captures = [row for scan in scans if (row := study_manifest_record(scan)) is not None]
    captures.sort(key=lambda row: str(row.get("created_at") or ""))
    participants = {row["participant_id"] for row in captures if row.get("participant_id")}
    sessions = {(row["participant_id"], row["session_id"]) for row in captures if row.get("participant_id") and row.get("session_id")}
    return {
        "study_mode_version": STUDY_MODE_VERSION,
        "study_notice_version": STUDY_NOTICE_VERSION,
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
