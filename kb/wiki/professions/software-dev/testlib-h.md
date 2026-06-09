---
title: testlib.h — Generator/Validator/Checker C++ 库
description: >
  Codeforces 标准出题库。Generator 用 rnd.next() 生成确定性随机测试数据，
  Validator 用 inf.readInt() 严格校验输入，Checker 用 ouf/ans 流比对输出。
  本项目测试数据生成器和判题系统的核心依赖。
type: tool
domain: [software-dev]
related: [[ai-code-factory-pipeline]], [[ioi-problem-conf]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
source: web-searched
source_detail:
  - https://github.com/MikeMirzayanov/testlib
  - https://codeforces.com/topic/18353/
---

# testlib.h

**仓库**: `github.com/MikeMirzayanov/testlib`

## Generator（测试数据生成器）

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);  // 第三个参数=1 使用新版

    int n = opt<int>("n");        // 命令行参数 --n 或 -n
    cout << rnd.next(1, n) << " ";
    cout << rnd.next(1, n) << endl;
    return 0;
}
```

### rnd.next() 速查

| 调用 | 返回值 |
|------|--------|
| `rnd.next(n)` | 0 到 n-1 |
| `rnd.next(from, to)` | from 到 to（含） |
| `rnd.next(limit)` | 0 到 limit（double） |
| `rnd.wnext(n, t)` | 偏置分布（t>0 偏大，t<0 偏小） |
| `rnd.any(container)` | 随机元素 |
| `rnd.perm(n)` | 随机排列 |
| `rnd.next("[a-z]{1,10}")` | 正则生成字符串 |

## Validator（输入校验器）

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);
    int n = inf.readInt(1, 100000, "n");
    inf.readSpace();
    int m = inf.readInt(1, n, "m");
    inf.readEoln();
    // ... 读取所有数据 ...
    inf.readEof();  // 必须：确保无多余数据
    return 0;
}
```

**关键原则**：validator 必须极其严格——检查空格、换行、前导零、边界。返回非零=数据非法。

## Checker（判题器）

```cpp
#include "testlib.h"

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    // inf=输入, ouf=选手输出, ans=标准答案
    int ja = ans.readInt();
    int pa = ouf.readInt();
    if (ja != pa)
        quitf(_wa, "Expected %d, found %d", ja, pa);
    ouf.readEof();  // 检查选手是否输出了多余内容
    quitf(_ok, "Correct");
}
```

### 判定结果

| 函数 | 含义 |
|------|------|
| `quitf(_ok, ...)` | Accepted |
| `quitf(_wa, ...)` | Wrong Answer |
| `quitf(_pe, ...)` | Presentation Error |
| `quitp(_pc(score), ...)` | 部分得分（score/100） |
| `quitf(_fail, ...)` | 判题系统内部错误 |

## 工具选择

| 场景 | 方案 |
|------|------|
| 生成随机测试数据 | `testlib.h` Generator + `rnd.next()` |
| 校验生成数据的合法性 | `testlib.h` Validator |
| 比对子Agent输出与期望 | `testlib.h` Checker (`ncmp`/`wcmp` 或自定义) |
| 需要多答案判定 | 自定义 Checker（`quitp` 部分给分） |
