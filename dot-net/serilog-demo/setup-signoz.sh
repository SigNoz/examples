#!/bin/bash

# SigNoz Configuration Script
# This script helps you set the SIGNOZ_REGION and SIGNOZ_INGESTION_KEY environment variables securely

echo "🔐 SigNoz Configuration Helper"
echo "================================"
echo ""
echo "This script will help you set your SigNoz configuration as environment variables."
echo "The values will NOT be stored in any file - only in your current shell session."
echo ""

# Check if variables are set
region_set=false
key_set=false

if [ -n "$SIGNOZ_REGION" ]; then
    echo "✅ SIGNOZ_REGION is set to: $SIGNOZ_REGION"
    region_set=true
else
    echo "❌ SIGNOZ_REGION is not set"
fi

if [ -n "$SIGNOZ_INGESTION_KEY" ]; then
    echo "✅ SIGNOZ_INGESTION_KEY is already set in your environment"
    key_set=true
else
    echo "❌ SIGNOZ_INGESTION_KEY is not set"
fi

echo ""

if [ "$region_set" = true ] && [ "$key_set" = true ]; then
    echo "🎉 All SigNoz configuration is set!"
    echo ""
    echo "To run the application with SigNoz:"
    echo "  dotnet run"
    echo ""
else
    echo "To set them for this session, run:"
    echo "  export SIGNOZ_REGION='in'  # or 'us', 'eu', etc."
    echo "  export SIGNOZ_INGESTION_KEY='your-key-here'"
    echo ""
    echo "Or run the application with the values inline:"
    echo "  SIGNOZ_REGION='in' SIGNOZ_INGESTION_KEY='your-key-here' dotnet run"
    echo ""
fi

echo "📝 Note: These values will only persist for your current terminal session."
echo "   For permanent setup, add the export commands to your ~/.zshrc or ~/.bashrc"
echo ""
