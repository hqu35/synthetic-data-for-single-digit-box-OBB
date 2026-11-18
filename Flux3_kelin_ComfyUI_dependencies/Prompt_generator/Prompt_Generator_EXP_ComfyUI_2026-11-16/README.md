# One V2 mask, three ComfyUI prompts

The shared geometry guide is [mask/conditioning.png](mask/conditioning.png).
The [preview](mask/preview.png) overlays OBBs on the gray strips.
All prompts use the same five FLUX boxes and the original V2 sample.
YOLO OBB labels are in [annotations.txt](mask/annotations.txt).

- [Prompt 1](prompt_01.txt): all centered, seed 539.
- [Prompt 2](prompt_02.txt): one rolling digit, seed 540.
- [Prompt 3](prompt_03.txt): many rolling digits, seed 541.

Digit identities and rolling states are generated independently of the mask.
These are text prompts; no FLUX or ComfyUI inference was performed.
