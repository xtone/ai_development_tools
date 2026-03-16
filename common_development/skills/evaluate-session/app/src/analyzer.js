/**
 * Claude Code セッションログ分析モジュール
 * JSONLファイルから統計情報を抽出し、テキストレポートとして返す。
 * サブエージェントのトランスクリプト（subagents/agent-*.jsonl）も自動検出して集計。
 */

const fs = require("fs");
const path = require("path");

/**
 * SessionStats: 1つのセッション（メインまたはサブエージェント）の統計
 */
function createStats(label, filePath) {
  return {
    label,
    filePath,
    fileSizeMb: 0,
    totalLines: 0,
    userCount: 0,
    assistantCount: 0,
    toolNames: {},
    readFiles: {},
    viewFiles: {},
    writeFiles: {},
    editFiles: {},
    skillReads: [],
    claudeMdReads: [],
    writtenExtensions: {},
    errorCount: 0,
    errorLines: [],
    totalInputTokens: 0,
    totalOutputTokens: 0,
    totalCacheRead: 0,
    totalCacheCreation: 0,
    inputTokenPerTurn: [],
    outputTokenPerTurn: [],
    toolSequence: [],

    // 時間情報
    firstTimestamp: null,
    lastTimestamp: null,
    timestamps: [],

    // セッションメタデータ
    sessionId: null,
    slug: null,
    gitBranch: null,
    cwd: null,
    version: null,

    // タスク/ゴール
    firstUserMessage: null,
    queueCommand: null,
    userMessages: [],  // ユーザーメッセージ一覧（先頭200文字、最大20件）

    // モデル情報
    models: {},
    modelToolUsage: {},  // { modelName: { toolName: count } } モデルごとのツール使用内訳

    // stop_reason分布
    stopReasons: {},

    // ツール分類
    mcpToolNames: {},
    builtinToolNames: {},

    // サブエージェント追跡
    subagentLaunches: [],

    // コンテキスト効率
    toolResultSizes: [],
    largeToolResults: [],
    totalToolResultChars: 0,

    // キャッシュ内訳
    ephemeral5mTokens: 0,
    ephemeral1hTokens: 0,

    // 会話フロー
    maxToolChainLength: 0,
    endTurnCount: 0,

    // 部分Read追跡
    partialReadCount: 0,

    // Skillツール呼び出し追跡
    skillInvocations: [],
  };
}

function counterIncr(counter, key, amount = 1) {
  counter[key] = (counter[key] || 0) + amount;
}

function counterMerge(...counters) {
  const result = {};
  for (const c of counters) {
    for (const [k, v] of Object.entries(c)) {
      result[k] = (result[k] || 0) + v;
    }
  }
  return result;
}

function counterMostCommon(counter, n = Infinity) {
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n);
}

/**
 * JSONLファイルをパースしてStatsを返す
 */
