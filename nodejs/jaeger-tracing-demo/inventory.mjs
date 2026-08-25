import express from 'express'
import { SpanStatusCode, trace } from '@opentelemetry/api'

const app = express()
const tracer = trace.getTracer('inventory-domain')

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds))

app.get('/stock', async (request, response) => {
  const sku = request.query.sku ?? 'unknown'
  const mode = request.query.mode ?? 'normal'

  return tracer.startActiveSpan('inventory.lookup', async (span) => {
    span.setAttribute('inventory.sku', sku)
    span.setAttribute('inventory.lookup.mode', mode)

    try {
      if (mode === 'slow') {
        span.addEvent('simulated slow database query')
        await wait(700)
      } else {
        await wait(35)
      }

      if (mode === 'fail') {
        const error = new Error(`Inventory database timed out for ${sku}`)
        span.recordException(error)
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message })
        return response.status(503).json({ error: error.message })
      }

      span.setAttribute('inventory.available', true)
      return response.json({ sku, available: true, quantity: 12 })
    } finally {
      span.end()
    }
  })
})

app.get('/health', (_request, response) => response.json({ status: 'ok' }))

app.listen(3001, () => {
  console.log('inventory-service listening on port 3001')
})
