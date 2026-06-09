---
title: 视频剪辑全流程
description: >
  从粗剪到导出的完整剪辑工作流。五阶段递进：粗剪→精剪→音频→调色→字幕→导出。含每个阶段的具体操作步骤、ffmpeg 命令、DaVinci Resolve 操作要点、导出参数对照表。
type: workflow
domain: [video-production]
source: web-searched
source_detail: [DaVinci Resolve workflow, ffmpeg docs, editing best practices, 2025]
related: [[video-material-pipeline]], [[video-editing-pipeline]], [[video-pacing-rhythm]], [[audio-loudness-standards]], [[general/color/color-theory-basics]], [[ffmpeg-video-editing]], [[subtitle-workflow]], [[video-transitions-guide]], [[advanced-color-grading]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
decomposition_depth: 0
is_atomic: false
prerequisites:
  - { entry: "workflows/material-generation.md", source: "same-session", confidence: high }
---

# 视频剪辑全流程

## 分解树

```
视频剪辑
├── [1] 项目设置
│   ├── 1.1 创建项目 → 分辨率/帧率与素材一致 (通常1080p 30fps) → [原子]
│   ├── 1.2 导入所有素材到媒体池 → [原子]
│   └── 1.3 创建代理文件 (4K素材 → 1080p代理, 编辑更流畅) → [原子]
│
├── [2] 粗剪 (Assembly Cut)
│   ├── 2.1 按脚本顺序排列主镜头(A-roll) → 只看叙事通顺 → [原子]
│   ├── 2.2 剪掉明显废话、口误、NG段落 → [原子]
│   └── 2.3 标记 B-roll 插入点 → 在时间轴上打标记 → [原子]
│
├── [3] 精剪 (Refinement)
│   ├── 3.1 节奏控制 → [[video-pacing-rhythm]] → [原子]
│   │   ├── 教程: 0.2-0.5 cuts/s → 每步骤一个镜头
│   │   ├── 短视频: 1.0-2.5 cuts/s → 每句话至少换一次画面
│   │   └── 检测: ffmpeg scdet scene detection
│   ├── 3.2 穿插 B-roll → 每个要点配 2-3 个辅助镜头 → [原子]
│   ├── 3.3 转场添加 → [[video-transitions-guide]] → [原子]
│   │   ├── 硬切: 90% 的转场应该用硬切 (最干净)
│   │   ├── 淡入淡出: 章节开头/结尾
│   │   ├── 交叉溶解: 时间流逝/场景切换 (0.3-0.5s)
│   │   └── 不要: 翻页/旋转/百叶窗等花哨转场
│   └── 3.4 J-cut / L-cut → 声音先入/后出, 听觉引导视觉 → [原子]
│
├── [4] 音频处理 → [[audio-loudness-standards]]
│   ├── 4.1 降噪 → [原子]
│   │   ├── DaVinci Fairlight: 噪声门 → 采样 → 降噪
│   │   └── ffmpeg: afftdn 滤镜
│   ├── 4.2 EQ → 人声增强: +2-3dB @ 3kHz, 低切 @ 80Hz → [原子]
│   ├── 4.3 压缩 → 人声: 2:1 ratio, -12dB threshold, 快attack → [原子]
│   ├── 4.4 响度标准化 → [原子]
│   │   ├── 目标: -14 LUFS (YouTube) / -16 LUFS (B站/通用)
│   │   └── 命令: ffmpeg loudnorm filter
│   └── 4.5 BGM 混音 → [原子]
│       ├── BGM 音量: 人声下方 12-18 LU (BGM 约 -30 to -24 LUFS)
│       ├── Sidechain: 人声出现时 BGM 自动降低 3-6dB
│       └── 淡入淡出: BGM 开头 1-2s 淡入 / 结尾 1-2s 淡出
│
├── [5] 调色 → [[general/color/color-theory-basics]]
│   ├── 5.1 一级校色 → [原子]
│   │   ├── Lift/Gamma/Gain: 黑位/中间调/白位
│   │   ├── 白平衡: 吸管点白色/灰色区域
│   │   └── 饱和度: +10-20%
│   ├── 5.2 二级调色 → [[advanced-color-grading]] → [原子]
│   │   ├── 肤色保护: Qualifier 选中 → 单独优化
│   │   └── 局部调整: 天空/背景 Mask
│   ├── 5.3 LUT 风格化 → 套用后强度 50-70% → [原子]
│   ├── 5.4 镜头匹配 → 切换到上一个镜头, 确认色调一致 → [原子]
│   └── 5.5 示波器检查 → Waveform/Parade/VectorScope 确认 → [原子]
│
├── [6] 字幕 → [[subtitle-workflow]]
│   ├── 6.1 AI 识别 → 剪映智能字幕 (中文选中文) → [原子]
│   ├── 6.2 校对 → 专有名词/数字/标点/填充词/拆分合并 → [原子]
│   ├── 6.3 时间轴 → 每条 1-7s, 中文每行 ≤20字 → [原子]
│   ├── 6.4 样式 → 白字+黑色描边(2-4px), 无衬线字体, ≥4.5:1对比度 → [原子]
│   └── 6.5 导出 → 短视频烧录 / 长视频SRT → [原子]
│
├── [7] 导出
│   ├── 7.1 参数选择 → [原子]
│   │   ├── YouTube: H.264, 1080p/4K, CRF 18-22, AAC 192kbps
│   │   ├── B站: H.264, 1080p ≤ 18000kbps, AAC 320kbps
│   │   └── 抖音: H.264, 1080x1920 (竖屏), CRF 22, AAC 128kbps
│   └── 7.2 导出前自查 → [原子]
│       ├── 从头到尾看一遍 (不要跳)
│       ├── 静音看一遍 (字幕能理解？)
│       ├── 手机屏幕尺寸看一遍 (字够大？)
│       └── 响度检测: ffmpeg loudnorm 确认合规
│
└── [8] 归档
    ├── 8.1 项目文件备份 → .drp (DaVinci) / .prproj (Premiere) → [原子]
    └── 8.2 清理中间文件 → 只保留原始素材+最终导出+项目文件 → [原子]
```

## 为什么这样拆？

按"后期制作的认知阶段"而非"软件功能模块"组织。每个阶段有明确的目标和禁止事项——粗剪不问颜色，调色不纠结字幕。这个顺序有依赖关系（不能先调色再精剪），但每个阶段内部可以迭代。新人最常见的问题是"在粗剪阶段就开始调色"，浪费时间。

## 阶段间检查点

```
粗剪 ❯ 精剪:  叙事完整吗？有没有缺失的重要段落？
精剪 ❯ 音频:  节奏合适吗？有没有需要留给 BGM 的留白？
音频 ❯ 调色:  人声清晰吗？BGM 压人声了吗？
调色 ❯ 字幕:  色调一致吗？有没有某个镜头特别跳？
字幕 ❯ 导出:  字幕准确吗？静音看能理解吗？
导出 ❯ 发布:  文件能正常播放吗？响度合规吗？
```

## 导出参数速查表

| 平台 | 分辨率 | 编码 | 视频码率 | 音频 | 备注 |
|------|--------|------|---------|------|------|
| YouTube | 1080p/4K | H.264 | CRF 18-22 | AAC 192k | VP9 可选, 文件小但编码慢 |
| B站 | 1080p | H.264 | ≤18000kbps | AAC ≤320k | 码率硬限制, 超出会被二压 |
| 抖音 | 1080x1920 | H.264 | CRF 20-23 | AAC 128k | 竖屏 9:16 |
| 微信视频号 | 1080p | H.264 | ≤6000kbps | AAC 128k | 1分钟以内 |

```bash
# 通用高质量导出命令 (ffmpeg)
ffmpeg -i input.mp4 \
  -c:v libx264 -preset slow -crf 20 \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  output.mp4
```

## 效率技巧

1. **代理文件**: 4K 素材先转 1080p 代理，编辑流畅度天差地别
2. **快捷键**: 至少记住 切刀/选择/删除/撤销/保存 五个
3. **保存频率**: 每完成一个阶段 Ctrl+S
4. **版本管理**: 大改动前先"另存为" → `project_v2.drp`
5. **参考轨道**: 导入参考视频放在最上层视频轨，静音，对照剪辑
