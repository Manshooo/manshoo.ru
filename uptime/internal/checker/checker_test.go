package checker

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
)

func monitor(url string, timeout time.Duration) config.Monitor {
	return config.Monitor{
		Slug:         "t",
		URL:          url,
		Timeout:      config.Duration(timeout),
		ExpectStatus: 200,
	}
}

func TestCheckOK(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("ok"))
	}))
	defer srv.Close()

	res := New().Check(context.Background(), monitor(srv.URL, time.Second))
	if !res.OK {
		t.Fatalf("OK = false, err = %q", res.Err)
	}
	if res.HTTPStatus != 200 {
		t.Errorf("HTTPStatus = %d, want 200", res.HTTPStatus)
	}
	if res.Err != "" {
		t.Errorf("Err = %q, want пусто", res.Err)
	}
}

func TestCheckUnexpectedStatus(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusBadGateway)
	}))
	defer srv.Close()

	res := New().Check(context.Background(), monitor(srv.URL, time.Second))
	if res.OK {
		t.Fatal("OK = true, хотя статус 502")
	}
	if res.HTTPStatus != 502 || !strings.Contains(res.Err, "502") {
		t.Errorf("status=%d err=%q, ждали 502 в обоих", res.HTTPStatus, res.Err)
	}
}

func TestCheckTimeout(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(_ http.ResponseWriter, _ *http.Request) {
		time.Sleep(300 * time.Millisecond)
	}))
	defer srv.Close()

	res := New().Check(context.Background(), monitor(srv.URL, 50*time.Millisecond))
	if res.OK {
		t.Fatal("OK = true, хотя сервер не успел ответить")
	}
	if res.Err != "таймаут" {
		t.Errorf("Err = %q, want таймаут", res.Err)
	}
}

func TestCheckConnectionRefused(t *testing.T) {
	// Закрытый сервер: порт уже никого не слушает.
	srv := httptest.NewServer(http.NotFoundHandler())
	url := srv.URL
	srv.Close()

	res := New().Check(context.Background(), monitor(url, time.Second))
	if res.OK {
		t.Fatal("OK = true для мёртвого адреса")
	}
	if res.Err == "" {
		t.Error("Err пустой, ждали причину ошибки соединения")
	}
}
