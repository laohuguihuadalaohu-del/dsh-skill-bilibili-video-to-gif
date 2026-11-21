#!/usr/bin/env python3
"""B站视频抓取：取 cid → 取 360p 直链 → 镜像回退下载。

用法：
    python3 bili_fetch.py BV1xxxxxxxxx [-o 输出目录] [--qn 16]

绕过两个常见拦截：
  1. 播放页 HTML 对非浏览器 UA 返回 HTTP 412 —— 因此不碰播放页，只走 api.bilibili.com。
  2. playurl 给的直链若落在 *.akamaized.net 会 403 —— 换成 bilivideo.com 镜像（签名串对 host 不敏感）。
"""
import argparse, json, os, subprocess, sys, time

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
REFERER = "https://www.bilibili.com/"
COOKIE = "buvid3=infoc; b_nut=1700000000"
MIRRORS = ("upos-sz-mirrorali.bilivideo.com",
           "upos-sz-mirrorcosov.bilivideo.com",
           "upos-sz-mirrorhw.bilivideo.com")


def curl(url, out=None, referer=REFERER, max_time=30):
    cmd = ["curl", "-sL", "--max-time", str(max_time), "-A", UA,
           "-H", f"Referer: {referer}", "-H", f"Cookie: {COOKIE}"]
    if out:
        cmd += ["-o", out]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout


def get_meta(bvid):
    raw = curl(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    d = json.loads(raw)
    if d.get("code") != 0:
        sys.exit(f"[x] view API 失败：{d.get('code')} {d.get('message')}")
    v = d["data"]
    return {"cid": v["cid"], "title": v["title"], "duration": v["duration"],
            "owner": v.get("owner", {}).get("name", "")}


def get_streams(bvid, cid, qn):
    url = (f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}"
           f"&qn={qn}&fnval=0&fnver=0&fourk=0")
    d = json.loads(curl(url, referer=f"https://www.bilibili.com/video/{bvid}"))
    if d.get("code") != 0:
        sys.exit(f"[x] playurl 失败：{d.get('code')} {d.get('message')}")
    return [u["url"] for u in (d.get("data") or {}).get("durl") or []]


def candidates(url):
    """原始直链 + 各镜像替换后的直链，按可用性顺序返回。"""
    if "bilivideo.com" in url:
        return [url] + [url.replace(url.split("/")[2], m) for m in MIRRORS]
    host = url.split("/")[2]
    out = [url.replace(host, m) for m in MIRRORS]
    return out + [url]


def is_mp4(path):
    try:
        with open(path, "rb") as f:
            return f.read(12)[4:8] == b"ftyp"
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bvid")
    ap.add_argument("-o", "--outdir", default="downloads")
    ap.add_argument("--qn", type=int, default=16, help="清晰度：16=360p 32=480p 64=720p（更高需登录）")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    meta = get_meta(a.bvid)
    print(f"[i] {meta['title']} | {meta['owner']} | {meta['duration']}s | cid={meta['cid']}")
    dst = os.path.join(a.outdir, f"{a.bvid}.mp4")
    if os.path.exists(dst) and is_mp4(dst):
        print(f"[=] 已存在，跳过：{dst}")
        return

    for attempt in range(4):
        for url in get_streams(a.bvid, meta["cid"], a.qn):
            for cand in candidates(url):
                curl(cand, out=dst, referer=f"https://www.bilibili.com/video/{a.bvid}", max_time=240)
                if is_mp4(dst):
                    print(f"[ok] {dst} ({os.path.getsize(dst)//1048576}MB) via {cand.split('/')[2]}")
                    return
        time.sleep(2)
    sys.exit("[x] 下载失败：所有镜像均不可用（可降低 qn 或换网络重试）")


if __name__ == "__main__":
    main()
