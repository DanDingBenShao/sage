# CLAUDE.md — Knowledge Base Protocols

> 将此文件放在你的 Claude Code 项目根目录，或合并到已有的 CLAUDE.md 中。
> 知识库本体位于 `F:/AI/projects/knowledge-base/wiki/`。

## 知识库路径

```
F:/AI/projects/knowledge-base/wiki/
```

## 核心协议

### Protocol 0 — Recursive Knowledge Completion（最优先）

**核心原则：绝不偷懒。** 

写入任何知识条目时，不能只写它自身。必须识别隐含的前置依赖，对缺失的依赖主动搜索、递归拆分，直到每个子节点达到"模型训练数据高度可能已包含"的程度。

**执行步骤**：显式声明依赖 → 搜索填补 → 结构写入 → 递归 → 建立 cross_refs

**停止条件**：训练数据覆盖 / 工具原子性 / 搜索枯竭 / 用户阻断

**完整规范**：见 `wiki/_schema.md`。

### Protocol 1 — Ingest

> Ingest 前必须先完成 Protocol 0。

**Trigger**: 用户将文件放入 `wiki/raw/` 或粘贴内容并说 "ingest this"。

**Steps**:
1. 归档原始材料至 `wiki/raw/`（不可变），粘贴内容先写为 `.md`
2. 创建 `wiki/sources/<YYYY-MM-DD>-<slug>.md`
3. 识别实体与概念，更新对应页面；**新建前先征得用户同意**
4. 维护双向 `[[wikilinks]]`
5. 追加 `wiki/_log.md`
6. 更新 `wiki/inbox-digest.md`
7. 运行 `python scripts/wiki_index.py --lint`

### Protocol 2 — Cross-Reference

- 更新 A 的 `related:` 后必须确认 B 的 `related:` 也包含 A
- 发现孤儿页主动提醒

### Protocol 3 — Contradiction Scan

每次写入新判断前扫描 `false-beliefs.md` → `rules.md` → 相关实体页面。

### Protocol 4 — Crystallization

用 2+ 来源回答研究问题后，主动提议保存为 exploration。
每次对话最多提议 2 次。

## 定期维护

```bash
python scripts/wiki_index.py --lint    # 健康检查
python scripts/wiki_index.py --stats   # 统计
python scripts/wiki_index.py --report  # 注意力报告
```

## 语言

默认中文。专有名词保留原文。

---

*完整 schema 见 `wiki/_schema.md`。*
