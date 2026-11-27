import { Mastra } from "@mastra/core";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { z } from "zod";
import { chefAgent } from "./chef-agent.ts";

const env = z.object({
  OPENAI_API_KEY: z.string().min(1),
  OTEL_SERVICE_NAME: z.string().min(1).default("mastra-agent-observability-demo"),
  OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: z.url({ protocol: /^https?$/ }).optional(),
  SIGNOZ_INGESTION_KEY: z.string().min(1).optional(),
  SIGNOZ_REGION: z.enum(["us", "eu", "in"]).default("us"),
}).parse(process.env);

if (!env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT && !env.SIGNOZ_INGESTION_KEY) {
  throw new Error("Set OTEL_EXPORTER_OTLP_TRACES_ENDPOINT for self-hosted SigNoz or SIGNOZ_INGESTION_KEY for SigNoz Cloud.");
}

const mastra = new Mastra({
  agents: { chefAgent },
  observability: new Observability({
    configs: {
      otel: {
        serviceName: env.OTEL_SERVICE_NAME,
        exporters: [
          new OtelExporter({
            provider: env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
              ? {
                  custom: {
                    endpoints: { traces: env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT },
                    protocol: "http/protobuf",
                  },
                }
              : { signoz: { apiKey: env.SIGNOZ_INGESTION_KEY, region: env.SIGNOZ_REGION } },
            resourceAttributes: { "deployment.environment.name": "development" },
            signals: { logs: false },
          }),
        ],
      },
    },
  }),
});

try {
  const result = await mastra.getAgent("chefAgent").generate(
    "How many grams of dry rice do I need for 3 servings?",
    {
      prepareStep: ({ stepNumber }) => stepNumber === 0
        ? { toolChoice: { type: "tool", toolName: "scaleRice" } }
        : { toolChoice: "none" },
    },
  );
  console.log(result.text);
} finally {
  await mastra.shutdown();
}
