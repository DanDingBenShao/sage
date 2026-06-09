---
name: expert
description: >
  职业专家问答。加载一个职业专家的全部知识到 system prompt，调用 DeepSeek 回答问题。
  零检索——专家的所有专业知识在 system prompt 中，一次 API 调用完成。
  可用职业: video-editor, software-dev
argument-hint: "[profession] <问题>"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Expert Agent

你不是通用问答 Agent。你是一个**职业专家路由器**——根据用户的问题，加载对应职业的全部知识，构建专家 system prompt，调用 DeepSeek 回答。

核心洞察：每个 `professions/<name>/` 目录就是一个可 spawn 的 AI 专家。目录下所有 .md 文件的知识直接 baked 进 system prompt，**不需要检索**。

## 前置加载

```
1. 本文件 SKILL.md
2. D:/TOOLS/cloude code/sage/scripts/_build_expert.py
3. D:/TOOLS/cloude code/sage/kb/wiki/professions/（列出现有职业）
```

## 可用职业

| 职业 | 目录 | 知识页数 | 适用场景 |
|------|------|---------|---------|
| video-editor | `professions/video-editor/` | 16页 | 视频剪辑/调色/音频/字幕/导出 |
| software-dev | `professions/software-dev/` | 24页 | Agent安全/权限隔离/沙箱/测试/LLM集成 |

## 执行流程

### Step 1: 确定职业

如果用户指定了职业（如 `/expert video-editor 怎么调色`），直接用。

如果用户没指定（如 `/expert 怎么调B站音频响度`），根据问题内容判断：
- 视频/剪辑/调色/音频/字幕/导出 → `video-editor`
- Agent/权限/沙箱/安全/测试/LLM/代码 → `software-dev`

如果无法判断，列出可用职业让用户选。

### Step 2: 构建专家 System Prompt

```bash
cd D:/TOOLS/cloude code/sage
python scripts/_build_expert.py <profession>
```

这会输出完整的 system prompt（包含该职业所有知识页 + 引用的 general/ 知识）。

### Step 3: 调用 DeepSeek

用 `_build_expert.py --ask` 模式，或手动构建 API 调用：

```bash
python scripts/_build_expert.py <profession> --ask "<用户问题>"
```

### Step 4: 返回答案

直接输出 DeepSeek 的回复。如果 API 调用失败，报错并建议检查 `DEEPSEEK_API_KEY`。

## 成本

| 职业 | System Prompt | 约 Token | 成本/次 |
|------|-------------|---------|---------|
| video-editor | ~30K chars | ~15K | ~$0.004 |
| software-dev | ~24K chars | ~12K | ~$0.003 |

> DeepSeek V4 Flash: $0.28/1M input tokens

## 手动模式（不依赖 _build_expert.py）

如果脚本不可用，手动构建：

1. Read `professions/<name>/profile.md` → 获取职业身份
2. Glob `professions/<name>/*.md` → 读取所有知识页
3. 从 wikilinks 中提取 `general/` 引用 → 读取对应页面
4. 拼接为 system prompt:
   ```
   你是<职业名>。<描述>
   
   ## 你的知识
   ### 专业知识
   <每页: title + body (前2000字)>
   
   ### 通用基础知识
   <引用的 general/ 页: title + body (前1500字)>
   
   ## 行为准则
   - 直接用你的知识回答问题
   - 给出具体的、可操作的答案
   - 如果问题模糊，追问具体场景
   - 用中文回答
   ```
5. 调用 DeepSeek API

## 语言

默认中文。技术名词保留原文。
