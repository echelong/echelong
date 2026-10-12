# Asset provenance

These four files are the only images the profile README uses.

| File | Size | What it is |
| :--- | :--- | :--- |
| `cobalt-hero.gif` | 1200 × 273, 48 frames, 4.8 s loop | Animated hero banner |
| `cobalt-hero.png` | 1200 × 273 | Still shown when the viewer prefers reduced motion |
| `crawler-patrol.gif` | 960 × 240, 18 frames, 1.26 s loop | CRAWLER_01 walking band |
| `crawler-patrol.png` | 960 × 240 | Still shown when the viewer prefers reduced motion |

## Hero banner

- **Key art.** The spider and city scene come from key art supplied by the repository owner. It was cropped to the banner area and upscaled 4x with Real-ESRGAN (`RealESRGAN_x4plus`, BSD-3-Clause), then resized to 1200 px wide.
- **Terminal panel and unit label.** The panel on the right of the original art was removed and re-typeset. The replacement text is set in Share Tech Mono (SIL Open Font License 1.1).
- **Motion.** The typing terminal, the visor pulse, the light sweep and the slight body movement are composited frame by frame with Pillow, NumPy and OpenCV.

## CRAWLER_01 band

- **Model and animation.** Original work for this profile. The spider is a procedural model built and rendered in Blender (EEVEE). Its eight legs are posed by inverse kinematics from an alternating-tetrapod gait, so each foot stays planted while the body moves. One gait cycle is one loop.
- **Reflection.** The wet-floor reflection is a mirrored copy of the scene seen through a translucent floor.
- **HUD text.** Set in Michroma and Share Tech Mono (both SIL Open Font License 1.1). The "gait phase" indicator is driven by the same gait schedule as the legs. It is not live data.

## Encoding

GIFs are encoded with ffmpeg using one shared palette, then optimised with gifsicle (`-O3`, mild lossy LZW). Image metadata is stripped.

## What is not in this repository

Source art, Blender scenes, render frames, fonts and the upscaling model are kept outside this repository to keep it small.

## Licence

No licence is granted for these images. They are part of the Cobalt identity. Ask before reusing them.
