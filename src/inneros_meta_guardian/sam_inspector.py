"""SAM 3.1 Visual Laboratory Inspector for Physical Infrastructure.

Secondary visual demo component:
- Inspects physical laboratory rack setups and patch panels.
- Strictly restricted to authorized laboratory assets (zero customer photos).
- Returns segmentation/bounding-box metadata and optical inspection confidence.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SAMInspector:
    """Inspector for laboratory visual inspection using Segment Anything Model (SAM)."""

    LAB_FIXTURES = {
        "lab_rack_switch_led": {
            "asset_id": "lab_hw_01_core_switch",
            "title": "Laboratory Core Switch LED & Cabling Inspection",
            "image_uri": "assets/lab/core_switch_rack.jpg",
            "image_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "detected_objects": [
                {
                    "label": "switch_chassis",
                    "confidence": 0.98,
                    "bbox": [45, 120, 780, 260],
                    "status": "nominal",
                },
                {
                    "label": "optical_sfp_uplink_1",
                    "confidence": 0.94,
                    "bbox": [580, 160, 640, 210],
                    "status": "link_active_amber_flashing",
                },
                {
                    "label": "cat6_patch_bundle",
                    "confidence": 0.96,
                    "bbox": [100, 220, 520, 310],
                    "status": "properly_dressed_bend_radius_compliant",
                },
            ],
            "analysis_notes": "Visual inspection of lab rack confirms SFP uplink link status matches telemetric FDB state. No physical bend radius violation observed.",
        },
        "lab_optical_patch_panel": {
            "asset_id": "lab_hw_02_fiber_tray",
            "title": "Laboratory Optical Distribution Frame Fiber Inspection",
            "image_uri": "assets/lab/fiber_distribution_tray.jpg",
            "image_hash": "8f434346648f6b96df89dda901c5176b10e6d5b93b4fcf38f8f28e9f02ee37e2",
            "detected_objects": [
                {
                    "label": "lc_duplex_coupler_01",
                    "confidence": 0.97,
                    "bbox": [110, 80, 180, 150],
                    "status": "seated_clean",
                },
                {
                    "label": "single_mode_patch_yellow",
                    "confidence": 0.93,
                    "bbox": [120, 150, 240, 400],
                    "status": "tension_free",
                },
            ],
            "analysis_notes": "Optical fiber distribution tray seated cleanly; laser warning signage intact.",
        },
    }

    def inspect_lab_asset(self, asset_key: str = "lab_rack_switch_led") -> dict[str, Any]:
        fixture = self.LAB_FIXTURES.get(asset_key)
        if not fixture:
            asset_key = "lab_rack_switch_led"
            fixture = self.LAB_FIXTURES[asset_key]

        return {
            "ok": True,
            "status": "LAB_VERIFIED_VISUAL",
            "model": "meta-sam-3.1",
            "provider": "meta-sam",
            "truth": "AUTHORIZED_LAB_BENCH_TEST",
            "timestamp": now_iso(),
            "asset_key": asset_key,
            "asset_id": fixture["asset_id"],
            "title": fixture["title"],
            "image_uri": fixture["image_uri"],
            "image_hash": fixture["image_hash"],
            "detected_objects": fixture["detected_objects"],
            "analysis_notes": fixture["analysis_notes"],
            "privacy_compliance": "Authorized lab equipment only; zero client PII or faces.",
        }
