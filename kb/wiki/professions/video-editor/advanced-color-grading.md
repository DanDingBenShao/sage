---
title: DaVinci Resolve 高级调色
description: >
  DaVinci Resolve 的节点式调色进阶指南。6 模块节点树模板、Qualifier (HSL/Luma)、Power Window 跟踪、Parallel/Layer Mixer 节点、Key Routing、Magic Mask、纹理与修饰效果(Grain/Glow/Halation)。附可复用 Power Grade 模板结构。
type: tool
domain: [video-production]
source: web-searched
source_detail: [AAA Presets, MiraCamp, VFXstudy, Blackmagic docs, 2025]
related: [[video-editing-workflow]], [[general/color/color-theory-basics]], [[video-editing-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# DaVinci Resolve 高级调色

## 6 模块节点树模板 (可保存为 Power Grade)

```
Block 1: INPUT & TECH CHECKS (Serial)
    └── 确认色彩管理、曝光、白平衡

Block 2: PRIMARY GRADE (Serial)
    └── Lift/Gamma/Gain 或 Offset+Contrast

Block 3: SECONDARIES & KEYS (Parallel)
    └── 肤色/天空/植物等局部调整 (并行)

Block 4: CREATIVE LUT (Serial)
    └── LUT 在调色后套用, 强度 50-70%

Block 5: TEXTURE & OPTICS (Parallel / Layer Mixer)
    └── Glow / Halation / Grain / 局部锐化

Block 6: OUTPUT (Serial)
    └── 限幅, 确认示波器, 输出色彩空间
```

## 二级调色核心工具

| 工具 | 用途 | 操作 |
|------|------|------|
| **HSL Qualifier** | 按颜色范围选取 | 吸管点目标颜色 → 调整 Hue/Width 范围 |
| **Luma Qualifier** | 按亮度范围选取 | 选取高光/阴影区域 |
| **Power Window** | 几何遮罩 | 椭圆/矩形/多边形 + 跟踪 |
| **Magic Mask** | AI 主体分离 | 自动检测人物/物体 (Resolve 18+) |
| **HDR Wheels** | 分色调范围调整 | 高光/中间调/阴影各自独立调 |
| **Color Warper** | 网格变形 | Hue/Sat/Luma 网格精确调整 |

## Parallel vs Layer Mixer (关键区别)

```
Parallel Mixer:
  ┌─────────┐   ┌─────────┐
  │ 肤色提亮  │   │ 天空压暗  │  ← 独立处理, 等权重混合
  └────┬────┘   └────┬────┘
       └──────┬──────┘
          输出

Layer Mixer:
  ┌─────────┐  ← 最低优先级
  ├─────────┤
  ├─────────┤
  ├─────────┤
  ├─────────┤  ← 最高优先级 (覆盖上面所有)
  └─────────┘

  右键节点 → "Morph Into Layer/Parallel Mixer Node" 切换
```

**选择规则**: 
- 多个二级调整互不重叠 → Parallel
- 需要某个调整覆盖另一个 → Layer Mixer (底部优先)
- 需要用 Composite Mode (Overlay/Screen/Multiply) → Layer Mixer

## Key Routing (跨节点传递遮罩)

```
问题: 经过大量风格化后 (低饱和/高对比), 无法准确提取肤色 Key
方案:
  [Node 1] 一级校色 (干净) ──── RGB ──→ [Node 6] 从这里提取 HSL 肤色 Key
       │                                    │
       └── [Node 2] → [Node 3] → [Node 4]  │ (风格化链)
                    └── [Node 5] ── Key Input ←┘ (用 Node 6 的 Key 限定调整范围)
```

**操作**: 右键 Node 6 → Key Output 连接到 Node 5 的 Key Input

## 常用曲线效果

| 曲线 | 效果 | 示例 |
|------|------|------|
| **Hue vs Hue** | 改色相 | 蓝天偏青、绿植偏黄 |
| **Hue vs Sat** | 改特定色饱和度 | 降肤色以外饱和度 |
| **Hue vs Lum** | 改特定色亮度 | 压暗蓝天 |
| **Luma vs Sat** | 按亮度降饱和 | 阴影降饱和 (去死黑偏色) |
| **Custom Curves** | Luma 微调 | 限幅后的暗部提亮 |

## 纹理与修饰效果 (起始参数)

| 效果 | 设置 | 说明 |
|------|------|------|
| **Glow/Diffusion** | Threshold 高于肤色高光, Blend 10-20% | 柔化高光, 增加"体积感" |
| **Halation** | 小 radius, 限制在暖光区域, Mix <10% | 光周围微红晕, 模拟胶片 |
| **Grain** | 35-50mm 细颗粒, Opacity 12-20% | 打破数字"塑料感", 天空区域降低 |
| **局部锐化** | 仅中间调细节, 避开高光和阴影 | 不要用全局 Sharpen 滑块 |

## 实用技巧

1. **示波器 > 眼睛**: 不同显示器颜色不同, 用 Waveform/Parade/VectorScope 判断
2. **肤色线**: VectorScope 上肤色沿 -5° 到 +15° 线
3. **Outside Node** (Alt+O): 选中已有 Key 的节点 → 自动创建去反选区域的节点
4. **Key Mixer**: 多个 Key 的加减运算 (天空 + 水面 - 高光过曝区)
5. **Groups**: 多镜头统一调色 → Post-Clip Group 加整体风格, Clip Group 做个体微调

## 文件保存

- **Power Grade**: 右键节点树 → "Save as Power Grade" → 可拖到任何项目复用
- **Still**: 右键预览画面 → "Grab Still" → 保存该帧的所有调色数据到 Gallery
- **LUT**: 节点树 → 右键 → "Generate LUT" (导出为 .cube 文件)
