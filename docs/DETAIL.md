# B站视频转 GIF

注册一个 `bilibili-video-to-gif` 技能。装上之后，Agent 就能把 B站视频（或任何本地视频）截成 GIF 动图，并且知道怎么绕开出 B站时最常见的两道拦截。

## 它解决的问题

| 常见失败 | 原因 | 本技能的做法 |
| --- | --- | --- |
| `yt-dlp` 报 HTTP 412 | 先抓播放页 HTML，非浏览器 UA 一律被风控 | 完全不碰播放页，只调 `api.bilibili.com` |
| 下载得到 `Access Denied` | 直链落在 `*.akamaized.net` | 换 `bilivideo.com` 镜像域名 |
| 截出来的 GIF 是黑帧/字幕卡 | 凭感觉 `-ss` 猜位置 | 先出带秒数标注的抽帧拼版，再定点 |
| GIF 几 MB 还发灰发脏 | 直接 `ffmpeg -i in.mp4 out.gif` | 两遍调色板法（palettegen + paletteuse） |

## 装上之后怎么用

技能会随会话出现在 Agent 的技能列表里。直接说需求即可，例如：

> 把这个 BV1T8J66CEEu 的第 34 秒开始 5 秒截成动图

Agent 会依次跑 `scripts/bili_fetch.py`、`scripts/frame_sheet.py`、`scripts/to_gif.sh`。

也可以手工执行：

```bash
python3 bilibili-video-to-gif/scripts/bili_fetch.py BV1T8J66CEEu -o downloads
python3 bilibili-video-to-gif/scripts/frame_sheet.py downloads/BV1T8J66CEEu.mp4 -i 4 -o sheets
./bilibili-video-to-gif/scripts/to_gif.sh downloads/BV1T8J66CEEu.mp4 34 5 out/clip.gif 400 10 64
```

## 运行时依赖

插件本身是纯 Node 的，只读一个 Markdown 文件并注册技能，不安装任何二进制。
技能里的脚本运行时需要：`curl`、`ffmpeg`、`python3` + Pillow。缺失时脚本会明确报错。

## 局限

- 只处理视频到 GIF 的转换，不做剪辑合成、字幕压制。
- 不下载音轨（GIF 无声）。
- 更高清晰度（720p 以上）需要 B站登录态，默认走 360p。
- 不存储、不分发任何视频内容；截取产物是原视频作者的作品，公开发布需获授权。

## 卸载

移除本插件后技能随之消失，不会残留配置或状态。
