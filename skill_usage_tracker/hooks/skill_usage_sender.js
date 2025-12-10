#!/usr/bin/env node

/**
 * Skill Usage Summary Hook (Stop)
 *
 * This hook displays a summary of skill usage when a Claude Code session ends.
 * Shows the data file path and usage counts for each skill.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const EVENTS_FILE = path.join(STATE_DIR, 'skill_usage_events.json');

/**
 * Load events data from file
 */
function loadEventsData() {
  try {
    if (fs.existsSync(EVENTS_FILE)) {
      const data = fs.readFileSync(EVENTS_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    // Silently ignore errors
  }
  return null;
}

/**
 * Main execution
 */
function main() {
  const data = loadEventsData();

  if (!data || !data.events || data.events.length === 0) {
    // No skill usage in this session, skip output
    return;
  }

  // Count skills used in this session (events since last clear)
  const sessionSkills = {};
  for (const event of data.events) {
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
