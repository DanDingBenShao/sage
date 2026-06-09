---
name: video-analysis
description: >
  视频分析 Agent。核心是量化——把视觉/听觉/节奏的"感觉"翻译成可对比的数字。
  一条管线四个层（元数据→量化指标→VL定性→对标），三个出口（质检/逆向配方/知识提取）。
  触发：需要审查视频质量、逆向学习博主制作手法、从视频中提取知识。
argument-hint: "[qa|learn|extract] <输入>"
allowed-tools: [Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep, Agent]
---

# Video Analysis Agent

你不是"让 VL 模型看视频然后写感想"的 Agent。你的核心竞争力是 **量化**——

- 量化能回答的事，不问 VL 模型
- VL 只做它擅长的事：叙事判断、整体感觉、最差段落定位
- 数字积累成历史画像，跑得越多越有价值

## 前置加载

```
1. 本文件 SKILL.md
2. 检查 DASHSCOPE_API_KEY（未设置则用用户提供的 key）
3. D:/TOOLS/cloude code/sage/kb/wiki/（知识库——extract 写入，qa/learn 读历史数据对标）
```

## 工具链

| 工具 | 做什么 | 为什么不是 VL |
|------|--------|-------------|
| `ffprobe` | 编码/分辨率/帧率/码率/时长/音轨 | 客观事实，不需要 AI 猜 |
| `ffmpeg scdet` | 场景切换检测 → 切镜时间戳列表 | 精确到帧，VL 只能估计 |
| `ffmpeg loudnorm` | EBU R128 积分响度/真峰值/响度范围 | 广播标准，有明确阈值 |
| `librosa` | BPM 检测 | VL 做不了节拍检测 |
| OpenCV / Pillow | 色相直方图/饱和度均值+方差/主体边界框 | 像素级精度，VL 给你形容词 |
| `video_qa.py` | VL 模型看视频做定性判断 | 叙事/感觉——只有它能做 |
| `yt-dlp` | 下载视频+字幕（extract/learn） | — |
| `whisper` (faster-whisper) | 本地语音转文字（无字幕时 fallback）| — |
| `extract.py` | extract 管线自动化（下载→转录→LLM→KB）| — |

---

## 核心管线

```
视频输入（本地文件 或 URL → yt-dlp 下载）
  │
  ├── Layer 1: 元数据 ──────────────────────────────────────────
  │   ffprobe 一键提取
  │   编码 / 分辨率 / 帧率 / 码率 / 时长 / 音轨格式 / 采样率
  │
  ├── Layer 2: 量化指标 ────────────────────────────────────────
  │   画面: 色相分布 / 饱和度 / 亮度曲线 / 场景检测 → 切频
  │   音频: LUFS / true peak / 响度范围 / BPM
  │   字幕: 位置 y 分布 / 字号-分辨率比 / 对比度（WCAG）
  │   → 输出: metrics.json（纯数字，可版本对比）
  │
  ├── Layer 3: VL 定性 ─────────────────────────────────────────
  │   只问 VL 擅长的问题:
  │     · 整体感觉（第一印象）
  │     · 叙事质量（结构清晰/拖沓/跳跃）
  │     · 最好的段落和最差的段落（时间+理由）
  │     · 量化检测不到的事（情绪/氛围/专业感）
  │   → 量化数据同时传给 VL 做参考——VL 知道切频 0.4cut/s
  │     就不会说"节奏很快"
  │
  └── Layer 4: 对标 ───────────────────────────────────────────
      对比什么:
        · 用户的风格画像（历史快照的分布区间）
        · 同类参考视频（learn 时保存的配方数据）
        · 平台/类型的通用基准
      输出: 偏差报告——"你的切频在你自己历史的 P25，
             参考视频中位数是 P60"
  │
  ├── 出口 A: 质检报告 ── 自己的视频 vs 自己的标准
  ├── 出口 B: 逆向配方 ── 别人的视频 → 可量化的制作参数
  └── 出口 C: 知识提取 ── 音频转文字 → LLM 提取 → KB
```

---

## Layer 1: 元数据

```bash
ffprobe -v quiet -print_format json -show_format -show_streams <video>
```

提取：

| 字段 | 来源 | 例 |
|------|------|-----|
| 时长 | format.duration | 347.2s |
| 分辨率 | streams[0].width × height | 1920×1080 |
| 帧率 | streams[0].r_frame_rate | 30/1 |
| 编码 | streams[0].codec_name | h264 |
| 码率 | format.bit_rate | 5.2Mbps |
| 音频编码 | streams[1].codec_name | aac |
| 音频采样率 | streams[1].sample_rate | 48000 |
| 文件大小 | format.size | 218MB |

---

## Layer 2: 量化指标

### 2.1 切镜检测（ffmpeg scdet）

