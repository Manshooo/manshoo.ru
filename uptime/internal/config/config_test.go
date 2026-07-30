package config

import (
	"strings"
	"testing"
	"time"
)

func TestParseDefaultsAndOverrides(t *testing.T) {
	raw := []byte(`
defaults:
  interval: 30s
monitors:
  - slug: a
    url: https://a.example
  - slug: b
    name: Б
    url: https://b.example
    interval: 2m
    timeout: 3s
    expect_status: 204
    failures_to_down: 5
`)
	cfg, err := Parse(raw)
	if err != nil {
		t.Fatalf("Parse: %v", err)
	}

	a := cfg.Monitors[0]
	if a.Interval.Std() != 30*time.Second {
		t.Errorf("a.Interval = %v, want 30s (из defaults)", a.Interval.Std())
	}
	if a.Timeout.Std() != 10*time.Second {
		t.Errorf("a.Timeout = %v, want 10s (глобальный дефолт)", a.Timeout.Std())
	}
	if a.ExpectStatus != 200 || a.FailuresToDown != 3 {
		t.Errorf("a: expect_status=%d failures=%d, want 200/3", a.ExpectStatus, a.FailuresToDown)
	}
	if a.Name != "a" {
		t.Errorf("a.Name = %q, want фолбэк на slug", a.Name)
	}

	b := cfg.Monitors[1]
	if b.Interval.Std() != 2*time.Minute || b.Timeout.Std() != 3*time.Second {
		t.Errorf("b: interval=%v timeout=%v, want 2m/3s", b.Interval.Std(), b.Timeout.Std())
	}
	if b.ExpectStatus != 204 || b.FailuresToDown != 5 || b.Name != "Б" {
		t.Errorf("b: не применились явные значения: %+v", b)
	}
}

func TestParseErrors(t *testing.T) {
	cases := []struct {
		name string
		raw  string
		want string
	}{
		{"пустой конфиг", ``, "ни одного монитора"},
		{"дубль slug", "monitors:\n  - {slug: x, url: https://x.example}\n  - {slug: x, url: https://y.example}", "повторяется"},
		{"плохой url", "monitors:\n  - {slug: x, url: ftp://x}", "некорректный url"},
		{"плохая длительность", "monitors:\n  - {slug: x, url: https://x.example, interval: сорок}", "длительность"},
		{"слишком частый interval", "monitors:\n  - {slug: x, url: https://x.example, interval: 1s}", "меньше 5s"},
		{"опечатка в поле", "monitors:\n  - {slug: x, url: https://x.example, intreval: 60s}", "разбор конфига"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := Parse([]byte(tc.raw))
			if err == nil {
				t.Fatal("ожидали ошибку")
			}
			if !strings.Contains(err.Error(), tc.want) {
				t.Fatalf("ошибка %q не содержит %q", err, tc.want)
			}
		})
	}
}
