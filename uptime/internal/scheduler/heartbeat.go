package scheduler

import (
	"context"
	"net/http"
	"time"
)

// heartbeatLoop пингует внешний dead-man's-switch (healthchecks.io и т.п.).
//
// Зачем: чекер живёт на том же VPS, что и manshoo.ru, и падение самого
// сервера он заметить не может — некому будет прислать алерт. Внешний
// сервис ждёт наши пинги и сам поднимает тревогу, когда они прекратились.
func (r *Runner) heartbeatLoop(ctx context.Context) {
	client := &http.Client{Timeout: 10 * time.Second}
	interval := r.cfg.Heartbeat.Interval.Std()

	for {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, r.cfg.Heartbeat.URL, nil)
		if err != nil {
			r.log.Error("heartbeat: request", "err", err)
			return
		}
		resp, err := client.Do(req)
		if err != nil {
			if ctx.Err() != nil {
				return
			}
			r.log.Warn("heartbeat: ping failed", "err", err)
		} else {
			_ = resp.Body.Close()
		}

		if !sleepCtx(ctx, interval) {
			return
		}
	}
}
