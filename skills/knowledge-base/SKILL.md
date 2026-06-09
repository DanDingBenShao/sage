---
name: knowledge-base
description: >
  Agent 专属知识库。触发：需要将任务强制拆解到原子层并完备化所有前置知识，
  或从已积累的知识库中检索信息。知识库为 Agent 服务，不为人类浏览服务。
argument-hint: "[complete|ask|ingest|lint|report] <输入>"
allowed-tools: [Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep, Agent]
---

# Knowledge Base Agent

你是知识库的自主 Agent。**判断**（质疑、拆解、自审、校验）由你亲自执行。**搜索和初稿**交给 Haiku 子 agent——你输出结构化搜索清单，它填结果回来。

知识库（`D:/TOOLS/cloude code/sage/kb/wiki/`）负责持久化、交叉引用审计和矛盾检测。

## 架构

- **任务 = 域入口**：每个大任务生成一个 workflow 页面，链接所用 tool/concept/comparison。Agent 来找信息时读 `workflows/_index.md` → 顺链接遍历。
- **通用知识 = 侧边储备**：从具体任务中提取跨任务可复用的原理、对比、模式，存入 concepts/、tools/、comparisons/。
- **搜索 = 清单化外包**：你写搜索清单（JSON），Haiku 子 agent 执行，你读结果做判断。搜索逻辑见 `search-protocol.md`。

## 路径

```
知识库根目录: D:/TOOLS/cloude code/sage/kb
Wiki 目录:    D:/TOOLS/cloude code/sage/kb/wiki
```

## 前置加载

每次操作前读取：

1. 本文件 SKILL.md
2. `D:/TOOLS/cloude code/sage/kb/wiki/_schema.md`
3. `D:/TOOLS/cloude code/sage/kb/wiki/_log.md`（最后 50 行）
4. `D:/TOOLS/cloude code/sage/kb/wiki/rules.md`
5. `D:/TOOLS/cloude code/sage/kb/wiki/false-beliefs.md`

---

## 命令 1: complete — 任务强制拆解 + 知识完备化

```
/knowledge-base complete "任务描述"                    # 默认 normal
/knowledge-base complete "任务描述" --depth quick      # wiki 命中多 / 简单任务
/knowledge-base complete "任务描述" --depth deep       # 覆盖率为 0 的新域
```

### 深度级别

| 级别 | 搜索范围 | 发散兜底 | 自审 | 概念提取/对比提升 | 适用 |
|------|---------|---------|------|------------------|------|
| **quick** | 只搜 wiki + 1 轮 WebSearch | 跳过 | Q1-Q3 快速过 | 跳过 | wiki 命中 ≥2 页 / 任务简单 |
| **normal** | wiki + 五维 WebSearch | 3-4 轮开放式 WebSearch | Q1-Q3 完整自审 | 执行，可跳过但写原因 | 新域或 wiki 命中 <2 页 |
| **deep** | normal + 每个 [需完备化] 节点单独五维搜索 | 3-4 轮开放式 WebSearch | Q1-Q3 + 新人路径模拟 | 强制执行 | 覆盖率为 0 的复杂新域 |

> 默认 normal。你自主判断是否升降级——在 Phase 0 输出时写明级别和理由。

### Phase 0: 质疑前提

1. 确认任务范围、产出、domain
2. 量级影响方案 → 追问或显式写假设
3. ★ 反问三个问题（无需搜索）：
   - **方案质疑**：输出形式一定最合适？替代？
   - **流程质疑**：用户描述的流程是最优顺序？
   - **边界质疑**：量级假设、平台假设

**输出**：
```
## Phase 0 质疑结论
- 深度级别：quick / normal / deep（理由：<...>）
- 方案质疑：<X> → 替代：<Y>, <Z>
- 流程质疑：<问题>
- 边界质疑：假设 <N>（用户未说明）
```

### Phase 0.3: 检查已有沉淀

Grep `_log.md` + `workflows/` 关键词。命中 → 读 workflow → 从断点继续。无命中 → 从零开始。

```
## 已有沉淀
- 命中：workflows <M> | concepts/tools <K>
- 决策：从零开始 / 复用已有 / 从断点继续
```

### Phase 0.5: 搜索清单 → Haiku 执行

你输出结构化搜索清单，Haiku 子 agent 执行后返回结果文件。清单格式：

```json
{
  "task": "<任务描述>",
  "depth": "quick|normal|deep",
  "searches": [
    {"domain": "wiki", "grep": "<关键词，| 分隔>", "dim": "<维度名>"},
    {"domain": "web",  "q": "<WebSearch query>", "dim": "<维度名>", "reason": "<搜这个想验证什么>"}
  ]
}
```

Haiku 子 agent 会：
1. 按清单 grep wiki → 读 frontmatter → 判决相关性
2. WebSearch 搜外网 → 1-2 篇 WebFetch 最权威的
3. 写结果到临时文件

你 Read 结果文件后，汇报颠覆性发现（标记 `⚠ DISRUPTIVE`），进入 Phase 0.6。

> quick 级别跳过此阶段——直接用已有沉淀结果。

### Phase 0.6: 发散搜索兜底 ★

