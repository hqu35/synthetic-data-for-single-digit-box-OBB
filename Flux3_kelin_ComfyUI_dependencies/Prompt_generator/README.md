<!-- recursive-summary:start -->
## Directory overview

Builds prompts from mask geometry; digit identities and rolling states are sampled independently of the mask.

Generate a new mask/prompt pair from the repository root:

```sh
python3 Flux3_kelin_ComfyUI_workflow/Prompt_generator/watermeter_generate_layout_prompt.py --output /private/tmp/meter-prompt-example --mask-seed 20261115 --prompt-seed 539
```

The prompt specifies nine appearance references followed by the mask. Bounding boxes in the prompt are text hints; no box-aware enforcement or FLUX inference is performed here.

V2 is the default. Add `--windows 6` for six windows or `--mask-version v1`
to use V1. For V2, the gray strips carry numerals; the white margins represent
surrounding window structure. The bounding boxes target the gray strips.
See the [V2 guide](../../2D_Mask_for_Diffusion/2d_mask_4_diffusion_V2/README.md).

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [watermeter\_build\_manifest.py](watermeter_build_manifest.py) | Build a pilot manifest from reference folders and native mask-worker samples. |
| [watermeter\_comfy\_api\_worker.py](watermeter_comfy_api_worker.py) | Patch an API-format ComfyUI prompt graph per manifest row. No server calls. |
| [watermeter\_generate\_layout\_prompt.py](watermeter_generate_layout_prompt.py) | Generate one 2D mask and its immediately matched water-meter prompt. |
| [watermeter\_geometry.py](watermeter_geometry.py) | Load mask-worker geometry for prompt generation. |
| [watermeter\_prompt\_generator.py](watermeter_prompt_generator.py) | Deterministic water-meter register prompt configurations; no ML dependencies. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