function parseJsonl(sf, label) {
  const stats = createStats(label, sf);
  const st = fs.statSync(sf);
  stats.fileSizeMb = st.size / 1024 / 1024;

  let currentToolChainLen = 0;
  let currentModel = null;  // 直近のassistantメッセージのモデル

  const content = fs.readFileSync(sf, "utf-8");
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    let entry;
    try {
      entry = JSON.parse(trimmed);
    } catch {
      continue;
    }

    stats.totalLines++;
    const msg = entry.message || {};
    const role = msg.role || "";

    // --- タイムスタンプ抽出 ---
    const ts = entry.timestamp;
    if (ts) {
      if (!stats.firstTimestamp) stats.firstTimestamp = ts;
      stats.lastTimestamp = ts;
      if (stats.timestamps.length < 2000) {
        stats.timestamps.push({ ts, type: entry.type || "", role });
      }
    }

    // --- セッションメタデータ（最初の出現を採用） ---
    if (!stats.sessionId && entry.sessionId) stats.sessionId = entry.sessionId;
    if (!stats.slug && entry.slug) stats.slug = entry.slug;
    if (!stats.gitBranch && entry.gitBranch) stats.gitBranch = entry.gitBranch;
    if (!stats.cwd && entry.cwd) stats.cwd = entry.cwd;
    if (!stats.version && entry.version) stats.version = entry.version;

    // --- queue-operation ---
    if (entry.type === "queue-operation" && entry.operation === "enqueue" && entry.content) {
      if (!stats.queueCommand) stats.queueCommand = entry.content;
    }

    if (role === "user") {
      stats.userCount++;

      // --- ユーザーメッセージ抽出 ---
      let userText = null;
      const c = msg.content;
      if (typeof c === "string" && c.trim()) {
        userText = c.trim();
      } else if (Array.isArray(c)) {
        for (const b of c) {
          if (typeof b === "object" && b !== null && b.type === "text" && b.text) {
            userText = b.text.trim();
            break;
          }
        }
      }
      if (userText) {
        if (!stats.firstUserMessage) {
          stats.firstUserMessage = userText.slice(0, 500);
        }
        if (stats.userMessages.length < 20) {
          stats.userMessages.push(userText.slice(0, 200));
        }
      }
    } else if (role === "assistant") {
      stats.assistantCount++;

      // --- モデル情報 ---
      if (msg.model) {
        counterIncr(stats.models, msg.model);
        currentModel = msg.model;
      }

      // --- stop_reason & ツールチェーン追跡 ---
      const stopReason = msg.stop_reason;
      if (stopReason) {
        counterIncr(stats.stopReasons, stopReason);
        if (stopReason === "tool_use") {
          currentToolChainLen++;
          if (currentToolChainLen > stats.maxToolChainLength) {
            stats.maxToolChainLength = currentToolChainLen;
          }
        } else {
          currentToolChainLen = 0;
          if (stopReason === "end_turn") stats.endTurnCount++;
        }
      }
    }

    // トークン使用量
    const usage = msg.usage || {};
    if (Object.keys(usage).length > 0) {
      const it = usage.input_tokens || 0;
      const ot = usage.output_tokens || 0;
      const cr = usage.cache_read_input_tokens || 0;
      const cc = usage.cache_creation_input_tokens || 0;
      stats.totalInputTokens += it;
      stats.totalOutputTokens += ot;
      stats.totalCacheRead += cr;
      stats.totalCacheCreation += cc;
      if (it > 0) stats.inputTokenPerTurn.push(it);
      if (ot > 0) stats.outputTokenPerTurn.push(ot);

      // --- キャッシュ内訳 ---
      const cacheCreation = usage.cache_creation;
      if (cacheCreation) {
        stats.ephemeral5mTokens += (cacheCreation.ephemeral_5m_input_tokens || 0);
        stats.ephemeral1hTokens += (cacheCreation.ephemeral_1h_input_tokens || 0);
      }
    }

    // content解析
    const contentBlocks = msg.content;
    if (typeof contentBlocks === "string" || !Array.isArray(contentBlocks))
      continue;

    for (const block of contentBlocks) {
      if (typeof block !== "object" || block === null) continue;

      const blockType = block.type || "";

      if (blockType === "tool_use") {
        const name = block.name || "";
        const inp = block.input || {};
        counterIncr(stats.toolNames, name);

        // --- モデル別ツール使用追跡 ---
        if (currentModel) {
          if (!stats.modelToolUsage[currentModel]) stats.modelToolUsage[currentModel] = {};
          counterIncr(stats.modelToolUsage[currentModel], name);
        }

        // --- ツール分類 ---
        if (name.startsWith("mcp__")) {
          counterIncr(stats.mcpToolNames, name);
        } else {
          counterIncr(stats.builtinToolNames, name);
        }

        const fp = inp.file_path || inp.filePath || inp.path || "";
        const cmd = inp.command || "";

        stats.toolSequence.push({
          line: stats.totalLines,
          name,
          target: fp || cmd,
          isError: false,
        });

        // --- サブエージェント検出 ---
        if (name === "Agent") {
          stats.subagentLaunches.push({
            type: inp.subagent_type || "unknown",
            model: inp.model || null,
            description: (inp.description || "").slice(0, 120),
            promptSnippet: (inp.prompt || "").slice(0, 200),
          });
        }

        // --- Skillツール呼び出し検出 ---
        if (name === "Skill") {
          stats.skillInvocations.push({
            skill: inp.skill || "unknown",
            args: (inp.args || "").slice(0, 120),
          });
        }

        if (name === "Read" || name === "View") {
          const target = name === "Read" ? stats.readFiles : stats.viewFiles;
          if (fp) counterIncr(target, fp);

          // --- 部分Read検出（offset/limit指定） ---
          if (inp.offset || inp.limit) {
            stats.partialReadCount++;
          }

          if (fp) {
            const lower = fp.toLowerCase();
            if (lower.includes("skill.md")) stats.skillReads.push(fp);
            if (lower.includes("claude.md")) stats.claudeMdReads.push(fp);
          }
        } else if (
          ["Write", "Edit", "MultiEdit", "str_replace"].includes(name)
        ) {
          if (fp) {
            if (name === "Write") {
              counterIncr(stats.writeFiles, fp);
              const ext = path.extname(fp);
              if (ext) counterIncr(stats.writtenExtensions, ext);
            } else {
              counterIncr(stats.editFiles, fp);
            }
          }
        }
      } else if (blockType === "tool_result") {
        // --- ツール結果サイズ測定 ---
        const resultContent = block.content;
        let resultSize = 0;
        if (typeof resultContent === "string") {
          resultSize = resultContent.length;
        } else if (Array.isArray(resultContent)) {
          for (const item of resultContent) {
            if (typeof item === "string") resultSize += item.length;
            else if (typeof item === "object" && item !== null) {
              if (item.text) resultSize += item.text.length;
              else resultSize += JSON.stringify(item).length;
            }
          }
        }
        stats.totalToolResultChars += resultSize;

        const lastTool = stats.toolSequence.length > 0
          ? stats.toolSequence[stats.toolSequence.length - 1]
          : null;
        if (stats.toolResultSizes.length < 2000) {
          const sizeEntry = {
            line: stats.totalLines,
            toolName: lastTool ? lastTool.name : "unknown",
            size: resultSize,
          };
          stats.toolResultSizes.push(sizeEntry);
          if (resultSize > 10000) {
            stats.largeToolResults.push(sizeEntry);
          }
        }

        const isErr = block.is_error || false;
        if (isErr) {
          stats.errorCount++;
          if (stats.toolSequence.length > 0) {
            const last = stats.toolSequence[stats.toolSequence.length - 1];
            last.isError = true;
            stats.errorLines.push({
              line: stats.totalLines,
              name: last.name,
              target: last.target,
            });
          }
        }
      }
    }
  }

  return stats;
}

