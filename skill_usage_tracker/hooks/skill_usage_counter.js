#!/usr/bin/env node

/**
 * Skill Usage Counter Hook
 *
 * This hook counts skill invocations via the "Skill" tool.
 * It reads tool usage data from stdin, extracts the skill name,
 * and persists usage counts to ~/.claude/hooks/state/skill_usage_counts.json
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const COUNTS_FILE = path.join(STATE_DIR, 'skill_usage_counts.json');

/**
 * Ensure state directory exists
 */
function ensureStateDirectory() {
  if (!fs.existsSync(STATE_DIR)) {
    fs.mkdirSync(STATE_DIR, { recursive: true });
  }
}

/**
 * Load existing skill usage counts
 * @returns {Object} Skill usage counts object
 */
function loadCounts() {
  try {
    if (fs.existsSync(COUNTS_FILE)) {
      const data = fs.readFileSync(COUNTS_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error(`Warning: Failed to load counts file: ${error.message}`);
  }
  return {};
}

/**
 * Save skill usage counts
 * @param {Object} counts - Skill usage counts object
 */
function saveCounts(counts) {
  try {
    ensureStateDirectory();
    fs.writeFileSync(COUNTS_FILE, JSON.stringify(counts, null, 2), 'utf8');
  } catch (error) {
    console.error(`Error: Failed to save counts: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Increment skill usage count
 * @param {string} skillName - Name of the skill to increment
 */
function incrementSkillCount(skillName) {
  const counts = loadCounts();
  counts[skillName] = (counts[skillName] || 0) + 1;
  saveCounts(counts);
  console.log(`Skill "${skillName}" usage count: ${counts[skillName]}`);
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
    // The Skill tool uses "skill" parameter to specify which skill to invoke
    const skillName = data?.tool_input?.skill;

    if (!skillName) {
      console.error('Warning: No skill name found in tool_input.skill');
      process.exit(0);
    }

    // Increment the count for this skill
    incrementSkillCount(skillName);

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run main function
main();
