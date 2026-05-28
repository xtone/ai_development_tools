---
name: aid-decision-point-registration
description: 新規プラグインで検出された判断ポイント候補（DP-DRAFT）を Notion 判断ポイントカタログDB（data_source_id 64248f5c-b2f5-4c90-8ccb-7f53692b59b2）に安全に起票するスキル。プラグイン実装フェーズで /aid-domain-architect-design が検出した DP-AID-02 80% 重複判定の結果を受け、プレビュー → ユーザ確認 → 起票の 3 段階で書き込み、対象プラグインの docs/decision-points.md も同期更新する。書き込み権限は本スキルに限定（他スキルは読み取りのみ）。
---

# AID Decision Point Registration Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`aid-plugin-architecture-design` / `aid-domain-architect-design` が検出した DP 候補（`dp_candidates`）のうち `reuse: false` の項目を、**Notion 判断ポイントカタログDB へ安全に起票**する専用スキル。書き込みは本スキルのみに限定し、誤起票・重複起票・命名衝突を防ぐ。

> 設計方針: Notion DP DB は AIデリバリシステム全体の真実の源。**全プラグイン横断で参照される共有資産**なので、書き込みは最小権限・最大の慎重さで行う。本スキルが**唯一の起票チャネル**。

## 入出力

- **入力:**
  - `target_plugin_path`（例: `ai-delivery/plugins/xtone-payment-plugin`）
  - `target_plugin_path/delivery/plugin-architecture.json`（`dp_candidates` を参照）
  - （省略可）`<usecase>-architect.md` の DP 比較表（最終確認用）
  - Notion MCP 接続（必須・書き込み権限）
- **出力:**
  - Notion 判断ポイントカタログDB（`data_source_id: 64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）の新規エントリ（プレビュー → ユーザ確認後）
  - `target_plugin_path/docs/decision-points.md` の同期更新（同フォーマット）
  - `delivery/dp-registration-log.md`（起票記録：仮 ID → 正規 DP-ID 対応表・Notion ページ URL・起票日時・起票者）
  - **`plugin-architecture.json` の更新**: `dp_candidates[*].id` を仮 ID（`DP-<USECASE>-DRAFT-NN`）から正規 ID（`DP-<USECASE>-NN` 等）に書き換え

## 起票プロセス（3 段階・必須）

### Step A: プレビュー

1. `dp_candidates` のうち `reuse: false` を抽出
2. 各候補について以下を表形式でユーザに提示：

| 仮 ID | タイトル | 選択肢 | 判断軸 | 誤判断リスク | 適用条件 | MVP 推奨 | フェーズ |
|---|---|---|---|---|---|---|---|
| `DP-PAYMENT-DRAFT-01` | 決済プロバイダ選択 | Stripe / GMO / Komoju | セキュリティ / コスト / 国際対応 | 後段で交代 | 全決済案件 | Stripe（adapter で差し替え可能） | 設計 |

3. **既存 DP との重複チェック結果**も同時に提示（DP-AID-02 80% ルールの再確認）：
   - 既存 DP DB を `usecase` 関連語で再検索
   - 80% 以上重複する既存 DP があれば「既存 `DP-NNN` の再利用を推奨。新規起票しますか？」と確認

### Step B: ユーザ確認

以下を**1 件ずつ**ユーザに確認（一括承認禁止・誤起票防止）：

1. **起票する / しない / 既存再利用に切替**の 3 択
2. **正規 ID の命名**:
   - 既存 DB に `DP-NNN` 形式（DP-001〜DP-028 等）と `DP-USECASE-NAME-NNN` 形式（DP-INVITATION-POLICY-001 等）が混在している
   - 新規プラグイン固有の DP は **`DP-<USECASE>-NNN`** 形式を推奨（CONV-19 拡張・要 ADR）
   - 既存 ID と衝突しないことを Notion 検索で**起票直前に再確認**
3. **MVP 推奨の有無**: 既定推奨を置かない判断（auth の DP-008 型）も**明示的に確認**
4. **適用条件**: 「全案件 / 特定の案件種別のみ / 本プラグインでは不採用」のいずれかを明示

### Step C: 起票

ユーザが承認した項目のみ Notion DP DB に**1 件ずつ**書き込む：

1. 仮 ID → 正規 ID への置換を `plugin-architecture.json` に反映
2. Notion ページ作成（DP-DB のスキーマに沿う）
3. 作成された Notion ページ URL を `delivery/dp-registration-log.md` に記録
4. **書き込み失敗時のリトライ**: 指数バックオフ（1s, 2s, 4s）3 回 → 失敗で人間エスカレ（mcp-setup-guide.md の Rate Limit 動作と整合）
5. **書き込み成功後**:
   - 対象プラグインの `docs/decision-points.md` に同フォーマットで追記
   - 対象プラグインの `<usecase>-architect.md` の DP-ID を仮から正規に置換
   - `pending-decisions.md` から該当行を除く（起票済みになったので「未決」ではなくなる）

## 命名衝突チェック（必須）

起票直前に以下を確認（Notion MCP で DP-DB を全文検索）：

| チェック項目 | 失敗時の動作 |
|---|---|
| `DP-<USECASE>-NNN` 形式で同 ID が既存 | 連番を +1 して再提案・ユーザ確認 |
| `DP-NNN` 形式と衝突（例: 新規が `DP-007` と被る） | 必ずプレフィックス付き形式に変える・ユーザ確認 |
| タイトル文字列が 90% 一致する既存 DP | 「既存 `DP-NNN` と内容が近い。再利用しますか？」と提示 |
| 同プラグインの `docs/decision-points.md` に既載 | 警告・新規起票しない |

> 命名衝突は**起票後の修正が困難**（Notion DB のリレーションを直す必要が出る）。**起票前に潰す**のが鉄則。

## 既存 DP 再利用候補の検証（DP-AID-02 80% ルール）

`dp_candidates` のうち `reuse: true` が立っているものは本スキルでは起票しない。代わりに：

1. 既存 DP（仮 `DP-007` 等）の最新内容を Notion から取得
2. 当該ユースケースでの**解釈の妥当性**をユーザに確認
3. 妥当なら `target_plugin_path/docs/decision-points.md` に「**`DP-NNN` を本プラグインでも採用（理由: ...）**」と追記（**新規 DP は起票しない**）
4. 妥当でない（解釈が苦しい・80% 重複の主張が弱い）なら `reuse: false` に切り替えてユーザに新規起票を提案

## Notion DP DB のスキーマ（書き込み時に埋めるフィールド）

`docs/notion-db-catalog.md` 記載の判断ポイントカタログDB（DP-, data_source_id `64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）に書き込む。auth プラグインの `docs/decision-points.md` から推定される必須フィールド：

