# shop.fzhang.dev 支付架构决策

这份文档用于冻结当前阶段关于 `shop.fzhang.dev` 支付与订单系统的判断。

它的目标不是比较所有支付工具。

它的目标是：

- 避免把 `Payoneer receiving account` 误当成独立站 checkout 方案
- 固定一套更适合数字产品 / SOP / 模板 / 订阅型资产的架构思路
- 让后续在 `shop.fzhang.dev` 或相关仓库里开发时有统一参考

## 当前结论

### 不推荐

不建议把：

- `Payoneer receiving account`

当作 `shop.fzhang.dev` 的主 checkout / 主支付网关。

### 推荐

推荐采用：

- `Stripe / Lemon Squeezy / Paddle` 这类支付 / 订阅 / 账单平台
- 自己的数据库只负责：
  - 用户映射
  - 权限状态
  - 订单镜像
  - 订阅镜像
  - 内容解锁状态
  - 操作后台

一句话：

> 支付平台负责收钱、订阅、账单、退款；你自己的系统负责用户、权限和内容交付。

## 为什么不建议用 Payoneer receiving account 直接做独立站支付

根据 Payoneer 官方帮助中心：

- `Request a Payment` 适合向 business clients 发收款请求
- 但官方明确写了：
  - 它 `does not support payments from consumers paying in your online store`
  - 它 `is not meant to be used as a payment gateway (checkout) for your ecommerce store`
- `Receiving accounts` 更像本地 / 国际银行收款信息，用于：
  - 客户打款
  - marketplace / 平台打款
  - 类似银行转账收款

这意味着：

- 它更像 payout / bank transfer rail
- 不像一个成熟的独立站 checkout stack
- 它不适合作为数字产品、订阅、退款、账单、订单自助管理的主入口

## 为什么更适合用 Stripe / Lemon Squeezy / Paddle 这类架构

这些平台的共同点是：

- 支持 checkout
- 支持 one-time orders 或 subscriptions
- 支持 refunds / billing / invoices
- 支持 webhooks
- 能让你把自己的数据库当成“业务镜像”，而不是支付真相源

这和你刚提到的理想架构是一致的：

- 支付平台负责：
  - payment
  - subscription lifecycle
  - invoicing
  - refunds
  - customer billing actions
- 你自己的数据库负责：
  - user mapping
  - entitlement state
  - order mirror
  - unlock state
  - admin operations

## 当前最推荐的方向

### 默认推荐

如果 `shop.fzhang.dev` 近期卖的是：

- SOP
- 模板
- 数字资源包
- 轻量订阅

那么当前更推荐优先走：

- `Merchant of Record` 路线

也就是：

- `Paddle` 或 `Lemon Squeezy`

而不是先自己承担更多支付合规和订单复杂度。

### 为什么

对当前阶段的 Frank 来说，最重要的不是“支付层最大控制权”，而是：

- 低维护负担
- 能尽快卖出第一个数字资产
- 不把有限执行预算过早耗在账单、退款、税务、订阅管理细节上

## Paddle / Lemon / Stripe 的当前判断

### `Paddle`

更适合的情况：

- 你预计会更快进入 subscription / billing-heavy 路线
- 你希望 customer portal、取消订阅、账单管理尽量少自己搭
- 你希望 webhook 驱动数据库镜像和权限同步

根据 Paddle 官方文档：

- customer portal 默认可用
- Paddle 邮件会带 customer portal 链接
- 适合把核心 billing workflow 交给 Paddle
- webhook provisioning 模型和“数据库镜像 + 权限同步”天然匹配

### `Lemon Squeezy`

更适合的情况：

- 你更偏 creator-style 的数字产品
- 更重 one-time digital products，同时保留订阅可能
- 你想要 hosted portal / my orders / downloadable files 这类现成功能

根据 Lemon Squeezy 官方文档：

- 提供 customer portal
- 提供 my orders
- 作为 merchant of record 处理支付相关责任

### `Stripe`

更适合的情况：

- 你未来明确需要更深的定制化 billing 流程
- 你愿意承担更高的系统设计与运营复杂度
- 你希望长期保留最大控制权

根据 Stripe 官方文档：

- 可管理 subscriptions
- 可管理 refunds
- 可自动生成 invoices
- 有 hosted customer portal

