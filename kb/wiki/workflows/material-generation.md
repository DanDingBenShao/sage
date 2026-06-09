---
title: 视频素材生成全流程
description: >
  从零到素材齐备的完整工作流。覆盖7大类素材：截图标注、屏幕录制、AI图像、AI视频、Stock素材、BGM/音效、图表文字卡片。含文件组织规范和素材质量检查清单。
type: workflow
domain: [video-production]
source: web-searched
source_detail: [multi-source synthesis, 2025]
related: [[video-editing-pipeline]], [[video-material-pipeline]], [[screen-recording-setup]], [[screenshot-annotation]], [[ai-image-generation]], [[royalty-free-music]], [[stock-footage-sources]], [[script-storyboard-methodology]], [[ai-video-generation]], [[chart-animation-tools]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
decomposition_depth: 0
is_atomic: false
prerequisites: []
---

# 视频素材生成全流程

## 分解树

```
素材生成
├── [1] 前置准备
│   ├── 1.1 确定脚本与分镜 → [[script-storyboard-methodology]] → [原子]
│   ├── 1.2 创建项目文件夹结构 → 按 video-material-pipeline 规范 → [原子]
│   └── 1.3 准备模板文件（文字卡片模板、调色预设） → [原子]
│
├── [2] 截图与标注
│   ├── 2.1 截图获取 → [[screenshot-annotation]] → [原子]
│   │   ├── Win: Snipaste (F1截图/F3贴图) 或 ShareX
│   │   └── Mac: CleanShot X (滚动截图/隐藏桌面图标)
│   ├── 2.2 标注增强
│   │   ├── 添加箭头/框标注（统一颜色: 红=强调, 黄=高亮背景） → [原子]
│   │   ├── 模糊敏感信息 → [原子]
│   │   └── 添加步骤编号 → [原子]
│   └── 2.3 导出 → PNG 格式, 分辨率 ≥ 视频分辨率 → [原子]
│
├── [3] 屏幕录制
│   ├── 3.1 配置录制软件 → [[screen-recording-setup]] → [原子]
│   │   ├── OBS Studio: NVENC H.264, CQ 18-22, 30fps(教程)/60fps(流畅演示)
│   │   └── Mac: Screen Studio 自动优化
│   ├── 3.2 设置录制场景 → 全屏/窗口/区域/画中画 → [原子]
│   ├── 3.3 录制 → F9开始/F10暂停/F9停止 → [原子]
│   └── 3.4 后期压缩 → ffmpeg -crf 22 二次编码减体积 → [[ffmpeg-video-editing]] → [原子]
│
├── [4] AI 生成素材
│   ├── 4.1 AI 图像生成 → [[ai-image-generation]] → [原子]
│   │   ├── 封面图 → Midjourney V7 (画质最好)
│   │   ├── 概念插图 → GPT-4o Image (文字标注能力最强)
│   │   ├── 风格背景 → Midjourney --sref (确保系列一致性)
│   │   └── 故事板预演 → DALL-E 3 (快, 改prompt方便)
│   └── 4.2 AI 视频生成 → [[ai-video-generation]] → [原子]
│       ├── B-roll补充 → Runway Gen-4 (相机控制强)
│       ├── 人物对话 → Kling (口型同步最好)
│       ├── 电影级产品 → Veo 3 (画质最好, 含音频)
│       └── 多镜头长片 → Indie Filmmaker 混合管线
│
├── [5] Stock 素材
│   ├── 5.1 视频素材 → [[stock-footage-sources]] → [原子]
│   │   ├── 免费: Pexels / Pixabay / Coverr / Mixkit
│   │   └── 付费: Artgrid ($25/月) / Storyblocks ($15/月)
│   ├── 5.2 图片素材
│   │   ├── 免费: Unsplash / Pexels / Pixabay
│   │   └── 付费: Shutterstock / Getty Images
│   └── 5.3 下载后统一处理 → 转码到项目统一格式 (1080p H.264 CRF18) → [原子]
│
├── [6] 音频素材
│   ├── 6.1 BGM 选择 → [[royalty-free-music]] → [原子]
│   │   ├── 免费: Uppbeat (attribution) / Pixabay Music (无attribution)
│   │   └── 付费: Epidemic Sound ($15/月, 曲库最大)
│   ├── 6.2 BGM 情绪-视频类型匹配 → 激昂=品牌片, Lo-fi=教程, 温暖=叙事 → [原子]
│   ├── 6.3 音效收集 → Pixabay SFX / Epidemic Sound SFX → [原子]
│   └── 6.4 旁白录制 (如需要)
│       ├── 麦克风: 领夹麦 > USB 麦 > 笔记本内置麦
│       └── 环境: 安静房间, 离墙30cm+, 录音电平 -12 to -6 dB → [原子]
│
├── [7] 图表与文字卡片
│   ├── 7.1 数据图表 → [[chart-animation-tools]] → [原子]
│   ├── 7.2 文字卡片 (标题/要点/总结) → 剪映内置 / After Effects → [原子]
│   └── 7.3 导出 → PNG 序列 或带透明通道 MOV → [原子]
│
└── [8] 素材审核
    ├── 8.1 逐项检查清单 → [原子]
    ├── 8.2 缺失素材补充 → 回到对应步骤 → [原子]
    └── 8.3 确认所有素材分辨率 ≥ 视频目标分辨率 → [原子]
```

## 为什么这样拆？

按"素材类型"而非"获取方式"组织——同一种素材可能有多种获取方式（如 B-roll 可以自己拍、AI 生成、Stock 下载），但它们在时间轴上的用途相同。创作者按类型收集更自然。

## 素材审核清单

```
[ ] 截图: 分辨率 ≥ 1080p, PNG 格式, 标注清晰可见
[ ] 屏幕录制: 1080p 30fps+, 光标可见, 无意外弹窗
[ ] AI 图像: 风格统一 (全系列用同 --sref), 16:9 画幅
[ ] AI 视频: 无画面崩坏/变形, 与实拍片段过渡自然
[ ] Stock 视频: 已转码统一格式, 无违规人脸
[ ] BGM: 版权确认, WAV/FLAC 无损格式, BPM 与节奏匹配
[ ] 音效: 已试听, 无爆音, 音量合适
[ ] 图表: 动画导出完成, 数据准确
[ ] 文字卡片: 字体统一, 对齐正确, 无错别字
[ ] 文件: 全部放入对应项目文件夹, 无散落文件
```

## 工具选择决策树

```
需要截图标注? → 教程类必须 → Snipaste (Win) / CleanShot X (Mac)
需要屏幕录制? → 软件演示 → OBS Studio
需要封面/插图? → 追求画质 → Midjourney V7
               → 需要文字标注 → GPT-4o Image
               → 预算为0 → Stable Diffusion 3 (免费本地)
需要 B-roll? → 有预算 → 实拍 > Artgrid
             → 没预算 → Pexels/Pixabay > AI生成
需要 BGM? → 预算为0 → Uppbeat (需attribution) / Pixabay Music
          → 有预算 → Epidemic Sound (最省心)
需要图表动画? → 简单 → Canva / Keynote
              → 专业 → After Effects 模板
```
