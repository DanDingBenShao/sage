---
title: Wiki Schema
type: meta
version: 2.0
updated: 2026-06-09
---

# Wiki Schema

> 知识库的"宪法"。AI agent 每次操作前读此文件。v2.0 引入三层结构（按使用者组织）。

## 三层结构

知识按 **谁在使用它** 分为三层，而非按知识类型分类：

```
general/          — 跨职业通用基础。仅当被 2+ 职业引用时存入。
professions/      — 职业专属知识。每个职业一个目录，profile.md 为入口。
projects/         — 项目特定上下文。引用上两层。
```

### general/ — 通用知识

- 条件：至少被 2 个职业使用
- 子目录按主题：`audio/` `color/` `video/` `standards/`
- 内容必须是可独立理解的（不需要职业上下文）
- type: `concept` | `tool` | `standard`

### professions/ — 职业节点

- 每个职业一个目录（如 `video-editor/`）
- 必须含 `profile.md` 作为入口：职业概述 + 知识地图 + 子专业方向
- type: `profession`（仅 profile.md）| `concept` | `workflow` | `tool` | `comparison`
- profile.md 声明引用哪些 general/ 知识
- 同一知识可被多个职业引用（物理一份，wikilink 连接）

### projects/ — 项目上下文

- 具体项目的知识，引用 professions/ 和 general/
- 必须含 `profile.md` 作为入口
- type: `project`（仅 profile.md）| `concept` | `workflow` | `tool` | `entity`

## 目录结构

```
wiki/
├── _schema.md          # 本文件
├── _log.md             # 操作日志（只追加）
├── _index.md           # 全局索引
├── rules.md            # 已验证规则
├── false-beliefs.md    # 被证伪的认知
├── general/
│   ├── audio/
│   ├── color/
│   ├── video/
│   └── standards/
├── professions/
│   ├── video-editor/
│   │   ├── profile.md  # ← 入口
│   │   └── *.md
│   └── software-dev/
│       ├── profile.md  # ← 入口
│       └── *.md
└── projects/
    └── sage/
        ├── profile.md  # ← 入口
        └── *.md
```

## 页面类型

| type | 位置 | 适用场景 |
|---|---|---|
| `profession` | `professions/{name}/profile.md` | 职业入口页 |
| `project` | `projects/{name}/profile.md` | 项目入口页 |
| `concept` | 任意层 | 连接多个实体的主题或框架 |
| `workflow` | 任意层 | 任务从入口到原子步骤的完整分解树 |
| `tool` | 任意层 | 具体工具/API/CLI 的使用知识 |
| `comparison` | 任意层 | A vs B 并排比较 |
| `entity` | 任意层 | 需长期跟踪的离散对象 |
| `standard` | general/ | 跨行业标准/规范 |
| `meta` | 根目录 | _schema.md, rules.md, false-beliefs.md |

## Frontmatter 规范

所有 `.md` 页面必须带 YAML frontmatter：

```yaml
---
title: <人类可读标题>
description: <1-2句精确描述，含同义词/别名。Agent 据此判断是否相关。>
type: concept | workflow | tool | comparison | entity | standard | profession | project | meta
domain: [video-production | software-dev | visual-design | business | general | ai-engineer]
source: human-curated | web-searched | self-audited
source_detail: [<URL>]
related: "[[example-page-1]]", "[[example-page-2]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high | medium | low
---
```

`profession` / `project` 类型额外：
```yaml
profession_domain: <职业领域名>
knowledge_map:
  - area: <领域名>
    pages: [[page1]], [[page2]]
```

## Wikilinks

- 同级目录：`[[page-name]]`（省略 .md）
- 跨目录：`[[dir/page-name]]` 或 `[[../dir/page-name]]`
- **双向链接强制**：A 链接 B，B 必须回链 A
- 职业 profile.md 应列出全部页面链接

## 五层结构（按变化速度）

| 层 | 变化频率 | 示例 |
|---|---|---|
| `raw/` | 几乎不变 | PDF、全文、转录稿 |
| `sources/` | 很少变 | 结构化来源摘要 |
| `entities/` `concepts/` | 周到月级 | 档案页、主题页 |
| `explorations/` `decisions/` | 按问题变化 | 固化答案 |
| `rules.md` `false-beliefs.md` | 季度级 | 长期经验总结 |

## 领域定义

| domain | 说明 |
|---|---|
| `visual-design` | 视觉设计：图表规范、图标、排版、色彩、动效 |
| `video-production` | 视频制作：素材、剪辑、调色、音效、导出 |
| `software-dev` | 软件开发：架构、安全、测试、部署 |
| `ai-engineer` | AI工程：模型选择、Agent设计、RAG、prompt |
| `business` | 商业：产品策略、营销 |
| `general` | 跨领域通用 |

---

## Protocol 0 — 递归知识完备化

**最核心协议。任何知识条目写入时，必须先完备化。**

### 核心原则

一个知识条目不能只写自身。必须识别隐含的前置依赖，对每个缺失依赖主动搜索、递归拆分，直到每个子节点达到"模型训练数据已高度覆盖"的程度。

### 执行步骤

1. **显式声明**：将隐含依赖写成明文 → 记录为 prerequisites
2. **检查已知**：搜索 wiki 是否已有 → 有且 confidence ≥ medium 则 wikilink；没有则搜索填补
3. **搜索填补**：WebSearch → WebFetch → 结构化写入
4. **递归**：对新条目执行 Protocol 0
5. **双向引用**：A.prerequisites 含 B → B.related 必须含 A

### 停止条件（满足任一即停）

① **训练数据覆盖阈值**（最优先）：HTTP请求/文件读写/JSON解析/SQL → 标记 is_atomic: true，不写入
② **工具原子性**：具体 CLI + 完整参数 → is_atomic: true
③ **搜索枯竭**：连续 3 次搜索无可靠来源 → 标记 open_question
④ **用户阻断**：用户明确指示不继续

---

## Ingest Protocol（摄入规则）

Ingest 前必须先完成 Protocol 0。

1. 原文放 `raw/`（不可变归档）
2. 创建 `sources/<date>-<slug>.md`
3. 识别实体与概念，更新对应页面；**新建前先征得用户同意**
4. 维护双向 `[[wikilinks]]`
5. 追加一行到 `_log.md`
6. 运行健康检查

## Cross-Reference Protocol（交叉引用）

- 更新 A 的 `related:` 后，必须确认 B 的 `related:` 也含 A
- 识别孤儿页（无入链无出链），主动提醒

## Contradiction Scan（矛盾扫描）

每次写入新判断前：
1. 检查 `false-beliefs.md` — 是否与已证伪认知冲突
2. 检查 `rules.md` — 是否违反现行规则
3. 检查相关页面 — 是否与历史判断矛盾

---

*这份 schema 是人与 AI 之间的契约。修改后建议提交 git。*
