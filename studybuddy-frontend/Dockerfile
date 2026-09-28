FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
# package-lock.json is gitignored in this repo, so fall back to npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

# NEXT_PUBLIC_* values are baked into the bundle at build time
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]
