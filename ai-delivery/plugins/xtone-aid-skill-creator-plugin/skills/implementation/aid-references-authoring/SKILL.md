---
name: aid-references-authoring
description: 既存 SKILL.md の言語非依存契約を満たす references/<stack>.md と templates/<stack>/ 雛形を起稿するスキル。プラグイン実装フェーズで、設計済み Skill に新しい言語/FW レシピ（rails / nextjs / hotwire / laravel / fastapi 等）を追加するときに使う。「契約は変えない」「既知の制約を徹底明文化」「コピペ起点として templates/ を併設」の3鉄則を SKILL.md と整合させる。
---

# AID References Authoring Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`aid-skill-authoring`（または既存）で起稿した SKILL.md の **言語非依存契約**を満たす実装手段（言語別レシピ）を `references/<stack>.md` に起稿する。同時に「コピペ起点」として `templates/<stack>/` のファイル雛形も並置する（B-09）。

> 設計方針: SKILL.md は不変・契約は不変。本スキルは「実装手段」の追加のみ担当する。**新しい言語を追加するとき契約を変えるなら別タスク**（契約変更は ADR 化）。

## 入出力

- **入力:**
  - `target_skill_path`（例: `ai-delivery/plugins/xtone-payment-plugin/skills/implementation/payment-stripe-setup`）
  - `stack`（例: `rails` / `nextjs` / `hotwire` / `laravel` / `fastapi` / `node-express` / `django`）
  - （省略可）`reference_recipe_path` — 学習リファレンスにする既存レシピ（既定: `xtone-auth-plugin` の同フェーズ・同 stack のレシピ）
- **出力:**
  - `<target_skill>/references/<stack>.md`（解説 + 契約根拠 + 運用詳細 + 既知の制約）
  - `<target_skill>/templates/<stack>/`（ファイル単位のコピペ雛形・README.md でディレクトリ説明）
  - SKILL.md の「言語別レシピ表」に **1 行追加**（state: ✅）
  - `delivery/references-authoring-log.md`（作成記録）

## references と templates の役割分担（B-09）

| ディレクトリ | 役割 | 粒度 | 読まれる場面 |
|---|---|---|---|
| `references/<stack>.md` | 解説（契約の根拠・運用詳細の why・設定値の意味） | 1 ファイル | 設計を理解したい / 既存実装に組み込む |
| `templates/<stack>/` | ファイル単位のコピペ雛形 | プロジェクトに `cp -R` で配置できる粒度 | 素早く骨格を置きたい / 新規プロジェクト |

両者は**コード片が重複してよい**（読み手が同じ内容に異なる場所で出会う）。ただし**契約に齟齬を生じない**ことが絶対条件。

## 必須セクション（references/<stack>.md の型）

auth プラグインの `references/rails.md` / `references/nextjs.md` / `references/hotwire.md` で確立された型：

1. **冒頭メタ** — 対象（言語/FW + 最新安定版を使う旨）/ 依存ライブラリ / templates への誘導
2. **セットアップ** — Gemfile / package.json / composer.json などインストール
3. **契約の実装** — SKILL.md で定義された adapter / port のインターフェースを当該言語の SDK で満たす具体コード
4. **運用詳細（why）** — 公開鍵キャッシュ / 失効 / 冪等性 等、SKILL.md で言語非依存に書いた運用契約の **言語特有の実装パターン** と理由
5. **既知の制約** — その言語/FW 特有の落とし穴を**徹底明文化**（後続が同じ穴を踏まないため）
6. **テスト** — その言語のテスト書き方（TestAdapter / mock / fixture など）
7. **(任意) 公式 SDK の有無・代替手段** — Ruby に公式 Admin SDK が無く REST で代替、等

## 「既知の制約」の書き方（auth プラグイン現物から学習）

`references/rails.md` には例えば以下が書かれている。**実機で踏んだ罠を必ず残す**：

- 「Zeitwerk 規約: 1 ファイル 1 定数。共通定数は `app/adapters/auth.rb` に集約し、各クラスは個別ファイルへ分割（B-19 / Issue #178）」
- 「Ruby 公式 Admin SDK は無いため Identity Toolkit REST API で代替」
- 「JWT 検証時 `decoded['sub'].empty?` チェック必須（Firebase 検証要件）」

