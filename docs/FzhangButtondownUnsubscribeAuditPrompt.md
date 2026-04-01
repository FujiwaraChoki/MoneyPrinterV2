# 给另一个 AI 的 Buttondown 退订与合规检查提示词

你现在要审查并改进 `fzhang.dev` 当前的 Buttondown 邮件链路，重点是：

1. 为什么确认邮件和资源交付邮件里看不到退订链接
2. 哪些邮件必须有退订或订阅管理入口
3. 应该如何用 Buttondown 的正确方式修复

不要泛泛给建议。请基于当前实现，给出明确判断、配置修改建议、模板修改方案和验证步骤。

## 当前已知情况

- 资源页和订阅页都已切到自建 `/api/subscribe`
- 新订阅者会收到确认邮件
- 确认后会收到资源交付邮件
- Buttondown 后台可以看到订阅者信息变化
- 但用户现在看不到明确的退订链接

## 你必须先核对的 Buttondown 官方约束

请先对照这些事实检查现有实现是否合理：

- Buttondown 官方文档显示：
  - `confirmation email` 可用变量只有 `confirmation_url`、`newsletter.name`、`newsletter.description`、`newsletter.absolute_url`、`subscriber.email`
  - 也就是说，确认邮件模板本身没有 `unsubscribe_url`
- Buttondown 官方文档显示：
  - 普通邮件可以手动插入 `{{ unsubscribe_url }}`
  - Buttondown 也会在邮件 footer 自动附加退订链接
- Buttondown 官方文档显示：
  - `welcome email` 支持 `unsubscribe_url`
  - `welcome email` 支持 `manage_subscription_url`
- Buttondown 官方文档显示：
  - 开启 Portal 后，订阅者可通过 `manage_subscription_url` 管理订阅
  - Portal 也会自动出现在邮件 footer

## 你的任务

### 任务 1：判断当前“看不到退订链接”是不是配置问题，还是 Buttondown 机制本来如此

你要明确区分：

- 确认邮件为什么可能天然没有退订链接
- 资源交付邮件为什么理论上应该有退订或管理入口

### 任务 2：检查当前站点链路里，资源交付邮件到底属于哪一类

判断它是：

- Buttondown welcome email
- Buttondown automation email
- 普通 newsletter email
- 还是自定义事务型邮件

并分别说明：

- 如果它是 welcome email，应该怎么写模板
- 如果它是 automation / newsletter email，应该怎么保证 footer 和 `unsubscribe_url`
- 如果它是自定义事务型邮件，应该如何补订阅管理入口

### 任务 3：给出最推荐的修复方案

你必须给出一个明确优先级，不要只罗列可能性。

至少包含：

1. 是否开启 Buttondown Portal
2. 是否在 welcome / resource delivery 邮件正文里显式加入：
   - `{{ unsubscribe_url }}`
   - `{{ manage_subscription_url }}`
3. 确认邮件里如果不能提供退订链接，应该用什么替代文案降低困惑
4. 哪些邮件必须出现退订或管理订阅入口

### 任务 4：给出验证 checklist

至少覆盖：

- 新邮箱首次订阅
- 收到确认邮件
- 确认后收到资源交付邮件
- 邮件正文是否有订阅管理入口
- footer 是否自动出现
- 点击后能否进入管理 / 退订页面
- 旧订阅者再次领取资源时是否仍能看到订阅管理入口

## 输出要求

请按下面结构输出：

1. 当前问题的根因判断
2. Buttondown 机制边界
3. 推荐修复方案
4. 需要修改的模板文案
5. 需要检查的 Buttondown 后台设置
6. 一份逐项验收 checklist

## 官方文档入口

- Confirmation email:
  - https://docs.buttondown.com/transactional-emails-confirmation
- Welcome email:
  - https://docs.buttondown.com/transactional-emails-welcome
- Sending emails / custom unsubscribe links:
  - https://docs.buttondown.com/sending-emails#avoiding-the-promotions-tab
- Portal:
  - https://docs.buttondown.com/portal

## 额外要求

- 不要建议“手动回复用户完成退订”
- 不要把“没有退订链接”简单归因于前端问题
- 要明确区分确认邮件、欢迎邮件、资源交付邮件、普通更新邮件的责任边界
