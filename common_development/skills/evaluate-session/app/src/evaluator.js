/**
 * Claude CLI 連携モジュール
 * 統計レポートを Claude CLI に渡してスコアリング評価を取得する。
 */

const { execFile, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

class EvaluationError extends Error {
  constructor(message) {
    super(message);
    this.name = "EvaluationError";
  }
}

/**
 * claude CLI が PATH 上に存在するか確認する。
 * shell: true で実行するためパス解決は不要、存在チェックのみ行う。
 */
function assertClaudeCliExists() {
  const { execSync } = require("child_process");
  try {
    execSync(
      process.platform === "win32" ? "where claude" : "which claude",
      { encoding: "utf-8", timeout: 5000, stdio: "pipe" }
    );
  } catch {
    throw new EvaluationError(
      "Claude CLI が見つかりません。'claude' コマンドがPATHに存在するか確認してください。"
    );
  }
}

const EVALUATION_PROMPT = `
あなたはClaude Codeセッションの「無駄」を検出する評価者です。
以下のフォーマットで評価レポートを出力してください。<stats>タグ内の数値のみを根拠にしてください。

### セッション効率レポート

**セッションID**: <stats内のセッションIDを使用>
**対象プロジェクト**: <stats内のCWDまたはファイルパスから判定>
**セッション時間**: <stats内の所要時間を使用>
**使用モデル**: <stats内のモデル名を使用>
**タスク概要**: <stats内の初回コマンドまたは初回ユーザーメッセージから要約（1行）>
**Gitブランチ**: <stats内のブランチ名を使用>
**総ターン数**: N（user: N / assistant: N）
**総トークン**: input: N / output: N
**キャッシュ活用率**: N%

#### スコア（合計100点）

| 観点 | 配点 | スコア | 根拠 |
|---|---|---|---|
| A. 重複作業 | /15 | | 同一ファイル重複読み、同一ファイル複数回書き直し、subagentとの作業重複 |
| B. トークン効率 | /15 | | 入力トークン量、キャッシュ活用率、大型ツール結果によるコンテキスト肥大 |
| C. 目的外作業 | /20 | | ユーザー指示と無関係なファイル操作、頼まれていない改善・リファクタリング |
| D. 初動の的確さ | /15 | | タスクに適した初手を取れているか、不要な前置き作業がないか |
| E. エラー回復効率 | /10 | | エラー後に原因分析せず同じことをリトライしていないか |
| F. 不要な探索 | /15 | | 目的に不要なファイル読み込み、使わなかったスキルの読み込み、過剰なGlob/Grep |
| G. モデル選定 | /10 | | タスク複雑さに対してモデルが不足していないか、サブエージェントのモデル選定は適切か |
| **合計** | **/100** | | |

**評価の原則**:
- このレポートの目的は「セッション中の無駄を見つけて改善すること」。品質や正確性は評価しない
- 統計データとタスク概要を照らし合わせ、「この作業はタスク達成に必要だったか？」を常に問う
- 無駄がない作業を減点してはならない。正当な調査・理解のためのReadは無駄ではない

**スコア基準（厳守）**:
- 各項目は配点の範囲内で採点する（例: A項目は0-15点）
- 配点の90%以上: 問題ゼロ（A〜Fでは稀だが、G項目は問題なければ満点が普通）
- 配点の70-89%: 軽微な無駄が1-2件
- 配点の40-69%: 明確な無駄あり
- 配点の0-39%: 重大な浪費
- 平均的なセッションは50-65/100を目安に。70超えは本当に無駄のないセッションのみ

**各観点の判定ガイド**:

**A. 重複作業（15点）**
統計データから機械的に検出できる無駄。

ファイル重複読み込み:
- 0件 → 満点の基礎
- 2-3件 → -2〜-4点
- 5件以上 → -5〜-8点
- 部分Read（offset/limit指定）は効率的な手法。同じファイルでも異なる範囲を読む場合は重複としない

同一ファイル書き直し（手戻り）:
- 3回以上書き込みファイルが0件 → 減点なし
- 1-2件 → -2〜-3点
- 3件以上 → -4〜-7点
- テストファイルの反復修正はTDD的パターンのため減点を緩和

subagentとの作業重複:
- subagentに調査させた後、メインで同じファイルを読んでいる → -2〜-3点
- subagentのRead対象とメインのRead対象の重複が多い場合は顕著な無駄

**B. トークン効率（15点）**
トークン消費の無駄。コストに直結する重要指標。

入力トークン異常:
- input_tokens TOP1が20万超 → 巨大ファイル丸読みの疑い → -4点
- input_tokens TOP1が10万超 → -2点

キャッシュ活用:
- キャッシュ活用率60%以上 → +2点ボーナス
- キャッシュ活用率20%未満 → -3点

大型ツール結果（コンテキスト肥大）:
- 大型ツール結果（10K+文字）が0件 → 減点なし
- 1-3件 → -2点
- 4件以上 → -3〜-5点
- ツール結果合計が100万文字超 → -2点

**C. 目的外作業（20点）**
AI評価者の判断が必要な項目。タスク概要と実際の作業内容を突き合わせて判定する。

以下の観点で判定:
- ユーザーが依頼していないリファクタリングやコード改善を行っていないか
- ユーザー指示と無関係なファイルへのWrite/Editがないか
- 不要なドキュメント追加（README、コメント等）を行っていないか
- タスク完了後に余計な「改善」を続けていないか

判定方法:
- タスク概要から「やるべきこと」を特定する
- Write/Edit対象ファイル一覧と照らし合わせる
- タスクに直接必要ないWrite/Editがあれば、その量に応じて減点
- 明らかに目的外の作業が多い → -8〜-15点
- 軽微な余計な作業が1-2件 → -3〜-5点
- 判断が難しい場合はセッションに有利な方向で判定する

**D. 初動の的確さ（15点）**
タスクに対して適切な初手を取れているか。不要な前置き作業がないか。

判定方法（タスク概要に基づく）:
- タスク概要と最初の15ツールを照らし合わせ、初手が適切か判定する
- 例: PRレビュー → gh pr viewやReadが初手なら適切
- 例: バグ修正 → Read/Grep/Globで調査から入れば適切
- 例: ドキュメント生成 → テンプレートやSKILL.md読み込みが初手なら適切
- 例: 既知ファイルの簡単な修正 → すぐにReadしてEditに入れば適切

減点基準:
- タスクに不要な広範な探索から始めている → -3〜-5点
- いきなりWriteから始めて後で手戻りしている → -5〜-8点
- 初手は妥当だが不要なステップが混じっている → -2〜-3点
- Skillツールを呼んだがSKILL.mdを実際には活用しなかった場合も無駄な初動に含む

**E. エラー回復効率（10点）**
エラーへの対処が効率的か。

- エラー0件 → 10点
- エラーあるが即リトライ0件（原因分析してから再試行） → 7-9点
- 即リトライ1-2件 → 4-6点
- 即リトライ3件以上 → 1-3点
- エラーの原因がClaude側にない場合（環境起因等）は減点を緩和

**F. 不要な探索（15点）**
AI評価者の判断が必要な項目。タスク達成に必要なかった探索・調査作業を検出する。

以下の観点で判定:
- Read対象ファイル一覧のうち、タスク達成に明らかに不要なファイルはないか
- 過剰なGlob/Grepを行っていないか（同じ情報を何度も別の方法で探す等）
- SKILL.mdを読んだのにそのスキルを使わなかった場合は無駄な読み込み
- subagentに探索させた結果を活用せず、自分で別の探索を始めていないか

判定方法:
- タスク概要から「知る必要がある情報」を特定する
- Read対象ファイル一覧、Glob/Grep対象、Skill呼び出し一覧と照らし合わせる
- タスクに直接必要ない探索が多い → -6〜-12点
- 軽微な余計な探索が1-2件 → -2〜-4点
- 正当な調査・理解のためのReadは無駄ではない。減点してはならない
- 判断が難しい場合はセッションに有利な方向で判定する

**G. モデル選定の適切さ（10点）**
タスクの複雑さに対して適切なモデルが使われているかを評価する。
過剰（高性能モデルの使用）は問題としない。不足（能力不足のモデル使用）を検出する。

モデル能力の序列（高い順）:
- opus: 最高性能。複雑な推論、大規模リファクタリング、設計判断に最適
- sonnet: 標準性能。大半のコーディングタスクに十分だが、以下の場面ではopusが望ましい:
  - 多数ファイル（10+）にまたがる整合性が必要な大規模変更
  - 曖昧な要件から最適な設計を判断する必要がある場面
  - 深い推論チェーン（複数の設計トレードオフを同時考慮）
- haiku: 軽量。思考が浅くなるリスクがある。以下の用途のみ適切:
  - ファイル名・キーワードによる単純なGlob/Grep検索
  - 定型的な文字列置換・フォーマット変換
  - haikuが不適切な用途: アーキテクチャの理解・分析、複数ファイルの関連性把握、設計判断を伴う探索、コードレビュー

メインモデルの判定:
- 複雑なタスク（大規模リファクタリング、設計判断、複数ファイルの整合性が必要）にhaiku → -5〜-8点
- 複雑なタスクにsonnet → -1〜-2点（opusが望ましかった）
- 中程度のタスクにhaiku → -3〜-5点
- 中程度のタスクにsonnet → 問題なし
- 単純なタスク（typo修正、簡単な変更）→ どのモデルでも問題なし

サブエージェントのモデル選定（プロンプト内容で判定すること）:
- サブエージェントなし or モデル指定なし（親継承） → 減点なし
- haikuのサブエージェント → プロンプト内容を必ず確認する:
  - 「〜を検索して」「〜というファイルを探して」等の単純検索 → 適切
  - 「〜の仕組みを調べて」「〜のアーキテクチャを理解して」「〜を分析して」等の理解・分析を伴う探索 → 不適切（-2〜-3点）
  - 設計・実装・レビューを担うサブエージェント → 不適切（-2〜-3点）
- sonnetのサブエージェント → 基本的に問題なし。ただし複雑な設計・実装を単独で担う場合は-1点
- opus → 常に問題なし

判定の原則:
- 過剰（overkill）は減点しない。コストより品質を重視する方針
- 不足（underpowered）のみ減点する
- 具体的な不足が検出されなければ10/10（満点）をつけること。「なんとなく-1点」は禁止
- 全てopus → 10/10
- haikuが使われていても、プロンプトが単純検索のみ → 10/10
- 判断が難しい場合はセッションに有利な方向で判定する

#### 検出された問題（重要度順）

問題ごとに:
- **問題**: 何が起きたか（statsの具体的数値を引用）
- **影響**: 推定浪費トークン数 or 推定余分ターン数
- **改善策**: 次回の具体的アクション

#### 改善提案

検出された問題ごとに、最も適切な対策カテゴリを選んで提案する。
問題が検出されなかった観点の提案は出力しない。全カテゴリ合計で最大5件。

カテゴリ選定基準（上から優先して検討）:
1. **hook** → 機械的に検出・防止できる問題
2. **rule** → Claudeの判断基準に関わる問題
3. **skill** → 複数ステップの手順が毎回同じパターンで必要な場合
4. **command** → ユーザーが任意のタイミングで手動実行したい定型処理
`.trim();

// フォールバック用ワークディレクトリ
const _WORK_DIR = path.join(__dirname, "..");

/**
 * Claude CLI を呼び出してセッション評価を取得する。
 *
 * targetProjectDir が指定された場合、Claude CLIをそのディレクトリで実行し、
 * プロジェクトのCLAUDE.mdやコンテキスト情報を活用できるようにする。
 * 一時ファイルはos.tmpdir()に書き出し、プロジェクトを汚染しない。
 */
function runEvaluation(statsText, model = null, targetProjectDir = null) {
  return new Promise((resolve, reject) => {
    try {
      assertClaudeCliExists();
    } catch (e) {
      reject(e);
      return;
    }

    // 対象プロジェクトディレクトリの決定
    const effectiveCwd = (targetProjectDir && fs.existsSync(targetProjectDir))
      ? targetProjectDir
      : _WORK_DIR;

    // 一時ファイルはos.tmpdir()に書き出してプロジェクトを汚染しない
    const tmpDir = os.tmpdir();
    const statsFile = path.join(tmpDir, "_eval_stats.txt");
    const rubricFile = path.join(tmpDir, "_eval_rubric.txt");
    const promptFile = path.join(tmpDir, "_eval_prompt.txt");

    // 絶対パスでファイルを参照するプロンプト
    const rubricPath = rubricFile.replace(/\\/g, "/");
    const statsPath = statsFile.replace(/\\/g, "/");
    const prompt =
      `${rubricPath} に評価ルーブリックが、` +
      `${statsPath} にセッション統計データがあります。` +
      `まず両方のファイルをReadで読み、` +
      (effectiveCwd !== _WORK_DIR
        ? `次にこのプロジェクトのCLAUDE.mdが存在すれば読んでプロジェクトのコンテキストを理解し、`
        : ``) +
      `ルーブリックに厳密に従って統計データをスコアリングし、` +
      `評価レポートを出力してください。`;

    try {
      fs.writeFileSync(statsFile, statsText, "utf-8");
      fs.writeFileSync(rubricFile, EVALUATION_PROMPT, "utf-8");
      fs.writeFileSync(promptFile, prompt, "utf-8");
    } catch (e) {
      reject(new EvaluationError(`一時ファイルの書き込みに失敗: ${e.message}`));
      return;
    }

    const args = [
      "--print",
      "--output-format", "text",
      "--no-session-persistence",
      "--allowedTools", "Read",
    ];
    if (model) args.push("--model", model);

    const env = { ...process.env };
    delete env.CLAUDECODE;

    // ログファイル
    const logFile = path.join(_WORK_DIR, "_eval_debug.log");
    const logStream = fs.createWriteStream(logFile, { flags: "w" });
    const log = (msg) => {
      const ts = new Date().toISOString();
      logStream.write(`[${ts}] ${msg}\n`);
      console.log(`[evaluator] ${msg}`);
    };

    log(`cmd: claude ${args.join(" ")} (prompt via stdin pipe)`);
    log(`cwd: ${effectiveCwd}`);
    log(`targetProjectDir: ${targetProjectDir || "(none)"}`);
    log(`prompt length: ${prompt.length} chars`);
    log(`prompt: ${prompt}`);

    // stdinをpipeにして、プロンプトをstdinから渡す
    const child = spawn("claude", args, {
      cwd: effectiveCwd,
      env,
      shell: true,
      stdio: ["pipe", "pipe", "pipe"],
    });

    // プロンプトをstdinに書き込んで閉じる
    child.stdin.write(prompt);
    child.stdin.end();

    let stdout = "";
    let stderr = "";
    let settled = false;

    child.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      stdout += text;
      log(`[stdout +${text.length}] ${text.slice(0, 200)}`);
    });

    child.stderr.on("data", (chunk) => {
      const text = chunk.toString();
      stderr += text;
      log(`[stderr +${text.length}] ${text.slice(0, 200)}`);
    });

    child.on("error", (err) => {
      log(`[error] ${err.message}`);
      cleanup();
      if (!settled) {
        settled = true;
        reject(new EvaluationError(`Claude CLI 起動エラー: ${err.message}`));
      }
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      log(`[close] code=${code} stdout=${stdout.length} stderr=${stderr.length}`);
      logStream.end();
      cleanup();
      if (settled) return;
      settled = true;

      if (code !== 0) {
        const errMsg = stderr.trim() || `exit code ${code}`;
        reject(new EvaluationError(`Claude CLI エラー (code=${code}): ${errMsg}`));
      } else {
        resolve(stdout.trim());
      }
    });

    const timer = setTimeout(() => {
      log(`[timeout] 180s elapsed, killing process`);
      child.kill();
      logStream.end();
      cleanup();
      if (!settled) {
        settled = true;
        reject(new EvaluationError(
          "Claude CLI がタイムアウトしました（180秒）。_eval_debug.log を確認してください。"
        ));
      }
    }, 180000);

    function cleanup() {
      try { fs.unlinkSync(statsFile); } catch {}
      try { fs.unlinkSync(rubricFile); } catch {}
      try { fs.unlinkSync(promptFile); } catch {}
    }
  });
}

