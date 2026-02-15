import { config } from 'dotenv';
config(); // Load environment variables

import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

// SigNoz Cloud configuration
const traceExporter = new OTLPTraceExporter({
  url:
    process.env.SIGNOZ_ENDPOINT ||
    'https://ingest.{region}.signoz.cloud:443/v1/traces',
  headers: {
    'signoz-access-token':
      process.env.SIGNOZ_ACCESS_TOKEN || 'your-signoz-token',
  },
});

// Create SDK instance configured for SigNoz
const sdk = new NodeSDK({
  traceExporter,
  instrumentations: [
    getNodeAutoInstrumentations({
      // Disable instrumentations that might cause issues
      '@opentelemetry/instrumentation-fs': { enabled: false },
      // Configure HTTP instrumentation for better trace context
      '@opentelemetry/instrumentation-http': {
        enabled: true,
        ignoreIncomingRequestHook: (req) => {
          // Ignore health check endpoints
          return (
            req.url?.includes('/health') ||
            req.url?.includes('/metrics') ||
            false
          );
        },
      },
    }),
  ],
});

export default sdk;
