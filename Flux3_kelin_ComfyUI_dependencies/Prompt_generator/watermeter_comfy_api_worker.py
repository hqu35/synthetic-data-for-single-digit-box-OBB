#!/usr/bin/env python3
"Patch an API-format ComfyUI prompt graph per manifest row. No server calls.\n\nExport your VERIFIED working ComfyUI workflow with 'Save (API Format)' first.\nNode IDs in the template must be the IDs from that exported workflow.\n"

from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path


def patch_graph(graph: dict, row: dict, mapping: dict) -> dict:
    graph = copy.deepcopy(graph)
    if len(mapping["reference_node_ids"]) != 10:
        raise ValueError("Expected exactly ten LoadImage node IDs")
    if len(row["reference_images_ordered"]) != 10:
        raise ValueError("Manifest row must have ten reference images")
    for node_id, path in zip(
        mapping["reference_node_ids"], row["reference_images_ordered"]
    ):
        node = graph[str(node_id)]
        if node["class_type"] != "LoadImage":
            raise ValueError(f"Node {node_id} is not a LoadImage node")
        # ComfyUI LoadImage uses image names relative to its input directory.
        node["inputs"]["image"] = Path(path).name
    graph[str(mapping["prompt_node_id"])]["inputs"][
        mapping.get("prompt_input", "text")
    ] = row["prompt"]
    graph[str(mapping["sampler_node_id"])]["inputs"]["seed"] = row[
        "diffusion_seed"
    ]
    if "prefix_node_id" in mapping:
        graph[str(mapping["prefix_node_id"])]["inputs"]["filename_prefix"] = (
            row["id"]
        )
    return graph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-template", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    graph = json.loads(Path(args.api_template).read_text())
    if "nodes" in graph and "links" in graph:
        raise ValueError(
            "Provided GUI workflow JSON, not an API-format graph; export 'Save (API Format)'"
        )
    mapping = json.loads(Path(args.mapping).read_text())
    dest = Path(args.out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for line in Path(args.manifest).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        patched = patch_graph(graph, row, mapping)
        path = dest / (row["id"] + ".json")
        path.write_text(
            json.dumps({"prompt": patched}, ensure_ascii=False, indent=2)
        )
        paths.append(path)
    print(
        (
            f"Prepared {len(paths)} API job request JSON "
            f"files in {dest}. Nothing has been "
            f"submitted."
        )
    )


if __name__ == "__main__":
    main()