/**
 * メインセッションに対応するサブエージェントJSONLを探す
 */
function findSubagentFiles(mainSf) {
  const stem = path.basename(mainSf, ".jsonl");
  const subagentDir = path.join(path.dirname(mainSf), stem, "subagents");
  if (fs.existsSync(subagentDir)) {
    return fs
      .readdirSync(subagentDir)
      .filter((f) => f.startsWith("agent-") && f.endsWith(".jsonl"))
      .sort()
      .map((f) => path.join(subagentDir, f));
  }

  const subagentDir2 = path.join(path.dirname(mainSf), "subagents");
  if (fs.existsSync(subagentDir2)) {
    return fs
      .readdirSync(subagentDir2)
      .filter((f) => f.startsWith("agent-") && f.endsWith(".jsonl"))
      .sort()
      .map((f) => path.join(subagentDir2, f));
  }

  return [];
}

/**
 * メインセッション + サブエージェントをまとめて分析し、レポート文字列を返す。
 * sf: メインJSONLファイルパス（存在しない場合は空statsで代替）
 */
function analyzeSession(sf) {
  const mainExists = fs.existsSync(sf);
  const mainStats = mainExists
    ? parseJsonl(sf, "main")
    : createStats("main (no main file)", sf);
  const subagentFiles = findSubagentFiles(sf);
  const subStatsList = subagentFiles.map((subF) => {
    const agentId = path.basename(subF, ".jsonl").replace("agent-", "");
    return parseJsonl(subF, `subagent:${agentId}`);
  });

  if (!mainExists && subStatsList.length === 0) {
    throw new Error(`Session file not found: ${sf}`);
  }

  const allStats = [mainStats, ...subStatsList];

  // 集計
  const totalLines = allStats.reduce((s, x) => s + x.totalLines, 0);
  const userCount = allStats.reduce((s, x) => s + x.userCount, 0);
  const assistantCount = allStats.reduce((s, x) => s + x.assistantCount, 0);
  const toolNames = counterMerge(...allStats.map((s) => s.toolNames));
  const readFiles = counterMerge(...allStats.map((s) => s.readFiles));
  const viewFiles = counterMerge(...allStats.map((s) => s.viewFiles));
  const writeFiles = counterMerge(...allStats.map((s) => s.writeFiles));
  const editFiles = counterMerge(...allStats.map((s) => s.editFiles));
  const writtenExtensions = counterMerge(
    ...allStats.map((s) => s.writtenExtensions)
  );
  const errorCount = allStats.reduce((s, x) => s + x.errorCount, 0);

  const skillReads = allStats.flatMap((s) => s.skillReads);
  const claudeMdReads = allStats.flatMap((s) => s.claudeMdReads);

  const totalInputTokens = allStats.reduce(
    (s, x) => s + x.totalInputTokens,
    0
  );
  const totalOutputTokens = allStats.reduce(
    (s, x) => s + x.totalOutputTokens,
    0
  );
  const totalCacheRead = allStats.reduce((s, x) => s + x.totalCacheRead, 0);
  const totalCacheCreation = allStats.reduce(
    (s, x) => s + x.totalCacheCreation,
    0
  );

  const allInputTurns = allStats.flatMap((s) => s.inputTokenPerTurn);
  const allOutputTurns = allStats.flatMap((s) => s.outputTokenPerTurn);

  const toolSequence = mainStats.toolSequence;

  // 手戻り検出
  const allWriteEdits = counterMerge(writeFiles, editFiles);
  const reworkFiles = Object.fromEntries(
    Object.entries(allWriteEdits).filter(([, c]) => c >= 3)
  );

  // エラー→リトライループ検出
  const retryLoops = [];
  for (const s of allStats) {
    for (let idx = 0; idx < s.toolSequence.length; idx++) {
      const entry = s.toolSequence[idx];
      if (entry.isError && idx + 1 < s.toolSequence.length) {
        const next = s.toolSequence[idx + 1];
        if (next.name === entry.name) {
          retryLoops.push({
            label: s.label,
            line: entry.line,
            name: entry.name,
            target: entry.target,
          });
        }
      }
    }
  }

  // 計画性分析
  const firstNTools = toolSequence.slice(0, 15).map((t) => {
    return t.target ? `${t.name}(${t.target.slice(0, 60)})` : t.name;
  });

  // 重複Read
  const combinedReads = counterMerge(readFiles, viewFiles);
  const dupReads = Object.fromEntries(
    Object.entries(combinedReads).filter(([, c]) => c >= 2)
  );

  // --- 新規集計: メタデータ・時間・モデル・コンテキスト効率・会話フロー ---
  const sessionMeta = {
    sessionId: mainStats.sessionId,
    slug: mainStats.slug,
    gitBranch: mainStats.gitBranch,
    cwd: mainStats.cwd,
    version: mainStats.version,
    firstUserMessage: mainStats.firstUserMessage,
    queueCommand: mainStats.queueCommand,
  };
  // slug/branch等はサブエージェントからも探す
  for (const s of subStatsList) {
    if (!sessionMeta.slug && s.slug) sessionMeta.slug = s.slug;
    if (!sessionMeta.gitBranch && s.gitBranch) sessionMeta.gitBranch = s.gitBranch;
    if (!sessionMeta.cwd && s.cwd) sessionMeta.cwd = s.cwd;
    if (!sessionMeta.version && s.version) sessionMeta.version = s.version;
  }

  const models = counterMerge(...allStats.map((s) => s.models));
  // モデル別ツール使用を集約
  const modelToolUsage = {};
  for (const s of allStats) {
    for (const [model, toolCounter] of Object.entries(s.modelToolUsage)) {
      if (!modelToolUsage[model]) modelToolUsage[model] = {};
      for (const [tool, count] of Object.entries(toolCounter)) {
        modelToolUsage[model][tool] = (modelToolUsage[model][tool] || 0) + count;
      }
    }
  }
  const stopReasons = counterMerge(...allStats.map((s) => s.stopReasons));
  const mcpToolNames = counterMerge(...allStats.map((s) => s.mcpToolNames));
  const builtinToolNames = counterMerge(...allStats.map((s) => s.builtinToolNames));
  const subagentLaunches = allStats.flatMap((s) => s.subagentLaunches);
  const skillInvocations = allStats.flatMap((s) => s.skillInvocations);
  const totalToolResultChars = allStats.reduce((s, x) => s + x.totalToolResultChars, 0);
  const largeToolResults = allStats.flatMap((s) => s.largeToolResults)
    .sort((a, b) => b.size - a.size);
  const partialReadCount = allStats.reduce((s, x) => s + x.partialReadCount, 0);
  const ephemeral5mTokens = allStats.reduce((s, x) => s + x.ephemeral5mTokens, 0);
  const ephemeral1hTokens = allStats.reduce((s, x) => s + x.ephemeral1hTokens, 0);
  const maxToolChainLength = Math.max(...allStats.map((s) => s.maxToolChainLength), 0);
  const endTurnCount = allStats.reduce((s, x) => s + x.endTurnCount, 0);

  // セッション時間計算
  const allTimestamps = allStats.flatMap((s) => s.timestamps);
  allTimestamps.sort((a, b) => new Date(a.ts) - new Date(b.ts));
  const firstTs = allTimestamps.length > 0 ? allTimestamps[0].ts : null;
  const lastTs = allTimestamps.length > 0 ? allTimestamps[allTimestamps.length - 1].ts : null;
  let durationStr = "N/A";
  let durationSec = 0;
  if (firstTs && lastTs) {
    durationSec = (new Date(lastTs) - new Date(firstTs)) / 1000;
    const h = Math.floor(durationSec / 3600);
    const m = Math.floor((durationSec % 3600) / 60);
    const s = Math.floor(durationSec % 60);
    durationStr = h > 0 ? `${h}h ${m}m ${s}s` : m > 0 ? `${m}m ${s}s` : `${s}s`;
  }

  // ユーザー操作間の最大待ち時間 TOP3
  const userTimestamps = allTimestamps
    .filter((t) => t.role === "user" || t.type === "user")
    .map((t) => new Date(t.ts).getTime());
  const userGaps = [];
  for (let i = 1; i < userTimestamps.length; i++) {
    userGaps.push((userTimestamps[i] - userTimestamps[i - 1]) / 1000);
  }
  userGaps.sort((a, b) => b - a);
  const topGaps = userGaps.slice(0, 3).map((g) => `${Math.round(g)}s`);

  // レポート生成
  const totalReadView =
    Object.values(readFiles).reduce((s, v) => s + v, 0) +
    Object.values(viewFiles).reduce((s, v) => s + v, 0);
  const cacheTotal = totalInputTokens + totalCacheRead + totalCacheCreation;
  const cacheRate = cacheTotal > 0 ? (totalCacheRead / cacheTotal) * 100 : 0;

  const inputTop5 = [...allInputTurns].sort((a, b) => b - a).slice(0, 5);
  const outputTop5 = [...allOutputTurns].sort((a, b) => b - a).slice(0, 5);

  // subagentとメインのRead重複検出
  const mainReadSet = new Set(Object.keys(counterMerge(mainStats.readFiles, mainStats.viewFiles)));
  const subReadSets = subStatsList.map((s) => new Set(Object.keys(counterMerge(s.readFiles, s.viewFiles))));
  const subagentMainOverlap = [];
  for (const file of mainReadSet) {
    for (let i = 0; i < subReadSets.length; i++) {
      if (subReadSets[i].has(file)) {
        subagentMainOverlap.push({ file, subagent: subStatsList[i].label });
      }
    }
  }

  // SKILL.md読み込みとSkillツール呼び出しの突き合わせ
  const skillReadNames = skillReads.map((fp) => {
    const lower = fp.toLowerCase();
    const match = lower.match(/([^/\\]+)[/\\]skill\.md$/);
    return match ? match[1] : path.basename(path.dirname(fp));
  });
  const skillInvokedNames = skillInvocations.map((s) => s.skill);
  const skillReadButNotUsed = skillReadNames.filter(
    (name) => !skillInvokedNames.some((inv) => inv.toLowerCase().includes(name.toLowerCase()))
  );

  const r = [];
  r.push("=".repeat(60));
  r.push("SESSION ANALYSIS REPORT");
  r.push("=".repeat(60));
  r.push(`ファイル: ${path.basename(sf)}`);
  r.push(`セッションID: ${path.basename(sf, ".jsonl")}`);
  if (sessionMeta.slug) r.push(`セッションスラグ: ${sessionMeta.slug}`);
  if (sessionMeta.version) r.push(`Claude Codeバージョン: ${sessionMeta.version}`);
  if (sessionMeta.gitBranch) r.push(`Gitブランチ: ${sessionMeta.gitBranch}`);
  if (sessionMeta.cwd) r.push(`対象プロジェクトCWD: ${sessionMeta.cwd}`);
  const modelEntries = counterMostCommon(models);
  if (modelEntries.length > 0) {
    r.push(`使用モデル: ${modelEntries.map(([m, c]) => `${m} (${c}回)`).join(", ")}`);
  }
  r.push(`メインファイルサイズ: ${mainStats.fileSizeMb.toFixed(1)} MB`);
  r.push(`サブエージェント数: ${subStatsList.length}`);
  if (subStatsList.length > 0) {
    const totalSubSize = subStatsList.reduce((s, x) => s + x.fileSizeMb, 0);
    r.push(`サブエージェント合計サイズ: ${totalSubSize.toFixed(1)} MB`);
  }
  r.push("");

  // --- セッション時間 ---
  r.push("--- セッション時間 ---");
  r.push(`開始: ${firstTs || "N/A"}`);
  r.push(`終了: ${lastTs || "N/A"}`);
  r.push(`所要時間: ${durationStr}`);
  if (topGaps.length > 0) {
    r.push(`ユーザー操作間隔 TOP3: [${topGaps.join(", ")}]`);
  }
  r.push("");

  // --- タスク/ゴール ---
  r.push("--- タスク/ゴール ---");
  if (sessionMeta.queueCommand) {
    r.push(`初回コマンド: ${sessionMeta.queueCommand}`);
  }
  if (sessionMeta.firstUserMessage) {
    r.push(`初回ユーザーメッセージ: ${sessionMeta.firstUserMessage}`);
  }
  if (!sessionMeta.queueCommand && !sessionMeta.firstUserMessage) {
    r.push("  (取得できず)");
  }
  r.push("");

  if (subStatsList.length > 0) {
    r.push("--- サブエージェント別サマリー ---");
    for (const s of subStatsList) {
      const subTools = Object.values(s.toolNames).reduce((a, b) => a + b, 0);
      r.push(
        `  ${s.label}: entries=${s.totalLines}, tools=${subTools}, errors=${s.errorCount}, input_tokens=${s.totalInputTokens.toLocaleString()}, output_tokens=${s.totalOutputTokens.toLocaleString()}`
      );
    }
    r.push("");
  }

  r.push("--- 基本統計（メイン+サブエージェント合算） ---");
  r.push(`総エントリ数: ${totalLines}`);
  r.push(`  メイン: ${mainStats.totalLines}`);
  for (const s of subStatsList) {
    r.push(`  ${s.label}: ${s.totalLines}`);
  }
  r.push(`User発言数: ${userCount}`);
  r.push(`Assistant発言数: ${assistantCount}`);
  r.push("");

  r.push("--- トークン使用量（合算） ---");
  r.push(`input_tokens合計: ${totalInputTokens.toLocaleString()}`);
  r.push(`output_tokens合計: ${totalOutputTokens.toLocaleString()}`);
  r.push(`cache_read合計: ${totalCacheRead.toLocaleString()}`);
  r.push(`cache_creation合計: ${totalCacheCreation.toLocaleString()}`);
  r.push(`キャッシュ活用率: ${cacheRate.toFixed(1)}%`);
  if (ephemeral5mTokens > 0 || ephemeral1hTokens > 0) {
    r.push(`キャッシュ内訳 - 5分枠: ${ephemeral5mTokens.toLocaleString()}, 1時間枠: ${ephemeral1hTokens.toLocaleString()}`);
  }
  r.push(`input_tokens TOP5: [${inputTop5.join(", ")}]`);
  r.push(`output_tokens TOP5: [${outputTop5.join(", ")}]`);
  if (subStatsList.length > 0) {
    const subInput = subStatsList.reduce(
      (s, x) => s + x.totalInputTokens,
      0
    );
    const subOutput = subStatsList.reduce(
      (s, x) => s + x.totalOutputTokens,
      0
    );
    r.push(
      `うちサブエージェント: input=${subInput.toLocaleString()} / output=${subOutput.toLocaleString()}`
    );
  }
  r.push("");

  // --- ツール使用概要 ---
  r.push("--- ツール使用回数（上位15、合算） ---");
  for (const [name, count] of counterMostCommon(toolNames, 15)) {
    r.push(`  ${String(count).padStart(4)}  ${name}`);
  }
  r.push("");

  r.push("--- ツール分類 ---");
  const builtinTotal = Object.values(builtinToolNames).reduce((a, b) => a + b, 0);
  const mcpTotal = Object.values(mcpToolNames).reduce((a, b) => a + b, 0);
  r.push(`ビルトインツール: ${Object.keys(builtinToolNames).length}種 (計${builtinTotal}回)`);
  for (const [name, count] of counterMostCommon(builtinToolNames, 10)) {
    r.push(`  ${String(count).padStart(4)}  ${name}`);
  }
  if (mcpTotal > 0) {
    r.push(`MCPツール: ${Object.keys(mcpToolNames).length}種 (計${mcpTotal}回)`);
    for (const [name, count] of counterMostCommon(mcpToolNames, 10)) {
      r.push(`  ${String(count).padStart(4)}  ${name}`);
    }
  }
  if (subagentLaunches.length > 0) {
    r.push(`Agentツール起動: ${subagentLaunches.length}回`);
    for (let i = 0; i < subagentLaunches.length; i++) {
      const sa = subagentLaunches[i];
      const modelStr = sa.model ? ` model=${sa.model}` : "";
      r.push(`  [${i + 1}] type=${sa.type}${modelStr} desc="${sa.description}"`);
    }
  }
  if (skillInvocations.length > 0) {
    r.push(`Skillツール呼び出し: ${skillInvocations.length}回`);
    for (const si of skillInvocations) {
      r.push(`  skill="${si.skill}" args="${si.args}"`);
    }
  }
  r.push("");

  // ============================================================
  // 評価項目別データ（A〜F）
  // ============================================================

  r.push("--- A. 重複作業 ---");
  // ファイル重複読み込み
  r.push(`Read/View合計: ${totalReadView}`);
  r.push(`部分Read（offset/limit指定）: ${partialReadCount}回`);
  const partialRate = totalReadView > 0 ? (partialReadCount / totalReadView) * 100 : 0;
  r.push(`部分Read使用率: ${partialRate.toFixed(1)}%`);
  r.push("重複読み込み（2回以上）:");
  const dupSorted = Object.entries(dupReads).sort((a, b) => b[1] - a[1]);
  for (const [fp, c] of dupSorted) {
    r.push(`  ${String(c).padStart(3)}回  ${fp}`);
  }
  if (dupSorted.length === 0) r.push("  なし");
  // 同一ファイル書き直し（手戻り）
  r.push("同一ファイル書き込み3回以上（手戻り）:");
  const reworkSorted = Object.entries(reworkFiles).sort((a, b) => b[1] - a[1]);
  for (const [fp, c] of reworkSorted) {
    r.push(`  ${String(c).padStart(3)}回  ${fp}`);
  }
  if (reworkSorted.length === 0) r.push("  なし");
  // subagentとの重複Read
  if (subStatsList.length > 0) {
    r.push(`subagentとメインのRead重複: ${subagentMainOverlap.length}件`);
    for (const { file, subagent } of subagentMainOverlap.slice(0, 10)) {
      r.push(`  ${file} (${subagent}と重複)`);
    }
    if (subagentMainOverlap.length === 0) r.push("  なし");
  }
  r.push("");

  r.push("--- B. トークン効率 ---");
  r.push(`input_tokens TOP5: [${inputTop5.join(", ")}]`);
  r.push(`キャッシュ活用率: ${cacheRate.toFixed(1)}%`);
  r.push(`ツール結果合計文字数: ${totalToolResultChars.toLocaleString()}`);
  r.push(`大型ツール結果（10K+文字）: ${largeToolResults.length}件`);
  for (const { line, toolName, size } of largeToolResults.slice(0, 10)) {
    r.push(`  ${size.toLocaleString()}文字  ${toolName} (行${line})`);
  }
  if (durationSec > 0) {
    const tokensPerMin = Math.round((totalOutputTokens / durationSec) * 60);
    r.push(`output_tokens/分: ${tokensPerMin.toLocaleString()}`);
  }
  r.push("");

  r.push("--- C. 目的外作業（AI判定用データ） ---");
  r.push("Write/Edit対象ファイル一覧:");
  const allWriteEditFiles = counterMerge(writeFiles, editFiles);
  for (const [fp, c] of counterMostCommon(allWriteEditFiles, 30)) {
    r.push(`  ${String(c).padStart(3)}回  ${fp}`);
  }
  if (Object.keys(allWriteEditFiles).length === 0) r.push("  なし");
  r.push("生成ファイル拡張子:");
  for (const [ext, c] of counterMostCommon(writtenExtensions)) {
    r.push(`  ${String(c).padStart(3)}  ${ext}`);
  }
  r.push("");

  r.push("--- D. 初動の的確さ（メインセッション最初の15ツール） ---");
  for (const t of firstNTools) r.push(`  ${t}`);
  r.push("");

  r.push("--- E. エラー回復効率 ---");
  r.push(`エラー発生数: ${errorCount}`);
  r.push(`  メイン: ${mainStats.errorCount}`);
  for (const s of subStatsList) {
    if (s.errorCount > 0) r.push(`  ${s.label}: ${s.errorCount}`);
  }
  r.push(`エラー→同一ツール即リトライ: ${retryLoops.length}`);
  for (const { label, line, name, target } of retryLoops.slice(0, 10)) {
    const shortTarget = target ? target.slice(0, 80) : "";
    r.push(`  [${label}] 行${line}: ${name} → ${shortTarget}`);
  }
  r.push("");

  r.push("--- F. 不要な探索（AI判定用データ） ---");
  r.push("Read対象ファイル一覧:");
  for (const [fp, c] of counterMostCommon(combinedReads, 30)) {
    r.push(`  ${String(c).padStart(3)}回  ${fp}`);
  }
  r.push(`Glob使用回数: ${toolNames["Glob"] || 0}`);
  r.push(`Grep使用回数: ${toolNames["Grep"] || 0}`);
  // SKILL.mdを読んだが対応Skillを呼ばなかった
  r.push(`SKILL.md読み込み: ${skillReads.length}`);
  for (const fp of skillReads) r.push(`  ${fp}`);
  r.push(`Skillツール呼び出し: ${skillInvocations.length}`);
  for (const si of skillInvocations) r.push(`  ${si.skill}`);
  if (skillReadButNotUsed.length > 0) {
    r.push(`SKILL.md読み込み済みだがSkill未呼び出し: ${skillReadButNotUsed.length}件`);
    for (const name of skillReadButNotUsed) r.push(`  ${name}`);
  }
  r.push("");

  r.push("--- G. モデル選定の適切さ ---");
  r.push("セッション全体の使用モデル:");
  for (const [m, c] of modelEntries) {
    r.push(`  ${m}: ${c}回`);
  }
  // メインモデルの推定（最も使用回数の多いモデル）
  if (modelEntries.length > 0) {
    r.push(`メインモデル（最多使用）: ${modelEntries[0][0]}`);
  }
  // モデル別ツール使用内訳（どのモデルが何をしたか）
  const modelNames = Object.keys(modelToolUsage);
  if (modelNames.length > 0) {
    r.push("モデル別ツール使用内訳:");
    for (const model of modelNames) {
      const tools = counterMostCommon(modelToolUsage[model], 10);
      const totalTools = tools.reduce((s, [, c]) => s + c, 0);
      r.push(`  ${model} (ツール計${totalTools}回):`);
      for (const [tool, count] of tools) {
        r.push(`    ${String(count).padStart(4)}  ${tool}`);
      }
    }
  }
  // ユーザーが何を依頼したか（タスク内容の判断材料）
  const mainUserMsgs = mainStats.userMessages;
  if (mainUserMsgs.length > 0) {
    r.push(`ユーザー指示一覧（${mainUserMsgs.length}件）:`);
    for (let i = 0; i < mainUserMsgs.length; i++) {
      r.push(`  [${i + 1}] ${mainUserMsgs[i]}`);
    }
  }
  // サブエージェント: モデル指定とプロンプト内容
  if (subagentLaunches.length > 0) {
    r.push("サブエージェント別詳細:");
    for (let i = 0; i < subagentLaunches.length; i++) {
      const sa = subagentLaunches[i];
      const modelLabel = sa.model || "(親モデル継承)";
      r.push(`  [${i + 1}] type=${sa.type} model=${modelLabel}`);
      r.push(`       desc: ${sa.description}`);
      r.push(`       prompt: ${sa.promptSnippet}`);
    }
  }
  // タスクの複雑さを推定する数値指標
  r.push(`タスク複雑さ指標:`);
  r.push(`  総ターン数: ${mainStats.userCount + mainStats.assistantCount}`);
  r.push(`  Write/Edit対象ファイル数: ${Object.keys(writeFiles).length}`);
  r.push(`  サブエージェント起動数: ${subagentLaunches.length}`);
  r.push(`  エラー発生数: ${errorCount}`);
  r.push("");

  r.push("=".repeat(60));
  r.push("END OF REPORT");
  r.push("=".repeat(60));

  return r.join("\n");
}

/**
 * サブエージェントのみのフォルダを分析する。
 * folderPath: セッションIDフォルダ（subagents/ を含む）
 * analyzeSessionにダミーのメインパスを渡して、subagentsを自動検出させる。
 */
function analyzeSubagentsOnly(folderPath) {
  const sessionId = path.basename(folderPath);
  const dummyMainPath = path.join(
    path.dirname(folderPath),
    sessionId + ".jsonl",
  );
  // analyzeSessionはメインファイルが無くてもsubagentsがあればOK
  return analyzeSession(dummyMainPath);
}

/**
 * JONLファイルの先頭からentry.cwdを抽出して返す。
 * 対象プロジェクトのディレクトリパスとして使用する。
 */
function extractTargetCwd(sf) {
  try {
    const content = fs.readFileSync(sf, "utf-8");
    const lines = content.split("\n");
    for (let i = 0; i < Math.min(lines.length, 20); i++) {
      const trimmed = lines[i].trim();
      if (!trimmed) continue;
      try {
        const entry = JSON.parse(trimmed);
        if (entry.cwd) return entry.cwd;
      } catch { continue; }
    }
  } catch {}
  return null;
}

module.exports = { analyzeSession, analyzeSubagentsOnly, extractTargetCwd };
