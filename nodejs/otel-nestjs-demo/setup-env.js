#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const TEMPLATE_FILE = path.join(__dirname, 'env.template');
const ENV_FILE = path.join(__dirname, '.env');

function setupEnv() {
  // Check if .env already exists
  if (fs.existsSync(ENV_FILE)) {
    console.log('⚠️  .env file already exists');
    console.log('📋 To update your configuration:');
    console.log('   1. Edit .env file directly');
    console.log('   2. Or delete .env and run this script again');
    return;
  }

  // Copy template to .env
  try {
    const templateContent = fs.readFileSync(TEMPLATE_FILE, 'utf8');
    fs.writeFileSync(ENV_FILE, templateContent);

    console.log('✅ Created .env file from template');
    console.log('');
    console.log('🔧 Next steps:');
    console.log('   1. Sign up for SigNoz Cloud: https://signoz.io/teams/');
    console.log(
      '   2. Get your access token from Settings → Ingestion Settings',
    );
    console.log('   3. Update these values in .env:');
    console.log(
      '      - SIGNOZ_ENDPOINT (replace {your-region} with your region)',
    );
    console.log('      - SIGNOZ_ACCESS_TOKEN (your actual token)');
    console.log('');
    console.log('📝 Example:');
    console.log(
      '   SIGNOZ_ENDPOINT=https://ingest.us.signoz.cloud:443/v1/traces',
    );
    console.log('   SIGNOZ_ACCESS_TOKEN=your-actual-token-here');
    console.log('');
    console.log('🚀 Then switch to SigNoz tracer:');
    console.log('   node switch-tracer.js signoz');
  } catch (error) {
    console.error('❌ Error creating .env file:', error.message);
  }
}

setupEnv();
