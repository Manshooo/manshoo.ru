package scheduler

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
)

type nopStore struct{}

func (nopStore) RecordCheck(string, time.Time, checker.Result) error { return nil }
func (nopStore) LoadState(string) (State, bool, error)               { return State{}, false, nil }
func (nopStore) SaveState(string, State) error                       { return nil }
func (nopStore) LoadTLS(string) (TLSRecord, bool, error)             { return TLSRecord{}, false, nil }
func (nopStore) SaveTLS(string, TLSRecord) error                     { return nil }

type nopNotifier struct{}

func (nopNotifier) Notify(context.Context, Event)      {}
func (nopNotifier) NotifyText(context.Context, string) {}

func TestHeartbeatPings(t *testing.T) {
	var hits atomic.Int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		hits.Add(1)
	}))
	defer srv.Close()

	cfg := &config.Config{
		Monitors: []config.Monitor{{Slug: "t", URL: "https://example.com"}},
		Heartbeat: config.Heartbeat{
			URL:      srv.URL,
			Interval: config.Duration(20 * time.Millisecond),
		},
	}
	runner := NewRunner(cfg, checker.New(), nopStore{}, nopNotifier{},
		slog.New(slog.NewTextHandler(io.Discard, nil)))

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Millisecond)
	defer cancel()
	runner.heartbeatLoop(ctx)

	if hits.Load() < 2 {
		t.Fatalf("пингов = %d, ждали минимум 2", hits.Load())
	}
}

func TestHeartbeatStopsOnCancel(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {}))
	defer srv.Close()

	cfg := &config.Config{
		Heartbeat: config.Heartbeat{URL: srv.URL, Interval: config.Duration(time.Hour)},
	}
	runner := NewRunner(cfg, checker.New(), nopStore{}, nopNotifier{},
		slog.New(slog.NewTextHandler(io.Discard, nil)))

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})
	go func() { runner.heartbeatLoop(ctx); close(done) }()

	cancel()
	select {
	case <-done:
	case <-time.After(time.Second):
		t.Fatal("heartbeatLoop не завершился после отмены контекста")
	}
}
