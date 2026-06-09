---
title: 调色基础
description: >
  视频调色的基本概念和操作流程。一级校色(曝光/对比/白平衡) → 二级调色(局部/肤色/天空) → 风格LUT。DaVinci Resolve 节点式工作流。
type: concept
domain: [video-production]
source: web-searched
source_detail: [DaVinci Resolve workflow, 2025]
related: [[professions/video-editor/video-editing-pipeline]], [[professions/video-editor/advanced-color-grading]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# 调色基础

## 两级调色模型

```
一级校色 (Primary Correction)
├── 曝光/对比度 — 画面亮度正常
├── 白平衡 — 白色是真的白，不是偏蓝/偏黄
├── 饱和度 — 整体色彩浓度
└── 目标: 所有镜头"看起来一样"

二级调色 (Secondary Grading)
├── 肤色优化 — 用 Qualifier 选中皮肤单独调
├── 天空增强 — 用遮罩选中天空压暗/加蓝
├── 风格 LUT — 套用电影感/复古/日系风格
└── 目标: 画面有"风格"
```

## DaVinci Resolve 节点结构（标准模板）

```
[Clip] → [Node 1: WB/曝光] → [Node 2: 对比/饱和]
       → [Node 3: 肤色 Qualifier] → [Node 4: 天空/背景 Mask]
       → [Node 5: LUT 风格化] → [Node 6: 锐化/暗角] → [Output]
```

每个 Node 只做一件事。出问题知道回哪个节点改。

## 示波器速查

| 示波器 | 看什么 | 正常范围 |
|--------|--------|---------|
| Waveform (波形) | 亮度分布 | 0-100 IRE，肤色 ≈ 45-70 IRE |
| Parade (RGB分量) | 白平衡 | R/G/B 波形一致 = 白平衡正确 |
| Vectorscope (矢量) | 肤色线 | 肤色沿 -5° 到 +15° 线 |
| Histogram (直方图) | 死黑/过曝 | 不贴左墙(死黑)不贴右墙(过曝) |

## 快速调色流程（5 分钟版）

1. **Lift/Gamma/Gain**: Lift 定黑位 → Gamma 定中间调 → Gain 定白位
2. **白平衡**: 用吸管点画面中"应该是白色/灰色"的区域
3. **饱和度**: +10% to +20%（不要过）
4. **LUT**: 套一个风格 LUT，强度 50-70%
5. **对比检查**: 切到上一个镜头，确认色调一致

## 经验法则

- 肤色是观众最敏感的颜色 → 优先确保肤色自然
- LUT 不是魔法 → 先做好一级校色再套 LUT
- 不同显示器颜色不同 → 用示波器判断，不要用眼睛猜
- "电影感" = 低饱和 + 暖色偏移 + 暗角 + 16:9 以上画幅
