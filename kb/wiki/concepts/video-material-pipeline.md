---
title: 视频素材准备管线
description: >
  视频制作的素材获取全流程，覆盖截图/标注、屏幕录制、AI生成图像/视频、Stock素材、BGM/音效、图表动画、文字卡片。素材准备是视频制作的第一步，质量决定成片上限。
type: concept
domain: [video-production]
source: web-searched
source_detail: [multiple sources, 2025]
related: [[video-editing-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# 视频素材准备管线

## 核心原则

**素材质量决定成片上限。** 剪辑可以救节奏，调色可以救画面，但没有素材什么都做不了。

## 素材分类

```
视觉素材
├── 截图 + 标注 (教程类核心素材)
├── 屏幕录制 (软件演示)
├── AI 生成图像 (封面/插图/概念图)
├── AI 生成视频 (B-roll/转场素材)
├── Stock 素材 (真实场景/空镜)
├── 图表动画 (数据可视化)
└── 文字卡片 (标题/要点/总结)

音频素材
├── BGM (背景音乐，定调情绪)
├── 音效 (转场/强调/UI 音效)
└── 旁白/配音 (人声轨)
```

## 素材准备优先级（按视频类型）

| 视频类型 | 核心素材 | 辅助素材 |
|----------|---------|---------|
| 软件教程 | 屏幕录制 + 截图标注 | BGM + 文字卡片 |
| 知识科普 | 图表动画 + AI图像 | Stock + BGM |
| Vlog/纪实 | 实拍 + Stock B-roll | BGM + 字幕 |
| 产品展示 | 截图标注 + AI图像 | BGM + 音效 |
| 数据分析 | 图表动画 + 文字卡片 | BGM + 屏幕录制 |

## 工具链全景

| 素材类型 | 首选工具 | 备选 |
|----------|---------|------|
| 截图标注 | Snipaste / CleanShot X | ShareX (免费) |
| 屏幕录制 | OBS Studio | Screen Studio (付费, macOS) |
| AI 图像 | Midjourney V7 | DALL-E 3 / SD3 |
| AI 视频 | Runway Gen-4 / Kling | Veo 3 / Pika |
| Stock 视频 | Pexels / Pixabay (免费) | Artgrid (付费) |
| BGM | Uppbeat (免费) | Epidemic Sound (付费) |
| 音效 | Pixabay SFX (免费) | Epidemic Sound |
| 图表动画 | After Effects + 模板 | Canva / Keynote |
| 文字卡片 | 剪映 / CapCut 内置 | After Effects |

## 文件组织规范

```
ProjectName/
├── 00-script/          # 脚本、分镜
├── 01-screenshots/     # 截图原图 + 标注版
├── 02-recording/       # 屏幕录制原始文件
├── 03-ai-generated/    # AI 生成的图像/视频
├── 04-stock/           # 下载的 Stock 素材
├── 05-audio/           # BGM + 音效
├── 06-graphics/        # 图表/文字卡片导出
├── 07-exports/         # 中间导出/渲染
└── project.ffmpeg.md   # 项目 ffmpeg 命令备忘
```

## 与其他概念的关系

- [[video-editing-pipeline]] — 素材准备好后进入剪辑管线
- [[audio-loudness-standards]] — 音频素材的响度规范
- [[color-grading-basics]] — 调色是后期的事，但素材拍摄时就该考虑
