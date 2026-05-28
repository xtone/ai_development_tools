---
name: aid-domain-architect-design
description: 対象プラグインの agents/<usecase>-architect.md を中身ごと埋めるスキル。authentication-architect.md を学習リファレンスに「DP 比較表 / MVP 推奨 / 差し替え可能設計の担保 / 案件固有 DP の選択肢と判断軸」を 2 つ以上のスタックで具体化する。プラグイン設計フェーズで、generate-plugin.sh が出した雛形（二重波括弧プレースホルダ ｛｛domain｝｝ 等の残存・DP-XXX 雛形）を案件に固有化したいときに使う。新規 DP の起票そのものは /aid-dp-register に渡す（本スキルは検出までを担う）。
---

# AID Domain Architect Design Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`generate-plugin.sh` が `xtone-plugin-template/agents/domain-architect.md.template` から実体化した `agents/<usecase>-architect.md` は、二重波括弧プレースホルダ `｛｛usecase｝｝` / `｛｛domain｝｝`（本文では全角で表記して grep 自己マッチ回避）が置換されているだけで **DP 比較表は雛形のまま**。本スキルは `authentication-architect.md` を学習リファレンスに、`plugin-architecture.json` の `dp_candidates` / `subagents` / `responsibility_split` を引き当てて中身を埋める。

> 設計方針: 「容器」は generate-plugin.sh + aid-plugin-scaffold が作る。「型」は本スキル（authentication-architect.md を写し取る）。「中身の具体化」は本スキル + 案件担当者の対話で行う。DP の Notion 起票は `/aid-dp-register`（=`aid-decision-point-registration`）に分離する。

## 入出力

- **入力:**
  - `target_plugin_path`（例: `ai-delivery/plugins/xtone-payment-plugin`）
  - `target_plugin_path/agents/<usecase>-architect.md`（generate-plugin.sh が実体化したファイル・雛形のまま）
  - `target_plugin_path/delivery/plugin-architecture.json`（`aid-plugin-architecture-design` の出力・必須）
  - 学習リファレンス: `plugins/xtone-auth-plugin/agents/authentication-architect.md`（固定）
- **出力:**
  - `target_plugin_path/agents/<usecase>-architect.md`（DP 比較表・MVP 推奨・差し替え可能設計・適用条件まで埋めた状態）
  - 検出した新規 DP は `plugin-architecture.json.dp_candidates` を **更新**（reuse: false の項目に MVP 推奨を追記）
  - `target_plugin_path/delivery/architect-authoring-log.md`（作成記録）

## 必須セクション（authentication-architect.md から抽出した型）

埋めるべきセクションは以下。auth プラグインの `authentication-architect.md` を**節構造ごと写し取る**：

1. **frontmatter**: `name` / `description`（3 要素）/ `tools` / `model`
   - `description` は SKL-12 準拠（domain 名と参照する DP-XXX を含む）
2. **冒頭口上**: 「あなたは Xtone AIデリバリシステムの `<domain>` 設計スペシャリストです」「基盤の designer（SCH-2）を `<domain>` ドメインに特化させた立場で」「最終決定は人間 — あなたは決めません」
3. **役割**: 入力 `requirements.schema.json` の `<domain>` 関連 → 出力 `design.schema.json`（`tech_stack` / `decision_record` / `undecided`）
4. **入出力**: schemas/ 参照、必要に応じ ADR
5. **検討する判断ポイント**（**核心セクション・必ず 2 つ以上のスタック比較**）:
   - **主要 DP（スタック選択）**: 選択肢 / 判断軸 / 誤判断リスク / MVP 推奨 / 差し替え可能設計の担保
   - **案件固有の DP（任意・複数可）**: 既定推奨を置くか / 置かないか の判断
   - **案件条件で適用判定する規約等（任意）**: 適用条件の明示
6. **手順**: requirements 洗い出し → DP 比較表 → 案件固有 DP の判定 → decision_record / undecided 記録 → 重要決定は ADR
7. **IaaS / プロバイダ差し替え可能設計（T-004 本決定）**: 抽象化レイヤー越しに呼ぶ、SDK 直叩き禁止、差し替え手順を比較表に
8. **warn_and_document（T-002 本決定）**: 未決があっても設計は生成、ブロックしない

## 主要 DP の比較表テンプレ（必須・2 スタック以上）

雛形セクション `### DP-XXX <domain>スタック選択` を以下の構造で埋める：

```markdown
### <DP-ID> <domain> スタック選択
選択肢: **<推奨候補>** / <代替候補1> / <代替候補2> ...
- 判断軸: セキュリティリスク / クライアント規制 / ユーザ規模 / コスト / <案件固有軸>
- 誤判断リスク: <具体的に何が起きるか・auth の DP-007「クライアント規制に不適合で後段スタック交代」の粒度>
- **MVP 推奨**: <推奨候補>（理由を 1〜2 文）。ただし **IaaS / プロバイダ差し替え可能な設計**（処理を抽象化レイヤー越しに呼ぶ）を必ず維持する。少なくとも 1 つの代替（例: <代替候補1>）を比較表に含め、差し替え手順の見通しを示す。
```

