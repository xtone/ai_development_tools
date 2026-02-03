#!/usr/bin/env node

/**
 * Skill Usage Statistics Command
 *
 * スキル使用状況のサマリーを表示し、Notionデータベースへの同期をサポートするコマンド
 * 使用方法:
 *   skill-stats.js         - 統計を表示
 *   skill-stats.js reset   - ローカルデータをリセット
 *   skill-stats.js sync    - Notionへの同期情報を出力
 *
 * Reads data from ~/.claude/hooks/logs/
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const LOGS_DIR = path.join(os.homedir(), '.claude', 'hooks', 'logs');
const SKILL_EVENTS_FILE = path.join(LOGS_DIR, 'skill_usage.jsonl');
const COMMAND_EVENTS_FILE = path.join(LOGS_DIR, 'slash_command.jsonl');
const SYNC_STATE_FILE = path.join(LOGS_DIR, 'sync_state.json');

/**
 * Load events from JSONL file
 */
function loadEvents(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return content
        .trim()
        .split('\n')
        .filter(line => line)
        .map((line, index) => ({ ...JSON.parse(line), _lineNumber: index + 1 }));
    }
  } catch {
    // Ignore parse errors
  }
  return [];
}

/**
 * Load sync state
 */
function loadSyncState() {
  try {
    if (fs.existsSync(SYNC_STATE_FILE)) {
      return JSON.parse(fs.readFileSync(SYNC_STATE_FILE, 'utf8'));
    }
  } catch {
    // Ignore parse errors
  }
  return {
    skill_usage: { last_synced_line: 0 },
    slash_command: { last_synced_line: 0 }
  };
}

/**
 * Reset events data by emptying JSONL files
 */
function resetEventsData() {
  try {
    if (fs.existsSync(SKILL_EVENTS_FILE)) {
      fs.writeFileSync(SKILL_EVENTS_FILE, '', 'utf8');
      console.log('✓ Skill usage data reset');
    }
    if (fs.existsSync(COMMAND_EVENTS_FILE)) {
      fs.writeFileSync(COMMAND_EVENTS_FILE, '', 'utf8');
      console.log('✓ Command usage data reset');
    }
    console.log('\nAll usage statistics have been reset.');
  } catch (error) {
    console.error('Error resetting data:', error.message);
  }
}

/**
 * Convert skill event to Notion MCP format (SQLite-style)
 */
function convertSkillEventToNotionFormat(event) {
  return {
    'Skill': event.skill || '',
    'date:Timestamp:start': event.timestamp || new Date().toISOString(),
    'date:Timestamp:is_datetime': 1,
    'User Name': event.user?.name || '',
    'User Email': event.user?.email || '',
    'System User': event.user?.system_user || '',
    'Project': event.context?.project || '',
    'Branch': event.context?.branch || '',
    'Remote': event.context?.remote || '',
    'Hostname': event.context?.hostname || ''
  };
}

/**
 * Convert command event to Notion MCP format (SQLite-style)
 */
function convertCommandEventToNotionFormat(event) {
  return {
    'Command': event.command || '',
    'Full Command': event.full_command || '',
    'Source': event.source || 'user_prompt',
    'date:Timestamp:start': event.timestamp || new Date().toISOString(),
    'date:Timestamp:is_datetime': 1,
    'User Name': event.user?.name || '',
    'User Email': event.user?.email || '',
    'System User': event.user?.system_user || '',
    'Project': event.context?.project || '',
    'Branch': event.context?.branch || '',
    'Remote': event.context?.remote || '',
    'Hostname': event.context?.hostname || ''
  };
}

/**
 * Output sync information for Notion
 */
