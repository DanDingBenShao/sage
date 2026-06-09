---
title: AI代码工厂 — 需求拆分→静态库→IOI判题→多Agent验证流水线
description: >
  将自然语言需求拆分为多个独立静态库，每个库生成预测试和隐藏测试数据，
  打包为IOI题目分发给子Agent。子Agent仅见预测试数据，通过后上游用隐藏测试验收。
  后端VCPToolBox做通信，复用ComFlow核心组件（agent-loop/agent-harness等约20文件）。
type: workflow
domain: [software-dev]
related: [[vcp-plugin-dev]], [[ioi-problem-conf]], [[testlib-h]], [[windows-sandbox-exec]], [[maris-isolation-pattern]], [[multi-llm-ensemble-split]]
created: 2026-06-09
updated: 2026-06-09
confidence: medium
decomposition_depth: 0
is_atomic: false
prerequisites:
  - { entry: "tools/vcp-plugin-dev.md", source: "WebSearch+WebFetch", confidence: medium }
  - { entry: "tools/ioi-problem-conf.md", source: "WebSearch", confidence: high }
  - { entry: "tools/testlib-h.md", source: "WebSearch", confidence: high }
  - { entry: "tools/windows-sandbox-exec.md", source: "WebSearch", confidence: medium }
  - { entry: "concepts/maris-isolation-pattern.md", source: "WebSearch", confidence: medium }
  - { entry: "concepts/multi-llm-ensemble-split.md", source: "WebSearch", confidence: medium }
---

# AI代码工厂流水线

## 项目概述

**一句话**：需求→自动拆成静态库→生成双轨测试数据→IOI打包→多子Agent并行实现→预测试自检→隐藏测试验收→合并入库。

**核心价值**：并行（快）、自动化（省人）、不可作弊（可信）。

**技术选型**：VCPToolBox（Agent通信基础设施）+ ComFlow核心组件（约20个文件，执行引擎）+ 自建业务层（拆分/测试生成/IOI打包/判题/隔离）。

---

## 为什么这样拆？

1. **复用 vs 重写的边界**：ComFlow的orchestrator→executor→agent-loop链路经过多轮审计和修复，是成熟资产。只替换db.cjs（数据schema）和index.cjs（VCP插件入口），不重写执行引擎。
2. **VCPToolBox的定位**：不做业务逻辑，只做通信+记忆+插件分发。VCPToolBox没有判题/沙箱/IOI打包能力，这些必须自建。
3. **拆分的顺序**：先接口（.h）→再并行生成测试+分发。如果先拆需求再定义接口，接口可能循环依赖，需要回溯。
4. **沙箱选型被平台限制**：IOI标准isolate只支持Linux。用户的开发环境是Windows。Windows下选项按推荐度：Chromium Sandbox（C++库，15年验证）> MXC（微软新项目）> Windows Sandbox VM（需Pro版）。

---

## 分解树

```
根：AI代码工厂流水线
│
├── 1. 项目骨架搭建
│   ├── 1.1 目录结构 [原子]
│   ├── 1.2 从ComFlow复制核心组件 → lib/ [原子]
│   ├── 1.3 新db schema [需完备化: VCPToolBox数据存储方式]
│   └── 1.4 VCP插件入口 [需完备化: VCP synchronous插件开发]
│
├── 2. 需求拆分引擎
│   ├── 2.1 LLM拆分prompt工程 [需完备化]
│   ├── 2.2 C/C++ .h接口生成 [需完备化]
│   ├── 2.3 依赖DAG分析 [原子]
│   └── 2.4 Multi-LLM Ensemble验证 [需完备化]
│
├── 3. 测试数据生成器
│   ├── 3.1 预测试数据（公开）[需完备化: CodeContests+ G-V模式]
│   ├── 3.2 隐藏测试数据（私密）[需完备化: 无泄露生成策略]
│   ├── 3.3 std.cpp参考实现 [原子]
│   └── 3.4 testlib.h validator+checker [需完备化]
│
├── 4. IOI打包器
│   ├── 4.1 problem.conf [需完备化: 完整配置规范]
│   ├── 4.2 implementer.cpp [原子]
│   ├── 4.3 目录打包 [原子]
│   └── 4.4 子Agent分发包 [原子]
│
├── 5. 信息隔离层 ★关键★
│   ├── 5.1 消息过滤器 [需完备化: Maris参考监控器模式]
│   ├── 5.2 上下文隔离 [原子]
│   ├── 5.3 分发清单 [原子]
│   └── 5.4 审计日志 [原子]
│
├── 6. 子Agent执行环境
│   ├── 6.1 沙箱 [需完备化: Windows C++安全执行]
│   ├── 6.2 编译工具链 [原子]
│   ├── 6.3 预测试运行器 [原子]
│   └── 6.4 提交收集器 [原子]
│
├── 7. 判题系统
│   ├── 7.1 编译沙箱 [原子]
│   ├── 7.2 运行时限制 [需完备化: 时空强制执行]
│   ├── 7.3 输出比对 [原子]
│   └── 7.4 结果汇总 [原子]
│
├── 8. VCPToolBox集成
│   ├── 8.1 插件注册 [需完备化]
│   ├── 8.2 Agent消息路由 [需完备化]
│   ├── 8.3 记忆隔离 [需完备化]
│   └── 8.4 分布式节点 [需完备化]
│
└── 9. 流水线编排（复用orchestrator.cjs）
    ├── 9.1 DAG定义 [原子]
    ├── 9.2 并行执行 [原子]
    ├── 9.3 失败处理 [原子]
    └── 9.4 最终集成 [原子]
```

