#!/usr/bin/env node

/**
 * Slash Command Usage Counter Hook (PostToolUse)
 *
 * This hook records slash command invocations via the "SlashCommand" tool with detailed metadata.
 * It stores events as JSONL (one JSON object per line) for efficient append-only logging.
 *
 * Data is stored in ~/.claude/hooks/logs/slash_command.jsonl
 */

const fs = require('fs');
const fsPromises = require('fs').promises;
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Configuration
const LOGS_DIR = path.join(os.homedir(), '.claude', 'hooks', 'logs');
const EVENTS_FILE = path.join(LOGS_DIR, 'slash_command.jsonl');
const LOCK_FILE = path.join(LOGS_DIR, 'slash_command.lock');
const LOCK_TIMEOUT = 5000; // 5 seconds
const LOCK_RETRY_INTERVAL = 50; // 50ms

/**
 * Ensure logs directory exists
 */
function ensureLogsDirectory() {
  if (!fs.existsSync(LOGS_DIR)) {
    fs.mkdirSync(LOGS_DIR, { recursive: true });
  }
}

/**
 * Acquire a file lock with timeout
 * Uses exclusive file creation to prevent race conditions
 */
async function acquireLock() {
  const startTime = Date.now();

  while (Date.now() - startTime < LOCK_TIMEOUT) {
    try {
      // Try to create lock file exclusively (fails if exists)
      const fd = fs.openSync(LOCK_FILE, 'wx');
      fs.writeSync(fd, String(process.pid));
      fs.closeSync(fd);
      return true;
    } catch (error) {
      if (error.code === 'EEXIST') {
        // Lock file exists, check if stale
        try {
          const stat = fs.statSync(LOCK_FILE);
          const age = Date.now() - stat.mtimeMs;
          // If lock is older than timeout, consider it stale and remove
          if (age > LOCK_TIMEOUT) {
            fs.unlinkSync(LOCK_FILE);
            continue;
          }
        } catch {
          // Lock file was removed, retry
          continue;
        }
        // Wait and retry
        await new Promise(resolve => setTimeout(resolve, LOCK_RETRY_INTERVAL));
      } else {
        throw error;
      }
    }
  }

  throw new Error('Failed to acquire lock: timeout');
}

/**
 * Release the file lock
 */
function releaseLock() {
  try {
    fs.unlinkSync(LOCK_FILE);
  } catch {
    // Ignore errors when releasing lock
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
 * Parse command string to extract command name
 * e.g., "/skill-usage-tracker:skill-stats help" -> "skill-usage-tracker:skill-stats"
 */
function parseCommandName(commandStr) {
  if (!commandStr) return null;
  // Remove leading slash and extract command name (before first space)
  const match = commandStr.match(/^\/?([^\s]+)/);
  return match ? match[1] : null;
}

/**
 * Append a slash command usage event to JSONL file (async) with file locking
 */
async function appendCommandEvent(commandName, fullCommand) {
  ensureLogsDirectory();

  // Create new event
  const event = {
    command: commandName,
    full_command: fullCommand,
    timestamp: new Date().toISOString(),
    user: getUserInfo(),
    context: getContextInfo(),
  };

  // Acquire lock before writing
  try {
    await acquireLock();

    // Append to JSONL file
    await fsPromises.appendFile(EVENTS_FILE, JSON.stringify(event) + '\n', 'utf8');

    console.log(`Recorded: ${commandName}`);
  } finally {
    releaseLock();
  }
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

    // Extract command from tool_input.command
    const fullCommand = data?.tool_input?.command;
    const commandName = parseCommandName(fullCommand);

    if (!commandName) {
      console.error('Warning: No command name found in tool_input.command');
      process.exit(0);
    }

    // Record the command usage event
    await appendCommandEvent(commandName, fullCommand);

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run main function
main();
