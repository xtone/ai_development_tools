# scaffold-log — xtone-project-init-plugin（T-051）

骨格生成（generate-plugin.sh / TPL-26）の実行記録。warn_and_document（T-002）。

## 実行コマンド（2026-06-01）

```bash
ai-delivery/scripts/generate-plugin.sh project-init --force --no-domain-architect \
  --description "実案件の初期化（プロジェクトブートストラップ）を担う独立メタプラグイン（T-051）。…/project-* 横断コマンドで提供する。" \
  --author "Xtone" \
  --domains "全ドメイン共通" \
  --modules "なし（横断メタプラグイン・特定 MOD 非依存）"
```

### 引数判断の根拠
- `--no-domain-architect`: T-051 は横断メタプラグインで、特定 MOD のアプリ tech_options に紐づかない。テンプレの domain-architect は tech-stack 比較型（authentication-architect 型）であり不適合。モジュール選定アドバイザ（DP-PINIT-02）は別途 `/aid-skill-new` で専用 Subagent として起稿する想定。
- `--modules "なし（横断メタプラグイン・特定 MOD 非依存）"`: 横断レイヤーゆえ依存 MOD なし。未置換プレースホルダ回避のため明示値を渡した。
- `--force`: 既存ディレクトリ（要件・設計のみの stub）があったため。**事前に `delivery/` と `docs/pending-decisions.md` を退避**し、生成後に復元（成果物消失を防止）。

## 成果物の保全（退避 → 生成 → 復元）
生成前に退避し、生成後に復元した:
- `delivery/requirements.json` / `delivery/design.json` / `delivery/adr/ADR-PINIT-001.md`
- `docs/pending-decisions.md`（DP-PINIT-05 / 06 / 07）

テンプレが生成した `docs/pending-decisions.md`（プレースホルダ版）は、退避していた DP-PINIT 入り版で上書き復元した。

## post-checks（すべて ✅）
- schemas / tech-version-check / implementation-skill-planner の symlink 解決可（CONV-14 / B-17 / B-18）
- 未置換の二重波括弧プレースホルダなし
- `.claude-plugin/plugin.json` 必須フィールド OK（CONV-01）
- `skills/project-init-plugin-guide/SKILL.md` 実体化済み
- `validate-plugin.sh` → ✅ Validation passed（delivery/design.json・requirements.json のスキーマ検証含む / exit 0）

## 次アクション（aid-scaffold 標準フロー）
1. `/aid-skill-creator-design` — スキル/サブエージェント分解を `delivery/plugin-architecture.json` として生成（/project-* 群の設計）
2. `/aid-skill-new <phase> <skill>` — `/project-init` `/project-modules` `/project-scaffold` `/project-load-guide` `/project-status` と モジュール選定アドバイザ Subagent を起稿
3. `/aid-references-new` — 必要なら言語別 references
4. `/aid-dp-register` — DP-PINIT-05/06/07 等を Notion DP DB と同期
5. `/aid-validation-runner` — 検証と pending 追記

## 未決（warn_and_document・継続）
DP-PINIT-05（着手タイミング）/ DP-PINIT-06（project-scope スキーマ配置）/ DP-PINIT-07（横断索引形式）。詳細は `docs/pending-decisions.md` と `delivery/design.json` の `undecided` / `_meta.undecided_recommendations`。
