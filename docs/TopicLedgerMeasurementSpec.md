# Topic Ledger & Measurement Spec

This document defines the minimum viable evidence system for Frank's current asset-compounding loop.

The goal is not "perfect analytics".

The goal is:

- make topic performance observable
- connect content outputs to downstream behavior
- avoid confusing activity with proof
- create a shared format that future project work can update consistently

## Why This Exists

The current strategy depends on evidence.

That means each serious topic cluster must be tracked across the whole path:

1. content published
2. asset CTA shown
3. capture triggered
4. subscriber created
5. replies / demand signals observed
6. paid interest or paid conversion observed later

Without this, it is too easy to:

- keep publishing without learning
- overestimate weak topics
- push paid assets before proof exists
- waste time on topics that do not move anyone deeper into the system

## Scope

This spec covers:

- topic-level tracking
- asset-level tracking
- first-pass funnel tracking for the checklist path
- evidence needed to justify deeper SOP pushes

This spec does not require:

- a full analytics warehouse
- a complex attribution model
- perfect automation from day one

## Primary Topic Cluster For Now

The first serious cluster is:

- `deployment / launch readiness / hardening`

Initial content in scope:

- `部署一个 GitHub 项目前，最应该先确认的 10 件事`
- `为什么很多开源 AI 项目“本地能跑”，一上服务器就出问题？`
- `开源 AI 项目上线前，哪些风险必须先处理，哪些可以后补？`
- `域名、HTTPS、反代、鉴权：第一次公开上线前最容易漏掉什么？`

Primary asset in scope:

- `开源 AI 项目部署前检查清单`

Primary paid asset in scope:

- `开源 AI 项目上线与基础加固 SOP`

## The Minimum Ledger

Maintain one ledger row per serious topic output.

At minimum, each row should track:

- `date_published`
- `topic_cluster`
- `content_title`
- `content_type`
- `canonical_url`
- `primary_cta`
- `asset_target`
- `page_views`
- `cta_clicks`
- `asset_unlocks_or_downloads`
- `confirmed_subscribers`
- `replies_or_feedback`
- `product_interest_signals`
- `paid_conversions`
- `notes`

## Recommended Ledger Columns

### Identity

- `topic_cluster`
  - example: `deployment`
- `content_title`
- `content_type`
  - allowed starter values:
    - `article`
    - `resource_page`
    - `success_page`
    - `short_pack`
    - `email`
    - `sales_page`
- `status`
  - `draft`
  - `published`
  - `archived`

### Funnel Mapping

- `primary_problem`
- `search_intent_level`
  - `high`
  - `medium`
  - `low`
- `primary_cta`
  - example:
    - `领取免费清单`
    - `订阅更新`
    - `了解 SOP`
- `asset_target`
  - example:
    - `deployment-checklist`
    - `launch-hardening-sop`
- `next_step`
  - what you expect the reader to do after this piece

### Performance

- `page_views`
- `cta_clicks`
- `asset_unlocks_or_downloads`
- `confirmed_subscribers`
- `welcome_email_opens`
  - optional when available
- `welcome_email_clicks`
  - optional when available
- `replies_or_feedback`
- `product_interest_signals`
  - examples:
    - asks for deeper version
    - asks for checklist expansion
    - asks for review / audit help
- `paid_conversions`

### Quality Notes

- `proof_summary`
- `what_worked`
- `what_failed`
- `next_iteration`

## Minimum Definitions

### Page Views

Definition:

- visits to the canonical article or resource page

### CTA Clicks

Definition:

- clicks on the main asset CTA inside that content

Current examples:

- click from article to checklist page
- click from homepage to checklist page

### Asset Unlocks Or Downloads

Definition:

- successful resource unlocks or downloads

For the current site model, this is not "email delivery".
It is:

- successful checklist access / unlock / download completion

### Confirmed Subscribers

Definition:

- subscribers who completed confirmation

