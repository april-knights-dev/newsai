import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

class ExternalNewsGenerator:
    """社外向けニュース生成（SNS投稿用）"""
    
    def __init__(self, openai_api_key: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
        
    def load_messages(self, filename: str) -> List[Dict]:
        """保存されたメッセージファイルを読み込む"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages = data.get('messages', [])
                print(f"📥 {len(messages)} 件のメッセージを読み込みました")
                return messages
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {filename}")
            return []
        except json.JSONDecodeError:
            print(f"❌ JSONファイルの読み込みエラー: {filename}")
            return []
    
    def filter_recent_messages(self, messages: List[Dict], days: int = 1) -> List[Dict]:
        """指定日数以内のメッセージをフィルタリング"""
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
        recent_messages = []
        
        for msg in messages:
            try:
                msg_ts = float(msg.get('ts', 0))
                if msg_ts >= cutoff_time:
                    recent_messages.append(msg)
            except (ValueError, TypeError):
                continue
        
        print(f"📅 過去{days}日間のメッセージ: {len(recent_messages)}件")
        return recent_messages
    
    def prepare_messages_for_analysis(self, messages: List[Dict]) -> str:
        """メッセージを分析用に整形"""
        formatted_messages = []
        
        # チャンネルごとにグループ化
        channels = {}
        for msg in messages:
            channel = msg.get('channel_name', 'unknown')
            if channel not in channels:
                channels[channel] = []
            
            # ボットメッセージや添付ファイルのみのメッセージはスキップ
            if msg.get('subtype') in ['bot_message', 'file_share']:
                continue
                
            text = msg.get('text', '').strip()
            if not text or len(text) < 10:  # 短すぎるメッセージはスキップ
                continue
                
            # URL削除
            text = re.sub(r'<https?://[^\s>]+>', '', text)
            text = re.sub(r'https?://[^\s]+', '', text)
            
            # メンション削除
            text = re.sub(r'<@[A-Z0-9]+>', '', text)
            
            # 絵文字削除（簡易版）
            text = re.sub(r':[a-z_]+:', '', text)
            
            # 改行削除
            text = re.sub(r'\n', '', text)
            
            channels[channel].append({
                'text': text[:500]  # 長すぎるメッセージは切り詰め
            })
        
        # チャンネルごとに整形
        for channel, msgs in channels.items():
            if msgs:
                formatted_messages.append(f"\n#チャンネル：【#{channel}】")
                for msg in msgs[-50:]:  # 各チャンネル最新50件まで
                    formatted_messages.append(f"- {msg['text']}")
        
        return "\n".join(formatted_messages)
    
    def generate_external_news(self, messages_text: str) -> str:
        """OpenAI APIを使用して社外向けニュースを生成"""
        print("🤖 OpenAI APIで社外向けニュース分析中...")
        
        try:
            prompt = """#指示
以下のSlackメッセージから、「社外向けSNS（Twitter/X）で共有するのに適切な話題」を最大5件選んでください。

選定基準：
- 企業の前向きな活動や成果を示すもの
- 社外に公開しても問題ない内容
- 一般の人が興味を持ちそうな話題
- ポジティブで建設的な内容
- 機密情報や社内限定の情報を含まないもの

生成内容：
各話題について以下を作成してください：
1. **日本語で**Twitter/X投稿用の文章を作成（280文字以内を目安）
2. ハッシュタグを2-3個含める
3. 絵文字を適度に使用して親しみやすさを演出
4. 企業アカウントとして適切なトーンで記述
5. 話題の元になったチャンネル名を明記

出力形式：
複数の投稿案を番号付きで日本語で出力してください。各投稿案の後に元チャンネル情報を記載し、空行で区切ってください。

例：
1. [投稿文1]
（元チャンネル: #channel-name）

2. [投稿文2]
（元チャンネル: #channel-name）

3. [投稿文3]
（元チャンネル: #channel-name）

※適切な話題が5件未満の場合は、見つかった分だけを出力してください。
※チャンネル名は必ず「#チャンネル：【#チャンネル名】」として提示されているものから選んでください。

#Slackメッセージ
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは企業のSNS担当者です。社内のSlackメッセージから、社外に共有するのに適切な話題を見つけ、Twitter/X投稿用の魅力的な日本語文章を作成することが得意です。必ず日本語で投稿文を生成してください。"},
                    {"role": "user", "content": prompt + messages_text}
                ],
                max_completion_tokens=2000
            )
            
            external_news = response.choices[0].message.content
            print("✅ 社外向けニュース生成完了")
            return external_news
            
        except Exception as e:
            print(f"❌ OpenAI APIエラー: {str(e)}")
            return None
    
    def generate_news_text(self, messages_file: str = None, days: int = 1, messages: List[Dict] = None) -> str:
        """社外向けニューステキストを生成して返す"""
        
        print(f"\n{'='*60}")
        print(f"📰 社外向けニュース生成を開始")
        print(f"{'='*60}\n")
        
        if messages is None:
            if not messages_file:
                print("❌ メッセージソースが指定されていません")
                return None
            messages = self.load_messages(messages_file)
            if not messages:
                print("❌ メッセージが読み込めませんでした")
                return None
        
        # 最近のメッセージをフィルタリング
        recent_messages = self.filter_recent_messages(messages, days)
        if not recent_messages:
            print("❌ 対象期間のメッセージがありません")
            return None
        
        # 分析用にメッセージを整形
        formatted_text = self.prepare_messages_for_analysis(recent_messages)
        if not formatted_text:
            print("❌ 分析可能なメッセージがありません")
            return None
        
        print(f"📝 分析対象: {len(formatted_text)} 文字")
        
        # 社外向けニュースを生成
        external_news = self.generate_external_news(formatted_text)
        if not external_news:
            print("❌ 社外向けニュースの生成に失敗しました")
            return None
        
        print("\n" + "="*60)
        print("📋 生成された社外向けニュース:")
        print("="*60)
        print(external_news)
        print("="*60 + "\n")
        
        return external_news