> 主要 DP は **必ず 2 つ以上のスタックを並べる**（T-004 本決定の根幹）。1 つしか書いていなければ警告して再生成。

## 案件固有 DP / 適用条件 DP のテンプレ

既定推奨を**置くか / 置かないか**は案件次第。authentication-architect.md の DP-008（MFA・既定推奨を置かない）と DP-015（dAccount・適用条件を明示）が学習リファレンス：

```markdown
### <DP-ID> <案件固有の方針>
選択肢: <選択肢1> / <選択肢2> / <選択肢3> ...
- 判断軸: <ヒアリング軸>
- 誤判断リスク: <誤った判断が招く具体的リスク>
- **既定の推奨は置かない**（または 置く場合は理由とともに記載）。案件の <domain> 要件と規制をヒアリングし、人間に決めてもらう。決まるまで `undecided` に <DP-ID> を残す。
```

```markdown
### <DP-ID> <案件条件で適用判定する規約等>
選択肢: <全面遵守> / <コア部分のみ> / <事前協議> / <独自規約>
- 判断軸: クライアント規制 / セキュリティリスク / スケジュール
- 誤判断リスク: 検収不合格・規約違反・過剰適用による開発コスト肥大
- **適用条件**: <特定の案件種別>のときのみ。非該当案件ではスコープ外として明示する。
```

## 手順

1. **入力チェック**:
   - `target_plugin_path/agents/<usecase>-architect.md` が存在（generate-plugin.sh で実体化済み）
   - `delivery/plugin-architecture.json` が存在（`aid-plugin-architecture-design` の出力）
   - 学習リファレンス `xtone-auth-plugin/agents/authentication-architect.md` を必ず Read
2. **プレースホルダ残存チェック**:
   - 二重波括弧プレースホルダ（`{` を 2 つ並べた表記）が `<usecase>-architect.md` に残っていないか確認
   - `{usecase}` / `{domain}` 未置換なら警告し、`generate-plugin.sh --domain ...` の再実行を促す（warn_and_document）
   - `DP-XXX` 雛形が残っていれば本スキルが埋める対象
3. **DP 候補の取り込み**:
   - `plugin-architecture.json.dp_candidates` から `reuse: false` の項目（新規候補）を主要 DP・案件固有 DP に振り分け
   - `reuse: true` の項目（既存 DP 再利用）は `<DP-007 をユースケースで再解釈>` のように引用
4. **主要 DP（スタック選択）の比較表生成**:
   - `stack_candidates` から 2 つ以上を取り出し、上テンプレで比較表を生成
   - **2 つ未満なら警告**して代替候補をユーザに質問（AI が勝手に増やさない）
   - **差し替え可能設計の担保**（adapter / port 名・差し替え手順 1〜2 文）を必ず書く
5. **案件固有 DP / 適用条件 DP の生成**:
   - `dp_candidates` の残りを上テンプレで埋める
   - 既定推奨を**置くか / 置かないか**は **AI が勝手に決めない**。ユーザに質問
   - 適用条件 DP（auth の DP-015 型）はユースケースに該当しなければ「適用条件: なし（本プラグインでは不採用）」と明示
6. **frontmatter description の SKL-12 化**:
   - 雛形は「`<domain>` 設計のスペシャリスト」のままなので、**当該ユースケースに固有の DP-ID を含めた 3 要素 description** に書き換える
   - 例（auth から学習）: 「Firebase Auth / Devise+OmniAuth / Cognito / dAccount を比較し、MVP は Firebase Auth を推奨（最終決定は人間）。DP-007/008/015 を参照。/auth-design から起動」
7. **検証**:
   - `aid-validation-runner` を呼ぶ（未置換プレースホルダ・frontmatter 整合）
   - **二重波括弧プレースホルダの残存が 0** を確認
   - DP-XXX 雛形の残存が 0 を確認
8. **記録**:
   - `delivery/architect-authoring-log.md` に「何を埋めたか・参照した DP・MVP 推奨の根拠」を残す
9. **次アクション**:
   - 新規 DP（`DP-<USECASE>-DRAFT-NN`）は `/aid-dp-register` で Notion 起票するよう促す
   - 重要決定があれば `/decide` で `docs/adr/ADR-<plugin>-NNN.md` を起票するよう促す

## 「差し替え可能設計」の具体記述（T-004 本決定）

`authentication-architect.md` の DP-007 では「**IaaS 差し替え可能な設計**（認証処理を抽象化レイヤー越しに呼ぶ）」と明記し、`AuthAdapter` 層をリファレンス実装で示している。本スキルが生成する `<usecase>-architect.md` でも、同レベルの具体性が必要：

