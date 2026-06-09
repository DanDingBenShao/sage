---
title: Wiki Schema
type: meta
updated: 2026-06-05
---

# Wiki Schema

> 知识库的"宪法"。AI agent 每次操作前应读此文件。人类可自由修改，建议 git 追踪演化。

## 架构

```text
wiki/
├── _schema.md          # 本文件 — 页面类型定义与约束
├── _log.md             # 操作日志（只追加）
├── _index.json         # 由 scripts/wiki_index.py 生成
├── overview.md         # 人类可读索引（生成文件）
├── rules.md            # 已验证规则
├── false-beliefs.md    # 被证伪的认知
├── inbox-digest.md     # 最近摄入摘要
├── inbox-archive.md    # 较早的周摘要归档
├── raw/                # 不可变的原始材料
├── sources/            # 编译后的结构化摘要（每个来源一个文件）
├── entities/           # 持续跟踪的对象（项目、工具、规范体系等）
│   └── {NAME}/
│       ├── profile.md  # 主页面
│       └── ...         # 必要时扩展子页面
├── concepts/           # 主题、框架、横向连接多个实体的想法
│   └── {THEME}.md
├── explorations/       # 固化后的研究问题答案
├── decisions/          # 决策日志
├── comparisons/        # 并排比较分析
├── workflows/          # 任务分解树（Protocol 0 产出）
└── tools/              # 工具/API/CLI 使用知识（Protocol 0 产物）
```

## 页面类型

| type | 位置 | 适用场景 |
|---|---|---|
| `entity` | `entities/{NAME}/` | 需要长期跟踪的离散对象（项目/工具/规范/平台） |
| `concept` | `concepts/{NAME}.md` | 连接多个实体的主题或框架 |
| `source-summary` | `sources/` | 对单个外部来源的结构化摘要 |
| `exploration` | `explorations/` | 某个研究问题的固化答案 |
| `decision` | `decisions/` | 一次明确决策及其理由 |
| `comparison` | `comparisons/` | A vs B 并排比较 |
| `workflow` | `workflows/{TASK}.md` 或相关域下 | 一个任务从入口到原子步骤的完整分解树 |
| `tool` | `tools/{NAME}.md` | 一个具体工具/API/CLI 的使用知识 |
| `meta` | 根目录 | `_schema.md`、`rules.md`、`false-beliefs.md` 等 |

## Frontmatter 规范

除 `raw/` 外，每个 `.md` 页面都必须带 YAML frontmatter：

```yaml
---
title: <人类可读标题>
type: entity | concept | source-summary | exploration | decision | comparison | meta
domain: [visual-design | video-production | software-dev | business | general]
sources: [raw/filename]            # 仅 source-summary 使用
related: [[entity1]], [[concept1]]
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high | medium | low
---
```

`entity` 页面额外包含：

```yaml
aliases: [alt-name-1]
tags: [tag1, tag2]
status: active | archived | watching
```

## Wikilinks

使用双中括号：`[[entity-name]]`、`[[concept-name]]`。

**双向链接是强制的**：A 链接到 B，B 也应回链到 A。

## 五层结构：按变化速度组织

> **变化速度不同的东西，必须分层存放。**

| 层 | 变化频率 | 示例 |
|---|---|---|
| `raw/` | 几乎不变 | PDF、全文、转录稿、视频字幕 |
| `sources/` | 很少变 | 结构化来源摘要 |
| `entities/`、`concepts/` | 周到月级 | 档案页、主题页 |
| `explorations/`、`decisions/` | 按问题变化 | 固化答案、一次决策 |
| `rules.md`、`false-beliefs.md` | 季度级 | 长期经验总结 |

## 领域定义

本知识库覆盖以下领域：

| domain | 说明 |
|---|---|
| `visual-design` | 视觉设计：图表规范、图标设计、排版、色彩、动效、审美理论 |
| `video-production` | 视频制作：素材准备、剪辑、调色、动效、音效、导出 |
| `software-dev` | 软件开发：架构、设计模式、测试、前后端、部署 |
| `business` | 商业：产品策略、路演、营销 |
| `general` | 通用：不属以上领域的跨域知识 |

## 页面类型扩展

| type | 位置 | 适用场景 |
|---|---|---|
| `workflow` | `workflows/{TASK}.md` 或相关域下 | 一个任务从入口到原子步骤的完整分解树 |
| `tool` | `tools/{NAME}.md` | 一个具体工具/API/CLI 的使用知识 |

`workflow` 和 `tool` 页面额外包含：

```yaml
decomposition_depth: 0      # 从入口任务的分解深度（入口=0，每层+1）
is_atomic: false            # true = 已达到训练数据覆盖阈值，不可再分解
prerequisites: [            # 显式声明的前置依赖（搜索结果来源标注）
  { entry: "tools/xxx.md", source: "WebSearch", confidence: high }
]
```

## Protocol 0 — 递归知识完备化（Recursive Knowledge Completion）

**这是本知识库最核心的协议。任何知识条目写入时，必须先通过此协议完备化。**

### 核心原则：绝不偷懒

> 一个知识条目写入时，不能只写它自身。必须识别其中隐含的前置依赖，对每个缺失的依赖主动搜索、递归拆分，直到每个子节点都达到"模型训练数据高度可能已包含"的程度。

### 触发条件

任何以下类型的知识条目写入时触发：
- `workflow`：一个任务的步骤分解
- `concept`：一个新概念的定义
- `entity/{NAME}/` 的 `profile.md` 中描述的操作流程
- 用户明确说"完备化这个知识点"

