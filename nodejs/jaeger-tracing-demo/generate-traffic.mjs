const scenarios = ['normal', 'normal', 'slow', 'normal', 'fail']
const frontendUrl = process.env.FRONTEND_URL ?? 'http://localhost:3000'

async function waitForFrontend() {
  for (let attempt = 1; attempt <= 30; attempt += 1) {
    try {
      const response = await fetch(`${frontendUrl}/health`)
      if (response.ok) return
    } catch {
      // Docker may report the container as started before Node is accepting traffic.
    }

    await new Promise((resolve) => setTimeout(resolve, 500))
  }

  throw new Error('frontend-service did not become ready within 15 seconds')
}

await waitForFrontend()

for (let index = 0; index < 20; index += 1) {
  const mode = scenarios[index % scenarios.length]
  const url = `${frontendUrl}/checkout?sku=camera-${String(index + 1).padStart(3, '0')}&mode=${mode}`
  const response = await fetch(url)
  console.log(`${response.status} ${mode.padEnd(6)} ${url}`)
  await new Promise((resolve) => setTimeout(resolve, 150))
}