```bash
ffmpeg -nostats -i <video> \
  -vf "scdet=threshold=0.4" \
  -f null /dev/null 2>&1 | grep 'lavfi\.scd' > scdet.log
```

`scdet.log` 每行一个检测到的切镜时间戳（精确到帧）。

从时间戳序列计算：

| 指标 | 算法 | 意义 |
|------|------|------|
| 切镜次数 | count(timestamps) | 总镜头数 |
| 平均切频 | 次数 / 时长 | 0.2=慢 0.5=正常 1.0+ =快 |
| 切频变异系数 | std(间隔序列)/mean | 节奏是否有起伏，太低 = 机械 |
| 最长单镜 | max(间隔) | >15s 可能拖沓 |
| 最短单镜 | min(间隔) | <0.3s 可能是跳帧/闪黑 |

### 2.2 响度（EBU R128）

```bash
ffmpeg -nostats -i <video> \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" \
  -f null /dev/null 2>&1
```

| 指标 | 标准 | 阈值 |
|------|------|------|
| integrated_loudness | 平台相关 | YouTube=-14, 广播=-23, 抖音≈-14 |
| true_peak | <-1dBTP | ≥0dBTP = 爆音 |
| loudness_range | 5-15 LU | <3=平淡 >20=吓人 |

### 2.3 BPM（librosa）

```python
import librosa
import soundfile as sf

y, sr = sf.read('audio_extracted.wav')
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

# 卡点精度：每个切镜时间戳距离最近 beat 的偏移
def beat_alignment_score(cut_timestamps_sec, beats, sr):
    beat_sec = librosa.frames_to_time(beats, sr=sr)
    offsets = []
    for cut in cut_timestamps_sec:
        nearest_beat = min(beat_sec, key=lambda b: abs(b - cut))
        offsets.append(abs(cut - nearest_beat) * 1000)  # ms
    return {
        'mean_offset_ms': sum(offsets)/len(offsets),
        'pct_within_50ms': sum(1 for o in offsets if o < 50) / len(offsets) * 100
    }
```

| 指标 | 意义 |
|------|------|
| 平均偏移 | <50ms=精确卡点 50-100ms=基本对齐 >200ms=不卡 |
| 卡点率 | 切镜中 <50ms 偏移的比例 |

### 2.4 色彩

```python
from PIL import Image
from collections import Counter

# 采样——每秒 1 帧足够
img = Image.open('frame.jpg').convert('HSV')
h, s, v = img.split()
h_data = list(h.getdata())
s_data = list(s.getdata())
v_data = list(v.getdata())

# 主色（色相峰值）
h_counter = Counter(h_data)
top_hues = h_counter.most_common(3)  # 主色/辅色/强调色

sat_mean = sum(s_data) / len(s_data)
sat_var = sum((x - sat_mean)**2 for x in s_data) / len(s_data)

# 亮度分位数
v_sorted = sorted(v_data)
p10, p50, p90 = v_sorted[len(v_data)//10], v_sorted[len(v_data)//2], v_sorted[len(v_data)*9//10]
```

| 指标 | 意义 |
|------|------|
| 主色-辅色色相差 | ~180°=互补 ~30°=类似 |
| 饱和度均值 | <10%=近乎黑白 >80%=过度饱和 |
| 饱和度方差 | 高=局部鲜艳局部灰——不协调 |
| 亮度 P10/P90 | P10<10=死黑 P90>245=过曝 |

### 2.5 字幕（OCR + 分析）

如果视频有内嵌字幕（非独立 srt 文件），需要 OCR 提取位置信息。

有独立 srt 或 ass 文件则直接从文件中读取样式。

| 指标 | 算法 | 标准 |
|------|------|------|
| y 位置均值 | OCR bbox y 坐标统计 | 1080p: y=850-980（Lower Third） |
| 字号 | OCR bbox 高度 | ≥2% 分辨率高度 |
| 对比度 | WCAG 算法：前景/背景亮度比 | ≥4.5:1（AA 级） |
| 出现时长 | 每条字幕持续时间 | 中文: 每字 0.15-0.3s |

### 输出格式：metrics.json

```json
{
  "video": {"file": "...", "duration_s": 347.2, "resolution": "1920x1080", "fps": 30},
  "cuts": {"count": 178, "avg_freq": 0.51, "freq_std": 0.23, "max_interval_s": 12.4, "min_interval_s": 0.4},
  "audio": {"integrated_lufs": -15.8, "true_peak_dbtp": -2.1, "loudness_range_lu": 7.2},
  "bpm": {"tempo": 124.5, "beat_alignment_mean_ms": 68, "beat_alignment_pct_50ms": 42.3},
  "color": {
    "top_hues": [12, 198, 45],
    "sat_mean": 38.5,
    "sat_var": 142.0,
    "v_p10": 18, "v_p50": 128, "v_p90": 232
  },
  "subtitle": {"y_mean": 902, "font_height_pct": 2.8, "contrast_ratio": 5.2}
}
```

