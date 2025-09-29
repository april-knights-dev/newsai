## ai-news

社内の Slack メッセージから「今週の注目ニュース」を自動生成し、Slack に投稿するツールです。
定期実行はGitHub Actionsを利用しています。このリポジトリをフォークし、以下の Repository secrets を適切に設定することで利用可能です。

- OPENAI_API_KEY
- SLACK_BOT_TOKEN
- SLACK_CHANNEL

詳細はブログに記載しております。

### 主な構成
- **collect_slack_messages.py**: Slack から直近のメッセージを収集して JSON に保存
- **generate_weekly_news.py**: 収集したメッセージを分析し、週次ニュース文面を生成
- **post_slack.py**: 生成した文面を Slack に投稿
- **main.py**: 収集→生成→投稿までを一括実行

## 要件
- **Python**: 3.13 以上
- **uv**: Python のパッケージ/環境管理に使用
- **Slack ボットトークン**: `SLACK_BOT_TOKEN`
- **OpenAI API キー**: `OPENAI_API_KEY`

### Slack 権限
- **読み取り系**: `channels:read`, `groups:read`, `channels:history`, `groups:history`
- **投稿系**: `chat:write`
- **参加系**: `conversations.join`（パブリックチャンネルに自動参加する場合）

## セットアップ

### uv のインストール（macOS）
```bash
brew install uv
```
または
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 依存関係のセットアップ
```bash
uv python install 3.13
uv sync
```

### 環境変数の設定（.env 推奨）
プロジェクト直下に `.env` を作成:
```bash
cp .env.example .env
```
各環境変数を適切に設定してください。

## 各スクリプトの説明と実行方法

### collect_slack_messages.py（Slack メッセージ収集）
- **概要**: ワークスペース内のパブリックチャンネルから、指定期間のメッセージを収集し、`slack_messages_YYYYMMDD_HHMMSS.json` として保存
- **主な引数**
  - `--days`: 収集する日数（既定: 7）
  - `--output`: 出力ファイル名（未指定なら自動命名）
  - `--token`: Slack ボットトークン（未指定なら `SLACK_BOT_TOKEN` を使用）
  - `--no-auto-join`: パブリックチャンネルへの自動参加を無効化
  - `--channel`: 名前に指定文字列を含むチャンネルのみ対象
- **実行例**
```bash
uv run python collect_slack_messages.py --days 7
uv run python collect_slack_messages.py --days 30 --channel general
uv run python collect_slack_messages.py --output messages.json
```

### generate_weekly_news.py（週次ニュース生成）
- **概要**: 保存済み JSON を読み込み、OpenAI API で「注目ニュース」「番外編」を含む週次ニュース文面を生成
- **主な引数**
  - `--messages-file`: 収集済み JSON パス（未指定時は `slack_messages_*.json` の最新を自動検出）
  - `--days`: 分析対象の日数（既定: 7）
  - `--openai-key`: OpenAI API キー（未指定なら `OPENAI_API_KEY` を使用）
- **実行例**
```bash
uv run python generate_weekly_news.py
uv run python generate_weekly_news.py --days 7 --messages-file slack_messages_20250929_145307.json
```
出力は標準出力にテキストとして表示されます。

### post_slack.py（Slack 投稿専用）
- **概要**: 任意のテキストを Slack に投稿。本文は `--text` または標準入力から渡すことが可能
- **主な引数**
  - `--channel`: 投稿先チャンネル名または ID（未指定時は `SLACK_CHANNEL`）
  - `--token`: Slack ボットトークン（未指定時は `SLACK_BOT_TOKEN`）
  - `--text`: 投稿本文（未指定時は標準入力を使用）
- **実行例**
```bash
uv run python post_slack.py --channel general --text "本文"
```

### main.py（一括実行）
- **概要**: 収集→要約生成→Slack 投稿までを一括で実行
- **必要な環境変数**: `SLACK_BOT_TOKEN`, `OPENAI_API_KEY`, `SLACK_CHANNEL`
- **実行例**
```bash
uv run python main.py
```
