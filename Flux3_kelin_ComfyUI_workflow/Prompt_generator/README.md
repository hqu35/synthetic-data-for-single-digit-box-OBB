# Water-meter mask and prompt integration

Generate one mask and its matching prompt in a new output directory:

```sh
python3 'Flux3_kelin_ComfyUI_workflow/Prompt generator/watermeter_generate_layout_prompt.py' \
  --output 2d_mask_4_diffusion/exp/my_mask_prompt \
  --mask-seed 20261115 --prompt-seed 539 --scenario one_rolling
```

The mask worker currently supports exactly five positions. The mask supplies the position count and left-to-right geometry only. The prompt generator independently chooses digit identities and rolling states from the prompt seed. FLUX guidance rectangles enclose the complete continuous curved strip boundary and use outward-rounded integer `[top,left,bottom,right]` coordinates in 0–1000 relative to the whole mask image. YOLO OBB labels remain independent and normalized to 0–1.

`mask/conditioning.png` is the geometry reference; `mask/preview.png` visualizes geometry and FLUX rectangles. `mask/flux_bboxes.json`, `mask/annotations.txt` and `mask/geometry.json` contain the underlying annotations. `prompt.txt`, `prompt_config.json`, and `layout_prompt.json` describe the matched prompt. The mask path in `layout_prompt.json` is relative to that JSON file.

The separate `watermeter_build_manifest.py` accepts mask sample directories via `--layouts-dir`, plus nine or more disjoint appearance references in each of `--clear-dir` and `--noisy-dir`. Its bounding boxes are text guidance unless a box-aware runtime is configured. The prompt assumes nine appearance references followed by the mask as reference 9. This code does not run FLUX or ComfyUI. If the workflow crops or pads the reference image, boxes must be transformed to the resulting canvas.
