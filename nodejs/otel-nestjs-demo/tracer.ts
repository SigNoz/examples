import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';

// Configure trace exporter - use console for debugging
const debugExporter = new ConsoleSpanExporter();
const traceExporter =
  process.env.NODE_ENV === 'development'
    ? debugExporter
    : new OTLPTraceExporter({
        url:
          process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT ||
          'http://localhost:4318/v1/traces',
      });

// Create SDK instance with comprehensive configuration
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
