# fzhang.dev 免费资源领取与自动回信蓝图

## 当前实站状态

我已实际检查 `https://www.fzhang.dev/` 与 `https://www.fzhang.dev/resources/open-source-ai-deployment-checklist/`，当前状态是：

- 免费资源页存在，当前前端表单已提交到自建 `/api/subscribe`
- 当前资源页表单字段包括：
  - `email`
  - `name`
  - `message`
  - 隐藏字段 `request_type=free_resource_download`
  - 隐藏字段 `signup_intent=resource-checklist`
  - 隐藏字段 `resource=开源 AI 项目部署前检查清单`
  - 隐藏字段 `topic=deployment`
  - 隐藏字段 `source_page=/resources/open-source-ai-deployment-checklist/`
  - 隐藏字段 `download=/downloads/open-source-ai-deployment-checklist.md`
- 当前 `订阅` 页已经不是 RSS-only，而是邮件订阅 + RSS 双入口
- 当前成功页会把用户引导到确认邮箱的后续流程
- 根据后续代码审查结果，当前资源本身是站内即时解锁，不是通过 Buttondown 邮件交付

这意味着：

- 你已经有资源领取入口
- 站点结构已经从“纯 RSS + 纯表单”升级成“站内资源领取 + Buttondown 订阅”
- 但当前不应误判为“完整自动化邮件系统已经全部落地”

## 当前验收结论

根据线上页面检查与后续代码审查结果，下面这些已经基本成立：

- 资源页已明确区分公开文章与执行版资源
- 表单已切到自建接口而不是纯表单托管
- 订阅页已完成邮件 + RSS 双路径
- 成功页已具备确认订阅与后续更新预期管理
- 资源交付当前主要依赖站内即时解锁，不依赖 Buttondown 发“资源交付邮件”

还不能只靠浏览器确认的部分：

- 确认邮件是否真实发出
- 是否写入正确标签
- Welcome 邮件是否已带管理订阅和退订入口
- 低频分群发送是否按设计执行

所以当前状态更准确的说法是：

> 前端与信息架构已经明显升级，但当前更接近“站内即时交付 + Buttondown 订阅确认 + Welcome + 低频分群发送”，还不是完整的多步自动化邮件系统。

## 已确认的实现边界

根据你补充的检查结果，当前应按下面这套边界理解系统：

### 1. 确认邮件没有退订链接是正常现象

- 这是 Buttondown double opt-in 的确认步骤
- 它不是正式 newsletter，也不是后续内容邮件
- 在用户还没完成确认前，Buttondown 不把这次关系视为已激活订阅

所以：

- 不应把“确认邮件里没有退订链接”视为 bug
- 不应花时间硬改确认邮件去补一个并不适配的退订入口

### 2. 当前并不存在“资源交付邮件”

当前更准确的交付路径是：

- 用户提交资源表单
- 站内即时解锁下载
- 如果用户勾选或进入订阅路径，则再进入 Buttondown 订阅关系

这意味着：

- 资源本身不是通过 Buttondown welcome / automation / transactional 邮件交付
- 不应继续把“资源交付邮件”当成当前系统的既有事实

### 3. 当前真正存在的邮件职责

当前应区分为：

- `Confirmation Email`
  - 负责确认订阅
- `Welcome Email`
  - 负责说明订阅了什么
  - 负责告诉用户先看什么
  - 负责提供管理订阅和退订入口
- 后续低频分群发送
  - 只在 deployment 主题下有新资源、新 SOP、重要相关文章时再发

## 当前最合理的运行模型

当前最符合现实、且对 Frank 负担最低的模型不是“多步全自动 drip”，而是：

`资源页 -> API -> Buttondown subscriber + tags -> confirmation -> welcome email -> 按 topic-deployment 低频分群发送`

这套模型的特点是：

- 资源继续站内即时交付
- 邮件只承担订阅关系和后续更新
- 当前先不强行上复杂 CRM 或重自动化
- 后续如果方案升级，再补 2 到 3 封 follow-up 或 RSS digest

## 推荐方案

不要把“自动回信”理解成邮箱规则自动回复。

更成熟的做法是：

`资源领取 -> 站内即时交付 -> 进入订阅系统 -> 标签化 -> Welcome 邮件 -> 低频主题更新`

我建议你采用两层结构：

### 第一层：资源交付

负责把免费资源立刻交付给用户。

当前最省力的实现：

- 继续保留站内即时解锁
- 不把免费资源强行改成邮件附件或邮件下载链接

原因：

- 维护成本最低
- 用户拿资源最快
- 不会把 welcome 邮件错误地承担成“资源交付邮件”

### 第二层：长期订阅

负责后续更新、标签、分组和少量自动化。

我建议优先用 `Buttondown`，原因是它更贴近你的博客形态：

- 支持标签与自动化
- 支持 RSS-to-email
- 适合内容站而不是纯销售漏斗站
- 支持自定义嵌入表单和 metadata

## 为什么当前不急着上更重的自动化

当前更重要的不是把系统做复杂，而是把现实链路跑稳。

当前不建议优先投入的方向：

- 为了 2 到 3 封 follow-up 额外接 Zapier / Make
- 为了显得先进而上复杂 CRM
- 对所有新文章做自动逐篇群发
- 把弱相关文章也硬塞给 `topic-deployment` 订阅者

## 为什么更适合 Buttondown

根据 Buttondown 官方文档与当前代码审查结果，它支持：

- 通过 API 创建 subscriber
- 通过标签做分群
- 基于 tags 做分群
- 在升级方案后再使用 automations / RSS-to-email

