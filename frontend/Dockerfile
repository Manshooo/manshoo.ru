# dev: hot-reload через vite + volume-mount кода (см. docker-compose.yml)
FROM node:24-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# adapter-node собирает самодостаточный build/ (prod-зависимостей у нас нет)
FROM node:24-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/build ./build
COPY package.json ./
EXPOSE 3000
CMD ["node", "build"]