---

## Phase 2: 知识完备化 状态

总计 [需完备化] 节点: 16 个

### 已完备化 ✅

1. **testlib.h** (节点 3.4) — Generator/Validator/Checker 完整API已搜到。`rnd.next()` 系列、`inf.readInt()`、`ouf.readInt()`、`quitf(_wa/_ok)` 等核心API明确。来源：Codeforces官方文档。confidence: high

2. **IOI problem.conf** (节点 4.1) — 完整配置项已搜到：`use_builtin_judger`、`n_tests`、`n_ex_tests`、`n_sample_tests`、`input_pre/suf`、`output_pre/suf`、`time_limit`、`memory_limit`、`full_score`、subtask配置（`subtask_end_N`、`subtask_score_N`、`subtask_type_N`、`subtask_dependence_N`）、`token`反作弊。来源：QOJ配置文档+IOI官方。confidence: high

3. **Windows沙箱执行** (节点 6.1) — 7个方案评估完成。推荐Chromium Sandbox（C++库，15年生产验证，MIT许可，无需管理员权限）+ Windows Sandbox VM备选。来源：Chromium官方文档+微软MXC GitHub。confidence: medium

4. **Maris参考监控器** (节点 5.1) — 5种消息流+Data Safeguard Engine+Data Protection Manifest+local LLM检测（非关键词匹配）。精确率97.2%，召回93.4%。来源：arXiv 2505.04799。confidence: high

### 待完备化（因搜索枯竭降级为假设）

5. **VCPToolBox数据存储方式** (节点 1.3) — VCPToolBox内部使用Rust SQLite+USearch。本项目可以继续用sql.js（与ComFlow相同）或直接文件系统存储。**假设：不嵌入VCPToolBox存储，独立建sql.js数据库，通过VCP插件stdio协议交互。** confidence: low

6. **VCP synchronous插件开发** (节点 1.4, 8.1) — 基础流程已知（plugin-manifest.json + stdio JSON通信 + PluginManager自动发现）。但无完整示例代码。**假设：按已知文档实现。** confidence: medium

7. **VCP AgentAssistant消息路由** (节点 8.2) — 确认存在Agent间通信能力但API细节不可得。**假设：通过VCP stdio协议传递目标Agent ID，自行在插件层实现路由。** confidence: low

8. **VCP记忆隔离** (节点 8.3) — VCP有per-Agent记忆分区但API未公开。**假设：不使用VCP记忆系统，独立在ComFlow的scope-manager.cjs+session.cjs层做隔离。** confidence: low

9. **VCP分布式节点** (节点 8.4) — VCPDistributedServer存在但集成文档不可得。**假设：MVP阶段不用分布式，所有子Agent在同一台机器上通过独立沙箱进程隔离。** confidence: low

10. **LLM需求拆分prompt** (节点 2.1) — 搜索结果显示单模型召回率仅0-52%，需要Multi-LLM Ensemble。**方案：3模型（DeepSeek+Claude+GPT）并行拆分+Meta-LLM融合，目标召回>75%。** confidence: medium

11. **CodeContests+ G-V模式** (节点 3.1) — Generator写testlib.h C++程序→Validator校验约束→以不同seed运行→生成多样化测试。**方案：适配此模式，Generator生成testlib.h代码而非直接生成测试数据。** confidence: high