This is more important than raw form submit count.

### Replies Or Feedback

Definition:

- actual responses, emails, DMs, or comments that show someone engaged with the topic deeply enough to respond

### Product Interest Signals

Definition:

- behavior that suggests demand for a deeper paid asset

Examples:

- "Do you have a more complete checklist?"
- "Can you share the SOP?"
- "Can you help me review this deployment?"
- repeated requests for the same missing step

### Paid Conversions

Definition:

- actual paid purchases tied to the paid asset path

## What Counts As Proof To Move Forward

Do not use one vanity spike as proof.

For a topic cluster to justify deeper SOP pushes, look for repeated signals such as:

- multiple articles produce checklist unlocks
- checklist unlocks turn into confirmed subscribers
- confirmed subscribers generate replies or deeper questions
- the same missing step is asked about more than once
- readers ask for a fuller or more executable version

## What Does Not Count As Proof

- raw impressions without action
- compliments without follow-up behavior
- traffic with no CTA click
- checklist unlocks with no confirmation and no replies
- personal excitement about a topic

## First-Pass Funnel To Measure Now

For the current checklist loop, track this path:

1. content page view
2. click to checklist page
3. checklist form submit / unlock
4. confirmed subscription
5. welcome email sent
6. welcome email click when available
7. reply / deeper interest signal
8. later SOP interest

This is enough to make better decisions even before a full analytics stack exists.

## Collection Method

### Phase 1: Manual Or Semi-Manual Is Acceptable

Right now, do not block progress on perfect instrumentation.

Acceptable phase-1 sources:

- site analytics page views
- click counts from simple event tracking or link tracking
- Buttondown confirmed subscriber counts by tag
- inbox replies
- manual notes from real conversations

### Phase 2: Add Better Event Tracking Later

When the system is stable, improve:

- CTA click events
- form submit / unlock events
- confirmed subscriber attribution
- SOP interest events

## Recommended File Format

Start with one simple file in-repo:

- `docs/topic-ledger.csv`

Recommended starter columns:

```csv
date_published,topic_cluster,content_title,content_type,canonical_url,primary_cta,asset_target,page_views,cta_clicks,asset_unlocks_or_downloads,confirmed_subscribers,replies_or_feedback,product_interest_signals,paid_conversions,notes
```

If a CSV feels too rigid later, add:

- `docs/topic-ledger.md`

for commentary and interpretation.

## Initial Rows To Add First

When the ledger is first created, seed at least:

1. the homepage checklist CTA
2. the checklist landing page
3. `部署一个 GitHub 项目前，最应该先确认的 10 件事`
4. the checklist success / confirmation page

Then add Batch 1 article #2 when published.

Current status:

- initial ledger file has now been seeded at `docs/topic-ledger.csv`
- next work should update it with real numbers instead of creating a second tracking format

## Review Cadence

### Weekly

Check:

- which topic got views
- which topic got CTA clicks
- whether checklist unlocks happened
- whether confirmed subscribers moved

### Monthly

Check:

- which topics created real downstream value
- whether the cluster is producing repeated product-interest signals
- whether the paid SOP path should be pushed harder

## Decision Rules

### Keep investing in a topic when:

- it produces meaningful CTA clicks
- it produces checklist unlocks
- it produces confirmed subscribers
- it produces replies or deeper questions

### Rewrite or demote a topic when:

- it gets views but no CTA clicks
- it gets clicks but no unlocks
- it gets unlocks but no confirmations or no follow-up behavior

### Consider pushing the paid SOP harder when:

- more than one article in the cluster produces downstream proof
- the same operational pain repeats in replies
- readers ask for a fuller execution version

## Current Priority

Do not overbuild the ledger before using it.

The correct next move after this spec is:

1. keep `docs/topic-ledger.csv` as the single source of truth for the current funnel
2. update the seeded rows with real numbers
3. publish Batch 1 content with explicit CTA mapping
4. review weekly