**目的**：清单搜索被你的先验知识框住——你不知道自己不知道什么。发散搜索用开放式 query 突破这个边界，捕捉清单漏掉的替代方案、反模式、边界案例。

**做法**（你亲自执行，不外包 Haiku）：

1. 以"开发者闲聊/论坛灌水"的视角，发 **3-4 轮开放式 WebSearch**——不问具体维度，问"还有什么"：
   - `"<主题> best practice anti-pattern common mistakes 2024"`
   - `"<主题> alternative approach vs 对比方案 tradeoff"`
   - `"<主题> race condition edge case production experience"`
   - `"<主题> what's new changed deprecated 2024 2025"`
2. 对比搜索结果与 Phase 0.5 已有发现，标记：
   - `🆕 NEW` — 清单完全没覆盖的知识
   - `⚠ CONFLICT` — 与已有认知冲突的观点
   - `🔺 DEEPER` — 已有但可以深挖的子话题
3. 输出发散发现清单（分类 + 动作），然后进入 Phase 1

```
## Phase 0.6 发散发现
- 🆕 <发现1> → 将在 Phase 2 完备化
- 🆕 <发现2> → 纳入已有页 [[xxx]] 增强
- ⚠ CONFLICT: <来源A说X，来源B说Y> → Phase 4 矛盾扫描重点
- 🔺 DEEPER: <话题> → 已有但需深挖
无新发现则写"本轮发散无增量"
```

> 最低要求：即使发散无增量，也必须执行搜索并写结论。跳过此阶段仅限 quick 级别。

### Phase 1: 任务拆解

递归拆到原子操作。反复问："这还能进一步拆分吗？"

- 先拆成"需要什么能力"，不要直接跳到具体工具
- 每个一级分支标注替代方案检查
- 横向搜索未发现替代 → 标注 `[替代方案：搜索未发现，当前路径最优]`

**停止条件**：通用编程操作（HTTP/文件读写/JSON/SQL）→ `[原子]`；具体 CLI + 完整参数 → `[原子]`；否则 → `[需完备化]`。

**输出**：树状结构，叶子标注 `[原子]` 或 `[需完备化]`。

### Phase 2: 知识完备化

一次只处理一个 `[需完备化]` 节点，该节点及子树全部完成（含自审）才能进下一个。

列出所有 [需完备化] 节点清单。每完成一个 ✅。

**对每个节点**：

**搜** — **deep 级别**每个节点单独搜索清单 → Haiku 执行。**normal/quick 级别**直接引用 Phase 0.5 结果，不重搜：

```json
{
  "node": "<节点名>",
  "task": "<原始任务>",
  "domain": "<domain>",
  "tree_context": { "parent": "<父节点>", "siblings": [...] },
  "existing_pages": ["[[已有页]]"]
}
```

**增** — 已有页面不足 → WebSearch 补全 → Edit 写入 → Read 回 → 自审。

**写** — 按"页面写入规范"写 frontmatter + 正文，`confidence: pending`。初稿可由 Haiku 代写（提交页面内容 + frontmatter 规范作为 prompt），但你（Opus）必须自审。

**★ 自审**（不可跳过）— Read 读回全文，逐段问：
- Q1: "提到读者不知道的东西了？" → 隐含依赖 → 回去补
- Q2: "有没有漏掉什么？" → 五维检查（工具/流程/概念/方案/环境）
- Q3: "新人拿着这个页面干活，会在哪里卡住？" → 卡住处 = 缺口

全通过后 confidence → high/medium/low。全秒答"没有" → 反问自己是否敷衍。

**交叉引用** — A 引用 B → B 的 related 加 A。

**★ 概念提取**（quick 跳过）— tool 页每段："是什么/为什么"且跨 tool 能用？→ 提取。本轮无提取写原因。

**★ 对比提升**（quick 跳过）— ≥3 工具对比 或 ≥2 对立方案？→ 提升为 comparisons/。本轮无提升写原因。

**停止条件**：训练数据覆盖 | 工具原子性 | 连续 3 次搜索无可靠来源 → `open_question`

### Phase 3: 写入 workflow + 索引

按页面写入规范写 workflow 页。写完 **必须** 追加 `workflows/_index.md` 一行索引——关键词列覆盖同义词。

### Phase 4: 校验

1. **矛盾扫描**：与 false-beliefs.md、rules.md、已有页面冲突？
2. **固化提议**：2+ 来源 + 可复用 → 提议 explorations/；无则说"本轮无"
3. **日志**：_log.md 追加一行
4. **健康检查**（执行命令，不是想一遍）：
   - 断链、description 覆盖率、confidence pending 残留
5. **多维度对比**：工具/方案/流程/环境/新手路径

### Phase 5: 汇报

```
✅ 拆解完成 — 深度 N 层，M 个原子叶子 | 深度级别: quick/normal/deep

搜索成本：Haiku 子 agent × N 次（Wiki grep + WebSearch + 写结果文件）
Opus 轮次：质疑 → 拆解 → 自审 × K → 校验（共 K+3 轮）

自审：发现 P 个缺口
  · [[page1]] — X 缺失 → 补 Y

新页面：K 个 | 交叉引用：Z 条 | open_question：W 个

Wiki 快照：总 N 页 | 热点(≥3入链) A | 冷页(0入链) B
```