| フィールド | 例 |
|---|---|
| ID（タイトル） | `DP-PAYMENT-001` |
| 名称 | `決済プロバイダ選択` |
| フェーズ | `設計` |
| 選択肢 | `Stripe / GMO / Komoju` |
| 判断軸 | `セキュリティリスク / クライアント規制 / コスト / 国際対応` |
| 誤判断リスク | `後段フェーズでスタック交代を迫られる。日本向け案件で Stripe の決済手段不足が顕在化` |
| 適用条件 | `決済機能を持つ全案件` |
| MVP の既定推奨 | `Stripe（PaymentAdapter で差し替え可能設計を維持）` |
| 関連プラグイン | `xtone-payment-plugin` |
| 関連タスク | `T-027`（型化タスクDB へのリレーション） |

> 実 DB スキーマは Notion MCP の `notion-fetch` で `collection://64248f5c-b2f5-4c90-8ccb-7f53692b59b2` を引いて確認する。本スキルは起票前に**必ず**スキーマ再確認を行う（DB プロパティが変わっている可能性に追従）。

## `docs/decision-points.md` の同期更新

Notion 起票成功後、対象プラグインの `docs/decision-points.md` に auth プラグインと**同フォーマット**で追記：

```markdown
## DP-PAYMENT-001 決済プロバイダ選択

- **フェーズ**: 設計
- **選択肢**: Stripe / GMO / Komoju
- **判断軸**: セキュリティリスク / クライアント規制 / コスト / 国際対応
- **誤判断リスク**: 後段フェーズでスタック交代を迫られる。日本向け案件で Stripe の決済手段不足が顕在化
- **適用条件**: 決済機能を持つ全案件
- **MVP の既定推奨**: Stripe（`PaymentAdapter` で差し替え可能設計を維持）
```

## 手順

1. **前提チェック**:
   - Notion MCP 接続確認（書き込み権限）
   - `delivery/plugin-architecture.json` 存在確認
   - `target_plugin_path/docs/decision-points.md` 存在確認（無ければ起票後に新規作成）
2. **候補抽出**:
   - `dp_candidates[?reuse == false]` を抽出
   - `dp_candidates[?reuse == true]` は別フローで処理（既存 DP 再利用検証）
3. **Step A: プレビュー**（上記）
   - 命名衝突チェックを**プレビュー時点で先行実施**（起票前に潰す）
4. **Step B: ユーザ確認**（1 件ずつ・上記）
5. **Step C: 起票**（1 件ずつ・上記）
   - リトライ・失敗エスカレ
   - 起票成功後の `docs/decision-points.md` 同期・`<usecase>-architect.md` の ID 置換
6. **記録**:
   - `delivery/dp-registration-log.md` に「仮 ID → 正規 ID → Notion ページ URL → 起票日時 → 起票者」の表
   - 失敗ログ（リトライ後も失敗した項目）も記録
