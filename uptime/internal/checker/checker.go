// Package checker выполняет одну HTTP-проверку монитора.
package checker

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
)

type Result struct {
	OK         bool
	HTTPStatus int // 0, если ответ не получен
	Latency    time.Duration
	Err        string // причина неудачи, пустая при OK
}

type Checker struct {
	client *http.Client
}

func New() *Checker {
	// Таймаут задаётся per-monitor через контекст; редиректы клиент
	// проходит сам (важен итоговый статус страницы).
	return &Checker{client: &http.Client{}}
}

func (c *Checker) Check(ctx context.Context, m config.Monitor) Result {
	ctx, cancel := context.WithTimeout(ctx, m.Timeout.Std())
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, m.URL, nil)
	if err != nil {
		return Result{Err: fmt.Sprintf("не удалось собрать запрос: %v", err)}
	}
	req.Header.Set("User-Agent", "manshoo-uptime/1.0 (+https://github.com/Manshooo/manshoo.ru)")

	start := time.Now()
	resp, err := c.client.Do(req)
	latency := time.Since(start)
	if err != nil {
		return Result{Latency: latency, Err: failReason(ctx, err)}
	}
	defer resp.Body.Close()
	// Дочитываем кусочек тела, чтобы соединение вернулось в keep-alive пул.
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 64<<10))

	res := Result{HTTPStatus: resp.StatusCode, Latency: latency}
	if resp.StatusCode == m.ExpectStatus {
		res.OK = true
	} else {
		res.Err = fmt.Sprintf("ожидали статус %d, получили %d", m.ExpectStatus, resp.StatusCode)
	}
	return res
}

func failReason(ctx context.Context, err error) string {
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		return "таймаут"
	}
	return err.Error()
}
