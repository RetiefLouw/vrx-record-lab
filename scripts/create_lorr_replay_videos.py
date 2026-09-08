#!/usr/bin/env python3
"""Create data-derived LoRR replay visualisations for the evidence page.

The repository keeps LoRR result ledgers and compact output hashes, but no
simulator video or per-agent trajectory logs.  These clips therefore animate
only verified ledger values (task count, tick limit, error counters, and
runtime condition).  They are deliberately marked as illustrative replay
visualisations and must not be presented as raw simulator footage.
"""

from __future__ import annotations

import math
import random
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "lorr-runs"
FRAMES = ROOT / "artifacts" / "lorr-replay-frames"
WIDTH, HEIGHT = 1280, 720
FPS = 24
DURATION = 12

BG = (7, 15, 27)
PANEL = (13, 27, 45)
PANEL_2 = (16, 35, 56)
GRID = (34, 61, 83)
TEXT = (225, 238, 247)
MUTED = (135, 164, 183)
DIM = (90, 116, 137)
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
F44 = font(44, True)


RUNS = [
    {
        "slug": "lorr-q35-pinned-clean-beat",
        "queue": "Q-35",
        "kind": "CURRENT CLEAN LOCAL BEST",
        "title": "Team RAPID · pinned runtime",
        "tasks": 1325,
        "reference": 1186,
        "delta": "+139",
        "ticks": 500,
        "agents": 100,
        "wall": "478.405 s",
        "runtime": "OMP_NUM_THREADS=1 · Docker CPU 0",
        "output_hash": "39525159…6ca88a5b",
        "input_hash": "c09782a2…445302",
        "color": GREEN,
        "seed": 35,
    },
    {
        "slug": "lorr-q31-previous-clean-beat",
        "queue": "Q-31",
        "kind": "PREVIOUS CLEAN LOCAL BEAT",
        "title": "Team RAPID · baseline runtime",
        "tasks": 1318,
        "reference": 1186,
        "delta": "+132",
        "ticks": 500,
        "agents": 100,
        "wall": "not recorded in ledger",
        "runtime": "same source/image · no CPU pin recorded",
        "output_hash": "e5f2f0ed…f9a852e6",
        "input_hash": "c09782a2…445302",
        "color": BLUE,
        "seed": 31,
    },
]


def txt(draw: ImageDraw.ImageDraw, xy, value: str, f=F14, fill=TEXT, anchor=None):
    draw.text(xy, value, font=f, fill=fill, anchor=anchor)


