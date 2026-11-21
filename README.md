# dsh-skill-bilibili-video-to-gif

一个 [DeepSeek Harness](https://github.com/deepseek-ai) 技能：把 B站（或任意本地）视频截成 GIF 动图。

解决的是实操中最容易卡住的三个点：

1. **B站 412 风控** —— `yt-dlp` 会先抓播放页 HTML，非浏览器 UA 一律 412，带 cookie 也救不回来。本技能根本不碰播放页，只走 `api.bilibili.com`。
2. **CDN 403** —— `playurl` 返回的直链若落在 `*.akamaized.net` 会被拒，换成 `bilivideo.com` 镜像即可（签名串对 host 不敏感）。
3. **盲截时间点** —— 不看完整视频也能选准区间：先出带秒数标注的抽帧拼版，挑区间，再抽单帧复核。

## 快速开始

依赖：`curl`、`ffmpeg`、`python3` + Pillow。无需登录、无需 API key。

```bash
# 1. 下载（默认 360p；qn=32 为 480p）
python3 bilibili-video-to-gif/scripts/bili_fetch.py BV1T8J66CEEu -o downloads

# 2. 定位时间点：输出带秒数标注的拼版 PNG，挑出想要的区间
python3 bilibili-video-to-gif/scripts/frame_sheet.py downloads/BV1T8J66CEEu.mp4 -i 4 -o sheets

# 3. 截取（视频 起点 时长 输出 宽 fps 色数）
./bilibili-video-to-gif/scripts/to_gif.sh downloads/BV1T8J66CEEu.mp4 34 5 out/clip.gif 400 10 64
```

第 2 步是关键：`-i 8` 先看全片节奏，锁定候选区间后用 `-i 1` 精确定位，
再 `ffmpeg -ss <t> -i in.mp4 -frames:v 1 -y check.png` 抽单帧复核。

## 安装为 DSH 技能

```bash
git clone <本仓库> && cp -R bilibili-video-to-gif ~/.dsh/skills/
```

DSH 扫描 `~/.dsh/skills/<name>/SKILL.md`，放进去即被识别，无需重启。

## 参数经验（实测）

| 参数 | 推荐 | 说明 |
| --- | --- | --- |
| 时长 | 3–5 秒 | 超过 5 秒体积翻倍、信息量不增 |
| 宽度 | 400px | 微信/网页场景够用 |
| fps | 10 | 比 12 省约 20% 体积，肉眼无差 |
| 色数 | 64 | 96 更干净但体积 +30%；人脸特写建议 96 |
| 单条体积 | ≤ 2MB | 400px/10fps/5s/64 色 ≈ 1.5–1.9MB |

体积压不下去时：先砍时长，再砍宽度，最后才动 fps 和色数。

## 已知坑

- **下载"成功"但文件是 HTML**：必须校验文件头 `ftyp`，否则 ffmpeg 报 `moov atom not found`。
- **PIL 保存 GIF 会自动去重相同帧**：自己画动图时连续重复帧会被合并，动画变卡顿；改用"唯一帧 + 逐帧 `duration` 列表"表达停顿。
- **表情包聚合站不可靠**：`doutula.com` 搜索为模糊匹配（搜"范德彪"给二战纪录片），人物类素材要么自制，要么从授权视频截。
- **B站水印**：截取画面自带水印与 UP主 ID，裁掉等于丢署名，不建议。

## 合规与免责

本项目只做**格式转换与公开接口调用**，不存储、不分发任何视频内容。

- 使用前请自行确认目标平台的服务条款与 robots 协议。
- 截取产物是**原视频作者的作品**，公开发布需获授权，或仅以引用评论方式使用。
- 涉及真人的换脸/仿声内容，可能叠加肖像权、声音权问题（《中华人民共和国民法典》规定自然人声音参照肖像权保护）。
- 本仓库不包含任何视频、GIF 或受版权保护的素材。
- 脚本不含任何账号凭证。代码中的 `buvid3=infoc` 是调用公开接口时用的**匿名设备标识占位值**，与任何真实账号无关；如需替换可改 `bili_fetch.py` 顶部的 `COOKIE` 常量。

## 目录结构

```
bilibili-video-to-gif/
├── SKILL.md
└── scripts/
    ├── bili_fetch.py      # 取 cid → 取直链 → 镜像回退下载
    ├── frame_sheet.py     # 带秒数标注的抽帧拼版
    └── to_gif.sh          # 两遍调色板转 GIF + 自检
```

## License

MIT
