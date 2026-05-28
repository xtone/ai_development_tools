---
description: 対象プラグインに新 Skill を SKL-12 / SKL-20 準拠で対話的に起稿する。aid-skill-authoring スキルを起動し、xtone-auth-plugin の対応フェーズ Skill を学習リファレンスに、「言語非依存契約 + references 分離」「責務分担表」「要件で別指定があれば要件優先」を強制する。
argument-hint: <phase> <skill_name> [target_plugin_path]
---

`aid-skill-authoring` スキル（`skills/implementation/aid-skill-authoring/SKILL.md`）に従って、対象プラグインに新 Skill を起稿してください。

引数: $ARGUMENTS （形式: `<phase> <skill_name> [target_plugin_path]`）

- `<phase>`: `requirements` / `design` / `implementation` / `test` のいずれか
- `<skill_name>`: kebab-case（例: `payment-stripe-setup`, `payment-design`, `payment-e2e-verify`）
- `<target_plugin_path>`: 省略時は直前の `/aid-scaffold` で生成したプラグイン

1. **入力チェック**: 
   - target プラグインが `/aid-scaffold` 完了済みか
   - `<phase>` が 4 値のいずれか、`<skill_name>` が kebab-case
   - 既存 `<target>/skills/<phase>/<skill_name>/SKILL.md` が**ない**ことを確認（上書きは明示確認）
2. **責務 / responsibility_split の取得**: `delivery/plugin-architecture.json.skills[]` から該当エントリを引き、`responsibility` / `responsibility_split` / `needs_references` / `references_stacks` を取得。
3. **フェーズ別必須セクション**:
   - **requirements**: 抽出チェックリスト + 入出力 + 運用方針 + 判断ポイント
   - **design**: 入出力（requirements → design スキーマ）+ 手順 + 差し替え可能設計 + templates 参照
   - **implementation**: 12 節（呼び出しトリガ / 前提（tech-version-check）/ 入出力 / 言語別レシピ表 / 実装契約 / 運用契約 / 手順 / 新言語展開 / DoD / 既知の制約 / 判断ポイント / responsibility_split 表）
   - **test**: 検証対象 UC + ツール + 通過証跡 + DoD
4. **SKL-12 description の 3 要素強制**: 何を / いつ / どんな条件で。万能記述・100 文字未満は警告して再質問。
5. **横断機能判定（B-19）**: `responsibility_split` が 2 層以上なら独立 Skill 化を強く推奨し、ユーザに確認。
6. **「要件で別指定があれば要件優先」フレーズ強制**: 既定パターンを書く節には必ず添える。
7. **references / templates 雛形**: `needs_references=true` なら `references/` ディレクトリ + 各 `<stack>.md` スタブ。implementation でコピペ起点が要るなら `templates/<stack>/README.md` も。
8. **検証**: `/aid-validation-runner` を呼ぶ。
9. **記録**: `delivery/skill-authoring-log.md` に作成記録。
10. **次アクション**: 言語別 references の本実装は `/aid-references-new <skill_name> <stack>` で行うよう促す。

> 学習リファレンス: `xtone-auth-plugin` の対応フェーズ Skill（`auth-requirements-extraction` / `firebase-auth-design` / `firebase-auth-setup` 等）。
> ブロックしない（warn_and_document, T-002）。