function outputSyncInfo() {
  const syncState = loadSyncState();

  console.log('\n🔄 Notion Sync Status');
  console.log('═'.repeat(60));

  // Load events
  const skillEvents = loadEvents(SKILL_EVENTS_FILE);
  const commandEvents = loadEvents(COMMAND_EVENTS_FILE);

  // Filter unsynced events
  const unsyncedSkillEvents = skillEvents.filter(
    e => e._lineNumber > syncState.skill_usage.last_synced_line
  );
  const unsyncedCommandEvents = commandEvents.filter(
    e => e._lineNumber > syncState.slash_command.last_synced_line
  );

  console.log(`\n📊 同期状態:`);
  console.log(`  Skill Events: ${unsyncedSkillEvents.length} 件の未同期イベント`);
  console.log(`    (Total: ${skillEvents.length}, Synced: ${syncState.skill_usage.last_synced_line})`);
  console.log(`  Command Events: ${unsyncedCommandEvents.length} 件の未同期イベント`);
  console.log(`    (Total: ${commandEvents.length}, Synced: ${syncState.slash_command.last_synced_line})`);

  if (unsyncedSkillEvents.length === 0 && unsyncedCommandEvents.length === 0) {
    console.log('\n✓ すべてのイベントが同期済みです。');
    return;
  }

  // Output sync data
  console.log('\n--- Sync Data ---');
  console.log(JSON.stringify({
    action: 'sync',
    sync_state_file: SYNC_STATE_FILE,
    current_sync_state: syncState,
    skill_usage_events: unsyncedSkillEvents.map(e => {
      const { _lineNumber, ...event } = e;
      return {
        line_number: _lineNumber,
        notion_properties: convertSkillEventToNotionFormat(event)
      };
    }),
    slash_command_events: unsyncedCommandEvents.map(e => {
      const { _lineNumber, ...event } = e;
      return {
        line_number: _lineNumber,
        notion_properties: convertCommandEventToNotionFormat(event)
      };
    }),
    new_sync_state: {
      skill_usage: {
        last_synced_line: skillEvents.length
      },
      slash_command: {
        last_synced_line: commandEvents.length
      }
    }
  }, null, 2));
  console.log('--- End Sync Data ---');
}

/**
 * Display usage statistics
 */
function displayStats() {
  const skillEvents = loadEvents(SKILL_EVENTS_FILE);
  const commandEvents = loadEvents(COMMAND_EVENTS_FILE);

  const hasSkillEvents = skillEvents.length > 0;
  const hasCommandEvents = commandEvents.length > 0;

  if (!hasSkillEvents && !hasCommandEvents) {
    console.log('使用データがありません');
    return;
  }

  // Skill usage summary
  if (hasSkillEvents) {
    const skills = {};
    for (const event of skillEvents) {
      skills[event.skill] = (skills[event.skill] || 0) + 1;
    }

    console.log('\n📊 Skill Usage Summary');
    console.log('─'.repeat(40));

    const sorted = Object.entries(skills).sort((a, b) => b[1] - a[1]);
    for (const [skill, count] of sorted) {
      console.log(`  ${skill}: ${count}`);
    }

    console.log('─'.repeat(40));
    console.log(`  Total: ${skillEvents.length} invocations`);
    console.log(`  Data: ${SKILL_EVENTS_FILE}`);
  }

  // Command usage summary
  if (hasCommandEvents) {
    const commands = {};
    for (const event of commandEvents) {
      commands[event.command] = (commands[event.command] || 0) + 1;
    }

    console.log('\n📋 Slash Command Usage Summary');
    console.log('─'.repeat(40));

    const sorted = Object.entries(commands).sort((a, b) => b[1] - a[1]);
    for (const [command, count] of sorted) {
      console.log(`  /${command}: ${count}`);
    }

    console.log('─'.repeat(40));
    console.log(`  Total: ${commandEvents.length} invocations`);
    console.log(`  Data: ${COMMAND_EVENTS_FILE}`);
  }
}

function main() {
  const args = process.argv.slice(2);

  if (args.includes('reset')) {
    resetEventsData();
    return;
  }

  if (args.includes('sync')) {
    outputSyncInfo();
    return;
  }

  displayStats();
}

main();
