"""GlowCue studio renderer: regenerates the original product and texture imagery in frontend/public/products.

Everything here is procedurally generated, so GlowCue owns every pixel. No faces, no real brands.
Usage: python studio.py <out_dir> [names...]
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
ONLY = set(sys.argv[2:])
os.makedirs(OUT, exist_ok=True)
SERIF = "C:/Windows/Fonts/georgia.ttf"
SANS = "C:/Windows/Fonts/bahnschrift.ttf"
SS = 2  # supersampling


def hexc(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def box(a, k, axis):
    pad = [(0, 0)] * a.ndim
    pad[axis] = (k + 1, k)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * k + 1, 2 * k + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * k + 1)).astype(np.float32)


def blur(a, r):
    k = int(max(1, r * 0.75))
    out = a.astype(np.float32)
    for _ in range(3):
        out = box(box(out, k, 0), k, 1)
    return out


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.W, self.H = w * SS, h * SS
        self.img = np.zeros((self.H, self.W, 3), np.float32)

    def mask(self, fn):
        m = Image.new("L", (self.W, self.H), 0)
        fn(ImageDraw.Draw(m))
        return np.asarray(m, np.float32) / 255

    def save(self, name, grain=0.012, q=84):
        self.img = np.nan_to_num(self.img, nan=0.9)
        im = Image.fromarray((np.clip(self.img, 0, 1) * 255).astype(np.uint8)).resize((self.w, self.h), Image.LANCZOS)
        a = np.asarray(im, np.float32) / 255
        rng = np.random.default_rng(len(name))
        a = a + rng.normal(0, grain, a.shape[:2])[..., None]  # luminance grain unifies the "photo"
        # gentle warm grade + soft vignette
        y, x = np.mgrid[0 : self.h, 0 : self.w]
        v = 1 - 0.10 * (((x / self.w - 0.5) ** 2 + (y / self.h - 0.5) ** 2) * 2.2)
        a = a * v[..., None]
        a = a * np.array([1.02, 1.0, 0.97], np.float32)
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(
            os.path.join(OUT, name), quality=q, optimize=True, progressive=True
        )
        print("saved", name)


# ----------------------------------------------------------------------------- scene
def backdrop(c, wall_top, wall_bot, floor_far, floor_near, horizon=0.72, light=(0.22, 0.18), glow=0.16):
    H, W = c.H, c.W
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    wt = np.clip(y / horizon, 0, 1)
    wall = hexc(wall_top) * (1 - wt) + hexc(wall_bot) * wt
    ft = np.clip((y - horizon) / (1 - horizon), 0, 1)
    floor = hexc(floor_far) * (1 - ft) + hexc(floor_near) * ft
    blend = smooth(horizon - 0.004, horizon + 0.004, y)
    img = wall * (1 - blend) + floor * blend
    d = np.sqrt((x - light[0]) ** 2 + (y - light[1]) ** 2)
    img = img * (1 + glow * np.exp(-((d / 0.5) ** 2)))
    c.img = np.broadcast_to(img, (H, W, 3)).astype(np.float32).copy()


def leaf_shadows(c, seed, strength=0.22, region=(0.0, -0.1, 0.7, 0.55), blur_r=10, count=4, scale=1.0):
    rng = np.random.default_rng(seed)

    def fn(d):
        for _ in range(count):
            x0, y0 = rng.uniform(region[0], region[2]) * c.W, rng.uniform(region[1], region[3]) * c.H
            ang = rng.uniform(0.2, 1.3)
            length = rng.uniform(0.35, 0.6) * c.W * scale
            d.line([(x0, y0), (x0 + math.cos(ang) * length, y0 + math.sin(ang) * length)], fill=255, width=int(3 * SS))
            for i, t in enumerate(np.linspace(0.08, 1, 10)):
                px, py = x0 + math.cos(ang) * length * t, y0 + math.sin(ang) * length * t
                la = ang + (1 if i % 2 else -1) * rng.uniform(0.7, 1.1)
                ll = rng.uniform(0.07, 0.12) * c.W * scale
                lw = ll * 0.42
                pts = []
                for k in range(28):
                    th = 2 * math.pi * k / 28
                    ex = (1 - math.cos(th)) / 2 * ll
                    ey = math.sin(th) * lw / 2 * (math.sin(math.pi * (1 - math.cos(th)) / 2) ** 0.6)
                    pts.append((px + ex * math.cos(la) - ey * math.sin(la), py + ex * math.sin(la) + ey * math.cos(la)))
                d.polygon(pts, fill=255)

    m = blur(c.mask(fn), blur_r * SS)
    tint = np.array([0.62, 0.55, 0.62], np.float32)  # shadows go slightly cool against warm light
    c.img = c.img * (1 - strength * m[..., None] * (1 - tint * 0.5))


def ground_shadow(c, cx, base_y, width, height, strength=0.5, caustic=None, side=1):
    s = SS
    cx, base_y, width, height = cx * s, base_y * s, width * s, height * s
    m = c.mask(
        lambda d: d.ellipse(
            [cx - width * 0.56, base_y - width * 0.06, cx + width * 0.56, base_y + width * 0.05], fill=255
        )
    )
    c.img *= (1 - strength * blur(m, width * 0.05))[..., None]
    length = height * 0.85
    pts = [
        (cx - width * 0.48, base_y),
        (cx + width * 0.48, base_y),
        (cx + side * length * 0.95 + width * 0.3, base_y - length * 0.22),
        (cx + side * length * 0.95 - width * 0.3, base_y - length * 0.26),
    ]
    m2 = blur(c.mask(lambda d: d.polygon(pts, fill=255)), width * 0.22)
    c.img *= (1 - 0.26 * m2)[..., None]
    if caustic is not None:
        m3 = blur(
            c.mask(
                lambda d: d.ellipse(
                    [
                        min(cx + side * width * 0.3, cx + side * (width * 0.3 + length * 0.55)),
                        base_y - width * 0.12,
                        max(cx + side * width * 0.3, cx + side * (width * 0.3 + length * 0.55)),
                        base_y + width * 0.02,
                    ],
                    fill=255,
                )
            ),
            width * 0.18,
        )
        tint = hexc(caustic)
        c.img = c.img * (1 - 0.45 * m3[..., None]) + (c.img * tint * 1.7) * 0.45 * m3[..., None]


def spec(u, center, width):
    return np.exp(-(((u - center) / width) ** 2))


def part(c, shape, color, mat, light=(-0.62, 0.78), label=None, liquid=None, fill=0.0, top_cap=False, rim=0.0):
    """Render one cylindrical part. shape: ('rrect', box, r) | ('poly', pts) | ('ellipse', box), in 1x px."""
    s = SS

    def fn(d):
        if shape[0] == "rrect":
            b = [v * s for v in shape[1]]
            d.rounded_rectangle(b, radius=shape[2] * s, fill=255)
        elif shape[0] == "poly":
            d.polygon([(x * s, y * s) for x, y in shape[1]], fill=255)
        else:
            d.ellipse([v * s for v in shape[1]], fill=255)

    m = c.mask(fn)
    on = m > 0.5
    rows = np.where(on.any(axis=1))[0]
    if rows.size == 0:
        return
    left = np.argmax(on, axis=1).astype(np.float32)
    right = (c.W - 1 - np.argmax(on[:, ::-1], axis=1)).astype(np.float32)
    center = (left + right) / 2
    half = np.maximum((right - left) / 2, 1)
    cols = np.arange(c.W, dtype=np.float32)[None, :]
    u = np.clip((cols - center[:, None]) / half[:, None], -1, 1)
    nz = np.sqrt(np.clip(1 - u * u, 0, 1))
    diff = np.clip(u * light[0] + nz * light[1], 0, 1)

    alb = np.broadcast_to(hexc(color), c.img.shape).copy()
    y0, y1 = rows[0], rows[-1]
    ty = np.clip((np.arange(c.H, dtype=np.float32) - y0) / max(1, y1 - y0), 0, 1)[:, None]
    if mat == "glass":
        shift = (u * 10 * s).astype(np.int32)  # cheap refraction of what's behind
        xs = np.clip(cols.astype(np.int32) + shift, 0, c.W - 1)
        behind = c.img[np.arange(c.H)[:, None], xs]
        glass_tint = hexc(color)
        alb = behind * (0.55 + 0.45 * glass_tint)
        if liquid is not None:
            level = 1 - fill
            liq = (ty > level)[..., None]
            liquid_col = hexc(liquid) * (0.8 + 0.25 * behind.mean(axis=2, keepdims=True))
            alb = np.where(liq, liquid_col, alb)
    if label is not None:
        lab = label(c)  # RGBA float array at canvas res
        a = lab[..., 3:4]
        alb = alb * (1 - a) + lab[..., :3] * a
    if mat == "glass":
        col = alb * (0.62 + 0.45 * diff[..., None])
        col = col * (1 - 0.38 * (np.abs(u) ** 5))[..., None]
        hl = spec(u, -0.55, 0.06) * 0.95 + spec(u, -0.36, 0.2) * 0.14 + spec(u, 0.78, 0.035) * 0.45
    elif mat == "gloss":
        col = alb * (0.40 + 0.70 * diff[..., None])
        hl = spec(u, -0.5, 0.07) * 0.62 + spec(u, -0.32, 0.25) * 0.10 + spec(u, 0.86, 0.05) * 0.12
    elif mat == "frosted":
        col = alb * (0.48 + 0.58 * diff[..., None])
        hl = spec(u, -0.45, 0.3) * 0.16
    elif mat == "flat":
        col = alb * (1.02 - 0.10 * ty[..., None])
        hl = np.zeros_like(u)
    else:  # matte
        col = alb * (0.30 + 0.78 * diff[..., None])
        hl = spec(u, -0.45, 0.28) * 0.07
    if rim:
        hl = hl + spec(u, 0.9, 0.05) * rim
    col = col * (1 - 0.10 * ty[..., None]) + hl[..., None] * np.array([1.0, 0.97, 0.92], np.float32)
    if top_cap:
        col = col + (1 - smooth(0.0, 0.08, ty))[..., None] * 0.10
    c.img = c.img * (1 - m[..., None]) + col * m[..., None]


def label_fn(box_xyxy, bg, lines, ink="#382C29"):
    """Flat label drawn at canvas resolution; shading is applied by part()."""

    def make(c):
        x0, y0, x1, y1 = [v * SS for v in box_xyxy]
        im = Image.new("RGBA", (c.W, c.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if bg:
            d.rectangle([x0, y0, x1, y1], fill=tuple(int(v * 255) for v in hexc(bg)) + (255,))
        cy = y0 + (y1 - y0) * 0.18
        for text, font, size, spacing in lines:
            t = " ".join(text) if spacing else text
            px = int(size * SS)
            f = ImageFont.truetype(font, px)
            while d.textlength(t, font=f) > (x1 - x0) * 0.86 and px > 6:
                px -= 1
                f = ImageFont.truetype(font, px)
            w = d.textlength(t, font=f)
            d.text(((x0 + x1) / 2 - w / 2, cy), t, font=f, fill=tuple(int(v * 255) for v in hexc(ink)) + (255,))
            cy += size * SS * 1.45
        return np.asarray(im, np.float32) / 255

    return make


# ----------------------------------------------------------------------------- products (1x coordinates)
def dropper(
    c, cx, by, h, glass, liquid, bulb="#2B201D", collar="#C9A27E", name="SERUM", fill=0.82, light=(-0.62, 0.78), rim=0.0
):
    wb, hb = h * 0.40, h * 0.64
    ground_shadow(c, cx, by, wb, h, caustic=liquid, side=1 if light[0] < 0 else -1)
    body = (cx - wb / 2, by - hb, cx + wb / 2, by)
    lab = label_fn(
        (cx - wb * 0.34, by - hb * 0.62, cx + wb * 0.34, by - hb * 0.24),
        "#FFFCF8",
        [("GlowCue", SERIF, h * 0.055, False), (name, SANS, h * 0.026, True), ("30 ML", SANS, h * 0.02, True)],
    )
    part(c, ("rrect", body, wb * 0.2), glass, "glass", liquid=liquid, fill=fill, label=lab, light=light, rim=rim)
    part(
        c,
        ("rrect", (cx - h * 0.115, by - hb - h * 0.075, cx + h * 0.115, by - hb + 2), 4),
        collar,
        "gloss",
        light=light,
        rim=rim,
    )
    part(
        c,
        ("rrect", (cx - h * 0.085, by - hb - h * 0.30, cx + h * 0.085, by - hb - h * 0.07), h * 0.08),
        bulb,
        "matte",
        light=light,
        top_cap=True,
        rim=rim,
    )


def pump(c, cx, by, h, color, cap="#2B201D", name="CLEANSER", ink="#382C29", light=(-0.62, 0.78), rim=0.0):
    wb, hb = h * 0.42, h * 0.70
    ground_shadow(c, cx, by, wb, h, side=1 if light[0] < 0 else -1)
    lab = label_fn(
        (cx - wb * 0.36, by - hb * 0.58, cx + wb * 0.36, by - hb * 0.2),
        None,
        [("GlowCue", SERIF, h * 0.06, False), (name, SANS, h * 0.026, True), ("150 ML", SANS, h * 0.02, True)],
        ink=ink,
    )
    part(
        c,
        ("rrect", (cx - wb / 2, by - hb, cx + wb / 2, by), wb * 0.16),
        color,
        "gloss",
        label=lab,
        light=light,
        rim=rim,
    )
    part(
        c,
        ("rrect", (cx - h * 0.1, by - hb - h * 0.06, cx + h * 0.1, by - hb + 2), 3),
        cap,
        "gloss",
        light=light,
        rim=rim,
    )
    part(
        c,
        ("rrect", (cx - h * 0.025, by - hb - h * 0.16, cx + h * 0.025, by - hb - h * 0.05), 2),
        cap,
        "matte",
        light=light,
    )
    part(
        c,
        ("rrect", (cx - h * 0.07, by - hb - h * 0.22, cx + h * 0.16, by - hb - h * 0.155), h * 0.02),
        cap,
        "gloss",
        light=light,
        rim=rim,
    )


def tube(c, cx, by, h, color, cap="#C96F50", name="SPF 50", ink="#382C29", light=(-0.62, 0.78), rim=0.0, slim=1.0):
    wc, hc = h * 0.27 * slim, h * 0.13
    ground_shadow(c, cx, by, wc * 1.3, h, side=1 if light[0] < 0 else -1)
    top_w = h * 0.42 * slim
    body = [
        (cx - wc / 2, by - hc),
        (cx + wc / 2, by - hc),
        (cx + top_w / 2, by - h * 0.97),
        (cx - top_w / 2, by - h * 0.97),
    ]
    lab = label_fn(
        (cx - top_w * 0.32, by - h * 0.78, cx + top_w * 0.32, by - h * 0.45),
        None,
        [
            ("GlowCue", SERIF, h * 0.055 * slim, False),
            (name, SANS, h * 0.026 * slim, True),
            ("50 ML" if slim >= 1 else "15 ML", SANS, h * 0.02 * slim, True),
        ],
        ink=ink,
    )
    part(c, ("poly", body), color, "gloss", label=lab, light=light, rim=rim)
    part(c, ("rrect", (cx - top_w / 2 - 1, by - h, cx + top_w / 2 + 1, by - h * 0.955), 2), color, "gloss", light=light)
    part(c, ("rrect", (cx - wc / 2, by - hc, cx + wc / 2, by), 4), cap, "gloss", light=light, rim=rim)


def jar(c, cx, by, w, color, lid="#382C29", name="CREAM", ink="#382C29", light=(-0.62, 0.78), rim=0.0):
    hb, hl = w * 0.5, w * 0.22
    ground_shadow(c, cx, by, w, w * 0.8, side=1 if light[0] < 0 else -1)
    lab = label_fn(
        (cx - w * 0.3, by - hb * 0.78, cx + w * 0.3, by - hb * 0.2),
        None,
        [("GlowCue", SERIF, w * 0.085, False), (name, SANS, w * 0.04, True)],
        ink=ink,
    )
    part(
        c, ("rrect", (cx - w / 2, by - hb, cx + w / 2, by), w * 0.08), color, "frosted", label=lab, light=light, rim=rim
    )
    part(
        c,
        ("rrect", (cx - w * 0.52, by - hb - hl, cx + w * 0.52, by - hb + 2), w * 0.05),
        lid,
        "gloss",
        light=light,
        rim=rim,
    )
    part(
        c,
        ("ellipse", (cx - w * 0.52, by - hb - hl - w * 0.07, cx + w * 0.52, by - hb - hl + w * 0.07)),
        lid,
        "matte",
        light=(light[0], 1.0),
    )


def bottle(c, cx, by, h, color, cap="#2B201D", name="TONER", liquid=None, ink="#382C29", light=(-0.62, 0.78), rim=0.0):
    wb, hb = h * 0.36, h * 0.74
    ground_shadow(c, cx, by, wb, h, caustic=liquid, side=1 if light[0] < 0 else -1)
    lab = label_fn(
        (cx - wb * 0.34, by - hb * 0.6, cx + wb * 0.34, by - hb * 0.24),
        "#FFFCF8",
        [("GlowCue", SERIF, h * 0.05, False), (name, SANS, h * 0.024, True), ("200 ML", SANS, h * 0.018, True)],
    )
    part(
        c,
        ("rrect", (cx - wb / 2, by - hb, cx + wb / 2, by), wb * 0.32),
        color,
        "glass" if liquid else "gloss",
        liquid=liquid,
        fill=0.86,
        label=lab,
        light=light,
        rim=rim,
    )
    part(
        c,
        ("rrect", (cx - h * 0.075, by - hb - h * 0.2, cx + h * 0.075, by - hb + 4), h * 0.02),
        cap,
        "matte",
        light=light,
        top_cap=True,
        rim=rim,
    )


# ----------------------------------------------------------------------------- textures (height fields)
def gel(c, stroke, color, thick, opacity=0.85, power=180, bubbles=0, seed=1, opaque=False):
    m = c.mask(stroke)
    hgt = blur(m, thick * SS)
    hgt = hgt / max(hgt.max(), 1e-6)
    hgt = (hgt**0.55) * blur(m, 1.5 * SS)
    gy, gx = np.gradient(hgt * thick * SS * 0.9)
    n = np.dstack([-gx, -gy, np.ones_like(gx)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    light = np.array([-0.45, -0.55, 0.7], np.float32)
    light /= np.linalg.norm(light)
    half = light + np.array([0, 0, 1], np.float32)
    half /= np.linalg.norm(half)
    diff = np.clip(n @ light, 0, 1)
    sp = np.clip(n @ half, 0, 1) ** power
    alpha = blur(m, 1.2 * SS)
    # soft drop shadow, offset away from the light
    sb = blur(alpha, thick * SS * 0.8)
    dy, dx = int(thick * SS * 0.35), int(thick * SS * 0.3)
    sh = np.zeros_like(sb)
    sh[dy:, dx:] = sb[: sb.shape[0] - dy, : sb.shape[1] - dx]  # shift without wrap-around
    c.img *= (1 - 0.22 * sh)[..., None]
    tint = hexc(color)
    if opaque:
        body = tint * (0.55 + 0.55 * diff[..., None])
    else:
        depth = smooth(0.0, 1.0, hgt)[..., None]
        body = c.img * (1 - opacity * depth) + tint * opacity * depth * (0.7 + 0.5 * diff[..., None])
        body = body * (1 - 0.25 * (1 - n[..., 2:3]) ** 2)
    fres = (1 - n[..., 2]) ** 3 * 0.35
    col = body + (sp * 0.9 + fres)[..., None]
    if bubbles:
        rng = np.random.default_rng(seed)
        ys, xs = np.where(hgt > 0.5)
        for _ in range(bubbles):
            i = rng.integers(len(ys))
            r = rng.uniform(3, 11) * SS
            yy, xx = np.mgrid[0 : c.H, 0 : c.W]
            dd = np.sqrt((yy - ys[i]) ** 2 + (xx - xs[i]) ** 2)
            ring = np.exp(-(((dd - r) / (1.2 * SS)) ** 2)) * 0.5
            dot = (
                np.exp(-((np.sqrt((yy - ys[i] + r * 0.4) ** 2 + (xx - xs[i] + r * 0.4) ** 2) / (r * 0.25)) ** 2)) * 0.9
            )
            col = col + (ring + dot)[..., None] * (dd < r * 1.4)[..., None]
    c.img = c.img * (1 - alpha[..., None]) + col * alpha[..., None]


def stroke_path(points, width):
    """Stamp discs densely along the path: a crack-free mask (thick PIL lines leave seams)."""

    def fn(d):
        r = width * SS / 2
        pts = [(x * SS, y * SS) for x, y in points]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] or pts, strict=False):
            steps = max(1, int(math.hypot(x1 - x0, y1 - y0) / (r * 0.15)))
            for k in range(steps + 1):
                x, y = x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps
                d.ellipse([x - r, y - r, x + r, y + r], fill=255)

    return fn


def bezier(p0, p1, p2, p3, n=80):
    t = np.linspace(0, 1, n)[:, None]
    pts = (
        (1 - t) ** 3 * np.array(p0)
        + 3 * (1 - t) ** 2 * t * np.array(p1)
        + 3 * (1 - t) * t**2 * np.array(p2)
        + t**3 * np.array(p3)
    )
    return [tuple(p) for p in pts]


# ----------------------------------------------------------------------------- the image set
def want(name):
    return not ONLY or name.split(".")[0] in ONLY


if want("hero_still"):
    c = Canvas(1600, 1150)
    backdrop(c, "#F2DFD0", "#ECD3C0", "#E3CDB9", "#D5BCA6", horizon=0.66, light=(0.2, 0.15), glow=0.22)
    leaf_shadows(c, 3, strength=0.30, region=(-0.15, -0.2, 0.55, 0.3), blur_r=9, count=4, scale=1.1)
    # travertine plinth
    part(c, ("rrect", (520, 690, 1380, 900), 6), "#E2CBB6", "flat")
    part(c, ("rrect", (520, 676, 1380, 700), 4), "#F1E3D5", "flat")
    ground_shadow(c, 950, 900, 860, 300, strength=0.45)
    dropper(c, 820, 690, 470, "#E7A07E", "#C2603B", name="VITAMIN C 10%")
    pump(c, 1130, 690, 380, "#F7F0E8", name="GEL CLEANSER")
    jar(c, 1300, 690, 170, "#F1E4D6", lid="#A9553A", name="BARRIER")
    gel(c, stroke_path(bezier((330, 1000), (430, 930), (540, 1060), (700, 990)), 70), "#D9785A", 26, bubbles=5, seed=4)
    c.save("hero_still.jpg")

if want("night_still"):
    c = Canvas(1400, 1000)
    backdrop(c, "#2A201D", "#33271F", "#2B211C", "#1F1714", horizon=0.7, light=(0.82, 0.3), glow=0.55)
    L = (0.6, 0.8)
    dropper(
        c, 560, 720, 520, "#8E9A80", "#5E6852", bulb="#EBD5C5", collar="#C9A27E", name="RETINOL 0.3%", light=L, rim=0.55
    )
    jar(c, 860, 720, 230, "#EBD5C5", lid="#C96F50", name="CERAMIDE", light=L, rim=0.5)
    tube(c, 330, 720, 330, "#F2E4D6", cap="#382C29", name="EYE GEL", light=L, rim=0.5, slim=0.8)
    c.save("night_still.jpg", grain=0.016)

if want("gel_coral"):
    c = Canvas(1000, 1000)
    backdrop(c, "#F4E6DA", "#F0DED0", "#EEDBCB", "#E8D2C0", horizon=1.0, light=(0.3, 0.25), glow=0.12)
    gel(c, stroke_path(bezier((120, 760), (280, 380), (620, 820), (880, 260)), 150), "#D9724F", 60, bubbles=9, seed=2)
    gel(c, stroke_path([(760, 760), (770, 770)], 70), "#D9724F", 28, seed=3)
    c.save("gel_coral.jpg")

if want("cream_swirl"):
    c = Canvas(1000, 1000)
    backdrop(c, "#EBD5C5", "#E6CDBB", "#E6CDBB", "#E6CDBB", horizon=1.0, light=(0.25, 0.2), glow=0.15)
    pts = []
    for t in np.linspace(0, 4.2 * math.pi, 220):
        r = 60 + 34 * t
        pts.append((500 + r * math.cos(t), 520 + r * math.sin(t) * 0.82))
    gel(c, stroke_path(pts, 120), "#FFF8F0", 52, power=28, opaque=True)
    c.save("cream_swirl.jpg")

if want("drops"):
    c = Canvas(900, 900)
    backdrop(c, "#E4EBDF", "#DCE4D6", "#DCE4D6", "#DCE4D6", horizon=1.0, light=(0.3, 0.2), glow=0.12)
    rng = np.random.default_rng(11)

    def dots(d):
        for _ in range(26):
            x, y, r = rng.uniform(80, 820), rng.uniform(80, 820), rng.uniform(10, 46)
            d.ellipse([(x - r) * SS, (y - r * 0.9) * SS, (x + r) * SS, (y + r * 0.9) * SS], fill=255)

    gel(c, dots, "#BFD0C4", 20, opacity=0.35, power=140)
    c.save("drops.jpg")

# ------------------------------------------------------------------- catalogue packshots (one per demo product)
PACKS = {
    "gc-cln-01": ("pump", "#F8F2EA", "CREAM CLEANSER", "#EDE3D6", "#E6D9C9"),
    "gc-cln-02": ("tube", "#DCE6D6", "GEL CLEANSER", "#E4EBDF", "#D8E0D2"),
    "gc-cln-03": ("pump", "#E9EFF0", "FOAM CLEANSER", "#E6ECEC", "#DAE2E2"),
    "gc-ser-01": ("dropper", "#E8C9B4", "NIACINAMIDE 5%", "#F3E3D7", "#E9D3C4"),
    "gc-ser-02": ("dropper", "#D6E1E6", "HYALURONIC", "#E7EEF0", "#DBE5E8"),
    "gc-ser-03": ("dropper", "#E7A07E", "VITAMIN C 10%", "#F4E1D3", "#EBCFBD"),
    "gc-ser-04": ("dropper", "#8E9A80", "RETINOL 0.3%", "#E6E2D8", "#D9D3C6"),
    "gc-ser-05": ("dropper", "#C9D8C4", "CENTELLA", "#E6ECE1", "#D9E1D3"),
    "gc-exf-01": ("bottle", "#EED9C3", "LACTIC 5%", "#F2E6D8", "#E7D7C6"),
    "gc-moi-01": ("jar", "#E9F0E6", "OIL-FREE GEL", "#E4EBDF", "#D7DFD1"),
    "gc-moi-02": ("jar", "#F4EADF", "CERAMIDE", "#F1E4D6", "#E5D4C3"),
    "gc-eye-01": ("tube", "#EEF2F3", "CAFFEINE EYE", "#E9EEEF", "#DDE4E6"),
    "gc-eye-02": ("tube", "#F1E6EE", "PEPTIDE EYE", "#F1E7EC", "#E5D8DF"),
    "gc-spf-01": ("tube", "#FBF5EE", "SHEER SPF 50", "#F5E4D6", "#EBD3C2"),
    "gc-spf-02": ("tube", "#EBCFBB", "MINERAL SPF 50", "#F3E2D5", "#E8D0BF"),
}
for pid, (kind, color, name, wall, floor) in PACKS.items():
    if not want(pid):
        continue
    c = Canvas(720, 900)
    backdrop(c, wall, wall, floor, floor, horizon=0.74, light=(0.22, 0.2), glow=0.14)
    leaf_shadows(c, hash(pid) % 97, strength=0.16, region=(-0.3, -0.25, 0.2, 0.2), blur_r=12, count=2, scale=1.3)
    by = 740
    if kind == "dropper":
        liquid = {"gc-ser-03": "#C2603B", "gc-ser-04": "#5E6852"}.get(pid)
        dropper(c, 360, by, 560, color, liquid or color, name=name, fill=0.8 if liquid else 0.0)
    elif kind == "pump":
        pump(c, 360, by, 520, color, name=name)
    elif kind == "tube":
        capc = {
            "gc-spf-01": "#C96F50",
            "gc-spf-02": "#382C29",
            "gc-eye-01": "#A9B4B8",
            "gc-eye-02": "#B98AA0",
            "gc-cln-02": "#5E6852",
        }[pid]
        tube(
            c,
            360,
            by,
            560 if pid.startswith("gc-spf") or pid == "gc-cln-02" else 470,
            color,
            cap=capc,
            name=name,
            slim=1.0 if pid.startswith("gc-spf") or pid == "gc-cln-02" else 0.8,
        )
    elif kind == "jar":
        jar(c, 360, by, 330, color, lid="#5E6852" if pid == "gc-moi-01" else "#A9553A", name=name)
    else:
        bottle(c, 360, by, 560, color, liquid="#D9A77F", name=name)
    c.save(f"{pid}.jpg", q=82)
