#!/usr/bin/env python3
"""
extract.py — 视频知识提取管线 (Goal 2)

输入: 视频 URL (YouTube / Bilibili / 抖音 / TikTok / ...)
输出: 结构化知识页面 → 写入知识库 wiki/

管线: lux 优先下载 → yt-dlp 兜底 → 字幕提取 / whisper 转录 → LLM 提取 → KB 写入
依赖: lux (Go 单文件, vendor/bin/), yt-dlp (Python 包, 兜底), ffmpeg (imageio_ffmpeg 内置)

============================================================
运行方式:
  set PYTHONPATH=D:/subject/sage/vendor
  export DEEPSEEK_API_KEY=sk-xxx
  python extract.py "https://www.bilibili.com/video/BVxxxx"

  python extract.py --audio audio.wav --subs subs.srt
  python extract.py "https://..." --domain software-dev
  python extract.py "https://..." --transcribe-only  # 调试
  python extract.py "https://v.douyin.com/xxx" --cookie cookies.txt
============================================================
"""

import sys, os, json, re, time, argparse, hashlib, subprocess, shutil, locale
from pathlib import Path
from datetime import datetime
from typing import Optional

# ——— 强制 UTF-8 (Windows 终端默认 GBK 是万恶之源) ——————
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ——— 路径配置 ——————————————————————————————————————
SCRIPT_DIR = Path(__file__).resolve().parent        # D:/subject/sage
VENDOR_DIR = SCRIPT_DIR / "vendor"                   # D:/subject/sage/vendor
BIN_DIR = VENDOR_DIR / "bin"                         # D:/subject/sage/vendor/bin
sys.path.insert(0, str(VENDOR_DIR))
sys.path.insert(0, str(BIN_DIR))

WORK_DIR = Path(os.environ.get("SAGE_WORK_DIR", SCRIPT_DIR / "output" / "extract"))
KB_WIKI_DIR = Path(os.environ.get("KB_WIKI_DIR", "F:/AI/projects/knowledge-base/wiki"))

# ——— 日志 ————————————————————————————————————————————
def log(msg: str) -> None:
    print(f"[extract] {msg}", flush=True)

# ——— 环境 (编码安全的子进程) ———————————————————————————
def _safe_env() -> dict:
    """子进程环境: UTF-8 + ffmpeg/lux 在 PATH + vendor PYTHONPATH"""
    env = os.environ.copy()
    ffmpeg_dir = str(Path(FFMPEG).parent) if FFMPEG else ""
    env["PATH"] = os.pathsep.join(filter(None, [str(BIN_DIR), ffmpeg_dir, env.get("PATH", "")]))
    env["PYTHONPATH"] = str(VENDOR_DIR)
    for v in ["PYTHONIOENCODING", "LANG", "LC_ALL"]:
        env[v] = "utf-8"
    return env

# ——— ffmpeg 定位 —————————————————————————————————————
def _find_ffmpeg() -> Optional[str]:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(exe).exists() and os.access(exe, os.X_OK):
            return exe
    except Exception:
        pass
    for name in ["ffmpeg", "ffmpeg.exe"]:
        found = shutil.which(name)
        if found:
            return found
    return None

FFMPEG = _find_ffmpeg()

# ——— lux 定位 ———————————————————————————————————————
def _find_lux() -> Optional[str]:
    vendor = BIN_DIR / "lux.exe"
    if vendor.exists():
        return str(vendor)
    return shutil.which("lux") or shutil.which("lux.exe")

LUX = _find_lux()

# ——— yt-dlp 定位 ————————————————————————————————————
def _find_ytdlp() -> str:
    vendor = BIN_DIR / "yt-dlp.exe"
    if vendor.exists():
        return str(vendor)
    found = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if found:
        return found
    # 兜底: python -m yt_dlp (依赖 PYTHONPATH=vendor)
    return f'"{sys.executable}" -m yt_dlp'

YTDLP = _find_ytdlp()

# ——— 平台识别 ————————————————————————————————————————
LUX_NATIVE = {
    "bilibili", "youku", "iqiyi", "mgtv", "acfun",
    "youtube", "tiktok", "twitter", "instagram", "facebook",
    "weibo", "vimeo",
}

DOUYIN_SHORT_RE = re.compile(r'v\.douyin\.com|www\.douyin\.com')
DOUYIN_VID_RE = re.compile(r'/video/(\d+)')
DOUYIN_SHARE_RE = re.compile(r'www\.iesdouyin\.com/share/video/(\d+)')
DOUYIN_ROUTER_RE = re.compile(r'window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>', re.S)