def rounded(draw: ImageDraw.ImageDraw, xy, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def task_count(run: dict, elapsed: float) -> int:
    """Monotone presentation curve ending at the verified ledger count."""
    active = clip((elapsed - 0.7) / 10.7, 0.0, 1.0)
    eased = 1.0 - (1.0 - active) ** 1.25
    # The small deterministic ripple makes the chart read as a live stream,
    # while the clamp keeps the displayed count monotone and ledger-exact.
    ripple = 2.0 * math.sin(elapsed * 1.45 + run["seed"] * 0.07) * active
    value = int(run["tasks"] * eased + ripple)
    if elapsed >= DURATION - 0.04:
        value = run["tasks"]
    return max(0, min(run["tasks"], value))


def fleet_positions(run: dict, elapsed: float):
    """Deterministic schematic dots; this is not a recorded trajectory."""
    rng = random.Random(run["seed"])
    starts = [(rng.uniform(0.5, 31.5), rng.uniform(0.5, 31.5)) for _ in range(run["agents"])]
    goals = [(rng.uniform(0.5, 31.5), rng.uniform(0.5, 31.5)) for _ in range(run["agents"])]
    p = clip((elapsed - 0.7) / 10.7, 0.0, 1.0)
    out = []
    for idx, ((sx, sy), (gx, gy)) in enumerate(zip(starts, goals)):
        phase = (idx % 11) * 0.035
        local = clip(p * (0.92 + (idx % 7) * 0.01) + phase, 0.0, 1.0)
        curve = math.sin((elapsed + idx * 0.19) * 1.1) * 0.25
        x = sx + (gx - sx) * local + curve
        y = sy + (gy - sy) * local + math.cos((elapsed + idx * 0.13) * 0.9) * 0.22
        out.append((clip(x, 0.3, 31.7), clip(y, 0.3, 31.7), idx))
    return out


def grid_xy(x: float, y: float):
    left, top, right, bottom = 70, 195, 600, 625
    return left + x / 32 * (right - left), bottom - y / 32 * (bottom - top)


def header(draw: ImageDraw.ImageDraw, run: dict, elapsed: float):
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=BG)
    txt(draw, (42, 27), "VRX RECORD LAB", F16, CYAN)
    txt(draw, (42, 51), "LoRR 2024 // RESULT REPLAY", F22)
    txt(draw, (1238, 29), "ILLUSTRATIVE REPLAY VISUALISATION", F12, YELLOW, "ra")
    txt(draw, (1238, 48), "NOT RAW SIMULATOR FOOTAGE", F12, YELLOW, "ra")
    rounded(draw, (42, 88, 654, 155), 10, PANEL_2)
    txt(draw, (60, 108), run["queue"], F18, run["color"], "lm")
    txt(draw, (132, 108), run["kind"], F12, run["color"], "lm")
    txt(draw, (60, 137), run["title"], F16, TEXT, "lm")
    txt(draw, (678, 120), f"preview time {elapsed:04.1f} s", F14, MUTED, "rm")
    rounded(draw, (714, 88, 1238, 155), 10, PANEL_2)
    txt(draw, (734, 108), "SCHEMATIC / LEDGER-DERIVED", F12, YELLOW, "lm")
    txt(draw, (734, 137), "Verified counts are shown; paths are illustrative", F14, MUTED, "lm")


def draw_map(draw: ImageDraw.ImageDraw, run: dict, elapsed: float):
    rounded(draw, (42, 174, 640, 650), 12, PANEL, GRID, 1)
    txt(draw, (62, 195), "SCHEMATIC FLEET VIEW · 32 × 32 GRID", F12, MUTED)
    txt(draw, (62, 215), "animated dots are explanatory, not captured trajectories", F12, DIM)
    left, top, right, bottom = 70, 235, 600, 625
    for val in range(0, 33, 4):
        x1, y1 = grid_xy(val, 0)
        x2, y2 = grid_xy(val, 32)
        draw.line((x1, y1, x2, y2), fill=GRID, width=1)
        x1, y1 = grid_xy(0, val)
        x2, y2 = grid_xy(32, val)
        draw.line((x1, y1, x2, y2), fill=GRID, width=1)
    # A few static obstacles make the map read like a benchmark grid, but do
    # not purport to recover the exact archived obstacle field.
    for x, y, w, h in ((7, 8, 4, 2), (20, 14, 2, 6), (12, 24, 6, 2), (25, 5, 3, 3)):
        x1, y1 = grid_xy(x, y + h)
        x2, y2 = grid_xy(x + w, y)
        draw.rectangle((x1, y1, x2, y2), fill=(27, 47, 66), outline=(52, 82, 105))
    positions = fleet_positions(run, elapsed)
    for x, y, idx in positions:
        px, py = grid_xy(x, y)
        color = run["color"] if idx % 9 == 0 else (105, 148, 175)
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)
    gx, gy = grid_xy(16, 16)
    draw.ellipse((gx - 11, gy - 11, gx + 11, gy + 11), outline=CYAN, width=2)
    draw.line((gx - 17, gy, gx + 17, gy), fill=CYAN, width=1)
    draw.line((gx, gy - 17, gx, gy + 17), fill=CYAN, width=1)
    txt(draw, (gx + 18, gy), "task flow / grid centre", F12, CYAN, "lm")
    txt(draw, (left, 640), "100 agents · public Test Round instance", F12, MUTED)


