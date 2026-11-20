"""Generator for the consumable "heart" GeckoLib model (Forge 1.20.1, GeckoLib 4).

Outputs (into ../output/ unless --out <assets/modid dir> is given):
  geo/heart.geo.json, animations/heart.animation.json,
  textures/entity/heart.png + heart_glowmask.png (GeckoLib AutoGlowingGeoLayer)
and preview renders into ./preview/.
Units: 1 block = 16 px. Texture 256x256, per-face UV at 2 texels per pixel, no overlaps.
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output")
if "--out" in sys.argv:
    OUT = sys.argv[sys.argv.index("--out") + 1]
PREVIEW = os.path.join(HERE, "preview")
NAME = "heart"
TEX = 256
DENSITY = 2.0


# ============================================================================ model + kinematics
class Model:
    def __init__(self):
        self.bones, self.by = [], {}

    def bone(self, name, parent, pivot, rot=(0, 0, 0)):
        b = dict(name=name, parent=parent, pivot=list(map(float, pivot)), rotation=list(map(float, rot)), cubes=[])
        self.bones.append(b)
        self.by[name] = b
        return b

    def cube(self, bone, origin, size, mat, faces=None, density=None):
        c = dict(origin=list(map(float, origin)), size=list(map(float, size)), mat=mat, faces=faces or {},
                 density=density)
        self.by[bone]["cubes"].append(c)
        return c

    def box(self, bone, x0, y0, z0, x1, y1, z1, mat, faces=None):
        return self.cube(bone, (x0, y0, z0), (x1 - x0, y1 - y0, z1 - z0), mat, faces)


def rot_matrix(fx, fy, fz):
    """GeckoLib/Bedrock file convention: actual right-handed angles (-x, -y, z), applied X then Y then Z."""
    ax, ay, az = np.radians([-fx, -fy, fz])
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def bone_matrices(model, anim=None):
    mats = {}
    for b in model.bones:
        rot, pos, scl = np.array(b["rotation"]), np.zeros(3), np.ones(3)
        if anim and b["name"] in anim:
            r, p, s = anim[b["name"]]
            rot = rot + np.array(r)
            pos = np.array(p, dtype=float) * np.array([-1, 1, 1])  # file position X is inverted
            scl = np.array(s, dtype=float)
        p = np.array(b["pivot"])
        m = np.eye(4)
        m[:3, :3] = rot_matrix(*rot) @ np.diag(scl)
        t1, t2, tp = np.eye(4), np.eye(4), np.eye(4)
        t1[:3, 3], t2[:3, 3], tp[:3, 3] = p, -p, pos
        mats[b["name"]] = (mats[b["parent"]] if b["parent"] else np.eye(4)) @ (tp @ t1 @ m @ t2)
    return mats


def cube_corners(c):
    x0, y0, z0 = c["origin"]
    sx, sy, sz = c["size"]
    return x0, y0, z0, x0 + sx, y0 + sy, z0 + sz


FACE_CORNERS = {  # (TL, TR, BL) as seen from outside
    "north": lambda a, b, c, d, e, f: ((d, e, c), (a, e, c), (d, b, c)),
    "south": lambda a, b, c, d, e, f: ((a, e, f), (d, e, f), (a, b, f)),
    "east": lambda a, b, c, d, e, f: ((d, e, f), (d, e, c), (d, b, f)),
    "west": lambda a, b, c, d, e, f: ((a, e, c), (a, e, f), (a, b, c)),
    "up": lambda a, b, c, d, e, f: ((a, e, c), (d, e, c), (a, e, f)),
    "down": lambda a, b, c, d, e, f: ((a, b, f), (d, b, f), (a, b, c)),
}
FACE_DIMS = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}


def posed_bbox(model, mats):
    pts = []
    for b in model.bones:
        m = mats[b["name"]]
        for c in b["cubes"]:
            a, bb, cc, d, e, f = cube_corners(c)
            for x in (a, d):
                for y in (bb, e):
                    for z in (cc, f):
                        pts.append((m @ np.array([x, y, z, 1.0]))[:3])
    pts = np.array(pts)
    return pts.min(axis=0), pts.max(axis=0)


# ============================================================================ build
CENTER_Y = 11.0
SLABS = [  # y0, y1, width(x), depth(z), centre x, centre z   (apex at the bottom, broad base at the top)
    (1.0, 2.2, 5.0, 4.5, 0.8, 0.3),
    (2.2, 3.8, 9.0, 7.0, 0.5, 0.2),
    (3.8, 6.0, 11.5, 8.5, 0.3, 0.0),
    (6.0, 8.5, 13.0, 9.0, 0.0, 0.0),
    (8.5, 11.0, 13.5, 9.5, 0.0, 0.0),
    (11.0, 13.0, 12.5, 9.0, 0.0, 0.2),
    (13.0, 14.2, 10.0, 7.0, 0.0, 0.5),
]


def tube(m, bone, x0, y0, z0, x1, y1, z1, mat, open_faces):
    lumen = "lumen_blue" if mat == "vessel_blue" else "lumen_red"
    m.box(bone, x0, y0, z0, x1, y1, z1, mat, faces={f: lumen for f in open_faces})


SHARD_CUTS = (("x", 0.0), ("z", 0.0), ("y", 6.0))   # 2 x 2 x 2 = 8 fragments
CUT_FACES = {"x": ("east", "west"), "y": ("up", "down"), "z": ("south", "north")}  # (low piece, high piece)
AXIS = {"x": 0, "y": 1, "z": 2}


def split_body(m):
    """Cut every cube of the "body" bone along SHARD_CUTS and move the pieces onto shard bones.
    Freshly exposed cut faces are painted as inner flesh ("flesh_inner")."""
    pieces = [dict(c) for c in m.by["body"]["cubes"]]
    for ax, v in SHARD_CUTS:
        i, out = AXIS[ax], []
        for c in pieces:
            a0, a1 = c["origin"][i], c["origin"][i] + c["size"][i]
            if a0 + 0.25 < v < a1 - 0.25:            # really crosses the cut -> two pieces
                lo, hi = dict(c), dict(c)
                lo["origin"], lo["size"], lo["faces"] = list(c["origin"]), list(c["size"]), dict(c["faces"])
                hi["origin"], hi["size"], hi["faces"] = list(c["origin"]), list(c["size"]), dict(c["faces"])
                lo["size"][i] = v - a0
                hi["origin"][i], hi["size"][i] = v, a1 - v
                lo["faces"][CUT_FACES[ax][0]] = "flesh_inner"
                hi["faces"][CUT_FACES[ax][1]] = "flesh_inner"
                out += [lo, hi]
            else:
                out.append(c)
        pieces = out
    groups = {}
    for c in pieces:
        ctr = [c["origin"][k] + c["size"][k] / 2 for k in range(3)]
        key = "".join(("hi" if ctr[1] > SHARD_CUTS[2][1] else "lo",
                       "_e" if ctr[0] > SHARD_CUTS[0][1] else "_w",
                       "s" if ctr[2] > SHARD_CUTS[1][1] else "n"))
        groups.setdefault(key, []).append(c)
    m.by["body"]["cubes"] = []
    m.shards = []
    for key in sorted(groups):
        cs = groups[key]
        vol = [c["size"][0] * c["size"][1] * c["size"][2] for c in cs]
        ctr = np.array([sum((c["origin"][k] + c["size"][k] / 2) * w for c, w in zip(cs, vol)) / sum(vol)
                        for k in range(3)])
        name = f"shard_{key}"
        m.bone(name, "body", [round(float(v), 2) for v in ctr])
        m.by[name]["cubes"] = cs
        m.shards.append((name, ctr))


def build(rng):
    m = Model()
    m.bone("root", None, (0, CENTER_Y, 0))
    m.bone("heart", "root", (0, 8, 0))          # the beating part
    m.bone("body", "heart", (0, 8, 0))

    # ---- ventricles: rounded voxel slabs (3 crossed boxes each -> octagonal section)
    for (y0, y1, w, d, cx, cz) in SLABS:
        m.box("body", cx - w / 2, y0, cz - d / 2 + 1, cx + w / 2, y1, cz + d / 2 - 1, "muscle")
        m.box("body", cx - w / 2 + 1, y0, cz - d / 2, cx + w / 2 - 1, y1, cz + d / 2, "muscle")
        m.box("body", cx - w / 2 + 0.5, y0, cz - d / 2 + 0.5, cx + w / 2 - 0.5, y1, cz + d / 2 - 0.5, "muscle")
    # muscle bands on the lower front-right / back-left (voxel striations like the reference)
    for (x, y0, y1, z) in ((-5.2, 4.0, 10.5, -4.5), (-4.0, 3.2, 9.8, -4.6), (4.2, 4.5, 10.2, 4.7)):
        m.box("body", x - 0.5, y0, z - 0.5, x + 0.5, y1, z + 0.5, "muscle_band")

    # ---- atria
    m.bone("atrium_right", "heart", (5, 12, 0))   # model +X = viewer's left when looking at the front (-Z)
    m.box("atrium_right", 3.0, 10.5, -2.6, 8.6, 14.6, 2.6, "atrium_r")
    m.box("atrium_right", 3.7, 10.0, -2.0, 8.0, 15.3, 2.0, "atrium_r")
    m.box("atrium_right", 3.5, 11.0, -3.3, 7.6, 14.0, 3.0, "atrium_r")
    m.bone("atrium_left", "heart", (-5, 12, 1))
    m.box("atrium_left", -8.6, 10.8, -1.2, -3.4, 14.6, 4.0, "atrium_l")
    m.box("atrium_left", -8.0, 10.2, -0.6, -4.0, 15.1, 3.4, "atrium_l")
    m.box("atrium_left", -7.8, 11.3, -1.9, -4.0, 14.0, 4.6, "atrium_l")

    # ---- great vessels (own bone so they can wobble a little on each beat)
    m.bone("vessels", "heart", (0, 14, 0))
    # aorta: ascends from the centre, arches over to -X and runs down the back
    tube(m, "vessels", -1.3, 13.0, -1.3, 1.3, 18.5, 1.3, "vessel_red", [])
    tube(m, "vessels", -6.2, 18.5, -1.1, 1.3, 21.0, 1.5, "vessel_red", [])
    tube(m, "vessels", -6.2, 13.5, 1.5, -3.6, 18.5, 4.1, "vessel_red", [])
    for i, x in enumerate((-0.4, -2.6, -4.8)):   # three branches with open tops
        h = (3.2, 2.6, 2.2)[i]
        tube(m, "vessels", x - 0.7, 21.0, -0.4, x + 0.7, 21.0 + h, 1.0, "vessel_red", ["up"])
    # superior vena cava (blue) on top of the right atrium, plus a forward branch
    tube(m, "vessels", 3.7, 14.5, -1.2, 6.1, 21.5, 1.2, "vessel_blue", ["up"])
    tube(m, "vessels", 4.1, 17.8, -4.8, 5.9, 19.6, -1.2, "vessel_blue", ["north"])
    # pulmonary trunk (blue) from the front, splitting toward -X with a big open mouth
    tube(m, "vessels", -1.2, 11.0, -5.6, 1.4, 13.6, -3.0, "vessel_blue", [])
    tube(m, "vessels", -3.3, 13.2, -5.0, 0.2, 15.5, -2.4, "vessel_blue", [])
    tube(m, "vessels", -9.8, 14.0, -4.6, -3.3, 16.3, -2.4, "vessel_blue", ["west"])
    # pulmonary veins: little open stubs on both sides
    for (y, z) in ((8.4, -0.8), (11.6, 0.6)):
        tube(m, "vessels", 7.0, y, z - 0.9, 9.8, y + 1.8, z + 0.9, "vessel_red", ["east"])
    for (y, z) in ((9.0, 1.2), (12.0, 2.4)):
        tube(m, "vessels", -9.8, y, z - 0.9, -7.0, y + 1.8, z + 0.9, "vessel_red", ["west"])

    # ---- coronary vessels creeping over the surface (front artery + vein, side artery, back vein)
    def front_z(k):
        y0, y1, w, d, cx, cz = SLABS[k]
        return cz - d / 2

    lad_x = [0.8, 0.4, 0.0, -0.4, -0.7, -0.8]
    for k in range(0, 6):
        y0, y1 = SLABS[k][0], SLABS[k][1]
        z = front_z(k) - 0.45
        m.box("body", lad_x[k] - 0.3, y0, z, lad_x[k] + 0.3, y1, z + 0.7, "artery")
    for k, (dx, ln) in ((3, (1, 2.4)), (4, (-1, 2.2)), (2, (1, 1.8))):
        y = (SLABS[k][0] + SLABS[k][1]) / 2
        z = front_z(k) - 0.4
        x = lad_x[k]
        x0, x1 = (x, x + ln) if dx > 0 else (x - ln, x)
        m.box("body", x0, y - 0.25, z, x1, y + 0.25, z + 0.6, "artery")
    for k in range(1, 6):   # blue vein along the front, toward -X
        y0, y1 = SLABS[k][0], SLABS[k][1]
        x = -2.6 - 0.25 * k
        z = front_z(k) - 0.4
        m.box("body", x - 0.25, y0, z, x + 0.25, y1, z + 0.6, "cvein")
    # groove artery around the +X side under the right atrium
    m.box("body", 6.2, 10.4, -4.4, 6.8, 10.9, 3.8, "artery")
    m.box("body", 6.3, 6.5, -4.4, 6.8, 10.9, -3.8, "artery")
    # back vein
    for k in range(1, 6):
        y0, y1, w, d, cx, cz = SLABS[k]
        x = 1.0 - 0.3 * k
        z = cz + d / 2 - 0.3
        m.box("body", x - 0.25, y0, z, x + 0.25, y1, z + 0.6, "cvein")

    # ---- shatter the ventricles into fragment bones (for the "break" animation; rest pose is unchanged)
    split_body(m)

    # ---- floating glowing cubes ("particles") on their own orbiting bones
    m.bone("orbit", "root", (0, CENTER_Y, 0))
    colors = ["spark_orange", "spark_pink", "spark_blue", "spark_orange", "spark_pink", "spark_orange"]
    sparks = []
    n = 14
    for i in range(n):
        ang = i / n * math.tau + rng.uniform(-0.18, 0.18)
        r = rng.uniform(9.5, 12.5)
        y = rng.uniform(2.0, 22.0)
        x, z = math.cos(ang) * r, math.sin(ang) * r
        tall = rng.random() < 0.3
        s = rng.choice([0.75, 1.0, 1.0, 1.25])
        size = (s * 0.8, s * 2.0, s * 0.8) if tall else (s, s, s)
        name = f"spark{i + 1}"
        m.bone(name, "orbit", (x, y, z))
        m.cube(name, (x - size[0] / 2, y - size[1] / 2, z - size[2] / 2), size, colors[i % len(colors)])
        sparks.append((name, np.array([x, y, z])))
    m.sparks = sparks
    return m


# ============================================================================ texture
def clamp(v):
    return max(0, min(255, int(round(v))))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


GRADIENTS = {  # material -> (colour at top, colour at bottom) by world height y in [1, 15]
    "muscle": ((236, 104, 74), (176, 34, 78)),
    "muscle_band": ((226, 96, 70), (168, 30, 72)),
    "atrium_r": ((240, 140, 140), (222, 96, 112)),
    "atrium_l": ((244, 134, 86), (228, 98, 70)),
    "flesh_inner": ((168, 26, 44), (112, 10, 36)),   # exposed cut faces of the shards
}
FLAT = {
    "vessel_red": (234, 102, 68), "vessel_blue": (112, 126, 194), "artery": (196, 28, 44),
    "cvein": (124, 126, 198), "spark_orange": (252, 172, 92), "spark_pink": (250, 176, 176),
    "spark_blue": (136, 156, 214),
}
GLOW_MATS = {"artery", "cvein", "spark_orange", "spark_pink", "spark_blue"}


def paint_face(px, gx, rect, mat, face, cube, rng):
    x0, y0, w, h = rect
    cy0 = cube["origin"][1]
    cy1 = cy0 + cube["size"][1]

    def world_y(v):
        if face == "up":
            return cy1
        if face == "down":
            return cy0
        return cy1 - (v + 0.5) / h * (cy1 - cy0)

    if mat in GRADIENTS:
        top, bot = GRADIENTS[mat]
        cells = {}
        for v in range(h):
            for u in range(w):
                t = 1 - (world_y(v) - 1) / 14
                c = mix(top, bot, t)
                key = (u // 2, v // 2)          # blocky 2x2 voxel blotches like the reference
                if key not in cells:
                    cells[key] = rng.choice([0.9, 0.95, 1.0, 1.0, 1.04, 1.08])
                k = cells[key] * rng.uniform(0.97, 1.03)
                if mat == "muscle_band" and u % 2 == 0:
                    k *= 0.88
                px[x0 + u, y0 + v] = shade(c, k) + (255,)
                if mat == "flesh_inner":                      # hot glowing core visible in the cracks
                    if rng.random() < 0.18:
                        gx[x0 + u, y0 + v] = mix(c, (255, 120, 90), 0.6) + (int(rng.uniform(110, 200)),)
                elif rng.random() < 0.012 and mat != "muscle_band":   # sparse shimmering glints
                    gx[x0 + u, y0 + v] = mix(c, (255, 200, 190), 0.35) + (150,)
        if mat == "muscle" and face not in ("up", "down") and w >= 6:   # faint striations
            for _ in range(max(1, w // 8)):
                u = rng.randrange(w)
                for v in range(h):
                    if rng.random() < 0.8:
                        c = px[x0 + u, y0 + v][:3]
                        px[x0 + u, y0 + v] = shade(c, 0.9) + (255,)
        return

    if mat.startswith("lumen"):
        base = FLAT["vessel_blue" if mat == "lumen_blue" else "vessel_red"]
        inner_dark = (40, 40, 86) if mat == "lumen_blue" else (70, 8, 20)
        glow = (150, 150, 255) if mat == "lumen_blue" else (255, 90, 80)
        for v in range(h):
            for u in range(w):
                rim = u == 0 or v == 0 or u == w - 1 or v == h - 1
                if rim:
                    px[x0 + u, y0 + v] = shade(base, rng.uniform(0.85, 1.0)) + (255,)
                else:
                    dx = (u + 0.5) / w - 0.5
                    dy = (v + 0.5) / h - 0.5
                    r = min(1.0, math.hypot(dx, dy) * 2.2)
                    px[x0 + u, y0 + v] = mix(inner_dark, shade(base, 0.6), r * 0.6) + (255,)
                    gx[x0 + u, y0 + v] = mix(glow, inner_dark, r) + (int(230 * (1 - r * 0.7)),)
        return

    base = FLAT[mat]
    for v in range(h):
        for u in range(w):
            if mat.startswith("spark"):
                k = 1.08 if (u == 0 or v == 0) else (0.92 if (u == w - 1 or v == h - 1) else 1.0)
                c = shade(base, k)
            elif mat.startswith("vessel"):
                key = (u // 2, v // 2)
                k = (hash((id(cube), face, key)) % 7) / 6.0
                c = shade(base, 0.86 + 0.24 * k)
                if mat == "vessel_blue" and k > 0.75:
                    c = mix(c, (150, 168, 214), 0.5)
            else:
                c = shade(base, rng.uniform(0.9, 1.08))
            px[x0 + u, y0 + v] = c + (255,)
            if mat in GLOW_MATS:
                gx[x0 + u, y0 + v] = c + (255,)


def pack_and_paint(model, rng):
    rects = []
    for b in model.bones:
        for c in b["cubes"]:
            d = c["density"] or DENSITY
            for face, (iu, iv) in FACE_DIMS.items():
                w = max(1, int(math.ceil(c["size"][iu] * d - 1e-6)))
                h = max(1, int(math.ceil(c["size"][iv] * d - 1e-6)))
                rects.append((h, w, c, face))
    rects.sort(key=lambda r: (-r[0], -r[1]))
    x = y = shelf = 0
    uv = {}
    for h, w, c, face in rects:
        if x + w > TEX:
            x, y, shelf = 0, y + shelf, 0
        if y + h > TEX:
            raise SystemExit("texture overflow")
        uv[(id(c), face)] = (x, y, w, h)
        x += w
        shelf = max(shelf, h)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    glow = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    px, gx = img.load(), glow.load()
    for h, w, c, face in rects:
        paint_face(px, gx, uv[(id(c), face)], c["faces"].get(face, c["mat"]), face, c, rng)
    occ = np.zeros((TEX, TEX), dtype=np.int32)
    for (x0, y0, w, h) in uv.values():
        occ[y0:y0 + h, x0:x0 + w] += 1
    assert occ.max() == 1, "UV overlap"
    return img, glow, uv, y + shelf


# ============================================================================ export
def r4(v):
    v = round(float(v), 4)
    return int(v) if v == int(v) else v


def export_geo(model, uv, path):
    bones = []
    for b in model.bones:
        bj = {"name": b["name"]}
        if b["parent"]:
            bj["parent"] = b["parent"]
        bj["pivot"] = [r4(v) for v in b["pivot"]]
        if any(abs(v) > 1e-9 for v in b["rotation"]):
            bj["rotation"] = [r4(v) for v in b["rotation"]]
        cubes = []
        for c in b["cubes"]:
            faces = {}
            for face in FACE_DIMS:
                x0, y0, w, h = uv[(id(c), face)]
                faces[face] = {"uv": [x0, y0], "uv_size": [w, h]}
            cubes.append({"origin": [r4(v) for v in c["origin"]], "size": [r4(v) for v in c["size"]], "uv": faces})
        if cubes:
            bj["cubes"] = cubes
        bones.append(bj)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.{NAME}", "texture_width": TEX, "texture_height": TEX,
                        "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
        "bones": bones}]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(geo, fh, indent="\t")


# ============================================================================ animations
def pl(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return keys[-1][1]


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def beat(phase):
    """Lub-dub heartbeat envelope for phase in [0,1): two quick pulses, then rest."""
    return pl(phase % 1.0, [(0, 0), (0.07, 1.0), (0.16, 0.15), (0.25, 0.65), (0.4, 0), (1.0, 0)])


def make_animations(m):
    rng = random.Random(7)
    sp = {n: (p, rng.uniform(0, math.tau), rng.choice([1, 2])) for n, p in m.sparks}
    TAU = math.tau

    def add(out, bone, rot=(0, 0, 0), pos=(0, 0, 0), scl=None):
        r, p, s = out.get(bone, ([0, 0, 0], [0, 0, 0], [1, 1, 1]))
        r = [r[i] + rot[i] for i in range(3)]
        p = [p[i] + pos[i] for i in range(3)]
        if scl is not None:
            s = [s[i] * scl[i] for i in range(3)]
        out[bone] = (r, p, s)

    def heartbeat(out, phase, amp=1.0):
        b = beat(phase) * amp
        add(out, "heart", scl=(1 + 0.09 * b, 1 + 0.07 * b, 1 + 0.09 * b))
        a = beat(phase - 0.08) * amp            # atria contract just after the ventricles
        add(out, "atrium_right", scl=(1 + 0.06 * a, 1 + 0.06 * a, 1 + 0.06 * a))
        add(out, "atrium_left", scl=(1 + 0.06 * a, 1 + 0.06 * a, 1 + 0.06 * a))
        add(out, "vessels", (2.5 * b, 0, -2.0 * b))

    def sparks_float(out, t, T, amp=1.0):
        for n, (p, ph, f) in sp.items():
            w = TAU * t / T * f + ph
            k = 0.75 + 0.35 * (0.5 + 0.5 * math.sin(w * 2))      # twinkle
            add(out, n, (0, 360 * t / T * (1 if f == 1 else -1), 0), (0, 1.6 * amp * math.sin(w), 0), (k, k, k))

    # idle: slow spin around its own axis, gentle bob, heartbeat once per second, cubes orbit & twinkle
    def idle(t):
        T = 4.0
        out = {}
        add(out, "root", (0, 360 * t / T, 0), (0, 1.2 * math.sin(TAU * t / T * 2), 0))
        add(out, "orbit", (0, -180 * t / T, 0))   # orbit drifts slower than the heart spins
        heartbeat(out, t / 1.0)
        sparks_float(out, t, T)
        return out

    # spawn: pops into existence with an overshoot, cubes burst outward from the centre
    def spawn(t):
        L = 0.8
        out = {}
        s = pl(t, [(0, 0.0), (0.35, 1.2), (0.55, 0.92), (0.7, 1.04), (0.8, 1.0)])
        add(out, "heart", scl=(s, s, s))
        add(out, "root", (0, 200 * smooth(t / L), 0))
        e = 1 - smooth(t / 0.6)
        for n, (p, ph, f) in sp.items():
            d = np.array([p[0], p[1] - CENTER_Y, p[2]]) * -e
            k = smooth(t / 0.5)
            add(out, n, pos=(-d[0], d[1], d[2]), scl=(k, k, k))
        return out

    # consume: the player absorbs it - rises, beats hard, spins fast, cubes spiral in, shrinks to nothing
    def consume(t):
        L = 1.2
        out = {}
        add(out, "root", (0, 900 * smooth(t / L), 0), (0, 6 * smooth(t / 0.9), 0))
        heartbeat(out, t / 0.3, amp=1.6)
        s = pl(t, [(0, 1.0), (0.3, 1.25), (0.75, 1.0), (1.2, 0.0)])
        add(out, "heart", scl=(s, s, s))
        add(out, "orbit", (0, 720 * smooth(t / L), 0))
        e = smooth((t - 0.15) / 0.85)
        for n, (p, ph, f) in sp.items():
            d = np.array([p[0], p[1] - CENTER_Y, p[2]]) * -e
            k = 1 - smooth((t - 0.6) / 0.6)
            add(out, n, pos=(-d[0], d[1], d[2]), scl=(k, k, k))
        return out

    # break: one-shot, played AFTER the player has broken the heart (on the break event, not while mining).
    # Impact squash + shudder -> cracks open (glowing core shows) -> shards, atria and vessels burst out,
    # tumble and fall under gravity while shrinking away; the sparks flash and scatter.
    brng = random.Random(13)
    HC = np.array([0.0, 8.0, 0.0])                        # heart centre (model space)
    fly = {}
    for n, c in m.shards + [("atrium_right", np.array(m.by["atrium_right"]["pivot"])),
                            ("atrium_left", np.array(m.by["atrium_left"]["pivot"])),
                            ("vessels", np.array([0.0, 20.0, 0.0]))]:
        d = c - HC
        d[1] *= 0.5
        d = d / (np.linalg.norm(d) + 1e-9)
        spin = [brng.uniform(-1, 1) * brng.uniform(240, 420) for _ in range(3)]
        fly[n] = (d, brng.uniform(9.0, 13.0), brng.uniform(5.0, 9.0), spin, brng.uniform(0.0, 0.05))
    G = 34.0                                              # px / s^2

    def brk(t):
        L = 1.0
        out = {}
        # impact: squash then snap back, root shudders
        q = pl(t, [(0, 0), (0.05, 1.0), (0.12, -0.5), (0.18, 0.0)])
        add(out, "heart", scl=(1 + 0.14 * q, 1 - 0.16 * q, 1 + 0.14 * q))
        j = max(0.0, 1 - t / 0.22)
        add(out, "root", (6 * j * math.sin(t * 95), 0, 5 * j * math.sin(t * 77 + 1)),
            (0.35 * j * math.sin(t * 120), 0, 0))
        for n, (d, speed, vy, spin, delay) in fly.items():
            crack = smooth(t / 0.16) * 0.6                # pieces part slightly: cracks open
            tt = max(0.0, t - 0.16 - delay)               # then the burst
            r = crack + speed * (1 - math.exp(-2.5 * tt)) / 2.5 * 2.0   # fast burst slowed by drag
            y = vy * tt - 0.5 * G * tt * tt
            w = d * r + np.array([0, y, 0])
            k = 1 - smooth((t - 0.55) / 0.42)
            rr = [a * smooth(tt / 0.8) * 0.9 for a in spin]
            add(out, n, rot=rr, pos=(-w[0], w[1], w[2]), scl=(k, k, k))
        for n, (p, ph, f) in sp.items():                  # sparks flash, then scatter outward and vanish
            d = np.array([p[0], p[1] - CENTER_Y, p[2]])
            e = smooth((t - 0.1) / 0.5)
            w = d * 0.9 * e + np.array([0, -6 * e * e, 0])
            k = pl(t, [(0, 1.0), (0.12, 1.8), (0.3, 1.2), (0.65, 0.0), (L, 0.0)])
            add(out, n, (0, 540 * e * (1 if f == 1 else -1), 0), (-w[0], w[1], w[2]), (k, k, k))
        return out

    return {
        "idle": dict(fn=idle, length=4.0, dt=0.05, loop=True),
        "spawn": dict(fn=spawn, length=0.8, dt=0.05, loop=False),
        "consume": dict(fn=consume, length=1.2, dt=0.05, loop="hold_on_last_frame"),
        "break": dict(fn=brk, length=1.0, dt=0.04, loop="hold_on_last_frame"),
    }


def export_animations(m, path):
    anims = make_animations(m)
    out = {"format_version": "1.8.0", "animations": {}}
    for name, a in anims.items():
        n = int(round(a["length"] / a["dt"]))
        times = [round(i * a["dt"], 4) for i in range(n + 1)]
        frames = [a["fn"](t) for t in times]
        bones = {}
        for b in m.bones:
            bn = b["name"]
            chans = {}
            for ci, (cname, ident) in enumerate((("rotation", 0.0), ("position", 0.0), ("scale", 1.0))):
                vals = [[round(float(x), 3) for x in f.get(bn, ([0] * 3, [0] * 3, [1] * 3))[ci]] for f in frames]
                if all(abs(v - ident) < 1e-3 for vv in vals for v in vv):
                    continue
                keys = {}
                for i, (t, v) in enumerate(zip(times, vals)):
                    if 0 < i < len(times) - 1:
                        pv, nv = vals[i - 1], vals[i + 1]
                        if all(abs((pv[k] + nv[k]) / 2 - v[k]) < 1e-3 for k in range(3)):
                            continue
                    keys[f"{t:g}"] = v
                chans[cname] = keys
            if chans:
                bones[bn] = chans
        out["animations"][f"animation.{NAME}.{name}"] = {"loop": a["loop"], "animation_length": a["length"],
                                                         "bones": bones}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent="\t")
    return anims


# ============================================================================ preview renderer (glowmask unshaded)
def render(model, tex, glow, uv, mats, eye, scale=24, title=None, bounds=None):
    eye = np.array(eye, dtype=float)
    fwd = -eye / np.linalg.norm(eye)
    right = np.cross(fwd, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    V = np.array([right, up, fwd])
    light = np.array([-0.4, 0.8, -0.45])
    light /= np.linalg.norm(light)
    faces = []
    for b in model.bones:
        M = mats[b["name"]]
        for c in b["cubes"]:
            co = cube_corners(c)
            for face, sel in FACE_CORNERS.items():
                tl, tr, bl = (np.array(p, dtype=float) for p in sel(*co))
                w = [(M @ np.append(p, 1))[:3] for p in (tl, tr, bl, tr + bl - tl)]
                n = np.cross(w[1] - w[0], w[2] - w[0])
                nn = np.linalg.norm(n)
                if nn < 1e-9:
                    continue
                n = -n / nn
                if (V @ n)[2] >= 0:
                    continue
                cam = [V @ p for p in w]
                faces.append((sum(p[2] for p in cam) / 4, cam, c, face, 0.55 + 0.45 * max(0.0, float(n @ light))))
    if bounds is None:
        pts = np.array([p for f in faces for p in f[1]])
        bounds = (pts.min(axis=0), pts.max(axis=0))
    mn, mx = bounds
    pad, top = 16, (22 if title else 0)
    W = int((mx[0] - mn[0]) * scale) + 2 * pad
    H = int((mx[1] - mn[1]) * scale) + 2 * pad + top
    img = Image.new("RGB", (W, H), (24, 24, 26))
    dr = ImageDraw.Draw(img)
    if title:
        dr.text((8, 5), title, fill=(200, 200, 200))
    rgb = tex.convert("RGB")

    def to2d(p):
        return np.array(((p[0] - mn[0]) * scale + pad, (mx[1] - p[1]) * scale + pad + top))

    faces.sort(key=lambda f: -f[0])
    for depth, cam, c, face, bright in faces:
        p0, p1, p2, p3 = (to2d(p) for p in cam)
        u0, v0, w, h = uv[(id(c), face)]
        xs, ys = [p0[0], p1[0], p2[0], p3[0]], [p0[1], p1[1], p2[1], p3[1]]
        bx0, by0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        bx1, by1 = int(math.ceil(max(xs))) + 1, int(math.ceil(max(ys))) + 1
        e1, e2 = p1 - p0, p2 - p0
        det = e1[0] * e2[1] - e2[0] * e1[1]
        if abs(det) < 1e-6:
            continue
        off = np.array((bx0, by0))
        mask = Image.new("L", (bx1 - bx0, by1 - by0), 0)
        ImageDraw.Draw(mask).polygon([tuple(p - off) for p in (p0, p1, p3, p2)], fill=255)
        P0 = p0 - off
        a, b_ = w * e2[1] / det, -w * e2[0] / det
        d, e = -h * e1[1] / det, h * e1[0] / det
        coef = (a, b_, -(a * P0[0] + b_ * P0[1]), d, e, -(d * P0[0] + e * P0[1]))
        patch = rgb.crop((u0, v0, u0 + w, v0 + h)).transform(mask.size, Image.AFFINE, coef, resample=Image.NEAREST)
        img.paste(patch.point(lambda v: clamp(v * bright)), (bx0, by0), mask)
        g = glow.crop((u0, v0, u0 + w, v0 + h)).transform(mask.size, Image.AFFINE, coef, resample=Image.NEAREST)
        ga = Image.fromarray(np.minimum(np.array(g.split()[3]), np.array(mask)).astype(np.uint8))
        img.paste(g.convert("RGB"), (bx0, by0), ga)
    return img


# ============================================================================ main
def main():
    m = build(random.Random(2024))
    tex, glow, uv, used = pack_and_paint(m, random.Random(77))
    mats = bone_matrices(m)
    mn, mx = posed_bbox(m, mats)
    print(f"bbox {np.round(mn, 1)} .. {np.round(mx, 1)}  -> {(mx - mn) / 16} blocks")
    print(f"bones {len(m.bones)}, cubes {sum(len(b['cubes']) for b in m.bones)}, texture rows {used}/{TEX}")
    for sub in ("geo", "animations", os.path.join("textures", "entity")):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    export_geo(m, uv, os.path.join(OUT, "geo", f"{NAME}.geo.json"))
    tex.save(os.path.join(OUT, "textures", "entity", f"{NAME}.png"))
    glow.save(os.path.join(OUT, "textures", "entity", f"{NAME}_glowmask.png"))
    anims = export_animations(m, os.path.join(OUT, "animations", f"{NAME}.animation.json"))

    views = [("front", (0, 0.25, -1)), ("34", (-0.8, 0.45, -1)), ("back", (0.7, 0.3, 1)), ("side", (1, 0.1, 0))]
    for vname, eye in views:
        render(m, tex, glow, uv, mats, eye, title=vname).save(os.path.join(PREVIEW, f"heart_{vname}.png"))
    tex.resize((TEX * 3, TEX * 3), Image.NEAREST).save(os.path.join(PREVIEW, "heart_texture_x3.png"))
    if "--anim" in sys.argv:
        for name, a in anims.items():
            n = 8
            times = [a["length"] * i / (n if a["loop"] is True else n - 1) for i in range(n)]
            frames = [render(m, tex, glow, uv, bone_matrices(m, a["fn"](t)), (-0.8, 0.45, -1), scale=10,
                             title=f"{name} t={t:.2f}", bounds=(np.array([-20, -4, 0]), np.array([20, 32, 0])))
                      for t in times]
            W, H = frames[0].size
            sheet = Image.new("RGB", (W * 4, H * 2))
            for i, f in enumerate(frames):
                sheet.paste(f, ((i % 4) * W, (i // 4) * H))
            sheet.save(os.path.join(PREVIEW, f"anim_{name}.png"))


if __name__ == "__main__":
    main()
