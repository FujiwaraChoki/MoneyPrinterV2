# YouTube Shorts Monetization Analytics — Design Spec

## Goal

YouTube Shorts による収益化の効果検証を行うための分析基盤を構築する。
複数ジャンルで動画を生成・アップロードし、パフォーマンスとコストを比較する。

## Scope

- Phase 1: 環境セットアップ（Fork、config、Google API OAuth）
- Phase 2: 動画生成 + コスト記録（3〜5ジャンル × 各5本）
- Phase 3: メトリクス収集 + 分析レポート

小規模テスト（計15〜25本）から開始し、結果を見ながら拡大。

## Decisions

- **リポジトリ**: MoneyPrinterV2 を Fork して開発。上流の更新も取り込める
- **データ保存**: 初期は JSON（既存パターンに合わせる）、将来 SQLite に移行
- **収益データ**: 初期は YouTube Data API（views, likes, comments）のみ。YPP 到達後に Analytics API で収益追加
- **コスト追跡**: Gemini API 呼び出し回数のみ（Ollama はローカル、ゼロコスト）
- **レポート**: CLI サマリー（PrettyTable）+ CSV エクスポート

## Architecture

### New Files

| File | Responsibility |
|------|---------------|
| `src/analytics.py` | YouTube Data API v3 連携。動画メトリクス取得（views, likes, comments） |
| `src/cost_tracker.py` | 動画生成時の API コスト記録・集計 |
| `src/report.py` | CLI サマリー表示（PrettyTable）+ CSV エクスポート |

### Modified Files

| File | Change |
|------|--------|
| `src/classes/YouTube.py` | `generate_image()` 呼び出し時に cost_tracker へ記録追加。`upload_video()` 完了時に video_id を analytics に記録 |
| `src/main.py` | メニューに「6. Analytics」オプション追加 |
| `src/config.py` | Google API OAuth 関連ゲッター追加 |
| `config.example.json` | `google_api_credentials_path` フィールド追加 |
| `requirements.txt` | `google-api-python-client`, `google-auth-oauthlib` 追加 |

### Data Structure

動画ごとのデータ（`.mp/analytics.json`）:

```json
{
  "videos": [
    {
      "video_id": "abc123",
      "title": "...",
      "niche": "cooking",
      "upload_date": "2026-03-26 10:00:00",
      "cost": {
        "gemini_api_calls": 5,
        "gemini_model": "gemini-3.1-flash-image-preview"
      },
      "metrics_history": [
        {
          "views": 500,
          "likes": 20,
          "comments": 2,
          "fetched_at": "2026-03-27 10:00:00"
        },
        {
          "views": 1200,
          "likes": 45,
          "comments": 3,
          "fetched_at": "2026-03-28 10:00:00"
        }
      ]
    }
  ]
}
```

### video_id Acquisition

`video_id` は `upload_video()` 完了時に YouTube Studio の URL から抽出する（既存コードで `video_id` を取得済み: YouTube.py L830）。この `video_id` を `analytics.json` に記録し、メトリクス取得のキーとして使用する。

## Metrics Collection

### YouTube Data API v3

Endpoint: `videos.list(part="statistics", id=video_id)`

| Metric | Field | YPP Required |
|--------|-------|-------------|
| viewCount | statistics.viewCount | No |
| likeCount | statistics.likeCount | No |
| commentCount | statistics.commentCount | No |
| estimatedRevenue | (Analytics API) | Yes — deferred |

### Collection Triggers

- **Manual**: CLI メニュー「Fetch Metrics」→ 全動画の最新メトリクスを一括取得
- **Auto (CRON)**: 既存 schedule ライブラリで1日1回自動取得（オプション、後から有効化）

### Google API Authentication

- OAuth 2.0 client credentials（Google Cloud Console で作成）
- Token は `.mp/google_token.json` にキャッシュ
- Scopes: `youtube.readonly`

## Report Output

### CLI Summary (PrettyTable)

ジャンル別集計:

```
┌─────────┬───────┬───────┬───────┬───────┬────────────┐
│ Niche   │ Videos│ Views │ Likes │ Cost  │ Views/Cost │
├─────────┼───────┼───────┼───────┼───────┼────────────┤
│ cooking │   5   │ 3,200 │  120  │ $0.25 │   12,800   │
│ fitness │   5   │ 1,800 │   65  │ $0.25 │    7,200   │
│ tech    │   3   │   900 │   30  │ $0.15 │    6,000   │
└─────────┴───────┴───────┴───────┴───────┴────────────┘
```

### CSV Export

`exports/analytics_YYYY-MM-DD.csv` に動画単位の全データを出力:

```csv
video_id,title,niche,upload_date,gemini_api_calls,views,likes,comments,fetched_at
abc123,Recipe Tips,cooking,2026-03-26,5,1200,45,3,2026-03-28
```

## Cost Tracking

### What to Track

- Gemini API 呼び出し回数（`generate_image()` 1回 = 1 call）
- 使用モデル名（pricing 計算用）

### What NOT to Track (Initial Phase)

- Ollama 推論コスト（ローカル、ゼロコスト）
- 電力・GPU 使用量
- 動画生成時間（将来追加可能）

### Cost Calculation

Gemini Flash Image の pricing に基づいて概算。config.json にレートを設定:

```json
{
  "gemini_cost_per_call": 0.005
}
```

## Future Extensions (Not in Scope)

- SQLite 移行（データ量増加時）
- YouTube Analytics API 連携（YPP 到達後）
- 時間コスト計測（生成時間の各ステップ計測）
- A/B テストフレームワーク（同一ジャンル内でパラメータ比較）
- Grafana ダッシュボード
