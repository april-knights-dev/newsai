import os
import argparse
from typing import Optional
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackLeaver:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def _resolve_channel_id(self, identifier: str) -> Optional[str]:
        if not identifier:
            return None
        if identifier.startswith("C") or identifier.startswith("G"):
            return identifier
        name = identifier.lstrip("#")
        try:
            response = self.client.conversations_list(
                exclude_archived=False,
                types="public_channel,private_channel",
                limit=1000,
            )
            channels = response.get("channels", [])
            for channel in channels:
                if channel.get("name") == name:
                    return channel.get("id")
            while response.get("response_metadata", {}).get("next_cursor"):
                cursor = response["response_metadata"]["next_cursor"]
                response = self.client.conversations_list(
                    exclude_archived=False,
                    types="public_channel,private_channel",
                    limit=1000,
                    cursor=cursor,
                )
                channels = response.get("channels", [])
                for channel in channels:
                    if channel.get("name") == name:
                        return channel.get("id")
        except SlackApiError:
            return None
        return None

    def leave(self, channel: str) -> bool:
        channel_id = self._resolve_channel_id(channel)
        if not channel_id:
            print("❌ チャンネルが見つかりませんでした")
            return False
        try:
            self.client.conversations_leave(channel=channel_id)
            print("✅ チャンネルから退出しました")
            return True
        except SlackApiError as e:
            data = getattr(e.response, "data", e.response)
            error = data.get("error", str(e)) if isinstance(data, dict) else str(e)
            if error == "not_in_channel":
                print("ℹ️ チャンネルのメンバーではありません")
            else:
                print(f"❌ 退出に失敗しました: {error}")
            return False


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="指定したSlackチャンネルから退出する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python leave_channel.py --channel general
  python leave_channel.py --channel C1234567890
        """,
    )
    parser.add_argument("--channel", type=str, required=True, help="チャンネル名またはID")
    parser.add_argument("--token", type=str, help="Slackボットトークン")
    args = parser.parse_args()

    slack_token = args.token or os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        print("❌ エラー: SLACK_BOT_TOKEN が設定されていません")
        print("export SLACK_BOT_TOKEN='xoxb-...' または --token を指定してください")
        return 1

    leaver = SlackLeaver(slack_token)
    success = leaver.leave(args.channel)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
