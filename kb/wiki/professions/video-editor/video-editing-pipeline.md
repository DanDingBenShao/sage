---
title: 视频剪辑管线
description: >
  从粗剪到导出的完整后期流程。五阶段：粗剪→精剪→音频→调色→字幕→导出。适用于短视频(抖音/B站)和长视频(YouTube)两种节奏。
type: concept
domain: [video-production]
source: web-searched
source_detail: [multiple sources, 2025]
related: [[video-material-pipeline]], [[video-pacing-rhythm]], [[audio-loudness-standards]], [[general/color/color-theory-basics]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# 视频剪辑管线

## 核心原则

**先粗后精，层层递进。** 不要在粗剪阶段纠结细节——每个阶段只做该阶段的事。

## 五阶段管线

```
[1] 粗剪 (Assembly Cut)
    └── 把所有可用素材按脚本顺序排上时间轴
        目标: 骨架完整，叙事通顺
        不问: 颜色、音量、转场好不好看

[2] 精剪 (Refinement)
    └── 卡节奏、剪废话、穿插 B-roll、加转场
        目标: 节奏紧凑，视觉丰富
        不问: 音频细节、字幕样式

[3] 音频处理 (Audio)
    └── 降噪 → EQ → 压缩 → 响度标准化 → BGM 混音
        目标: 人声清晰，BGM 不抢戏，响度合规

[4] 调色 (Color)
    └── 一级校色 → 二级调色 → 风格 LUT → 统一性检查
        目标: 画面干净，风格一致

[5] 字幕 + 导出 (Subtitles + Export)
    └── AI 识别 → 校对 → 样式 → 烧录/导出 SRT → 平台参数导出
        目标: 字幕可读，文件合规
```

## 短视频 vs 长视频节奏差异

| 维度 | 短视频 (<3min) | 长视频 (5-30min) |
|------|---------------|-------------------|
| 切频 | 1.0-2.5 cuts/s | 0.3-0.6 cuts/s |
| 钩子 | 前 3 秒必须抓住 | 前 15-30 秒建立预期 |
| B-roll 密度 | 几乎每句都在换画面 | 每段 2-3 个 B-roll |
| 转场 | 快节奏，硬切为主 | 可留白，淡入淡出 |
| 字幕 | 大字、居中、KTV 跟读风格 | 底部标准字幕 |
| LUFS | -14 to -12 | -16 to -14 |

## 工具选择

| 阶段 | 专业工具 | 快速工具 |
|------|---------|---------|
| 剪辑 | DaVinci Resolve / Premiere Pro | 剪映 / CapCut |
| 音频 | Fairlight (DaVinci 内置) / Audacity | 剪映内置 |
| 调色 | DaVinci Resolve (行业标准) | 剪映滤镜 |
| 字幕 | Arctime / Subtitle Edit | 剪映 AI 字幕 |
| 导出 | DaVinci Deliver / Media Encoder | 剪映导出 |

**建议**: 新手从剪映入手，熟练后迁移到 DaVinci Resolve（免费版已够用）。

## 与其他概念的关系

- [[video-material-pipeline]] — 素材准备好才能开始剪辑
- [[video-pacing-rhythm]] — 精剪阶段的核心判断依据
- [[audio-loudness-standards]] — 音频阶段的响度目标值
- [[general/color/color-theory-basics]] — 调色阶段的基础操作
