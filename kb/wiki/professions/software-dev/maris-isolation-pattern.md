---
title: Maris 参考监控器 — 多Agent消息流信息隔离
description: >
  AutoGen上的隐私增强范式：5种消息流（Agent间/群组/LLM/工具/用户）×
  Data Safeguard Engine × Data Protection Manifest。local LLM检测敏感数据，
  非关键词匹配。精确率97.2%。本项目信息隔离层直接借鉴此模式。
type: concept
domain: [software-dev]
related: [[ai-code-factory-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
source: web-searched
source_detail:
  - https://ar5iv.labs.arxiv.org/html/2510.12803
---

# Maris 参考监控器模式

**论文**: "Safeguard-by-Development" (arXiv:2505.04799, May 2025)

## 核心架构

### Data Protection Manifest（策略定义）

JSON格式，定义每条消息流的规则：
- `message_source` / `message_destination` — 消息的起点和终点
- `disallow_data` — 禁止传输的数据项 ["hidden_test_data", "upstream_code", ...]
- `pet_action` — 检测到违规时的动作：block（阻断）/ mask（遮盖）/ warning（告警）

### Data Safeguard Engine（运行时执行）

两个子模块：
1. **Conversation Handler** — 在5种消息流中嵌入hook：
   - Agent Transition Handler（agent间send）
   - Group Message Handler（广播/路由）
   - Environment Interaction Handler（LLM调用/工具调用/用户输入）
2. **Manifest Enforcer** — 用local LLM检测敏感数据（能识别改写和上下文隐含的泄露，不是关键词匹配），然后执行 pet_action

## 性能

- 精确率: 97.2%
- 召回率: 93.4%
- 延迟: <1分钟（平均）

## 在本项目中的应用

```
上游 → [隔离Guard] → 子Agent
         ↑
    Data Protection Manifest:
    - disallow_data: ["hidden_test_data", "upstream_code", "other_agents_work"]
    - pet_action: "block"
    - message_source: "orchestrator"
    - message_destination: "sub_agent_*"
```

简化版实现（不依赖AutoGen）：
```javascript
// isolation-guard.cjs
function sanitizeMessage(message, manifest) {
  for (const rule of manifest.rules) {
    if (matchFlow(message, rule)) {
      for (const item of rule.disallow_data) {
        if (containsPattern(message.content, item)) {
          return { action: rule.pet_action, blocked: item };
        }
      }
    }
  }
  return { action: 'pass' };
}
```

## 与其他概念的关系

- **SplitAgent**：更重型的方案（企业-云端分割+差分隐私），本项目不需要那么重
- **租户隔离（Silo/Bridge/Pool）**：数据库层面隔离，Maris是消息流层面，两者互补
- **OWASP LLM06:2025**：明确指出"不能信任LLM做隔离"，必须在LLM之前的中间件层执行