12. **无泄露生成策略** (节点 3.2) — 这是本项目最核心的原创问题，搜索未发现直接解决方案。**方案：用不同LLM+不同seed+不同策略生成预测试和隐藏测试，再加相似度检测（输入分布重叠率）确保两者无信息泄露。** confidence: low

---

## 架构图

```
┌──────────────────────────────────────────────────────────┐
│  ComFlow 上游编排层 (复用 orchestrator + executor)         │
│                                                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐  │
│  │需求拆分   │  │测试生成    │  │IOI打包    │  │上游判题 │  │
│  │splitter  │  │generator  │  │packager  │  │judge   │  │
│  └──────────┘  └───────────┘  └──────────┘  └────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 信息隔离层 (isolation-guard) ★                    │    │
│  │ - 只下发 .h + pre_test + 题目描述                  │    │
│  │ - 拦截隐藏测试数据                                  │    │
│  │ - 子Agent互不可见                                  │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────┬───────────────────────────────────┘
                       │ VCP插件协议 (stdio JSON)
                       ▼
┌──────────────────────────────────────────────────────────┐
│  VCPToolBox (Agent 通信基础设施)                          │
│  - AgentAssistant: 消息路由                               │
│  - PluginManager: 插件加载                                │
│  - 不参与业务逻辑                                         │
└──────┬──────────────────────┬────────────────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐      ┌──────────────┐
│ 子Agent沙箱 1 │      │ 子Agent沙箱 2 │  ...
│ (Chromium     │      │ (Chromium     │
│  Sandbox)     │      │  Sandbox)     │
│              │      │              │
│ .h + pre_test │      │ .h + pre_test │
│ → 编码        │      │ → 编码        │
│ → 编译        │      │ → 编译        │
│ → 预测试      │      │ → 预测试      │
│ → 提交 .cpp   │      │ → 提交 .cpp   │
└──────────────┘      └──────────────┘
```

---

## 实施顺序（MVP分阶段）

### Phase A: 骨架 + 单库手动验证（1-2天）
1. 目录初始化 + 从ComFlow复制lib/组件
2. 替换db.cjs为新schema
3. 手动创建一个静态库（lib_example/.h + pre_test + hidden_test）
4. 实现IOI打包器（4.1-4.4）
5. 实现沙箱+预测试运行器（6.1-6.3）
6. 实现判题系统（7.1-7.4）
7. **验证**：手动写一个.cpp → 预测试通过 → 隐藏测试通过

### Phase B: 拆分+测试生成（2-3天）
8. 实现需求拆分引擎（2.1-2.4）
9. 实现测试数据生成器（3.1-3.4）
10. **验证**：给一个真实需求 → 自动拆分 → 自动生成测试 → 手动验证拆分和测试质量

### Phase C: VCPToolBox集成 + 信息隔离（2-3天）
11. 实现VCP插件入口（1.4, 8.1）
12. 实现信息隔离层（5.1-5.4）
13. 实现子Agent消息路由（8.2-8.4）
14. **验证**：通过VCPToolBox分发给子Agent → 子Agent编码 → 预测试 → 提交 → 上游判题

### Phase D: 并行 + 编排（1-2天）
15. 流水线编排（9.1-9.4）
16. **验证**：一次需求 → 自动拆N个库 → N个子Agent并行 → 全部通过 → 合并

---

## 关键风险

| 风险 | 等级 | 缓解策略 |
|------|------|---------|
| VCPToolBox API不透明，集成遇阻 | 🔴高 | MVP阶段VCP只做stdio通信，不做深度集成；备选方案：绕过VCP直接用ComFlow自己的ws.cjs |
| 需求拆分质量不达标 | 🟡中 | 先用人工拆分的典型案例做few-shot，再逐步自动化；Multi-LLM Ensemble提升召回 |
| 隐藏测试数据泄露给预测试 | 🟡中 | 不同LLM+不同seed生成两套数据，加输入分布相似度检测 |
| Windows沙箱安全性不足 | 🟡中 | Chromium Sandbox + 网络禁用 + 文件系统只读 + 资源限制多层防护 |
| 子Agent修复循环断裂（看不到隐藏测试数据无法debug） | 🟡中 | 只做判定不做修复；失败后重新分发或由上游做代码diff分析后生成引导性反馈 |
