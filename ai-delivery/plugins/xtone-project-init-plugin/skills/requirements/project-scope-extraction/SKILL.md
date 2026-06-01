---
name: project-scope-extraction
description: 実案件の初期ヒアリング（ドメイン・規模・制約）から project-scope.json を生成するスキル。requirements フェーズ（/project-init）で、案件を立ち上げる最初の一歩として、ドメインタグ・規模・制約・代表要件を聞き取り、後続のモジュール選定（/project-modules）とスタック選定（project-stack-select）の入力になる project-scope.json を作りたいときに使う。機能モジュール単位の要件定義（各モジュールプラグインの /req-collect）ではなく、案件全体の横断スコープを扱う。
---

# Project Scope Extraction Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

実案件を「これから始める」ときの最初のヒアリングを行い、案件全体の横断スコープ `project-scope.json` を生成する。各モジュール固有の要件定義は各モジュールプラグインの `/req-collect` が担い、本スキルは**案件全体の地図**（どのドメインか・規模・制約・どのモジュールが要りそうか）を作る。

## 抽出チェックリスト

- [ ] **ドメイン**（T-008 ドメインタクソノミーから1つ以上。例: BtoCアプリ / EC・D2C / イベントLP / 業務SaaS …）
- [ ] **規模**（チーム規模・想定ユーザ数・期間など。任意）
- [ ] **制約**（技術・規制・スケジュール・予算。category で分類）
- [ ] **代表的にやりたいこと**（必要モジュールの当たりを付けるためのざっくり要件）
- [ ] **クライアント承認の要否**（approved の初期値は false）

## 入出力（スキーマ）

- 入力: 案件担当者のヒアリング（自然言語）
- 出力: `schemas/v1/project-scope.schema.json` 準拠の `project-scope.json`（`project_name` / `domain` / `scale` / `constraints`。`selected_modules` / `stack` は後続コマンドが埋める）
- スキーマは編集しない（CONV-14）。

## 手順

1. 案件担当者にドメイン・規模・制約・やりたいことをヒアリング（不足・曖昧は質問する）。
2. `project-scope.json` に `project_name` / `domain` / `scale` / `constraints` をマッピング。
3. `selected_modules` / `stack` は空のまま残し、次アクション（`/project-modules`）を案内。
4. 人間判断が要る点は勝手に決めず未決として残す（warn_and_document）。

## 運用方針

- ドメインは T-008 タクソノミーの語彙に寄せる（後続の `/project-modules` が MCS／タクソノミーを引くため）。
- **要件で別指定があれば要件優先**（既定の聞き取り粒度より案件の要望を優先）。

## 判断ポイント（人間判断をスルーさせない）

- ドメイン・規模・制約の確定はクライアントの認識と一致させる（曖昧なまま埋めない）。未確定は `docs/pending-decisions.md` に残す。
- 個人アサイン（client/pm/lead）は判断ポイントではない（捏造しない・TBD 可）。
