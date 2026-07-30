package api_test

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/api"
	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
	"github.com/Manshooo/manshoo.ru/uptime/internal/store"
)

func setup(t *testing.T) http.Handler {
	t.Helper()

	st, err := store.Open(filepath.Join(t.TempDir(), "api.db"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = st.Close() })

	now := time.Now()
	if err := st.SaveState("azzb", scheduler.State{Status: scheduler.StatusUp, Since: now}); err != nil {
		t.Fatal(err)
	}
	ok := checker.Result{OK: true, HTTPStatus: 200, Latency: 120 * time.Millisecond}
	if err := st.RecordCheck("azzb", now, ok); err != nil {
		t.Fatal(err)
	}

	cfg := &config.Config{Monitors: []config.Monitor{
		{Slug: "azzb", Name: "azzb.ru", URL: "https://azzb.ru"},
	}}
	return api.New(cfg, st, slog.New(slog.NewTextHandler(io.Discard, nil)))
}

func get(t *testing.T, h http.Handler, path string) *httptest.ResponseRecorder {
	t.Helper()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, path, nil))
	return rec
}

func TestHealthz(t *testing.T) {
	rec := get(t, setup(t), "/healthz")
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestStatus(t *testing.T) {
	rec := get(t, setup(t), "/api/status")
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body: %s", rec.Code, rec.Body)
	}

	var out []struct {
		Slug      string   `json:"slug"`
		Status    string   `json:"status"`
		Uptime24h *float64 `json:"uptime_24h"`
		LastCheck *struct {
			OK        bool  `json:"ok"`
			LatencyMs int64 `json:"latency_ms"`
		} `json:"last_check"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &out); err != nil {
		t.Fatalf("json: %v, body: %s", err, rec.Body)
	}
	if len(out) != 1 {
		t.Fatalf("len = %d, want 1", len(out))
	}
	m := out[0]
	if m.Slug != "azzb" || m.Status != "up" {
		t.Errorf("монитор: %+v", m)
	}
	if m.Uptime24h == nil || *m.Uptime24h != 100 {
		t.Errorf("Uptime24h = %v, want 100", m.Uptime24h)
	}
	if m.LastCheck == nil || !m.LastCheck.OK || m.LastCheck.LatencyMs != 120 {
		t.Errorf("LastCheck: %+v", m.LastCheck)
	}
}

func TestMonitorDetail(t *testing.T) {
	rec := get(t, setup(t), "/api/monitors/azzb")
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d", rec.Code)
	}
	var out struct {
		Monitor struct {
			Slug string `json:"slug"`
		} `json:"monitor"`
		Checks []any `json:"checks"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &out); err != nil {
		t.Fatalf("json: %v", err)
	}
	if out.Monitor.Slug != "azzb" || len(out.Checks) != 1 {
		t.Errorf("детали: %+v", out)
	}
}

func TestMonitorNotFound(t *testing.T) {
	rec := get(t, setup(t), "/api/monitors/nope")
	if rec.Code != http.StatusNotFound {
		t.Fatalf("status = %d, want 404", rec.Code)
	}
}
