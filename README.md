# Hearts Addon — consumable heart GeckoLib model (Forge 1.20.1, GeckoLib 4)

Context repo for AI assistants: a procedural generator plus its generated assets and preview renders.
Companion to [flesh-spread-faster-addon](https://github.com/6PateL/flesh-spread-faster-addon).

- `heart.jpg` — reference concept art.
- `tools/gen_heart.py` — single-file generator (Python 3, numpy, Pillow): geometry, 256x256 texture + glowmask,
  animations (idle / spawn / consume / break). Run `python tools/gen_heart.py [--out <assets/modid dir>]`.
- `output/` — `geo/heart.geo.json`, `animations/heart.animation.json`, `textures/entity/heart(.png|_glowmask.png)`.
- `tools/preview/` — renders (front/side/back/3-4, texture sheet, animation frames) for visual checks.

1 block = 16 px.

## `animation.heart.break`
One-shot (1.0 s, `hold_on_last_frame`), meant to play **after** the player has broken the heart, not while it is
being mined. Impact squash and shudder, then the cracks open and show the glowing core, then the 8 ventricle shards
(`shard_*` bones under `body`), both atria and the vessels burst outward, tumble, fall and shrink to nothing while
the sparks flash and scatter. Trigger it from the break event (e.g. GeckoLib `triggerAnim`), then remove the
entity about 1 s later.
