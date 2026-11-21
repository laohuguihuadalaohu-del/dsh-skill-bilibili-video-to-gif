#!/usr/bin/env python3
"""带时间戳的抽帧拼版：用来在不看视频的情况下定位"该截哪几秒"。

用法：
    python3 frame_sheet.py video.mp4 [-i 4] [-o sheets] [--cols 6] [--rows 4] [--thumb 240]

输出若干张 PNG，每格左上角标注该帧的秒数。对着拼版挑时间点，再交给 to_gif.sh。
"""
import argparse, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = ["/System/Library/Fonts/STHeiti Medium.ttc",
                   "/System/Library/Fonts/PingFang.ttc",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   "C:/Windows/Fonts/msyh.ttc"]


def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-i", "--interval", type=float, default=4.0, help="抽帧间隔（秒）")
    ap.add_argument("-o", "--outdir", default="sheets")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--thumb", type=int, default=240)
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    frames_dir = os.path.join(a.outdir, "_frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

    subprocess.run(["ffmpeg", "-v", "error", "-i", a.video,
                    "-vf", f"fps=1/{a.interval},scale={a.thumb}:-1",
                    os.path.join(frames_dir, "f_%04d.jpg")], check=True)

    files = sorted(os.listdir(frames_dir))
    if not files:
        sys.exit("[x] 抽帧为空，检查输入文件")

    per = a.cols * a.rows
    cell_w, cell_h = a.thumb + 6, int(a.thumb * 0.75) + 26
    font = load_font(15)
    for si in range(0, len(files), per):
        chunk = files[si:si + per]
        sheet = Image.new("RGB", (a.cols * cell_w, a.rows * cell_h), (20, 20, 22))
        d = ImageDraw.Draw(sheet)
        for k, fn in enumerate(chunk):
            im = Image.open(os.path.join(frames_dir, fn)).convert("RGB")
            im.thumbnail((a.thumb, a.thumb))
            cx, cy = (k % a.cols) * cell_w, (k // a.cols) * cell_h
            sheet.paste(im, (cx + 2, cy + 20))
            ts = (si + k) * a.interval
            d.text((cx + 4, cy + 2), f"{ts:.0f}s", font=font, fill=(255, 220, 90))
        out = os.path.join(a.outdir, f"sheet_{si // per + 1}.png")
        sheet.save(out)
        print(f"[ok] {out}  ({len(chunk)} 格, 起点 {si * a.interval:.0f}s)")
    print(f"[i] 共 {len(files)} 帧，间隔 {a.interval}s")


if __name__ == "__main__":
    main()
