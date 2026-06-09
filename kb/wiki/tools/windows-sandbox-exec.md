---
title: Windows 下 C/C++ 代码安全执行方案
description: >
  IOI标准isolate仅Linux。Windows替代方案评估：Chromium Sandbox（C++库，15年验证）、
  MXC（微软新项目）、Windows Sandbox VM、Hyperlight MicroVM。本项目推荐Chromium Sandbox。
type: tool
domain: [software-dev]
related: [[ai-code-factory-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: medium
source: web-searched
source_detail:
  - https://chromium.googlesource.com/chromium/src/+/main/docs/design/sandbox_faq.md
  - https://github.com/microsoft/mxc
  - https://github.com/forderud/runinsandbox
---

# Windows C/C++ 代码安全执行方案

## 方案对比

| 方案 | 隔离级别 | 管理员权限 | 成熟度 | 适用 |
|------|---------|-----------|--------|------|
| **Chromium Sandbox** | 进程级（AppContainer + Low IL + Restricted Token） | 不需要 | ⭐⭐⭐⭐⭐ (15年) | 推荐 |
| **MXC** | 进程级/VM/Hyper-V 可选 | 不需要 | ⭐⭐⭐ (新项目) | 备选 |
| **Windows Sandbox** | 完整VM硬件隔离 | 需要Pro/Enterprise | ⭐⭐⭐⭐ | 最安全但最重 |
| **Hyperlight** | MicroVM | 需要Hyper-V | ⭐⭐ | 实验性 |
| **Docker Desktop** | 容器（共享内核） | 需要 | ⭐⭐⭐ | 不够安全 |
| **RunInSandbox** | AppContainer | 不需要 | ⭐⭐ | 最简可用 |

## 推荐方案：Chromium Sandbox

Chrome 渲染进程的沙箱机制，纯C++库：

- **AppContainer** — 阻止磁盘写入、窗口创建、原始系统调用
- **Low Integrity Level** — 限制进程可访问的资源
- **Restricted Token** — 移除危险权限
- 无需驱动、内核模块、管理员权限
- 沙箱进程通过pipe/shared memory与broker通信

### 最小可用封装

```cpp
// sandbox_runner.cpp — 在沙箱中编译+运行子Agent代码
#include <windows.h>
#include <sandbox/win/src/sandbox.h>

int RunInSandbox(const wchar_t* cmd_line) {
    sandbox::BrokerServices* broker = sandbox::BrokerServices::GetInstance();
    sandbox::ResultCode result = broker->Init();

    sandbox::TargetPolicy* policy = broker->CreatePolicy();
    policy->SetJobLevel(sandbox::JOB_LOCKDOWN, 0);
    policy->SetTokenLevel(sandbox::USER_RESTRICTED_SAME_ACCESS,
                          sandbox::USER_LOCKDOWN);
    policy->SetDelayedIntegrityLevel(sandbox::INTEGRITY_LEVEL_LOW);
    policy->SetLockdownDefaultDacl();  // 阻止文件系统访问

    // 只允许读工作目录
    policy->AddRule(sandbox::TargetPolicy::SUBSYS_FILES,
                    sandbox::TargetPolicy::FILES_ALLOW_READONLY,
                    L"workdir\\*");

    PROCESS_INFORMATION pi;
    sandbox::ResultCode result = broker->SpawnTarget(cmd_line, policy, &pi);
    // 等待进程结束，检查退出码和资源使用
}
```

## 沙箱执行流程

```
子Agent提交 solution.cpp
  → 复制到临时工作目录
  → 启动沙箱进程: g++ implementer.cpp solution.cpp -o solution.exe
  → 编译成功？
    → 是: 启动沙箱进程: solution.exe < test.in > out.txt
    → 否: 返回编译错误
  → 检查退出码、运行时间、内存使用
  → 超出限制？→ TLE/MLE 判定
  → 正常退出 → 比对 out.txt 和 test.ans
```

## 多层防护

| 层 | 措施 |
|----|------|
| 编译时 | 编译超时限制（30s），禁止 `#include </dev/zero>` 等攻击 |
| 运行时 | Sandbox + 进程超时 + 内存上限 |
| 网络 | 完全禁用（Chromium Sandbox默认无网络） |
| 文件系统 | 只读工作目录 + 禁止访问其他路径 |
| 资源 | Job Object限制CPU核心数、内存、进程数 |
