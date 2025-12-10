#!/usr/bin/env node

/**
 * Skill Usage Counter Hook (PostToolUse)
 *
 * This hook records skill invocations via the "Skill" tool with detailed metadata.
 * It stores events with timestamps, user info, and context for later aggregation.
 *
 * Data is stored in ~/.claude/hooks/state/skill_usage_events.json
 */

const fs = require('fs');
const fsPromises = require('fs').promises;
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Configuration
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const EVENTS_FILE = path.join(STATE_DIR, 'skill_usage_events.json');

/**
 * Ensure state directory exists
 */
function ensureStateDirectory() {
  if (!fs.existsSync(STATE_DIR)) {
    fs.mkdirSync(STATE_DIR, { recursive: true });
  }
}

/**
 * Execute command safely and return result or default value
 */
function execSafe(command, defaultValue = '') {
  try {
    return execSync(command, { encoding: 'utf8', timeout: 5000 }).trim();
  } catch {
    return defaultValue;
  }
}

/**
 * Get user information from git config and environment
 */
function getUserInfo() {
  return {
    name: execSafe('git config user.name'),
    email: execSafe('git config user.email'),
    system_user: process.env.USER || os.userInfo().username,
  };
}

/**
 * Get context information (project, branch, etc.)
 */
function getContextInfo() {
  return {
    project: path.basename(process.cwd()),
    branch: execSafe('git branch --show-current'),
    remote: execSafe('git remote get-url origin'),
    hostname: os.hostname(),
    cwd: process.cwd(),
  };
}

/**
 * Load existing events data
 */
function loadEventsData() {
  try {
    if (fs.existsSync(EVENTS_FILE)) {
      const data = fs.readFileSync(EVENTS_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch {
    console.error('Warning: Failed to load events file');
  }
  return { events: [], summary: {}, pending_sync: true };
}

/**
 * Save events data (async)
 */
async function saveEventsData(data) {
  try {
    ensureStateDirectory();
    await fsPromises.writeFile(EVENTS_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (error) {
    console.error('Error: Failed to save events');
    throw error;
  }
}

/**
 * Record a skill usage event (async)
 */
async function recordSkillEvent(skillName) {
  const data = loadEventsData();

  // Create new event
  const event = {
    skill: skillName,
    timestamp: new Date().toISOString(),
    user: getUserInfo(),
    context: getContextInfo(),
  };

  // Add event to list
  data.events.push(event);

  // Update summary counts
  data.summary[skillName] = (data.summary[skillName] || 0) + 1;

  // Mark as pending sync
  data.pending_sync = true;

  await saveEventsData(data);

  console.log(`Recorded: ${skillName} (total: ${data.summary[skillName]})`);
}

/**
 * Main execution
 */
async function main() {
  try {
    // Read JSON data from stdin
    const chunks = [];
    for await (const chunk of process.stdin) {
      chunks.push(chunk);
    }
    const input = Buffer.concat(chunks).toString('utf8');

    if (!input.trim()) {
      console.error('Error: No input received from stdin');
      process.exit(1);
    }

    // Parse JSON input
    const data = JSON.parse(input);

    // Extract skill name from tool_input.skill
    const skillName = data?.tool_input?.skill;

    if (!skillName) {
      console.error('Warning: No skill name found in tool_input.skill');
      process.exit(0);
    }

    // Record the skill usage event
    await recordSkillEvent(skillName);

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run main function
main();
