package checker

import (
	"context"
	"net/http/httptest"
	"testing"
	"time"
)

func TestCheckTLSReadsCertificate(t *testing.T) {
	srv := httptest.NewTLSServer(nil)
	defer srv.Close()

	info, err := CheckTLS(context.Background(), srv.URL)
	if err != nil {
		t.Fatalf("CheckTLS: %v", err)
	}
	if info == nil {
		t.Fatal("info = nil для https-цели")
	}
	if info.NotAfter.Before(time.Now()) {
		t.Errorf("NotAfter в прошлом: %v", info.NotAfter)
	}
	if info.DaysLeft < 0 {
		t.Errorf("DaysLeft = %d, ждали неотрицательное", info.DaysLeft)
	}
}

func TestCheckTLSSkipsPlainHTTP(t *testing.T) {
	info, err := CheckTLS(context.Background(), "http://example.com")
	if err != nil || info != nil {
		t.Fatalf("для http ждали (nil, nil), получили (%v, %v)", info, err)
	}
}

func TestCheckTLSUnreachable(t *testing.T) {
	srv := httptest.NewTLSServer(nil)
	url := srv.URL
	srv.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if _, err := CheckTLS(ctx, url); err == nil {
		t.Fatal("ждали ошибку для закрытого сервера")
	}
}
