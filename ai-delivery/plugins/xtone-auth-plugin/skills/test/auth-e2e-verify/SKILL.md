---
name: auth-e2e-verify
description: 実装フェーズの最後に、`design.yaml` の representative_use_cases / page_access_control / responsibility_split の全ユースケースを **Playwright（または playwright MCP）でブラウザ実機検証**するスキル。Emulator+Docker 既定（B-12）の構成上で実 Firebase 不要・再現可能。「コード書いて終わり」「DP 決定済みのフローが未実装で止まる」事故を防ぎ、未通過 UC があれば pending-decisions に警告として残す。
---

# Auth E2E Verify Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

実装フェーズの **完了条件 / DoD** として、`design.yaml` で定義された全ユースケースを **ブラウザ実機 E2E** で通す。サンプル案件 sample-auth で「コード書いて終わり」になり、**DP-008 で `optional` と決めた MFA / 退会 / パスワード変更が未実装で止まった**問題への対応（B-15）。本スキルが回らない限り実装フェーズは完了扱いにしない。

> **ローカル既定**: 実 Firebase につながず、[`firebase-auth-emulator`](../../implementation/firebase-auth-emulator/SKILL.md)（B-12）で起動した emulator + Docker 環境で完結させる。CI でも emulator スタックを立てて回す（実 Firebase の課金とフレーキーを避ける）。

> **warn_and_document**: 未通過 UC があってもブロックしない。`docs/pending-decisions.md` と `delivery/e2e-verification-report.md` に警告で残し、進行は止めない（T-002）。

## 呼び出しトリガ（B-13 連携）

`implementation-skill-planner` の skill_plan に追加されるトリガ:

- `design.yaml.representative_use_cases` に **1 件以上の UC が定義されている**（実装フェーズの全案件で必須）
- かつ `firebase-auth-setup` / `firebase-auth-frontend` のいずれかが skill_plan に含まれている（auth 系の UC を扱う案件のみ）

未呼び出しのまま実装フェーズが完了に到達した場合は warn_and_document に従い警告（T-002）。

> 本スキルは **skill_plan の最末尾**（setup / frontend / mfa / emulator がすべて呼ばれた後）に置く。`tech-version-check`（B-11、最先頭）と対の構造。

## 入出力

- 入力:
  - `delivery/design.yaml` の `representative_use_cases` / `page_access_control` / `responsibility_split` / `authentication.mfa_requirement` / `local_dev_stack`
  - `delivery/implementation-plan.json` の `skill_plan`（called 状況）
  - 実装済みのアプリ（`docker compose up` で起動可能であること）
- 出力:
  - `delivery/e2e-verification-report.md`（UC ごとの通過 / 未通過、スクショ参照、所要時間、未実装の UC リスト）
  - 未通過 UC があれば `docs/pending-decisions.md` に「未実装 UC: <id> / 理由 / 対応方針」を起票

スキーマは編集しない（CONV-14）。

## 必ず通す UC 集合（design.yaml 経由で確定）

design からマップして、最低でも以下を通す（不該当は skip）:

| カテゴリ | UC 例 | 通すべき条件 |
|---|---|---|
| **基本サインイン** | メール+PW / パスワードレス / OIDC（Google / Apple） | `representative_use_cases` または `responsibility_split` に該当が含まれる場合 |
| **セッション** | 確立（/auth/session）/ Bearer 付与（保護リソース）/ ログアウト | `responsibility_split.backend` に含まれる場合 |
| **アクセス制御 A/B/C** | A: protected-only 未認証で `/login?callback=` リダイレクト、B: public-aware で UI 切替、C: guest-only でログイン済みは default_after_login へ | `page_access_control.pages` の各 path |
| **MFA** | enrollment / challenge（SMS で代替可、TOTP は emulator 非対応） | `authentication.mfa_requirement` ∈ {`required`, `admin_only`, `optional`} |
| **アカウント変更** | パスワード変更 / リセット / メール変更 | iaas で完結＝ クライアント側で Firebase API を直接呼ぶ動作確認 |
| **退会** | DELETE /account → Admin SDK 削除 → 再ログイン拒否 | `responsibility_split.shared` の退会項目 |

> **DP 決定済みなのに未実装な UC** が見つかった場合（例: `mfa_requirement=optional` なのに enrollment 導線が無い）は、 **「DoD 違反」として警告**し、`pending-decisions.md` に残す（中断はしない）。

## 取得手段（優先順）

| 優先 | 手段 | 使い所 |
|---|---|---|
| 1 | **`mcp__playwright__*` MCP** | 開発時の即時 E2E。各 `browser_*` で実ブラウザ操作・スクショ取得・network 検証 |
| 2 | **`@playwright/test` スクリプト**（プロジェクトに `playwright/` ディレクトリを作成） | CI でも回す再現可能なテスト集。MCP 不在環境用 |

> MCP / スクリプトのどちらでも **同じ UC を通す**ことが原則。MCP は対話操作の効率化、スクリプトは再現性と CI が用途。並行運用してよい。