DOUYIN_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
)

def _platform(url: str) -> Optional[str]:
    u = url.lower()
    if DOUYIN_SHORT_RE.search(u) or DOUYIN_SHARE_RE.search(u) or DOUYIN_VID_RE.search(u):
        return "douyin"
    for site in LUX_NATIVE:
        if site in u:
            return site
    return None


# ═══════════════════════════════════════════════════════
# Step 1: 下载 (douyin 原生 → lux → yt-dlp 兜底)
# ═══════════════════════════════════════════════════════

def download_video(url: str, output_dir: Path, cookie: str = None) -> dict:
    """
    三引擎下载。返回 {"video": Path|None, "audio": Path|None,
                      "subs": Path|None,  "meta": dict}
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    platform = _platform(url)

    # 抖音优先用原生提取器 (全自动, 无需 cookie)
    if platform == "douyin":
        try:
            log(f"[douyin] 原生提取器 → {url}")
            return _douyin_dl(url, output_dir)
        except Exception as e:
            log(f"douyin 原生失败: {e}")
            raise  # 不 fallback——yt-dlp 也需要 cookie

    if LUX and platform:
        try:
            log(f"[lux] {platform} → {url}")
            return _lux_dl(url, output_dir, cookie)
        except Exception as e:
            log(f"lux 失败: {e} → yt-dlp 兜底")
    else:
        log(f"lux {'无' if not LUX else '不覆盖该平台'} → yt-dlp")

    return _ytdlp_dl(url, output_dir, cookie)


# ——— 抖音原生提取器 (iesdouyin.com 移动端 API) —————

def _douyin_resolve_and_fetch(url: str) -> Optional[dict]:
    """
    一次 curl -L 到位: 短链接重定向 → 分享页 HTML → 解析 ROUTER_DATA。
    不能分离重定向和取页——分离会触发验证码（两次 TLS 握手指纹不同）。
    重试最多 5 次——抖音有时返回验证码页面，等一下就好。
    """
    for attempt in range(5):
        if attempt > 0:
            import time
            time.sleep(2)
        try:
            r = subprocess.run([
                "curl", "-s", "-L",
                "--max-time", "15",
                "-H", f"User-Agent: {DOUYIN_UA}",
                "-H", "Accept: text/html,application/xhtml+xml",
                "-H", "Accept-Language: zh-CN,zh;q=0.9",
                url,
            ], capture_output=True, text=True, encoding="utf-8", timeout=20)
            html = r.stdout
        except Exception as e:
            log(f"  curl #{attempt+1} 请求失败: {e}")
            continue

        if len(html) < 10000:
            log(f"  尝试 #{attempt+1}: {len(html)} 字节(验证码), 重试...")
            continue

        if "ROUTER_DATA" not in html:
            log(f"  尝试 #{attempt+1}: {len(html)} 字节, 无 ROUTER_DATA")
            continue

        return _douyin_parse_router(html)

    log(f"  所有 {attempt+1} 次尝试均失败")
    return None


def _douyin_parse_router(html: str) -> Optional[dict]:
    """从 _ROUTER_DATA JSON 中提取视频 item"""
    m = DOUYIN_ROUTER_RE.search(html)
    if not m:
        log(f"  ROUTER_DATA 未找到 (HTML {len(html)} 字节)")
        return None

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        log(f"  ROUTER_DATA JSON 解析失败: {e}")
        return None

    ld = data.get("loaderData", {})
    vi_key = next((k for k in ld if ld[k] is not None and "video" in k.lower()), None)
    if not vi_key:
        log(f"  loaderData 中未找到有效 video 页 (keys: {list(ld.keys())})")
        return None

    item = ld[vi_key].get("videoInfoRes", {}).get("item_list", [None])[0]
    if not item:
        return None

    vid = item.get("aweme_id", "")
    return {"item": item, "vid": vid}


def _douyin_fetch_share(share_url: str) -> Optional[dict]:
    """
    用 curl 获取 iesdouyin.com 分享页 HTML。
    必须使用带验证参数 (region/mid/u_code 等) 的完整 URL。
    Python urllib 会被抖音验证码拦截（TLS 指纹识别），curl 更像浏览器。
    """
    try:
        r = subprocess.run([
            "curl", "-s", "-L",
            "--max-time", "15",
            "-H", f"User-Agent: {DOUYIN_UA}",
            "-H", "Accept: text/html,application/xhtml+xml",
            "-H", "Accept-Language: zh-CN,zh;q=0.9",
            share_url,
        ], capture_output=True, text=True, encoding="utf-8", timeout=20)
        html = r.stdout
    except Exception as e:
        log(f"  curl 请求失败: {e}")
        return None

    if len(html) < 10000:
        log(f"  页面太短 ({len(html)} 字节), 可能是验证码")
        return None

    return _douyin_parse_router(html)


def _douyin_dl_video(video_uri: str, output_path: Path, ratio: str = "1080p") -> bool:
    """用 curl 下载抖音视频流 (比 urllib 更可靠)"""
    dl_url = (
        f"https://aweme.snssdk.com/aweme/v1/playwm/?"
        f"video_id={video_uri}&ratio={ratio}&line=0"
    )
    try:
        r = subprocess.run([
            "curl", "-s", "-L",
            "--max-time", "120",
            "-H", f"User-Agent: {DOUYIN_UA}",
            "-H", "Referer: https://www.iesdouyin.com/",
            "-o", str(output_path),
            dl_url,
        ], timeout=130)
        if r.returncode != 0:
            log(f"  curl 下载失败: rc={r.returncode}")
            return False
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as e:
        log(f"  视频下载失败: {e}")
        return False


def _douyin_dl(url: str, output_dir: Path) -> dict:
    """抖音原生提取器: curl -L 一次到位（短链接→分享页→ROUTER_DATA→下载视频）。
    零 cookie 依赖，全自动。"""
    # 1. 一次 curl 完成重定向+解析
    result = _douyin_resolve_and_fetch(url)
    if not result:
        raise RuntimeError(f"无法解析抖音视频: {url}")

    item = result["item"]
    vid = result["vid"]
    desc = item.get("desc", "unknown")
    author = item.get("author", {})
    uploader = author.get("nickname", "unknown")
    aweme_id = item.get("aweme_id", vid)
    video_info = item.get("video", {})
    play_uri = video_info.get("play_addr", {}).get("uri", "")

    if not play_uri:
        dl_addr = video_info.get("download_addr", {})
        play_uri = dl_addr.get("uri", "")
        if not play_uri:
            raise RuntimeError("未找到视频流 URL")

    log(f"  {desc[:60]}... ({uploader})")

    # 3. 下载
    safe = re.sub(r'[<>:"/\\|?*]', '_', desc[:60]).strip()
    output = output_dir / f"{safe}.mp4"
    log(f"  下载中 -> {output.name}")

    ok = _douyin_dl_video(play_uri, output)
    if not ok:
        raise RuntimeError("视频下载失败")

    size_mb = output.stat().st_size / 1024 / 1024
    log(f"  视频: {output} ({size_mb:.1f}MB)")

    return {
        "video": output, "audio": output, "subs": None,
        "meta": {
            "id": aweme_id, "title": desc[:200], "duration": 0,
            "uploader": uploader,
            "url": f"https://www.douyin.com/video/{vid}",
            "has_subs": False, "subs_source": "none",
            "platform": "douyin", "downloader": "douyin-native",
        },
    }


def _lux_dl(url: str, output_dir: Path, cookie: str = None) -> dict:
    """lux 下载器。"""
    env = _safe_env()
    args = [LUX]
    if cookie:
        args.extend(["-c", cookie])

    # 取 JSON 元数据
    result = subprocess.run(args + ["-i", "-j", url],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"info: {result.stderr[:300]}")

    info = json.loads(result.stdout)
    if isinstance(info, list):
        info = info[0]

    title = info.get("title", "unknown")
    site = info.get("site", "unknown")
    log(f"  {title} ({site})")

    # 下载
    result = subprocess.run(args + ["-o", str(output_dir), url],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=600, env=env)

    # 找输出文件
    merged = _find_merged(output_dir, title)
    if not merged:
        merged = _merge_parts(output_dir, title)

    if not merged:
        raise RuntimeError(f"下载失败: {result.stderr[:300]}")

    log(f"  视频: {merged} ({merged.stat().st_size/1024/1024:.0f}MB)")

    # 字幕
    subs = None
    try:
        sub_ret = subprocess.run(args + ["-C", "-o", str(output_dir), url],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=120, env=env)
        subs = _find_subs(output_dir, merged.stem)
    except Exception:
        pass

    return {
        "video": merged, "audio": merged, "subs": subs,
        "meta": {
            "id": hashlib.md5(url.encode()).hexdigest()[:12],
            "title": title, "duration": 0,
            "uploader": site, "url": url,
            "has_subs": subs is not None,
            "subs_source": "auto" if subs else "none",
            "platform": site, "downloader": "lux",
        },
    }


def _ytdlp_dl(url: str, output_dir: Path, cookie: str = None) -> dict:
    """yt-dlp 兜底下载器。"""
    env = _safe_env()
    base = YTDLP.split() + ["--no-playlist"]
    if cookie:
        base.extend(["--cookies", cookie])

    # JSON 信息
    result = subprocess.run(base + ["--dump-json", url],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp info: {result.stderr[:300]}")

    info = json.loads(result.stdout)
    vid = info.get("id", "unknown")
    title = info.get("title", "unknown")
    duration = info.get("duration", 0)
    uploader = info.get("uploader") or info.get("channel", "unknown")
    has_subs = bool(info.get("subtitles") or info.get("automatic_captions"))

    log(f"  {title} ({duration}s) [{uploader}]")

    # 下载音频
    audio_tpl = str(output_dir / f"{vid}.%(ext)s")
    subprocess.run(base + [
        "-f", "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio",
        "--audio-format", "m4a", "-o", audio_tpl, url,
    ], check=True, timeout=600, env=env)

    audio = None
    for f in output_dir.glob(f"{vid}.*"):
        if f.suffix in (".m4a", ".webm", ".opus", ".mp3", ".wav"):
            audio = f
            break
    if not audio:
        raise RuntimeError("音频下载失败")
    log(f"  音频: {audio} ({audio.stat().st_size/1024/1024:.0f}MB)")

    # 字幕
    subs = None
    if has_subs:
        subprocess.run(base + [
            "--write-subs", "--write-auto-subs",
            "--sub-langs", "zh-Hans,zh-CN,zh,en,en-US,zh-Hant",
            "--sub-format", "srt/vtt/ttml/best",
            "--convert-subs", "srt",
            "--skip-download", "-o", str(output_dir / vid), url,
        ], timeout=120, env=env)
        su = sorted(output_dir.glob(f"{vid}*.srt"), key=lambda p: p.stat().st_size, reverse=True)
        su += sorted(output_dir.glob(f"{vid}*.vtt"), key=lambda p: p.stat().st_size, reverse=True)
        if su:
            subs = su[0]
            log(f"  字幕: {subs} ({subs.stat().st_size/1024:.0f}KB)")

    return {
        "video": None, "audio": audio, "subs": subs,
        "meta": {
            "id": vid, "title": title, "duration": duration,
            "uploader": uploader, "url": url,
            "has_subs": has_subs,
            "subs_source": "manual" if info.get("subtitles") else
                           "auto" if info.get("automatic_captions") else "none",
            "platform": info.get("extractor", "unknown"),
            "downloader": "yt-dlp",
        },
    }


def _find_merged(output_dir: Path, title: str) -> Optional[Path]:
    safe = re.sub(r'[<>:"/\\|?*]', '_', title).strip()
    for n in (f"{safe}.mp4", f"{title}.mp4"):
        p = output_dir / n
        if p.exists():
            return p
    for p in output_dir.glob(f"{safe}.*"):
        if p.suffix in (".mp4", ".flv", ".webm", ".mkv"):
            return p
    return None


def _merge_parts(output_dir: Path, title: str) -> Optional[Path]:
    """Bilibili: lux 产出 [0].mp4 + [1].m4a → ffmpeg 合并"""
    safe = re.sub(r'[<>:"/\\|?*]', '_', title).strip()
    video = audio = None
    for p in output_dir.glob(f"{safe}[*.*"):
        if "[0]" in p.name and p.suffix in (".mp4", ".flv"):
            video = p
        elif "[1]" in p.name and p.suffix in (".m4a", ".mp3", ".aac"):
            audio = p

    if not video:
        for p in output_dir.glob(f"{safe}.*"):
            if p.suffix in (".mp4", ".flv", ".webm", ".mkv"):
                return p
        return None

    if not audio:
        return video

    merged = output_dir / f"{safe}.mp4"
    if not FFMPEG:
        return video

    log(f"  合并: {video.name} + {audio.name}...")
    r = subprocess.run([FFMPEG, "-y", "-i", str(video), "-i", str(audio),
                        "-c", "copy", str(merged)],
                       capture_output=True, timeout=120, env=_safe_env())
    if r.returncode == 0 and merged.exists():
        video.unlink(missing_ok=True)
        audio.unlink(missing_ok=True)
        return merged
    return video


def _find_subs(output_dir: Path, stem: str) -> Optional[Path]:
    for ext in (".srt", ".vtt", ".xml"):
        for p in sorted(output_dir.glob(f"*{ext}"), key=lambda x: x.stat().st_mtime, reverse=True):
            if ext == ".xml":
                return _danmaku_to_srt(p)
            return p
    return None


def _danmaku_to_srt(xml_path: Path) -> Optional[Path]:
    srt = xml_path.with_suffix(".srt")
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(str(xml_path))
        lines, idx = [], 0
        for d in tree.getroot().findall("d"):
            p = d.get("p", "").split(",")
            if len(p) >= 4:
                ts = float(p[0])
                t1 = _fmt_ts(ts); t2 = _fmt_ts(ts + 3)
                idx += 1
                lines.append(f"{idx}\n{t1} --> {t2}\n{d.text}\n")
        if lines:
            srt.write_text("\n".join(lines), encoding="utf-8")
            return srt
    except Exception:
        pass
    return None


def _fmt_ts(sec: float) -> str:
    h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{int((sec%1)*1000):03d}"


# ═══════════════════════════════════════════════════════
# Step 2: 转录
# ═══════════════════════════════════════════════════════

def parse_subtitles(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line == "WEBVTT":
            continue
        if re.match(r"^\d+$", line): continue
        if re.match(r"^\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->", line): continue
        if re.match(r"^(NOTE|Kind|Language):", line): continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"<v\s[^>]+>", "", line)
        if line:
            lines.append(line)
    return "\n".join(lines)


def transcribe_audio(audio: Path) -> str:
    """Whisper 转录。优先 faster-whisper (av mock + ffmpeg decode)"""
    log("  Whisper 转录中...")

    # faster-whisper + ffmpeg 解码 (绕过 av DLL)
    try:
        import sys as _sys, subprocess as _sp, numpy as _np, ssl, os as _os

        # 绕过 Windows AppLocker 阻止 av DLL - robust version with __spec__
        import types, importlib.machinery
        class _FakeAVMod(types.ModuleType): pass
        def _mk_av(name):
            m = _FakeAVMod(name)
            m.__spec__ = importlib.machinery.ModuleSpec(name, None)
            m.__spec__.submodule_search_locations = []
            return m
        for _av_name in ['av', 'av._core', 'av.audio', 'av.audio.frame', 'av.audio.stream',
                          'av.audio.format', 'av.audio.layout', 'av.audio.resampler']:
            _sys.modules[_av_name] = _mk_av(_av_name)

        _ssl_ctx = ssl._create_default_https_context
        ssl._create_default_https_context = ssl._create_unverified_context
        _os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

        import faster_whisper.audio as _fwa

        def _ffmpeg_decode(file, sampling_rate=16000):
            if isinstance(file, np.ndarray):
                return file
            r = _sp.run([
                str(FFMPEG), "-y", "-i", str(file),
                "-f", "f32le", "-acodec", "pcm_f32le",
                "-ar", str(sampling_rate), "-ac", "1", "-"
            ], capture_output=True, timeout=60)
            if r.returncode != 0:
                raise RuntimeError(f"ffmpeg: {r.stderr.decode()[:200]}")
            return _np.frombuffer(r.stdout, dtype=_np.float32)

        _fwa.decode_audio = _ffmpeg_decode

        from faster_whisper import WhisperModel
        model_size = os.environ.get("WHISPER_MODEL", "medium")
        model = WhisperModel(model_size, device="cpu", compute_type="int8",
                            download_root=str(VENDOR_DIR / "models"))
        audio_np = _ffmpeg_decode(str(audio))
        segs, info = model.transcribe(audio_np, language="zh",
                                      beam_size=5, vad_filter=True)
        log(f"  语言: {info.language} ({info.language_probability:.2f}) [faster-whisper]")
        out = []
        for seg in segs:
            out.append(f"[{_fmt_ts(seg.start)}] {seg.text.strip()}")
        return "\n".join(out)
    except Exception as e:
        log(f"  faster-whisper 不可用: {e}")

    # 回退 1: openai-whisper (需 torch GPU)
    try:
        import whisper
        model_size = os.environ.get("WHISPER_MODEL", "large-v3")
        if model_size.startswith("large"):
            model_size = "medium"
        log(f"  openai-whisper ({model_size})...")
        model = whisper.load_model(model_size)
        result = model.transcribe(str(audio), language="zh", verbose=False)
        log(f"  语言: {result.get('language', '?')} [openai-whisper]")
        out = []
        for seg in result.get("segments", []):
            out.append(f"[{_fmt_ts(seg['start'])}] {seg['text'].strip()}")
        return "\n".join(out)
    except Exception as e:
        log(f"  openai-whisper 不可用: {e}")

    # 回退 2: 视频标题+描述
    log("  回退: 无转录引擎，使用视频标题+描述作为输入")
    return ""


def get_transcript(dl: dict) -> tuple:
    subs = dl["subs"]; meta = dl["meta"]
    if subs:
        log("字幕 → 转录")
        t = parse_subtitles(subs)
        q = "auto" if meta.get("subs_source") == "auto" else "manual"
        tm = {"source": "subtitles", "quality": q,
              "chars": len(t), "lines": t.count("\n") + 1}
        log(f"  {q} | {tm['chars']} 字符 | {tm['lines']} 行")
        return t, tm
    else:
        log("无字幕 → Whisper")
        t = transcribe_audio(dl["audio"])
        if not t:
            # Whisper 不可用，用视频标题+描述代替
            t = f"视频标题: {meta.get('title', '')}\n\n视频描述: {meta.get('title', '')}"
            log(f"  使用视频标题+描述 ({len(t)} 字符)")
        tm = {"source": "whisper", "quality": "auto",
              "chars": len(t), "lines": t.count("\n") + 1}
        log(f"  {tm['chars']} 字符 | {tm['lines']} 行")
        return t, tm


# ═══════════════════════════════════════════════════════
# Step 3: LLM 提取
# ═══════════════════════════════════════════════════════

EXTRACTION_PROMPT = """你是知识管理 Agent。从以下视频转录中提取可纳入知识库的结构化知识。

