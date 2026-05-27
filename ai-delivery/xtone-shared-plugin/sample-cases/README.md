# sample-cases — 業種別 架空案件カタログ

各 Rollout プラグイン（T-023〜T-045）の DoD には **「サンプル案件（架空）で要件定義〜実装まで進められる」** という Verification 項目がある。プラグインごとに別々の架空案件を作ると、同じ案件が認証では使えても決済では使えないといった整合性崩れが起きるため、本ディレクトリに **業種別の架空案件カタログ**を集約し、各プラグインからは symlink or 参照で取り込む（CONV-14 と同じ「Single Source of Truth」の発想を、検証用入力にも適用）。

> 認証プラグインで先行運用していた `plugins/xtone-auth-plugin/sample-inputs/bookclub-app.requirements-input.md` は、リファレンス実装の経緯保存のためそのまま残す（**並存**）。新規 Rollout プラグインの Verification では原則として本カタログを使う。

## ディレクトリ構造

```
xtone-shared-plugin/sample-cases/
├── README.md                              # このファイル
├── ec-d2c-app/
│   ├── requirements-input.md              # 自然言語のヒアリングメモ（/req-collect への入力）
│   └── requirements.json                  # requirements.schema.json 準拠の構造化要件
├── maas-carshare/
├── media-content/
├── education-voucher/
├── corporate-site/
├── business-saas/
└── event-campaign-lp/
```

各案件ディレクトリは以下 2 ファイルを持つ:

| ファイル | 用途 |
|---|---|
| `requirements-input.md` | 自然言語のクライアントヒアリング想定テキスト。`/req-collect` などの requirements-extraction スキルの入力として使う |
| `requirements.json` | `requirements.schema.json` 準拠の構造化要件。後段のスキル（design / implementation）が直接インプットとして使える |

両ファイルとも `requirements.schema.json` でバリデートできる必要はないが（自然言語側は対象外）、`requirements.json` は **`validate-plugin.sh` の対象になっても pass する**ことを基準とする。

## 案件 × ユースケース マトリクス

各プラグインが「自分のユースケース該当案件」を素早く見つけられるよう、横断マトリクスを置く。`✔` は当該案件で扱われていることを示す（=その Rollout プラグインの Verification 入力に使える）。

| 業種 / 案件 | 認証 | 決済 | 通知 | コンテンツ | 検索 | 管理画面 | 帳票 | 位置情報 | QR | 予約 | RBAC | 監査ログ | 分析 | コミュニティ | OGP / 静的 | キャンペーン |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| [ec-d2c-app](./ec-d2c-app/) | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |  | ✔ | ✔ |  |  |
| [maas-carshare](./maas-carshare/) | ✔ | ✔ | ✔ |  |  |  |  | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| [media-content](./media-content/) | ✔ |  |  | ✔ | ✔ |  |  |  |  |  |  |  | ✔ |  | ✔ |  |
| [education-voucher](./education-voucher/) | ✔ |  | ✔ |  |  | ✔ | ✔ |  |  |  | ✔ | ✔ |  |  |  |  |
| [corporate-site](./corporate-site/) |  |  | ✔ | ✔ |  | ✔ |  |  |  |  |  |  | ✔ |  | ✔ |  |
| [business-saas](./business-saas/) | ✔ |  | ✔ |  |  | ✔ |  |  |  |  | ✔ | ✔ |  |  |  |  |
| [event-campaign-lp](./event-campaign-lp/) | ✔ |  | ✔ |  |  |  |  |  | ✔ |  |  |  | ✔ |  | ✔ | ✔ |

> マトリクスは雛形であり、各 Rollout プラグイン側で対応関係を見直したうえで `sample-inputs/` から symlink を張る運用にする。新規プラグインが「自分のユースケースは✔がないので新案件追加」と判断したら、本カタログに追加して PR を立てる（カタログ更新は本ガイドの責務）。

## 各プラグインからの参照方式

各 Rollout プラグインは `sample-inputs/` 直下に **symlink を 1 本以上**置き、検証用入力としてこのカタログを参照する。

```bash
# 例: 決済プラグインが ec-d2c-app と event-campaign-lp を使う
cd plugins/xtone-payment-plugin/sample-inputs
ln -s ../../../xtone-shared-plugin/sample-cases/ec-d2c-app ec-d2c-app
ln -s ../../../xtone-shared-plugin/sample-cases/event-campaign-lp event-campaign-lp
```

- リンク名はカタログ側のディレクトリ名と一致させる（マトリクスの再利用性のため）。
- プラグイン固有の追加ヒアリング（その案件で**そのプラグインに特化した想定**を補足したいケース）が必要なら、symlink と並べて `sample-inputs/<case-name>.notes.md` を置く。本体（カタログ側）は編集しない。
- 認証プラグインの既存 `bookclub-app.requirements-input.md` は並存（移行しない）。リファレンス実装の経緯保存のため。

## 案件追加・編集の運用

- **新規案件を追加**: 本カタログにディレクトリを新設 → `requirements-input.md` と `requirements.json` を作成 → 本 README のマトリクスを更新 → PR
- **既存案件の修正**: 既に他プラグインが symlink で参照している可能性が高いため、**破壊的変更（要件削除・ID 変更）は別案件として新設**し、旧案件は残す（migration 期間を取る）
- **schema 準拠**: `requirements.json` は `validate-plugin.sh` で常に検証可能な状態を維持する

## 関連

- スキーマ: [`../schemas/v1/requirements.schema.json`](../schemas/v1/requirements.schema.json)
- 上位ガイド: [`../../docs/plugin-developer-guide.md`](../../docs/plugin-developer-guide.md) Step 5「パイロット → 訂正バックログ → 再パイロット」
- リファレンス実装の bookclub-app: [`../../plugins/xtone-auth-plugin/sample-inputs/bookclub-app.requirements-input.md`](../../plugins/xtone-auth-plugin/sample-inputs/bookclub-app.requirements-input.md)
