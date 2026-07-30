# dev: hot-reload через air + volume-mount кода (см. docker-compose.yml)
FROM golang:1.26-alpine AS dev
WORKDIR /app
RUN go install github.com/air-verse/air@latest
COPY go.mod ./
COPY . .
EXPOSE 8080
CMD ["air"]

FROM golang:1.26-alpine AS build
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /out/uptime ./cmd/uptime

FROM gcr.io/distroless/static-debian12:nonroot AS prod
COPY --from=build /out/uptime /uptime
EXPOSE 8080
ENTRYPOINT ["/uptime"]
