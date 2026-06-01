# references: nx（モノレポ方式レシピ）

> ⬜ **未実装スタブ**。本実装は `/aid-references-new project-monorepo-scaffold nx` で起こす。契約は `../SKILL.md` を参照。

## 対象

大規模・高度なタスクオーケストレーション/キャッシュが必要な案件向け Nx モノレポ。

## 起こすべき内容（実装時に埋める）

- `nx.json` / ワークスペース（apps / libs）
- ルート共有設定（最小核・DP-PINIT-10）: lint / format / tsconfig base / CI 核
- Nx のタスクパイプライン・キャッシュ設定
- バージョンは `tech-version-check` で解決

## templates

`../templates/nx/`（未作成）。
