# 実行環境セットアップ・バージョン方針

プラグインを使った開発 / プラグインを実装するための **実行環境前提** と **バージョン選定方針**。

## バージョン方針（重要）

1. **バージョンは固定しない（陳腐化回避）。** ドキュメント・テンプレートに特定の数値（例: 「Ruby 3.x」「Rails 8」）をハードコードしない。
2. **基本は公式の最新安定版を使う。** 着手時に下記「公式情報源」から最新安定版を確認して導入する。
3. **特定バージョンが必要な場合は判断ポイント。** クライアント制約・レガシー互換・特定ライブラリ依存などで最新以外を使う必要があるときは、**人間に確認**し、決定をプラグインの `docs/pending-decisions.md` に記録する（warn_and_document）。AI が勝手に固定しない。

> 言い換え: 既定は「最新安定版（公式から取得）」。固定は例外で、必ず人間判断を経る。

## 公式情報源（最新安定版の確認先）

| 対象 | 確認先 | 補足 |
|---|---|---|
| Ruby | https://www.ruby-lang.org/en/downloads/ | 最新安定版（stable releases） |
| Rails | https://rubygems.org/gems/rails | 最新版。リリース内容は https://guides.rubyonrails.org |
| Node.js | https://nodejs.org | Active LTS を既定とする |

**フレームワークが要求する最小ランタイムは固定で覚えない。** 例: Rails が要求する最小 Ruby は数値で記憶せず、その Rails バージョンの **gemspec（`required_ruby_version`）/ リリースノート**で都度確認する（`gem spec rails required_ruby_version`、または `rails new` がエラーで要求を提示する）。

## セットアップ（バージョンマネージャ・番号を固定しない）

システム同梱の古いランタイムを避け、バージョンマネージャで最新安定版を導入する。

```bash
# Ruby（rbenv の例。<latest> は固定値ではなく「確認した最新安定版」を入れる）
rbenv install -l          # インストール可能な最新安定版を確認
rbenv install <latest>
rbenv local  <latest>     # プロジェクト直下に .ruby-version を生成

# Node（mise / nvm 等で Active LTS を導入）
mise use node@lts   # または nvm install --lts
```

- プロジェクトの `.ruby-version` / `.node-version` には **選定時点の最新安定版**を記録する。テンプレートには固定値を置かない（生成・着手時に解決）。
- バージョンマネージャは rbenv / mise / asdf いずれでもよい（チームの標準に従う）。

## なぜこの方針か（実例）

実案件で**システム同梱の古い Ruby（例: 2.6 系）でプラグインを使おうとして、最新 Rails が動かない**ケースが発生した。`rbenv` で当時の最新安定版（3.3 系）を導入することで回避できた。**着手時に公式最新を用意する**ことを徹底する。なお、具体的な数値は「その時点の最新」であって将来の固定要件ではない。

## 関連

- プラグインの**言語別レシピ**: `plugins/<plugin>/skills/implementation/<skill>/references/<stack>.md`
- 特定バージョン固定が必要な場合の起票先: プラグインの `docs/pending-decisions.md`