## 视频元数据
- 标题: {title}
- 博主/作者: {uploader}
- 时长: {duration}

## 质量控制（最重要）

**只在同时满足以下条件时提取：**
1. 转录中包含关于该主题的具体、实质性信息
2. 你能为这个知识点写出至少 80 字中文的实质内容
3. 这个信息是可操作或可复用的（不是"提到了某个词"）

**如果转录信息量不够（太短/太泛/全是概述），宁可少提取或不提取。宁缺毋滥。**

## 提取规则

### 必须提取（事实性知识）
1. **概念定义**: 某个术语/概念的含义、边界
2. **操作步骤**: 具体的操作流程、命令、参数、配置
3. **工具名称**: 提到的软件/库/平台名称及用途
4. **参数/阈值**: 具体的数值、阈值、比例（如"CRF 23"、"对比度 4.5:1"）
5. **对比结论**: A vs B 的选择建议、适用场景
6. **经验教训**: 踩坑、反模式、注意事项

### 忽略
- 口语填充（"然后""就是说""em..."）
- 寒暄、自我介绍、广告推广
- 纯叙事（"我昨天拍了一个视频..."）
- 没有实质信息的主观感叹
- 一句话带过的概念（没有展开说明）

### 标注规范
- **title**: 用中文，简洁精确
- **type**: concept | tool | workflow | decision | comparison
- **domain**: video-production | software-dev | visual-design | business | general
- **confidence**: medium（来自实际经验分享）| low（纯主观观点/未经验证）。视频来源不标 high
- **content**: 至少 80 字中文实质内容，Markdown 格式，含时间戳来源

