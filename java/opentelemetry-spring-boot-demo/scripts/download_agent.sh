#!/usr/bin/env bash
# Downloads the OpenTelemetry Java Agent JAR.
# Run once before starting the app: make download-agent
set -euo pipefail

AGENT_VERSION="2.12.0"
AGENT_JAR="agent/opentelemetry-javaagent.jar"
DOWNLOAD_URL="https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v${AGENT_VERSION}/opentelemetry-javaagent.jar"

mkdir -p agent

if [ -f "$AGENT_JAR" ]; then
    echo "Agent already present: $AGENT_JAR (v${AGENT_VERSION})"
    exit 0
fi

echo "Downloading OTel Java Agent v${AGENT_VERSION}..."
curl -fL "$DOWNLOAD_URL" -o "$AGENT_JAR"
echo "Saved to $AGENT_JAR"
