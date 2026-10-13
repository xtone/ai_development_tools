# ナレッジカード 2026-W43（10/19〜10/25）

<!-- 直したい箇所はそのまま書き換えてください。カードを出さないときは節ごと消すか、状態を dropped にします。id の無い ### 節を足すと新しいカードになります。根拠は「- 種類 `参照`: 抜粋」の形で、抜粋の 2 行目以降は 2 字下げます。 -->

## P1 この週、どのプロジェクトで何を進めたか（機能領域・フェーズ・状態）

### ai_development_tools: ナレッジカードのスキルを実装し、PR をレビュー中

- id: 2026-W43/P1/y.toyota/001
- 状態: draft
- 極性: fact / 確度: observed / 公開範囲: internal
- プロジェクト: ai_development_tools
- タグ: skill

設計書を書き、抽出・検査・提出のスクリプトを実装した。PR を作りレビューを受けている。

**根拠**

- commit `<session_id>@2026-10-20T03:00+00:00`: feat(knowledge-sharing): knowledge-cards を追加
- pr `<session_id>@2026-10-20T05:10+00:00`: feat(knowledge-sharing): 週次のナレッジカード提出スキルを追加

## Q2 言い直し・中断が起きた場面で、最初の依頼に何が足りなかったか

### 完了条件を書かずに依頼し、テストの範囲で 2 回言い直した

- id: 2026-W43/Q2/y.toyota/001
- 状態: draft
- 極性: failed / 確度: inferred / 公開範囲: internal
- プロジェクト: ai_development_tools
- タグ: prompt, testing

週の計算を直す依頼で、どのテストを通せば終わりかを書かなかった。年またぎのテストを後から 2 回足すことになった。

**根拠**

- prompt `<session_id>@2026-10-20T10:12+00:00`: 週の計算を直して
- prompt `<session_id>@2026-10-20T10:20+00:00`: 年またぎも
  テストして
