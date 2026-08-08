package scheduler

import (
	"strings"
	"testing"
	"time"
)

func TestShouldWarnTLS(t *testing.T) {
	now := time.Date(2026, 8, 1, 12, 0, 0, 0, time.UTC)
	never := time.Time{}

	cases := []struct {
		name      string
		daysLeft  int
		warnDays  int
		lastAlert time.Time
		want      bool
	}{
		{"запас большой", 40, 14, never, false},
		{"порог достигнут", 14, 14, never, true},
		{"почти истёк", 2, 14, never, true},
		{"просрочен", -1, 14, never, true},
		{"следить отключено", 1, 0, never, false},
		{"уже предупреждали час назад", 3, 14, now.Add(-time.Hour), false},
		{"предупреждали вчера", 3, 14, now.Add(-25 * time.Hour), true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := ShouldWarnTLS(tc.daysLeft, tc.warnDays, tc.lastAlert, now)
			if got != tc.want {
				t.Errorf("ShouldWarnTLS = %v, want %v", got, tc.want)
			}
		})
	}
}

func TestFormatTLSWarning(t *testing.T) {
	notAfter := time.Date(2026, 8, 15, 0, 0, 0, 0, time.UTC)

	text := FormatTLSWarning("manshoo.ru", 14, notAfter)
	if !strings.Contains(text, "14 дн.") || !strings.Contains(text, "15.08.2026") {
		t.Errorf("текст предупреждения = %q", text)
	}

	expired := FormatTLSWarning("manshoo.ru", 0, notAfter)
	if !strings.Contains(expired, "просрочен") {
		t.Errorf("текст для просроченного = %q", expired)
	}
}
