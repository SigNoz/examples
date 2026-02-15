#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const MAIN_FILE = path.join(__dirname, 'src/main.ts');
const CONSOLE_TRACER = "import tracer from '../tracer';";
const SIGNOZ_TRACER = "import tracer from '../tracer.signoz';";

function getCurrentTracer() {
  const content = fs.readFileSync(MAIN_FILE, 'utf8');
  if (content.includes("'../tracer.signoz'")) {
    return 'signoz';
  } else if (content.includes("'../tracer'")) {
    return 'console';
  } else {
    return 'unknown';
  }
}

function switchTracer(target) {
  const content = fs.readFileSync(MAIN_FILE, 'utf8');
  let newContent;

  if (target === 'signoz') {
    newContent = content.replace(CONSOLE_TRACER, SIGNOZ_TRACER);
  } else if (target === 'console') {
    newContent = content.replace(SIGNOZ_TRACER, CONSOLE_TRACER);
  } else {
    console.error('Invalid target. Use "console" or "signoz"');
    process.exit(1);
  }

  fs.writeFileSync(MAIN_FILE, newContent);
  console.log(`✅ Switched tracer to: ${target}`);
}

function showUsage() {
  console.log(`
🔧 OpenTelemetry Tracer Switcher

Usage:
  node switch-tracer.js console   # Switch to console output (development)
  node switch-tracer.js signoz    # Switch to SigNoz Cloud (production)
  node switch-tracer.js status    # Show current configuration

Current tracer: ${getCurrentTracer()}
`);
}

const command = process.argv[2];

switch (command) {
  case 'console':
    switchTracer('console');
    break;
  case 'signoz':
    switchTracer('signoz');
    break;
  case 'status':
    console.log(`Current tracer: ${getCurrentTracer()}`);
    break;
  default:
    showUsage();
}
