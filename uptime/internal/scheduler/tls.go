package scheduler

import (
	"context"
	"fmt"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
)

// TLSRecord — что известно о сертификате монитора (хранится в БД).
type TLSRecord struct {
	NotAfter    time.Time
	DaysLeft    int
	CheckedAt   time.Time
	LastAlertAt time.Time
}

// tlsCheckInterval — сертификаты живут месяцами, чаще смотреть незачем.
const tlsCheckInterval = 12 * time.Hour

// tlsAlertCooldown — не напоминать об одном и том же чаще раза в сутки.
const tlsAlertCooldown = 24 * time.Hour

// ShouldWarnTLS решает, пора ли предупреждать о скором истечении.
func ShouldWarnTLS(daysLeft, warnDays int, lastAlert, now time.Time) bool {
	if warnDays <= 0 || daysLeft > warnDays {
		return false
	}
	return now.Sub(lastAlert) >= tlsAlertCooldown
}

// FormatTLSWarning — текст предупреждения о сертификате.
func FormatTLSWarning(name string, daysLeft int, notAfter time.Time) string {
	if daysLeft <= 0 {
		return fmt.Sprintf("🔒 %s: сертификат просрочен (истёк %s)", name, notAfter.Format("02.01.2006"))
	}
	return fmt.Sprintf(
		"🔒 %s: сертификат истекает через %d дн. (%s)",
		name, daysLeft, notAfter.Format("02.01.2006"),
	)
}

// tlsLoop раз в полсуток обходит мониторы и предупреждает о близком истечении.
func (r *Runner) tlsLoop(ctx context.Context) {
	for {
		for _, m := range r.cfg.Monitors {
			r.checkTLS(ctx, m)
			if ctx.Err() != nil {
				return
			}
		}
		if !sleepCtx(ctx, tlsCheckInterval) {
			return
		}
	}
}

func (r *Runner) checkTLS(ctx context.Context, m config.Monitor) {
	info, err := checker.CheckTLS(ctx, m.URL)
	if err != nil {
		// Недоступность цели уже видна в обычных проверках — здесь только лог
		r.log.Warn("tls check failed", "monitor", m.Slug, "err", err)
		return
	}
	if info == nil {
		return // http-цель, сертификата нет
	}

	previous, _, err := r.store.LoadTLS(m.Slug)
	if err != nil {
		r.log.Error("load tls state", "monitor", m.Slug, "err", err)
	}

	record := TLSRecord{
		NotAfter:    info.NotAfter,
		DaysLeft:    info.DaysLeft,
		CheckedAt:   info.CheckedAt,
		LastAlertAt: previous.LastAlertAt,
	}

	now := info.CheckedAt
	if ShouldWarnTLS(info.DaysLeft, r.cfg.Defaults.TLSExpiryWarnDays, previous.LastAlertAt, now) {
		r.notifier.NotifyText(ctx, FormatTLSWarning(m.Name, info.DaysLeft, info.NotAfter))
		record.LastAlertAt = now
		r.log.Info("tls expiry warning", "monitor", m.Slug, "days_left", info.DaysLeft)
	}

	if err := r.store.SaveTLS(m.Slug, record); err != nil {
		r.log.Error("save tls state", "monitor", m.Slug, "err", err)
	}
}
