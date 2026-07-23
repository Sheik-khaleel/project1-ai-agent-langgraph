# Build stage
FROM node:20-alpine AS build
WORKDIR /usr/src/app
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY frontend/package.json frontend/package-lock.json frontend/vite.config.js ./
COPY frontend/index.html ./
COPY frontend/src ./src
RUN npm ci && npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /usr/src/app
COPY --from=build /usr/src/app/dist ./dist
RUN npm install -g npm@latest && npm install -g serve

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

ENV PORT=3000
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]