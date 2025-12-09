#!/usr/bin/env node

/**
 * Skill Usage Statistics Command
 *
 * スキル使用状況のサマリーを表示するコマンド
 * 使用方法: skill-stats.js [reset]
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const SKILL_EVENTS_FILE = path.join(STATE_DIR, 'skill_usage_events.json');
const COMMAND_EVENTS_FILE = path.join(STATE_DIR, 'slash_command_events.json');

/**
 * Load events data from file
 */
function loadEventsData(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    }
  } catch {
    // Ignore parse errors
  }
  return { events: [], summary: {} };
}

/**
 * Reset events data
 */
function resetEventsData() {
  const emptyData = { events: [], summary: {}, pending_sync: false };

  try {
    if (fs.existsSync(SKILL_EVENTS_FILE)) {
      fs.writeFileSync(SKILL_EVENTS_FILE, JSON.stringify(emptyData, null, 2), 'utf8');
      console.log('✓ Skill usage data reset');
    }
    if (fs.existsSync(COMMAND_EVENTS_FILE)) {
      fs.writeFileSync(COMMAND_EVENTS_FILE, JSON.stringify(emptyData, null, 2), 'utf8');
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
  const skillData = loadEventsData(SKILL_EVENTS_FILE);
  const commandData = loadEventsData(COMMAND_EVENTS_FILE);

  const hasSkillEvents = skillData.events && skillData.events.length > 0;
  const hasCommandEvents = commandData.events && commandData.events.length > 0;

  if (!hasSkillEvents && !hasCommandEvents) {
    console.log('使用データがありません');
    return;
  }

  // Skill usage summary
  if (hasSkillEvents) {
    const skills = {};
    for (const event of skillData.events) {
      skills[event.skill] = (skills[event.skill] || 0) + 1;
    }

    console.log('\n📊 Skill Usage Summary');
    console.log('─'.repeat(40));

    const sorted = Object.entries(skills).sort((a, b) => b[1] - a[1]);
    for (const [skill, count] of sorted) {
      console.log(`  ${skill}: ${count}`);
    }

    console.log('─'.repeat(40));
    console.log(`  Total: ${skillData.events.length} invocations`);
    console.log(`  Data: ${SKILL_EVENTS_FILE}`);
  }

  // Command usage summary
  if (hasCommandEvents) {
    const commands = {};
    for (const event of commandData.events) {
      commands[event.command] = (commands[event.command] || 0) + 1;
    }

    console.log('\n📋 Slash Command Usage Summary');
    console.log('─'.repeat(40));

    const sorted = Object.entries(commands).sort((a, b) => b[1] - a[1]);
    for (const [command, count] of sorted) {
      console.log(`  /${command}: ${count}`);
    }

    console.log('─'.repeat(40));
    console.log(`  Total: ${commandData.events.length} invocations`);
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