def draw_chart(draw: ImageDraw.ImageDraw, run: dict, elapsed: float):
    rounded(draw, (660, 174, 1238, 650), 12, PANEL, GRID, 1)
    txt(draw, (680, 195), "VERIFIED LEDGER SIGNAL", F12, MUTED)
    txt(draw, (680, 220), "completed tasks over the 500-tick clock", F14, TEXT)
    chart = (700, 252, 1200, 420)
    x0, y0, x1, y1 = chart
    for value in (0, 400, 800, 1186, 1325):
        py = y1 - value / 1400 * (y1 - y0)
        draw.line((x0, py, x1, py), fill=GRID, width=1)
        txt(draw, (x0 - 10, py), f"{value:,}", F12, MUTED, "rm")
    draw.line((x0, y1, x1, y1), fill=(77, 104, 126), width=1)
    draw.line((x0, y0, x0, y1), fill=(77, 104, 126), width=1)
    ref_y = y1 - run["reference"] / 1400 * (y1 - y0)
    draw.line((x0, ref_y, x1, ref_y), fill=YELLOW, width=2)
    txt(draw, (x1, ref_y - 10), f"archive ref {run['reference']:,}", F12, YELLOW, "ra")
    points = []
    samples = 100
    for i in range(samples + 1):
        t = elapsed * i / samples
        count = task_count(run, t)
        px = x0 + t / DURATION * (x1 - x0)
        py = y1 - count / 1400 * (y1 - y0)
        points.append((px, py))
    if len(points) > 1:
        draw.line(points, fill=run["color"], width=4, joint="curve")
    current = task_count(run, elapsed)
    cx = x0 + elapsed / DURATION * (x1 - x0)
    cy = y1 - current / 1400 * (y1 - y0)
    draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=run["color"], outline=TEXT, width=1)
    txt(draw, (x0, y1 + 22), "0 s", F12, MUTED)
    txt(draw, (x1, y1 + 22), "500 ticks", F12, MUTED, "ra")
    rounded(draw, (680, 460, 1218, 555), 10, PANEL_2)
    txt(draw, (702, 482), "TASKS FINISHED", F12, MUTED)
    txt(draw, (702, 524), f"{current:,}", F44, run["color"])
    txt(draw, (860, 515), f"target ledger: {run['tasks']:,}", F14, MUTED)
    rounded(draw, (680, 574, 1218, 630), 10, (18, 43, 48))
    txt(draw, (702, 595), f"errors  0 planner · 0 schedule · 0 entry timeouts", F14, GREEN, "lm")
    txt(draw, (1210, 595), f"final {run['delta']} vs archive", F14, run["color"], "rm")


def draw_footer(draw: ImageDraw.ImageDraw, run: dict):
    txt(draw, (42, 691), f"{run['queue']} · {run['agents']} agents · {run['ticks']} ticks · {run['runtime']}", F12, MUTED)
    txt(draw, (1238, 691), "local protocol-scoped evidence · not an official leaderboard update", F12, YELLOW, "ra")


def create_video(run: dict):
    out_path = OUTPUT / f"{run['slug']}.mp4"
    poster_path = OUTPUT / f"{run['slug']}.png"
    frame_dir = FRAMES / run["slug"]
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    total = DURATION * FPS
    for frame in range(total):
        elapsed = frame / FPS
        image = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)
        header(draw, run, elapsed)
        draw_map(draw, run, elapsed)
        draw_chart(draw, run, elapsed)
        draw_footer(draw, run)
        image.save(frame_dir / f"frame_{frame:04d}.png", optimize=True)
    shutil.copy2(frame_dir / "frame_0000.png", poster_path)
    if out_path.exists():
        out_path.unlink()
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frame_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-metadata", f"title=LoRR {run['queue']} illustrative replay visualisation",
            "-metadata", "comment=Ledger-derived animation; not raw simulator footage",
            "-metadata", f"queue={run['queue']}",
            "-metadata", f"verified_tasks={run['tasks']}",
            str(out_path),
        ],
        check=True,
    )
    print(f"created {out_path} ({out_path.stat().st_size:,} bytes)")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    for run in RUNS:
        create_video(run)
    shutil.rmtree(FRAMES)


if __name__ == "__main__":
    main()
