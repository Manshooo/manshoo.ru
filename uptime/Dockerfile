# dev: hot-reload через air + volume-mount кода (см. docker-compose.yml)
FROM golang:1.26-alpine AS dev
WORKDIR /app
RUN go install github.com/air-verse/air@latest
COPY go.mod go.sum ./
RUN go mod download
COPY . .
EXPOSE 8080
CMD ["air"]

FROM golang:1.26-alpine AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /out/uptime ./cmd/uptime \
    && mkdir -p /out/data

FROM gcr.io/distroless/static-debian12:nonroot AS prod
COPY --from=build /out/uptime /uptime
# 65532 = nonroot; каталог с этим владельцем наследует и named volume при первом старте
COPY --from=build --chown=65532:65532 /out/data /data
COPY --from=build /app/config.yaml /config.yaml
ENV UPTIME_CONFIG=/config.yaml \
    UPTIME_DB_PATH=/data/uptime.db
EXPOSE 8080
ENTRYPOINT ["/uptime"]
