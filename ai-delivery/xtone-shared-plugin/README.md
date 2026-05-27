# xtone-shared-plugin

各プラグイン（`plugins/xtone-<usecase>-plugin/`）が共有するアセットの **Single Source of Truth**（CONV-14）。プラグインからは **symlink で参照**され、コピーはしない。

## 提供物

| カテゴリ | パス | 内容 |
|---|---|---|
| スキーマ | `schemas/v1/` | 5 フェーズの I/O 契約（requirements / design / implementation-plan / modules / risks / decision-point / module / quality-gate-rules） |
| 横断スキル | `skills/implementation/tech-version-check/` | 採用言語・FW・主要ライブラリの最新安定版と相互互換性を実装前に取得・記録するスキル（B-11 で起票 → B-17 で横断化） |
| 横断スキル | `skills/implementation/implementation-skill-planner/` | `design.yaml` から「実装フェーズで呼び出すべきスキル」を導出して `implementation-plan.json.skill_plan` を生成する Step 0 スキル（B-13 で起票 → B-18 で横断化） |

## 参照方式

各プラグインから symlink で参照する。例: `plugins/xtone-auth-plugin/`:

```
schemas             -> ../../xtone-shared-plugin/schemas/v1
skills/implementation/tech-version-check
                    -> ../../../../xtone-shared-plugin/skills/implementation/tech-version-check
skills/implementation/implementation-skill-planner
                    -> ../../../../xtone-shared-plugin/skills/implementation/implementation-skill-planner
```

`xtone-plugin-template/` も同じ構造で symlink を持つ。新規プラグイン生成時の symlink 再作成手順は [`../xtone-plugin-template/README.md`](../xtone-plugin-template/README.md) を参照。

## 横断スキルの追加方針

複数プラグインで共通利用する想定のスキルは、最初から本ディレクトリに置く。**特定プラグイン内に置いてから後で横断化** は移管コストが高い（B-17 の経緯）。判断に迷う場合は **最初は shared に置き、必要なら個別プラグインで上書き** する方が安全。

## 関連

- `../CLAUDE.md` — ai-delivery 全体の作業ガイド（鉄則 4: スキーマは 1 箇所だけ = CONV-14）
- `../xtone-plugin-template/README.md` — 新規プラグイン作成手順
