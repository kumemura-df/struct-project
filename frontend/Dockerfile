FROM node:20-alpine AS builder
WORKDIR /app

# Accept build argument for API URL
ARG NEXT_PUBLIC_API_URL
# Set default for production if not provided via build args
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-https://project-progress-api-prod-29226667525.asia-northeast1.run.app}

COPY package*.json ./
COPY .npmrc ./
RUN npm ci
COPY . .

# Debug: Print the API URL during build
RUN echo "Building with NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Also set runtime env var (though NEXT_PUBLIC_* are baked at build time)
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-https://project-progress-api-prod-29226667525.asia-northeast1.run.app}

COPY --from=builder /app/next.config.mjs ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
