# Build stage
FROM node:20-alpine AS build

WORKDIR /usr/src/app

COPY frontend/package.json frontend/vite.config.js ./
COPY frontend/index.html ./
COPY frontend/src ./src

RUN npm install && npm run build

# Runtime stage
FROM node:20-alpine

WORKDIR /usr/src/app

COPY --from=build /usr/src/app/dist ./dist

RUN npm install -g serve

ENV PORT=3000
CMD ["serve", "-s", "dist", "-l", "3000"]