7. **後処理**:
   - 全件処理後、`pending-decisions.md` を見直し、起票済みになった項目を削除
   - `aid-validation-runner` を呼ぶ（`<usecase>-architect.md` の DP-DRAFT 残存ゼロ確認）

## 書き込み権限の限定（重要）

- **本スキル以外から Notion DP DB への書き込み禁止**（他スキルは読み取りのみ）
- `aid-plugin-scope-extraction` / `aid-plugin-architecture-design` / `aid-domain-architect-design` は**検出・整理まで**を担当し、起票は本スキルに**必ず**渡す
- これにより：
  - 起票プロセス（3 段階）が一元化される
  - 命名衝突チェックの抜け穴を作らない
  - DP DB の品質が保たれる

## 既知の制約・落とし穴

- **DP-DB のスキーマ変更に追従できない事故**: Notion DB のプロパティが追加・改名されると、本スキルが古いスキーマで書き込んで失敗する。**起票前に必ず `notion-fetch` でスキーマ再確認**。
- **一括起票の事故**: ユーザが「全部 OK」と言っても**1 件ずつ確認**を守る（誤起票時の取り消しコストが高い）。
- **`pending-decisions.md` との同期漏れ**: 起票成功後に `pending-decisions.md` から該当行を削除し忘れると、永遠に未決扱いになる。**起票成功時の sync を手順に強制**。
- **MVP 推奨を AI が勝手に決める事故**: `dp_candidates` に MVP 推奨が書かれていても、起票時に**ユーザに最終確認**を取る。auth の DP-008 のように「既定推奨を置かない」が正解のケースを潰さない。
- **既存 DP 再利用の判定ミス**: 80% 重複ルールは主観的。**迷ったら新規起票せず既存再利用**を推奨（DP-DB の膨張防止）。再利用が苦しいと後で気付いたら、新規起票し直す PR を別途立てる。
- **Notion 書き込み失敗時の中途半端な状態**: ページ作成は成功したが `docs/decision-points.md` 更新が失敗、等。**起票ログを必ず残し**、人間が手動で完了させられる状態にする。
- **WSL2 環境での Notion MCP タイムアウト**: mcp-setup-guide.md のエラーハンドリング 3 パターン（タイムアウト / 認証失敗 / Rate Limit）に準拠。タイムアウト時はローカルキャッシュからの再試行と、`pending-decisions.md` への警告書き込み。

## 判断ポイント（人間判断をスルーさせない）

- **DP-AID-02**（既存 DP 再利用 vs 新規起票）: 80% 重複ルールで判定するが、迷ったらユーザに最終判断を仰ぐ。
- **正規 ID 命名**: `DP-<USECASE>-NNN` 形式の採用は CONV-19 拡張に関わる（要 ADR）。本プラグインでの運用が固まったら `ADR-AID-002`（命名規約拡張）として ADR 化を推奨。
- **「既定推奨を置かない」の起票**: auth の DP-008 型。AI が勝手に MVP 推奨を埋めない。空欄（または「既定推奨なし: 案件のヒアリングで決定」）も valid な起票内容。
- **CONV-19 への影響**: 新ユースケース固有 DP プレフィックスが増えると CONV-19（ID プレフィックス体系）が肥大化する。**プラグイン単位で 5 件超えるなら ADR 化して整理**（DP-AID 議論候補）。

未決は `delivery/dp-registration-log.md` に明示し、`docs/pending-decisions.md` に追記する（T-002 warn_and_document）。

## メタゆえの留意点

- **本スキルは Notion 書き込みを行う数少ない実装系スキル**。慎重さの粒度は他スキルの倍を要求する。
- **本プラグイン自身の DP-AID-01〜05 起票にも使える**（ドッグフード）。Step 2 で `docs/decision-points.md` にドラフトを残してあるので、本スキルが安定したらドッグフード経由で正式起票する。
- **Notion DP DB へのアクセス権**: 本スキルは Notion MCP の書き込みトークンを要求する。CI / 他環境では起票せず、ローカルから人間が起動する運用を既定とする（誤起票防止）。
- **既存 DP との重複判定の AI 寄与**: 単純な文字列マッチでなく**意味的な近さ**（例: 認証の DP-007 と決済の「プロバイダ選択」の構造的類似）を判定する。AI が見落としを補う場面。
- **書き込み権限の TOKEN ローテーション**: 90 日ごとのトークン更新（mcp-setup-guide.md）で本スキルが失敗するタイミングが必ず来る。失敗ログから人間がトークン更新する運用ループを `docs/usage-guide.md` に書く。

## 参考

- `docs/notion-db-catalog.md` — DP-DB の data_source_id と DB プロパティ
- `mcp-setup-guide.md` — Notion MCP のエラーハンドリング 3 パターン
- `plugins/xtone-auth-plugin/docs/decision-points.md` — 同期更新時の Markdown フォーマット
- `xtone-plugin-template/docs/pending-decisions.md` — 未決管理の運用ルール