### 执行步骤

```
For 当前条目中的每个步骤/依赖:

  1. 显式声明：将隐含依赖写成明文
     "这个步骤需要知道 X" → 记录为 prerequisites

  2. 检查已知：搜索 wiki/ 中是否已有 X 的知识
     → 有且 confidence ≥ medium：直接 [[交叉引用]]
     → 有但 confidence = low：标记需验证
     → 没有：执行步骤 3

  3. 搜索填补：主动搜索 X
     - WebSearch（关键词：X + "tutorial"/"documentation"/"API"）
     - WebFetch（获取具体页面内容）
     - 对论文/学术内容：学术搜索引擎
     - 对工具/CLI：官方文档 + GitHub README

  4. 结构写入：将搜索结果写入 wiki/
     - 类型为 tool 或 concept 或 workflow（取决于内容性质）
     - 必须标注 source（搜索来源 URL）
     - 必须标注 confidence（high/medium/low）

  5. 递归：对该新条目执行 Protocol 0
     直到满足任一停止条件

  6. 建立双向 cross_refs
     A.prerequisites 包含 B → B.related 必须包含 A
```

### 停止条件（满足任一即停）

```
① 训练数据覆盖阈值（最优先）：
   当前子任务的操作是极其通用且高度标准化的
   例：HTTP 请求 / 文件读写 / JSON 解析 / SQL 查询 / ffmpeg 基础命令
   → 标记 is_atomic: true
   → 不写入知识库（模型训练数据已包含）

② 工具原子性：
   当前子任务映射到一个具体的 CLI 命令或 API 调用，且参数已完整
   例：npx puppeteer screenshot URL --viewport 1920x1080
   → 标记 is_atomic: true
   → 可以写入 tool 页面，附带精确命令

③ 搜索枯竭：
   连续 3 次搜索未找到可靠来源
   → 标记为 open_question，等待人类补充

④ 用户阻断：
   用户明确指示不继续扩展此分支
```

### 原子性判断标准

| 类型 | 原子（is_atomic: true） | 非原子（需继续拆分） |
|---|---|---|
| 编程操作 | `fetch()` / `fs.readFile()` | "读取 PDF 中的表格数据" |
| 命令行 | `ffmpeg -i a.mp4 -i b.mp4 concat` | "用 ffmpeg 实现高级转场效果" |
| 工具调用 | `puppeteer.screenshot()` | "自动化截图工具的选择与配置" |
| 领域知识 | "HTTP GET 请求的基本结构" | "Google Scholar API 的查询参数" |

### 示例：一次完备化的完整链路

```
入口：video-production/editing/workflow.md
  type: workflow, depth: 0
  step: "准备图片素材" → 隐含依赖：图片来源、截图方法

  → 拆分出 material-prep/image-sources.md (depth: 1)
    "论文截图" → 隐含依赖：论文搜索、浏览器截图
    "官方视频截图" → 隐含依赖：视频下载、逐帧提取
    "AI 图表生成" → 隐含依赖：图表库、数据格式

    → 拆分出 tools/academic-search.md (depth: 2)
      Google Scholar API / Semantic Scholar / arXiv API
      → 每个 API 的具体查询参数和认证方式
      
      → 拆分出 tools/scholar-api-query.md (depth: 3)
        GET https://api.semanticscholar.org/graph/v1/paper/search?query=XXX
        → is_atomic: true（HTTP GET + JSON 解析，模型训练数据已覆盖）
        停止。
```

## 摄入规则（Ingest Protocol）

> **注意**：Ingest Protocol 执行前，必须先完成 Protocol 0（递归知识完备化）。

1. 原文放入 `raw/`（不可变归档）
2. 创建 `sources/<date>-<slug>.md`
3. 识别实体与概念，更新对应页面；**新建前先征得用户同意**
4. 维护双向 `[[wikilinks]]`
5. 追加一行到 `_log.md`
6. 更新 `inbox-digest.md` 当前周内容
7. 运行 `python scripts/wiki_index.py --lint`

## 交叉引用规则（Cross-Reference Protocol）

- 更新 A 的 `related:` 后，必须确认 B 的 `related:` 也包含 A
- 识别孤儿页（无入链无出链），主动提醒用户

## 矛盾扫描规则（Contradiction Scan Protocol）

每次准备写入新判断前：
1. 检查 `false-beliefs.md` — 是否与已证伪认知冲突
2. 检查 `rules.md` — 是否违反现行规则
3. 检查相关实体页面 — 是否与历史判断矛盾

## Concept Synthesis（重编译）

每个 `concept` 页面包含 `## Synthesis / 综述` 区块。

**触发重编译**：自上次编译以来，新增 3 个以上来源引用该 concept。

## 可验证预测

```markdown
## Verifiable Predictions / 可验证预测

| Prediction | Target date | Status | Verified date | Result |
|---|---|---|---|---|
| <claim> | YYYY-MM | pending | | |
```

状态：`pending` → `confirmed` / `partially` / `denied`
- `confirmed` 累积 3 次 → 建议提升到 `rules.md`
- `denied` 且暴露偏差 → 建议加入 `false-beliefs.md`

## 索引生成

```bash
python scripts/wiki_index.py              # 重建索引
python scripts/wiki_index.py --lint       # 健康检查
python scripts/wiki_index.py --stats      # 统计
python scripts/wiki_index.py --search Q   # 搜索
python scripts/wiki_index.py --report     # 注意力报告
```

---

*这份 schema 是人与 AI 之间的契约。修改后建议提交 git。*
