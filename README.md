# adtech-news

アドテク業界の日次ダイジェストを生成して、平日の朝にメールで送る。

- 探索は広く（Digiday / AdExchanger / IAB Tech Lab ほか十数サイト）、配信は 3 本に絞る
- 日本語と英語の両方を 1 通に入れる
- 配信済みトピックは `state/seen.json` に記録し、翌日以降は除外する（続報は「前回からの差分」だけ書く）
- 平日 06:12 に launchd が起動

## セットアップ

### 1. Gmail アプリパスワードを Keychain に入れる

2 段階認証を有効にしたうえで https://myaccount.google.com/apppasswords でアプリパスワードを発行し、
Keychain に登録する（平文でファイルに置かない）。

```sh
security add-generic-password -a onodera212@gmail.com -s adtech-news-smtp -w '<16桁のアプリパスワード>'
```

### 2. launchd に登録

```sh
./bin/install.sh
```

### 3. 動作確認

```sh
./bin/run.sh --force --dry-run   # 生成のみ。送信も state 更新もしない
./bin/run.sh --force             # 生成して送信
```

## 使い方

| コマンド | 動作 |
|---|---|
| `bin/run.sh` | 生成して送信（土日はスキップ） |
| `bin/run.sh --force` | 土日でも実行 |
| `bin/run.sh --dry-run` | 生成・レンダリングのみ。送信せず `state` も更新しない |
| `bin/run.sh --date 2026-07-28` | 日付を指定 |
| `bin/run.sh --send-only --date 2026-07-28` | 既存の JSON を送るだけ（生成をやり直さない） |
| `bin/uninstall.sh` | launchd から解除 |

## 構成

```
config.sh                  送信先・モデル・本数・コスト上限
prompts/digest.md          調査と執筆の指示。品質のチューニングはここを触る
bin/run.sh                 生成 → 検証 → レンダリング → 送信
lib/render.py              JSON → HTML / プレーンテキスト（日英2部構成）
lib/send.py                Gmail SMTP 送信 + state 更新
state/seen.json            配信済みトピック（120日で自動的に切り捨て）
out/YYYY-MM-DD.{json,html,txt}   生成物
logs/YYYY-MM-DD.log        実行ログ
launchd/                   スケジュール定義
```

## 動作の流れ

1. launchd が `bin/run.sh` を起動
2. `claude -p` をヘッドレスで実行。`state/seen.json` を読んで既報を除外し、
   `prompts/digest.md` に従って 12 本以上の候補を集め、インパクト順に 3 本を選び、
   日英で書いて `out/<date>.json` に出力
3. `lib/render.py` が HTML とテキストを生成
4. `lib/send.py` が Gmail SMTP で送信し、配信したトピックを `state/seen.json` に追記

送信が失敗した場合、`state` は更新されない。同じ内容で `--send-only` を再実行できる。

## チューニング

品質を変えたいときに触る場所:

- **選定基準** — `prompts/digest.md` の「3 本に絞る」の加点／減点リスト
- **探索範囲** — 同ファイルの「一次ソース」「準ソース」
- **本数** — `config.sh` の `ITEM_COUNT`
- **書き方（ASIS / TOBE / 何が新しいか）** — 同ファイルの「各記事を書く」
- **配信時刻** — `launchd/com.onod.adtech-news.plist` の `StartCalendarInterval` を変えて `bin/install.sh` を再実行

`out/<date>.json` の `runners_up` に、選ばなかった候補と却下理由が入っている。
選定基準がズレていると感じたらここを見る。

## 制約

- Mac が起動している必要がある。スリープ中に発火時刻を過ぎた場合、launchd は次に起きたときに 1 回だけ実行する
- `claude` CLI の認証（Keychain の OAuth トークン）に依存する。ログアウトすると止まる
- 1 実行あたりのコストは `config.sh` の `MAX_BUDGET_USD` で上限を掛けている
