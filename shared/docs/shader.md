# Plastic shader reproduction and scale adaptation

The primary specification is the supplied `Plastic_Shader_操作指南.md`, read before
implementation. Its source is [SILVER PUNK — Plastic material in Blender](https://www.youtube.com/watch?v=AYDjqXizaYs).
The accompanying screenshots were also inspected. They include intermediate
states; the strongly mottled intermediate bump is not the final material target.

| Node | Fractal | Scale | Detail | Roughness | Lacunarity | Distortion |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Noise A | 3D fBM | 100 | 10 | 1 | 2 | 0.1 |
| Noise B | 3D fBM | 20 | 8 | 0.9 | 2 | 0.1 |
| Noise C | 3D Multifractal | 30 | 10 | 1 | 2 | 2 |

Generated coordinates feed one identity Point Mapping node, which feeds every
Noise Vector input. Noise A Fac feeds both color and roughness ramps. B Fac and
C Fac feed separate inputs of **ShaderNodeMath / MULTIPLY**. That output feeds
Bump Height; inverted Bump Normal feeds Principled Normal. Noise normalization
is enabled. No unavailable or renamed noise settings were encountered in Blender
5.1.1. Material nodes use Blender's supported shader API; camera processing avoids
Blender 5's substantially changed compositor interface by running a deterministic
image-processing stage inside its Python rendering process.

Reference-dark preset: color ramp endpoints at positions 0 and 0.5, using linear
RGBA (0.022, 0.024, 0.027, 1) and (0.006, 0.007, 0.008, 1). These approximate the
guide's uncertain near-black endpoints; the video did not establish exact final
colors or complete lighting. Roughness ramp positions 0.3/0.8 use black/white
outputs. Bump is inverted, strength 0.05, distance 1.0. Principled metallic is 0,
IOR 1.5, and unspecified inputs preserve Blender's defaults.

Cream adaptation: the same graph uses configurable warm off-white endpoints with
small aging/color variation. Roughness outputs are 0.55–0.80. At radius 1.9–2.2 and
width 0.76–0.84, bump distance is reduced to **0.004** and strength sampled in
**0.01–0.025**. This scale adaptation is deliberate; it does not claim to reproduce
the video's dark semi-gloss finish. Ink combines color and roughness with the same
cylindrical alpha mask, preserving printed edges. Separate materials handle pins,
rims, axle and viewing frame.

The diagnostic suite renders basic, reference-dark and cream materials with
identical geometry, camera, lighting and wheel states. The exported node/link
reports and actual-Blender regression checks verify the prescribed topology,
noise modes/scales, shared Mapping, Math Multiply, inverted bump, and reference
bump values. Material comparisons establish implementation consistency; lighting,
shape and color uncertainty prevent claiming an exact visual copy of the video.
