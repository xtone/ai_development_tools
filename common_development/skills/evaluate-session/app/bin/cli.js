#!/usr/bin/env node

/**
 * Session Evaluator CLI
 * npx session-evaluator [--port PORT]
 */

const { createApp } = require("../src/server");

const DEFAULT_PORT = 5173;

function parseArgs() {
  const args = process.argv.slice(2);
  let port = DEFAULT_PORT;

  for (let i = 0; i < args.length; i++) {
    if ((args[i] === "--port" || args[i] === "-p") && args[i + 1]) {
      port = parseInt(args[i + 1], 10);
      if (isNaN(port) || port < 1 || port > 65535) {
        console.error(`Invalid port: ${args[i + 1]}`);
        process.exit(1);
      }
      i++;
    } else if (args[i] === "--help" || args[i] === "-h") {
      console.log(`
Session Evaluator - Claude Code セッション効率分析ツール

セッションログ（JSONL）を解析し、7 観点 100 点満点でスコアリングします。
「品質」ではなく「無駄の有無」に焦点を当てた評価で、セッション改善に役立ちます。

Usage:
  npx session-evaluator [options]

Options:
  -p, --port PORT  ポート番号を指定 (default: ${DEFAULT_PORT})
  -h, --help       このヘルプを表示

分析モード:
  Analyze    Claude CLI で AI 評価 + 統計レポート生成（要 claude コマンド）
  Stats Only 統計レポートのみ生成（Claude CLI 不要）

評価の 7 観点:
  A. 重複作業      /15  同一ファイル重複 Read・書き直し・subagent 重複
  B. トークン効率  /15  入力トークン異常値・キャッシュ活用率
  C. 目的外作業    /20  ユーザー指示と無関係なファイル操作
  D. 初動の的確さ  /15  タスクに適した初手を取れているか
  E. エラー回復    /10  原因分析なしの即リトライ
  F. 不要な探索    /15  目的外のファイル読み込み・過剰な検索
  G. モデル選定    /10  タスク複雑さに対して適切なモデルか

必要環境:
  Node.js 18+
  Claude CLI（Analyze モードのみ）
`);
      process.exit(0);
    }
  }

  return { port };
}

async function main() {
  const { port } = parseArgs();
  const app = createApp();

  const server = app.listen(port, () => {
    const url = `http://localhost:${port}`;
    console.log(`Session Evaluator running at ${url}`);

    // ブラウザを自動で開く
    import("open")
      .then((mod) => mod.default(url))
      .catch(() => {
        // open がなくてもサーバーは動く
        console.log(`Open ${url} in your browser`);
      });
  });

  server.on("error", (err) => {
    if (err.code === "EADDRINUSE") {
      console.error(`Port ${port} is already in use. Use --port to specify another port.`);
      process.exit(1);
    }
    throw err;
  });

  // Graceful shutdown
  for (const sig of ["SIGINT", "SIGTERM"]) {
    process.on(sig, () => {
      console.log("\nShutting down...");
      server.close(() => process.exit(0));
    });
  }
}

main();