---

## Layer 3: VL 定性

传给 VL 模型时不只传视频——**同时传量化摘要**，让 VL 在数据基础上做判断而非凭空猜测。

```python
from video_qa import qa_video

prompt = f"""你是视频质量分析专家。以下是你已知的量化数据：

## 量化指标
- 切镜频率: {metrics['cuts']['avg_freq']:.2f} cuts/s（行业参考: 0.3-0.6 教程, 0.8-1.5 MV）
- 最长单镜: {metrics['cuts']['max_interval_s']:.1f}s
- 响度: {metrics['audio']['integrated_lufs']:.1f} LUFS
- 真峰值: {metrics['audio']['true_peak_dbtp']:.1f} dBTP
- 卡点精度: {metrics['bpm']['beat_alignment_mean_ms']:.0f}ms 平均偏移
- 主色: H={metrics['color']['top_hues'][0]}°, 饱和度: {metrics['color']['sat_mean']:.1f}%
- 字幕对比度: {metrics['subtitle']['contrast_ratio']:.1f}:1

## 你需要回答（不要重复数字，用你的视觉感知补充判断）

1. **整体感觉**: 这个视频看完的第一印象？什么感觉？
2. **叙事质量**: 结构是否流畅？有没有拖沓或跳跃的段落？时间点+理由
3. **最好的段落**: 哪段最精彩？（时间+为什么）和量化数据吻合吗？
4. **最差的段落**: 哪段可以改进？（时间+为什么）量化数据有没有线索？
5. **画面专业感**: 视觉语言是否统一？有没有跳色/构图问题？
6. **如果只能改一件事**: 你最建议改什么？

输出 markdown 报告，不要重复量化数据——补充数据告诉不了我的东西。"""

report = qa_video(video_path, storyboard_json=[], work_dir=work_dir,
                  custom_prompt=prompt)
```

> **需要改造 `video_qa.py`**：`qa_video()` 函数增加 `custom_prompt` 参数，允许调用方传入 prompt 替换默认的工程向检查清单。

### VL 模型的能力边界

| ✅ 让 VL 做 | ❌ 别让 VL 做 |
|------------|-------------|
| 整体感觉 / 第一印象 | 切镜频率（scdet 更准）|
| 叙事结构是否流畅 | 响度 LUFS（loudnorm 更准）|
| 最差/最好段落定位 | 色彩饱和度（HSV 直方图更准）|
| 画面统一感 / 跳色 | BPM（librosa 更准）|
| 情绪传达 | 字幕对比度（WCAG 算法更准）|
| 专业感判断 | "这个画面好不好看"（量化+对标更可靠） |

---

## Layer 4: 对标

### 4.1 风格画像（用户自己的历史数据）

每次 qa 产出 `metrics.json`，存入 `D:/TOOLS/cloude code/sage/kb/wiki/data/video-qa/`。

积累 N 次后构建画像：

```
## 你的视频风格画像（N=12）

| 指标 | P25 | P50 | P75 | 趋势 |
|------|-----|-----|-----|------|
| 切频 | 0.38 | 0.52 | 0.61 | ↗ 近 5 期上升 |
| LUFS | -17.2 | -15.8 | -14.3 | → 稳定 |
| 卡点精度 | 28ms | 52ms | 78ms | ↗ 近 3 期明显改善 |
| 饱和度 | 41% | 47% | 55% | → 稳定 |
| 字幕对比度 | 3.8 | 5.1 | 6.2 | ↘ 近 2 期偏弱 |

本次视频各项指标在画像中的位置 → 偏差报告
```

### 4.2 参考视频对标（learn 时积累的配方数据）

learn 分析过的博主视频 → 其 `metrics.json` 作为参考基线。

```
本次 vs 参考「<博主名>-<视频标题>」

| 指标 | 你 | 参考 | 偏差 |
|------|-----|------|------|
| 切频 | 0.51 | 0.78 | ⬇️ 慢了 35% |
| 卡点精度 | 68ms | 28ms | ⬆️ 差 40ms |

你的节奏显著慢于参考——如果目标是这个风格，建议提高切频。
```

### 4.3 平台通用基准

| 平台 | 时长 | 典型切频 | 典型 LUFS |
|------|------|---------|----------|
| B 站知识科普 | 5-20min | 0.3-0.6 | -16 to -14 |
| B 站 vlog | 3-10min | 0.5-1.0 | -16 to -14 |
| 抖音/短视频 | <3min | 1.0-2.5 | -14 to -12 |
| YouTube 教程 | 5-30min | 0.2-0.5 | -14 to -13 |

