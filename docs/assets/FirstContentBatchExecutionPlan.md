# 第一批可转化长尾内容执行计划

这份计划的目标不是继续罗列想法。

目标是：

- 从现有 10 个 long-tail topics 中选出第一批真正要发的内容
- 明确每篇内容服务于哪一段漏斗
- 让每篇内容都为免费清单和后续付费 SOP 铺路

## 当前漏斗基线

当前默认路径：

1. 长尾文章
2. 免费清单
3. 邮件订阅 / 后续跟进
4. 付费 SOP / 模板

所以第一批内容必须满足两个条件：

- 有明确搜索意图
- 能自然引到 checklist 或 SOP

## Batch 1 选题

### 1. 部署一个 GitHub 项目前，最应该先确认的 10 件事

当前状态：

- 已有首发文章草稿

角色：

- 漏斗入口主文

主要任务：

- 承接最强搜索意图
- 把“解释版 -> 执行版清单”关系讲清楚

主要 CTA：

- `领取开源 AI 项目部署前检查清单`

下一步承接：

- checklist 下载

### 2. 为什么很多开源 AI 项目“本地能跑”，一上服务器就出问题？

当前状态：

- 已有文章草稿

角色：

- 问题放大型文章

主要任务：

- 把“本地可跑 != 可上线”讲透
- 引出部署顺序、环境差异、暴露面和回滚问题

主要 CTA：

- `先用部署前检查清单过一遍`

下一步承接：

- checklist 下载
- SOP 预告

### 3. 开源 AI 项目上线前，哪些风险必须先处理，哪些可以后补？

角色：

- checklist 到 SOP 的桥梁文

主要任务：

- 让读者意识到“不是所有问题都要一次解决”
- 引出“基础加固 SOP” 的必要性

主要 CTA：

- `先领清单`
- `如果你更关心上线与基础加固，留意后续 SOP`

下一步承接：

- checklist
- paid SOP waitlist / interest signal later

### 4. 域名、HTTPS、反代、鉴权：第一次公开上线前最容易漏掉什么？

角色：

- 高执行细节文

主要任务：

- 为 SOP 建立“更细、更实操”的预期
- 开始把主题往 deployment + hardening cluster 收拢

主要 CTA：

- `下载清单`

下一步承接：

- checklist
- future SOP

## 发布顺序

推荐顺序：

1. `部署一个 GitHub 项目前，最应该先确认的 10 件事`
2. `为什么很多开源 AI 项目“本地能跑”，一上服务器就出问题？`
3. `开源 AI 项目上线前，哪些风险必须先处理，哪些可以后补？`
4. `域名、HTTPS、反代、鉴权：第一次公开上线前最容易漏掉什么？`

原因：

- 先吃最明确的搜索意图
- 再放大问题
- 再桥接到 SOP
- 再往更细执行主题推进

## 每篇内容的最小完成标准

每篇文章发布前都至少满足：

- 有明确主关键词或问题句
- 首屏能在 5 秒内说明这篇文章解决什么问题
- 文中至少 1 次自然引到 checklist
- 文末至少 1 个明确 CTA
- 能进入 `deployment` / `launch readiness` / `hardening` 主题簇

## 每篇内容需要带出的证据

不要只看阅读量。

每篇文章至少要观察：

- 页面访问
- checklist 点击
- checklist 提交
- 订阅确认
- 邮件回复
- 是否有人问更深版本

## 不该优先写的内容

当前阶段不优先：

- 纯热点评论
- 泛 AI 观点文
- 与部署、自托管、上线准备弱相关的内容
- 很难自然连接 checklist 或 SOP 的主题

## Batch 1 之后的判断门槛

只有当下面这些信号开始重复出现，才说明可以继续加速 paid SOP 路径：

- 多篇文章都能稳定带来 checklist 下载
- 下载后有人回复具体上线问题
- 有人明确询问更完整版本
- 同类问题反复出现

如果这些信号不出现，就先继续优化主题与漏斗，不急着扩 product lane。

## Distribution Validation

Current rule:

- do not assume low subscriber count automatically means weak content
- first build a minimum distribution sample before making that judgment

Execution reference:

- `docs/DistributionValidationPlan.md`
