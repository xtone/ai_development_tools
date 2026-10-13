# カードの書き方

カードは「問いへの答え」を 1 枚に 1 つ書いた付箋である。合成の工程で他の人のカードと並べ、正（worked）と反（failed）の対立から提案を作る。並べたときに意味が通ることを優先する。

## 採るカード

次の 3 つをすべて満たすものだけを下書きする。

1. **記録に根拠がある**: `sessions.json` のどこかに裏付けがある。根拠の無い推測はカードにしない。記録から推し量った部分があるときは `confidence: inferred` にする
2. **問いに答えている**: 問いの文に対する答えになっている。別の問いの答えなら、そちらの問いのカードにする
3. **自分の作業の話である**: 自分が依頼したこと、自分のセッションで起きたことを書く

次のものは採らない。

- コード、公式ドキュメント、ライブラリの仕様の書き写し
- 一度だけの事故で、もう一度起きる条件を説明できないもの
- 他人の作業や判断の評価（「〜さんのレビューが遅かった」など）。チームの話はプロセスとして書く
- 人事評価・処遇（評価、査定、給与、賞与、昇格要件、1on1 など）と、Xtone・PKSHA の経営（経営会議、役員、決算、業績、事業計画、M&A、組織変更など）に関する話題。経営層の利用で社内秘が全社エリアに出ないようにするため。抽出の段階で外しているが、すり抜けた材料があってもカードにせず、`validate` のエラー（confidential topic）が出たら言い換えずに消す。要確認の語（昇格、退職など）のエラーだけは、本人に聞いて業務用語だと確認できたときに `--allow-term` で通す

## claim の書き方

- 20〜80 字。結論を書く。「〜について」「〜に関して」で終わる見出しにしない
- 1 枚に 1 つの主張。「A し、B もした」と 2 つ書きたくなったら 2 枚に分ける
- 主語は依頼やプロセス。人を主語にした失敗談にしない
  - よい例: 「完了条件のテスト名を最初に書くと、言い直しなしで commit まで進んだ」
  - よい例: 「完了条件を書かずに依頼し、テストの範囲で 2 回言い直した」
  - 悪い例: 「テストについて」「自分の指示が悪かった」
- P1・P2・Q6（事実カード）は「<プロジェクト>: <内容>」で始める

文脈（`context`）には、どんな状況で起きたかを 2〜3 文で書く。読み手は別のプロジェクトの人で、エンジニア以外も読むと考える。

## 極性と確度

| polarity | 意味 | 使う問い |
|---|---|---|
| worked | うまくいったこと（正） | Q1 |
| failed | うまくいかなかったこと（反） | Q2, Q4, Q7 |
| proposal | 提案・定型化できるもの | Q3, Q8。Q4 と Q7 では「先にこうしていれば」を別カードにするときに使う |
| question | 問い・未解決・判断が要ること | Q5, Q9 |
| fact | 事実 | P1, P2, Q6 |

問いの既定値（`questions.json` の `polarity`）か `allowed_polarities` 以外は `cards.py validate` が落とす。

| confidence | 意味 |
|---|---|
| observed | 根拠の抜粋にそのまま書いてある |
| inferred | 抜粋から推し量った（因果関係、効いた理由など） |

## 根拠（evidence）

1 枚に 1 件以上。抜粋（`excerpt`）は `sessions.json` の伏せ字済みの文字列から 300 字以内で取る。抜粋を書き換えたり、伏せ字を戻したりしない。

| type | ref の形 | 出どころ |
|---|---|---|
| prompt | `<session_id>@<time>`（session_id が null なら `prompt@<time>`） | `prompts[]` |
| command | `<session_id>@<time>`（無ければ `command@<project>`） | `bash_samples[]` |
| commit | `<session_id>@<time>` | `commits[]` |
| pr | `<session_id>@<time>` | `prs[]` |
| memory | `memory:<project>/<name>` | `memories[]` |
| harness | `harness:<commands|skills|agents|hooks|plugins>/<name>` | `harness` |
| session | `<session_id>#<uuid>` | Phase 2（extract v2）で使う |

