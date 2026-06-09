# Sage — AI 知识库系统

> 视频分析 + 知识提取 + 递归完备化。CLAUDE.md for agent。

## 路径

```
项目根:    D:/TOOLS/cloude code/sage
vendor:    D:/TOOLS/cloude code/sage/vendor/bin/   (lux, ffmpeg)
models:    D:/TOOLS/cloude code/sage/vendor/models/ (whisper)
输出:      D:/TOOLS/cloude code/sage/output/extract/
知识库:    D:/TOOLS/cloude code/sage/kb/wiki/
skills:    C:/Users/16535/.claude/skills/video-analysis/SKILL.md
           C:/Users/16535/.claude/skills/knowledge-base/SKILL.md
```

## Python 环境

```bash
# 主 Python (GPT-SoVITS runtime, 3.9.13, faster-whisper/numpy/requests installed)
D:/TOOLS/GPT-SoVITS-v2pro-20250604/runtime/python.exe

# 备用 Python (ComfyUI, 3.11.9)
D:/TOOLS/ComfyUI-aki-v1.7/python/python.exe
```

## 环境变量

```bash
# 文本提取 (知识提取)
export DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 视频视觉分析 (VL, Layer 3) — 用便宜模型
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export VL_MODEL=qwen3-vl-flash

export HF_ENDPOINT=https://hf-mirror.com
export PYTHONPATH=D:/TOOLS/cloude code/sage/vendor
```

## 核心脚本

| 脚本 | 用途 |
|------|------|
| `scripts/_extract_douyin.py` | 抖音全自动提取 (零cookie) |
| `scripts/extract.py` | 通用提取管线 (三引擎: douyin-native/lux/yt-dlp) |

## 已知问题

1. av DLL 可能被 Windows 阻止 → `_extract_douyin.py` 已内置 ffmpeg subprocess 绕过
2. huggingface SSL → 需 `HF_ENDPOINT=hf-mirror.com`
3. yt-dlp 抖音需 cookie → 用 iesdouyin API 原生提取代替

## 模型策略

| 用途 | API | 模型 | 费用 |
|------|-----|------|------|
| 转录→知识提取 | DeepSeek | `deepseek-chat` (V4 Flash) | 极低 |
| 视频画面分析 (VL) | DashScope | `qwen3-vl-flash` | 极低 ($0.05/$0.40 per 1M) |
| 语音转录 | 本地 | faster-whisper medium | 免费 |

### VL 模型选择依据 (DashScope 全线对比)

| 模型 | 输入/输出 $/1M | 适用场景 |
|------|---------------|----------|
| **qwen3-vl-flash** ← 默认 | **0.05 / 0.40** | 视频画面分析，1h视频，262K上下文，时序定位 |
| qwen3-vl-32b-instruct | 0.16 / 0.64 | 需要更强推理时备选 |
| qwen-vl-plus | 0.21 / 0.63 | 旧版性价比之选 (兼容) |
| qwen-vl-max | 0.80 / 3.20 | 旧版旗舰，太贵不推荐 |
| qwen3-vl-235b-a22b | 0.40 / 1.60 | 235B 超大模型，非必要不用 |

> `qwen3-vl-flash` 输入价格是 `qwen-vl-max` 的 **1/16**，输出是 **1/8**，且专门为视频理解优化。

## 工具链

```
/bin/bash (mingw64)     shell
curl                    HTTP 请求
ffmpeg                   音频/视频处理
lux (vendor/bin)        B站/YouTube 下载
yt-dlp (pip)            通用下载兜底
faster-whisper (pip)    语音转录
DeepSeek V4 Flash       LLM 文本提取
Qwen-VL (DashScope)     VL 视频画面分析
```
