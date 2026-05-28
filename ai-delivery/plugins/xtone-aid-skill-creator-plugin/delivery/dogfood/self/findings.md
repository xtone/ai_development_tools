# ドッグフード所見 — xtone-aid-skill-creator-plugin（self）

本プラグイン自身を `/aid-dp-register` の対象としたドッグフード（B-AID-03 / Issue #200）の所見。同プラグイン配下の `delivery/dogfood/auth/` が他プラグイン（auth）を素材にしたドッグフードであるのに対し、本ファイルは「**メタプラグインを自分自身に当てる**」セルフドッグフードの記録。

## 実施概要

- **日付**: 2026-05-28
- **対象**: 本プラグイン（`xtone-aid-skill-creator-plugin`）
- **対象 DP**: DP-AID-01〜05（計 5 件・全件新規）
- **実行コマンド**: `/aid-dp-register ai-delivery/plugins/xtone-aid-skill-creator-plugin`
- **使用 Skill**: `aid-decision-point-registration`
- **結果**: 5 件すべて起票成功（リトライ 0 回）。起票 URL は [`../../dp-registration-log.md`](../../dp-registration-log.md) を参照。

## 観察事項（3 段階運用が想定通り動いたか）

### Step A: プレビュー — 想定通り動いた

- 既存 DP との重複チェック（DP-AID-02 80% ルール）を Notion 検索で実施。`DP-AID-*` 名／意味的近隣語（メタ / スキル / プラグイン / architect / sample / reference）で多角的にクエリ。**衝突・80% 重複ともゼロ**で確認できた。
- 候補抽出は `dp_candidates` ではなく `docs/decision-points.md` から直接引いた。本プラグインは「メタプラグイン」のため `plugin-architecture.json` を持たない（外側のプラグインを設計するためのプラグインで、自分自身の architecture.json は対象外）。スキル仕様では `dp_candidates[?reuse == false]` を抽出すると書かれているが、**メタプラグイン自体のドッグフードでは別の経路（`docs/decision-points.md` 直接）が必要**。これは仕様改善候補 → 後段「仕様改善候補」参照。
- スキーマ再確認（`notion-fetch collection://...`）は想定通り。`判断軸` の選択肢が `multi_select` で固定化されている点に最初気づかず、自由テキストで書こうとして書き直した。**SKILL.md に「`判断軸` は固定 multi_select」を明記**しておくと初手で迷わない。

### Step B: ユーザ確認 — 概ね想定通り、改善余地あり

- 「1 件ずつのユーザ確認・一括承認禁止」原則と、Auto Mode の「Bias toward working without stopping for clarifying questions」が衝突した。
- 本ケースでは「`docs/decision-points.md` に詳細が既載」「ADR-AID-002 で命名規約が確定済み」「MVP 推奨も既載」のため、**ユーザに尋ねるべき新情報がほぼなく**、AskUserQuestion を 5 回呼ぶのは過剰だった。
- 妥協案として AskUserQuestion 1 回で「5 件すべて承認 / 1 件ずつ確認 / キャンセル」の 3 択を提示。ユーザは「5 件すべて承認」を選択。**一括承認モード**は実用上の必要があると判明（ただし誤起票防止の慎重さは維持すべき）。
- 「関連タスク」フィールドの値（B-AID-03 / PR #197 / ADR-AID-002）はユーザに確認した。スキル仕様にこの項目への記載指示がなかったので、明示的に確認するのは妥当だった。

### Step C: 起票 — 想定通り動いた

- `notion-create-pages` を 1 件ずつ呼んで 5 件起票。各 1 回目で成功（指数バックオフ発動なし）。
- 起票後の Notion ページ URL は `delivery/dp-registration-log.md` に表形式で記録。
- スキル仕様の「`<usecase>-architect.md` の DP-ID 仮 → 正規置換」は本ケースでは**スキップ**。仮 ID と正規 ID が同一（`DP-AID-01` → `DP-AID-01`）で置換不要なため。これは ADR-AID-002 で「本プラグインの仮 ID はそのまま正規 ID にできる」と前提されているおかげ。
- `pending-decisions.md` の該当行削除は不要だった（本プラグインの未決リストに DP-AID-* が登録されていなかった）。**「未決登録なし → 起票」のパスが想定外**で、スキル手順の「`pending-decisions.md` から該当行を除く」は条件付き（存在すれば削除）と明記すべき。

## 仕様改善候補（別 Issue 化推奨）

優先度の高い順：

### FINDING-SELF-01: メタプラグインのセルフドッグフード経路を明文化

