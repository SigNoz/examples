import assert from 'node:assert/strict'

const jaegerApi = process.env.JAEGER_API_URL ?? 'http://localhost:16686/api'

async function getJson(path) {
  const response = await fetch(`${jaegerApi}${path}`)
  assert.equal(response.ok, true, `Jaeger API returned ${response.status} for ${path}`)
  return response.json()
}

async function waitForTraces() {
  for (let attempt = 1; attempt <= 20; attempt += 1) {
    const result = await getJson('/traces?service=frontend-service&limit=100&lookback=1h')
    const traces = result.data ?? []

    const slowTrace = traces.find((trace) =>
      trace.spans.some((span) =>
        span.tags.some(
          (tag) => tag.key === 'inventory.lookup.mode' && tag.value === 'slow',
        ),
      ),
    )

    const failedTrace = traces.find((trace) =>
      trace.spans.some((span) =>
        span.logs?.some((log) =>
          log.fields.some(
            (field) =>
              field.key === 'exception.message' &&
              String(field.value).includes('Inventory database timed out'),
          ),
        ),
      ),
    )

    if (slowTrace && failedTrace) {
      return { traces, slowTrace, failedTrace }
    }

    await new Promise((resolve) => setTimeout(resolve, 500))
  }

  throw new Error('Timed out waiting for both slow and failed traces')
}

const servicesResult = await getJson('/services')
assert.ok(servicesResult.data.includes('frontend-service'))
assert.ok(servicesResult.data.includes('inventory-service'))

const { traces, slowTrace, failedTrace } = await waitForTraces()

const slowServices = new Set(
  Object.values(slowTrace.processes).map((process) => process.serviceName),
)
assert.deepEqual([...slowServices].sort(), ['frontend-service', 'inventory-service'])

const slowLookup = slowTrace.spans.find((span) => span.operationName === 'inventory.lookup')
assert.ok(slowLookup, 'Slow trace is missing inventory.lookup')
assert.ok(slowLookup.duration >= 650_000, 'Slow lookup should take at least 650 ms')
assert.ok(
  slowLookup.logs?.some((log) =>
    log.fields.some(
      (field) => field.key === 'event' && field.value === 'simulated slow database query',
    ),
  ),
  'Slow lookup is missing the diagnostic span event',
)

const failedServices = new Set(
  Object.values(failedTrace.processes).map((process) => process.serviceName),
)
assert.deepEqual([...failedServices].sort(), ['frontend-service', 'inventory-service'])

const failedLookup = failedTrace.spans.find(
  (span) => span.operationName === 'inventory.lookup',
)
assert.ok(failedLookup, 'Failed trace is missing inventory.lookup')
assert.ok(
  failedLookup.tags.some(
    (tag) => tag.key === 'otel.status_code' && tag.value === 'ERROR',
  ),
  'Failed lookup is missing ERROR status',
)

console.log(
  JSON.stringify(
    {
      serviceNames: servicesResult.data,
      tracesChecked: traces.length,
      slowTrace: {
        traceID: slowTrace.traceID,
        durationMs: Math.max(...slowTrace.spans.map((span) => span.duration)) / 1000,
        lookupDurationMs: slowLookup.duration / 1000,
      },
      failedTrace: {
        traceID: failedTrace.traceID,
        errorSpanCount: failedTrace.spans.filter((span) =>
          span.tags.some((tag) => tag.key === 'error' && tag.value === true),
        ).length,
      },
    },
    null,
    2,
  ),
)
