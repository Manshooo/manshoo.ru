// Package notify — уведомления о смене статуса: Telegram или лог.
package notify

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
)

// Format собирает человекочитаемый текст алерта.
func Format(e scheduler.Event) string {
	switch e.Tr.To {
	case scheduler.StatusDown:
		s := fmt.Sprintf("🔴 %s упал", e.Monitor.Name)
		if e.Reason != "" {
			s += " (" + e.Reason + ")"
		}
		return s
	case scheduler.StatusUp:
		s := fmt.Sprintf("🟢 %s поднялся", e.Monitor.Name)
		if e.Tr.DownFor > 0 {
			s += " — лежал " + humanDuration(e.Tr.DownFor)
		}
		return s
	default:
		return fmt.Sprintf("%s: статус %s", e.Monitor.Name, e.Tr.To)
	}
}

func humanDuration(d time.Duration) string {
	switch {
	case d < time.Minute:
		return fmt.Sprintf("%d с", int(d.Seconds()))
	case d < time.Hour:
		return fmt.Sprintf("%d мин", int(d.Minutes()))
	default:
		h := int(d.Hours())
		m := int(d.Minutes()) - h*60
		if m == 0 {
			return fmt.Sprintf("%d ч", h)
		}
		return fmt.Sprintf("%d ч %d мин", h, m)
	}
}

// Telegram шлёт алерты через Bot API.
type Telegram struct {
	token  string
	chatID string
	base   string // переопределяется в тестах
	client *http.Client
	log    *slog.Logger
}

// NewTelegram создаёт нотификатор. base — адрес Bot API: обычно
// https://api.telegram.org, но с хостингов, где он заблокирован,
// ходим через свой прокси (env TELEGRAM_API_BASE, см. docs/05-uptime.md).
func NewTelegram(token, chatID, base string, log *slog.Logger) *Telegram {
	return &Telegram{
		token:  token,
		chatID: chatID,
		base:   strings.TrimRight(base, "/"),
		client: &http.Client{Timeout: 10 * time.Second},
		log:    log,
	}
}

func (t *Telegram) Notify(ctx context.Context, e scheduler.Event) {
	payload, err := json.Marshal(map[string]any{
		"chat_id":                  t.chatID,
		"text":                     Format(e),
		"disable_web_page_preview": true,
	})
	if err != nil {
		t.log.Error("telegram: marshal", "err", err)
		return
	}

	url := fmt.Sprintf("%s/bot%s/sendMessage", t.base, t.token)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		t.log.Error("telegram: request", "err", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := t.client.Do(req)
	if err != nil {
		// ВАЖНО: не логируем err как есть — url.Error содержит URL с токеном бота
		t.log.Error("telegram: send", "err", sanitizeSendErr(err))
		return
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		t.log.Error("telegram: api error", "status", resp.StatusCode, "body", string(body))
	}
}

// sanitizeSendErr вынимает причину сбоя без URL запроса (в нём токен бота).
func sanitizeSendErr(err error) string {
	var ue *url.Error
	if errors.As(err, &ue) {
		return fmt.Sprintf("%s: %v", ue.Op, ue.Err)
	}
	return "request failed"
}

// Log — запасной нотификатор, когда Telegram не настроен.
type Log struct {
	log *slog.Logger
}

func NewLog(log *slog.Logger) *Log { return &Log{log: log} }

func (l *Log) Notify(_ context.Context, e scheduler.Event) {
	l.log.Warn("alert (telegram not configured)", "text", Format(e))
}
