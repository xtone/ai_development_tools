---
description: 対象プラグインの <usecase>-architect.md を中身ごと埋める。aid-domain-architect-design スキルを起動し、authentication-architect.md を学習リファレンスに DP 比較表 / MVP 推奨 / 差し替え可能設計の担保を具体化する。
argument-hint: <usecase> [target_plugin_path]
---

`aid-domain-architect-design` スキル（`skills/design/aid-domain-architect-design/SKILL.md`）に従って、対象プラグインの domain-architect Subagent を中身ごと埋めてください。

引数: $ARGUMENTS （形式: `<usecase> [target_plugin_path]`、`target_plugin_path` 省略時は `ai-delivery/plugins/xtone-<usecase>-plugin`）

1. **前提**: 
   - `<target_plugin>/agents/<usecase>-architect.md` が存在（`/aid-scaffold` 完了済み）
   - `<target_plugin>/delivery/plugin-architecture.json` が存在（`/aid-skill-creator-design` 完了済み）
   - 学習リファレンス `plugins/xtone-auth-plugin/agents/authentication-architect.md` を必ず Read
2. **プレースホルダ残存チェック**: 二重波括弧プレースホルダ（`｛｛usecase｝｝` / `｛｛domain｝｝`）が未置換のまま残っていれば警告し、`generate-plugin.sh --domain ...` 再実行を促す。
3. **DP 候補の取り込み**: `plugin-architecture.json.dp_candidates` から主要 DP・案件固有 DP・適用条件 DP に振り分け。
4. **主要 DP の比較表生成**: `stack_candidates` から **2 つ以上**を取り出し、選択肢 / 判断軸 / 誤判断リスク / MVP 推奨 / 差し替え可能設計の担保（adapter のメソッドシグネチャまで）を埋める。
5. **案件固有 DP**: 既定推奨を**置くか / 置かないか**は AI が決めずユーザに質問。
6. **frontmatter description の SKL-12 化**: 当該ユースケース固有の DP-ID とコマンド名（`/<usecase>-design`）を含めた 3 要素 description に書き換える。
7. **検証**: `/aid-validation-runner` を呼び、`DP-XXX` 雛形・二重波括弧プレースホルダの残存が 0 を確認。
8. **記録**: `delivery/architect-authoring-log.md` に「何を埋めたか・参照した DP・MVP 推奨の根拠」を残す。
9. **次アクション**: 新規 DP（`DP-<USECASE>-DRAFT-NN`）は `/aid-dp-register` で Notion 起票するよう促す。

> auth プラグインの `authentication-architect.md` は**構造の手本**であって**内容は流用しない**（DP-007/008/015 をそのままコピーしない）。
> ブロックしない（warn_and_document, T-002）。
