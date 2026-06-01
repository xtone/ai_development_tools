# references: turborepo-pnpm（モノレポ方式レシピ）

> ⬜ **未実装スタブ**。本実装は `/aid-references-new project-monorepo-scaffold turborepo-pnpm` で起こす（DP-AID-04: 案件で必要になった時点）。契約は `../SKILL.md` を参照（本ファイルは契約を変えない）。

## 対象

JS 重心の案件（複数 Next.js アプリ・共有パッケージ）向け pnpm workspaces + Turborepo 構成。

## 起こすべき内容（実装時に埋める）

- `pnpm-workspace.yaml`（`apps/*` / `packages/*`）
- `turbo.json`（pipeline: build / lint / test / dev）
- ルート共有設定（最小核・DP-PINIT-10）: `eslint` / `prettier` / `tsconfig.base.json` / `.editorconfig` / `.gitignore` / CI ワークフロー核
- バージョンは `tech-version-check` で解決（固定しない）

## templates

`../templates/turborepo-pnpm/` に雛形を置く（未作成）。