但当前阶段：

- Stripe 更像“能力最强的底层积木”
- 不一定是“最省执行预算”的第一选择

## 当前建议的最终判断

### 1. 支付架构原则

采用：

- `支付平台作为支付真相源`
- `自有数据库作为业务镜像和权限系统`

不要采用：

- `自建订单系统 + Payoneer 直接收款` 作为主路径

### 2. Payoneer 的角色

当前更适合把 Payoneer receiving account 视为：

- payout rail
- B2B 银行转账收款方式
- 特定客户 / 公司付款的补充渠道

不应视为：

- 主 checkout
- 主 ecommerce payment gateway
- 主 subscription stack

### 3. 近期 vendor 倾向

如果你接下来很快要上线 `shop.fzhang.dev` 来卖数字资产，我的当前建议是：

- 优先评估 `Paddle`
- 次选 `Lemon Squeezy`
- `Stripe` 作为未来需要更深度定制时再考虑的方案

原因不是“Paddle 永远更强”，而是：

- 当前更接近 subscription / portal / low-maintenance 目标
- 更符合你现在“先卖出第一个数字资产，再逐步复杂化”的阶段

## 推荐系统边界

### 支付平台负责

- checkout
- subscriptions
- invoices
- refunds
- billing emails
- customer self-service billing actions

### 你的数据库负责

- internal user id 与 external customer id 映射
- product ownership / entitlement
- order mirror
- subscription status mirror
- unlock state
- admin queries / support lookup

### 你的应用逻辑负责

- webhook signature verification
- entitlement updates
- unlock / revoke content
- support tooling
- analytics / topic ledger / monetization evidence

## 当前最小实现建议

如果现在就要开始落地：

1. 先选定一个支付平台，不要继续停留在 Payoneer 方案上
2. 先把 one-time digital product + webhook mirror 跑通
3. 再补 subscriptions / portal / cancellation flows
4. 最后再考虑更复杂的自定义后台或 billing abstraction

## InsForge Re-Evaluation Condition

Current judgment:

- do not introduce `InsForge` now

Why:

- the current bottleneck is not backend infrastructure
- the near-term priority is still:
  - prove the asset loop
  - validate paid digital assets
  - choose and integrate a payment platform
- adding a new agent-native backend now would likely increase coordination cost before it creates real leverage

Re-evaluate `InsForge` only when most of the following become true:

- `shop.fzhang.dev` needs a real internal backend beyond static pages and payment-hosted flows
- you already have a chosen payment platform and stable webhook model
- you need a persistent internal system for:
  - user accounts
  - entitlement state
  - order / subscription mirrors
  - admin operations
  - support lookup
- you expect repeated backend changes where an agent-friendly backend stack would save meaningful time
- the first paid asset is already selling or the shop backend has become an active execution bottleneck

Do not re-evaluate `InsForge` merely because:

- it looks promising
- it could maybe speed up future backend work
- it feels more modern than the current stack

One-sentence rule:

> Only reconsider `InsForge` after payment integration and the first paid asset path are real enough that backend coordination becomes the bottleneck.

## 这条决策对当前系统的影响

它意味着：

- `MoneyPrinterV2` 继续负责资产与漏斗
- `fzhang.dev` 继续负责 trust / traffic / capture
- `shop.fzhang.dev` 负责 checkout / monetization surface
- `Payoneer` 不承担独立站主支付网关角色

## 官方依据

### Payoneer

- Request a payment - Information for Receivers
- How to receive funds to your Payoneer account

核心依据：

- Payoneer 官方明确说明 request a payment 不是给 ecommerce store 做 checkout 用的
- receiving accounts 更偏银行收款 / marketplace 打款

### Stripe

- Customers
- Customer Portal
- Refunds
- Subscription invoices

### Lemon Squeezy

- Merchant of Record
- Customer Portal
- My Orders
- Refunds and Chargebacks

### Paddle

- Customer Portal
- Handle provisioning and fulfillment
- Subscription cancellation
- Customer portal sessions

## 当前一句话规则

> `shop.fzhang.dev` 的主支付方案应该是“支付平台 + 自有数据库镜像”，而不是 “Payoneer receiving account 直接做独立站 checkout”。`
