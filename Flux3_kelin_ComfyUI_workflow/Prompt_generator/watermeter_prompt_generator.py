#!/usr/bin/env python3
"""Deterministic water-meter register prompt configurations; no ML dependencies."""
from __future__ import annotations
import random
from typing import Any

T_VALUES = (
    0.0,
    0.05,
    0.10,
    0.20,
    0.35,
    0.50,
    0.65,
    0.80,
    0.90,
    0.95,
    1.0,
)
MODES = ("centered_clean", "centered_neighbors", "rolling")
# The neighboring-symbol visibility is a visual request, not a measured label.
NEIGHBOR_VISIBILITY = (5, 10, 20)
SCENARIOS = (
    "all_centered",
    "one_rolling",
    "mixed_rolling",
    "many_rolling",
)


def generate_configuration(
    digit_count: int, seed: int, scenario: str | None = None
) -> dict[str, Any]:
    if digit_count not in (5, 6):
        raise ValueError(
            "Expected 5 or 6 digit windows, matching the layout"
        )
    rng = random.Random(seed)
    scenario = scenario or rng.choice(SCENARIOS)
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario}")
    rolls = {
        "all_centered": 0,
        "one_rolling": 1,
        "mixed_rolling": rng.randint(
            1, max(1, digit_count // 2)
        ),
        "many_rolling": rng.randint(
            max(2, digit_count // 2), digit_count
        ),
    }[scenario]
    rolling_slots = set(
        rng.sample(range(digit_count), rolls)
    )
    windows = []
    for index in range(digit_count):
        d = rng.randrange(10)
        if index in rolling_slots:
            progress = rng.choice(
                T_VALUES[1:-1]
            )  # avoid double-counting t=1 as centered
            windows.append(
                {
                    "slot": index + 1,
                    "mode": "rolling",
                    "current_digit": d,
                    "next_digit": (d + 1) % 10,
                    "progress": progress,
                }
            )
        else:
            mode = rng.choice(
                ("centered_clean", "centered_neighbors")
            )
            windows.append(
                {
                    "slot": index + 1,
                    "mode": mode,
                    "current_digit": d,
                    "next_digit": (d + 1) % 10,
                    "progress": 0.0,
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


def make_prompt(
    configuration: dict, flux_boxes: list[list[int]]
) -> str:
    """Return FLUX caption plus layout rows. The boxes are SOFT layout hints."""
    windows = configuration["windows"]
    if len(windows) != configuration['digit_count'] or len(
        windows
    ) != len(flux_boxes):
        raise ValueError(
            "Prompt windows and layout boxes have different counts"
        )
    sentences, rows = [], []
    for w, bbox in zip(windows, flux_boxes):
        i, d, mode = (
            w["slot"],
            w["current_digit"],
            w["mode"],
        )
        if mode == "rolling":
            successor = w["next_digit"]
            t = w["progress"]
            desc = (
                f"mechanical digit wheel {i}, rotating upward from numeral {d} "
                f"to numeral {successor}, with normalized roll progress {t:.2f} "
                f"(0 = {d} centered, 1 = {successor} centered); departing numeral "
                f"{d} appears above incoming numeral {successor} below"
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
        rows.append(
            {"id": f"digit_{i}", "bbox": bbox, "desc": desc}
        )
    # Layout rows are prompt text unless a box-aware node is used.
    return (
        f"Photorealistic close-up of one mechanical water-meter register with exactly "
        f"{configuration['digit_count']} digit windows in one left-to-right row. "
        "Reference images 0 through 8 supply "
        "photographic appearance only: real wheel material, "
        "numeral typography, texture, lighting, and exposure. "
        "Reference image 9 is a grayscale GEOMETRY "
        "GUIDE, not a texture source. "
        "Keep every digit window aligned with reference image 9, preserving spacing, "
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

    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    )
