---
title: 音频响度标准 (LUFS)
description: >
  EBU R128 响度标准在视频制作中的应用。YouTube、B站、抖音等平台的 LUFS 目标值、真峰值限制、响度范围(LRA)参考。音频后期必须掌握的基础知识。
type: concept
domain: [video-production]
source: web-searched
source_detail: [EBU R128 standard, platform specs, 2025]
related: [[video-editing-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# 音频响度标准 (LUFS)

## 核心指标

| 指标 | 含义 | 检测命令 |
|------|------|---------|
| Integrated LUFS | 整个文件的平均响度 | `ffmpeg loudnorm` |
| True Peak (dBTP) | 最响瞬间的真实峰值 | `ffmpeg loudnorm` |
| Loudness Range (LRA) | 响度动态范围 | `ffmpeg loudnorm` |

## 各平台目标值

| 平台 | Integrated LUFS | True Peak | 说明 |
|------|----------------|-----------|------|
| YouTube | -14 LUFS | ≤ -1 dBTP | 超过-14会被自动降低音量 |
| B站 (Bilibili) | -16 to -14 LUFS | ≤ -1 dBTP | 没有官方规范，参考YouTube |
| 抖音/TikTok | -14 to -12 LUFS | ≤ -1 dBTP | 短视频偏响 |
| 广播电视 | -23 LUFS | ≤ -1 dBTP | EBU R128 广播标准 |
| Spotify (仅音频) | -14 LUFS | ≤ -1 dBTP | 音乐平台参考 |

## 检测命令

```bash
# ffmpeg EBU R128 响度检测
ffmpeg -nostats -i input.mp4 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" \
  -f null /dev/null 2>&1

# 输出示例:
# integrated: -15.8 LUFS
# true_peak: -2.1 dBTP
# loudness_range: 7.2 LU
```

## 响度归一化命令

```bash
# 将视频响度标准化到 -16 LUFS (适合 B站/YouTube)
ffmpeg -i input.mp4 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:linear=true" \
  -c:v copy output.mp4
```

## 经验法则

- **人声**: 保持在 -18 to -12 LUFS，对话清晰
- **BGM**: 在人声下方 12-18 LU，即 BGM 约 -30 to -24 LUFS
- **LRA < 3 LU**: 太"平"，没有起伏，适合背景音乐但不适合演讲
- **LRA > 20 LU**: 太"吓人"，观众会频繁调音量
- **True Peak ≥ 0 dBTP**: 爆音，必须修

## 实用技巧

1. 先调人声到目标响度，再加 BGM
2. BGM 用 sidechain compression（人声出现时 BGM 自动降低）
3. 导出前跑一次 `loudnorm` 检测确认合规
