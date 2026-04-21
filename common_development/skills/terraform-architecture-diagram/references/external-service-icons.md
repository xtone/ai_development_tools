# External Service Icons (3rd Party / Cross-cloud)

AWS / GCP のいずれの構成でも参照される **外部サービス（3rd Party）** のアイコンカタログ。
Terraform で直接管理されないサービス（GitHub、Firebase 等）でも、アーキテクチャ図に登場する場合は **必ず本カタログの SVG 埋め込み形式** で描画する。

## 目次

1. [使用ルール](#使用ルール)
2. [スタイルテンプレート](#スタイルテンプレート)
3. [⚠️ 重要な落とし穴（;base64, を書かない）](#-重要な落とし穴base64-を書かない)
4. [カタログ](#カタログ)
   - [GitHub](#github)
   - [Firebase Hosting](#firebase-hosting)
5. [カタログに無いサービスを追加する場合](#カタログに無いサービスを追加する場合)

---

## 使用ルール

### 必須ルール

- 外部サービスを図に登場させる場合、**plain 矩形 / shape=mxgraph.signs.tech.\* / 単色四角形での代替表現は禁止**
- 必ず本カタログから SVG を引いて `shape=image;...image=data:image/svg+xml,<base64>` 形式で描画する
- 理由: Draw.io Desktop 版で `mxgraph.signs.tech.*` 等は標準ライブラリに含まれず fallback で単色矩形になる。SVG 埋め込みなら Desktop / Web どちらでも同一描画になる

### 利用シーン

| サービス | 典型的な登場文脈 |
|---------|----------------|
| GitHub | CodePipeline / GitHub Actions の source、external git ホスティング |
| Firebase Hosting | CloudFront origin（frontend SPA 配信）、独立 hosting |

---

## スタイルテンプレート

```
shape=image;aspect=fixed;imageAspect=0;image=data:image/svg+xml,<base64データ>;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top
```

XML 例：

```xml
<mxCell id="github_source" value=""
  style="shape=image;aspect=fixed;imageAspect=0;image=data:image/svg+xml,{BASE64};labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top"
  vertex="1" parent="1">
  <mxGeometry x="{X}" y="{Y}" width="{W}" height="{H}" as="geometry"/>
</mxCell>
```

ラベルは別の `text` セルとしてアイコン下に配置する（[drawio-xml-guide.md §10 ラベル配置パターン](drawio-xml-guide.md) 参照）。アイコンの `value` は空文字列にする。

---

## ⚠️ 重要な落とし穴（`;base64,` を書かない）

`image=data:image/svg+xml;base64,...` と書くと、`;base64,` の `;` が drawio スタイル区切り文字と衝突してスタイルが分断され、画像が描画されない。

**必ず以下の形式で記述する**：

```
image=data:image/svg+xml,<base64データ>
```

（`;base64` を省略し、base64 データは `,` の後ろに直接続ける。drawio は拡張仕様として base64 をそのまま解釈する。）

---

## カタログ

### GitHub

**用途**: CodePipeline source / GitHub Actions / external git hosting
**推奨サイズ**: 48 × 48
**配置例**: CI/CD コンテナの先頭（CodePipeline の上）に配置し、GitHub → CodePipeline のエッジ（赤実線 = `DEPLOY_FLOW`）で接続

```
image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA5OCA5NiI+PHBhdGggZmlsbD0iIzI0MjkyRiIgZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik00OC44NTQgMEMyMS44MzkgMCAwIDIyIDAgNDkuMjE3YzAgMjEuNzU2IDEzLjk5MyA0MC4xNzIgMzMuNDA1IDQ2LjY5IDIuNDI3LjQ5IDMuMzE2LTEuMDU5IDMuMzE2LTIuMzYyIDAtMS4xNDEtLjA4LTUuMDUyLS4wOC05LjEyNy0xMy41OSAyLjkzNC0xNi40Mi01Ljg2Ny0xNi40Mi01Ljg2Ny0yLjE4NC01LjcwNC01LjQyLTcuMTctNS40Mi03LjE3LTQuNDQ4LTMuMDE1LjMyNC0zLjAxNS4zMjQtMy4wMTUgNC45MzQuMzI2IDcuNTIzIDUuMDUyIDcuNTIzIDUuMDUyIDQuMzY3IDcuNDk2IDExLjQwNCA1LjM3OCAxNC4yMzUgNC4wNzQuNDA0LTMuMTc4IDEuNjk5LTUuMzc4IDMuMDc0LTYuNi0xMC44MzktMS4xNDEtMjIuMjQzLTUuMzc4LTIyLjI0My0yNC4yODMgMC01LjM3OCAxLjk0LTkuNzc4IDUuMDE0LTEzLjItLjQ4NS0xLjIyMi0yLjE4NC02LjI3NS40ODYtMTMuMDM4IDAgMCA0LjEyNS0xLjMwNCAxMy40MjYgNS4wNTJhNDYuOTcgNDYuOTcgMCAwIDEgMTIuMjE0LTEuNjNjNC4xMjUgMCA4LjMzLjU3MSAxMi4yMTMgMS42MyA5LjMwMi02LjM1NiAxMy40MjctNS4wNTIgMTMuNDI3LTUuMDUyIDIuNjcgNi43NjMuOTcgMTEuODE2LjQ4NSAxMy4wMzggMy4xNTUgMy40MjIgNS4wMTUgNy44MjIgNS4wMTUgMTMuMiAwIDE4LjkwNS0xMS40MDQgMjMuMDYtMjIuMzI0IDI0LjI4MyAxLjc4IDEuNTQ4IDMuMzE2IDQuNDgxIDMuMzE2IDkuMTI2IDAgNi42LS4wOCAxMS44OTctLjA4IDEzLjUyNiAwIDEuMzA0Ljg5IDIuODUzIDMuMzE2IDIuMzY0IDE5LjQxMi02LjUyIDMzLjQwNS0yNC45MzUgMzMuNDA1LTQ2LjY5MUM5Ny43MDcgMjIgNzUuNzg4IDAgNDguODU0IDB6Ii8+PC9zdmc+
```

ラベル文字列: `GitHub`（リポジトリ名やブランチ名等のプロジェクト固有情報は含めない。これらは注釈セルで提示する）

---

### Firebase Hosting

**用途**: CloudFront default origin（frontend SPA 配信）、独立 hosting
**推奨サイズ**: 44 × 60（縦長の flame ロゴ）
**配置例**: AWS 構成では CloudFront (Public) の右隣（`layout-algorithm.md` §9.6 priority 1）。GCP 構成では project 内の独立配置

```
image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMzUxIj48cGF0aCBmaWxsPSIjRkZDMjRBIiBkPSJNMS4yNTMgMjgwLjczMmwxLjYwNS0zLjEzMSA5OS4zNTMtMTg4LjUxOC0uMTktLjkyN0w1OC4yNjYgMjEuMTI0Yy0xLjkyNy00Ljg1MS04LjgzMS00LjU4OC0xMC4zNzUuMzk3TDEuMjUzIDI4MC43MzJ6Ii8+PHBhdGggZmlsbD0iI0ZGQTcxMiIgZD0iTTIuODU4IDI3Ny42MDFsOTguNjM1LTE4Ny4xNjQgNDQuMjExLTgzLjU4NmMxLjU4My0zLjg0NCA2Ljg2NS00LjM1NyA5LjE0OC0uNzU3bDgzLjk1IDEzMi40MzkgMy4yMSA1LjA2M0wyLjg1OCAyNzcuNjAxeiIvPjxwYXRoIGZpbGw9IiNGNEJENjIiIGQ9Ik0xMzQuNzcyIDE0OC4wNTNsMzMuNDY1LTM0LjEwOC0zMy40NjItNjMuODk4Yy0zLjE3LTYuMDE4LTEyLjA4My02LjA1OC0xNS4zMDIuMDQ1TDEwMS4zOTIgOTMuNTN2My4wOGwzMy4zOCA1MS40NDN6Ii8+PHBhdGggZmlsbD0iI0ZGQTUwRSIgZD0iTTEzNS4wMDkgMzUwLjUzMkwyNTQuOTIgMjgxLjM3bC0zNC4yNjYtMjAwLjkxYy0xLjA3My02LjI5Ny04Ljg1OS04LjY4OS0xMy4yNjQtMy45ODlMMS4yNTMgMjgwLjczMmwxMzIuNTc5IDcyLjI4YzMuNzYgMi4wOTkgNy4zNTcgMi4wOTkgMTEuMTE3IDB6Ii8+PC9zdmc+
```

ラベル文字列: `Firebase Hosting`（`(external, frontend)` のような副情報行は付けない）

備考: 同じ flame ロゴは Firestore / Firebase Auth など Firebase 系サービス全般で共用可能。

---

## カタログに無いサービスを追加する場合

新規 3rd Party サービスを図に追加する必要がある場合：

1. 公式 SVG ロゴを取得（例: Slack、Datadog、PagerDuty、Stripe 等）
2. SVG を base64 エンコード（`base64` コマンド or オンラインツール）
3. 本ファイルにエントリ追加：
   - サービス名
   - 用途
   - 推奨サイズ
   - 配置例
   - base64 データ（`image=data:image/svg+xml,<data>` の形式）
4. **暫定での plain 矩形描画は禁止**。SVG 取得が間に合わない場合はユーザーに確認・対応依頼する

### 候補（未追加）

以下は将来追加候補として記録：

| サービス | 想定用途 | 状態 |
|---------|---------|------|
| Slack | SNS subscription / 通知連携 | 未追加 |
| Datadog | 監視連携 | 未追加 |
| PagerDuty | アラート連携 | 未追加 |
| Stripe | 決済連携 | 未追加 |
| Auth0 / Okta | external IdP | 未追加 |
| Cloudflare | CDN / DNS | 未追加 |
