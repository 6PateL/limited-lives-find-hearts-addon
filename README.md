# Life Hearts — аддон до Limited Lives (Forge 1.20.1, GeckoLib 4)

У світі зрідка з'являються живі серця (на поверхні й у печерах, біля гравців). Кілька ударів — серце розлітається на
шматки, а той, хто його розбив, отримує ще одне життя: урочистий звук, золото-червоне сяйво й «+1 ЖИТТЯ» на екрані.
ПКМ по серцю — поглинути його (теж +1 життя). Якщо життя вже повні — серце лікує.

- Залежності: GeckoLib 4 (обов'язково), Limited Lives (необов'язково; без нього серце дає поглинання).
- Конфіг `config/lifehearts-common.toml`: частота й шанс появи, відстань, ліміт поруч, час життя серця, кількість ударів,
  дозволені життя понад максимум.
- Дебаг: «Виклик серця» у творчій вкладці «Інструменти».
- Збірка: GitHub Actions (`.github/workflows/build.yml`), jar в артефактах.

Моделі й анімації: `tools/gen_heart.py` → `output/` (копія в `src/main/resources/assets/lifehearts/`).

---

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
