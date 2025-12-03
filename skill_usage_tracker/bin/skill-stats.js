#!/usr/bin/env node

/**
 * Skill Usage Statistics Command
 *
 * スキル使用状況のサマリーを表示するコマンド
 * 使用方法: skill-stats.js
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const EVENTS_FILE = path.join(os.homedir(), '.claude', 'hooks', 'state', 'skill_usage_events.json');

function main() {
  // ファイルが存在するか確認
  if (!fs.existsSync(EVENTS_FILE)) {
    console.log('スキル使用データがありません');
    console.log(`(${EVENTS_FILE} が見つかりません)`);
    return;
  }

  // データを読み込む
  let data;
  try {
    const content = fs.readFileSync(EVENTS_FILE, 'utf8');
    data = JSON.parse(content);
  } catch (error) {
    console.log('データの解析に失敗しました:', error.message);
    return;
  }

  // イベントがあるか確認
  if (!data.events || data.events.length === 0) {
    console.log('スキル使用データがありません');
    return;
  }

  // スキルごとにカウント
  const skills = {};
  for (const event of data.events) {
    skills[event.skill] = (skills[event.skill] || 0) + 1;
  }

  // サマリーを表示
  console.log('\n📊 Skill Usage Summary');
  console.log('─'.repeat(40));

  const sorted = Object.entries(skills).sort((a, b) => b[1] - a[1]);
  for (const [skill, count] of sorted) {
    console.log(`  ${skill}: ${count}`);
  }

  console.log('─'.repeat(40));
  console.log(`  Total: ${data.events.length} invocations`);
  console.log(`  Data: ${EVENTS_FILE}`);
}

main();
