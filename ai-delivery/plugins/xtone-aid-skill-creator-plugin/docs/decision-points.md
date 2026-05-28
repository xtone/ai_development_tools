# xtone-aid-skill-creator-plugin の判断ポイント一覧（設計資料）

このファイルは xtone-aid-skill-creator-plugin が扱う **人間判断必須ポイント**の一覧。

> **本プラグインは「メタプラグイン」**（プラグインを作るためのプラグイン）なので、ここに記載する DP は、**新規プラグインを起こす過程で発生するメタな判断**を扱う。具体的なドメイン判断（DP-007 認証スタック / DP-008 MFA 等）は対象プラグイン側の `docs/decision-points.md` に記載される。

正は判断ポイントカタログDB（DP-, data_source_id: `64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）。各 DP の `undecided` 連携と `decision_record` 記録は warn_and_document（T-002）で扱う。

> **DP-AID-01〜05 は Notion DP DB に正式起票済み（2026-05-28・B-AID-03 / Issue #200）**。命名は `DP-AID-NN`（ADR-AID-002 確定）。起票記録は [`../delivery/dp-registration-log.md`](../delivery/dp-registration-log.md) を、各 DP の Notion ページ URL は本ファイル下部の各セクションを参照。本ファイルは Notion DP DB と同期更新する（`/aid-dp-register` で同期）。

## DP-AID-01 新規 Skill 追加時の境界判断（既存 Skill 拡張 vs 新規独立 Skill）

- **フェーズ**: メタ設計 → 実装（`aid-plugin-architecture-design` / `aid-skill-authoring` で判定）
- **選択肢**:
  - 既存 Skill を拡張する（責務を追加・節を増やす）
  - 新規独立 Skill を立てる（B-19 の「横断機能」型）
- **判断軸**:
  - **責務分担**（responsibility_split が client / backend / iaas / infrastructure のうち何層にまたがるか）
  - **横断の種類**（`kind`: feature-spanning / environment-spanning / concern-spanning。ADR-AID-003 候補）
  - スキル本体の長さ（200 行超え）と読解コスト
  - 他プラグインでの再利用見込み（横断機能として独立させたほうが流用しやすいか）
- **誤判断リスク**:
  - 既存 Skill を肥大化させる → 1 Skill 内に責務が混在し、後続開発者が「何を担当するスキルか」を見失う
  - むやみに新規 Skill を立てる → スキル数が爆発し、Claude の Skill 選択がブレる（SKL-12 description の精度が下がる）
- **適用条件**: 新規プラグインの設計フェーズと、既存プラグインへの Skill 追加時
- **MVP の既定推奨**: **responsibility_split が 2 層以上（client + backend など）にまたがる場合は新規独立 Skill**。1 層に閉じるなら既存 Skill 拡張。リファレンス: auth プラグインの `firebase-auth-mfa`（feature-spanning: client + backend + iaas）/ `firebase-auth-emulator`（environment-spanning: infrastructure + backend + client）が独立 Skill 化された前例（B-19）。横断の `kind` を併記して後段の SKILL.md テンプレ選択に使う（FINDING-01 / ADR-AID-003 候補）
- **ステータス**: accepted
- **Notion ページ URL**: https://www.notion.so/36eceb782fa381c89247dd2e29578a6e

## DP-AID-02 DP 再利用 vs 新規 DP 起票（80% 重複ルール）

- **フェーズ**: メタ設計 → 実装（`aid-plugin-scope-extraction` / `aid-plugin-architecture-design` / `aid-decision-point-registration` で判定）
- **選択肢**:
  - 既存 DP-XXX をそのまま再利用する（`docs/decision-points.md` に「`DP-NNN` を本プラグインでも採用」と追記のみ・新規起票しない）
  - 既存 DP-XXX をベースに新規 DP を起票する
  - 完全新規 DP を起票する
- **判断軸**:
  - **選択肢の重複率 80%**: 既存 DP と「選択肢」「判断軸」「誤判断リスク」「適用条件」を比較し、80% 以上が一致するなら再利用
  - 適用条件の独立性（既存が「認証案件のみ」など特定領域に閉じている場合、別ドメインで再利用すると意味がブレる）
  - DP DB の肥大化リスク（同じ趣旨の DP が複数存在すると DP-DB のノイズが増える）
- **誤判断リスク**:
  - 安易に新規起票 → DP-DB が肥大化し、再利用候補が見えにくくなる（参照効率の低下）
  - 安易に既存再利用 → ドメイン固有の判断軸を捨て、案件で本来必要な判断が抜け落ちる（例: 認証の DP-007 を決済に流用すると、決済固有の PCI DSS スコープ判定が漏れる）
- **適用条件**: 全プラグイン新規起稿時。`/aid-dp-register` 起動時に必ず適用
- **MVP の既定推奨**: **80% 重複なら既存再利用、迷ったら人間判断**（`/aid-dp-register` の Step B でユーザに 3 択を確認）。新規起票時の命名は `DP-<USECASE>-NN` 形式を推奨（CONV-19 拡張・ADR-AID-002 で確定）
- **ステータス**: accepted
- **Notion ページ URL**: https://www.notion.so/36eceb782fa381ccb600f445a1b2631b

## DP-AID-03 sample-case の選定（カタログから選ぶ vs 新案件追加 PR）

- **フェーズ**: メタ設計 → 実装（`aid-plugin-scope-extraction` / `aid-sample-case-binding` で判定）
- **選択肢**:
  - `xtone-shared-plugin/sample-cases/` のカタログから 1〜3 件選定（既存 7 案件: ec-d2c-app / event-campaign-lp / business-saas / media-content / corporate-site / education-voucher / maas-carshare）
  - カタログにない場合、新案件追加 PR を立てる
  - 既存案件の `*.notes.md` 並置で当該プラグイン固有の追加メモを補う（カタログ本体は編集しない）
- **判断軸**:
  - 当該ユースケースが既存案件のどれかで自然に発生するか
  - 既存案件で「該当度 ⭐」が複数（カタログから複数選定可）
  - クライアントワーク固有制約（共通方針 4）が既存案件で十分カバーされるか
- **誤判断リスク**:
  - 該当ゼロのまま「ec-d2c-app を流用」とすると pilot で**型化対象外の挙動を案件特性で測ってしまう**（例: 決済 in BtoB SaaS 案件は決済機能の主目的が薄く、pilot 価値が下がる）
  - 安易に新案件 PR → カタログが肥大化し、他プラグインからも参照される負荷
- **適用条件**: 全プラグイン新規起稿時の pilot 入力選定
- **MVP の既定推奨**: **まずカタログから 2 件選定**（複数の案件で型の汎用性を確認するため）。該当ゼロ（または該当度 ⭐ が 1 件以下）なら新案件追加 PR を立て、`xtone-shared-plugin/sample-cases/` を更新する責務を本プラグインの起稿担当者が持つ。新案件追加 PR は plugin-developer-guide §1 Step 5 の「カタログ更新は本ガイドの責務」に従う
- **既存プラグインの後追い起稿時のみ**（FINDING-02）: B-21 以前に独自 `sample-inputs/` を持つプラグイン（auth プラグインの `bookclub-app` 等）は `sample_case_legacy` フィールドで経緯を残し、`/aid-sample-case-binding --legacy-only` で symlink を作らず記録のみ行う運用（新規 Rollout プラグインには適用しない）
- **ステータス**: accepted
- **Notion ページ URL**: https://www.notion.so/36eceb782fa38180afb2f4cdcdf6adcc

## DP-AID-04 言語別 references を増やすタイミング（案件で必要時 vs 先回り）

- **フェーズ**: 実装（`aid-references-authoring` で判定）
- **選択肢**:
  - 案件で必要になった時点で `references/<stack>.md` を追加する（遅延追加）
  - 想定スタック（rails / nextjs / hotwire 等）を先回りで揃える（一括追加）
- **判断軸**:
  - 契約（adapter / port のメソッドシグネチャ）が安定しているか
  - 当該 stack で **実機 E2E を通す案件があるか**（テストされていない references は型のドリフトを招く）
  - 他プラグインで同 stack の references がすでにあるか（重複・整合性）
- **誤判断リスク**:
  - 先回り追加 → **未検証のレシピが SKILL.md の表に並ぶ**ことで、他案件担当者が「動く前提」で参照して事故る（auth の B-09 で議論済み・現状は使用案件が出てから追加）
  - 遅延追加 → 案件着手時に references がなく、ゼロからの起稿コストがかかる（ただし型のドリフトリスクよりは小さい）
- **適用条件**: 全プラグインの implementation Skill。requirements / design / test Skill では基本的に references を持たない
- **MVP の既定推奨**: **案件で必要になった時点で追加**（遅延追加）。SKILL.md の「言語別レシピ表」に未作成 stack の行を `⬜ 未作成` で並べておくことで意図は可視化する。先回り追加する場合は `decision_record` に理由必須
- **ステータス**: accepted
- **Notion ページ URL**: https://www.notion.so/36eceb782fa38102a4e5d051515a4d64

## DP-AID-05 domain-architect の責務拡大判断（基盤 designer で十分 vs 特化が必要）

- **フェーズ**: メタ設計（`aid-plugin-architecture-design` で判定）
- **選択肢**:
  - 基盤の `designer` Subagent（SCH-2）だけで設計を回す（`<usecase>-architect.md` を作らない・`--no-domain-architect` で scaffold）
  - ドメイン特化 `<usecase>-architect.md` を新設する（DP 比較表・差し替え可能設計を担保）
- **判断軸**:
  - **比較対象スタックの数**（2 つ以上あればドメイン特化が必要）
  - 主要 DP の複雑度（規制適用判定・冪等性要件など、汎用設計では拾えない判断軸が必要か）
  - 他プラグインで同様の domain-architect が成功しているか（auth プラグインの `authentication-architect` が型）
- **誤判断リスク**:
  - 必要なのに省略 → 主要 DP の比較が浅くなり、後段でスタック交代を迫られる（T-004 本決定が要求する差し替え可能設計の担保ができない）
  - 不要なのに新設 → `<usecase>-architect.md` が雛形のまま放置される（DP 比較表に中身が入らない）リスク
- **適用条件**: 全プラグインの scaffold 前判定
- **MVP の既定推奨**: **2 つ以上の比較対象スタックを持つドメインは特化を作る**。リファレンス: 認証（Firebase Auth / Devise+OmniAuth / Cognito / dAccount / NextAuth.js / Laravel Sanctum）/ 決済（Stripe / GMO / Komoju）/ 通知（SES / Mailgun / Slack / Web push）。比較対象スタックが 1 つしかない（例: 単一 IaaS 固定）なら基盤 designer で足り、`--no-domain-architect` で scaffold する
- **ステータス**: accepted
- **Notion ページ URL**: https://www.notion.so/36eceb782fa3815fa65ce568a1d5ac5e

## 運用

1. 新規プラグイン起稿時に、上記 DP を**メタ設計の判断軸**として当てはめる。
2. 各 DP について、ユーザの判断結果を `delivery/architect-authoring-log.md` / `delivery/dp-registration-log.md` 等に **decision_record（decided_by / decided_at / rationale）**として記録する。
3. 未決のまま実装に進める場合は `docs/pending-decisions.md` に該当 DP を残す（warn_and_document）。
4. ~~本プラグインのドッグフード（Step 11 予定）で運用が安定したら、`/aid-dp-register` で Notion DP DB に DP-AID-01〜05 を正式起票する（仮 ID → 正規 ID）。~~ **完了**: 2026-05-28（B-AID-03 / Issue #200）。仮 ID と正規 ID は同一（`DP-AID-NN`）で、ADR-AID-002 で命名規約が確定。起票記録は [`../delivery/dp-registration-log.md`](../delivery/dp-registration-log.md) を参照。今後の DP 追加時は本リストに draft 行を追加し、`/aid-dp-register` で同期する。

## CONV-19 拡張（命名規約の議論）

本プラグインで新たに導入する DP プレフィックスは `DP-AID-NN`（メタ層）と `DP-<USECASE>-NN`（ユースケース固有層）。これは現行 CONV-19 の `DP-NNN` 形式とは異なる**プレフィックス付き命名**であり、CONV-19 の拡張議論が必要。

- 既存例: `DP-INVITATION-POLICY-001` / `DP-AUDIT-VIEW-001` / `DP-NOTIFY-001`（auth プラグインで先行採用）
- 本プラグイン: `DP-AID-NN` を導入予定
- 想定 Rollout: `DP-PAYMENT-NN` / `DP-NOTIFY-NN`（既存と重複） / `DP-IAC-NN` / `DP-CMS-NN` 等

CONV-19 拡張の合意は別途 ADR 化（`ADR-AID-002` 予定）。本プラグインでの運用が固まったら起票する。

## 関連

- 未決一覧: [`./pending-decisions.md`](./pending-decisions.md)
- 使い方ガイド: [`./usage-guide.md`](./usage-guide.md)
- 本プラグインの作業ガイド: [`../skills/aid-skill-creator-plugin-guide/SKILL.md`](../skills/aid-skill-creator-plugin-guide/SKILL.md)
- リファレンス実装の判断ポイント: [`../../xtone-auth-plugin/docs/decision-points.md`](../../xtone-auth-plugin/docs/decision-points.md)
- 判断ポイントカタログDB（Notion）: data_source_id `64248f5c-b2f5-4c90-8ccb-7f53692b59b2`