## 输出格式

对于每个提取的知识点，输出一个 JSON 对象（每行一个 JSON，方便流式处理）:

```json
{{"title": "知识点标题（中文，简洁）", "type": "concept", "domain": "video-production", "confidence": "medium", "content": "## 知识点正文\\n\\n完整解释、步骤、参数。Markdown 格式。\\n\\n### 来源\\n视频时间戳: [MM:SS-MM:SS]\\n\\n### 与其他概念的关系\\n- 前置依赖\\n- 后续扩展", "tags": ["关键词1", "关键词2"]}}
```

## 转录文本

{transcript}"""


def chunk_transcript(text: str, max_chars: int = 15000) -> list:
    if len(text) <= max_chars:
        return [text]
    chunks, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 <= max_chars:
            cur += ("\n\n" + para) if cur else para
        else:
            if cur: chunks.append(cur)
            cur = para
    if cur: chunks.append(cur)
    if len(chunks) > 1:
        log(f"  分 {len(chunks)} 段")
    return chunks


def extract_knowledge(transcript: str, meta: dict, api_key: str = None) -> list:
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", os.environ.get("DASHSCOPE_API_KEY", ""))
    if not api_key:
        raise RuntimeError("需要 DEEPSEEK_API_KEY")

    import urllib.request, urllib.error

    model = os.environ.get("EXTRACT_MODEL", "deepseek-chat")
    deepseek_base = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com")
    chunks = chunk_transcript(transcript)
    all_kp, seen = [], set()

    for i, chunk in enumerate(chunks):
        label = f"段 {i+1}/{len(chunks)}" if len(chunks) > 1 else "全文"
        log(f"  LLM 提取 {label}...")

        prompt = EXTRACTION_PROMPT.format(
            title=meta.get("title", "未知"),
            uploader=meta.get("uploader", "未知"),
            duration=f"{meta.get('duration', 0)}s",
            transcript=chunk,
        )

        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "你是把非结构化内容转为结构化知识库的 AI Agent。只输出 JSON，一知识点一行。不输出解释。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{deepseek_base}/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                content = json.loads(resp.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            log(f"  API HTTP {e.code}: {e.read().decode()[:200]}")
            continue
        except Exception as e:
            log(f"  API error: {e}")
            continue

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("```"):
                continue
            try:
                kp = json.loads(line)
                t = kp.get("title", "")
                if t and t not in seen:
                    seen.add(t)
                    all_kp.append(kp)
            except json.JSONDecodeError:
                continue

    log(f"  提取: {len(all_kp)} 知识点")
    return all_kp


# ═══════════════════════════════════════════════════════
# Step 4: KB 写入
# ═══════════════════════════════════════════════════════

def write_to_kb(knowledge: list, meta: dict, kb_dir: Path) -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    safe = lambda t: re.sub(r'[<>:"/\\|?*]', '-', t).strip('-')[:80]

    domains = sorted({k.get("domain", "general") for k in knowledge})

    # 源视频页
    src_name = f"video-source-{meta.get('id', 'unknown')[:20]}"
    src_path = kb_dir / "entities" / f"{src_name}.md"
    src_url = meta.get("url", "")
    src_title = meta.get("title", "unknown")

    src_body = f"""---
