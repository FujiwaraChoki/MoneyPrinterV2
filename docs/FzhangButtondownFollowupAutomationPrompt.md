# 给另一个 AI 的 Buttondown 后续更新自动化提示词

你现在要审查并改进 `fzhang.dev` 当前“资源领取后，后续优先发相关文章和主题更新”的实现方式。

目标不是堆更多手工邮件，而是确认：

1. 这件事在 Buttondown 里应该怎么自动化
2. 如何保证不会给 Frank 增加过多运营负担
3. 如何让“后续优先发送”真正可执行

## 当前业务目标

用户通过个人网站提交邮箱领取：

- `开源 AI 项目部署前检查清单`

之后希望实现：

- 资源先站内即时解锁
- 再发少量订阅后续邮件
- 后续如果这条主题下扩展出新文章、资源、SOP，也能优先发给这批人

但前提是：

- 不能让 Frank 进入高频手工运营
- 不能每发一篇内容就手工给这批人发一封
- 不能把整个系统做成很重的 CRM

## 你必须先核对的 Buttondown 官方能力与计划边界

请检查并利用这些能力：

- Automations 支持：
  - welcome sequences
  - based on triggers / filters / actions
- Tags 支持：
  - 通过 API 或订阅表单打标签
- RSS-to-email 支持：
  - 每篇更新自动发
  - 每周汇总发
  - 每月汇总发
- Create subscriber API 默认 double opt-in

同时请核对一个现实前提：

- 当前 Frank 使用的 Buttondown 方案不一定已经包含 `Automations` 或 `RSS-to-email`
- 请不要把付费功能当作已可用能力直接假设

## 当前判断方向

请围绕下面这个判断做验证或修正：

### 最可能的低负担实现

资源领取用户进入一条单独的订阅路径：

1. 提交资源表单
2. double opt-in 确认
3. 资源站内即时解锁
4. 确认后收到 Welcome 邮件
5. 后续按 `topic-deployment` 做低频分群发送
6. 如果未来升级方案，再补 short welcome sequence 或 RSS digest

这比：

- 每次手工群发
- 每有新文章就手动筛人发
- 靠个人邮箱规则自动回复

更合理。

## 你的任务

### 任务 1：判断“后续优先发给我”最适合落在哪条链路

请在下面几种方式里做选择并说明理由：

- Buttondown welcome email + automations
- Buttondown automations + tags
- Buttondown RSS-to-email weekly digest
- 手工 newsletter segmentation
- 混合方案

### 任务 2：给出最推荐的低负担方案

必须明确：

- 哪些内容应该自动发
- 哪些内容不该自动发
- 周更、月更、逐篇发，哪个更适合当前阶段

我更偏向的目标是：

- 当前先跑稳 `confirmation + welcome + 低频分群发送`
- 以后若升级能力，再加 2 到 3 封自动后续邮件
- 之后再考虑主题相关的 digest 更新
- 不做高频手工运营

### 任务 3：设计标签与过滤逻辑

请基于当前资源页，给出建议标签，例如：

- `lead-magnet`
- `resource-checklist`
- `topic-deployment`
- `source-fzhang-dev`

并回答：

- 后续新文章应该如何进入这条线
- 是靠 tags 发，还是靠独立 automation，还是靠 RSS cadence

### 任务 4：回答“会不会增加太多负担”

请明确判断：

- 当前最省力的实现是什么
- 哪种实现会明显增加 Frank 的长期负担
- 应该避免哪些“看起来先进、实际很重”的自动化设计

### 任务 5：给出建议的最终架构

输出一个简洁的自动化架构图或步骤：

例如：

`资源页 -> 站内即时解锁 -> API -> Buttondown subscriber + tags -> confirmation -> welcome email -> 按 topic-deployment 低频分群发送`

## 输出要求

请按下面结构输出：

1. 最推荐方案
2. 为什么它负担最低
3. 标签与分群设计
4. 后续更新该如何自动发
5. 不推荐的重方案
6. 最终落地步骤

## 官方文档入口

- Automations:
  - https://docs.buttondown.com/automations-introduction
- Welcome sequence:
  - https://docs.buttondown.com/welcome-sequence
- RSS-to-email:
  - https://docs.buttondown.com/rss-to-email
- Create subscriber API:
  - https://docs.buttondown.com/api-subscribers-create
- Sending emails / unsubscribe:
  - https://docs.buttondown.com/sending-emails#avoiding-the-promotions-tab

## 额外要求

- 不要默认推荐复杂 CRM
- 不要把“后续优先发给我”设计成必须人工一封一封维护
- 不要把“资源站内即时交付”误写成“必须邮件交付”
- 优先给出“当前阶段够用、未来可扩展”的方案
