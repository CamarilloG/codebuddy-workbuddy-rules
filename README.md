<a id="top"></a>

<div align="center">

# 🧩 CodeBuddy / WorkBuddy Rules

**请求兼容规则手册 · 文档分享 · 非官方**

CodeBuddy / WorkBuddy troubleshooting for Claude Code, Codex & DeepSeek Harness

请求兼容 · 反代 / reverse proxy · HTTP 400 / 11128 · 会话请求头

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
![Documentation only](https://img.shields.io/badge/Scope-Docs%20Only-64748b)
![Unofficial](https://img.shields.io/badge/Status-Unofficial-orange)
![Evidence: production records and external reports](https://img.shields.io/badge/Evidence-Production%20Records%20%2B%20External%20Reports-64748b)
![Documentation reviewed: 2026-10-31](https://img.shields.io/badge/Docs%20Reviewed-2026--10--31-blue)

**[🔎 按报错查](#error-index) · [English](#english) · [📖 规则目录](#rule-index) · [🛡️ 免责声明](#disclaimer) · [💬 安全反馈](https://github.com/CamarilloG/codebuddy-workbuddy-rules/security/advisories/new) · [📜 许可证](LICENSE)**

</div>

---

> [!WARNING]
> **不是官方接口规范，不提供账号、模型服务或通过校验的保证。** 修改客户端身份不等于获得平台授权。请先阅读[完整免责声明](#disclaimer)，再判断是否适合你的环境；不要将真实凭证、完整系统提示词或私人部署信息提交到仓库。

非官方的 **CodeBuddy / WorkBuddy 反代与第三方 Agent 请求兼容排障手册**，面向自建网关集成 Claude Code、Codex 与 DeepSeek Harness（DSH）时的相关报错。只分享规则与排障记录，不提供可运行反代或官方接入授权。

<a id="error-index"></a>

## 🔎 按错误快速定位 / Troubleshooting by error

**看到 CodeBuddy / WorkBuddy 的 `HTTP 400 / 11128`，先区分消息角色、请求结构、会话头与已知客户端文本，不要直接判定“封号”或“额度不足”。** 下表的错误文本是历史记录中的原文或片段，不代表所有版本都使用同一文案。

| 错误原文 / 检索入口 | 平台、区域与证据 | 优先排查方向 | 详细说明 |
|---|---|---|---|
| `HTTP 400` / `11128` | CodeBuddy：生产记录；WorkBuddy：分区域实现与外部记录，不能跨区推断 | 角色、消息形状、会话头及已知文本特征；单凭码不能定位 | [案例](#incident-records) · [文本规则](#identity-rules) |
| `Illegal API invocation from an unapproved channel` | CodeBuddy 历史调用记录；具体客户端版本未知 | 第三方客户端请求特征与渠道授权；不是通用网络故障 | [Claude Code / Codex / DSH 案例](#incident-records) |
| `first message is not system prompt` | WorkBuddy 外部调研记录（E）；区域与版本未明确 | 首条消息形状；不要把同一个 `11128` 一律归为指纹 | [system 处理](#protocol-rules) |
| `check ua, get coding copilot version error` | CodeBuddy 模型目录请求，生产记录（P）；不推广至所有端点 | 目录端点与客户端版本头要求，不是身份文本清理 | [目录头检查](#catalog-headers) |
| `Non-stream chat request is currently not supported` / `11101` | CodeBuddy 非流式接入记录（P） | 上游是否收到非流式请求；聚合时检查正常结束 | [流式规则](#protocol-rules) |
| `422` / `unknown variant developer` | 生产排障中的非 Buddy 回退上游（P） | 找到实际失败的候选；检查角色支持，别误归因 CodeBuddy | [回退案例](#incident-records) |
| `11140` | 来源实现的账号限制分类；不是已证明由指纹清理解除的案例 | 检查账号与官方渠道状态，不承诺通过改词解决 | [不属于清洗成果的限制](#not-identity-fixes) |
| `429` / `6004` | 来源实现的频率、配额或模型窗口分类；不保证仅凭码能定因 | 分析额度、频率与错误上下文 | [独立限制](#not-identity-fixes) |
| `401` | 登录或凭证相关分类，非身份规则通过证明 | 核查授权状态与凭证有效性；不要公开令牌 | [独立限制](#not-identity-fixes) |

### 按客户端定位

- **Claude Code + CodeBuddy / WorkBuddy**：查看[身份句、反馈样板与分支措辞](#claude-codex-rules)。Claude Code 原生 Anthropic 请求需先完成适当的协议适配，本文不提供翻译层。
- **Codex + CodeBuddy / WorkBuddy**：查看[产品来源句](#claude-codex-rules)；不把其他 SDK 身份变体自动视为已验证规则。
- **DeepSeek Harness / DSH + CodeBuddy**：查看[GUI 句式变化、assistant 历史与路径组合案例](#incident-records)，再看 [DSH 具体规则](#dsh-rules)。
- **WorkBuddy reverse proxy / 反向代理**：查看[会话请求头](#conversation-headers)及[国内 / 国际区边界](#platform-scope)；来源中的 CodeBuddy 生产结论不是 WorkBuddy 所有区域的独立验证。

<a id="english"></a>

## English · CodeBuddy / WorkBuddy error reference

**Unofficial troubleshooting notes and request compatibility rules for CodeBuddy and WorkBuddy with third-party agents: Claude Code, Codex, and DeepSeek Harness (DSH).** Intended for developers integrating a self-hosted gateway or reverse proxy. This is a documentation-only repository, not a runnable proxy, official SDK, or access authorization.

### Where to start

- **CodeBuddy HTTP 400 / 11128** or **“Illegal API invocation from an unapproved channel”**: examine request roles, known client identity text, and assistant history. The code alone does not identify the cause. See [production incident records](#incident-records) and [identity rules](#identity-rules).
- **WorkBuddy 11128**: distinguish message shape and conversation headers from prompt text. **“first message is not system prompt”** is reported in external material, not independently reproduced here. See [conversation headers](#conversation-headers) and [regional scope](#platform-scope).
- **CodeBuddy model catalog error “check ua, get coding copilot version error”**: this concerns the catalog endpoint and version-related headers, not every chat request. See [catalog request notes](#catalog-headers).
- **CodeBuddy 11101 / “Non-stream chat request is currently not supported”**: inspect upstream streaming behavior and completion checks. See [protocol rules](#protocol-rules).
- **DeepSeek Harness / DSH requests rejected by CodeBuddy**: production repair records describe a GUI sentence regression, assistant identity quotations, and an isolated two-sentence path-preamble case. See [DSH rules](#dsh-rules).
- **11140, 429, 6004, or 401**: these are not established identity-text fixes. Diagnose account, quota, rate, permission, and credential conditions separately. See [out-of-scope restrictions](#not-identity-fixes).

### Evidence and limitations

**P** = production repair record; **A** = production record explicitly describing live isolation/bisection; **E** = external report cited by the source research. Source records support historical repairs; they are not a guarantee for current versions. The public repository does not publish private logs or private source links. WorkBuddy international prompt filtering must not be inferred from domestic behavior. The latest documentation review is **2026-10-31**; it is **not a live-platform test date**. Exact historical live-test dates and complete account/client version matrices are not established in this public reference.

No promise of bypassing channel checks, avoiding account restrictions, or obtaining third-party authorization is made. Changes may affect model/tool behavior. Never publish credentials, private prompts, or production dumps. Read the [full risk disclosure](#disclaimer) before applying any rule.

[中文规则与案例 / Chinese rules and cases ↓](#rule-index)

## 项目速览

| 分享什么 | 不提供什么 |
|---|---|
| 请求参数与角色兼容经验 | 可运行网关、SDK、执行器或测试套件 |
| Claude Code / Codex / DSH 的选定文本处理规则 | 完整提示词、实时有效性保证或防封号承诺 |
| 输入请求头过滤与会话头构造边界 | 官方客户端身份伪装配方、账号与凭证 |
| 适用区域、证据范围与已知风险 | 登录、签到奖励、付费服务或官方支持 |

<a id="rule-index"></a>

## 📖 阅读导航

- [🔎 错误原文索引](#error-index) · [English reference](#english)：按报错和客户端直接定位。
- [平台与区域](#platform-scope)：先看哪些经验不能跨区域套用。
- [🧭 排障案例与验证来源](#incident-records)：遇到什么、怎么定位、怎么修复。
- [一、协议格式](#protocol-rules)：角色、工具选择、流式与用量。
- [二、客户端身份文本](#identity-rules)：Claude Code、Codex、DeepSeek Harness。
- [三、请求头](#header-rules)：调用方过滤与上游构造分开处理。
- [四、使用与反馈边界](#feedback-scope)：数据最小化与安全反馈。
- [🔗 相关项目与参考资料](#related-projects)：高关联实现与专题，单向参考、非背书。
- [五、免责声明与风险告知](#disclaimer)：授权、费用、数据、责任与许可证关系。

### 推荐阅读顺序

**确认授权与区域 → 阅读具体规则 → 用合成样例检查 → 在获准环境小范围验证 → 固定版本并保留回退**

---

非官方的 CodeBuddy、WorkBuddy 请求兼容规则分享：整理已有适配中的请求处理方式、适用边界和已知风险，供自建网关或代理参考。本仓库只提供文档，不包含执行器、测试或模型服务。

适用场景：用自建网关或代理把 OpenAI 格式（`/chat/completions`）的请求转发到 CodeBuddy / WorkBuddy。如果你的客户端发的是 Anthropic 格式（如 Claude Code 原生请求），先转成 OpenAI 格式，再套用下面的规则。

> **来源与验证范围**：本文包含从实际生产接入问题中积累的兼容规则。来源项目的修复历史记录了问题定位与处理，其中 DSH 路径组合和 assistant 历史有明确的真实上游隔离验证说明；并非只有合成样例依据。不同条目的记录详略不同，WorkBuddy 部分结论来自外部调研，见下方[排障案例](#incident-records)。本次文档整理没有重新执行全部历史实验，也未逐一复核原始请求记录。历史验证不等于当前所有版本、区域与账号均适用。
>
> 与腾讯及相关客户端项目无隶属或背书关系。使用前请核对服务条款和授权范围；身份文本处理应单独评估并显式选择，不承诺通过渠道校验或避免账号风控。

<a id="platform-scope"></a>

### 平台与区域

| 范围 | 本文身份文本规则的适用说明 |
|---|---|
| CodeBuddy | 来源实现包含这些兼容处理；不能据此推断所有区域、版本或账号均适用 |
| WorkBuddy 国内区 | 来源实现启用身份文本处理；仅代表已有实现策略，不是持续有效性承诺 |
| WorkBuddy 国际区 | 来源实现默认不启用身份文本处理；不得从同名业务码推断与国内区具有相同指纹规则。会话请求头构造与文本处理是两个独立问题 |

身份文本表中的客户端名称用于标识匹配对象，不表示已覆盖该客户端全部版本与 SDK 变体。

<a id="incident-records"></a>

## 🧭 排障案例与验证来源

以下是公开化后的经验摘要，不包含真实账号、完整提示词、线上请求转储或私有项目链接。**有历史生产验证的事实，与没有在本次整理中重跑实验的事实可以同时成立。**

- **P · 生产修复记录**：来源项目有对应修复提交和处理实现，但早期部分提交没有保留完整实验步骤。
- **A · 明确隔离验证记录**：生产修复说明明确记载真实上游的逐句探测或二分定位；本次没有重新审阅原始流量。
- **E · 外部调研记录**：来源调研引用外部实现或实验，不冒充本项目独立复现；本文未重新访问或复核外部实验。
- 本节按问题组织，不承诺是完整时间线，也不将某次成功推广为所有平台的通用规律。

### 证据与复核状态登记

**最近文档复核：2026-10-31。** 这是规则描述与来源记录的整理日期，不是对各平台重新进行真实请求验证的日期。下表补充案例表的共同元数据；具体适用范围仍以每条记录为准。

| 条目组 | 平台 / 区域 | 证据类型 | 历史验证信息与未知项 | 本次复核状态 |
|---|---|---|---|---|
| Claude 身份、反馈、分支与 Codex 来源句 | CodeBuddy 接入；历史区域、完整客户端版本未逐项确认 | P | 有修复历史；逐条真实实验日期、完整 A/B 原始记录未知 | 文档与修复说明核对；未重跑线上实验 |
| developer 角色、DSH 身份与 GUI 回归 | CodeBuddy 接入；不扩展到全部区域；developer 回退错误另有非 Buddy 上游 | P | 有原因与处理记录；完整模型 / 版本矩阵未知 | 文档与实现核对；未重跑线上实验 |
| assistant 身份复述、DSH 两句路径组合 | CodeBuddy 接入；不自动推广到 WorkBuddy | A | 修复说明明确记载真实上游隔离 / 二分；精确实验日期及完整版本矩阵未公开确认 | 核对隔离说明与规则边界；未重新读取原始流量 |
| 模型目录版本头、非流式与具名工具选择 | CodeBuddy 对应端点；目录与聊天分开看 | P | 目录版本错误有实现记录；非流式有接入验证说明；具名工具不主张全模型实测 | 描述与来源核对；无新增真实调用 |
| 国内区身份规则启用 | WorkBuddy 国内区 | 实现策略；借鉴 CodeBuddy 记录和外部材料，**非独立全链路验证** | 知道实现开启范围；逐条生产验证时间与客户端矩阵未知 | 仅确认来源实现策略 |
| 会话头、首条 system 错误形态 | WorkBuddy；会话头与国际区有关，首条错误的具体区域未知 | E + 本地适配实现 | 引用外部实验；不能记作本项目完成的独立复现 | 未重新核验外部实验或进行真实 A/B |
| 11140 / 429 / 6004 / 401 | 依实际上游、区域、账号分类 | 错误处理分类，**不是已解除限制的验证** | 不主张这些限制已被规则解决 | 仅核对分类边界 |

### 生产中积累的身份与角色处理

| 案例 | 遇到的现象与定位 | 采用的处理 / 历史结果 | 依据 |
|---|---|---|---|
| Claude Code 产品身份句 | CodeBuddy 渠道拒绝，后续修复针对固定产品身份样板 | 移除选定身份片段，保留任务指令；积累为 `identity.claude-code` | P：有独立修复提交，早期说明较简略，不声称保留了完整 A/B 记录 |
| Claude Code 反馈样板 | 身份句处理后仍继续补充固定反馈说明的兼容处理 | 移除对应反馈行；公开规则额外限定整行边界，避免误删相似 URL | P：有独立修复提交；更严格匹配边界属于文档建议，不代表每种变体都经过生产验证 |
| Claude Code Git 分支措辞 | 固定 Git 快照说明被纳入兼容修复 | 简化 `Main branch` 的说明措辞，保留实际分支名 | P：有独立修复提交，不单凭它断言该短语在所有环境单独触发拒绝 |
| Codex 产品来源句 | 修复说明记录开头的 Codex 来源样板导致 CodeBuddy 返回 `400 / 11128` | 删除来源样板，保留其余请求内容；记录为解除该次渠道拒绝的处理 | P：提交说明明确描述原因及处理，未记录全部客户端版本 |
| `developer` 角色 | CodeBuddy 最小 developer 消息也会被 `11128` 拒绝，不能只归因于正文品牌词 | 改为 system，保留内容且不修改原始回退请求 | P：修复记录和实现注释明确；角色优先级变化仍需宿主评估 |
| DSH 身份与 GUI 产品说明 | 修复记录将两类固定产品句与渠道拒绝联系起来 | 改写品牌措辞，保留运行时指令与其他候选的原始输入 | P：有对应修复记录 |
| DSH GUI 句式升级后再次被拒 | 旧规则匹配整句；客户端调整句尾后失配，品牌特征重新到达上游，返回 `11128` | 改成锚定固定前缀，不绑定具体地址和整句结尾 | P：修复说明明确记载回归原因与修改方式 |
| assistant 历史复述身份 | 会话中讨论适配规则后，模型自己的回复引用身份样板，导致下一轮整条请求被拒 | 对 assistant 仅处理已定位的 Claude 身份、反馈样板与 DSH 身份句，不泛删品牌词 | **A**：修复说明记载逐句请求真实上游并区分角色、工具定义和不同句子 |
| DSH 路径说明两句组合 | 前面特征处理后仍被拒；真实 system prompt 二分记录显示：两句分别通过、组合时 `400 / 11128` | 对两句作保留路径说明意图的改写，而非删除；修复记录描述该组合特征不再命中 | **A**：明确记载真实上游二分；不将单次通过理解为永远无法识别 |

**assistant 隔离实验的边界**：当时记录中，user/tool 消息、工具定义、普通品牌词、Codex 来源句与 DSH GUI 句未触发同类 assistant 拒绝，因此选用了更小的处理集合。这不意味着这些内容在任意平台和未来版本都安全，也不应据此改写用户数据。

### 请求头、消息形状与其他接入拒绝

| 案例 | 现象 / 定位 | 处理与边界 | 依据 |
|---|---|---|---|
| CodeBuddy 目录接口 | 请求普通 `/models` 得到 404；配置请求缺相应客户端版本头时，记录返回 `400` 和 `check ua, get coding copilot version error` | 用配置接口获取目录，单独核对该端点要求的版本头；不是所有对话请求通用的头部结论，见 [3.3](#catalog-headers) | P：接入历史与实现注释；不公开固定版本伪装配方 |
| WorkBuddy 会话头 | 外部 A/B 记录指出：文本已处理但缺少会话头时仍可返回 `11128` | 目前实现构造 `X-Conversation-*`，见 [3.2](#conversation-headers)；不据此判定国际区文本规则与国内相同 | **E**：外部实验引用，不作为本项目独立完成的隔离实验 |
| WorkBuddy 首条消息形状 | 外部资料记录 `first message is not system prompt`，也可能伴随 `11128` | 来源实现确保首条为 system；需要有效对话内容，不能用插入默认消息掩盖空请求 | E：错误形态来自调研；本地实现本身不是全部场景通过的证明 |
| CodeBuddy 非流式 | 真实接入记录上游拒绝非流式：`400 / 11101` | 上游流式、网关按需聚合；初始接入提交记录流式、聚合与工具调用等路径验证成功 | P：生产接入验证记录；不是身份识别问题 |
| CodeBuddy 具名工具选择 | 来源修复针对不接受对象式工具选择的兼容问题 | 仅提供目标工具并使用字符串 `required`；历史工具调用的完整性仍需检查 | P：有修复实现；不将现有回归测试当作所有模型真实验证 |
| 回退目标拒绝 developer | 排障说明记录最终 `422 unknown variant developer` 来自另一家回退上游，不是 CodeBuddy | 通用 OpenAI 兼容路径也规范化角色；提示排查时分清每次尝试的真实上游 | P：生产排障说明；不是新增的 Buddy 指纹规则 |

WorkBuddy 外部记录的原始参考项目包括 [WorkBuddy2API-Hub](https://github.com/ardeyouxipianyi/workbuddy2api-hub)；本文不复制其源码、不承诺其当前状态，也不把外部验证计入本项目亲自实测的数量。

<a id="not-identity-fixes"></a>

### 哪些不能归入“清洗已解决”

`401` 登录失效、`429 / 6004` 配额或频率、模型权限不足、余额问题及 `11140` 相关限制，应单独分类。实现中存在错误处理分支，不代表亲自遇到并成功解除过每种限制；更不能将账号风控解释为换几个词即可解决。

<a id="protocol-rules"></a>

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
| `compat.workbuddy-token-limit` | WorkBuddy | 本次补充并做合成回归的字段别名规范化，尚未真实模型验证 | 将 `max_completion_tokens` 映射到 `max_tokens` 并移除原别名；两者同时存在时以显式 `max_tokens` 为准，不修改原请求。不同模型的推理预算语义可能不同，不能保证完全等价 |

注意：

- CodeBuddy 缩减工具列表后，如果历史消息里调用过其他工具，上游可能因为找不到那些工具而拒绝请求，需要在你的工作流里实测。
- 只在必要字段应用明确规则；身份文本处理仅作用于表中指定的 system / developer / assistant，不修改 user/tool 正文，也不删除图片等非文本内容块。
- 转换前复制输入，避免污染其他上游的回退请求。不要丢失工具调用消息与其对应结果。
- 宿主仍需校验有效消息、工具结构与目标协议要求；只补一条默认 system 并不能让空请求成为有效对话。

### 生态规则差异复核（2026-10-31）

本次以外部公开材料作问题线索，再检查来源实现；没有执行第三方代码或调用真实上游。以下不是新增的“生产上游验证成功”记录：

- **已修正实现**：保留现有 `stream_options`，只强制用量开关；反馈样板仅匹配独立整行，保留相似 URL、issue 详情、查询串与同行任务说明。后者使实现与本仓库已有的严格匹配描述保持一致。
- **已补合成回归的已有边界**：逐个标准 text 块处理，保留图片、缓存元数据、工具调用及结果关联、user/tool 正文；验证输入不变和重复处理。这些不是此前完全缺失的能力。
- **新增的字段别名处理**：见 `compat.workbuddy-token-limit`。有本地合成回归，不宣称真实平台验收完成。
- **未直接采纳**：全局替换品牌、工具单向改名、改变 tuple/enum/regex 语义的 schema“修复”、tool→user 无条件插空 assistant、以首问内容推定会话，以及照搬其他站点固定身份头。这些可能丢失工具约束、破坏响应名称回传或混淆会话，不能仅凭其他项目的 PR 自述就作为通用规则。
- **继续验证的方向**：工具名与 `tool_choice` 的双向映射、schema 语义保真、注入/合并顺序、跨轮次与重试 ID 的生命周期矩阵。国际区文本处理范围没有因本次调研而扩大。

<a id="identity-rules"></a>

## 二、客户端身份文本

这些固定句子可能表明请求来自某个客户端。来源注释曾将部分 `HTTP 400 / code 11128` 与客户端特征联系起来，但 **`11128` 本身不足以证明命中了客户端指纹**：渠道校验、消息结构或协议头等问题都应分别排查，不能仅凭业务码确定原因。本文不把该业务码定义为官方错误码规范。

两种处理方式：

- **删除**：针对选定的产品样板片段（Claude Code、Codex）；即使是样板，删除也可能改变模型行为，需要宿主回归验证。
- **改写**：对包含任务上下文的句子尽量保留含义（DSH）；不保证语义完全等价，也不保证改写后能通过当前平台校验。

<a id="claude-codex-rules"></a>

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

<a id="dsh-rules"></a>

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

<a id="header-rules"></a>

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

<a id="conversation-headers"></a>

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

<a id="catalog-headers"></a>

### 3.3 CodeBuddy 模型目录请求的版本检查

来源接入实现记录：模型目录不是从普通 `/models` 获取，而是从 `/v3/config` 获取；配置请求缺少对应 `User-Agent` / `X-IDE-Version` 时，曾返回 `400` 和 `check ua, get coding copilot version error`。这条经验只针对该目录端点，**不能自动套用到对话端点或 WorkBuddy**。

集成时应先确认端点可用性及接入授权，再依据获准方式核对版本要求；不要把某个历史固定版本当作永久有效值，不透传调用方 Agent 的 UA 代替目标端点的版本要求。本仓库不提供官方身份伪装或保证通过版本校验的固定头部值。

<a id="feedback-scope"></a>

## 四、使用与反馈边界

- 仅记录规则 ID、修改位置和必要状态，不默认保存请求正文、请求头值或完整错误体。错误响应也可能含身份信息。
- 分享问题时使用合成最小样例，不提交真实 Token、Cookie、授权 state、用户/会话 ID、本机路径、私人域名或完整系统提示词。
- 固定所参考的提交版本，在自己的工作流回归后更新；规则分享不是远程自动下发配置。
- `11128` 应结合 HTTP 状态、请求结构与受控排查结果分析；不能通过修改错误码掩盖上游拒绝。配额不足、登录失效、权限不足和账号风控应分别处理，不属于身份文本改写可以解决的问题。

- 普通问题请在 [Issues](https://github.com/CamarilloG/codebuddy-workbuddy-rules/issues) 中提供**合成、去标识化**的最小样例。敏感漏洞优先使用 [GitHub 私密漏洞报告](https://github.com/CamarilloG/codebuddy-workbuddy-rules/security/advisories/new)，不要先公开细节。

<a id="related-projects"></a>

## 🔗 相关项目与参考资料 / Related projects

**单向参考列表，不是已建立互链的“友情链接”，也不表示合作、推荐、代码依赖、授权或安全背书。** 本仓库专注规则与排障说明，下列项目主要提供运行实现或 Agent 集成。能力和维护状态依据 2026-10-31 的公开资料快照，未运行验收，后续请以各项目自身说明为准。

| 项目 | 与本文的关联 / 值得参考的内容 | 注意事项 |
|---|---|---|
| [WorkBuddy2API Hub](https://github.com/ardeyouxipianyi/workbuddy2api-hub) | 国内/国际独立网关、多 Agent 配置、兼容修复记录 | README 宣告低频维护；Messages 是实验性能力，不当作全场景支持保证 |
| [WorkBuddy Local Gateway](https://github.com/CangShui/workbuddy-gateway) | Go 网关；[出站兼容](https://github.com/CangShui/workbuddy-gateway/blob/b65634ae098bddaff9b786e1d04d8288c012c211/docs/outbound-compatibility.md)与 [DSH 历史/文本块专题](https://github.com/CangShui/workbuddy-gateway/blob/b65634ae098bddaff9b786e1d04d8288c012c211/docs/11128-dsh-history.md)（复核时固定版本） | 文档中的验证范围与实际实现需分别看；不据此扩大本仓库验证范围，复用代码前自行核对许可 |
| [OmniRoute](https://github.com/cheaper-inference/OmniRoute) | 多供应商网关；[WorkBuddy 兼容 PR #17046](https://github.com/cheaper-inference/OmniRoute/pull/17046) 提供头部、工具 schema、消息形状与 ID 设计的研究线索 | 已合并不等于每项处理都适合本项目；PR 自述与本仓库独立验证不同 |
| [dsh-connect-workbuddy](https://github.com/dingminhua/dsh-connect-workbuddy) | WorkBuddy 接入 DeepSeek Harness 的插件；模型目录、双区域和具体 Agent 接入体验 | 依赖非官方开放 API 的客户端接口；项目不承诺长期可用，本仓库没有代其验收 |
| [magpie](https://github.com/yetone/magpie) | 多 Agent / 多供应商网关、配置与插件生态 | 不仅面向 Buddy；README 指明社区反馈走 Discord、不接受外部 PR，联系前先看当前规则 |

欢迎提出有明确关联的资料建议：说明具体问题、对应章节和证据类型即可；不收录账号售卖、凭证分享、无关广告或“永久免封”承诺。这里的参考不增加 Apache-2.0 的许可限制。

<a id="disclaimer"></a>

## 五、🛡️ 免责声明与风险告知

> [!IMPORTANT]
> 以下内容旨在说明项目边界和已知风险，**不是法律意见，不是“绝对免责”承诺，也不能使未经授权的行为合法化**。免责声明的效力取决于适用法律和具体事实。涉及商业运营、第三方转接或较高风险用途时，应取得所需授权并咨询合格专业人士。

<details open>
<summary><strong>1—4 · 项目性质、平台授权与使用范围</strong></summary>

### 1. 非官方、无关联与无代理关系

本项目由独立维护者分享，不代表腾讯、CodeBuddy、WorkBuddy、Anthropic、OpenAI、DeepSeek Harness 或其他第三方。产品名、接口名、字段名及片段仅用于识别讨论对象，不构成官方认证、合作、推荐或背书。维护者无权代表相关平台批准接入、解释合同或承诺账户待遇。

### 2. 文档不是服务，也不是专业意见

当前主分支只提供技术文档与许可证，不提供模型推理、代理运营、账号交易、充值、登录、凭证保管、计费或售后服务。文档中的观察、示例和建议不构成法律、财务、安全审计、隐私合规或其他专业意见，也不替代官方文档与独立评估。

### 3. 开源许可不等于第三方服务授权

Apache-2.0 处理本项目作品的许可，不授予任何第三方账号、API、订阅额度、客户端渠道、商标或非公开系统的访问权。购买订阅、持有有效 Token、访问官方域名或技术上能够调用，均不当然表示允许第三方客户端、中转、共享、转售、自动化或商业运营。使用者应自行核对适用条款及授权范围；不清楚时应先向权利人确认。

### 4. 不鼓励未经授权或违法使用

本文不邀请使用者绕过访问控制、风控、支付、限额、身份验证或安全措施，不鼓励盗用凭证、共享他人账号、批量滥用、欺诈、侵犯隐私或其他违法行为。遇到明确拒绝、账号限制或平台禁止的用途，应停止并通过获准渠道处理，不应靠反复变更身份来继续访问。此为风险提示，不新增或改变 Apache-2.0 的许可条件。

</details>

<details>
<summary><strong>5—9 · 技术效果、账号、费用与部署风险</strong></summary>

### 5. 不保证准确、完整、实时或兼容

内容可能过时、有误、不完整或存在理解偏差。来源注释与历史观察不是本仓库独立复核的现行事实。平台、区域、账号类型、灰度策略、客户端与模型版本的差异，都可能使规则失效。未承诺无错误、持续可用、覆盖全部场景、符合特定用途或不侵犯第三方权利；适用范围以许可证及法律规定为准。

### 6. 不保证语义与工具行为保持不变

角色降级、文本删除、正则改写、工具列表缩减、头部过滤与会话关联可能改变指令优先级、模型输出、工具调用、上下文、缓存或推理行为。错误匹配可能造成内容丢失；错误聚合可能造成截断被误判成功。使用者需要自行验证正例、反例、幂等性与回退机制，不应直接用于高风险或不可逆操作。

### 7. 账号与渠道风险

不承诺“免封号”“官方认可”“无法识别”或“必过校验”。即使规则曾生效，平台仍可能拒绝请求、要求重新认证、限流、冻结或终止账号与权益。维护者不能控制或恢复第三方账号，不能保证申诉、退款或额度恢复。文本转换也不能替代真实授权。

### 8. 费用、额度与经济损失

请求、重试、探测、流式聚合、工具调用、自动化和日志存储可能产生费用、消耗积分或触发额外计费。空响应、失败响应和网络中断未必不计费。本文不保证免费、不保证价格或用量统计准确；退款与账单争议由实际服务关系及适用规则处理，不因本仓库分享而形成维护者代付、报销或赔偿承诺。

### 9. 宿主集成、生产与高风险用途

实现、部署、密钥管理、网络、超时、重试、并发、资源限制、可观测性与回滚由实际运营者负责。文档不是经过认证的安全组件，也不是医疗、金融、法律、关键基础设施等高风险用途的可靠性保证。使用者应根据风险采取人工复核、最小权限、费用上限和隔离措施；这些建议不能代替专业安全评估。

</details>

<details>
<summary><strong>10—13 · 数据隐私、安全、第三方内容与贡献</strong></summary>

### 10. 隐私与数据处理

当前文档本身不接收或转发使用者的模型请求；GitHub 页面、徽章与外部链接仍可能由相应服务商记录访问，适用其隐私政策。宿主转发可能把个人信息、业务秘密、源代码、提示词、工具结果或附件发送给第三方或其他地区。使用者应核实处理依据、告知与同意、保密义务、保留期限及跨境要求。身份清理不等于匿名化，也不保证去除所有可识别信息。

### 11. 凭证与安全事件

不要向本仓库、公开 Issue、PR 或评论提交真实凭证、Cookie、授权 state、用户/会话标识、私人地址、完整提示词或日志。发现泄露应立即撤销或轮换凭证并采取必要补救；删除评论、文件或提交不能保证消除 Git 历史、缓存、镜像、克隆与索引中的副本。维护者不能承诺替使用者清除互联网副本或承担第三方存储的安全保障。

### 12. 第三方权利、链接与衍生内容

第三方商标、产品、文字和其他材料的权利归相应权利人；本项目不授予其独立许可。外部链接、徽章、Fork、转载、翻译、讨论和他人建议不受维护者完全控制，可能失效、错误或被更改。转载者的收费、支持或担保不代表本项目承担同样义务。发现疑似侵权或敏感信息时，可通过安全渠道提供定位与必要证明；维护者可核查并更正，但不因此预先承认主张成立。

### 13. 反馈、贡献与信息最小化

提交者应确认有权公开所提交内容，避免泄露雇主、客户、平台或其他第三方的保密材料。请只提供合成的最小复现与必要版本信息，不以真实线上转储替代复现。贡献的许可处理遵循 Apache-2.0 第 5 条及另行书面约定；不要求额外转让权利，也不因参与讨论当然建立保密、雇佣、委托或服务关系。公开协作渠道不适合传递秘密。

</details>

<details>
<summary><strong>14—17 · 维护、担保、责任限制与法律保留</strong></summary>

### 14. 无持续维护与服务等级承诺

除非另行书面约定，不承诺答复时限、修复期限、更新频率、兼容周期、功能开发、持续托管、免费支持或 SLA。维护者可能修订、移除文档、关闭讨论或归档项目；仓库状态、Star、徽章与发布日期都不是质量或持续服务保证。内容更新不会追溯消除已发生的风险，也不会自动使旧版本安全有效。

### 15. 按现状提供与责任限制

在适用法律允许且无另行书面约定的范围内，本作品按“现状”（AS IS）提供，不提供明示或默示的担保或条件；担保排除及责任限制以 Apache-2.0 第 7、8 条为准。使用或无法使用可能导致账号权益、数据、利润、商誉、业务连续性、设备或其他损失。是否承担责任、责任范围与救济方式仍由有效约定、适用法律及具体事实决定，不能仅凭本文预先排除全部责任。

### 16. 不排除法定不可免责责任

本声明不试图排除或限制法律规定不得排除或限制的责任及权利，包括在适用情况下因故意、重大过失、人身损害等产生的责任和不可放弃的法定权利。不得以“仅供学习”“使用即同意”或“后果自负”等措辞当然免除本应承担的义务；本文也不主张访问页面或使用内容即形成新的合同。

### 17. 与许可证及法律的关系

本节是风险告知和说明，不修改、替代或缩减 [Apache-2.0 正文](LICENSE) 授予的权利，不增加“禁止商用”“仅限学习”“限时删除”等与既定许可证冲突的附加条件。若表述冲突，许可证事项以许可证正文为准，强制性法律规定优先。某项声明无效或不适用，不当然使其他依法有效的部分失效；具体效力仍需依法判断。本项目不另行指定争议管辖地，也不宣称某一法域的免责声明对所有地区都有效。

</details>

### 使用前自查

- [ ] 我已确认第三方平台允许拟采用的接入方式，而非仅持有可用凭证。
- [ ] 我了解区域、版本与账号差异，未把历史观察当作官方现行规范。
- [ ] 我已用合成样例检查改写边界、工具行为和回退，不直接盲目上线。
- [ ] 我已设置凭证保护、数据最小化、费用控制与必要人工审核。
- [ ] 我知道此文档不提供法律授权、账号保障或绝对免责。

---

## 📜 许可证与致谢

[Apache-2.0](LICENSE)。CodeBuddy、WorkBuddy、Claude Code、Codex、DeepSeek Harness 等名称仅用于说明兼容目标，商标及相关权利归各自权利人。

感谢提供**去标识化、可核查、边界清晰**反馈的贡献者。欢迎修正文档；请不要提交账号、真实请求或私人运行时上下文。

<div align="center">

**规则分享，不是服务承诺。清楚边界，比堆叠补丁更重要。**

[返回顶部 ↑](#top)

</div>