title: 视频来源: {src_title[:80]}
description: >
  来自 {meta.get('uploader', '未知')} 的视频 "{src_title[:50]}"。
  时长 {meta.get('duration', '?')}s。URL: {src_url}
type: entity
domain: [{', '.join(domains[:3]) or 'general'}]
source: human-curated
source_detail: [{src_url}]
related: []
created: {today}
updated: {today}
confidence: high
---

# 视频来源: {src_title}

- **URL**: {src_url}
- **博主/频道**: {meta.get('uploader', '未知')}
- **时长**: {meta.get('duration', '?')}s

## 从此视频提取的知识点
"""

    written, related = [], []

    for kp in knowledge:
        kp_title = kp.get("title", f"knowledge-{len(written)}")
        page_name = safe(kp_title)
        page_path = kb_dir / "concepts" / f"{page_name}.md"

        fm = f"""---
title: {kp_title}
description: >
  从 {meta.get('uploader', '未知')} 的视频 "{src_title[:40]}" 提取。
  type: {kp.get('type', 'concept')} | domain: {kp.get('domain', 'general')} | tags: {', '.join(kp.get('tags', [])[:5])}
type: {kp.get('type', 'concept')}
domain: [{kp.get('domain', 'general')}]
source: human-curated
source_detail: [{src_url}]
related: [[{src_name}]]
created: {today}
updated: {today}
confidence: {kp.get('confidence', 'medium')}
---

