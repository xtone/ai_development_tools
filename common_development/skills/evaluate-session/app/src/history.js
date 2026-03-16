/**
 * 評価履歴の保存/読み込みモジュール
 * ~/.claude/session-evaluator-history.json に評価結果を永続化する。
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

const HISTORY_FILE = path.join(
  os.homedir(),
  ".claude",
  "session-evaluator-history.json"
);

function loadRaw() {
  if (fs.existsSync(HISTORY_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(HISTORY_FILE, "utf-8"));
    } catch {
      return { evaluations: [] };
    }
  }
  return { evaluations: [] };
}

function saveRaw(data) {
  const dir = path.dirname(HISTORY_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(data, null, 2), "utf-8");
}

/**
 * 評価結果を履歴ファイルに追記する。
 */
function saveEvaluation(record) {
  const data = loadRaw();
  data.evaluations.push(record);
  saveRaw(data);
}

/**
 * 履歴ファイルから全評価結果を読み込む。新しい順に返す。
 */
function loadEvaluations() {
  const data = loadRaw();
  const records = (data.evaluations || []).slice();
  records.reverse();
  return records;
}

/**
 * 新しい順のインデックスで指定した評価を削除する。
 */
function deleteEvaluation(indexFromNewest) {
  const data = loadRaw();
  const evals = data.evaluations || [];
  if (!evals.length) return;
  const actualIndex = evals.length - 1 - indexFromNewest;
  if (actualIndex >= 0 && actualIndex < evals.length) {
    evals.splice(actualIndex, 1);
    data.evaluations = evals;
    saveRaw(data);
  }
}

module.exports = { saveEvaluation, loadEvaluations, deleteEvaluation };
