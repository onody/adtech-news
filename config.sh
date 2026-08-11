# adtech-news 設定
# run.sh から読み込まれる。

# 送信先
RECIPIENT="onodera212@gmail.com"

# 送信元 Gmail アカウント（SMTP 認証に使う）
SENDER="onodera212@gmail.com"
SENDER_NAME="AdTech Daily"

# アプリパスワードを保存している macOS Keychain のサービス名
KEYCHAIN_SERVICE="adtech-news-smtp"

# 記事本数
ITEM_COUNT=3

# 使用モデル（opus / sonnet / claude-opus-5 など）
# 2026-08-12: コスト削減のため opus から sonnet に変更。品質劣化があれば戻すこと。
MODEL="sonnet"

# 1 実行あたりのコスト上限（USD）
MAX_BUDGET_USD=3.00

# 生成のタイムアウト（秒）
GEN_TIMEOUT=1500
