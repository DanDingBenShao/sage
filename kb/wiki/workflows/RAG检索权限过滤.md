---
title: RAG检索权限过滤
description: 从抖音视频提取。作者: 小哲讲面经。类型: workflow
type: workflow
domain: [software-dev]
source: human-curated
source_detail: [https://www.douyin.com/video/7649049443420998964]
related: [[video-source-douyin-dbfda0b83b0f]]
tags: [RAG, 权限过滤, 检索安全]
created: 2026-06-09
updated: 2026-06-09
confidence: medium
---

## RAG检索权限过滤流程
### 来源: [33.7s-45.6s]
权限要在召回前过滤，索引里保存ACL标签，召回后再做一次校验，防止索引延迟。不要让模型先看到无权内容再自觉不说。

---

- **来源**: [阿里三面：Agent权限隔离八连问 准备面试大厂AI岗？今天分享阿里三面常考的Agent系统权限隔离问题。视频详细盘点了](https://www.douyin.com/video/7649049443420998964) | **作者**: 小哲讲面经
- **提取时间**: 2026-06-09 | **置信度**: medium
