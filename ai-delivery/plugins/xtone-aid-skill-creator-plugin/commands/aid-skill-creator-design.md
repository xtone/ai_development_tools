---
description: AIデリバリ用プラグインのメタ設計。aid-skill-creator-architect サブエージェントを起動し、新規ユースケース（T-023〜T-045 Rollout）に対する必要 Skill / Subagent / Command / DP 候補 / 言語別 references 見立て / sample-cases 紐付け案を、Notion 16 DB と xtone-auth-plugin（リファレンス実装）を引きながら提示する。
---

aid-skill-creator-architect サブエージェントを使い、新規 AIデリバリプラグインのメタ設計（プラグインそのものの骨格設計）を進めてください。

1. **入力読取**: `delivery/plugin-scope.json`（`aid-plugin-scope-extraction` Skill の出力）を読む。なければ `/req-collect` で先に scope を抽出するよう促す。
2. **リファレンス読取**: `plugins/xtone-auth-plugin/agents/authentication-architect.md` と `skills/auth-plugin-guide/SKILL.md` を必ず参照（型を写し取る対象）。
3. **Notion 16 DB を引く**（Notion MCP 必須）:
   - SKL-DB（Skill 骨格）/ CONV-DB（規約）/ DP-DB（既存判断ポイント・再利用判定）
   - SCH-DB（Subagent/Command/Hook）/ MCS-DB（モジュール跨ぎ）/ MCP-DB（外部 MCP 必要性）
4. **4 チャネルで出力**（aid-skill-creator-architect.md の出力フォーマットに準拠）:
   - 必要 Skill リスト（フェーズ別・responsibility_split）
   - Subagent / Command 拡張提案
   - DP 候補（既存再利用 + 新規起票候補）
   - 言語別 references 見立て + sample-cases 該当度
5. **横断機能の判定**: client / backend / iaas のうち 2 層以上にまたがるものは独立 Skill 候補に切り出す（B-19）。
6. **DP 比較**: 主要 DP は 2 つ以上のスタックを並べ、MVP 推奨と差し替え可能設計（T-004）の担保を書く。
7. **出力**: `delivery/plugin-architecture.md`（人間レビュー用）+ `delivery/plugin-architecture.json`（後続 Skill の機械可読入力）。
8. **未決の明示**: 判断できない箇所は `undecided` に残し `docs/pending-decisions.md` に追記（warn_and_document）。

> 基盤の汎用設計でよい場合は `/design`（designer）を使う。`/aid-skill-creator-design` は AIデリバリ プラグインそのものの構造設計に特化したメタ設計。
>
> 出力後の次アクション: `/aid-scaffold <usecase>` → `/aid-architect-author <usecase>` → `/aid-skill-new <phase> <skill>` の順で骨格と中身を順次起こす（本プラグインの想定ユースフローは `skills/aid-skill-creator-plugin-guide/SKILL.md` 参照）。
