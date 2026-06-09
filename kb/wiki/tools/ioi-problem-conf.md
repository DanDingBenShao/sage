---
title: IOI problem.conf 完整配置规范
description: >
  IOI/Codeforces/QOJ 风格 problem.conf 所有配置项：内置判题器、测试数据路径、时空限制、
  子任务分组与依赖、反作弊token、自定义checker/validator/interactor。打包IOI题目时用。
type: tool
domain: [software-dev]
related: [[ai-code-factory-pipeline]], [[testlib-h]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
source: web-searched
source_detail:
  - https://www.cnblogs.com/dai-se-can-tian/p/16715745.html
  - https://training.qoj.ac/blog/qingyu/blog/1423
---

# problem.conf 配置规范

## 基础配置

```ini
use_builtin_judger on          # 使用内置判题器（on/off）
use_builtin_checker ncmp       # 内置checker类型: ncmp(精确比对)/wcmp(忽略空白)/fcmp(浮点容差)
n_tests 10                     # 正式测试数据数量
n_ex_tests 5                   # 额外/样例测试数据数量
n_sample_tests 1               # 样例测试数据数量
input_pre www                  # 输入文件名前缀（www1.in, www2.in ...）
input_suf in                   # 输入文件名后缀
output_pre www                 # 输出文件名前缀
output_suf ans                 # 输出文件名后缀
time_limit 1                   # 时间限制（秒），支持毫秒精度
memory_limit 256               # 内存限制（MB）
output_limit 64                # 输出限制（MB）
full_score 100                 # 满分
```

## 子任务配置

```ini
n_subtasks 6                   # 子任务数量
subtask_end_1 5                # 子任务1包含测试点1-5
subtask_score_1 10             # 子任务1分值
subtask_end_2 10               # 子任务2包含测试点6-10
subtask_score_2 10
subtask_type_5 packed          # packed=全对才给分; min=取最低测试点得分
subtask_dependence_5 3         # 子任务5依赖子任务3（子任务3通过才测子任务5）
```

## 自定义程序

```ini
with_implementer on            # 启用评测评桩（与子Agent代码一起编译）
token wahaha233                # 交互题反作弊token（judge先输出token再输出数据）
```

## 内置Checker类型

| checker | 说明 |
|---------|------|
| `ncmp` | 精确比对（逐字节） |
| `wcmp` | 忽略空白字符比对 |
| `fcmp` | 浮点容差比对 |
| 自定义 | `chk.cpp`（使用testlib.h） |

## 目录结构

```
problem_folder/
├── problem.conf
├── 1.in, 2.in, ...           # 正式输入（或 www1.in）
├── 1.ans, 2.ans, ...         # 期望输出
├── ex_1.in, ex_1.ans, ...    # 样例/额外测试数据
├── chk.cpp                   # 自定义checker（可选）
├── val.cpp                   # 输入validator（可选）
├── implementer.cpp           # 评测评桩（with_implementer时）
├── download/                 # 分发给选手的附件
└── require/                  # 运行时需要的文件（头文件等）
```

## 工具选择

| 场景 | 方案 |
|------|------|
| 本项目静态库判题 | `with_implementer on` + 自定义 `implementer.cpp` 调用子Agent的库函数 |
| 纯函数输出比对 | `ncmp` 内置checker |
| 浮点结果 | `fcmp` 或自定义 `chk.cpp` |
| 多答案问题 | 自定义 `chk.cpp` |
