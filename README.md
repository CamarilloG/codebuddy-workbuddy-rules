# CodeBuddy / WorkBuddy Rules

非官方的 CodeBuddy、WorkBuddy 请求兼容规则分享：整理已有适配中的请求处理方式、适用边界和已知风险，供自建网关或代理参考。本仓库只提供文档，不包含执行器、测试或模型服务。

适用场景：用自建网关或代理把 OpenAI 格式（`/chat/completions`）的请求转发到 CodeBuddy / WorkBuddy。如果你的客户端发的是 Anthropic 格式（如 Claude Code 原生请求），先转成 OpenAI 格式，再套用下面的规则。

> **证据范围**：本文整理自已有适配实现及其代码注释。注释中的历史平台观察未由本仓库独立复核；此前的合成样例检查只验证文本转换，不证明真实平台可用。本次文档更新未发起真实上游请求。平台与客户端版本随时可能变化，以下内容不是官方协议规范或当前有效性保证。
>
> 与腾讯及相关客户端项目无隶属或背书关系。使用前请核对服务条款和授权范围；身份文本处理应单独评估并显式选择，不承诺通过渠道校验或避免账号风控。

### 平台与区域

| 范围 | 本文身份文本规则的适用说明 |
|---|---|
| CodeBuddy | 来源实现包含这些兼容处理；不能据此推断所有区域、版本或账号均适用 |
| WorkBuddy 国内区 | 来源实现启用身份文本处理；仅代表已有实现策略，不是持续有效性承诺 |
| WorkBuddy 国际区 | 来源实现默认不启用身份文本处理；不得从同名业务码推断与国内区具有相同指纹规则。会话请求头构造与文本处理是两个独立问题 |

身份文本表中的客户端名称用于标识匹配对象，不表示已覆盖该客户端全部版本与 SDK 变体。

## 一、协议格式

以下是来源实现采用的处理，不将每项防御性转换都视为已独立证实的上游硬限制。

| 规则 ID | 平台 | 来源处理针对的问题 | 处理方式 |
|---|---|---|---|
| `compat.developer-role` | 两者 | 来源实现为兼容角色限制而降级角色 | 把 `role: "developer"` 改成 `role: "system"`，文本不变；角色优先级语义可能改变 |
| `compat.codebuddy-tool-choice` | CodeBuddy | 来源实现只向上游发送字符串工具选择 | 对 `tool_choice: {"type":"function","function":{"name":"X"}}`，仅保留名为 `X` 的工具并设 `"required"`；目标工具不存在时应在本地报错，不静默降级 |
| `compat.workbuddy-system` | WorkBuddy | 来源实现确保第一条消息为 system | 第一条不是 system 时插入 `{"role":"system","content":"You are a helpful assistant."}`；这不是空请求有效性的证明 |
| `compat.codebuddy-stream` | CodeBuddy | 来源实现记录上游拒绝非流式请求 | 向上游发送 `stream: true`；若调用方需要非流式结果，由宿主聚合 SSE 并检查正常结束，不能把半截流当成功 |
| `compat.workbuddy-stream` | WorkBuddy | 来源实现统一走上游流式链路 | 设 `stream: true`；需要非流式结果时同样由宿主聚合并检查结束状态 |
| `compat.workbuddy-usage` | WorkBuddy | 来源实现显式请求流式用量 | 设 `stream_options.include_usage: true`；集成时保留可支持的其他字段，不承诺上游必然返回完整用量 |
| `compat.empty-tool-calls` | WorkBuddy | 来源实现清除空工具调用字段 | 删除 assistant 消息里的空 `tool_calls: []`；非空列表保持不变 |

注意：

- CodeBuddy 缩减工具列表后，如果历史消息里调用过其他工具，上游可能因为找不到那些工具而拒绝请求，需要在你的工作流里实测。
- 只在必要字段应用明确规则；身份文本处理仅作用于表中指定的 system / developer / assistant，不修改 user/tool 正文，也不删除图片等非文本内容块。
- 转换前复制输入，避免污染其他上游的回退请求。不要丢失工具调用消息与其对应结果。
- 宿主仍需校验有效消息、工具结构与目标协议要求；只补一条默认 system 并不能让空请求成为有效对话。

## 二、客户端身份文本

这些固定句子可能表明请求来自某个客户端。来源注释曾将部分 `HTTP 400 / code 11128` 与客户端特征联系起来，但 **`11128` 本身不足以证明命中了客户端指纹**：渠道校验、消息结构或协议头等问题都应分别排查，不能仅凭业务码确定原因。本文不把该业务码定义为官方错误码规范。

两种处理方式：

- **删除**：针对选定的产品样板片段（Claude Code、Codex）；即使是样板，删除也可能改变模型行为，需要宿主回归验证。
- **改写**：对包含任务上下文的句子尽量保留含义（DSH）；不保证语义完全等价，也不保证改写后能通过当前平台校验。

