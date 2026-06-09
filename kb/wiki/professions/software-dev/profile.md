---
title: 软件开发工程师
description: AI Agent 安全、权限隔离、沙箱执行、多LLM集成、测试工具。加载此职业即可获得软件工程师视角的全部知识。
type: profession
domain: [software-dev]
source: human-curated
created: 2026-06-09
updated: 2026-06-09
confidence: medium
---

# 软件开发工程师 (Software Developer)

## 职业概述

软件开发工程师负责设计、开发、测试和维护软件系统。本知识库聚焦于AI安全、权限隔离、沙箱执行、测试工具以及竞赛编程等专业领域，涵盖从架构设计到部署运维的实践知识。

## 知识领域

### AI安全与权限
- [[agent-permission-isolation-layers]] — Agent权限隔离层设计
- [[permission-isolation-layers]] — 权限隔离层通用模式
- [[multi-agent-permission-propagation]] — 多Agent权限传播
- [[multi-agent-permission-cn]] — 多Agent权限（中文）
- [[tool-permission-modeling]] — 工具权限建模
- [[tool-permission-modeling-cn]] — 工具权限建模（中文）
- [[prompt-injection-prevention]] — 提示注入防护
- [[prompt-injection-prevention-cn]] — 提示注入防护（中文）

### 缓存安全
- [[cache-security-requirements]] — 缓存安全需求
- [[cache-security-cn]] — 缓存安全（中文）

### 跨租户数据泄露
- [[cross-tenant-data-leak-response]] — 跨租户数据泄露响应
- [[cross-tenant-leak-response-cn]] — 跨租户数据泄露响应（中文）

### RAG与检索
- [[rag-retrieval-permission-filtering]] — RAG检索权限过滤
- [[rag-permission-filtering-cn]] — RAG权限过滤（中文）

### 沙箱与执行
- [[windows-sandbox-exec]] — Windows沙箱执行
- [[maris-isolation-pattern]] — Maris隔离模式

### 测试与竞赛编程
- [[testlib-h]] — Testlib.h测试库
- [[ioi-problem-conf]] — IOI问题配置

### 插件开发
- [[vcp-plugin-dev]] — VCP插件开发

### 多LLM集成
- [[multi-llm-ensemble-split]] — 多LLM集成与拆分

### AI代码工厂
- [[ai-code-factory-pipeline]] — AI代码工厂流水线

## 通用知识引用

本职业目前未直接引用通用知识文件，但以下通用领域可能相关：
- [[general/color/color-theory-basics]] — 用于UI/UX设计
- [[general/audio/audio-loudness-standards]] — 用于多媒体应用
- [[general/video/video-pacing-rhythm]] — 用于视频处理应用
- [[general/video/video-transitions-guide]] — 用于视频处理应用

## 子专业方向

- **AI安全工程师 (AI Security Engineer)** — 专注于Agent权限、提示注入防护
- **后端安全工程师 (Backend Security Engineer)** — 专注于缓存安全、跨租户隔离
- **沙箱与隔离工程师 (Sandbox Engineer)** — 专注于执行环境隔离
- **测试工程师 (Test Engineer)** — 专注于测试库与竞赛编程工具
- **插件开发工程师 (Plugin Developer)** — 专注于VCP等插件开发
- **AI集成工程师 (AI Integration Engineer)** — 专注于多LLM集成与代码工厂

## 知识地图

| 文件 | 描述 |
|------|------|
| [[agent-permission-isolation-layers]] | Agent权限隔离层设计模式 |
| [[permission-isolation-layers]] | 通用权限隔离层架构 |
| [[multi-agent-permission-propagation]] | 多Agent间权限传播机制 |
| [[multi-agent-permission-cn]] | 多Agent权限中文版 |
| [[tool-permission-modeling]] | 工具权限建模方法 |
| [[tool-permission-modeling-cn]] | 工具权限建模中文版 |
| [[prompt-injection-prevention]] | 提示注入攻击防护策略 |
| [[prompt-injection-prevention-cn]] | 提示注入防护中文版 |
| [[cache-security-requirements]] | 缓存安全需求文档 |
| [[cache-security-cn]] | 缓存安全中文版 |
| [[cross-tenant-data-leak-response]] | 跨租户数据泄露应急响应 |
| [[cross-tenant-leak-response-cn]] | 跨租户数据泄露响应中文版 |
| [[rag-retrieval-permission-filtering]] | RAG检索中的权限过滤 |
| [[rag-permission-filtering-cn]] | RAG权限过滤中文版 |
| [[windows-sandbox-exec]] | Windows沙箱执行配置 |
| [[maris-isolation-pattern]] | Maris隔离模式实现 |
| [[testlib-h]] | Testlib.h测试库使用指南 |
| [[ioi-problem-conf]] | IOI竞赛问题配置 |
| [[vcp-plugin-dev]] | VCP插件开发教程 |
| [[multi-llm-ensemble-split]] | 多LLM集成与拆分策略 |
| [[ai-code-factory-pipeline]] | AI代码工厂流水线设计 |