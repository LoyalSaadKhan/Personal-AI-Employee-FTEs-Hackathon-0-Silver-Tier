#!/usr/bin/env node
/**
 * Test MCP Email Server
 * 
 * Usage: node test-mcp-email.js
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Configuration
const GMAIL_CREDENTIALS_PATH = 'C:/Users/Jawaria Noor/Desktop/Personal-AI-Employee-FTEs/Personal-AI-Employee-FTEs/AI_Employee_Vault/.gmail/credentials.json';
const GMAIL_TOKEN_PATH = 'C:/Users/Jawaria Noor/Desktop/Personal-AI-Employee-FTEs/Personal-AI-Employee-FTEs/AI_Employee_Vault/.gmail/token.json';

console.log('=' .repeat(60));
console.log('MCP Email Server Test');
console.log('=' .repeat(60));
console.log();

// Check if files exist
console.log('Checking files...');
console.log(`Credentials: ${fs.existsSync(GMAIL_CREDENTIALS_PATH)}`);
console.log(`Token: ${fs.existsSync(GMAIL_TOKEN_PATH)}`);
console.log();

if (!fs.existsSync(GMAIL_CREDENTIALS_PATH)) {
  console.error('❌ Credentials not found!');
  console.error(`Expected at: ${GMAIL_CREDENTIALS_PATH}`);
  process.exit(1);
}

if (!fs.existsSync(GMAIL_TOKEN_PATH)) {
  console.error('❌ Token not found!');
  console.error('Run: python scripts/setup_gmail_oauth.py ./AI_Employee_Vault');
  process.exit(1);
}

// Start MCP server
console.log('Starting MCP Email Server...');
const mcpProcess = spawn('node', ['index.js'], {
  env: {
    ...process.env,
    GMAIL_CREDENTIALS_PATH,
    GMAIL_TOKEN_PATH,
  },
  stdio: ['pipe', 'pipe', 'pipe'],
});

let output = '';
let errorOutput = '';

mcpProcess.stdout.on('data', (data) => {
  output += data.toString();
  console.log(`STDOUT: ${data}`);
});

mcpProcess.stderr.on('data', (data) => {
  errorOutput += data.toString();
  console.error(`STDERR: ${data}`);
});

mcpProcess.on('close', (code) => {
  console.log(`Process exited with code ${code}`);
  
  if (errorOutput.includes('running')) {
    console.log();
    console.log('=' .repeat(60));
    console.log('✅ MCP Email Server is working!');
    console.log('=' .repeat(60));
    console.log();
    console.log('Next steps:');
    console.log('1. Add to ~/.qwen/mcp.json (already done)');
    console.log('2. Test with: qwen "List email tools"');
    console.log();
  }
});

// Send test message after 3 seconds
setTimeout(() => {
  console.log();
  console.log('Sending test message...');
  
  // Send JSON-RPC list_tools request
  const listToolsRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/list',
    params: {},
  };
  
  mcpProcess.stdin.write(JSON.stringify(listToolsRequest) + '\n');
  
  // Close after 2 more seconds
  setTimeout(() => {
    mcpProcess.kill();
  }, 2000);
  
}, 3000);