| ドメイン例 | adapter 層の名称 | 差し替え手順の見通し |
|---|---|---|
| 決済 | `PaymentAdapter`（charge / refund / webhook_verify） | Stripe → GMO 移行は `StripeAdapter` を `GmoAdapter` に差し替え、webhook 検証ロジックを再実装。決済状態モデルは共通 |
| 通知 | `NotificationAdapter`（send_email / send_push / send_slack） | SES → Mailgun 移行は `SesAdapter` を `MailgunAdapter` に差し替え、テンプレ管理側は不変 |
| 位置情報 | `GeocodingAdapter`（geocode / reverse_geocode / distance） | Google Maps → Mapbox 移行はキー差し替え + adapter 実装の差し替え |

抽象は**メソッドシグネチャまで**書く。「抽象化レイヤーを設ける」だけの記述は不十分（auth プラグインの authentication-architect.md より低品質）。

## 既知の制約・落とし穴

- **DP-XXX 雛形を残したまま完了扱いにする事故**: generate-plugin.sh の出力には `DP-XXX` リテラルが複数箇所残る。本スキルは出力後に `grep 'DP-XXX' agents/<usecase>-architect.md` を実行して残存ゼロを確認する。
- **「差し替え可能設計」の抽象化が抽象すぎる事故**: 「抽象化レイヤーを設ける」「将来差し替え可能にする」だけでは T-004 本決定の担保にならない。**adapter / port のメソッドシグネチャまで書く**（auth プラグインを下回らない粒度）。
- **比較対象スタックが 1 つしかない事故**: MVP 推奨だけ書いて代替候補を書かないと、後段で「やっぱり別の選択肢の方が良かった」が起きる。**最低 2 つ**を強制する。
- **「既定推奨を置くか / 置かないか」を AI が勝手に決める事故**: 案件固有 DP（auth の DP-008 のような）は既定推奨を置かないのが正解のことが多い。AI が「MVP 推奨: ...」を勝手に書くと案件担当者の判断を奪う。**ユーザに毎回質問**。
- **学習リファレンスの DP-007 / 008 / 015 をそのままコピーする事故**: 新ユースケースに固有の判断軸を作らず authentication の DP を流用すると、案件で本来必要な判断が抜け落ちる。**`authentication-architect.md` は構造の手本であって内容は流用しない**。
- **frontmatter description の SKL-12 違反**: 雛形のままだと 3 要素が薄い。ユースケース固有の DP-ID とコマンド名（`/<usecase>-design`）を必ず含める。

## 判断ポイント（人間判断をスルーさせない）

- **主要 DP の MVP 推奨**: 2 つ以上のスタック比較の上で、AI は推奨候補を提示するが**最終決定は人間**（authentication-architect.md と同じ流儀）。
- **案件固有 DP の既定推奨**: 既定推奨を置くか / 置かないかは AI が決めない。ユーザに質問し、回答を `decision_record` に残す（**置かない**選択も明示的な判断）。
- **DP-AID-05**: そもそも `<usecase>-architect` Subagent が必要かは `aid-plugin-architecture-design` で判定済みのはず。本スキルが起動した時点で「必要」前提。
- **適用条件 DP の対象判定**: 「本プラグインで採用する / しない」は案件確認のうえユーザ判断。「採用しない」場合は `適用条件: なし（本プラグインでは不採用）` と**明示的に書く**（無記載で済ませない）。

未決は `delivery/architect-authoring-log.md` に明示し、`docs/pending-decisions.md` に追記する（T-002 warn_and_document）。

## メタゆえの留意点

- **本スキルは「authentication-architect.md の型を写し取る」専用**。auth の中身（DP-007/008/015）を新ユースケースで使い回さない。
- **`authentication-architect.md` 自体は本スキルを通っていない**（B-19 以前に手で書かれた）。リファレンスとしてのみ参照し、新規 `<usecase>-architect.md` は必ず本スキル経由で起こす（容器の品質を担保）。
- **本プラグイン自身の `aid-skill-creator-architect.md` は Step 3 で手書き済み**。本スキルの起源・学習対象としても機能する（auth と aid の 2 例を持つことで型が安定する）。
- **scaffold 直後（`/aid-scaffold` 完了直後）に本スキルを呼ぶのが基本**。間が空くと `｛｛domain｝｝` 等の二重波括弧プレースホルダがコミットされる事故が起きやすい。
- **DP の Notion 起票は本スキルの責務ではない**。検出・整理までを本スキルが行い、起票は `/aid-dp-register` に委譲（書き込み権限の集約）。

## リファレンス実装（必読）

- `plugins/xtone-auth-plugin/agents/authentication-architect.md` — 構造の手本
- `plugins/xtone-auth-plugin/docs/decision-points.md` — DP の項目構造（フェーズ / 選択肢 / 判断軸 / 誤判断リスク / 適用条件 / MVP 既定推奨）
- `plugins/xtone-aid-skill-creator-plugin/agents/aid-skill-creator-architect.md` — メタ層での写し取り例（Step 3）