`<time>` は `sessions.json` の `time` をそのまま使う（例: `2026-10-20T10:12+00:00`）。

## 問いごとに見る場所

| 問い | sessions.json で見るところ | 下書きの要点 |
|---|---|---|
| P1 | `commits[]`、`prs[]`、`prompts[]` の `project` | プロジェクトごとに 1 枚。「<プロジェクト>: <領域>を<フェーズ>。<状態>」。commit と PR のタイトルを根拠にする |
| P2 | `tool_usage.mcp_servers`、`tool_usage.skills`、`bash_samples`、`harness` | プロジェクトごとに 1 枚。言語・FW・インフラ・外部 API・MCP・スキル |
| Q1 | `prompts[]` のうち、同じ `session_id` の prompt が少なく、その後に `commits[]` か `prs[]` があるもの。繰り返し使っている文型 | 実際の prompt を引用し、何が効いたかを 1 文で書く |
| Q2 | `prompts[]` を `session_id` ごとに時刻順に並べ、短い間隔で続く prompt や、「違う」「そうではなく」「やっぱり」「戻して」「もう一度」「じゃなくて」で始まる prompt | 「最初の依頼」「起きたこと」「足りなかった条件」の 3 点。依頼の書き方の話として書く |
| Q3 | `harness.commands`・`harness.skills`・`harness.agents`、`tool_usage.skills`、毎回付けている前置き | 既にある定型手順と、まだ手で書いている定型化の候補の両方 |
| Q4 | 同じ `session_id` で prompt が長く続いたもの、テストやエラーについての prompt | 手戻りの大きさ（prompt の数・時間）を根拠にする。「先にこうしていれば」は proposal の別カードにしてよい |
| Q5 | `prompts[]` のうち `!` で始まるもの、許可や判断を求める往復 | 介入の種類と、必要だったかの自己判定 |
| Q6 | `tool_usage.skills`、`tool_usage.gh`、`prs[]` | プロジェクトごとに 1 枚。要件・設計・実装・レビューで AI を使ったか、使わなかった理由 |
| Q7 | `tool_usage.gh` の `gh pr view`、レビュー後の修正を頼む prompt | 指摘の種類と、どの工程に入れていれば防げたか |
| Q8 | `memories[]` の `how_to_apply`、CLAUDE.md や rules を直した prompt | ルールの原文（伏せ字済み）と、共通化できる理由 |
| Q9 | 未解決のまま終わった話題、繰り返し調べている話題、`memories[]` の落とし穴 | 詰まっていることと、誰に聞けば解けそうか |

Phase 1 の抽出には中断・訂正・エラーの専用シグナルが無い。Q2・Q4・Q5 は prompt の並びから推し量ることが多いので、その場合は `confidence: inferred` にする。

## 該当なし

問いに答える材料が無ければ、`claim` を「該当なし: <理由>」で始めて 1 枚出す（例: 「該当なし: 今週は中断が無かった」）。極性は問いの既定値、根拠には見た範囲（例: `prompt@<期間の最初の時刻>` と「期間中の prompt 32 件を確認」）を書く。

## 枚数

1 問あたり 1〜3 枚、1 週で 10 枚までを目安にする。多いときは根拠の強いものを残す。超えると `validate` が警告を出す。

## タグ

`questions.json` の `tags`（prompt, plan-mode, worktree, review, hooks, skill, mcp, testing, git, ci）から選ぶ。合うものが無ければ空でよい。`questions.json` に無いタグを付けると `validate` が警告を出す。提出するには Notion の選択肢に足す必要がある（`references/notion-submit.md` の手順 4）ので、本当に要るか判断する。

## 機密

`sessions.json` は秘密情報を伏せ字にしてあるが、ホスト名やクライアントの社名が残ることがある。社内（internal）ではプロジェクト名・リポジトリ名・著者名は残してよい。次は書かない。

- トークン・鍵・パスワード、メールアドレス
- 顧客の個人情報、クライアント内部のホスト名・URL
- 組織 ID・アカウント ID、ホームディレクトリのパス、Notion の内部 URL

`scan_sensitive.py --tier internal` が 0 件にならない限り提出しない。
