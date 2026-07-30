package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/api"
	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
	"github.com/Manshooo/manshoo.ru/uptime/internal/notify"
	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
	"github.com/Manshooo/manshoo.ru/uptime/internal/store"
)

const retention = 90 * 24 * time.Hour

func main() {
	healthcheck := flag.Bool("healthcheck", false,
		"проверить /healthz локального сервера и выйти (для docker healthcheck)")
	flag.Parse()

	addr := envOr("UPTIME_ADDR", ":8080")
	if *healthcheck {
		os.Exit(runHealthcheck(addr))
	}

	log := slog.New(slog.NewTextHandler(os.Stderr, nil))
	if err := run(log, addr); err != nil {
		log.Error("fatal", "err", err)
		os.Exit(1)
	}
}

func run(log *slog.Logger, addr string) error {
	cfg, err := config.Load(envOr("UPTIME_CONFIG", "config.yaml"))
	if err != nil {
		return err
	}

	st, err := store.Open(envOr("UPTIME_DB_PATH", "data/uptime.db"))
	if err != nil {
		return err
	}
	defer st.Close()

	var notifier scheduler.Notifier
	token, chatID := os.Getenv("TELEGRAM_BOT_TOKEN"), os.Getenv("TELEGRAM_CHAT_ID")
	if token != "" && chatID != "" {
		notifier = notify.NewTelegram(token, chatID, log)
		log.Info("telegram notifications enabled")
	} else {
		notifier = notify.NewLog(log)
		log.Info("telegram not configured, alerts go to log")
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	runner := scheduler.NewRunner(cfg, checker.New(), st, notifier, log)
	go runner.Run(ctx)
	go retentionLoop(ctx, st, log)

	srv := &http.Server{
		Addr:              addr,
		Handler:           api.New(cfg, st, log),
		ReadHeaderTimeout: 5 * time.Second,
	}

	errCh := make(chan error, 1)
	go func() {
		log.Info("listening", "addr", addr, "monitors", len(cfg.Monitors))
		errCh <- srv.ListenAndServe()
	}()

	select {
	case err := <-errCh:
		if !errors.Is(err, http.ErrServerClosed) {
			return err
		}
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			log.Error("shutdown", "err", err)
		}
		log.Info("stopped")
	}
	return nil
}

// retentionLoop раз в сутки чистит проверки старше retention.
func retentionLoop(ctx context.Context, st *store.Store, log *slog.Logger) {
	for {
		n, err := st.CleanupBefore(time.Now().Add(-retention))
		if err != nil {
			log.Error("retention cleanup", "err", err)
		} else if n > 0 {
			log.Info("retention cleanup", "deleted", n)
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(24 * time.Hour):
		}
	}
}

func runHealthcheck(addr string) int {
	url := addr
	if strings.HasPrefix(url, ":") {
		url = "127.0.0.1" + url
	}
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get("http://" + url + "/healthz")
	if err != nil {
		fmt.Fprintln(os.Stderr, "healthcheck:", err)
		return 1
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		fmt.Fprintln(os.Stderr, "healthcheck: status", resp.StatusCode)
		return 1
	}
	return 0
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
