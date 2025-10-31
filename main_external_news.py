import os
from dotenv import load_dotenv
from collect_slack_messages import SlackMessageCollector
from generate_external_news import ExternalNewsGenerator
from post_slack import SlackPoster


def main() -> int:
    load_dotenv()
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    external_news_channel = os.environ.get("EXTERNAL_NEWS_CHANNEL")

    if not slack_token:
        print("❌ エラー: SLACK_BOT_TOKEN が設定されていません")
        return 1
    if not openai_key:
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return 1
    if not external_news_channel:
        print("❌ エラー: EXTERNAL_NEWS_CHANNEL が設定されていません。社外向けニュースの下書き投稿先チャンネルを環境変数で指定してください")
        return 1

    print("📥 過去1日分のSlackメッセージを取得します...")
    collector = SlackMessageCollector(slack_token)
    result = collector.collect_messages(days=1, auto_join=True)
    messages = result.get("messages", [])
    if not messages:
        print("⚠️ メッセージが取得できませんでした")
        return 1

    print("🧠 社外向けニュース（SNS投稿用）を生成します...")
    generator = ExternalNewsGenerator(openai_key)
    external_news = generator.generate_news_text(days=1, messages=messages)
    if not external_news:
        print("❌ 社外向けニュースの生成に失敗しました")
        return 1

    print("📤 Slackに下書きとして投稿します...")
    poster = SlackPoster(token=slack_token, default_channel=external_news_channel)
    
    # 社外向けニュース用のフォーマット（複数の投稿案）
    draft_message = f"🌟 *社外向けニュース下書き（最大5件）*\n\n{external_news}\n\n_※このメッセージはSNS投稿用の下書きです。複数の投稿案から選択し、内容を確認の上、適宜編集してご利用ください。_"
    
    poster.post(text=draft_message, channel=external_news_channel, thread=False)
    return 0


if __name__ == "__main__":
    exit(main())
