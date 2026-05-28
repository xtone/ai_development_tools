---
description: 対象 Skill に新しい言語別 references レシピ（rails / nextjs / hotwire / laravel / fastapi 等）と templates 雛形を起稿する。aid-references-authoring スキルを起動し、「契約は変えない」「既知の制約を徹底明文化」を絶対条件にする。
argument-hint: <skill_name> <stack> [target_plugin_path]
---

`aid-references-authoring` スキル（`skills/implementation/aid-references-authoring/SKILL.md`）に従って、対象 Skill に新しい言語別レシピを起稿してください。

引数: $ARGUMENTS （形式: `<skill_name> <stack> [target_plugin_path]`）

- `<skill_name>`: 対象 Skill 名（例: `payment-stripe-setup`）
- `<stack>`: 言語/FW（例: `rails` / `nextjs` / `hotwire` / `laravel` / `fastapi` / `node-express` / `django`）
- `<target_plugin_path>`: 省略時は直前の `/aid-scaffold` で生成したプラグイン

1. **入力チェック**:
   - `<target>/skills/*/<skill_name>/SKILL.md` が存在し、SKL-20 必須を満たすか
   - 既存 `references/<stack>.md` が**ない**ことを確認（上書きは明示確認）
   - SKILL.md に「言語別レシピ表」セクションがあるか（無ければ `/aid-skill-new` で追加するよう促す）
2. **契約の読取（不変）**: SKILL.md の「実装契約（言語非依存）」と「運用契約」を抽出。**本コマンドは契約に手を加えない**（契約変更は別タスク・ADR 化）。
3. **学習リファレンス読取**: 既定 `plugins/xtone-auth-plugin/skills/<phase>/<some-skill>/references/<stack>.md`（同 stack の既存があれば必ず読む）。「既知の制約」セクションを必ず読み、新 stack で類似の罠を質問。
4. **tech-version-check の前提**: `delivery/version-matrix.md` に当該 stack の最新安定版が記録済みか確認。無ければ「先に `tech-version-check` を実行」と促す。
5. **references/<stack>.md 生成**: 7 セクション（冒頭メタ / セットアップ / 契約の実装 / 運用詳細 / 既知の制約 / テスト / 公式 SDK の有無）を順に埋める。**契約は変えない**。
6. **templates/<stack>/ 生成**: ファイル単位の `cp -R` 可能な雛形 + README.md。コミット禁止項目は `.sample` 拡張子・README に `.gitignore` 案内。
7. **SKILL.md の言語別レシピ表更新**: `| <stack> | references/<stack>.md | templates/<stack>/ | ✅ |` を 1 行追加。
8. **「契約は変えない」検証**: adapter のメソッドシグネチャ・運用契約の整合確認。齟齬があれば「契約を変える / references を契約に合わせる」をユーザ選択（AI が勝手に決めない）。
9. **検証**: `/aid-validation-runner` を呼ぶ（特に未置換二重波括弧プレースホルダ・SKILL.md frontmatter 整合）。
10. **記録**: `delivery/references-authoring-log.md` に作成記録（skill / stack / 参照したリファレンス / 既知の制約として新規追加した項目）。

> DP-AID-04（references を増やすタイミング）: 案件で必要になった時点で追加が既定。先回り追加は型のドリフトを招くため、現案件で使う stack かを必ず確認。
> ブロックしない（warn_and_document, T-002）。
