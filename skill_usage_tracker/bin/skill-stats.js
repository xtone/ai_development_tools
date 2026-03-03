#!/usr/bin/env node

/**
 * Skill Usage Statistics Command
 *
 * スキル使用状況のサマリーを表示し、Notionデータベースへの同期をサポートするコマンド
 * 使用方法:
 *   skill-stats.js                              - 統計を表示
 *   skill-stats.js reset --force               - ローカルデータをリセット（バックアップ作成）
 *   skill-stats.js sync                         - Notionへの同期情報を出力
 *   skill-stats.js setup <skill_db> <cmd_db>   - Notion設定ファイルを作成
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

// Warning threshold for large data sets
const MAX_EVENTS_WARNING = 1000;

/**
 * Load events from JSONL file with improved error handling
 */
function loadEvents(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return content
        .trim()
        .split('\n')
        .filter(line => line)
        .map((line, index) => {
          try {
            return { ...JSON.parse(line), _lineNumber: index + 1 };
          } catch (error) {
            console.error(`Warning: Failed to parse line ${index + 1} in ${filePath}: ${error.message}`);
            return null;
          }
        })
        .filter(event => event !== null);
    }
  } catch (error) {
    console.error(`Error loading ${filePath}: ${error.message}`);
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
 * Ensure logs directory exists
 */
function ensureLogsDirectory() {
  if (!fs.existsSync(LOGS_DIR)) {
    fs.mkdirSync(LOGS_DIR, { recursive: true });
  }
}

/**
 * Setup Notion config file
 */
function setupNotionConfig(args) {
  // Parse arguments: setup <skill_db_id> <command_db_id>
  const setupIndex = args.indexOf('setup');
  const skillDbId = args[setupIndex + 1];
  const commandDbId = args[setupIndex + 2];

  console.log('\n🔧 Notion Sync Setup');
  console.log('═'.repeat(60));

  // Check existing config
  const existingConfig = loadNotionConfig();
  if (existingConfig) {
    console.log('\n現在の設定:');
    console.log(`  設定ファイル: ${NOTION_CONFIG_FILE}`);
    console.log(`  Skill Usage DB: ${existingConfig.skill_usage_db_id || '未設定'}`);
    console.log(`  Slash Command DB: ${existingConfig.slash_command_db_id || '未設定'}`);
  }

  if (!skillDbId || !commandDbId) {
    console.log('\n使用方法:');
    console.log('  skill-stats.js setup <skill_usage_db_id> <slash_command_db_id>');
    console.log('\n例:');
    console.log('  skill-stats.js setup b787567d-9565-49ac-89d4-fd2569497d15 a24187ec-c81b-4853-a6ae-d8139abffc0b');
    console.log('\ndata_source_id は Notion MCP の mcp__notion__notion-fetch で取得できます。');
    return;
  }

  // Validate UUID format (simple check)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(skillDbId)) {
    console.error(`\n⚠ 無効な skill_usage_db_id: ${skillDbId}`);
    console.error('UUID形式 (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) で指定してください。');
    return;
  }
  if (!uuidRegex.test(commandDbId)) {
    console.error(`\n⚠ 無効な slash_command_db_id: ${commandDbId}`);
    console.error('UUID形式 (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) で指定してください。');
    return;
  }

  // Create config
  const config = {
    skill_usage_db_id: skillDbId,
    slash_command_db_id: commandDbId
  };

  try {
    ensureLogsDirectory();
    fs.writeFileSync(NOTION_CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
    console.log('\n✓ 設定ファイルを作成しました');
    console.log(`  ファイル: ${NOTION_CONFIG_FILE}`);
    console.log(`  Skill Usage DB: ${skillDbId}`);
    console.log(`  Slash Command DB: ${commandDbId}`);
    console.log('\n/skill-stats sync で同期を開始できます。');
  } catch (error) {
    console.error(`\n⚠ 設定ファイルの作成に失敗しました: ${error.message}`);
  }
}

/**
 * Reset events data by emptying JSONL files (with backup)
 */
function resetEventsData(options = {}) {
  if (!options.force) {
    console.log('\n⚠ Warning: This will delete all usage data.');
    console.log('Use --force to confirm: /skill-stats reset --force');
    console.log('\nA backup will be created before deletion.');
    return;
  }

  // Create backup before reset
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupDir = path.join(LOGS_DIR, 'backups');

  try {
    // Ensure backup directory exists
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
    }

    // Backup and reset skill events
    if (fs.existsSync(SKILL_EVENTS_FILE)) {
      const stat = fs.statSync(SKILL_EVENTS_FILE);
      if (stat.size > 0) {
        const backupFile = path.join(backupDir, `skill_usage_${timestamp}.jsonl`);
        fs.copyFileSync(SKILL_EVENTS_FILE, backupFile);
        fs.writeFileSync(SKILL_EVENTS_FILE, '', 'utf8');
        console.log(`✓ Skill usage data reset (backup: ${backupFile})`);
      } else {
        console.log('✓ Skill usage data already empty');
      }
    }

    // Backup and reset command events
    if (fs.existsSync(COMMAND_EVENTS_FILE)) {
      const stat = fs.statSync(COMMAND_EVENTS_FILE);
      if (stat.size > 0) {
        const backupFile = path.join(backupDir, `slash_command_${timestamp}.jsonl`);
        fs.copyFileSync(COMMAND_EVENTS_FILE, backupFile);
        fs.writeFileSync(COMMAND_EVENTS_FILE, '', 'utf8');
        console.log(`✓ Command usage data reset (backup: ${backupFile})`);
      } else {
        console.log('✓ Command usage data already empty');
      }
    }

    console.log('\nAll usage statistics have been reset.');
    console.log(`Backups saved to: ${backupDir}`);
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
  const config = loadNotionConfig();
  const syncState = loadSyncState();

  console.log('\n🔄 Notion Sync Status');
  console.log('═'.repeat(60));

  if (!config) {
    console.log('\n⚠ Notion設定が見つかりません。');
    console.log(`\n設定ファイルを作成してください: ${NOTION_CONFIG_FILE}`);
    console.log('\n例:');
    console.log(JSON.stringify({
      skill_usage_db_id: 'your-skill-usage-data-source-id',
      slash_command_db_id: 'your-slash-command-data-source-id'
    }, null, 2));
    return;
  }

  if (!config.skill_usage_db_id || !config.slash_command_db_id) {
    console.log('\n⚠ データベースIDが設定されていません。');
    console.log(`notion_config.json に skill_usage_db_id と slash_command_db_id を設定してください。`);
    console.log(`設定ファイル: ${NOTION_CONFIG_FILE}`);
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

  // Warning for large data sets
  const totalUnsyncedEvents = unsyncedSkillEvents.length + unsyncedCommandEvents.length;
  if (totalUnsyncedEvents > MAX_EVENTS_WARNING) {
    console.log(`\n⚠ 警告: ${totalUnsyncedEvents} 件の未同期イベントがあります。`);
    console.log(`  大量のデータを同期すると時間がかかる場合があります。`);
    console.log(`  Notion APIのレート制限により、バッチ処理が必要になることがあります。`);
  }

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

  if (args.includes('setup')) {
    setupNotionConfig(args);
    return;
  }

  if (args.includes('reset')) {
    resetEventsData({ force: args.includes('--force') });
    return;
  }

  if (args.includes('sync')) {
    outputSyncInfo();
    return;
  }

  displayStats();
}

main();
