#!/usr/bin/env python3
"""Create compact, illustrative VRX station-keeping run videos.

These are visual explainers, not recordings from the private VRX 2019 phase-3
evaluator. The trajectories are deterministic and intentionally annotated with
that distinction in every video.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "sample-runs"
FRAMES = ROOT / "artifacts" / "sample-run-frames"
WIDTH, HEIGHT = 1280, 720
FPS = 24
DURATION_S = 12

BG = (7, 15, 27)
PANEL = (13, 27, 45)
PANEL_2 = (16, 35, 56)
GRID = (34, 61, 83)
TEXT = (225, 238, 247)
MUTED = (135, 164, 183)
CYAN = (64, 211, 202)
YELLOW = (249, 190, 70)
RED = (250, 105, 94)
BLUE = (83, 151, 255)
GREEN = (94, 219, 137)


def font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


F12 = font(12)
F14 = font(14)
F16 = font(16)
F18 = font(18, True)
F22 = font(22, True)
F30 = font(30, True)


SCENARIOS = [
    {
        "slug": "vrx-sample-run-01-calm",
        "label": "SAMPLE RUN 01",
        "title": "Calm water / clean hold",
        "seed": 10,
        "wind": "0 m/s mean",
        "waves": "0.0 m gain",
        "kind": "completed",
        "color": GREEN,
    },
    {
        "slug": "vrx-sample-run-02-disturbed",
        "label": "SAMPLE RUN 02",
        "title": "Crosswind / oscillating hold",
        "seed": 15,
        "wind": "4 m/s mean",
        "waves": "0.2 m gain",
        "kind": "completed",
        "color": YELLOW,
    },
    {
        "slug": "vrx-sample-run-03-timeout",
        "label": "SAMPLE RUN 03",
        "title": "Gust / timeout recovery",
        "seed": 42,
        "wind": "8 m/s gust",
        "waves": "0.7 m gain",
        "kind": "timeout",
        "color": RED,
    },
]


def trajectory(index: int, n: int):
    t = np.linspace(0, DURATION_S, n)
    run = np.maximum(0.0, (t - 1.8) / 9.0)
    if index == 0:
        x = (10.5 * np.exp(-0.75 * t) * np.cos(0.70 * t) + 0.16 * np.sin(3.2 * t)) * (t < 1.8) + (0.6 * np.exp(-0.8 * run * 9) * np.cos(2.1 * t) + 0.10 * np.sin(4 * t)) * (t >= 1.8)
        y = (-7.0 * np.exp(-0.68 * t) * np.sin(0.75 * t) + 0.11 * np.cos(2.5 * t)) * (t < 1.8) + (-0.48 * np.exp(-0.75 * run * 9) * np.sin(1.8 * t) + 0.10 * np.cos(3.2 * t)) * (t >= 1.8)
        hd = 0.45 * np.exp(-0.6 * t) + 0.018 * np.sin(2.7 * t)
    elif index == 1:
        x = 8.8 * np.exp(-0.48 * t) * np.cos(0.74 * t) + 0.55 * np.sin(1.35 * t) * run + 0.18 * np.sin(5.0 * t)
        y = -6.6 * np.exp(-0.52 * t) * np.sin(0.78 * t) + 0.8 * np.sin(1.1 * t + 0.8) * run + 0.16 * np.cos(4.4 * t)
        hd = 0.52 * np.exp(-0.42 * t) + 0.11 * np.sin(1.55 * t) * run + 0.025 * np.sin(4.6 * t)
    else:
        gust = np.clip((t - 5.4) / 1.0, 0, 1) * np.clip((10.9 - t) / 1.5, 0, 1)
        x = 3.6 * np.exp(-0.9 * t) * np.cos(1.1 * t) + 3.4 * gust + 0.45 * np.sin(1.7 * t) * run
        y = -2.8 * np.exp(-0.8 * t) * np.sin(1.0 * t) - 2.2 * gust + 0.35 * np.cos(1.25 * t) * run
        hd = 0.30 * np.exp(-0.4 * t) + 0.75 * gust + 0.04 * np.sin(2.0 * t)
    phase = np.where(t < 0.9, "INITIAL", np.where(t < 1.8, "READY", np.where(t < 10.8, "RUNNING", "FINISHED")))
    return t, x, y, hd, phase


def score_components(x, y, hd, phase):
    mask = phase == "RUNNING"
    position = np.hypot(x, y)
    heading = np.abs(hd)
    heading_term = np.clip(heading / math.pi, 0, 1)
    pose = position + heading_term
    running_mean = np.full_like(pose, np.nan, dtype=float)
    vals = pose[mask]
    for i in np.flatnonzero(mask):
        running_mean[i] = float(np.mean(pose[np.flatnonzero(mask)[0] : i + 1]))
    return position, heading_term, pose, running_mean


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, f=F14, fill=TEXT, anchor=None):
    draw.text(xy, value, font=f, fill=fill, anchor=anchor)


def plot_bounds():
    return (56, 154, 716, 596)


def to_xy(x, y):
    left, top, right, bottom = plot_bounds()
    return left + (x + 15) / 30 * (right - left), bottom - (y + 15) / 30 * (bottom - top)


def draw_base(draw, scenario, elapsed, phase):
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=BG)
    text(draw, (42, 26), "VRX RECORD LAB", F16, CYAN)
    text(draw, (42, 49), "VRX 2019 // STATION KEEPING", F22)
    text(draw, (1237, 34), "ILLUSTRATIVE RECONSTRUCTION", F12, YELLOW, "ra")
    text(draw, (1237, 52), "NOT OFFICIAL PHASE-3 FOOTAGE", F12, YELLOW, "ra")
    rounded(draw, (42, 90, 716, 132), 10, PANEL_2)
    text(draw, (58, 111), scenario["label"], F14, scenario["color"], "lm")
    text(draw, (206, 111), scenario["title"], F16, TEXT, "lm")
    text(draw, (700, 111), f"t = {elapsed:04.1f} s", F14, MUTED, "rm")
    rounded(draw, (742, 90, 1238, 132), 10, PANEL_2)
    text(draw, (760, 111), "STATE", F12, MUTED, "lm")
    phase_color = GREEN if phase == "RUNNING" else YELLOW if phase == "READY" else MUTED
    if phase == "FINISHED" and scenario["kind"] == "timeout":
        phase_color = RED
    text(draw, (820, 111), phase, F16, phase_color, "lm")
    text(draw, (1222, 111), "lower score is better", F12, MUTED, "rm")
    rounded(draw, (42, 148, 730, 610), 12, PANEL, GRID, 1)
    rounded(draw, (746, 148, 1238, 610), 12, PANEL, GRID, 1)
    text(draw, (60, 170), "TOP-DOWN LOCAL FRAME", F12, MUTED)
    text(draw, (760, 170), "LIVE RUN TELEMETRY", F12, MUTED)


def draw_spatial(draw, x, y, trail_x, trail_y, hd, wind_strength):
    left, top, right, bottom = plot_bounds()
    for val in range(-15, 16, 5):
        px1, py1 = to_xy(val, -15)
        px2, py2 = to_xy(val, 15)
        draw.line((px1, py1, px2, py2), fill=GRID, width=1)
        px1, py1 = to_xy(-15, val)
        px2, py2 = to_xy(15, val)
        draw.line((px1, py1, px2, py2), fill=GRID, width=1)
        text(draw, (px1, bottom + 14), f"{val}", F12, MUTED, "ma")
        text(draw, (left - 13, py1), f"{val}", F12, MUTED, "rm")
    draw.line((to_xy(-15, 0)[0], to_xy(-15, 0)[1], to_xy(15, 0)[0], to_xy(15, 0)[1]), fill=(77, 104, 126), width=1)
    draw.line((to_xy(0, -15)[0], to_xy(0, -15)[1], to_xy(0, 15)[0], to_xy(0, 15)[1]), fill=(77, 104, 126), width=1)
    text(draw, (385, 587), "x error (m)", F12, MUTED, "ma")
    text(draw, (52, 375), "y error (m)", F12, MUTED, "mm")
    gx, gy = to_xy(0, 0)
    draw.ellipse((gx - 30, gy - 30, gx + 30, gy + 30), outline=(64, 211, 202), width=2)
    draw.ellipse((gx - 5, gy - 5, gx + 5, gy + 5), fill=CYAN)
    text(draw, (gx + 40, gy - 10), "GOAL", F12, CYAN, "lm")
    if len(trail_x) > 1:
        points = [to_xy(a, b) for a, b in zip(trail_x, trail_y)]
        draw.line(points, fill=(80, 127, 149), width=3, joint="curve")
    bx, by = to_xy(x, y)
    draw.ellipse((bx - 13, by - 13, bx + 13, by + 13), fill=YELLOW, outline=TEXT, width=2)
    length = 28
    draw.line((bx, by, bx + math.cos(-hd) * length, by + math.sin(-hd) * length), fill=YELLOW, width=4)
    text(draw, (bx, by + 23), "WAM-V", F12, YELLOW, "ma")
    if wind_strength > 0:
        ax, ay = 610, 215
        draw.line((ax - 36 * wind_strength, ay, ax, ay), fill=BLUE, width=4)
        draw.polygon([(ax + 4, ay), (ax - 10, ay - 8), (ax - 10, ay + 8)], fill=BLUE)
        text(draw, (ax - 42, ay - 18), "WIND", F12, BLUE, "ma")
    text(draw, (60, 568), "Goal = fixed pose at (0, 0, 0°)", F12, MUTED)


def draw_chart(draw, t, position, heading, running_mean, current_idx, scenario):
    left, top, right, bottom = 776, 210, 1208, 380
    # position-error chart
    for yval in (0, 2, 4, 6, 8, 10):
        py = bottom - yval / 10 * (bottom - top)
        draw.line((left, py, right, py), fill=GRID, width=1)
        text(draw, (left - 12, py), str(yval), F12, MUTED, "rm")
    draw.line((left, bottom, right, bottom), fill=(77, 104, 126), width=1)
    draw.line((left, top, left, bottom), fill=(77, 104, 126), width=1)
    text(draw, (left, 190), "position error (m)", F12, MUTED)
    text(draw, (right, bottom + 24), "time", F12, MUTED, "ra")
    def chartxy(tx, val):
        return left + tx / DURATION_S * (right - left), bottom - val / 10 * (bottom - top)
    pos_points = [chartxy(float(a), float(b)) for a, b in zip(t[: current_idx + 1], position[: current_idx + 1])]
    if len(pos_points) > 1:
        draw.line(pos_points, fill=YELLOW, width=3)
    cx, cy = chartxy(float(t[current_idx]), float(position[current_idx]))
    draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=YELLOW)
    text(draw, (1056, 190), "● position", F12, YELLOW)
    # score panel
    rounded(draw, (776, 408, 1208, 514), 10, PANEL_2)
    text(draw, (796, 432), "RUNNING MEAN-POSE SCORE", F12, MUTED)
    score = running_mean[current_idx]
    if np.isnan(score):
        score_label = "not scoring yet"
    else:
        score_label = f"{score:.2f}"
    score_color = scenario["color"] if not np.isnan(score) else MUTED
    score_font = F30 if not np.isnan(score) else F22
    text(draw, (796, 474), score_label, score_font, score_color)
    if not np.isnan(score):
        text(draw, (910, 474), "m-equivalent", F14, MUTED)
    text(draw, (796, 501), "Illustrative public-code mean; not an official result", F12, MUTED)
    # state timeline
    text(draw, (776, 552), "RUN LIFECYCLE", F12, MUTED)
    phases = [("INITIAL", 0, 0.9, MUTED), ("READY", 0.9, 1.8, YELLOW), ("RUNNING", 1.8, 10.8, GREEN), ("FINISHED", 10.8, 12, RED if scenario["kind"] == "timeout" else MUTED)]
    x0, y0, w, h = 776, 570, 432, 14
    for label, start, end, color in phases:
        x1 = x0 + start / DURATION_S * w
        x2 = x0 + end / DURATION_S * w
        draw.rectangle((x1, y0, x2, y0 + h), fill=color)
        if x2 - x1 > 45:
            text(draw, ((x1 + x2) / 2, y0 + h / 2), label, F12, BG, "mm")
    elapsed = float(t[current_idx])
    cursor = x0 + min(elapsed, DURATION_S) / DURATION_S * w
    draw.line((cursor, y0 - 6, cursor, y0 + h + 6), fill=TEXT, width=2)
    text(draw, (x0, y0 + 30), "0 s", F12, MUTED)
    text(draw, (x0 + w, y0 + 30), "12 s preview", F12, MUTED, "ra")


def create_video(index: int, scenario: dict):
    t, x, y, hd, phase = trajectory(index, int(DURATION_S * FPS))
    position, heading, pose, running_mean = score_components(x, y, hd, phase)
    out_path = OUTPUT / f"{scenario['slug']}.mp4"
    poster_path = OUTPUT / f"{scenario['slug']}.png"
    frame_dir = FRAMES / scenario["slug"]
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(len(t)):
        image = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)
        draw_base(draw, scenario, float(t[idx]), str(phase[idx]))
        trail_start = max(0, idx - int(5 * FPS))
        draw_spatial(draw, float(x[idx]), float(y[idx]), x[trail_start : idx + 1], y[trail_start : idx + 1], float(hd[idx]), 0.35 if index == 1 else 0.75 if index == 2 else 0.0)
        draw_chart(draw, t, position, heading, running_mean, idx, scenario)
        image.save(frame_dir / f"frame_{idx:04d}.png", optimize=True)
    shutil.copy2(frame_dir / "frame_0000.png", poster_path)
    if out_path.exists():
        out_path.unlink()
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frame_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-metadata", f"title=VRX Record Lab {scenario['title']}",
            "-metadata", "comment=Illustrative reconstruction; not official VRX phase-3 footage",
            str(out_path),
        ],
        check=True,
    )
    print(f"created {out_path} ({out_path.stat().st_size:,} bytes)")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    for index, scenario in enumerate(SCENARIOS):
        create_video(index, scenario)
    shutil.rmtree(FRAMES)


if __name__ == "__main__":
    main()
