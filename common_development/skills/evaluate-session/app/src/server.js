/**
 * Express Web Server
 * API routes + static file serving
 */

const express = require("express");
const path = require("path");
const fs = require("fs");
const os = require("os");
const { execSync } = require("child_process");
const sessionFinder = require("./session-finder");
const analyzer = require("./analyzer");
const evaluator = require("./evaluator");
const history = require("./history");

/**
 * パストラバーサル防止: ~/.claude/ 配下のパスのみ許可
 */
function validatePath(targetPath) {
  const allowedBase = path.join(os.homedir(), ".claude");
  const resolved = path.resolve(targetPath);
  return resolved.startsWith(allowedBase + path.sep) || resolved === allowedBase;
}

function createApp() {
  const app = express();
  app.use(express.json());
  app.use(express.static(path.join(__dirname, "..", "public")));

  // --- API Routes ---

  // プロジェクト一覧
  app.get("/api/projects", (req, res) => {
    try {
      const projects = sessionFinder.getProjects();
      const result = projects.map((encoded) => ({
        encoded,
        decoded: sessionFinder.decodeProjectPath(encoded),
      }));
      res.json(result);
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // セッション一覧
  app.get("/api/sessions/:projectEncoded", (req, res) => {
    try {
      const projectsDir = path.join(os.homedir(), ".claude", "projects");
      const resolved = path.resolve(projectsDir, req.params.projectEncoded);
      if (!resolved.startsWith(projectsDir + path.sep) && resolved !== projectsDir) {
        return res.status(403).json({ error: "Access denied: invalid project path" });
      }
      const sessions = sessionFinder.getSessions(req.params.projectEncoded);
      const result = sessions.map((s) => ({
        sessionId: s.sessionId,
        jsonlPath: s.jsonlPath,
        modified: s.modified.toISOString(),
        totalSizeBytes: s.totalSizeBytes,
        formattedSize: sessionFinder.formatSize(s.totalSizeBytes),
        firstMessage: s.firstMessage,
        projectName: s.projectName,
      }));
      res.json(result);
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // 統計分析のみ (jsonlPath or folderPath)
  app.post("/api/analyze", (req, res) => {
    const { jsonlPath, folderPath } = req.body;
    if (!jsonlPath && !folderPath) {
      return res.status(400).json({ error: "jsonlPath or folderPath is required" });
    }
    if (jsonlPath && !validatePath(jsonlPath)) {
      return res.status(403).json({ error: "Access denied: path must be under ~/.claude/" });
    }
    if (folderPath && !validatePath(folderPath)) {
      return res.status(403).json({ error: "Access denied: path must be under ~/.claude/" });
    }
    try {
      const statsText = folderPath
        ? analyzer.analyzeSubagentsOnly(folderPath)
        : analyzer.analyzeSession(jsonlPath);
      res.json({ statsText });
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // 統計 + Claude 評価 (jsonlPath or folderPath)
  app.post("/api/evaluate", async (req, res) => {
    const { jsonlPath, folderPath, model, sessionId, projectName } = req.body;
    if (!jsonlPath && !folderPath) {
      return res.status(400).json({ error: "jsonlPath or folderPath is required" });
    }
    if (jsonlPath && !validatePath(jsonlPath)) {
      return res.status(403).json({ error: "Access denied: path must be under ~/.claude/" });
    }
    if (folderPath && !validatePath(folderPath)) {
      return res.status(403).json({ error: "Access denied: path must be under ~/.claude/" });
    }

    try {
      const statsText = folderPath
        ? analyzer.analyzeSubagentsOnly(folderPath)
        : analyzer.analyzeSession(jsonlPath);

      // 対象プロジェクトのCWDを取得（Claude CLIをそのディレクトリで実行するため）
      const targetCwd = analyzer.extractTargetCwd(jsonlPath || folderPath);

      let evalResult;
      try {
        evalResult = await evaluator.runEvaluation(statsText, model || null, targetCwd);
      } catch (e) {
        // 評価エラーでも統計は返す
        return res.json({
          statsText,
          evalResult: null,
          evalError: e.message,
          score: null,
        });
      }

      const score = evaluator.extractTotalScore(evalResult);

      // statsTextから初回ユーザーメッセージを抽出
      const taskMatch = statsText.match(/初回ユーザーメッセージ: (.+)/);
      const taskSummary = taskMatch ? taskMatch[1].trim().slice(0, 200) : "";

      // 履歴保存
      history.saveEvaluation({
        timestamp: new Date().toISOString(),
        session_id: sessionId || path.basename(jsonlPath, ".jsonl"),
        project: projectName || "",
        task_summary: taskSummary,
        stats_summary: statsText.slice(0, 500),
        stats_text: statsText,
        evaluation_result: evalResult,
        result_text: `=== EVALUATION ===\n\n${evalResult}\n\n=== STATISTICS ===\n\n${statsText}`,
        score_total: score,
      });

      res.json({ statsText, evalResult, score });
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // 最新セッション取得
  app.get("/api/latest-session", (req, res) => {
    const { project } = req.query;
    try {
      const session = sessionFinder.findLatestSession(project || null);
      if (!session) {
        return res.json(null);
      }
      res.json({
        sessionId: session.sessionId,
        jsonlPath: session.jsonlPath,
        modified: session.modified.toISOString(),
        totalSizeBytes: session.totalSizeBytes,
        formattedSize: sessionFinder.formatSize(session.totalSizeBytes),
        firstMessage: session.firstMessage,
        projectName: session.projectName,
      });
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // 履歴一覧
  app.get("/api/history", (req, res) => {
    try {
      const records = history.loadEvaluations();
      res.json(records);
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // 履歴削除
  app.delete("/api/history/:index", (req, res) => {
    try {
      const idx = parseInt(req.params.index, 10);
      history.deleteEvaluation(idx);
      res.json({ ok: true });
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  // OSのフォルダ選択ダイアログでセッションフォルダを選択
  app.post("/api/open-folder-dialog", (req, res) => {
    try {
      // PowerShellでFolderBrowserDialogを表示
      const psScript = `
Add-Type -AssemblyName System.Windows.Forms
$d = New-Object System.Windows.Forms.FolderBrowserDialog
$d.Description = 'Select Session Folder'
$d.RootFolder = 'MyComputer'
$d.SelectedPath = [System.IO.Path]::Combine($env:USERPROFILE, '.claude', 'projects')
if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath } else { '' }
`.trim();
      const result = execSync(
        `powershell -NoProfile -Command "${psScript.replace(/\n/g, "; ")}"`,
        { encoding: "utf-8", timeout: 120000 },
      ).trim();

      if (!result) {
        return res.json({ cancelled: true });
      }

      const folderPath = result;

      // フォルダ内からメインJSONLファイルを探す
      // パターン1: フォルダ自体がセッションIDフォルダ → 親にsessionId.jsonlがある
      const folderName = path.basename(folderPath);
      const parentJsonl = path.join(path.dirname(folderPath), folderName + ".jsonl");

      if (fs.existsSync(parentJsonl)) {
        // 親ディレクトリにメインJSONLがある場合（セッションIDフォルダを選んだ）
        return res.json({
          cancelled: false,
          jsonlPath: parentJsonl,
          sessionId: folderName,
          projectName: path.basename(path.dirname(path.dirname(folderPath))),
        });
      }

      // パターン2: フォルダ直下に.jsonlファイルがある（プロジェクトフォルダを選んだ等）
      const jsonlFiles = fs.readdirSync(folderPath)
        .filter((f) => f.endsWith(".jsonl"))
        .sort();

      if (jsonlFiles.length > 0) {
        // 最初の（or 最新の）jsonlをメインとして使う
        const mainJsonl = path.join(folderPath, jsonlFiles[0]);
        return res.json({
          cancelled: false,
          jsonlPath: mainJsonl,
          sessionId: path.basename(mainJsonl, ".jsonl"),
          projectName: path.basename(folderPath),
        });
      }

      // パターン3: subagentsフォルダのみ存在する
      const subagentsDir = path.join(folderPath, "subagents");
      if (fs.existsSync(subagentsDir)) {
        const agentFiles = fs.readdirSync(subagentsDir)
          .filter((f) => f.startsWith("agent-") && f.endsWith(".jsonl"));
        if (agentFiles.length > 0) {
          return res.json({
            cancelled: false,
            jsonlPath: null,
            folderPath,
            sessionId: folderName,
            projectName: path.basename(path.dirname(folderPath)),
            subagentsOnly: true,
          });
        }
      }

      res.json({ cancelled: false, error: "No .jsonl files found in selected folder" });
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });

  return app;
}

module.exports = { createApp };