这和你当前的站点结构是匹配的：

- 你本来就有 RSS
- 你的网站本来就是内容站
- 你后续需要的是“围绕主题的持续更新”，不是高频运营系统

## 当前最推荐的落地路径

当前阶段最推荐的路径已经不是“二选一设计题”，而是：

1. 保留资源页即时解锁
2. 保留 API 写入 Buttondown + tags
3. 保留 confirmation
4. 把 Welcome Email 做完整
5. 后续只按 `topic-deployment` 做低频分群发送
6. 以后如果付费升级，再接 2 到 3 封 follow-up 或 RSS digest

这条路径的优点：

- 最低维护成本
- 符合你当前免费方案的能力边界
- 不需要额外引入重运营工具
- 能先把“主题订阅关系”跑稳

## 推荐的数据模型

无论选哪条路径，至少统一这些字段：

- `email`
- `name`
- `resource`
- `request_type`
- `source_page`
- `interest_topic`
- `submitted_at`

当前已知关键标签：

- `lead-magnet`
- `resource-checklist`
- `topic-deployment`
- `source-fzhang-dev`
- `site-updates`
- `owned-audience`

如果后续还会有别的资源，再继续扩：

- `resource-self-hosting-risk-sheet`
- `resource-ai-tool-stack`

## 推荐的订阅逻辑

### 最成熟的处理方式

1. 用户提交资源表单
2. 资源在站内即时交付
3. 如果用户进入订阅路径，则收到确认邮件
4. 确认后收到 Welcome Email
5. 之后只在 deployment 主题下有真正值得发的更新时，再低频分群发送

这比“提交后直接把人扔进长期群发”更适合当前阶段，原因是：

- 更合规
- 保持订阅质量
- 降低运营负担
- 不会为了自动化而自动化

## 当前推荐的邮件结构

### Email 1：Confirmation Email

触发：

- 用户提交订阅后立即发送

目的：

- 完成 double opt-in 确认

边界：

- 不必强求退订链接
- 不应被误判为正式 newsletter
- 只需完成确认动作

### Email 2：Welcome Email

触发：

- 用户确认订阅后

目的：

- 说明订阅了什么
- 告诉用户先看什么
- 给出主题预期
- 显式提供管理订阅和退订入口

建议正文必须包含：

- `{{ manage_subscription_url }}`
- `{{ unsubscribe_url }}`
- 一条起步阅读入口
- 一条关于后续发送节奏的说明

### Email 3 之后：低频主题更新

触发：

- Frank 真的发了 deployment 主题下值得发的新资源、新 SOP、重要相关文章或主题汇总

建议：

- 当前不做所有文章自动逐篇发
- 当前优先低频、分群、主题相关
- 如果未来升级，再加 fixed cadence 的 digest 或 follow-up automation

## 你的站点应该怎么改

### 资源页

- 保留资源领取页
- 明确说明“这不是公开文章复述”
- 增加执行预览
- 降低表单摩擦
- 增加许可说明：
  - 会收到这份资源
  - 可能收到这一主题下的后续更新
  - 可随时退订

### 订阅页

现在的订阅页只有 RSS，这不够。

建议改成双入口：

- 主要入口：邮件订阅
- 次要入口：RSS 订阅

这样不会破坏你喜欢 RSS 的站点气质，同时也能承接资源用户。

## 实现步骤

### 方案 A：Formspree + Buttondown

1. 在 Formspree 开启 autoresponse
2. 交付第一封资源邮件
3. 若你的 Formspree 计划支持 Webhooks，则配置 webhook
4. webhook 把 `email/name/resource/source_page` 发到你的同步服务
5. 同步服务调用 Buttondown API，创建 subscriber 并打标签
6. 在 Buttondown 中创建：
   - welcome / nurture automation
   - RSS-to-email automation

### 方案 B：Serverless + Buttondown

1. 前端表单发到 `/api/resource-signup`
2. 后端验证 Turnstile
3. 后端发送资源交付邮件
4. 后端调用 Buttondown API 创建 subscriber
5. subscriber 打上：
   - `lead-magnet`
   - `resource-checklist`
   - `topic-deployment`
   - `source-fzhang-dev`
6. Buttondown 负责后续 automation 和 RSS-to-email

## 关键优化点

### 1. 不要把“后续更新”说得太虚

改成更具体的话术：

- `后续如果我继续完善这条线，比如更完整的 SOP、风险速查表或相关文章更新，也会优先发给你。`

### 2. 不要一上来收太多信息

资源领取阶段先拿：

- 邮箱
- 可选称呼

项目上下文可以在后续邮件里再收。

### 3. 不要把订阅页继续做成 RSS-only

RSS 应该保留，但不该继续独占“订阅”入口。

### 4. 把资源交付和长期订阅分层

这是成熟方案最重要的区别之一。

- 资源交付邮件：事务型
- 后续更新邮件：订阅型

## 官方文档依据

- Formspree autoresponse: https://help.formspree.io/hc/en-us/articles/360025007233-Sending-a-confirmation-or-response-email
- Formspree webhooks: https://help.formspree.io/hc/en-us/articles/360015234873-Webhooks
- Buttondown automations: https://docs.buttondown.com/automations-introduction
- Buttondown create subscriber API: https://docs.buttondown.com/api-subscribers-create
- Buttondown RSS-to-email: https://docs.buttondown.com/rss-to-email
- Buttondown subscriber base / embed form / metadata: https://docs.buttondown.com/building-your-subscriber-base
