---
title: Sage — AI 知识库系统
description: 视频分析 + 知识提取 + 递归完备化。从视频中自动提取结构化知识，三层知识库（通用/职业/项目）。
type: project
domain: [video-production, software-dev, ai-engineer]
source: human-curated
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# Sage 项目

## 项目概述

Sage 是一个视频分析与知识提取流水线。输入视频 URL → 自动下载 → Whisper 转录 → LLM 提取知识点 → 写入三层知识库。

**核心技术栈**：curl (抖音原生API) / lux / yt-dlp → faster-whisper → DeepSeek V4 Flash → Qwen3-VL-Flash

## 项目文件

- [[video-source-douyin-dbfda0b83b0f]] — 抖音视频源：阿里三面Agent权限隔离八连问

## 相关职业

本项目的知识需求跨越两个职业：
- [[professions/video-editor/profile]] — 视频剪辑师：素材处理、剪辑工作流、调色、音频
- [[professions/software-dev/profile]] — 软件开发：Agent安全、权限模型、沙箱

## 通用知识引用

- [[general/video/video-pacing-rhythm]] — 视频节奏分析（extract 管线 Layer 2 量化）
- [[general/video/video-transitions-guide]] — 转场识别
- [[general/audio/audio-loudness-standards]] — 音频标准化（EBU R128 检测）
- [[general/color/color-theory-basics]] — 色彩分析（HSV 直方图）