> 自审发现 0 个缺口 = 红旗。重新检查是否敷衍。

---

## 命令 2: ask — 从知识库检索

```
/knowledge-base ask "查询"
```

### 步骤

**Step 1: 域定位**
读 `workflows/_index.md` → 关键词匹配行 → 有命中则读对应 workflow 页摘要（frontmatter + 分解树第一层）。

**Step 2: Frontmatter grep（非全文）**
在 wiki/ 目录 grep 关键词，但**只搜 frontmatter 区域**（`---` 到 `---` 之间的 title、description、related 三行），不搜正文。这样排除"正文碰巧提到这个词"的噪声页。

```bash
# 示例：用 awk 截取 frontmatter 再 grep
find wiki/ -name '*.md' -exec awk '/^---$/{f++;next} f==1' {} \; | grep -i "<关键词>"
```

或者直接用 Grep 工具，`pattern: "关键词"`, `path: wiki/`, 但只匹配 `.md` 文件中位于 `^---$` 边界内的行。

**为什么只搜 frontmatter？** 
- `title` + `description` + `related` 已经精准描述了这个页面是什么
- 正文里有大量"技术术语路过"（比如所有安全页面都提到 "token"，但只有 JWT 页面是关于 token 的）
- 搜索面缩小 10x，命中相关度大幅提高

**Step 3: 分层返回**

| 命中数 | 策略 |
|--------|------|
| 1-2 页 | 直接返全文——页少，不等了 |
| 3-5 页 | 先返 frontmatter 摘要（title + description + confidence + sections）→ 等 Agent 说"读 XX 页"再返全文 |
| 6+ 页 | 返 frontmatter 摘要 + 主动标注最相关的 Top 3 → 问 Agent "读哪几个？" |

**Step 4: 兜底**
wiki 0 命中 → 直接 WebSearch，返回结果时标注"知识库未覆盖"。

### 输出格式

```
## 检索结果：<查询>

### 知识库命中（N 页）
- [[page1]] — <description> — confidence: high | [读全文]
- [[page2]] — <description> — confidence: medium | [读全文]

### 前置依赖
- [[prereq1]] — <description>

### 知识缺口
- <未覆盖的主题> → 建议 /knowledge-base complete
```

> Agent 回复 "读 [[page1]] [[page2]]" 后你再 Read 返回全文。

---

## 命令 3: ingest — 人工精选知识入库

```
/knowledge-base ingest "内容描述" --source-url "https://..."
```

1. **确认来源**：URL、类型、摘要
2. **结构化写入**：`source: human-curated`（固定），`confidence: pending`
3. **提取隐含依赖**：Q1-Q3 自审 → 未覆盖概念写入 `open_question`（不自动补全）
4. **自审 + 交叉引用 + 日志**

---

## 命令 4: lint — 健康检查

```
/knowledge-base lint
```

1. Grep `[[` → 断链
2. Grep `confidence: low` → 占位页
3. root meta 文件更新时间

---

## 命令 5: report — 注意力报告

```
/knowledge-base report
```

1. 每页入链数统计
2. god nodes（入链 Top 10）
3. 孤儿页（0 入链 + 0 出链）
4. domain 分布

---

## 页面写入规范

### Frontmatter 必填

```yaml
---
title: <标题>
description: >
  <1-2 句。Agent 仅凭 frontmatter 判断是否相关。
  写清：1) 这是什么 2) 什么时候用>
type: concept | tool | workflow | entity | source-summary | exploration | decision | comparison | meta
domain: [visual-design | video-production | software-dev | business | general]
source: human-curated | web-searched | self-audited
source_detail: [<URL>]
related: [[p1]], [[p2]]
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: pending | high | medium | low
---
```

### 来源层级

| source | 含义 | 行为 |
|--------|------|------|
| `human-curated` | 人筛选的高质量内容 | 优先引用，不覆盖 |
| `web-searched` | AI 搜索总结 | 正常引用，可增强 |
| `self-audited` | 自审缺口补全 | 正常引用 |

### Description

- 1-2 句，≤50 字
- 含：(1) 内容精确描述 (2) 什么场景用 (3) **同义词/别名**——Agent 用不同词搜也能命中
- ✗ "介绍了 ffmpeg 用法"
- ✓ "ffmpeg palettegen/paletteuse 两 pass 转 GIF，含 gifski 对比、体积优化。录屏转动图时用。"

### Wikilinks

- `[[page-name]]`，不含 `.md`，双向链接强制

### 置信度

| 级别 | 条件 |
|------|------|
| pending | 已写但自审未过 |
| high | 2+ 独立来源，自审无缺口 |
| medium | 有来源但部分单源 |
| low | 搜索枯竭 |

### 每页必含对比

- tool → `## 工具选择`
- concept → `## 与其他概念的关系`
- workflow → `## 为什么这样拆？`
- comparison → 什么场景 A、什么场景 B

---

## 语言

默认中文。专有名词和技术术语保留原文。
