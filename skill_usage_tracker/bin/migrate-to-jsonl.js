#!/usr/bin/env node

/**
 * Migration Script: JSON to JSONL
 *
 * Migrates existing JSON format data to JSONL format.
 *
 * Source: ~/.claude/hooks/state/*.json
 * Target: ~/.claude/hooks/logs/*.jsonl
 *
 * Usage: node migrate-to-jsonl.js [--dry-run]
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const LOGS_DIR = path.join(os.homedir(), '.claude', 'hooks', 'logs');

// Source files (old JSON format)
const OLD_SKILL_FILE = path.join(STATE_DIR, 'skill_usage_events.json');
const OLD_COMMAND_FILE = path.join(STATE_DIR, 'slash_command_events.json');

// Target files (new JSONL format)
const NEW_SKILL_FILE = path.join(LOGS_DIR, 'skill_usage.jsonl');
const NEW_COMMAND_FILE = path.join(LOGS_DIR, 'slash_command.jsonl');

/**
 * Ensure logs directory exists
 */
function ensureLogsDirectory() {
  if (!fs.existsSync(LOGS_DIR)) {
    fs.mkdirSync(LOGS_DIR, { recursive: true });
    console.log(`Created directory: ${LOGS_DIR}`);
  }
}

/**
 * Load JSON data from old format file
 */
function loadOldData(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.error(`Error loading ${filePath}: ${error.message}`);
  }
  return null;
}

/**
 * Check if JSONL file already has data
 */
function hasExistingData(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8').trim();
      return content.length > 0;
    }
  } catch {
    // Ignore errors
  }
  return false;
}

/**
 * Convert events to JSONL format
 */
function convertToJsonl(events) {
  if (!events || !Array.isArray(events) || events.length === 0) {
    return '';
  }
  return events.map(event => JSON.stringify(event)).join('\n') + '\n';
}

/**
 * Migrate a single file
 */
function migrateFile(oldPath, newPath, label, dryRun) {
  console.log(`\n${label}:`);
  console.log(`  Source: ${oldPath}`);
  console.log(`  Target: ${newPath}`);

  // Check if source exists
  if (!fs.existsSync(oldPath)) {
    console.log('  Status: Source file not found, skipping');
    return { skipped: true, reason: 'source_not_found' };
  }

  // Check if target already has data
  if (hasExistingData(newPath)) {
    console.log('  Status: Target file already has data, skipping to prevent duplicates');
    return { skipped: true, reason: 'target_has_data' };
  }

  // Load old data
  const data = loadOldData(oldPath);
  if (!data) {
    console.log('  Status: Failed to load source data, skipping');
    return { skipped: true, reason: 'load_error' };
  }

  const events = data.events || [];
  if (events.length === 0) {
    console.log('  Status: No events to migrate');
    return { skipped: true, reason: 'no_events' };
  }

  // Convert to JSONL
  const jsonlContent = convertToJsonl(events);

  if (dryRun) {
    console.log(`  Status: Would migrate ${events.length} events (dry-run)`);
    console.log(`  Preview (first 3 lines):`);
    const previewLines = jsonlContent.split('\n').slice(0, 3);
    for (const line of previewLines) {
      if (line) console.log(`    ${line.substring(0, 80)}${line.length > 80 ? '...' : ''}`);
    }
    return { migrated: true, count: events.length, dryRun: true };
  }

  // Write to new file
  try {
    fs.writeFileSync(newPath, jsonlContent, 'utf8');
    console.log(`  Status: Migrated ${events.length} events successfully`);
    return { migrated: true, count: events.length };
  } catch (error) {
    console.error(`  Status: Failed to write target file: ${error.message}`);
    return { skipped: true, reason: 'write_error' };
  }
}

/**
 * Main migration function
 */
function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');

  console.log('='.repeat(60));
  console.log('Skill Usage Tracker: JSON to JSONL Migration');
  console.log('='.repeat(60));

  if (dryRun) {
    console.log('\n[DRY RUN MODE - No files will be modified]');
  }

  // Ensure logs directory exists
  if (!dryRun) {
    ensureLogsDirectory();
  }

  // Migrate skill usage events
  const skillResult = migrateFile(
    OLD_SKILL_FILE,
    NEW_SKILL_FILE,
    'Skill Usage Events',
    dryRun
  );

  // Migrate slash command events
  const commandResult = migrateFile(
    OLD_COMMAND_FILE,
    NEW_COMMAND_FILE,
    'Slash Command Events',
    dryRun
  );

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('Migration Summary');
  console.log('='.repeat(60));

  if (skillResult.migrated) {
    console.log(`  Skill events: ${skillResult.count} events ${dryRun ? 'would be ' : ''}migrated`);
  } else {
    console.log(`  Skill events: Skipped (${skillResult.reason})`);
  }

  if (commandResult.migrated) {
    console.log(`  Command events: ${commandResult.count} events ${dryRun ? 'would be ' : ''}migrated`);
  } else {
    console.log(`  Command events: Skipped (${commandResult.reason})`);
  }

  if (!dryRun && (skillResult.migrated || commandResult.migrated)) {
    console.log('\nMigration complete!');
    console.log('You can now safely delete the old JSON files in:');
    console.log(`  ${STATE_DIR}`);
  }

  if (dryRun) {
    console.log('\nTo perform the actual migration, run without --dry-run');
  }
}

// Run migration
main();
