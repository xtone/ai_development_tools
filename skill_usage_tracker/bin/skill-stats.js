#!/usr/bin/env node

/**
 * Skill Usage Statistics Command
 *
 * スキル使用状況のサマリーを表示するコマンド
 * 使用方法: skill-stats.js [reset]
 *
 * Reads data from ~/.claude/hooks/logs/
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const LOGS_DIR = path.join(os.homedir(), '.claude', 'hooks', 'logs');
const SKILL_EVENTS_FILE = path.join(LOGS_DIR, 'skill_usage.jsonl');
const COMMAND_EVENTS_FILE = path.join(LOGS_DIR, 'slash_command.jsonl');

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
        .map(line => JSON.parse(line));
    }
  } catch {
    // Ignore parse errors
  }
  return [];
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

  displayStats();
}

main();
