#!/usr/bin/env node

/**
 * User Prompt Slash Command Counter Hook (UserPromptSubmit)
 *
 * This hook detects when users directly type slash commands in their prompts.
 * It records these invocations to complement the SlashCommand tool tracking.
 *
 * Data is stored in ~/.claude/hooks/state/slash_command_events.json
 */

const fs = require('fs');
const fsPromises = require('fs').promises;
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Configuration
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const EVENTS_FILE = path.join(STATE_DIR, 'slash_command_events.json');

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
    // Ignore errors, return default
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
 * Parse slash command from user prompt
 * Returns command name if prompt starts with /command, null otherwise
 */
function parseSlashCommand(prompt) {
  if (!prompt || typeof prompt !== 'string') return null;

  const trimmed = prompt.trim();
  // Check if prompt starts with a slash command
  const match = trimmed.match(/^\/([^\s]+)/);
  return match ? match[1] : null;
}

/**
 * Record a slash command usage event (async)
 */
async function recordCommandEvent(commandName, fullPrompt, source) {
  const data = loadEventsData();

  // Create new event
  const event = {
    command: commandName,
    full_command: '/' + commandName,
    source: source, // 'user_prompt' or 'slash_command_tool'
    timestamp: new Date().toISOString(),
    user: getUserInfo(),
    context: getContextInfo(),
  };

  // Add event to list
  data.events.push(event);

  // Update summary counts
  data.summary[commandName] = (data.summary[commandName] || 0) + 1;

  // Mark as pending sync
  data.pending_sync = true;

  await saveEventsData(data);
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
      // No input, exit silently
      process.exit(0);
    }

    // Parse JSON input
    const data = JSON.parse(input);

    // UserPromptSubmit provides prompt in data.prompt
    const prompt = data?.prompt;
    const commandName = parseSlashCommand(prompt);

    if (!commandName) {
      // Not a slash command, exit silently
      process.exit(0);
    }

    // Record the command usage event
    await recordCommandEvent(commandName, prompt, 'user_prompt');

  } catch (error) {
    // Exit silently on errors to not disrupt user experience
    process.exit(0);
  }
}

// Run main function
main();
