<!-- recursive-summary:start -->
## Directory overview

Example in which the geometry mask and prompt digit/rolling configuration are generated independently.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [layout\_prompt.json](layout_prompt.json) | Combined layout and prompt configuration. |
| [prompt.txt](prompt.txt) | Generated prompt with geometry hints. |
| [prompt\_config.json](prompt_config.json) | Independently sampled digit and rolling settings. |

### Subdirectories

| Directory | Role |
|---|---|
| [mask/](mask/) | Generated geometry guide, metadata, FLUX boxes and YOLO OBB labels. |

### Summary

The sample illustrates the independent mask-to-prompt handoff; no FLUX inference is included.

<!-- recursive-summary:end -->