---

## 命令 1: qa — 视频质检

```
/video-analysis qa <video_path> [--compare <reference_video_or_metrics>]
```

### 步骤

1. 跑 Layer 1（ffprobe）→ 元数据表
2. 跑 Layer 2（scdet + loudnorm + librosa + 色彩）→ `metrics.json`
3. **读取审美标准**：从 KB 检索用户定义的审美标准
   ```bash
   # 用 knowledge-base ask 检索审美相关页面
   /knowledge-base ask "视频质量标准 审美 字幕 色彩 节奏"
   ```
   读入 KB 中已有的审美规范页面（如字幕设计规范、色彩搭配、节奏标准等）。
   如果没有——跳过，仅用量化数据对标。

4. 跑 Layer 4 对标：
   - 如果用户风格画像存在 → 对比本次 vs 历史
   - 如果 `--compare` 指定了参考 → 对比本次 vs 参考
5. 跑 Layer 3（VL 模型）→ 传入量化数据 + 对标结果 + 审美标准 → VL 补充定性判断

   ```python
   from video_qa import qa_video
   
   # video_qa.py v2 支持三个新参数
   report = qa_video(
       video_path,
       storyboard_json=[],
       work_dir=work_dir,
       metrics_json=metrics,           # Layer 2 量化数据
       aesthetic_standards=kb_standards,  # 从 KB 读入的审美标准
       # custom_prompt 不传——用默认 prompt（已自动拼装上述数据）
   )
   ```
   
   > **`video_qa.py` v2 改动**：`qa_video()` 新增 `custom_prompt`（完全替换默认 prompt）、`metrics_json`（量化数据自动注入）、`aesthetic_standards`（审美标准自动注入）三个参数。重试策略从统一 `sleep(2)` 改为：429 等 Retry-After / 4xx 不重试 / 5xx 指数退避。大文件 >200MB 打印警告。

6. 合并输出完整质检报告
7. 将 `metrics.json` 存入历史目录（积累画像）
8. 报告：哪些指标偏离画像？哪些趋势需要注意？

### VL 收到的 prompt 结构

当 `custom_prompt` 不传时，`_build_default_qa_prompt()` 自动拼装：

```
1. 你是视频质量审查专家。请观看以下视频...
2. ## 分镜脚本摘要
3. ## 已知量化数据（无需重复这些数字——用你的视觉感知验证和补充）
   | 维度 | 本次 | 行业参考 |
   ...
4. ## 参考审美标准（从 KB 读入）
5. ## 检查维度 (7 项逐项检查 + 输出格式)
```

> **设计意图**：量化数据让 VL 在判断前已经知道数字——它不会说"节奏很快"当 scdet 显示 0.4 cut/s。审美标准让 VL 不是凭个人口味评价，而是"对比你声明的标准，偏离了哪里"。

### 输出格式

```markdown
# 视频质检报告
**文件**: xxx.mp4 | **时长**: 5:47

## 📊 量化指标
| 维度 | 本次 | 你的画像(P50) | 参考 | 判定 |
|------|------|-------------|------|------|
| 切频 | 0.51 | 0.52 | 0.78 | ✅ 正常 |
| LUFS | -15.8 | -15.8 | - | ✅ 正常 |
| 卡点 | 68ms | 52ms | 28ms | ⚠️ 偏弱 |
| 字幕对比度 | 5.1 | 5.1 | - | ✅ |
| 饱和度 | 47% | 47% | - | ✅ |

## 🎯 VL 定性
<Layer 3 输出——感觉/叙事/最好段落/最差段落>

## 🔧 优先修改
1. ...
2. ...
```

---

## 命令 2: learn — 视频制作方式逆向

```
/video-analysis learn <video_url>
```

### 步骤

