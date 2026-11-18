#!/usr/bin/env python3
"""Deterministic water-meter register prompt configurations; no ML dependencies."""

from __future__ import annotations
import random
from typing import Any

T_VALUES = (
    0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90, 0.95, 1.0
)
MODES = ("centered_clean", "centered_neighbors", "rolling")
# The neighboring-symbol visibility is a visual request, not a measured label.
NEIGHBOR_VISIBILITY = (5, 10, 20)
SCENARIOS = ("all_centered", "one_rolling", "mixed_rolling", "many_rolling")


def generate_configuration(
    digit_count: int, seed: int, scenario: str | None = None
) -> dict[str, Any]:
    if digit_count not in (5, 6):
        raise ValueError("Expected 5 or 6 digit windows, matching the layout")
    rng = random.Random(seed)
    scenario = scenario or rng.choice(SCENARIOS)
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario}")
    rolls = {
        "all_centered": 0,
        "one_rolling": 1,
        "mixed_rolling": rng.randint(1, max(1, digit_count // 2)),
        "many_rolling": rng.randint(max(2, digit_count // 2), digit_count),
    }[scenario]
    rolling_slots = set(rng.sample(range(digit_count), rolls))
    windows = []
    for index in range(digit_count):
        d = rng.randrange(10)
        if index in rolling_slots:
            position = rng.choice(T_VALUES[1:-1])
            windows.append(
                {
                    "slot": index + 1,
                    "mode": "rolling",
                    "current_digit": d,
                    "next_digit": (d + 1) % 10,
                    "upper_visible_pct": round(100 * (1 - position) - 2.5, 1),
                    "lower_visible_pct": round(100 * position - 2.5, 1),
                }
            )
        else:
            mode = rng.choice(("centered_clean", "centered_neighbors"))
            windows.append(
                {
                    "slot": index + 1,
                    "mode": mode,
                    "current_digit": d,
                    "next_digit": (d + 1) % 10,
                    "neighbor_visibility_hint_pct": (
                        rng.choice(NEIGHBOR_VISIBILITY)
                        if mode == "centered_neighbors"
                        else 0
                    ),
                }
            )
    return {
        "digit_count": digit_count,
        "scenario": scenario,
        "config_seed": seed,
        "windows": windows,
    }


def make_prompt(configuration: dict, flux_boxes: list[list[int]],
                mask_version: str = "v2") -> str:
    """Return FLUX caption plus layout rows. The boxes are SOFT layout hints."""
    windows = configuration["windows"]
    if len(windows) != configuration["digit_count"] or len(windows) != len(
        flux_boxes
    ):
        raise ValueError(
            "Prompt windows and layout boxes have different counts"
        )
    sentences, rows = [], []
    for w, bbox in zip(windows, flux_boxes):
        i, d, mode = (w["slot"], w["current_digit"], w["mode"])
        if mode == "rolling":
            successor = w["next_digit"]
            upper = w["upper_visible_pct"]
            lower = w["lower_visible_pct"]
            desc = (
                "inside this single digit window, show two consecutive "
                "numerals on one continuous mechanical wheel surface. "
                f"The upper portion shows numeral {d}, occupying approximately "
                f"{upper:.1f}% of the vertical numeral-bearing region. "
                f"The lower portion shows numeral {successor}, occupying "
                f"approximately {lower:.1f}% of that vertical region. "
                f"Numeral {d} must appear ABOVE numeral "
                f"{successor}, never beside it. Both belong to one wheel, "
                "not two separate windows"
            )
        elif mode == "centered_neighbors":
            v = w["neighbor_visibility_hint_pct"]
            desc = (
                f"mechanical digit wheel {i} showing {d} precisely centered, "
                f"with only about {v}% of adjacent wheel numerals visible "
                "at the upper and lower window edges"
            )
        else:
            desc = (
                f"mechanical digit wheel {i} "
                f"showing numeral {d} centered, "
                "without visible neighboring numerals"
            )
        sentences.append(f"Window {i}: {desc}.")
        rows.append({"id": f"digit_{i}", "bbox": bbox, "desc": desc})
    # Layout rows are prompt text unless a box-aware node is used.
    if mask_version == "v2":
        guide = (
            "In the geometry guide, each gray strip marks the numeral-bearing "
            "surface of a digit wheel; place its digits within that strip. "
            "The white margins beside it represent surrounding window "
            "structure and environment, not numeral-bearing surfaces. "
            "Black gaps separate neighboring windows. Each bounding box "
            "corresponds to a gray strip. "
        )
    else:
        guide = ""
    return (
        f"Photorealistic close-up of one mechanical water-meter register with exactly "
        f"{configuration['digit_count']} digit windows in one left-to-right row. "
        "Reference images 0 through 8 supply "
        "photographic appearance only: real wheel material, "
        "numeral typography, texture, lighting, and exposure. "
        "Learn realistic photographic imperfections from those references, "
        "including blur, dust, dirt, mud stains, water droplets, and smudges. "
        "Reference image 9 is a grayscale GEOMETRY "
        "GUIDE, not a texture source. "
        + guide
        + "Keep the wheel layout aligned with reference image 9, "
        "preserving spacing, "
        "the camera perspective, and the full vertical rolling numeral strips. "
        + " ".join(sentences)
        + " Use the following normalized FLUX layout "
        "hints, with each bbox in "
        "[top,left,bottom,right] order on a 0–1000 canvas: "
        + json_dumps(rows)
        + ". Render one coherent realistic register; no markers, bounding-box outlines, "
        "explanatory text, dots, or collage."
    )


def json_dumps(value):
    import json

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
