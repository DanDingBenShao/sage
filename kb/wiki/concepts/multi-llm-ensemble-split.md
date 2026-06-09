---
title: Multi-LLM Ensemble 需求拆分
description: >
  单LLM需求拆分的召回率仅0-52%，用3+模型并行拆分+Meta-LLM融合可达75%+召回。
  本项目需求拆分引擎的核心策略。
type: concept
domain: [software-dev]
related: [[ai-code-factory-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: medium
source: web-searched
source_detail:
  - https://conf.researchr.org/details/ase-2025/ase-2025-nier-track/13/
  - https://ieeexplore.ieee.org/document/11334724
---

# Multi-LLM Ensemble 需求拆分

## 问题

ASE 2025 论文 "Detecting and Repairing Incomplete Software Requirements with Multi-LLM Ensembles" 发现：
- 单LLM检测缺失需求的召回率：**0-52%**
- 3-LLM Ensemble的召回率：**75%+**（最高100%）
- 建议合理性：**95-100%**

## 方案

```
需求文档
  ├── DeepSeek → 拆分方案A（.h 接口列表 + 依赖关系 + 功能描述）
  ├── Claude   → 拆分方案B
  └── GPT      → 拆分方案C
         ↓
    Meta-LLM 融合
    - 多数投票：3个中至少2个同意才定义一个接口
    - 冲突仲裁：GPT-4o 做最终裁决
    - 完整性检查：是否覆盖了需求文档的所有功能点？
         ↓
    最终拆分方案（.h 文件列表 + DAG）
```

## 融合策略

| 策略 | 说明 | 适用 |
|------|------|------|
| 多数投票 | 2/3 模型同意才保留 | 接口存在性判定 |
| 加权投票 | Claude/DeepSeek/GPT 权重不同 | 接口设计细节 |
| Meta-LLM | 由第4个模型做最终裁决 | 冲突解决 |
| 人工审核 | 最终结果由人确认 | MVP阶段 |

## Prompt 模板（初版）

```
你是一个C/C++软件架构师。请将以下需求拆分为独立编译的静态库。
每个库应：
1. 只暴露一个 .h 头文件作为公共接口
2. 可以被独立实现和测试
3. 接口正交，与其他库无循环依赖

对每个库，输出JSON格式：
{
  "name": "库名",
  "header": "接口声明（C语言风格）",
  "description": "功能描述（给实现者看的题目描述）",
  "dependencies": ["依赖的库名列表"],
  "test_hints": ["应该测试的关键场景"]
}

需求文档：
<REQUIREMENT>
```
