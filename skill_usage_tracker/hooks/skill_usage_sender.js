#!/usr/bin/env node

/**
 * Skill Usage Summary Hook (Stop)
 *
 * This hook displays a summary of skill usage when a Claude Code session ends.
 * Shows the data file path and usage counts for each skill.
 *
 * Reads data from ~/.claude/hooks/logs/skill_usage.jsonl
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const LOGS_DIR = path.join(os.homedir(), '.claude', 'hooks', 'logs');
const EVENTS_FILE = path.join(LOGS_DIR, 'skill_usage.jsonl');

/**
 * Load events from JSONL file
 */
function loadEvents() {
  try {
    if (fs.existsSync(EVENTS_FILE)) {
      const content = fs.readFileSync(EVENTS_FILE, 'utf8');
      return content
        .trim()
        .split('\n')
        .filter(line => line)
        .map(line => JSON.parse(line));
    }
  } catch (error) {
    // Silently ignore errors
  }
  return [];
}

/**
 * Main execution
 */
function main() {
  const events = loadEvents();

  if (events.length === 0) {
    // No skill usage, skip output
    return;
  }

  // Count skills
  const sessionSkills = {};
  for (const event of events) {
    if (event && event.skill) {
      sessionSkills[event.skill] = (sessionSkills[event.skill] || 0) + 1;
    }
  }

  // Display summary
  console.log('\n📊 Skill Usage Summary');
  console.log('─'.repeat(40));

  const totalCount = Object.values(sessionSkills).reduce((a, b) => a + b, 0);

  for (const [skill, count] of Object.entries(sessionSkills).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${skill}: ${count}`);
  }

  console.log('─'.repeat(40));
  console.log(`  Total: ${totalCount} invocations`);
  console.log(`  Data: ${EVENTS_FILE}`);
}

// Run main function
main();