1. 下载视频（yt-dlp）
2. 跑 Layer 1 + Layer 2 → `metrics.json`（量化数据是配方的核心）
3. 如果有字幕/转录 → 提取文案（Pass 5 备用）
4. 跑 Layer 3 — 5 个独立 Pass，每个聚焦一个维度。每 Pass 调用一次 `video_qa.qa_video()`，
   用 `custom_prompt` 传入该 Pass 专属的问题 + 相关量化数据。

   **关键原则**：每个 Pass 的 prompt 都先告诉 VL 已知的量化数字，然后只问 VL 能回答的问题。
   VL 回答不了的问题（字体名称、软件名称、精确参数）改用描述性语言——"什么风格""什么效果""什么复杂度"。

   ### Pass 1: 叙事结构

   ```python
   prompt = f"""你是视频叙事分析专家。观看这个视频，分析它的叙事结构。

   ## 已知量化数据
   - 总时长: {metrics['video']['duration_s']:.0f}s
   - 切镜次数: {metrics['cuts']['count']} 次
   - 平均切频: {metrics['cuts']['avg_freq']:.2f} cuts/s

   ## 你需要回答（只答你能感知的，不要猜数字）

   1. **钩子（前 5-15 秒）**: 视频用什么手法抓注意力？是抛出问题、展示结果、制造悬念还是其他？
      这个钩子在你看来效果如何——想继续看下去吗？

   2. **分段结构**: 视频可以分成几个大段？每段的核心主题是什么？
      用时间戳标注：`[MM:SS-MM:SS] 段名 — 主题`

   3. **转折/高潮**: 叙事中有没有明显的转折点或情绪高潮？在哪个时间点？
      这个转折是依靠画面变化还是旁白推进？

   4. **结尾方式**: 结尾怎么收的？是总结、号召行动、留悬念还是自然淡出？
      结尾的时长占比合理吗？（参考：<5% 可能草率，>15% 可能拖沓）

   5. **节奏感知**: 结合已知切频 {metrics['cuts']['avg_freq']:.2f} cuts/s——
      你的视觉感受和这个数字吻合吗？有没有某段感觉"太快"或"太慢"但数字没反映出来的？

   输出 markdown，每部分一个小标题。"""
   ```

   ### Pass 2: 视觉风格

   ```python
   prompt = f"""你是视觉风格分析专家。观看这个视频，分析它的视觉语言。

   ## 已知量化数据
   - 主色相: H={metrics['color']['top_hues'][0] if metrics['color']['top_hues'] else '?'}°
   - 饱和度均值: {metrics['color']['sat_mean']:.1f}%  |  方差: {metrics['color']['sat_var']:.1f}
   - 亮度 P10/P50/P90: {metrics['color']['v_p10']}/{metrics['color']['v_p50']}/{metrics['color']['v_p90']}
   - 分辨率: {metrics['video']['resolution']}

   ## 你需要回答（描述风格特征，不要猜字体名/软件名）

   1. **色彩方案**: 已知主色 H={metrics['color']['top_hues'][0] if metrics['color']['top_hues'] else '?'}°——
      这个视频整体是什么色调？（暖/冷/中性）色彩搭配给你什么感觉？
      有没有明显的强调色（accent color）用在特定元素上？

   2. **字体风格（不要猜字体名！）**: 字幕/标题用的字体属于哪一类？
      - 衬线 / 无衬线 / 混合？
      - 字重：细/常规/粗/超粗？
      - 标题和正文字号对比大吗？（大≈标题很大，正文很小）
      - 整体风格：现代/传统/手写感/科技感/可爱？

   3. **构图习惯**: 博主习惯用什么构图？
      - 居中人物 / 三分法 / 对称 / 留白多 / 填满画面？
      - 是否有规律性的构图模式？（如每段开头全景→特写）

   4. **B-roll / 素材风格**: 除了博主本人，画面上还出现什么类型的素材？
      - 图表/数据可视化（风格：简洁/花哨/动态/静态）
      - 屏幕录制（带鼠标/不带/局部放大）
      - 素材片段（真实场景/产品特写/文字卡片）
      - 纯色背景 + 文字

   5. **特效/动画**: 画面上有没有特效或动画？
      - 如果有，描述其风格和密度——不是"用了什么插件"，而是"画面元素怎么动的"
      - 特效是轻量的（淡入淡出/滑动）还是重的（粒子/3D/Motion Graphics）？

   6. **视觉统一性**: 整个视频的视觉语言统一吗？有没有某段突然变风格？

   输出 markdown，每部分一个小标题。"""
   ```

   ### Pass 3: 音频策略

   ```python
   prompt = f"""你是音频策略分析专家。观看（听）这个视频，分析它的音频设计。

   ## 已知量化数据
   - 积分响度: {metrics['audio']['integrated_lufs']:.1f} LUFS
   - 真峰值: {metrics['audio']['true_peak_dbtp']:.1f} dBTP
   - 响度范围: {metrics['audio']['loudness_range_lu']:.1f} LU
   - BPM: {metrics['bpm']['tempo']:.1f}
   - 卡点精度: {metrics['bpm']['beat_alignment_mean_ms']:.0f}ms（<50ms 精确，>200ms 不卡）

   ## 你需要回答

   1. **BGM 风格（不要猜曲名！）**: 背景音乐是什么风格？
      - 电子/钢琴/管弦/Lo-fi/摇滚/氛围/无BGM？
      - 情绪：激昂/舒缓/紧张/温馨/中性？
      - BPM ≈{metrics['bpm']['tempo']:.0f}——这个速度和画面节奏搭吗？

   2. **BGM 切换策略**: BGM 在哪些时间点变化？
      - 是否随叙事段落切换？（如高潮段换激昂曲）
      - 切换是硬切还是淡入淡出？
      - 有没有 BGM 完全消失的"留白"段落？效果如何？

   3. **人声与 BGM 平衡**: 人声是否始终清晰可辨？
      响度范围 {metrics['audio']['loudness_range_lu']:.1f} LU——这个波动合理吗？
      BGM 有没有盖过人声的段落？

   4. **音效使用**: 是否有音效？（弹出音/转场音/强调音/UI 音效）
      如果有，音效的密度和风格如何？是每几秒一个还是偶尔出现？

   5. **卡点感知**: 已知卡点精度 {metrics['bpm']['beat_alignment_mean_ms']:.0f}ms——
      你的听觉感受和这个数字吻合吗？哪些部分卡点最明显？哪些部分不卡但感觉也没问题？

   输出 markdown，每部分一个小标题。"""
   ```

   ### Pass 4: 剪辑手法

   ```python
   prompt = f"""你是剪辑分析专家。观看这个视频，分析它的剪辑手法。

   ## 已知量化数据
   - 切镜次数: {metrics['cuts']['count']} 次
   - 平均切频: {metrics['cuts']['avg_freq']:.2f} cuts/s
   - 切频标准差: {metrics['cuts']['freq_std']:.2f}（低=节奏均匀，高=节奏起伏大）
   - 最长单镜: {metrics['cuts']['max_interval_s']:.1f}s
   - 最短单镜: {metrics['cuts']['min_interval_s']:.1f}s
   - 时长: {metrics['video']['duration_s']:.0f}s

   ## 你需要回答（描述视觉特征，不要猜"用了什么转场名"）

   1. **切镜节奏**: 已知平均切频 {metrics['cuts']['avg_freq']:.2f} cuts/s——
      你的视觉感受吻合吗？有没有段落切得特别快或特别慢？
      最长单镜 {metrics['cuts']['max_interval_s']:.1f}s——这一段是故意的留白还是可能拖沓？

   2. **转场类型（描述特征，不要猜名称）**:
      - 大多数转场是直接切（硬切）还是带过渡效果？
      - 如果有过渡：过渡时长大约多长？过渡方式是溶解/滑动/缩放/旋转/其他？
      - 有没有特定的转场模式？（如每个新段开头用相同过渡）
      - 转场方向是否有规律？（如一直从左到右、从下到上）

   3. **变速/时间处理**: 有没有明显的变速段落？
      - 慢动作（画面比正常慢）
      - 快进/延时（画面比正常快）
      - 定格/冻结帧
      如果有，用在什么类型的段落？（重要强调/B-roll 过渡/结尾）

   4. **素材处理方式**: 博主怎么处理不同类型的素材？
      - 屏幕录制区域：全屏还是局部？有没有放大关键区域？
      - 图片/截图：直接静态显示还是 Ken Burns 效果（慢慢缩放/平移）？
      - 多人对话：同框还是切来切去？

   5. **开头和结尾的剪辑**: 视频前 10 秒和后 10 秒的剪辑密度如何？
      开头是高密度快切吸引注意力，还是慢入？结尾是快出还是留白？

   输出 markdown，每部分一个小标题。"""
   ```

   ### Pass 5: 文案与信息设计

   ```python
   prompt = f"""你是信息设计分析专家。观看这个视频，分析它的文案和信息呈现方式。

   ## 已知量化数据
   - 时长: {metrics['video']['duration_s']:.0f}s
   - 字幕对比度: {metrics['subtitle']['contrast_ratio']:.1f}:1（WCAG AA ≥4.5:1）
   - 字幕 y 位置: {metrics['subtitle']['y_mean']:.0f}px（1080p Lower Third = 850-980）
   - 字幕字号占比: {metrics['subtitle']['font_height_pct']:.1f}%（≥2% 可读）

   ## 视频文案（如有字幕/转录）
   {transcript_preview}

   ## 你需要回答

   1. **文案密度**: 这个视频的信息量如何？
      - 每分钟大约讲了几个要点？（不是数句子，是感觉信息密度）
      - 是"轻松聊天型"（密度低）还是"干货输出型"（密度高）？
      - 有没有信息过载的段落——听一遍根本记不住？

   2. **信息层级**: 博主怎么组织信息？
      - 有没有明确的"首先/其次/最后"结构？
      - 是不是用了列举（"三个原因""五个步骤"）？
      - 有没有"一句话总结"或"金句"？

   3. **修辞手法**: 博主用什么方式让信息好记？
      - 类比/比喻（"就像..."）
      - 讲故事/举例
      - 重复强调（同样的话换方式说两遍）
      - 数字/数据引用
      - 对比（"以前 vs 现在""A vs B"）

   4. **画面与文案的同步**: 旁白提到关键概念时，画面上有对应的文字/图表吗？
      两者是同时出现还是先后出现？
      画面是补充了旁白（展示旁白没说到的细节）还是只重复旁白？

   5. **字幕设计（如有内嵌字幕）**: 
      已知对比度 {metrics['subtitle']['contrast_ratio']:.1f}:1——人眼看够清晰吗？
      字幕位置 y={metrics['subtitle']['y_mean']:.0f}——有没有遮挡重要内容？
      字幕样式（描边/阴影/背景条/纯文字）是怎么处理的？
      中英文混排时字体风格一致吗？

   输出 markdown，每部分一个小标题。"""
   ```