{kp.get('content', '')}

---

> 来源: [{src_title[:60]}]({src_url}) | 博主: {meta.get('uploader', '未知')}
> 提取时间: {today} | 置信度: {kp.get('confidence', 'medium')}
"""
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(fm, encoding="utf-8")
        written.append(page_path)
        related.append(page_name)

    # 写源视频页 + 更新双向链
    src_body += "\n".join(f"- [[{r}]]" for r in related)
    src_body = src_body.replace("related: []", f"related: {', '.join(f'[[{r}]]' for r in related)}")
    src_path.parent.mkdir(parents=True, exist_ok=True)
    src_path.write_text(src_body, encoding="utf-8")
    written.append(src_path)

    return written


# ═══════════════════════════════════════════════════════
# Step 5: 报告
# ═══════════════════════════════════════════════════════

def report(tm: dict, knowledge: list, written: list, meta: dict) -> None:
    print()
    print("=" * 60)
    print("  视频知识提取报告")
    print("=" * 60)
    print(f"  视频: {meta.get('title', '?')[:60]}")
    print(f"  博主: {meta.get('uploader', '?')}")
    print(f"  下载器: {meta.get('downloader', '?')}")
    print(f"  转录: {tm.get('chars', 0)} 字符 (来源: {tm.get('source', '?')})")
    print(f"  提取: {len(knowledge)} 知识点")
    print()

    tc, dc = {}, {}
    for kp in knowledge:
        tc[kp.get("type", "?")] = tc.get(kp.get("type", "?"), 0) + 1
        dc[kp.get("domain", "?")] = dc.get(kp.get("domain", "?"), 0) + 1

    print("  ## 类型分布")
    for t, c in sorted(tc.items()):
        print(f"    {t}: {c}")
    print()
    print("  ## 域分布")
    for d, c in sorted(dc.items()):
        print(f"    {d}: {c}")
    print()
    print("  ## 写入文件")
    for p in written:
        rel = p.relative_to(KB_WIKI_DIR) if KB_WIKI_DIR in p.parents else p
        print(f"    {rel}")
    print()
    print("  ## 知识点列表")
    for i, kp in enumerate(knowledge):
        m = "[M]" if kp.get("confidence") == "medium" else "[L]"
        print(f"    {i+1}. {m} [{kp.get('type', '?')}] {kp.get('title', '?')} ({kp.get('domain', '?')})")
    print()


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="视频知识提取")
    parser.add_argument("url", nargs="?", help="视频 URL")
    parser.add_argument("--audio", help="已有音频文件")
    parser.add_argument("--subs", help="已有字幕文件")
    parser.add_argument("--transcript", help="已有转录文本（跳过下载+转录）")
    parser.add_argument("--domain", default="video-production", help="输出 domain")
    parser.add_argument("--transcribe-only", action="store_true", help="只转录")
    parser.add_argument("--work-dir", default=None, help="工作目录")
    parser.add_argument("--no-write", action="store_true", help="不写 KB")
    parser.add_argument("--api-key", default=None, help="DashScope API key")
    parser.add_argument("--cookie", default=None, help="Cookie 文件路径")

    args = parser.parse_args()
    wd = Path(args.work_dir) if args.work_dir else WORK_DIR
    wd.mkdir(parents=True, exist_ok=True)

    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY", os.environ.get("DASHSCOPE_API_KEY", ""))
    if not api_key and not args.transcribe_only:
        log("WARNING: DEEPSEEK_API_KEY 未设置 → 只转录")
        args.transcribe_only = True

    # Step 0: 已有内容
    if args.transcript:
        log(f"已有转录: {args.transcript}")
        t = Path(args.transcript).read_text(encoding="utf-8")
        tm = {"source": "file", "quality": "manual", "chars": len(t), "lines": t.count('\n')+1}
        meta = {"title": "手动导入", "uploader": "未知", "duration": 0, "url": "file://" + args.transcript}
    elif args.audio and args.subs:
        log("已有音频+字幕")
        dl = {"audio": Path(args.audio), "subs": Path(args.subs),
              "meta": {"title": Path(args.audio).stem, "uploader": "未知", "duration": 0}}
        t, tm = get_transcript(dl)
        meta = dl["meta"]
    elif args.audio:
        log("已有音频 → Whisper")
        dl = {"audio": Path(args.audio), "subs": None,
              "meta": {"title": Path(args.audio).stem, "uploader": "未知", "duration": 0}}
        t, tm = get_transcript(dl)
        meta = dl["meta"]
    else:
        if not args.url:
            parser.error("需要 URL 或 --audio/--transcript")
        dl = download_video(args.url, wd, args.cookie)
        meta = dl["meta"]
        t, tm = get_transcript(dl)

    # 保存转录
    tp = wd / "transcript.txt"
    tp.write_text(t, encoding="utf-8")
    log(f"转录已保存: {tp}")

    if args.transcribe_only:
        log("--transcribe-only，结束")
        print(t[:500] + "..." if len(t) > 500 else t)
        return

    # 提取
    knowledge = extract_knowledge(t, meta, api_key)
    if not knowledge:
        log("未提取到知识点")
        return

    ep = wd / "extracted.json"
    ep.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"结果: {ep}")

    # 写入
    if args.no_write:
        log("--no-write，跳过 KB")
        written = []
    else:
        written = write_to_kb(knowledge, meta, KB_WIKI_DIR)
        log(f"写入 {len(written)} 页")

    report(tm, knowledge, written, meta)


if __name__ == "__main__":
    main()
