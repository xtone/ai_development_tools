#!/usr/bin/env node

/**
 * Send Registration Tool
 *
 * This tool sends registration data to an external service.
 * It combines user payload with skill usage statistics and POSTs to a configured endpoint.
 *
 * Usage:
 *   sendRegistration.js [--url <url>] [--payload <json>]
 *
 * Environment Variables:
 *   REGISTRATION_URL - Target endpoint URL (default: https://example.com/register)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
const COUNTS_FILE = path.join(STATE_DIR, 'skill_usage_counts.json');
const DEFAULT_URL = process.env.REGISTRATION_URL || 'https://example.com/register';

/**
 * Load skill usage counts from state file
 * @returns {Object} Skill usage counts object
 */
function loadSkillUsageCounts() {
  try {
    if (fs.existsSync(COUNTS_FILE)) {
      const data = fs.readFileSync(COUNTS_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error(`Warning: Failed to load skill usage counts: ${error.message}`);
  }
  return {};
}

/**
 * Parse command line arguments
 * @returns {Object} Parsed arguments { url, payload }
 */
function parseArguments() {
  const args = process.argv.slice(2);
  let url = DEFAULT_URL;
  let payload = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url' && i + 1 < args.length) {
      url = args[i + 1];
      i++;
    } else if (args[i] === '--payload' && i + 1 < args.length) {
      try {
        payload = JSON.parse(args[i + 1]);
      } catch (error) {
        console.error(`Error: Invalid JSON payload: ${error.message}`);
        process.exit(1);
      }
      i++;
    }
  }

  return { url, payload };
}

/**
 * Send registration request to external service
 * @param {string} url - Target endpoint URL
 * @param {Object} data - Data to send
 */
async function sendRegistration(url, data) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const responseText = await response.text();
    let responseData;

    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = responseText;
    }

    console.log('\n=== Registration Request ===');
    console.log(`URL: ${url}`);
    console.log(`Status: ${response.status} ${response.statusText}`);
    console.log('\n=== Request Data ===');
    console.log(JSON.stringify(data, null, 2));
    console.log('\n=== Response ===');
    console.log(typeof responseData === 'string'
      ? responseData
      : JSON.stringify(responseData, null, 2));

    if (!response.ok) {
      console.error(`\nError: Request failed with status ${response.status}`);
      process.exit(1);
    }

  } catch (error) {
    if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
      console.error(`\nError: Failed to connect to ${url}`);
      console.error(`Details: ${error.message}`);
      console.error('\nPlease check:');
      console.error('  - The URL is correct');
      console.error('  - The service is running');
      console.error('  - You have internet connectivity');
    } else {
      console.error(`\nError: ${error.message}`);
    }
    process.exit(1);
  }
}

/**
 * Display usage information
 */
function showUsage() {
  console.log(`
Usage: sendRegistration.js [OPTIONS]

Options:
  --url <url>        Target endpoint URL (default: ${DEFAULT_URL})
  --payload <json>   JSON payload to send (default: {})
  --help             Show this help message

Environment Variables:
  REGISTRATION_URL   Override default endpoint URL

Examples:
  # Send with custom payload
  sendRegistration.js --payload '{"name":"John","email":"john@example.com"}'

  # Send to custom URL
  sendRegistration.js --url https://api.example.com/v1/register --payload '{"name":"Jane"}'

  # Use environment variable for URL
  REGISTRATION_URL=https://api.example.com/register sendRegistration.js --payload '{}'
`);
}

/**
 * Main execution
 */
async function main() {
  // Check for help flag
  if (process.argv.includes('--help') || process.argv.includes('-h')) {
    showUsage();
    process.exit(0);
  }

  try {
    // Parse command line arguments
    const { url, payload } = parseArguments();

    // Load skill usage counts
    const skillUsageCounts = loadSkillUsageCounts();

    // Combine payload with skill usage statistics
    const requestData = {
      ...payload,
      skill_usage_stats: {
        counts: skillUsageCounts,
        total_invocations: Object.values(skillUsageCounts).reduce((sum, count) => sum + count, 0),
        timestamp: new Date().toISOString(),
      },
    };

    // Send registration request
    await sendRegistration(url, requestData);

    console.log('\n✓ Registration completed successfully');

  } catch (error) {
    console.error(`\nFatal error: ${error.message}`);
    process.exit(1);
  }
}

// Run main function
main();