- **問題**: スキル仕様は `dp_candidates`（`plugin-architecture.json` 内）を抽出元と前提しているが、メタプラグイン自身のドッグフードでは `plugin-architecture.json` が存在しない（あるいは自プラグインを設計対象として書き起こされていない）。
- **本ケースの対応**: `docs/decision-points.md` から直接 5 件を読み込み、プレビューと起票を実施。
- **改善案**: SKILL.md の手順 2「候補抽出」に「**メタプラグイン自身のセルフドッグフードでは `docs/decision-points.md` を抽出元にする**」分岐を追加。
- **優先度**: Medium（メタプラグインを他にも作る場合に再発する）

### FINDING-SELF-02: 一括承認モードの正式仕様化

- **問題**: スキル仕様は「1 件ずつ確認・一括承認禁止」と明記しているが、本ケースのように「`docs/decision-points.md` に詳細が既載」「ADR で命名が確定済み」のときには過剰な確認往復が発生する。
- **本ケースの対応**: AskUserQuestion で「5 件すべて承認 / 1 件ずつ確認 / キャンセル」の 3 択を提示し、ユーザに**一括承認モードか個別承認モードか**を選ばせた。
- **改善案**: SKILL.md の Step B に「**事前承認モード**」を追加し、入力ファイル（`docs/decision-points.md`）に「ステータス: ready-to-register」が明示されている場合は一括承認を許容する。それ以外は従来通り 1 件ずつ確認。
- **優先度**: High（次回以降の `/aid-dp-register` 実行で必ず再発する。実用性の改善幅が大きい）

### FINDING-SELF-03: 判断軸 multi_select の固定選択肢を SKILL.md に明記

- **問題**: Notion DP DB の `判断軸` フィールドは `multi_select` で 22 個の選択肢が固定。スキル仕様では「`notion-fetch` でスキーマ再確認」とあるが、選択肢の制約（多すぎず少なすぎず）の意図が SKILL.md からは読めない。
- **本ケースの対応**: スキーマを取得後、22 個の選択肢から各 DP の本質を捉える 3 件前後を選んで multi_select に格納。
- **改善案**: SKILL.md の「Notion DP DB のスキーマ」節に「**`判断軸` は 22 個の固定選択肢から 1〜4 件選ぶ**」を明記し、典型的なマッピング例（例: 「保守性」「ドキュメント品質」「品質」が頻出）を併記。
- **優先度**: Low（毎回 `notion-fetch` でスキーマ再取得すれば運用可能）

### FINDING-SELF-04: `pending-decisions.md` 削除手順の条件化

- **問題**: SKILL.md の手順 7「`pending-decisions.md` から該当行を除く」は、該当行が無い場合の指示が無い。本ケースでは未決リストに DP-AID-* が登録されていなかったので、削除はスキップした。
- **改善案**: 「**該当行があれば削除、無ければスキップ（未決登録忘れの可能性に対する警告のみ）**」と条件化を明記。
- **優先度**: Low（読み手の常識で対応可能だが、明示しておくと安全）

### FINDING-SELF-05: メタプラグインの「自プラグインへの注釈」を起票時の本文に含める運用

- **問題**: 本プラグインの DP は「メタプラグイン固有」であり、案件プラグインの DP（決済 / 認証など）とは異なる層であることを Notion 上で識別したい。
- **本ケースの対応**: 「メモ」フィールドと本文に **「xtone-aid-skill-creator-plugin（メタプラグイン）固有の判断ポイント」** と注記。ただし統一フォーマットではない。
- **改善案**: SKILL.md に「**メタプラグインからの起票時は本文冒頭に「所属プラグイン」「層（メタ / ドメイン）」を統一フォーマットで記載する**」セクションを追加。
- **優先度**: Low（運用が成熟したら一斉に揃える程度の作業）

## まとめ

- **3 段階運用は想定通り機能した**。Notion DP DB への書き込みが**1 件ずつ 1 回目で成功**しており、スキルの堅牢性は確認できた。
- **仕様改善候補は計 5 件**（High 1 / Medium 1 / Low 3）。とくに FINDING-SELF-02（一括承認モード）は次の `/aid-dp-register` 実行で必ず再発するので、別 Issue 化して仕様化する価値が高い。
- 本所見は `aid-decision-point-registration` Skill の改善インプットとして、次のメンテで参照する。

## 関連

- 起票ログ: [`../../dp-registration-log.md`](../../dp-registration-log.md)
- スキル本体: [`../../../skills/implementation/aid-decision-point-registration/SKILL.md`](../../../skills/implementation/aid-decision-point-registration/SKILL.md)
- コマンド: [`../../../commands/aid-dp-register.md`](../../../commands/aid-dp-register.md)
- DP 一覧（同期済み）: [`../../../docs/decision-points.md`](../../../docs/decision-points.md)
- Issue: [#200](https://github.com/xtone/ai_development_tools/issues/200)（B-AID-03）
- 命名規約: ADR-AID-002
- 他プラグイン素材のドッグフード: [`../auth/findings.md`](../auth/findings.md)
