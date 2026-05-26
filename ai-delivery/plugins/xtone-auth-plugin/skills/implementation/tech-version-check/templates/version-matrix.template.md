# 採用バージョン記録（tech-version-check / B-11）

> 本テンプレートは `tech-version-check` スキルの出力雛形。値は採用時点で context7 / 公式リリースから取得した実際の数値に置換する（プレースホルダ `<...>` を埋める）。`docs/environment-setup.md` の方針に従い、AI は固定値を勝手に決めない。

- 作成日: `<YYYY-MM-DD>`
- 案件: `<project name>`
- 採用根拠: `docs/environment-setup.md`「公式の最新安定版」+ 採用日時点の確認

## 1. 言語ランタイム

| 名前 | 採用バージョン | 公式最新 | 要求 | 根拠 URL |
|---|---|---|---|---|
| `<lang>` | `<version>` | `<version>` | — | `<url>` |

## 2. メイン FW

| 名前 | 採用 | 公式最新 | 要求ランタイム | 根拠 URL |
|---|---|---|---|---|
| `<fw>` | `<version>` | `<version>` | `<lang> <constraint>` | `<url>` |

## 3. 主要ライブラリ・SDK

| 名前 | 採用 | 公式最新 | 要求 | 根拠 URL |
|---|---|---|---|---|
| `<lib>` | `<version>` | `<version>` | `<lang> <constraint>` | `<url>` |

## 4. ツール / コンテナ

| 名前 | 採用 | 公式最新 | 用途 | 根拠 URL |
|---|---|---|---|---|
| `<tool>` | `<version>` | `<version>` | `<purpose>` | `<url>` |

## 5. 既知の非互換性 / 警戒事項

- `<例: connection_pool 3.0.2 が Ruby 3.3 で例外 — リリースノート https://... を参照>`

## 6. 採用根拠の要約

- `<例: 「公式最新を採る方針（environment-setup.md）」に従い、context7 で 2026-05-26 時点の最新を確認・採用。特定バージョン固定の要望なし。>`
- 特定バージョン固定の要望があった場合は `docs/pending-decisions.md` の DP-XXX として記録（warn_and_document）。