## 環境前提（emulator + docker）

`design.yaml.local_dev_stack` が `emulator_docker`（既定）の前提:

- `docker compose up` で auth-emulator + backend (+ frontend) が起動可能
- `FIREBASE_AUTH_EMULATOR_HOST` / `FIREBASE_PUBLIC_EMULATOR_HOST` が適切に通っている（B-12 参照）
- mock user は emulator UI（`http://localhost:4000`）か REST から作成
- SMS MFA コードは `GET http://localhost:9099/emulator/v1/projects/{project}/verificationCodes` で取得（emulator スキル `references/` 参照）

`cloud_direct` が選ばれた案件は staging Firebase での E2E に切り替え（本スキルのスコープ外、案件 ADR に分担を明記する）。

## 手順

1. **前提確認**: `docker compose up -d`（detached）で emulator + backend が `healthy` になるまで待つ。
2. **UC 列挙**: `design.yaml.representative_use_cases` から通すべき UC リストを生成（上の「必ず通す UC 集合」表で補完）。
3. **MCP で対話 E2E**:
   - `mcp__playwright__browser_navigate` で各ページに遷移
   - `mcp__playwright__browser_fill_form` / `_click` で入力・操作
   - `mcp__playwright__browser_snapshot` / `_take_screenshot` で証跡
   - `mcp__playwright__browser_console_messages` / `_network_requests` で副作用（API 呼び出し）を検証
   - **`alert()` / `confirm()` / `prompt()` の使用を検出したら警告**（B-16 の禁止事項。E2E が固まる）
4. **再現可能スクリプト**（任意）: 同じ UC を `@playwright/test` で `playwright/` 配下に書き、CI に組み込む。
5. **`delivery/e2e-verification-report.md` を生成**: UC ごとの ✓/✗、所要時間、未通過の理由（実装不在 / バグ / DP 未決等）、スクショファイル名を記録。
6. **DoD チェック**: skill_plan の `firebase-auth-setup` / `firebase-auth-frontend` / `firebase-auth-mfa` の `called=true` かつ、本スキル `called=true` で UC が全 PASS なら完了。未通過があれば `pending-decisions.md` に警告を残し、`called=true` にする（中断しない）。

## 出力テンプレ（e2e-verification-report.md）

```markdown
# E2E 検証レポート（auth-e2e-verify / B-15）

- 案件: <project>
- 実施日: <YYYY-MM-DD>
- 環境: docker compose（emulator + backend [+ frontend]）
- design.yaml.local_dev_stack: emulator_docker

## UC サマリ

| UC | カテゴリ | 状態 | 所要時間 | 証跡 | 備考 |
|---|---|---|---|---|---|
| UC-A01 サインイン（メール+PW） | 基本 | ✓ | 0.8s | screenshots/uc-a01.png | — |
| UC-A02 パスワードレス | 基本 | ✓ | 1.2s | — | emulator REST でリンク取得 |
| UC-A05 MFA enrollment | MFA | ✗ | — | — | **未実装**（DP-008=optional だが導線無し）|
| UC-A07 退会 | 退会 | ✓ | 1.5s | screenshots/uc-a07-*.png | 再ログイン拒否確認 |

## アクセス制御 (page_access_control)
- `/login` (C: guest-only): ✓ ログイン済みなら default_after_login へ
- `/settings/profile` (A: protected-only): ✓ 未認証で `/login?callback=` リダイレクト
- `/` (B: public-aware): ✓ 認証状態でコンテンツ切替

## 未通過 UC の警告（pending-decisions に同期）
- UC-A05: 設計で MFA enrollable と決定（DP-008）だが、`/mfa/enroll` ページが未実装。

## DoD
- [x] backend テスト PASS（参考: bin/rails test 結果）
- [ ] ブラウザ実機 UC 全件 PASS（未通過 1 件）
- [x] skill_plan の called 全項目 true
```

## 判断ポイント（人間判断をスルーさせない）

- **未通過 UC の取り扱い**: 「DP 決定済みなのに未実装」は実装漏れ。`pending-decisions.md` に残し、修正後に再実行するか案件として後追いするか人間判断。
- **TOTP MFA の検証先**: emulator は TOTP 非対応のため、staging Firebase で E2E するか・本リリース前に手動確認するかは ADR で決める（emulator スキルと整合）。
- **MCP vs スクリプト**: 案件単発なら MCP のみで足りる場合あり。継続開発するなら `@playwright/test` でレグレッションを残すべき（CI 組込の判断）。

## 関連

- 前提スキル: `firebase-auth-emulator`（B-12）/ `firebase-auth-setup` / `firebase-auth-frontend` / `firebase-auth-mfa` / `tech-version-check`（B-11）
- planner 連携: `implementation-skill-planner` の skill_plan 最末尾エントリ
- 関連方針: B-16（`alert()` / `confirm()` 禁止＝ E2E 固まり防止）
