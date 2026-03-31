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
- 当前成功页已经显示“先确认邮箱，再送达清单”的 double opt-in 式引导

这意味着：

- 你已经有资源领取入口
- 站点结构已经基本切换到成熟订阅路径
- 但是否真的完成邮件送达、标签写入和自动序列，仍需要真实邮箱验收

## 当前验收结论

根据线上页面检查，下面这些已经基本成立：

- 资源页已明确区分公开文章与执行版资源
- 表单已切到自建接口而不是纯表单托管
- 订阅页已完成邮件 + RSS 双路径
- 成功页已具备确认订阅与后续 digest 预期管理

还不能只靠浏览器确认的部分：

- 确认邮件是否真实发出
- 资源交付邮件是否真实发出
- 是否写入正确标签
- 自动序列是否按时触发
- 退订入口是否真实可用

所以当前状态更准确的说法是：

> 前端与信息架构已经明显升级，但邮件闭环仍需要真实邮箱验收。

## 推荐方案

不要把“自动回信”理解成邮箱规则自动回复。

更成熟的做法是：

`资源领取表单 -> 立即交付邮件 -> 进入订阅系统 -> 标签化 -> 自动序列 -> 周更或月更更新`

我建议你采用两层结构：

### 第一层：立即交付

负责把免费资源立刻发出去。

可选实现：

- 继续使用 `Formspree` 自动回复
- 或改成你自己的 serverless endpoint 发送事务型邮件

### 第二层：长期订阅

负责后续更新、标签、分组和自动序列。

我建议优先用 `Buttondown`，原因是它更贴近你的博客形态：

- 支持标签与自动化
- 支持 RSS-to-email
- 适合内容站而不是纯销售漏斗站
- 支持自定义嵌入表单和 metadata

## 为什么不建议只靠 Formspree

`Formspree` 适合做表单接收和简单自动回复，但不适合作为长期订阅系统。

原因：

- 它不是完整的 newsletter / subscriber system
- 后续更新、标签、自动序列、分群都不够自然
- 你最终还是会需要一个专门的订阅平台

## 为什么更适合 Buttondown

根据 Buttondown 官方文档，它支持：

- 通过 API 创建 subscriber
- 通过标签做分群
- 基于 subscriber confirmed 等触发器做 automations
- 基于 RSS 自动发送站点更新

这和你当前的站点结构是匹配的：

- 你本来就有 RSS
- 你的网站本来就是内容站
- 你后续需要的是“围绕主题的持续更新”，不是一次性表单通知

## 两种落地路径

### 路径 A：最快可用

保留当前 `Formspree` 表单。

实现方式：

1. 开启 `Formspree` 自动回复，立即发送清单
2. 如果你的 Formspree 计划支持 Webhooks，把提交同步到 `Buttondown`
3. 在 Buttondown 里创建标签、自动序列和 RSS-to-email

优点：

- 改动最小
- 站点前端几乎不用大改

缺点：

- 对 Formspree 计划有依赖
- 数据链路拆成两段

### 路径 B：更干净的长期方案

把表单提交改到你自己的 serverless endpoint。

推荐部署位置：

- Cloudflare Workers
- Vercel Functions

服务分工：

- Turnstile 继续做人机校验
- 你的 endpoint 接收表单
- endpoint 发送一封事务型资源交付邮件
- endpoint 再把订阅者写入 Buttondown

优点：

- 你完全掌控数据和流程
- 不依赖 Formspree 的 webhook 计划
- 后续接更多资源、更多标签、更多序列更稳

缺点：

- 需要一次真正的工程实现

## 我建议你选哪条

如果你想最快上线：

- 先走 `路径 A`

如果你准备认真把站点做成长期内容资产系统：

- 直接走 `路径 B`

我更推荐 `路径 B`，因为它更接近成熟订阅方案，也更符合你后续会继续扩资源、扩标签、扩自动化的方向。

## 推荐的数据模型

无论选哪条路径，至少统一这些字段：

- `email`
- `name`
- `resource`
- `request_type`
- `source_page`
- `interest_topic`
- `submitted_at`

推荐标签：

- `lead-magnet`
- `resource-checklist`
- `topic-deployment`
- `source-fzhang-dev`

如果后续还会有别的资源，再继续扩：

- `resource-self-hosting-risk-sheet`
- `resource-ai-tool-stack`

## 推荐的订阅逻辑

### 最成熟的处理方式

1. 用户提交表单
2. 立即收到“资源交付邮件”
3. 同时进入“邮件订阅确认流程”
4. 只有确认后，才进入后续更新流

这比“提交后直接把人扔进长期群发”更成熟，原因是：

- 更合规
- 更少垃圾地址
- 打开率更高
- 长期列表质量更好

## 推荐的自动邮件结构

### Email 1：资源交付

触发：

- 表单提交成功后立即发送

目的：

- 把资源交付出去
- 明确“解释版 vs 执行版”的差异
- 给一个低摩擦下一步

核心内容：

- 下载链接
- 一句使用建议
- 一篇相关文章入口

### Email 2：使用提醒

触发：

- 订阅确认后 2 天

目的：

- 提高资源实际打开率
- 告诉读者什么时候应该打开这份清单

### Email 3：主题深化

触发：

- 订阅确认后 5 到 7 天

目的：

- 引到更完整的 SOP 方向
- 观察真实需求反馈

### Email 4 之后：站点更新

触发：

- 周更 digest 或按 RSS 生成的更新邮件

建议：

- 不要每篇文章都即时轰炸
- 优先周更
- 后续如果能按 tag 发，只给部署相关订阅者发对应内容更好

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
