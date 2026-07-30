// Package api — JSON API статусов для сайта и healthz для docker.
package api

import (
	"encoding/json"
	"log/slog"
	"math"
	"net/http"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
	"github.com/Manshooo/manshoo.ru/uptime/internal/store"
)

type handler struct {
	cfg *config.Config
	st  *store.Store
	log *slog.Logger
}

func New(cfg *config.Config, st *store.Store, log *slog.Logger) http.Handler {
	h := &handler{cfg: cfg, st: st, log: log}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("GET /api/status", h.status)
	mux.HandleFunc("GET /api/monitors/{slug}", h.monitor)
	return mux
}

type lastCheck struct {
	At         time.Time `json:"at"`
	OK         bool      `json:"ok"`
	HTTPStatus int       `json:"http_status"`
	LatencyMs  int64     `json:"latency_ms"`
	Error      string    `json:"error,omitempty"`
}

type monitorStatus struct {
	Slug               string     `json:"slug"`
	Name               string     `json:"name"`
	URL                string     `json:"url"`
	Status             string     `json:"status"`
	Since              time.Time  `json:"since"`
	Uptime24h          *float64   `json:"uptime_24h"`
	Uptime7d           *float64   `json:"uptime_7d"`
	Uptime30d          *float64   `json:"uptime_30d"`
	MedianLatencyMs24h *int64     `json:"median_latency_ms_24h"`
	LastCheck          *lastCheck `json:"last_check"`
}

func (h *handler) status(w http.ResponseWriter, r *http.Request) {
	out := make([]monitorStatus, 0, len(h.cfg.Monitors))
	for _, m := range h.cfg.Monitors {
		ms, err := h.monitorStatus(m)
		if err != nil {
			h.log.Error("api: monitor status", "monitor", m.Slug, "err", err)
			http.Error(w, "internal error", http.StatusInternalServerError)
			return
		}
		out = append(out, ms)
	}
	writeJSON(w, http.StatusOK, out)
}

func (h *handler) monitor(w http.ResponseWriter, r *http.Request) {
	slug := r.PathValue("slug")
	var found *config.Monitor
	for i := range h.cfg.Monitors {
		if h.cfg.Monitors[i].Slug == slug {
			found = &h.cfg.Monitors[i]
			break
		}
	}
	if found == nil {
		writeJSON(w, http.StatusNotFound, map[string]string{"error": "монитор не найден"})
		return
	}

	ms, err := h.monitorStatus(*found)
	if err != nil {
		h.log.Error("api: monitor status", "monitor", slug, "err", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	history, err := h.st.History(slug, time.Now().Add(-24*time.Hour), 100)
	if err != nil {
		h.log.Error("api: history", "monitor", slug, "err", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	checks := make([]lastCheck, 0, len(history))
	for _, c := range history {
		checks = append(checks, toLastCheck(c))
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"monitor": ms,
		"checks":  checks,
	})
}

func (h *handler) monitorStatus(m config.Monitor) (monitorStatus, error) {
	now := time.Now()

	st, found, err := h.st.LoadState(m.Slug)
	if err != nil {
		return monitorStatus{}, err
	}
	if !found {
		st = scheduler.NewState(now)
	}

	ms := monitorStatus{
		Slug:   m.Slug,
		Name:   m.Name,
		URL:    m.URL,
		Status: string(st.Status),
		Since:  st.Since,
	}

	for _, p := range []struct {
		dst **float64
		age time.Duration
	}{
		{&ms.Uptime24h, 24 * time.Hour},
		{&ms.Uptime7d, 7 * 24 * time.Hour},
		{&ms.Uptime30d, 30 * 24 * time.Hour},
	} {
		sum, err := h.st.Summary(m.Slug, now.Add(-p.age))
		if err != nil {
			return monitorStatus{}, err
		}
		*p.dst = roundPct(sum.UptimePct)
		if p.age == 24*time.Hour {
			ms.MedianLatencyMs24h = sum.MedianLatencyMs
		}
	}

	last, err := h.st.LastCheck(m.Slug)
	if err != nil {
		return monitorStatus{}, err
	}
	if last != nil {
		lc := toLastCheck(*last)
		ms.LastCheck = &lc
	}
	return ms, nil
}

func toLastCheck(c store.CheckRow) lastCheck {
	return lastCheck{
		At:         c.At,
		OK:         c.OK,
		HTTPStatus: c.HTTPStatus,
		LatencyMs:  c.LatencyMs,
		Error:      c.Error,
	}
}

func roundPct(p *float64) *float64 {
	if p == nil {
		return nil
	}
	v := math.Round(*p*100) / 100
	return &v
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