5. 将所有 5 个 Pass 的输出聚合为配方文档——**配方不只是文字，附完整的 metrics.json**
6. 可选：将配方中跨视频可复用的模式写入 KB

### 输出

```markdown
# 视频制作配方：<标题>
**来源**: <URL> | **博主**: <频道> | **时长**: 5:47 | **分析日期**: YYYY-MM-DD

## 📊 量化快照
| 维度 | 数值 | 行业参考 |
|------|------|---------|
| 切频 | 0.78 cuts/s | 教程 0.3-0.6, MV 0.8-1.5 |
| 积分响度 | -14.2 LUFS | YouTube -14, 广播 -23 |
| BPM | 128 | — |
| 卡点精度 | 28ms | <50ms 精确 |
| 饱和度均值 | 52% | — |
| 字幕对比度 | 6.2:1 | WCAG AA ≥4.5:1 |

## 🎬 叙事公式
- **钩子**: <手法 — 抛出问题/展示结果/...>
- **结构**: 钩子(0:00-0:12) → 展开1(0:12-2:30) → 转折(2:30-3:00) → 高潮(3:00-5:00) → 结尾(5:00-5:47)
- **结尾方式**: <总结/CTA/悬念/...>

## 🎨 视觉配方
- **色调**: <暖/冷/中性> — 主色 H={top_hues[0]}° 饱和度={sat_mean}%
- **字体风格**: <衬线/无衬线> <细/粗>体 — 标题:正文 ≈ <比例>
- **构图**: <居中/三分法/...> — <特征描述>
- **B-roll**: <图表类型/素材类型/特效类型>
- **统一性**: <一致/某段突变>

## 🔊 音频配方
- **BGM 风格**: <电子/钢琴/...> — <情绪> — BPM {tempo}
- **BGM 切换**: <时机+方式>
- **人声平衡**: <清晰/被压> — 响度范围 {loudness_range} LU
- **音效密度**: <每 X 秒一个 / 偶尔 / 无>

## ✂️ 剪辑配方
- **切频**: {avg_freq} cuts/s — <快/正常/慢>
- **转场类型**: <硬切为主/带过渡> — <过渡描述>
- **变速**: <有/无> — <慢动作/快进/定格> 用于 <场景>
- **素材处理**: <屏幕录制:全屏/局部放大> <图片:静态/Ken Burns>

## 📝 文案配方
- **密度**: <高/中/低> — 每 min ~N 个要点
- **结构**: <列举式/三段式/故事线>
- **修辞**: <类比/举例/数据/对比/重复>
- **画面同步**: <补充/重复> — <先画面后旁白/同时>

## 🔍 差异点（这个博主为什么独特）
- <2-3 个让你"和别的视频不一样"的具体特征>

## 🎯 适用场景
- <这个配方适合什么类型的视频？>

## 完整量化数据
见附件: `metrics.json`
```

