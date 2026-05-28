# DP 起票ログ — xtone-aid-skill-creator-plugin

`/aid-dp-register` での Notion 判断ポイントカタログDB（DP-, data_source_id `64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）への起票記録。`aid-decision-point-registration` Skill が更新する。

## 仮 ID → 正規 ID 対応表

本プラグインは「メタプラグイン」のため、ユースケース固有の `DP-<USECASE>-NN` ではなく、メタ層の `DP-AID-NN` 形式（ADR-AID-002 確定）で命名。

| 仮 ID | 正規 ID | タイトル | Notion ページ URL | 起票日時 | 起票者 | ステータス |
|---|---|---|---|---|---|---|
| DP-AID-01 | DP-AID-01 | 新規 Skill 追加時の境界判断（既存 Skill 拡張 vs 新規独立 Skill） | https://www.notion.so/36eceb782fa381c89247dd2e29578a6e | 2026-05-28 | TOYOTA, Yoichi（B-AID-03 / Issue #200） | accepted |
| DP-AID-02 | DP-AID-02 | DP 再利用 vs 新規 DP 起票（80% 重複ルール） | https://www.notion.so/36eceb782fa381ccb600f445a1b2631b | 2026-05-28 | TOYOTA, Yoichi（B-AID-03 / Issue #200） | accepted |
| DP-AID-03 | DP-AID-03 | sample-case の選定（カタログから選ぶ vs 新案件追加 PR） | https://www.notion.so/36eceb782fa38180afb2f4cdcdf6adcc | 2026-05-28 | TOYOTA, Yoichi（B-AID-03 / Issue #200） | accepted |
| DP-AID-04 | DP-AID-04 | 言語別 references を増やすタイミング（案件で必要時 vs 先回り） | https://www.notion.so/36eceb782fa38102a4e5d051515a4d64 | 2026-05-28 | TOYOTA, Yoichi（B-AID-03 / Issue #200） | accepted |
| DP-AID-05 | DP-AID-05 | domain-architect の責務拡大判断（基盤 designer で十分 vs 特化が必要） | https://www.notion.so/36eceb782fa3815fa65ce568a1d5ac5e | 2026-05-28 | TOYOTA, Yoichi（B-AID-03 / Issue #200） | accepted |

## 起票プロセスの記録

### 実施日

2026-05-28

### 実施コマンド

```text
/aid-dp-register ai-delivery/plugins/xtone-aid-skill-creator-plugin
```

### 実施した 3 段階運用

1. **Step A: プレビュー**
   - `docs/decision-points.md` に詳細化済みの DP-AID-01〜05 を 1 つの表に整理して提示
   - **重複チェック**: Notion DP DB に `DP-AID-*` 名のページなし、命名衝突なし。「メタ」「スキル」「プラグイン」「architect」「sample」「reference」など意味的に近い既存 DP も検索したが、構造的に重複する DP はなし（80% 重複ルールに抵触する既存 DP はゼロ）
   - **スキーマ確認**: `notion-fetch` で DP-DB のプロパティを再取得し、判断軸 multi_select の選択肢を確認

2. **Step B: ユーザ確認**
   - 起票方針: 「5 件すべて承認（一括起票）」を選択
   - 関連タスク: `B-AID-03 / PR #197 / ADR-AID-002` を全件に共通記載
   - 命名規約: `DP-AID-NN`（2 桁 0 埋め）形式（ADR-AID-002 確定済み）
   - MVP 推奨: `docs/decision-points.md` 記載の MVP 既定推奨をそのまま採用
   - 適用条件: 各 DP の `docs/decision-points.md` 記載どおり

3. **Step C: 起票**
   - `notion-create-pages` で 1 件ずつ起票（5 件すべて 1 リクエスト 1 ページ）
   - リトライ発動なし（5 件とも 1 回目で成功）
   - 起票 URL を本ファイルに記録

### 後処理

- `docs/decision-points.md`: 各 DP セクションに「Notion ページ URL」と「ステータス: accepted」を追記
- `docs/pending-decisions.md`: 該当行なし（本プラグインで未決一覧に DP-AID-* が登録されていなかった）ため削除不要
- `delivery/dogfood/self/findings.md`: 3 段階運用のドッグフード所見を追記

## 関連

- Issue: [#200](https://github.com/xtone/ai_development_tools/issues/200)（B-AID-03）
- 先行 PR: [#197](https://github.com/xtone/ai_development_tools/pull/197)（DP 詳細化）
- 命名規約: ADR-AID-002
- スキル: [`skills/implementation/aid-decision-point-registration/SKILL.md`](../skills/implementation/aid-decision-point-registration/SKILL.md)
- コマンド: [`commands/aid-dp-register.md`](../commands/aid-dp-register.md)
- 同期更新先: [`docs/decision-points.md`](../docs/decision-points.md)
