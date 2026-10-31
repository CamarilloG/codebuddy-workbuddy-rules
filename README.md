# CodeBuddy / WorkBuddy Rules

**非官方的 CodeBuddy、WorkBuddy 请求兼容规则与 Python 参考执行器。**

面向自建网关、代理和 Agent 工作流：规则在一个地方维护，宿主固定版本引用，自行完成认证、请求发送与响应处理。不是 API 中转服务，不提供账号、Token、模型额度或登录功能；与腾讯及相关客户端项目无隶属或背书关系。

> 未进行真实平台请求验证，不承诺任何规则能解决当前渠道限制。身份规则默认关闭，请在确认授权与影响后显式选择。

## 包含什么

- **协议兼容**：developer → system；CodeBuddy 具名函数选择转换为仅保留目标工具的 `required`；WorkBuddy 补充 system、流式和用量参数、移除 assistant 空工具列表。
- **请求头边界**：默认仅允许 `accept`、`content-type`；不透传调用方凭证、Cookie、会话头和客户端产品头。未知头默认丢弃，而不是维护不完整的黑名单。
- **可选身份文本规则**：Claude Code 产品身份与反馈样板、Codex 产品身份。默认不改写，必须逐个规则 ID 启用；只处理指定角色与文本块，不处理 user/tool 正文或非文本块。
- **修改记录**：返回规则 ID、字段位置、操作类型，不包含正文与请求头值。
- **可同步规则清单**：见 [规则清单](buddy_rules/rules.json)，包含身份文本规则与请求头策略。协议兼容转换、执行顺序、区域门槛和异常行为目前定义在 [Python 参考实现](buddy_rules/__init__.py) 中；仅复制 JSON 不足以复现全部行为，跨语言实现还须对照源码和回归测试。

不包含：官方客户端身份头伪装、账号登录、签到奖励、凭证刷新、SSE 聚合、故障切换、自动网络同步、私有部署配置。没有提供 DSH 运行时提示词或个人工作流规则。

## 安装与接入

Python 3.10+，运行时零第三方依赖。在仓库目录执行：

```sh
python -m pip install .
python -m unittest discover -s tests -v
```

```python
from buddy_rules import transform

result = transform(
    {"messages": [{"role": "user", "content": "Hello"}]},
    {"Content-Type": "application/json", "User-Agent": "MyClient/1.0"},
    platform="codebuddy",  # 或 workbuddy
    region="cn",          # cn / intl
)

# 在宿主中使用 result.payload 和 result.headers。
# 此后由宿主注入目标平台凭证和获准使用的协议头；不要注入调用方凭证。
# result.changes 可用于审计，但不要默认记录 result.payload。
```

明确有权采用对应转换后，才选择启用身份规则：

```python
result = transform(
    payload,
    platform="codebuddy",
    identity_rules=("identity.claude-code",),
)
```

WorkBuddy intl 不继承国内区身份规则：如果显式选身份规则，还需额外指定 `allow_international_identity=True`。这是防误用门槛，**不是国际区兼容性或授权证明**。

`extra_forward_headers=("x-trace",)` 可扩展透传允许列表，但不能放行已知凭证、逐跳头和客户端身份头。宿主仍须确保新增字段没有用户隐私。会话关联应由宿主单独设计，不要把用户会话 ID 当成可公开共享的规则值。

## 规则契约与限制

1. 先复制输入，不原地修改，避免污染其他供应商回退候选。
2. 不修改 user/tool 消息；不丢弃工具调用消息和非文本内容。身份规则清空文本后保留空文本/消息结构，由宿主完成目标协议校验。
3. 规则不保证语义完全无损：角色降级、工具列表缩减、身份文本删除均可影响行为，应在宿主工作流测试。
4. CodeBuddy 的流式限制仍需宿主适配；本库不会把非流式自动聚合成完整回复。
5. HTTP 请求头输出统一小写。不生成授权头、官方产品 UA、版本、账号或会话标识。
6. Change 记录不会回显正文或任意输入头名称，但 payload/headers 本身仍可能含隐私，不能直接打日志。
7. 公共样板匹配不等于第三方渠道获准；不保证通过渠道校验，不提供防封号承诺。

## 验证与更新

本版只通过合成回归样例验证转换行为，**没有真实平台验证日期或官方支持承诺**。不要把过去某版本的行为当作当前事实。规则失效时记录平台/区域/客户端版本、最小合成复现和预期差异，不能提交原始请求转储。

生产环境固定 tag/commit，更新后运行自己的回归测试再部署；不下载并执行远端最新规则。不支持在配置中注入任意可执行脚本。

## 安全与贡献

- [安全说明](SECURITY.md)：漏洞报告及数据最小化。
- [贡献规范](CONTRIBUTING.md)：规则分类、反例、变更记录与隐私要求。
- [变更记录](CHANGELOG.md)。

本库不是官方 SDK。CodeBuddy、WorkBuddy、Claude Code、Codex 等名称仅用于说明兼容目标，商标归各自权利人。使用者须核对服务条款、授权范围与所在环境的合规要求。本项目按 [Apache-2.0](LICENSE) 许可证发布。
