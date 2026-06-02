# 採用バージョン記録（tech-version-check / B-11・B-25）

> 本ファイルは `tech-version-check` スキルの出力。値は採用時点で公式リリースから取得した実数。`docs/environment-setup.md`「公式の最新安定版」に従い、AI は固定値を勝手に決めない。setup 系 Skill（`project-monorepo-scaffold` / `project-frontend-init` / `project-backend-init` / `project-local-infra`）が参照する。

- 作成日: 2026-06-02
- 案件: project-backend-init レシピ検証（rails / hotwire）
- 採用根拠: `docs/environment-setup.md`「公式の最新安定版」+ 採用日時点の確認

## 1. 言語ランタイム

| 名前 | 採用バージョン | 公式最新 | 要求 | 根拠 URL |
|---|---|---|---|---|
| Ruby | **未確定（DP-RUBY-VER 起票済み）**／既定サジェスト 4.0.5 | 4.0.5（4系）／ 3.4.9（3系） | — | https://www.ruby-lang.org/en/downloads/ |

> Ruby は 4系（4.0.5）と 3系（3.4.9）が安定版として並存。**最新の 4系を既定サジェスト**とするが、メジャー選択は案件依存のため「6.」で DP-RUBY-VER として起票（断定で書かない）。

## 2. メイン FW

| 名前 | 採用 | 公式最新 | 要求ランタイム | 根拠 URL |
|---|---|---|---|---|
| Rails | 8.1.3 | 8.1.3 | Ruby は gemspec の `required_ruby_version` で都度確認（数値固定しない）。8.1 系は Ruby 4 系に対応 | https://rubygems.org/gems/rails |

## 3. 主要ライブラリ・SDK

| 名前 | 採用 | 公式最新 | 要求 | 根拠 URL |
|---|---|---|---|---|
| （土台のみ・ドメイン gem は各モジュール） | — | — | — | — |

> backend-init は土台の器のみ生成（DP-PINIT-11）。lint は Rails 標準同梱の `rubocop-rails-omakase` を使う（別途追加しない）。

## 4. ツール / コンテナ

| 名前 | 採用 | 公式最新 | 用途 | 根拠 URL |
|---|---|---|---|---|
| postgres（image） | 16 | （local-infra で解決） | docker compose の DB | https://hub.docker.com/_/postgres |
| ruby（image） | `${RUBY_VERSION}`-slim（.ruby-version 連動） | — | Dockerfile.dev ベース | https://hub.docker.com/_/ruby |

## 5. 既知の非互換性 / 警戒事項

- 採用 Ruby のメジャー（4系）は比較的新しい。gem の一部が 4系未対応の場合がある → `bundle install` で解決確認。問題時は DP-RUBY-VER で 3系（3.4.9）採用を再検討。
- システム同梱の古い Ruby では最新 Rails が動かない（environment-setup の実例）。docker compose 方針ではコンテナの `RUBY_VERSION` で解決するため本リスクは緩和。

## 6. 複数候補が残った技術判断（DP 起票 / B-25）

| 仮 DP ID | 対象 | 候補 | 選定が案件依存な理由 | pending 起票 |
|---|---|---|---|---|
| DP-RUBY-VER | 言語ランタイム Ruby | 4.0.5（4系・最新メジャー）/ 3.4.9（3系・実績豊富） | 採用 FW の `required_ruby_version` を満たす範囲で、4系の新機能・将来性 vs 3系の gem 互換実績のトレードオフ。Rails 8.1 は両対応 | 済（`docs/pending-decisions.md`） |

> 既定サジェストは **4系（4.0.5）**。確定は人間が行う（warn_and_document）。1〜2 の表で Ruby を断定せず「未確定（DP-RUBY-VER）」と記載済み。

## 7. 採用根拠の要約

- 「公式最新を採る方針（environment-setup.md）」に従い 2026-06-02 時点の公式最新を確認。Ruby は 4系/3系が並存するため **4系を既定サジェスト**としつつ DP-RUBY-VER を起票（B-25・人間判断をスルーさせない）。
- Rails は公式最新 8.1.3 を採用（候補一意のため DP 起票せず）。
- 特定バージョン固定の要望があれば `docs/pending-decisions.md` の DP として記録（warn_and_document）。

## 8. Dockerfile / Gemfile に残すコメント例

```dockerfile
# Dockerfile.dev（Rails コンテナ）
# tech-version-check (B-11) 2026-06-02 確認: https://hub.docker.com/_/ruby
# RUBY_VERSION は .ruby-version と一致させる（固定しない）。Ruby は 4系を既定サジェスト（DP-RUBY-VER）。
ARG RUBY_VERSION
FROM docker.io/library/ruby:${RUBY_VERSION}-slim
```

```ruby
# .ruby-version（生成時に採用版へ置換。既定サジェストは 4系最新）
# tech-version-check (B-11) 2026-06-02 確認: https://www.ruby-lang.org/en/downloads/
```

> **AI は固定値を勝手に決めない**。`<採用バージョン>` は公式リリースで確認した実値で置換し、確認日と URL を残す。