/**
 * 評価結果テキストから合計スコアを抽出する。
 * /100 を優先し、フォールバックで /80, /60 にも対応（既存履歴との後方互換性）。
 */
function extractTotalScore(evaluationText) {
  // 「合計 85/100」形式
  const match100 = evaluationText.match(/合計.*?(\d{1,3})\s*\/\s*100/);
  if (match100) return parseInt(match100[1], 10);
  // テーブル形式: 「| 合計 | /100 | 73 |」（/100 がスコアより前の列にある）
  const matchTable100 = evaluationText.match(/合計.*?\/\s*100\D*?(\d{1,3})/);
  if (matchTable100) return parseInt(matchTable100[1], 10);
  // 後方互換: 旧80点・60点スケール
  const match80 = evaluationText.match(/合計.*?(\d{1,2})\s*\/\s*80/);
  if (match80) return parseInt(match80[1], 10);
  const matchTable80 = evaluationText.match(/合計.*?\/\s*80\D*?(\d{1,3})/);
  if (matchTable80) return parseInt(matchTable80[1], 10);
  const match60 = evaluationText.match(/合計.*?(\d{1,2})\s*\/\s*60/);
  if (match60) return parseInt(match60[1], 10);
  const matchTable60 = evaluationText.match(/合計.*?\/\s*60\D*?(\d{1,3})/);
  return matchTable60 ? parseInt(matchTable60[1], 10) : null;
}

module.exports = { EvaluationError, runEvaluation, extractTotalScore };
