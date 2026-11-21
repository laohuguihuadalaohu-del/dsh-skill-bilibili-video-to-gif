#!/usr/bin/env bash
# 视频片段 → GIF，并在生成后自检。
# 用法: ./to_gif.sh <视频> <起始秒> <时长秒> <输出.gif> [宽度=400] [fps=10] [色彩数=64]
set -euo pipefail

SRC=${1:?需要输入视频}
START=${2:?需要起始秒}
DUR=${3:?需要时长秒}
OUT=${4:?需要输出路径}
W=${5:-400}
FPS=${6:-10}
COLORS=${7:-64}

command -v ffmpeg >/dev/null || { echo "[x] 缺少 ffmpeg" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"

# 两遍调色板法：GIF 只有 256 色，直接转会脏；palettegen/paletteuse 明显更干净。
ffmpeg -v error -ss "$START" -t "$DUR" -i "$SRC" \
  -vf "fps=${FPS},scale=${W}:-1:flags=lanczos,split[a][b];\
[a]palettegen=max_colors=${COLORS}:stats_mode=diff[p];\
[b][p]paletteuse=dither=bayer:bayer_scale=4" \
  -loop 0 -y "$OUT"

KB=$(( $(stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT") / 1024 ))
echo "[ok] $OUT  ${KB}KB"

# 自检：帧数、尺寸；只有 1 帧说明片段是静帧或时间点截错了。
python3 - "$OUT" <<'PY'
import sys
try:
    from PIL import Image
except ImportError:
    sys.exit("[!] 未装 Pillow，跳过自检")
p = sys.argv[1]
im = Image.open(p)
n = getattr(im, "n_frames", 1)
print(f"[i] {im.size[0]}x{im.size[1]}, {n} 帧")
if n < 2:
    sys.exit("[!] 只有 1 帧：该时间点可能是静帧/黑帧，换个时间点重截")
if n < 12:
    print("[!] 帧数偏少，动作可能不连贯（时长太短或 fps 太低）")
PY
