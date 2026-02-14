import { config } from 'dotenv';
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import {
  ConsoleSpanExporter,
  BatchSpanProcessor,
  TraceIdRatioBasedSampler,
  ParentBasedSampler,
} from '@opentelemetry/sdk-trace-base';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';

config(); // Load environment variables

const isProduction = process.env.NODE_ENV === 'production';

// Configure trace exporter based on environment
const traceExporter = isProduction
  ? new OTLPTraceExporter({
    url:
      process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT ||
      'http://localhost:4318/v1/traces',
    headers: process.env.OTEL_EXPORTER_OTLP_HEADERS
      ? JSON.parse(process.env.OTEL_EXPORTER_OTLP_HEADERS)
      : {},
  })
  : new ConsoleSpanExporter();

// Production-optimized configuration
const sdk = new NodeSDK({
  // Sample 10% of traces in production, 100% in development
  sampler: new ParentBasedSampler({
    root: new TraceIdRatioBasedSampler(isProduction ? 0.1 : 1.0),
  }),

  // Batch export for better performance
  spanProcessor: new BatchSpanProcessor(traceExporter, {
    maxExportBatchSize: isProduction ? 200 : 50,
    exportTimeoutMillis: isProduction ? 5000 : 2000,
    scheduledDelayMillis: isProduction ? 2000 : 1000,
  }),

  resource: resourceFromAttributes({
    [ATTR_SERVICE_NAME]: process.env.SERVICE_NAME,
    [ATTR_SERVICE_VERSION]: process.env.SERVICE_VERSION,
    // use raw string or the deprecated SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT resource attribute
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV,
  }),

  instrumentations: [
    getNodeAutoInstrumentations({
      // Disable high-volume instrumentation in production
      '@opentelemetry/instrumentation-fs': { enabled: false },
      '@opentelemetry/instrumentation-dns': { enabled: false },

      '@opentelemetry/instrumentation-http': {
        enabled: true,
        ignoreIncomingRequestHook: (req) => {
          const ignorePaths = ['/health', '/metrics', '/favicon.ico'];
          return ignorePaths.some((path) => req.url?.includes(path)) || false;
        },
      },
    }),
  ],
});

export default sdk;
