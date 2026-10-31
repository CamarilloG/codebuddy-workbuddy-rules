# CodeBuddy / WorkBuddy Rules

非官方的 CodeBuddy、WorkBuddy 请求规则分享：上游对请求有哪些限制或识别点，转发前应该把请求改成什么样。

适用场景：用自建网关或代理把 OpenAI 格式（`/chat/completions`）的请求转发到 CodeBuddy / WorkBuddy。如果你的客户端发的是 Anthropic 格式（如 Claude Code 原生请求），先转成 OpenAI 格式，再套用下面的规则。

> 以下规则只用合成样例验证过，**没有在真实平台上测试**，平台随时可能调整。与腾讯及相关客户端项目无隶属或背书关系；使用前请自行核对服务条款。

## 一、协议格式

| 规则 ID | 平台 | 上游限制 | 改成什么 |
|---|---|---|---|
| `compat.developer-role` | 两者 | 不接受 `developer` 角色 | 把 `role: "developer"` 改成 `role: "system"`，内容不变 |
| `compat.codebuddy-tool-choice` | CodeBuddy | 不接受按名字指定工具：`tool_choice: {"type":"function","function":{"name":"X"}}` | `tools` 只保留名为 `X` 的那一个工具，`tool_choice` 改成 `"required"` |
| `compat.workbuddy-system` | WorkBuddy | 第一条消息必须是 system | 第一条不是 system 时，在最前面插入 `{"role":"system","content":"You are a helpful assistant."}` |
| `compat.workbuddy-stream` | WorkBuddy | 只支持流式 | 设 `stream: true`；需要非流式结果的话，由网关自己把 SSE 聚合成完整回复 |
| `compat.workbuddy-usage` | WorkBuddy | 不返回用量，除非显式要求 | 设 `stream_options.include_usage: true`，保留 `stream_options` 里原有的其他字段 |
| `compat.empty-tool-calls` | WorkBuddy | 不接受 assistant 消息里的空 `tool_calls: []` | 删掉这个字段；非空的 `tool_calls` 保持不变 |

注意：

- CodeBuddy 缩减工具列表后，如果历史消息里调用过其他工具，上游可能因为找不到那些工具而拒绝请求，需要在你的工作流里实测。
- 只改 system / developer / assistant 消息，不要动 user 和 tool 消息，也不要删图片等非文本内容块。

## 二、客户端身份文本

system 提示词里的这些固定句子会暴露请求来自哪个客户端。下面的正则按整行匹配，命中后**删除整行**（替换为空字符串），同一行里的其他内容和对品牌名的普通提及不受影响。

| 规则 ID | 客户端 | 作用角色 | 匹配的原文 | 正则 |
|---|---|---|---|---|
| `identity.claude-code` | Claude Code | system、developer、assistant | `You are Claude Code, Anthropic's official CLI for Claude.`（含 `, running within the Claude Agent SDK` 变体） | `(?m)^[ \t]*You are Claude Code, Anthropic's official CLI for Claude(?:, running within the Claude Agent SDK)?\.(?=\s\|$)[ \t]*(?:\r?\n)?` |
| `identity.claude-feedback` | Claude Code | system、developer、assistant | `- To give feedback, users should report the issue at https://github.com/anthropics/claude-code/issues`（必须是独立一整行） | `(?m)^[ \t]*-[ \t]*To give feedback, users should report the issue at https://github\.com/anthropics/claude-code/issues[ \t]*(?=\r?$)(?:\r?\n)?` |
| `identity.codex` | Codex | system、developer | `Codex CLI is an open source project led by OpenAI.` | `(?m)^[ \t]*Codex CLI is an open source project led by OpenAI\.(?:[ \t]*\r?\n\|[ \t]+\|$)` |

表格里的 `\|` 是为了不打断 Markdown 表格，复制到代码里时写成 `|`。

已知没覆盖到的变体：Agent SDK 的 `You are a Claude agent, built on Anthropic's Claude Agent SDK.` 不在上面的规则里，需要的话按同样的整行写法自己加一条。

## 三、请求头

上游能从请求头看出调用方是谁、用的什么客户端。做法是**只放行白名单**，其余全部丢弃，而不是维护一份黑名单。

| 类别 | 头部名称 | 处理 |
|---|---|---|
| 默认放行 | `accept`、`content-type` | 保留，名称统一转小写 |
| 调用方凭证 | `authorization`、`proxy-authorization`、`cookie`、`set-cookie`、`x-api-key`、`api-key` | 丢弃；由网关注入目标平台自己的凭证 |
| 逐跳头 | `host`、`content-length`、`connection`、`transfer-encoding`、`keep-alive`、`te`、`trailer`、`upgrade` | 丢弃；`Connection` 头里点名的字段也一并丢弃 |
| 客户端身份 / 会话头 | `user-agent`、`x-ide-name`、`x-ide-type`、`x-ide-version`、`x-agent-intent`、`x-agent-purpose`、`x-agent-type`、`x-claude-code-session-id`、`x-opencode-session`、`x-opencode-session-id` | 丢弃；这只是常见例子，未列出的头默认也丢 |

其他要点：

- 放行的头值里不能有控制字符（`\t` 除外），防止 `\r\n` 注入。
- 大小写不同的同名头（如 `Accept` 和 `accept`）同时出现时，不要随便取一个，应直接拒绝。
- 需要额外透传某个头（例如链路追踪 `x-trace`）时再单独加进白名单，但凭证、逐跳头和上面的客户端身份头不要放行。

## 许可证

[Apache-2.0](LICENSE)。CodeBuddy、WorkBuddy、Claude Code、Codex 等名称仅用于说明兼容目标，商标归各自权利人。
