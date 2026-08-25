import express from 'express'

const app = express()
const inventoryUrl = process.env.INVENTORY_URL ?? 'http://localhost:3001'

app.get('/checkout', async (request, response) => {
  const sku = request.query.sku ?? 'camera-001'
  const mode = request.query.mode ?? 'normal'
  const params = new URLSearchParams({ sku, mode })

  try {
    const inventoryResponse = await fetch(`${inventoryUrl}/stock?${params}`)
    const inventory = await inventoryResponse.json()

    if (!inventoryResponse.ok) {
      return response.status(502).json({
        message: 'Checkout could not verify inventory',
        inventory,
      })
    }

    return response.json({
      message: 'Checkout is ready',
      sku,
      inventory,
    })
  } catch (error) {
    return response.status(502).json({
      message: 'Inventory service was unreachable',
      error: error.message,
    })
  }
})

app.get('/health', (_request, response) => response.json({ status: 'ok' }))

app.listen(3000, () => {
  console.log('frontend-service listening on port 3000')
})
