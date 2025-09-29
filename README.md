## newsai

newsai (News×AI) is a tool that automatically generates "This Week's Highlights" from your organization's Slack messages and posts it to Slack.
Scheduled runs use GitHub Actions. Fork this repository and configure the following Repository secrets to use it.

- OPENAI_API_KEY
- SLACK_BOT_TOKEN
- SLACK_CHANNEL

See the blog for more details.

### Main components
- **collect_slack_messages.py**: Collect recent messages from Slack and save them as JSON
- **generate_weekly_news.py**: Analyze the collected messages and generate the weekly news copy
- **post_slack.py**: Post the generated copy to Slack
- **main.py**: Run collect → generate → post end to end

## Requirements
- **Python**: 3.13 or later
- **uv**: Used for Python package and environment management
- **Slack bot token**: `SLACK_BOT_TOKEN`
- **OpenAI API key**: `OPENAI_API_KEY`

### Slack permissions
- `channels:read`, `channels:history`
- `chat:write`
- `channels.join` (if you want to auto-join public channels)

## Setup

### Install uv (macOS)
```bash
brew install uv
```
or
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Set up dependencies
```bash
uv python install 3.13
uv sync
```

### Environment variables (.env recommended)
Create `.env` at the project root:
```bash
cp .env.example .env
```
Set each environment variable appropriately.

## Scripts and how to run

### collect_slack_messages.py (Collect Slack messages)
- **Overview**: Collect messages from public channels in the workspace for a specified period and save as `slack_messages_YYYYMMDD_HHMMSS.json`
- **Key arguments**
  - `--days`: Number of days to collect (default: 7)
  - `--output`: Output file name (auto-named if omitted)
  - `--token`: Slack bot token (uses `SLACK_BOT_TOKEN` if omitted)
  - `--no-auto-join`: Disable auto-joining public channels
  - `--channel`: Target only channels whose names contain the specified string
- **Examples**
```bash
uv run python collect_slack_messages.py --days 7
uv run python collect_slack_messages.py --days 30 --channel general
uv run python collect_slack_messages.py --output messages.json
```

### generate_weekly_news.py (Generate weekly news)
- **Overview**: Read the saved JSON and, using the OpenAI API, generate weekly news copy including "Highlights" and "Extras"
- **Key arguments**
  - `--messages-file`: Path to the collected JSON (if omitted, automatically detect the latest `slack_messages_*.json`)
  - `--days`: Number of days to analyze (default: 7)
  - `--openai-key`: OpenAI API key (uses `OPENAI_API_KEY` if omitted)
- **Examples**
```bash
uv run python generate_weekly_news.py
uv run python generate_weekly_news.py --days 7 --messages-file slack_messages_20250929_145307.json
```
The output is printed as text to stdout.

### post_slack.py (Post to Slack)
- **Overview**: Post arbitrary text to Slack. You can pass the body via `--text` or via standard input
- **Key arguments**
  - `--channel`: Destination channel name or ID (defaults to `SLACK_CHANNEL`)
  - `--token`: Slack bot token (defaults to `SLACK_BOT_TOKEN`)
  - `--text`: Message body (if omitted, read from standard input)
- **Example**
```bash
uv run python post_slack.py --channel general --text "Body"
```

### main.py (Run end to end)
- **Overview**: Run collection → summary generation → Slack post end to end
- **Required environment variables**: `SLACK_BOT_TOKEN`, `OPENAI_API_KEY`, `SLACK_CHANNEL`
- **Example**
```bash
uv run python main.py
```