これらは**実装中に踏んだ穴をスキル本文に昇格**したもの。本スキルは新規 references を起稿する際、**学習リファレンスの既知の制約を必ず読み込み**、新 stack で類似の罠がないかをユーザに質問する。

## templates/<stack>/ の構造例（B-09）

実プロジェクトに `cp` で配置できる粒度。例（`firebase-auth-setup/templates/rails/`）：

```
templates/rails/
├── README.md                       # 配置手順・前提
├── Gemfile.snippet                 # add to existing Gemfile
├── dotenv.sample                   # ENV 一覧（コミット不可の本体は別途）
├── db/migrate/00000000000000_add_tokens_valid_after_to_users.rb.template
├── db/seeds.rb.template
├── config/initializers/app_auth.rb
├── app/adapters/auth.rb
├── app/adapters/auth/adapter.rb
├── app/adapters/auth/firebase_adapter.rb
├── app/adapters/auth/test_adapter.rb
└── app/controllers/concerns/authenticatable.rb
```

新 stack ではこの構造を**当該言語/FW の慣習にマッピング**する（例: Next.js なら `app/`, `lib/`, `.env.local.sample`）。

## 手順

1. **入力チェック**:
   - `<target_skill>/SKILL.md` が存在し、`name` / `description` 等の SKL-20 必須を満たしているか
   - `<target_skill>/references/<stack>.md` が**ない**ことを確認（上書きは `--force` 明示確認）
   - SKILL.md に「言語別レシピ表」セクションがあるか（無ければ `aid-skill-authoring` で追加してくるよう促す・warn_and_document）
2. **契約の読取**:
   - SKILL.md の「実装契約（言語非依存）」と「運用契約」を抽出
   - **契約は変えない**。本スキルは契約に手を加えない
3. **学習リファレンスの読取**:
   - `reference_recipe_path` 指定があればそれを Read
   - 無ければ既定: `xtone-auth-plugin/skills/<phase>/<some-skill>/references/<stack>.md`（同 stack の既存実装があれば必ず読む）
   - 既知の制約セクションを必ず読み込み、新 stack で類似の罠を質問
4. **Notion DB 検索**（Notion MCP 必須・任意）:
   - TPL-DB で当該 stack の共通テンプレ実装候補があるか
   - 型化資産インベントリで社内既存資産（同 stack の認証実装等）があるか
5. **`tech-version-check` の前提確認**:
   - `delivery/version-matrix.md` に当該 stack の最新安定版が記録済みか
   - 無ければ「先に `tech-version-check` を実行してください」と促す（warn_and_document）
6. **references/<stack>.md 生成**:
   - 上の 7 セクションを順に埋める
   - 契約を当該言語の SDK で**そのまま満たす**コードを書く（**契約を変えない**）
   - 「既知の制約」は学習リファレンスから流用 + 新 stack 特有を追加
7. **templates/<stack>/ 生成**:
   - ファイル単位の雛形を `cp -R` できる粒度で配置
   - `README.md` に配置手順・前提・ENV キー一覧を書く
   - **コミット禁止項目**（鍵・トークン）は `.sample` 拡張子で雛形化、`.gitignore` に本体を含める旨を README に明記
8. **SKILL.md の言語別レシピ表を更新**:
   - `| <stack> | references/<stack>.md | templates/<stack>/ | ✅ |` を 1 行追加
   - 表が無ければ `aid-skill-authoring` に差し戻し
9. **検証**:
   - `aid-validation-runner` を呼ぶ（特に未置換プレースホルダ・SKILL.md frontmatter 整合）
10. **記録**:
    - `delivery/references-authoring-log.md` に作成記録（skill / stack / 参照したリファレンス / 既知の制約として新規追加した項目）

## 「契約は変えない」の検証

新 references が SKILL.md の契約と整合しているか、本スキルは以下を確認する：

- adapter / port のメソッド名・引数・返り値型が SKILL.md の表と一致しているか
- 運用契約（冪等性・キャッシュ・失効の 2 段階等）が references でも触れられているか
- 契約に無いメソッドを references で勝手に追加していないか（追加したいなら SKILL.md を直す ＝ 別タスク・ADR 化）

