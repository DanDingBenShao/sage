---
title: 屏幕录制工具配置
description: >
  OBS Studio 和 Screen Studio 的配置方案。录制参数（分辨率/帧率/码率）、场景设置（全屏/窗口/区域）、音频路由、常见问题排查。教程类视频核心素材来源。
type: tool
domain: [video-production]
source: web-searched
source_detail: [OBS Studio docs, Screen Studio, 2025]
related: [[video-material-pipeline]], [[ffmpeg-video-editing]], [[screenshot-annotation]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# 屏幕录制工具配置

## 工具选择

| 工具 | 平台 | 价格 | 适合 |
|------|------|------|------|
| **OBS Studio** | Win/Mac/Linux | 免费开源 | 所有人，功能最强 |
| **Screen Studio** | macOS only | $89 一次性 | 自动平滑光标/缩放，macOS 首选 |
| **Loom** | 全平台 | 免费/付费 | 快速分享，不适合后期编辑 |
| **ShareX** | Windows | 免费开源 | 截图+录屏+标注一体 |

## OBS Studio 推荐配置

### 录制设置（教程用）

```
输出 → 输出模式: 高级
  → 录制:
    编码器: NVIDIA NVENC H.264 (或 AMD HW H.264)
    码率控制: CQP
    CQ 级别: 18-22 (越低越清晰, 18=视觉无损)
    预设: P5 (Slow, 高质量)
    配置文件: high

视频:
  基础分辨率: 1920x1080 (或显示器原生分辨率)
  输出分辨率: 1920x1080
  缩小算法: Lanczos (36采样)
  帧率: 30 FPS (教程) / 60 FPS (游戏/流畅演示)

音频:
  采样率: 48kHz
  声道: 立体声
  桌面音频: 开启 (录制系统声音)
  麦克风: 开启 (录制人声)
```

### 场景设置

```
场景 1: "全屏"
  源: 显示器捕获

场景 2: "窗口"
  源: 窗口捕获 (选目标窗口)

场景 3: "区域"
  源: 显示器捕获 → 按住 Alt 拖拽裁剪

场景 4: "画中画"
  源: 显示器捕获 + 视频捕获设备(摄像头)

快捷键:
  F9: 开始/停止录制
  F10: 暂停/继续录制
```

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 录出来黑屏 | GPU 渲染冲突 | 设置→高级→渲染器改为 Direct3D 11 |
| 声音不同步 | 采样率不一致 | 所有设备统一 48kHz |
| 文件巨大 | CQP 太低 | CQP 调到 22-26 |
| 录不到系统声音 | 音频路由 | 确认"桌面音频"设备选对 |

## Screen Studio (macOS)

不推荐参数配置——它自动优化。只需设置:
- 分辨率: 2x Retina (高清)
- 帧率: 60 FPS (自动平滑鼠标移动)
- 自动缩放: 开启 (自动放大点击区域)

## 录制后处理

```bash
# 用 ffmpeg 二次编码压缩体积（画质基本无损）
ffmpeg -i recording.mkv -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 128k output.mp4
```