def main():
    parser = argparse.ArgumentParser(
        description='社外向けニュース生成ツール（SNS投稿用）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python generate_external_news.py
  python generate_external_news.py --days 1
  python generate_external_news.py --messages-file slack_messages_20250928.json
        """
    )
    
    parser.add_argument('--messages-file', type=str, help='メッセージファイルのパス（デフォルト: 最新のslack_messages_*.json）')
    parser.add_argument('--days', type=int, default=1, help='分析対象の日数（デフォルト: 1日）')
    parser.add_argument('--openai-key', type=str, help='OpenAI APIキー（環境変数より優先）')
    
    args = parser.parse_args()
    
    # APIキー取得
    openai_key = args.openai_key or os.environ.get('OPENAI_API_KEY')
    
    if not openai_key:
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        print("\n環境変数を設定してください:")
        print("export OPENAI_API_KEY='sk-...'")
        return 1
    
    # メッセージファイルを自動検出
    if not args.messages_file:
        import glob
        json_files = glob.glob("slack_messages_*.json")
        if json_files:
            args.messages_file = sorted(json_files)[-1]  # 最新のファイル
            print(f"📁 メッセージファイル: {args.messages_file}")
        else:
            print("❌ slack_messages_*.json ファイルが見つかりません")
            print("先に collect_slack_messages.py を実行してください")
            return 1
    
    # ジェネレーター初期化
    generator = ExternalNewsGenerator(openai_key)
    
    try:
        # ニューステキスト生成
        news_text = generator.generate_news_text(
            messages_file=args.messages_file,
            days=args.days
        )
        
        if news_text:
            print("\n✅ 社外向けニューステキストの生成が完了しました")
            return 0
        else:
            print("\n❌ 社外向けニューステキストの生成に失敗しました")
            return 1
            
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
