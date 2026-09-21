from __future__ import annotations

from typing import Any

SESSION_VERSION = "1.0"

SESSION_PLANS: dict[str, tuple[str, ...]] = {
    "uv": ("forehead", "left_cheek", "right_cheek", "nose", "chin"),
    "rgb": ("full_face",),
}


def session_plan(modality: str) -> list[str]:
    if modality not in SESSION_PLANS:
        raise ValueError(f"Unsupported session modality: {modality}")
    return list(SESSION_PLANS[modality])


def next_region(plan: list[str], completed_regions: list[str]) -> str | None:
    completed = set(completed_regions)
    for region in plan:
        if region not in completed:
            return region
    return None


def session_progress(plan: list[str], completed_regions: list[str]) -> dict[str, Any]:
    done = [r for r in plan if r in set(completed_regions)]
    nxt = next_region(plan, done)
    return {
        "completed_count": len(done),
        "total_count": len(plan),
        "completed_regions": done,
        "next_region_code": nxt,
        "progress_fraction": len(done) / max(1, len(plan)),
        "complete": nxt is None,
    }