---

## 命令 3: extract — 视频知识提取

```
/video-analysis extract <video_url|local_file>
```

### 参数

| 参数 | 说明 |
|------|------|
| `<url>` | 抖音 / Bilibili / YouTube 视频链接，或本地文件路径 |
| `--domain` | 知识域: `software-dev`(默认) / `video-production` / `visual-design` / `business` / `general` |
| `--cookie` | (仅 B站/YouTube) 浏览器名或 cookie 文件路径 |
| `--transcript` | 已有转录文本路径 (跳过下载+转录) |
| `--no-review` | 跳过人工审核步骤 (默认会逐条展示等用户确认) |

### 平台差异

| 平台 | 下载方式 | 字幕 | 特殊要求 |
|------|---------|------|---------|
| 抖音 | curl 原生 (iesdouyin API) | 无 (Whisper) | **零 cookie, 全自动** |
| Bilibili | lux → yt-dlp 兜底 | CC 字幕 (需登录) | 无字幕时 Whisper fallback |
| YouTube | lux / yt-dlp | 自动字幕 + 人工 | 沙箱外可用 |
| 本地文件 | 直接读取 | ffprobe 检测内嵌字幕 | — |

### 执行流程

```
/video-analysis extract <url>
          │
          ├── Step 1: 下载视频 ──────────────────────────────
          │   根据平台选择下载引擎 (douyin-native / lux / yt-dlp)
          │   输出: video.mp4 + audio.wav + subs.srt (可选)
          │
          ├── Step 2: 转录 ──────────────────────────────────
          │   有字幕 → parse_subtitles() 解析 SRT/VTT
          │   无字幕 → Whisper medium (CPU, ffmpeg decode)
          │   输出: transcript.txt
          │
          ├── Step 3: LLM 提取 ──────────────────────────────
          │   调用 Qwen3-235B (DashScope)
          │   Prompt: 提取概念/流程/工具/参数/对比/经验
          │   输出: N 个 JSON 知识点 (每行一个)
          │
          ├── Step 4: 人工审核 ⭐ ──────────────────────────
          │   逐条展示提取结果，用户选择:
          │     [y] 确认写入  [n] 丢弃  [e] 编辑后写入
          │   --no-review 参数跳过此步
          │
          ├── Step 5: 去重 ──────────────────────────────────
          │   对比标题哈希 + KB 已有页面
          │   重复 → 跳过或合并; 已有但不足 → 增强
          │
          ├── Step 6: 写入知识库 ────────────────────────────
          │   按 _schema.md 规范写 frontmatter + wikilinks
          │   位置: concepts/ + entities/video-source-*.md
          │
          └── Step 7: 汇报 ──────────────────────────────────
              知识点列表 + 知识缺口 + 转录质量
```

