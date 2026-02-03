#!/usr/bin/env node

/**
 * Skill Usage Statistics Command
 *
 * スキル使用状況のサマリーを表示し、Notionデータベースへの同期をサポートするコマンド
 * 使用方法:
 *   skill-stats.js         - 統計を表示
 *   skill-stats.js reset   - ローカルデータをリセット
 *   skill-stats.js setup   - Notion同期の初期設定情報を出力
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
const NOTION_CONFIG_FILE = path.join(LOGS_DIR, 'notion_config.json');

const DEFAULT_PARENT_PAGE_ID = '2fcceb782fa380b396eecc76182a52fa';

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
 * Load Notion config
 */
function loadNotionConfig() {
  try {
    if (fs.existsSync(NOTION_CONFIG_FILE)) {
      return JSON.parse(fs.readFileSync(NOTION_CONFIG_FILE, 'utf8'));
    }
  } catch {
    // Ignore parse errors
  }
  return null;
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
 * Output setup information for Notion integration
 */
function outputSetupInfo() {
  const config = loadNotionConfig();

  console.log('\n🔧 Notion Sync Setup');
  console.log('═'.repeat(60));

  if (config) {
    console.log('\n✓ 設定済み');
    console.log(`  Config file: ${NOTION_CONFIG_FILE}`);
    console.log(`  Parent Page ID: ${config.parent_page_id}`);
    console.log(`  Skill Usage DB ID: ${config.skill_usage_db_id || '未設定'}`);
    console.log(`  Slash Command DB ID: ${config.slash_command_db_id || '未設定'}`);
    return;
  }

  console.log('\n⚠ 未設定: Notionデータベースの作成が必要です');
  console.log('\n--- Setup Information ---');
  console.log(JSON.stringify({
    action: 'setup',
    parent_page_id: DEFAULT_PARENT_PAGE_ID,
    config_file_path: NOTION_CONFIG_FILE,
    databases_to_create: [
      {
        name: 'Skill Usage Events',
        config_key: 'skill_usage_db_id',
        properties: {
          'Skill': { title: {} },
          'Timestamp': { date: {} },
          'User Name': { rich_text: {} },
          'User Email': { email: {} },
          'System User': { rich_text: {} },
          'Project': { rich_text: {} },
          'Branch': { rich_text: {} },
          'Remote': { url: {} },
          'Hostname': { rich_text: {} }
        }
      },
      {
        name: 'Slash Command Events',
        config_key: 'slash_command_db_id',
        properties: {
          'Command': { title: {} },
          'Full Command': { rich_text: {} },
          'Source': { select: { options: [{ name: 'user_prompt' }, { name: 'slash_command_tool' }] } },
          'Timestamp': { date: {} },
          'User Name': { rich_text: {} },
          'User Email': { email: {} },
          'System User': { rich_text: {} },
          'Project': { rich_text: {} },
          'Branch': { rich_text: {} },
          'Remote': { url: {} },
          'Hostname': { rich_text: {} }
        }
      }
    ]
  }, null, 2));
  console.log('--- End Setup Information ---');

  console.log('\n📝 セットアップ手順:');
  console.log('1. 上記の情報を使用してNotionデータベースを作成');
  console.log('2. 作成したデータベースIDを notion_config.json に保存');
  console.log(`3. 設定ファイルのパス: ${NOTION_CONFIG_FILE}`);
}

/**
 * Output sync information for Notion
 */
function outputSyncInfo() {
  const config = loadNotionConfig();
  const syncState = loadSyncState();

  console.log('\n🔄 Notion Sync Status');
  console.log('═'.repeat(60));

  if (!config) {
    console.log('\n⚠ Notion設定が見つかりません。先に `/skill-stats setup` を実行してください。');
    return;
  }

  if (!config.skill_usage_db_id || !config.slash_command_db_id) {
    console.log('\n⚠ データベースIDが設定されていません。');
    console.log('notion_config.json に skill_usage_db_id と slash_command_db_id を設定してください。');
    return;
  }

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
    config: {
      skill_usage_db_id: config.skill_usage_db_id,
      slash_command_db_id: config.slash_command_db_id
    },
    sync_state_file: SYNC_STATE_FILE,
    current_sync_state: syncState,
    skill_usage_events: unsyncedSkillEvents.map(e => {
      const { _lineNumber, ...event } = e;
      return {
        line_number: _lineNumber,
        data: event,
        notion_properties: {
          'Skill': { title: [{ text: { content: event.skill || '' } }] },
          'Timestamp': { date: { start: event.timestamp || new Date().toISOString() } },
          'User Name': { rich_text: [{ text: { content: event.user?.name || '' } }] },
          'User Email': { email: event.user?.email || null },
          'System User': { rich_text: [{ text: { content: event.user?.system_user || '' } }] },
          'Project': { rich_text: [{ text: { content: event.context?.project || '' } }] },
          'Branch': { rich_text: [{ text: { content: event.context?.branch || '' } }] },
          'Remote': { url: event.context?.remote || null },
          'Hostname': { rich_text: [{ text: { content: event.context?.hostname || '' } }] }
        }
      };
    }),
    slash_command_events: unsyncedCommandEvents.map(e => {
      const { _lineNumber, ...event } = e;
      return {
        line_number: _lineNumber,
        data: event,
        notion_properties: {
          'Command': { title: [{ text: { content: event.command || '' } }] },
          'Full Command': { rich_text: [{ text: { content: event.full_command || '' } }] },
          'Source': { select: { name: event.source || 'user_prompt' } },
          'Timestamp': { date: { start: event.timestamp || new Date().toISOString() } },
          'User Name': { rich_text: [{ text: { content: event.user?.name || '' } }] },
          'User Email': { email: event.user?.email || null },
          'System User': { rich_text: [{ text: { content: event.user?.system_user || '' } }] },
          'Project': { rich_text: [{ text: { content: event.context?.project || '' } }] },
          'Branch': { rich_text: [{ text: { content: event.context?.branch || '' } }] },
          'Remote': { url: event.context?.remote || null },
          'Hostname': { rich_text: [{ text: { content: event.context?.hostname || '' } }] }
        }
      };
    }),
    new_sync_state: {
      skill_usage: {
        last_synced_line: skillEvents.length,
        notion_db_id: config.skill_usage_db_id
      },
      slash_command: {
        last_synced_line: commandEvents.length,
        notion_db_id: config.slash_command_db_id
      }
    }
  }, null, 2));
  console.log('--- End Sync Data ---');

  console.log('\n📝 同期手順:');
  console.log('1. 上記の sync data を使用して mcp__notion__notion-create-pages でページを作成');
  console.log('2. 同期完了後、sync_state.json を new_sync_state の内容で更新');
  console.log(`3. 状態ファイルのパス: ${SYNC_STATE_FILE}`);
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

  if (args.includes('setup')) {
    outputSetupInfo();
    return;
  }

  if (args.includes('sync')) {
    outputSyncInfo();
    return;
  }

  displayStats();
}

main();
