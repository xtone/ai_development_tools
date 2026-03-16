/**
 * プロジェクト/セッション検出モジュール
 * ~/.claude/projects/ からプロジェクト一覧・セッション一覧を取得し、
 * 各セッションの最初のユーザー発言を抽出する。
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const readline = require("readline");

const CLAUDE_PROJECTS_DIR = path.join(os.homedir(), ".claude", "projects");

/**
 * エンコードされたプロジェクトディレクトリ名をデコードする。
 * Claude Code はパスの区切り文字（/ \ :）をすべて '-' に変換する。
 * 例: 'C:\\tools\\session-evaluator' → 'C--tools-session-evaluator'
 */
function decodeProjectPath(encodedName) {
  if (!encodedName) return encodedName;

  const segments = encodedName.split("-");

  // Windows ドライブレター判定
  if (
    segments.length >= 2 &&
    segments[0].length === 1 &&
    /^[a-zA-Z]$/.test(segments[0])
  ) {
    const drive = segments[0];
    let remaining;
    let root;
    if (segments[1] === "") {
      // 'C--tools-session-evaluator' → ['C', '', 'tools', 'session', 'evaluator']
      remaining = segments.slice(2);
      root = `${drive}:/`;
    } else {
      remaining = segments.slice(1);
      root = `${drive}:/`;
    }
    return rebuildPath(root, remaining);
  } else if (segments[0] === "") {
    // Mac/Linux 絶対パス: '-Users-alice-...'
    const remaining = segments.slice(1);
    return rebuildPath("/", remaining);
  }

  return encodedName;
}

/**
 * セグメント列からファイルシステム上で実在するパスを貪欲法で再構築する。
 */
function rebuildPath(root, segments) {
  if (!segments.length) return root;

  let current = root;
  let i = 0;

  while (i < segments.length) {
    if (segments[i] === "") {
      i++;
      continue;
    }

    let found = false;
    for (let end = segments.length; end > i; end--) {
      const candidate = segments.slice(i, end).join("-");
      const testPath = path.join(current, candidate);
      try {
        if (fs.existsSync(testPath)) {
          current = testPath;
          i = end;
          found = true;
          break;
        }
      } catch {
        // ignore
      }
    }

    if (!found) {
      const remaining = segments.slice(i).join("-");
      return path.join(current, remaining).replace(/\\/g, "/");
    }
  }

  return current.replace(/\\/g, "/");
}

/**
 * プロジェクトディレクトリ名（エンコード済み）のリストを返す。
 * 更新日時が新しい順にソート。
 */
function getProjects() {
  if (!fs.existsSync(CLAUDE_PROJECTS_DIR)) return [];

  const dirs = [];
  for (const entry of fs.readdirSync(CLAUDE_PROJECTS_DIR, {
    withFileTypes: true,
  })) {
    if (!entry.isDirectory()) continue;

    const dirPath = path.join(CLAUDE_PROJECTS_DIR, entry.name);
    try {
      const jsonlFiles = fs
        .readdirSync(dirPath)
        .filter((f) => f.endsWith(".jsonl"));
      if (jsonlFiles.length > 0) {
        let latestMtime = 0;
        for (const jf of jsonlFiles) {
          const st = fs.statSync(path.join(dirPath, jf));
          if (st.mtimeMs > latestMtime) latestMtime = st.mtimeMs;
        }
        dirs.push({ name: entry.name, mtime: latestMtime });
      }
    } catch {
      dirs.push({ name: entry.name, mtime: 0 });
    }
  }

  dirs.sort((a, b) => b.mtime - a.mtime);
  return dirs.map((d) => d.name);
}

/**
 * セッションの合計サイズ（メイン + サブエージェント）を返す。
 */
function getSessionTotalSize(jsonlPath) {
  let total = fs.statSync(jsonlPath).size;

  const stem = path.basename(jsonlPath, ".jsonl");
  const subagentDir = path.join(path.dirname(jsonlPath), stem, "subagents");
  if (fs.existsSync(subagentDir)) {
    for (const f of fs.readdirSync(subagentDir)) {
      if (f.startsWith("agent-") && f.endsWith(".jsonl")) {
        try {
          total += fs.statSync(path.join(subagentDir, f)).size;
        } catch {
          // ignore
        }
      }
    }
  }

  return total;
}

/**
 * JSONLの先頭数行から最初のユーザー発言を抽出する。
 */
function extractFirstUserMessage(jsonlPath, maxLines = 50) {
  try {
    const content = fs.readFileSync(jsonlPath, "utf-8");
    const lines = content.split("\n");
    for (let i = 0; i < Math.min(lines.length, maxLines); i++) {
      const line = lines[i].trim();
      if (!line) continue;
      try {
        const entry = JSON.parse(line);
        if (entry.type === "user") {
          const msg = entry.message || {};
          const c = msg.content;
          if (typeof c === "string" && c.trim()) {
            let text = c.trim().replace(/\n/g, " ");
            if (text.length > 100) text = text.slice(0, 100) + "...";
            return text;
          }
        }
      } catch {
        continue;
      }
    }
  } catch {
    // ignore
  }
  return "(no message)";
}

/**
 * プロジェクト内のセッション一覧を返す。更新日時が新しい順。
 */
function getSessions(projectEncoded) {
  const projectDir = path.join(CLAUDE_PROJECTS_DIR, projectEncoded);
  if (!fs.existsSync(projectDir)) return [];

  const decodedName = decodeProjectPath(projectEncoded);
  const sessions = [];

  for (const f of fs.readdirSync(projectDir)) {
    if (!f.endsWith(".jsonl")) continue;
    const fullPath = path.join(projectDir, f);

    // subagentsディレクトリ内のファイルは除外
    if (fullPath.includes("subagents")) continue;

    try {
      const stat = fs.statSync(fullPath);
      const totalSize = getSessionTotalSize(fullPath);
      const firstMsg = extractFirstUserMessage(fullPath);
      sessions.push({
        sessionId: path.basename(f, ".jsonl"),
        jsonlPath: fullPath,
        modified: new Date(stat.mtimeMs),
        totalSizeBytes: totalSize,
        firstMessage: firstMsg,
        projectName: decodedName,
      });
    } catch {
      continue;
    }
  }

  sessions.sort((a, b) => b.modified - a.modified);
  return sessions;
}

/**
 * 最新のセッションを取得。プロジェクト指定なしなら全プロジェクトから。
 */
function findLatestSession(projectEncoded = null) {
  if (projectEncoded) {
    const sessions = getSessions(projectEncoded);
    return sessions.length > 0 ? sessions[0] : null;
  }

  const allSessions = [];
  for (const proj of getProjects()) {
    allSessions.push(...getSessions(proj));
  }

  if (!allSessions.length) return null;
  allSessions.sort((a, b) => b.modified - a.modified);
  return allSessions[0];
}

/**
 * バイト数を人間が読みやすい形式に変換する。
 */
function formatSize(sizeBytes) {
  if (sizeBytes < 1024) return `${sizeBytes}B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)}KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)}MB`;
}

module.exports = {
  CLAUDE_PROJECTS_DIR,
  decodeProjectPath,
  getProjects,
  getSessions,
  findLatestSession,
  formatSize,
  extractFirstUserMessage,
};