### Claude Code / Codex：删除选定样板

下表是文本处理建议，正则采用 Python `re` 语法。身份句规则锚定行首，但只移除匹配片段，不保证整行删除；反馈链接规则要求独立整行，以免误删 URL 后缀或同行指令。普通品牌提及不应泛删。

| 规则 ID | 客户端 | 作用角色 | 匹配的原文 | 正则 |
|---|---|---|---|---|
| `identity.claude-code` | Claude Code | system、developer、assistant | `You are Claude Code, Anthropic's official CLI for Claude.`（含 `, running within the Claude Agent SDK` 变体） | `(?m)^[ \t]*You are Claude Code, Anthropic's official CLI for Claude(?:, running within the Claude Agent SDK)?\.(?=\s\|$)[ \t]*(?:\r?\n)?` |
| `identity.claude-feedback` | Claude Code | system、developer、assistant | `- To give feedback, users should report the issue at https://github.com/anthropics/claude-code/issues`（必须是独立一整行） | `(?m)^[ \t]*-[ \t]*To give feedback, users should report the issue at https://github\.com/anthropics/claude-code/issues[ \t]*(?=\r?$)(?:\r?\n)?` |
| `identity.codex` | Codex | system、developer | `Codex CLI is an open source project led by OpenAI.` | `(?m)^[ \t]*Codex CLI is an open source project led by OpenAI\.(?:[ \t]*\r?\n\|[ \t]+\|$)` |

表格里的 `\|` 是为了不打断 Markdown 表格，复制到代码里时写成 `|`。

已知未覆盖的变体：Agent SDK 的 `You are a Claude agent, built on Anthropic's Claude Agent SDK.` 不在上述规则中。不能仅凭相似措辞断言它会触发同类校验；新增规则前应确认授权、需求与匹配边界。

### Claude Code：分支说明改写

来源实现还包含以下措辞转换，仅用于 system / developer，保留缩进和实际分支名，不修改 assistant、user 或 tool。它不是官方协议要求，也不证明该短语单独触发校验。

| 规则 ID | 原文（合成示例） | 改成 | 正则与替换 |
|---|---|---|---|
| `identity.claude-main-branch` | `Main branch (you will usually use this for PRs): example-branch` | `Main branch: example-branch` | `(?m)^([ \t]*)Main branch \(you will usually use this for PRs\):([ \t]*[^\r\n]+)$` → `\1Main branch:\2` |

### DeepSeek Harness（DSH）：改写措辞

| 规则 ID | 作用角色 | 原文 | 改成 | 正则 |
|---|---|---|---|---|
| `identity.dsh` | system、developer、assistant | `You are an AI agent powered by DeepSeek Harness.` | `You are an AI agent.` | `(?m)^([ \t]*)You are an AI agent powered by DeepSeek Harness(?=[.\t ]\|$)` → `\1You are an AI agent` |
| `identity.dsh-gui` | system、developer | `You are interacting with the user through the DeepSeek Harness Web GUI ...` | `You are interacting with the user through the Web GUI ...` | `(?m)^([ \t]*)You are interacting with the user through the DeepSeek Harness Web GUI(?=[.\t ])` → `\1You are interacting with the user through the Web GUI` |
| `identity.dsh-path-at` | system、developer | `Tokens prefixed with @ are paths the user explicitly referenced.` | `@-prefixed tokens are paths the user referenced explicitly.` | `Tokens prefixed with @\s+are paths the user\s+explicitly referenced\.` |
| `identity.dsh-path-resolve` | system、developer | `Relative paths resolve from the workspace root; absolute paths identify files or directories on the host.` | `Relative paths are resolved against the workspace root; absolute paths point at files or directories on the host.` | `Relative paths resolve\s+from the workspace root;\s*absolute paths identify files or directories on the host\.` |

说明：

- **Web GUI 句只锚定固定前缀**。来源注释记录结尾曾包含运行时 URL 的间接描述或具体地址，因此不把地址写进匹配规则。此处不发布实际地址、版本部署信息或完整运行时上下文；固定前缀本身变化时仍需更新。
- **路径两句的关联仅是历史观察**：来源注释记录过“两句连用被拒、单句通过”的现象，本仓库未独立复核，不能推广为所有版本的必然规律。它们承载路径解析说明，若选择处理，应优先改写而非删除，并检查实际工具行为。
- 两条路径正则用 `\s+` / `\s*` 容纳句中换行；未使用点号通配符，因此单为允许换行无需额外启用 `re.S`（DOTALL）。
- **assistant 的处理范围更小**：来源实现只对其中的 DSH 身份句应用改写，不对其中的 GUI 和路径句应用这些规则。这是实现边界，不是其他文本在所有平台上都不会触发校验的证明。
- 对表中示例，改写结果不会再次命中同一规则；集成时仍应验证幂等性、文本块处理和工具行为，不宣称任意输入均已验证。

## 三、请求头

