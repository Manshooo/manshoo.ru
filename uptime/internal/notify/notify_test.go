package notify

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
)

func event(to scheduler.Status, downFor time.Duration, reason string) scheduler.Event {
	return scheduler.Event{
		Monitor: config.Monitor{Slug: "azzb", Name: "azzb.ru"},
		Tr:      scheduler.Transition{From: scheduler.StatusUp, To: to, DownFor: downFor},
		Reason:  reason,
	}
}

func TestFormat(t *testing.T) {
	cases := []struct {
		name string
		e    scheduler.Event
		want string
	}{
		{"падение с причиной", event(scheduler.StatusDown, 0, "таймаут"), "🔴 azzb.ru упал (таймаут)"},
		{"падение без причины", event(scheduler.StatusDown, 0, ""), "🔴 azzb.ru упал"},
		{"подъём", event(scheduler.StatusUp, 12*time.Minute, ""), "🟢 azzb.ru поднялся — лежал 12 мин"},
		{"подъём после секунд", event(scheduler.StatusUp, 45*time.Second, ""), "🟢 azzb.ru поднялся — лежал 45 с"},
		{"подъём после часов", event(scheduler.StatusUp, 2*time.Hour+5*time.Minute, ""), "🟢 azzb.ru поднялся — лежал 2 ч 5 мин"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := Format(tc.e); got != tc.want {
				t.Errorf("Format = %q, want %q", got, tc.want)
			}
		})
	}
}

func TestTelegramNotify(t *testing.T) {
	var (
		gotPath string
		gotBody map[string]any
	)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer srv.Close()

	tg := NewTelegram("TOKEN123", "42", srv.URL, slog.New(slog.NewTextHandler(io.Discard, nil)))
	tg.Notify(context.Background(), event(scheduler.StatusDown, 0, "таймаут"))

	if gotPath != "/botTOKEN123/sendMessage" {
		t.Errorf("path = %q", gotPath)
	}
	if gotBody["chat_id"] != "42" {
		t.Errorf("chat_id = %v", gotBody["chat_id"])
	}
	text, _ := gotBody["text"].(string)
	if !strings.Contains(text, "упал") {
		t.Errorf("text = %q, нет слова «упал»", text)
	}
}

func TestTelegramSendErrorDoesNotLeakToken(t *testing.T) {
	// Регрессия: url.Error содержит URL с токеном — в лог он попадать не должен.
	var buf bytes.Buffer
	log := slog.New(slog.NewTextHandler(&buf, nil))

	// Закрытый сервер: гарантированная ошибка соединения.
	srv := httptest.NewServer(http.NotFoundHandler())
	base := srv.URL
	srv.Close()

	tg := NewTelegram("SECRET-TOKEN-123", "42", base, log)
	tg.Notify(context.Background(), event(scheduler.StatusDown, 0, ""))

	out := buf.String()
	if out == "" {
		t.Fatal("ожидали запись об ошибке в логе")
	}
	if strings.Contains(out, "SECRET-TOKEN-123") {
		t.Fatalf("токен утёк в лог: %s", out)
	}
}
