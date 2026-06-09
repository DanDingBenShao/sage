# Sage Video Analysis Pipeline

一键提取抖音/抖音/B站视频的知识点到知识库。

## 安装

### 1. Python 环境
```bash
pip install faster-whisper ctranslate2 requests yt-dlp numpy huggingface_hub
```

### 2. ffmpeg (必须)
- 下载: https://ffmpeg.org/download.html
- 放 `vendor/bin/ffmpeg.exe`，或系统 PATH 里

### 3. lux (可选, B站/YouTube 下载)
- 下载: https://github.com/iawia002/lux/releases
- 放 `vendor/bin/lux.exe`

### 4. Whisper 模型 (首次运行自动下载)
```bash
# 设置 HF 镜像 (国内)
export HF_ENDPOINT=https://hf-mirror.com
```
首次运行会自动下载 medium 模型 (~1.5GB) 到 `vendor/models/`。

### 5. API Key
```bash
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## 使用

```bash
# 抖音 (全自动，零 cookie)
python scripts/_extract_douyin.py https://v.douyin.com/xxxxx

# 其他平台 (B站/YouTube/本地)
python scripts/extract.py https://www.bilibili.com/video/BVxxxx

# 指定知识域 + 跳过人工审核
python scripts/_extract_douyin.py https://v.douyin.com/xxxxx --domain software-dev --no-review
```

## Skill 安装 (Claude Code)

把 `skills/video-analysis.md` 放到:
```
C:\Users\<用户名>\.claude\skills\video-analysis\SKILL.md
```

然后就可以用 `/video-analysis extract <url>` 了。

## 路径配置

首次运行时编辑目标路径:
```python
# scripts/_extract_douyin.py 里的默认路径
OUT_DIR = Path("D:/subject/sage/output/extract")   # 输出目录
KB_DIR = Path("D:/AI/projects/knowledge-base/wiki")  # 知识库目录
FFMPEG = "ffmpeg"  # 如果在 PATH 里
MODEL_DIR = Path("D:/subject/sage/vendor/models")    # 模型缓存
```

## 已知问题

1. Windows 可能阻止 av DLL → 脚本已内置绕过 (mock av + ffmpeg subprocess)
2. 需要 ssl._create_unverified_context (沙箱/国内网络环境)
3. yt-dlp 抖音需 cookie → 已用 iesdouyin API 原生提取代替
