---
title: VCPToolBox synchronous 插件开发
description: >
  VCPToolBox插件开发流程：plugin-manifest.json + stdio JSON通信 + PluginManager自动发现。
  本项目通过synchronous插件将ComFlow流水线注册到VCPToolBox。
type: tool
domain: [software-dev]
related: [[ai-code-factory-pipeline]]
created: 2026-06-09
updated: 2026-06-09
confidence: medium
source: web-searched
source_detail:
  - https://blog.gitcode.com/d8c9c364415996ba0ca03c797ac1f5b7.html
  - https://github.com/ANGLE404/VCPToolBox
---

# VCPToolBox Synchronous 插件开发

## 插件类型选择

本项目使用 **synchronous** 类型：AI对话中同步调用，等待执行结果返回。匹配流水线的同步执行模型。

## plugin-manifest.json

```json
{
  "name": "CodeFactoryPipeline",
  "displayName": "AI代码工厂流水线",
  "version": "1.0.0",
  "description": "需求拆分→静态库→IOI打包→多Agent验证",
  "pluginType": "synchronous",
  "entryPoint": "node adapters/vcp-plugin.cjs",
  "communication": { "protocol": "stdio" },
  "configSchema": {
    "model_count": { "type": "number", "default": 3 },
    "sandbox_type": { "type": "string", "default": "chromium" }
  },
  "capabilities": {
    "invocationCommands": [
      {
        "command": "split_and_verify",
        "description": "拆分需求为静态库并启动验证流水线。\n参数：\n- requirement: 需求文档文本\n- language: c|cpp\n返回JSON：{ pipeline_id, libraries: [{name, header, status}] }"
      },
      {
        "command": "check_pipeline_status",
        "description": "查询流水线状态。\n参数：\n- pipeline_id: 流水线ID\n返回JSON：{ status, completed, failed, results }"
      },
      {
        "command": "get_library_result",
        "description": "获取单个库的验证结果。\n参数：\n- pipeline_id: 流水线ID\n- library_name: 库名\n返回JSON：{ passed, pre_test_results, hidden_test_results, solution_code }"
      }
    ]
  }
}
```

## Stdio 通信协议

插件通过 stdin/stdout 与 PluginManager 通信：

**输入（stdin）**:
```json
{
  "command": "split_and_verify",
  "params": {
    "requirement": "...自然语言需求...",
    "language": "cpp"
  }
}
```

**输出（stdout）**:
```json
{
  "status": "success",
  "result": {
    "pipeline_id": "pipe_20260609_001",
    "libraries": [
      {"name": "lib_color_utils", "header": "void rgb_to_hsl(...);", "status": "dispatched"},
      {"name": "lib_filter_core", "header": "void apply_kernel(...);", "status": "dispatched"}
    ]
  }
}
```

**错误输出（stdout）**:
```json
{
  "status": "error",
  "error": "需求文档为空",
  "code": "EMPTY_REQUIREMENT"
}
```

## 入口文件骨架

```javascript
// adapters/vcp-plugin.cjs
const { splitRequirement } = require('../services/requirement-splitter.cjs');
const { generateTests } = require('../services/test-generator.cjs');
const { packageIOI } = require('../services/ioi-packager.cjs');
const { dispatchToAgents } = require('./agent-dispatcher.cjs');
const { judgeSubmission } = require('./judge-adapter.cjs');

let inputBuffer = '';

process.stdin.on('data', async (chunk) => {
  inputBuffer += chunk.toString();
  try {
    const request = JSON.parse(inputBuffer);
    inputBuffer = '';
    const result = await handleCommand(request);
    process.stdout.write(JSON.stringify(result) + '\n');
  } catch (e) {
    // JSON还未完整，继续等待
  }
});

async function handleCommand(request) {
  const { command, params } = request;
  try {
    switch (command) {
      case 'split_and_verify': {
        const libs = await splitRequirement(params.requirement, params.language);
        const withTests = await Promise.all(libs.map(generateTests));
        const packages = await Promise.all(withTests.map(packageIOI));
        const pipelineId = await dispatchToAgents(packages);
        return { status: 'success', result: { pipeline_id: pipelineId, libraries: packages } };
      }
      case 'check_pipeline_status': {
        const status = await getPipelineStatus(params.pipeline_id);
        return { status: 'success', result: status };
      }
      case 'get_library_result': {
        const result = await getLibraryResult(params.pipeline_id, params.library_name);
        return { status: 'success', result };
      }
      default:
        return { status: 'error', error: `Unknown command: ${command}` };
    }
  } catch (e) {
    return { status: 'error', error: e.message };
  }
}
```

## 工具选择

| 场景 | 方案 |
|------|------|
| 前端触发流水线 | VCP synchronous 插件（AI在对话中调用`split_and_verify`） |
| 程序化触发 | 直接调用Node.js入口（绕过VCP协议层） |
| 状态查询 | `check_pipeline_status` + `get_library_result` 命令 |
