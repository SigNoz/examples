FROM node:24.11.1-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY instrumentation.mjs frontend.mjs inventory.mjs verify-traces.mjs ./

CMD ["npm", "run", "frontend"]