齟齬を見つけたら警告し、ユーザに「契約を変える（SKILL.md を直す + 全 stack 影響あり）」か「references を契約に合わせる」のどちらかを選択してもらう（**AI が勝手に決めない**）。

## 既知の制約・落とし穴

- **複数 stack の references が乖離する**: 同じ契約を各 stack で実装するため、初稿時点では揃っていても**運用契約追加時に一斉更新が必要**。SKILL.md を直す PR は全 stack の references を同 PR で更新する運用にする（CONV-XX 追加候補）。
- **公式 SDK が無い言語の扱い**: Ruby の Firebase Admin のように公式 SDK が無い場合は REST API で代替。**REST URL / OAuth2 認証フロー / 冪等性の保証手段を「既知の制約」に詳述**する。
- **テンプレ vs 解説の重複コード**: `references/<stack>.md` と `templates/<stack>/` で同じコードが出てくるのは想定内。**齟齬を生じないこと**だけが絶対条件。コード片が長いときは references から templates へリンクするだけにし、本文の重複を減らす。
- **`templates/<stack>/` の名前空間衝突**: 異なる Skill の templates が同じパス（例: `app/adapters/auth/adapter.rb`）を出すと、案件で `cp -R` の競合が起きる。**Skill 横断で配置パスが被るときは事前に統合 PR**（auth プラグインの adapter 統一が好例）。
- **大型バイナリ・サービスアカウント鍵**: `templates/` に**絶対に置かない**。`.sample` で枠だけ示し、本体は `.gitignore`。本スキルは出力前に対象ディレクトリを grep して `*.json` の中に `"type": "service_account"` が含まれないか確認する。
- **`{` を 2 つ並べる箇所**は要注意。`templates/` 内に Embedded Ruby（ERB の `<%= ... %>`）を使う場合は問題ないが、**generate-plugin.sh 用の二重波括弧プレースホルダ（全角 `｛｛…｝｝` で本文に書く）と混同しないこと**。

## 判断ポイント（人間判断をスルーさせない）

- **DP-AID-04**（references を増やすタイミング）: 案件で必要になった時点で追加が既定。先回り追加は型のドリフトを招く。本スキルは「現案件で使う stack か」をユーザに質問してから生成する（先回り依頼は警告つきで実行）。
- **契約変更の可否**: references を書いていて契約に齟齬が出たら、AI が勝手に SKILL.md を直さない。**ユーザに選択肢を提示**（契約変更＝全 stack 影響、または references を契約に合わせる）。
- **新 stack で既知の制約が見つかった場合**: SKILL.md の言語非依存「既知の制約」へ昇格させるか、references にとどめるかは案件依存。ユーザ確認のうえ `decision_record` に残す。

未決は `docs/pending-decisions.md` に追記する（T-002 warn_and_document）。

## 新しい言語/FW への展開ワークフロー（auth プラグインから抽出）

1. SKILL.md の「言語別レシピ表」に空行 `| <stack> | references/<stack>.md | templates/<stack>/ | ⬜ 未作成 |` を**先に**追加して **意図を可視化**
2. `tech-version-check` で当該 stack の最新安定版を `delivery/version-matrix.md` に記録
3. 本スキル（`/aid-references-new <skill> <stack>`）で `references/<stack>.md` と `templates/<stack>/` を起稿
4. 案件で実機検証（test 系スキルで E2E まで）→ 既知の制約を追加
5. 「言語別レシピ表」の state を ✅ に更新

## メタゆえの留意点

- **本スキルは「実装手段の追加」のみ**。契約変更は別タスク（ADR 化）。
- **学習リファレンスは auth プラグイン固定ではない**: 決済プラグインの `payment-stripe-setup/references/rails.md` が後発で書かれたら、それも学習リファレンスとして使える。`reference_recipe_path` で明示指定する運用。
- **`templates/` の更新は PR 分離が無難**: references の更新と templates の更新は同 PR でもよいが、**templates 単独修正は別 PR** が良い（コード雛形の差分は大きくなりがちで、references の解説との関係をレビューしやすくする）。
- **言語別レシピ表が無い古い Skill** が将来見つかったら、`aid-skill-authoring` で SKILL.md を一度通して表を足してから本スキルを呼ぶ（型遵守の責務は `aid-skill-authoring` 側）。