请求头可能包含凭证、客户端身份、会话或遥测信息。需要区分两个步骤：**过滤调用方输入头**，再**按目标协议构造上游请求头**。下面的允许列表是数据最小化建议，不是平台强制规范；只保留两个头并不足以构造完整的上游请求。

### 3.1 调用方输入头过滤

优先只透传明确需要的允许列表，而不是试图穷举所有 Agent 特征。不要把调用方凭证当成目标平台凭证。

| 类别 | 头部名称 | 处理 |
|---|---|---|
| 默认放行 | `accept`、`content-type` | 保留，名称统一转小写 |
| 调用方凭证 | `authorization`、`proxy-authorization`、`cookie`、`set-cookie`、`x-api-key`、`api-key` | 丢弃；由网关注入目标平台自己的凭证 |
| 逐跳头 / 传输协商 | `connection`、`transfer-encoding`、`keep-alive`、`te`、`trailer`、`upgrade` | 不直接透传；`Connection` 头里点名的字段也移除，由 HTTP 客户端按目标连接处理 |
| 目标与消息长度 | `host`、`content-length` | 不直接透传，由 HTTP 客户端根据目标 URL 和处理后的请求体生成；它们不应统称为逐跳头 |
| 客户端身份 / 会话头 | `user-agent`、`x-ide-name`、`x-ide-type`、`x-ide-version`、`x-agent-intent`、`x-agent-purpose`、`x-agent-type`、`x-claude-code-session-id`、`x-opencode-session`、`x-opencode-session-id` | 丢弃；这只是常见例子，未列出的头默认也丢 |

其他要点：

- 放行的头值里不能有控制字符（`\t` 除外），防止 `\r\n` 注入。
- 大小写不同的同名头（如 `Accept` 和 `accept`）同时出现时，不要随便取一个，应直接拒绝。
- 需要额外透传某个头（例如链路追踪 `x-trace`）时再单独加进白名单，但凭证、逐跳头和上面的客户端身份头不要放行。

### 3.2 WorkBuddy 上游会话头构造

来源实现会在聊天请求中主动构造下列字段，而不是透传调用方同名字段。下表描述已有实现，不表示字段全部为官方公开必填项，也不承诺补齐后可以通过渠道校验。

| 字段 | 来源实现的构造关系 | 集成边界 |
|---|---|---|
| `X-Conversation-ID` | 会话范围的标识；有可信会话上下文时保持关联，否则创建新标识 | 不直接暴露调用方原始会话 ID，不跨用户或账号复用；生命周期由宿主明确管理 |
| `X-Conversation-Request-ID` | 每次聊天请求生成新标识 | 不在不同请求间复用同一个常量 |
| `X-Root-Request-ID` | 与本次 `X-Conversation-Request-ID` 使用相同标识 | 这是来源实现的关联方式，不是通用追踪协议定义 |
| `X-Conversation-Message-ID` | 来源实现也与本次请求标识相同 | 不声称所有客户端或后续协议版本都采用相同关系 |
| `X-Request-ID` | 来源实现另行生成请求标识 | 与上述标识区分，不填入真实用户标识或凭证 |

来源记录曾将国际区的 `11128` 与缺少会话头联系起来，但本仓库没有独立进行缺头/补头对照实验，**不能断言缺头一定报错、补头一定通过，或据此推断身份文本规则适用国际区**。

其他字段应分开处理：

- **鉴权与账号上下文**：例如 `Authorization`、`X-User-Id`、`X-Domain`，由宿主根据自己合法取得的目标平台授权构造；不提供真实值，不照搬其他账号字段，也不透传调用方凭证。
- **产品与客户端身份字段**：例如 `User-Agent`、`X-IDE-*`、`X-Agent-*`。不能因为来源实现设置过它们，就认为冒充官方客户端获得授权；本文不提供官方身份或版本值的伪装配方。是否设置及设置什么，应以获准使用的接入方式为准。
- **来源与目标地址字段**：`Origin`、`Referer` 等不能复制调用方的私人地址。目标区域、协议和授权必须分别核实；本文不发布个人部署地址。

## 四、使用与反馈边界

- 仅记录规则 ID、修改位置和必要状态，不默认保存请求正文、请求头值或完整错误体。错误响应也可能含身份信息。
- 分享问题时使用合成最小样例，不提交真实 Token、Cookie、授权 state、用户/会话 ID、本机路径、私人域名或完整系统提示词。
- 固定所参考的提交版本，在自己的工作流回归后更新；规则分享不是远程自动下发配置。
- `11128` 应结合 HTTP 状态、请求结构与受控排查结果分析；不能通过修改错误码掩盖上游拒绝。配额不足、登录失效、权限不足和账号风控应分别处理，不属于身份文本改写可以解决的问题。

## 许可证

[Apache-2.0](LICENSE)。CodeBuddy、WorkBuddy、Claude Code、Codex 等名称仅用于说明兼容目标，商标归各自权利人。
