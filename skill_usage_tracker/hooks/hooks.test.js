#!/usr/bin/env node

/**
 * Tests for hooks.json configuration
 *
 * Validates that:
 * - hooks.json is valid JSON
 * - All hooks have async: true for non-blocking execution
 * - Required hook types are configured
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const HOOKS_FILE = path.join(__dirname, 'hooks.json');

/**
 * Load and parse hooks.json
 */
function loadHooksConfig() {
  const content = fs.readFileSync(HOOKS_FILE, 'utf8');
  return JSON.parse(content);
}

/**
 * Extract all hook definitions from config
 */
function getAllHooks(config) {
  const hooks = [];
  for (const [hookType, hookGroups] of Object.entries(config.hooks || {})) {
    for (const group of hookGroups) {
      for (const hook of group.hooks || []) {
        hooks.push({ hookType, matcher: group.matcher, ...hook });
      }
    }
  }
  return hooks;
}

/**
 * Test: hooks.json is valid JSON
 */
function testValidJson() {
  console.log('Test: hooks.json is valid JSON...');
  try {
    loadHooksConfig();
    console.log('  PASS: hooks.json is valid JSON');
    return true;
  } catch (error) {
    console.error(`  FAIL: Invalid JSON - ${error.message}`);
    return false;
  }
}

/**
 * Test: All hooks have async: true
 */
function testAsyncEnabled() {
  console.log('Test: All hooks have async: true...');
  const config = loadHooksConfig();
  const hooks = getAllHooks(config);

  let allPassed = true;
  for (const hook of hooks) {
    if (hook.async !== true) {
      console.error(`  FAIL: Hook ${hook.command} (${hook.hookType}) does not have async: true`);
      allPassed = false;
    }
  }

  if (allPassed) {
    console.log(`  PASS: All ${hooks.length} hooks have async: true`);
  }
  return allPassed;
}

/**
 * Test: Required hook types are configured
 */
function testRequiredHookTypes() {
  console.log('Test: Required hook types are configured...');
  const config = loadHooksConfig();
  const requiredTypes = ['UserPromptSubmit', 'PostToolUse', 'Stop'];

  let allPassed = true;
  for (const type of requiredTypes) {
    if (!config.hooks[type] || config.hooks[type].length === 0) {
      console.error(`  FAIL: Missing required hook type: ${type}`);
      allPassed = false;
    }
  }

  if (allPassed) {
    console.log(`  PASS: All required hook types are configured`);
  }
  return allPassed;
}

/**
 * Test: Hook commands reference existing files
 */
function testHookFilesExist() {
  console.log('Test: Hook command files exist...');
  const config = loadHooksConfig();
  const hooks = getAllHooks(config);

  let allPassed = true;
  for (const hook of hooks) {
    // Replace variable with current directory for testing
    const command = hook.command.replace('${CLAUDE_PLUGIN_ROOT}/hooks/', '');
    const filePath = path.join(__dirname, command);

    if (!fs.existsSync(filePath)) {
      console.error(`  FAIL: Hook file not found: ${command}`);
      allPassed = false;
    }
  }

  if (allPassed) {
    console.log(`  PASS: All ${hooks.length} hook files exist`);
  }
  return allPassed;
}

/**
 * Run all tests
 */
function runTests() {
  console.log('Running hooks.json tests...\n');

  const results = [
    testValidJson(),
    testAsyncEnabled(),
    testRequiredHookTypes(),
    testHookFilesExist(),
  ];

  const passed = results.filter(r => r).length;
  const total = results.length;

  console.log(`\nResults: ${passed}/${total} tests passed`);

  if (passed === total) {
    console.log('All tests passed!');
    process.exit(0);
  } else {
    console.error('Some tests failed.');
    process.exit(1);
  }
}

// Run tests
runTests();
