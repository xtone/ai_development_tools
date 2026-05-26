---
name: implementation-skill-planner
description: 設計成果物（design.yaml）から実装フェーズで呼び出すべきスキルを導出して skill_plan を生成するスキル。実装フェーズの Step 0 として、responsibility_split / page_access_control / authentication.mfa_requirement / local_dev_stack の値に応じて firebase-auth-setup / firebase-auth-frontend / firebase-auth-mfa / firebase-auth-emulator のうち呼ぶべきものを列挙し、implementation-plan.json の skill_plan に反映、`delivery/implementation-skill-plan.md` を出力する。frontend スキル等の呼び出し漏れ防止（B-13 由来）。
---

# Implementation Skill Planner

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

実装フェーズの **Step 0** として、`design.yaml` の決定値から「呼び出すべきスキルの計画」を機械的に導出する。これにより、frontend / emulator / mfa などのスキルが Claude の自己判断で素通りされる事故（B-13 由来。サンプル案件 `~/WebstormProjects/sample-auth/` で `firebase-auth-frontend` がページ構成に反映されないまま実装された）を防ぐ。

> warn_and_document: 本スキルは **計画を出すだけ**でブロックしない。実装フェーズ完了時に `skill_plan[].called` が false のままなら警告するが、進行は止めない（T-002）。

## 入出力（スキーマ）

- 入力: `delivery/design.yaml`（または `design.json`、`design.schema.json` 準拠）
- 出力:
  - `delivery/implementation-plan.json` の **`skill_plan` フィールド**（`implementation-plan.schema.json` 必須）
  - `delivery/implementation-skill-plan.md`（人間向けチェックリスト）

スキーマは編集しない（CONV-14）。

## 導出ルール（design → skill_plan）

design の値から **必ず** 以下を skill_plan に列挙する。

| design のフィールドと値 | 追加するスキル | recipe | owners | required |
|---|---|---|---|---|
| `responsibility_split[].owner` に `backend` or `shared` がある | `firebase-auth-setup` | 採用言語/FW（例: rails / node / laravel） | `[backend]`（shared 含む場合 `[backend, shared]`） | true |
| `responsibility_split[].owner` に `client` or `shared` がある | `firebase-auth-frontend` | hotwire / nextjs / その他 | `[client]`（shared 含む場合 `[client, shared]`） | true |
| `authentication.mfa_requirement` ∈ {`required`, `admin_only`, `optional`} | `firebase-auth-mfa` | rails＋hotwire / rails＋nextjs 等の組合せ | `[backend, client, iaas]` | `required`/`admin_only` は true、`optional` は false（推奨） |
| `local_dev_stack` ∈ {`emulator_docker`, `emulator_host`} **または未指定** | `firebase-auth-emulator` | docker-compose（基本） | `[shared]` | true（既定はローカル開発 = emulator） |
| `page_access_control.pages` が定義されている | `firebase-auth-frontend`（既出なら統合） | 同上 | 同上＋`applies_to` に各 page.path を入れる | true |

> **`local_dev_stack` が未指定**でも emulator スキルを追加するのは、B-12（Emulator+Docker を既定とする方針）に整合させるため。`cloud_direct` を選んだ場合のみ planner は emulator を外し、その判断を `decision_record` に残すよう促す。

## 手順

1. `delivery/design.yaml` を読み込み、`responsibility_split` / `page_access_control` / `authentication.mfa_requirement` / `local_dev_stack` を抽出。
2. 上表のルールで対象スキルを列挙し、重複は `owners` / `applies_to` を統合してまとめる。
3. 採用言語/FW を `architecture.stack` から推定し `recipe` を埋める（複数 FW 採用なら複数エントリ可）。
4. `delivery/implementation-plan.json` に **`skill_plan`** を書き込む（既存があれば差分マージ）。`called` 初期値は `false`。
5. `delivery/implementation-skill-plan.md` を生成: 各スキルにチェックボックス、`trigger` / `owners` / `applies_to` を表で示す。
6. 実装フェーズ中、各スキルの呼び出し完了時にこの md と JSON の `called=true` を更新する（implementer/各スキル側の責務）。
7. フェーズ完了時、`called=false` のままで `required=true` のエントリがあれば **警告**（warn_and_document）し、`docs/pending-decisions.md` に「未呼び出しスキル」を起票する。

## 出力テンプレ（implementation-skill-plan.md）

```markdown
# 実装スキル呼び出しプラン

design.yaml から自動導出（implementation-skill-planner / B-13）。

## 呼び出し計画

| skill | recipe | owners | applies_to | required | called |
|---|---|---|---|---|---|
| firebase-auth-setup | rails | backend, shared | "ID トークン検証", "退会" | true | ☐ |
| firebase-auth-frontend | hotwire | client, shared | /login, /signup, /settings/* | true | ☐ |
| firebase-auth-mfa | rails+hotwire | backend, client, iaas | DP-008 | true | ☐ |
| firebase-auth-emulator | docker-compose | shared | local_dev_stack=emulator_docker（既定） | true | ☐ |

## 未呼び出し警告（フェーズ完了時に更新）

- _(まだありません)_
```

## 判断ポイント（人間判断をスルーさせない）

- **`cloud_direct` を選ぶ場合**: emulator を外す代わりに「ローカルで実 Firebase に直接接続する」根拠を `decision_record` に残させる（XSS 配慮 / コスト / 開発体制）。AI が勝手に既定にしない（T-002）。
- **`recipe` が複数候補**: 採用 FW が固まっていない場合は確定しない。`undecided` に DP を起票し、planner は **両方のエントリ**を skill_plan に並べて警告で残す。
- 未対応の `architecture.stack`（既存レシピが無い）は `firebase-auth-setup` の「新しい言語・FW への展開」に従って `references/<stack>.md` を追加してから skill_plan を確定する。

## 関連

- 受け入れ先: `firebase-auth-setup` / `firebase-auth-frontend` / `firebase-auth-mfa` / `firebase-auth-emulator`（各 SKILL.md 冒頭に「いつ呼ばれるか」のトリガ条件を明記）
- 設計入力: `design.schema.json` の `responsibility_split` / `page_access_control` / `authentication` / `local_dev_stack`
- B-13（実装スキル呼び出し漏れ防止）の中核成果物