### 实际调用

Agent 收到 `/video-analysis extract <url>` 后，读取本文件，然后执行：

```bash
# 设置环境变量
export DASHSCOPE_API_KEY=<从用户配置读取>
export HF_ENDPOINT=https://hf-mirror.com
export PYTHONPATH=D:/TOOLS/cloude code/sage/vendor

# 运行提取脚本
python D:/TOOLS/cloude code/sage/scripts/_extract_douyin.py
```

> **Agent 注意**：
> - 脚本路径：`D:/TOOLS/cloude code/sage/scripts/_extract_douyin.py`（抖音）/ `D:/TOOLS/cloude code/sage/scripts/extract.py`（通用）
> - 如果 whisper 转录失败（av DLL 问题），脚本会自动降级为"标题+描述"模式，此时提取质量明显下降，需向用户说明
> - 输出目录：`D:/TOOLS/cloude code/sage/output/extract/`
> - 知识库目录：`D:/AI/projects/knowledge-base/wiki/`
> - 如果用户要提取的是**抖音链接**，直接用 `_extract_douyin.py`；其他平台用 `extract.py`

### 输出格式

```
============================================================
  视频知识提取报告
============================================================
  视频: <标题> | 博主: <作者> | 时长: MM:SS
  下载: <平台> (<引擎>), <大小>
  转录: N 字符 (<来源>)

  ## 提取知识点 (K 个)
  | # | 标题 | 类型 | 置信度 | 操作 |
  |---|------|------|--------|------|
  | 1 | xxx | concept | medium | [y] [n] [e] |
  | 2 | yyy | workflow | medium | [y] [n] [e] |

  ## 知识缺口
  - [MM:SS] 处提到 "XXX"，上下文不足
  
  ## 写入文件
  - [[page1]] — concepts/xxx.md
  - [[page2]] — concepts/yyy.md
```

### 边界情况

| 情况 | 处理 |
|------|------|
| 视频 < 30s | 可能信息不足 → 警告但仍尝试提取 |
| 转录全是外语 | 标注 + 跳过 |
| 视频已删除 | 报 URL 不可达 |
| 同 URL 已提取过 | 查 entities/ 去重 → 提示用户 |
| Whisper 转录为空 | 退回到"标题+描述"模式 |
| API 调用超时 | 重试 1 次 |

---

## 数据积累

### 历史目录

```
D:/TOOLS/cloude code/sage/kb/wiki/data/video-qa/
  ├── 2026-06-08-xxx.json     (每次 qa 的 metrics.json)
  ├── 2026-06-09-yyy.json
  └── profile.json            (聚合画像，每次 qa 后更新)
```

### profile.json 格式

```json
{
  "updated": "2026-06-09",
  "n": 12,
  "metrics": {
    "avg_freq": {"p25": 0.38, "p50": 0.52, "p75": 0.61},
    "integrated_lufs": {"p25": -17.2, "p50": -15.8, "p75": -14.3},
    "beat_alignment_mean_ms": {"p25": 28, "p50": 52, "p75": 78},
    "sat_mean": {"p25": 41, "p50": 47, "p75": 55},
    "contrast_ratio": {"p25": 3.8, "p50": 5.1, "p75": 6.2}
  }
}
```

---

## 语言

默认中文。技术名词保留原文。
