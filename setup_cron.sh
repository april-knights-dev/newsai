#!/bin/bash

# スクリプトのパスを設定
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="$(which python3)"

# cronジョブを追加
echo "現在のcrontab:"
crontab -l 2>/dev/null || echo "crontabが設定されていません"

echo ""
echo "以下のcronジョブを追加します:"
echo "0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH collect_slack_messages.py --days 1"

# 既存のcrontabを保存
crontab -l > /tmp/mycron 2>/dev/null || touch /tmp/mycron

# 新しいジョブを追加
echo "0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH collect_slack_messages.py --days 1" >> /tmp/mycron

# crontabを更新
crontab /tmp/mycron
rm /tmp/mycron

echo ""
echo "crontabを更新しました。現在の設定:"
crontab -l